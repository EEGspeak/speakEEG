from preprocess import MNEFilter, ReadCSV

import mne
import numpy as np
import pandas as pd

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, WeightedRandomSampler

mne.set_config("MNE_BROWSE_RAW_SIZE", "10,5") # Window size = 10in x 5in

# GPU acceleration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class P300Checker(MNEFilter):
    """
    Class for P300 detection using Convolutional Neural Networks (CNNs).
    
    Functionality:
    - `train`: Trains CNN model on training data.
    - `evaluate`: Evaluates model on test data.
    - `predict`: Predicts P300 signal on new data.
    - `plot`: Plots P300 signal.
    """
    
    def __init__(self, train_path, test_path):
        """
        Parameters:
        - `train_path` (str): Path to training data CSV file.
        - `test_path` (str): Path to test data CSV file.
        """

        super().__init__()

        self.train_path = train_path
        self.test_path = test_path

        self.train_F = self._quick_filter(train_path)
        self.test_F = self._quick_filter(test_path)

        """
        TODO: stopped here
        
        ! - p300 checker algorithm
        ! - find out how to place markers in CSV (preferably at column 10)
        !     - ref chacklam code
        """

        
        # Extract training and test data
        self.X_train, self.y_train = self.extract_data(self.train_data)
        self.X_test, self.y_test = self.extract_data(self.test_data)
        
        # Initialize CNN model
        self.model = self.init_model()
        
        # Initialize loss function and optimizer
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
    
    def _quick_filter(self, path):
        """
        Uses ReadCSV and MNEFilter commands to quickly filter data.
        """

        return path._load_df().iloc[:, 1:9].to_mne().filter_mne()

        
    def extract_data(self, data):
        """
        Extracts data from MNE `Raw` object.
        
        Parameters:
        - `data` (mne.io.RawArray): MNE `Raw` object.
        
        Returns:
        - `X` (torch.Tensor): Tensor of shape (n_samples, n_channels, n_timepoints).
        - `y` (torch.Tensor): Tensor of shape (n_samples).
        """
        
        # Extract data and labels
        X = torch.tensor(data.get_data(), dtype=torch.float32).unsqueeze(1)
        y = torch.tensor(data.annotations.description, dtype=torch.long)
        
        return X, y
    
    
    def init_model(self):
        """
        Initializes CNN model.
        
        Returns:
        - `model` (nn.Module): CNN model.
        """
        
        
        # model = nn.Sequential(
            # nn.Conv