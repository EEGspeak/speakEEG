"""
Live-streaming layer

The overall process to effectively use brainflow is by starting a session and 
continously appending data recorded to a CSV file. A thread runs in the background
to check if the enter key is hit, and if it is the stream is stopped and the CSV
file is saved.
"""


import brainflow
import numpy as np
import pandas as pd
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
import threading
import time

# initialize neurosity features
EEG_INDICES = [0, 1, 2, 3, 4, 5, 6, 7]  # Indices for the 8 channels
SAMPLE_FREQ = 256  # Sampling frequency
EEG_CHANNELS = ["C3", "C4", "CP3", "CP4", "F5", "F6", "PO3", "PO4"]  # Channel names
CSV_FILE = 'collected_eeg_data.csv'

# start brainflow
brainflow_params = BrainFlowInputParams()
board_id = BoardIds.CROWN_BOARD.value

# starts thread to look for enter press
stop_recording = threading.Event()

# listen for the enter key
def listen_for_stop():
    input("Press enter to stop\n")
    stop_recording.set()

# prep board for brainflow use
def initialize_board():
    # stop previous sessions (can interfere)
    try:
        board = BoardShim(board_id, brainflow_params)
        board.release_session()
        print("session released")
    except Exception as e: #all try and excepts are to stop random errors from printing
        print(f"nothing left to release: {e}")

    # begin new session
    try:
        board = BoardShim(board_id, brainflow_params)
        board.prepare_session()
        print("session prepped")
        return board
    except Exception as e:
        print(f"failure to prep session {e}")
        exit(1)

# Starts appending data to CSV file
def collect_data(board):
    try:
        data = board.get_board_data()  # takes data from board
        print("completed!")

        # DATA PROCESSING
        
        data = data.T  # Transpose data
        #basic data info
        ch_names = BoardShim.get_eeg_names(board_id)
        eeg_data = data[:, BoardShim.get_eeg_channels(board_id)]
        timestamps = data[:, BoardShim.get_timestamp_channel(board_id)]

        df = pd.DataFrame(eeg_data, index=timestamps, columns=ch_names)
        
        # Append data to CSV file
        df.to_csv(CSV_FILE, mode='a', header=not pd.io.common.file_exists(CSV_FILE), index=False)
        print("Data saved to CSV file.")
    except Exception as e:
        print(f"Error collecting or processing data: {e}")

# thread listning for stop
thread = threading.Thread(target=listen_for_stop)
thread.start()

# clear csv after every use
with open(CSV_FILE, 'w') as f:
    f.truncate()

# prep board
board = initialize_board()

# stream start
try:
    board.start_stream()
    print("Stream started.")
except Exception as e:
    print(f"Error starting stream: {e}")
    board.release_session()
    exit(1)



# continously loop every 5 seconds
try:
    while not stop_recording.is_set():
        #! time.sleep(.3)  # Collect data every .3 seconds
        collect_data(board)
except KeyboardInterrupt:
    pass

# stream stop
try:
    board.stop_stream()
    print("Stream stopped.")
except Exception as e:
    print(f"Error stopping stream: {e}")

# stream release
try:
    board.release_session()
    print("Session released.")
except Exception as e:
    print(f"Error releasing session: {e}")

print("Data saved properly")
