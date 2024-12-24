import pandas as pd
import os
import numpy as np

import mne
import matplotlib.pyplot as plt


# **** CONFIGURATION **** #
                                            #!!!!!!!!!!!!!!!!!!!! vvvvvv MUST UPDATE THIS WITH ANY FILE INPUTTED vvvvvv !!!!!!!!!!!!!!!!!!!!#
DATA_MODE = "train" # ? "default", "fusion", "train"

channels = ["CP3", "C3", "F5", "PO3", "PO4", "F6", "C4", "CP4"]

DEFAULT_COL = ["index", *channels, "none", "timestamp"]
FUSION_COL = ["index", "timestamp", *channels]
TRAIN_COL = ["index", *channels, "marker"]

modes: dict[str, tuple] = {
    "default": (DEFAULT_COL, (1, 9 ), False),
    "fusion" : (FUSION_COL , (2, 10), False),
    "train"  : (TRAIN_COL  , (1, 10), True )
}
col_labels, CHANNEL_IX, IS_TRAIN_DATA = modes[DATA_MODE]


class ReadCSV:
    """
    Works with Neurosity Crown data in CSV format.

    Functionality:
    - `_load_df`: Load entire CSV DataFrame from file.
    - `get_second`: Access pd.DataFrame representing one second of data.
    """

    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self._DF = self._load_df().iloc[:, CHANNEL_IX[0]:CHANNEL_IX[1]]
    

    def _load_df(self) -> pd.DataFrame:
        """
        Load entire CSV DataFrame from file. Returns pd.DataFrame

        Returns error if file not found or not readable.
        """
        if not os.path.exists(self.csv_file_path):
            raise FileNotFoundError(f"The file at {self.csv_file_path} does not exist.")
        try:
            init_df = pd.read_csv(self.csv_file_path, header=None, float_precision="round_trip")

            # Convert all cells to floats, except first column
            init_df.iloc[1:, CHANNEL_IX[0]:CHANNEL_IX[1]] = init_df.iloc[1:, CHANNEL_IX[0]:CHANNEL_IX[1]].astype(float)

            #! Markers are all floats (0.0, 1.0, 2.0)

            return init_df

        except Exception as e:
            raise ValueError(f"An error occurred while reading the CSV file: {e}")
        

    def get_second(self, second: int) -> tuple[pd.DataFrame, bool]:
        """
        Access 256x11 DataFrame representing one second of data. 0-indexed
        - Neurosity Crown data has 256 Hz sampling rate, split into chunks of 0...31 equating to 1/8 sec.
        
        Raises error if second requested is not in data.
        
        If requested second is not completely recorded, outputted tuple will return `False`.
        """

        df = self._DF
        start_ix = second * 256

        if second < 0:
            raise ValueError(f"Requested second {second} not positive value.")
        elif start_ix >= df.shape[0]:
            raise ValueError(f"Requested second {second} not in dataset.")
        
        return df.iloc[start_ix:start_ix+256, :], start_ix+255 < df.shape[0]


class MNEFilter(ReadCSV):
    """
    Preprocesses data using MNE-python.

    Functionality:
    - `to_mne`: Converts CSV file to MNE `Raw` data format.
    - `filter_mne`: Filters MNE data using low-pass and powerline filters.
    - `plot_raw`: Plots raw data using MNE.
    - `plot_filtered_raw`: Plots raw data with filters applied.
    - `plot_psd`: Plots power spectral density (PSD) of filtered data using MNE.
    """

    def __init__(self, _DF): # parameters passed into ReadCSV, not MNEFilter
                             # e.g. if you initialize MNEFilter(X), X is not a pd.DataFrame, but a path to a CSV file
        super().__init__(_DF)
        self._RAW = self.to_mne()
        self._RAW_FILTERED = self.filter_mne()
    
    
    def to_mne(self):
        """
        Converts CSV file to MNE `Raw` data format (similar to pd.DataFrame)
        - Takes pd.DataFrame --> mne.RawArray
        - Outputted RawArray contains metadata `info`.
 
        *Note that MNE has channels in rows instead of columns.*
        """

        ch_types = ["eeg"] * 8
        ch_names = channels
        if IS_TRAIN_DATA: # ! Marker column
            ch_types.append("stim")
            ch_names.append("marker")
    
        # Instantiates metadata(labels) associated with CSV data. `sfreq` is sampling rate (256 Hz).
        info = mne.create_info(
            ch_names=ch_names,
            sfreq=256,
            ch_types=ch_types
        )

        df = self._DF.T.iloc[:, 1:] # Transpose DataFrame to have channels in rows
                                    # Exclude first column (channels)

        # Convert from microvolts to volts (MNE expects volts)
        if IS_TRAIN_DATA:
            df.iloc[:-1, 1:] = df.iloc[:-1, 1:].mul(1e-6)
        else:
            df.iloc[:, 1:] = df.iloc[:, 1:].mul(1e-6)
        raw = mne.io.RawArray(df, info)

        # 10-20 channel location system
        montage = mne.channels.make_standard_montage("standard_1020")
        raw.set_montage(montage)

        return raw
    

    def filter_mne(self):
        """
        Filters mne.RawArray data using:
        - Low-pass filter: removes any noise outside of P300 frequencies
          - According to Lafuente et al. (https://doi.org/10.1016/j.eswa.2016.12.038):
            "The smaller the probability of related event is, the more prominent the P300 will be" (Citi, Poli, & Cinel, 2010).
        - Powerline filter: removes any frequency emitted by powerlines (60Hz in Americas)        
        """

        raw_U = self._RAW

        # Low-pass filter
        CUTOFF_LOW_FREQ, CUTOFF_HIGH_FREQ = 1, 18  # !! 10/9/24 # Changed from 1, 40 to 1, 18
            # TODO -- EXPERIMENT WITH DIFFERENT P300 FREQUENCIES
            # https://arc.net/l/quote/yiztowhs (0.1, 20)
            # https://arc.net/l/quote/vadqwzby (1, 40)
        
        # FIRwin is type of low-pass filter. Other type is butterworth.
        raw_Lpass = raw_U.filter(
            CUTOFF_LOW_FREQ,
            CUTOFF_HIGH_FREQ,
            fir_design="firwin"
        )

        # Powerline filter
        raw_Lpass_notch = raw_Lpass.notch_filter(
            freqs=60,             # 60 Hz in Americas
            picks=list(range(8))  # Channels to pick; all 8 EEG channels
        )

        return raw_Lpass_notch # Low-pass & Powerline-filtered
    

    def plot_raw(self):
        """
        Plot raw data using MNE.
        """

        raw_U = self._RAW

        raw_U.plot(
            n_channels=8,
            scalings="auto",
            title="Raw EEG data",
            show=True, block=True
        )

        return 0
    

    def plot_mpl(self):
        """
        Plot raw data using Matplotlib.
        ! May not be accurate
        """

        if DATA_MODE != "default":
            return 1  # ! Not supported for non-default data

        sfreq = 256  
        times = np.arange(0, 10, 1 / sfreq)  # 10 secs
    
        ch_names = channels[:8] # picks first 8 channels (always will be EEG channels)

        info = mne.create_info(
            ch_names=ch_names,
            sfreq=256,
            ch_types=["eeg"] * 8
        )

        raw_F = self._RAW_FILTERED
        raw_F = (raw_F[:-1] if IS_TRAIN_DATA else raw_F) # Exclude marker row



        data, times = raw_F.get_data(return_times=True)

        # channel loop
        for channel_index in range(data.shape[0]):
            channel_data = data[channel_index]

            plt.figure(figsize=(10, 5))  
            plt.plot(times, channel_data)
            plt.xlabel('time')
            plt.ylabel('amplitude')
            plt.title(f'EEG Data for Channel {mne.io.RawArray(data, info).ch_names[channel_index]}')
            plt.show()
        
        return 0


    def plot_filtered_raw(self):
        """
        Plot raw data with Low-pass and Powerline filters applied onto it.
        Uses MNE-python.
        """

        raw_F = self._RAW_FILTERED

        raw_F.plot(
            n_channels=8,
            scalings="auto",
            title="Filtered EEG data",
            show=True, block=True
        )

        return 0


    def plot_psd(self):
        """
        Plot power spectral density (PSD) of filtered data using MNE.
        """

        raw_F = self._RAW_FILTERED
        raw_F = (raw_F[:-1] if IS_TRAIN_DATA else raw_F)

        raw_F.compute_psd().plot(show=True)
        plt.title("PSD")
        plt.show()

        return 0
    
    def equalize_markers(self):
        """
        Each training file has markers in the last column. (Unique set = {0, 1, 2})
        Remove surplus 1s such that 1s = 2s. We perform this action by replacing the 1s with 3s.
        """

        if not IS_TRAIN_DATA:
            return 1

        raw_F = self._RAW_FILTERED
        data, times = raw_F.get_data(return_times=True)
        markers = data[-1]

        # find all 2s
        marker_ix_2 = np.where(markers == 2)[0]
        # find all 1s
        marker_ix_1 = np.where(markers == 1)[0]
        np.random.shuffle(marker_ix_1)
        # indices of the 1s to remove
        rem_ix = marker_ix_1[:len(marker_ix_1) - len(marker_ix_2)]

        # replace 1s with 3s
        markers[rem_ix] = 3
        data[-1] = markers

        raw_F = mne.io.RawArray(data, raw_F.info)

        return raw_F



if __name__ == "__main__":
    test_path = "/Users/rishabh/code/eeg/speakEEG/data/testdata.csv"
    test_path = "/Users/rishabh/code/eeg/speakEEG/data/fusion_P300_test_1/rawBrainwaves_1718993930.csv"
    test_path = "/Users/rishabh/code/eeg/speakEEG/data/markers_eeg_data.csv"
    test_path = "/Users/rishabh/code/eeg/speakEEG/data/AAROOSH_data4.csv"
    data = MNEFilter(test_path) # parameters passed into ReadCSV, not MNEFilter

    # ! TEST MARKER EQUALIZER
    x = data.equalize_markers()
    data1, times = x.get_data(return_times=True)

    df = pd.DataFrame(data1.T,index=times,columns=channels)

    print(df.iloc[:, -1].value_counts()) # should have equal 1s and 2s
    """ with AAROOSH_data4.csv
    0.0    70499
    3.0      170
    2.0      132
    1.0      132
    Name: count, dtype: int64
    """
