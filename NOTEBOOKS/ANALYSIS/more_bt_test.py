# bluetooth data collection module for P300 data


import pygame
import pandas as pd
import time
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
import threading
import random

# Set up BrainFlow parameters for Neurosity Crown
params = BrainFlowInputParams()
params.mac_address = "C0:EE:40:A1:7F:BA"  # Replace with your Neurosity Crown MAC Address
params.timeout = 15  # Timeout in seconds
params.serial_port = ""  # Keep this empty for Bluetooth

# Board ID for Neurosity Crown
board_id = BoardIds.CROWN_BOARD.value

# Initialize the BoardShim
board = BoardShim(board_id, params)

# Prepare session and start streaming
try:
    board.prepare_session()
    board.start_stream(45000, "")  # Buffer size
    print("Bluetooth connection started and streaming data.")
except BrainFlowError as e:
    print(f"Error initializing BrainFlow: {e}")
    exit()

# Initialize Pygame
pygame.init()

# Screen dimensions
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("P300 Data Collector")

# Colors and stimuli
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
BLACK = (0, 0, 0)
letters = ["X", "Y", "Z", "W"]
colors = [RED, GREEN, YELLOW, PURPLE]

# Marker values
marker_value = 0
marker_lock = threading.Lock()

# EEG Data Collection
eeg_data = []
stop_flag = False

def collect_data():
    """Continuously collect EEG data with markers."""
    global stop_flag
    while not stop_flag:
        try:
            data = board.get_board_data()  # Fetch streamed data
            eeg_channel_indices = board.get_eeg_channels(board_id)  # Get EEG channel indices
            with marker_lock:
                current_marker = marker_value
            for row in data.T:  # Iterate through collected rows
                eeg_data.append([row[channel] for channel in eeg_channel_indices] + [current_marker])
            time.sleep(0.1)  # Adjust sleep time for desired update frequency
        except BrainFlowError as e:
            print(f"Error collecting data: {e}")
            stop_flag = True


# Start data collection thread
data_thread = threading.Thread(target=collect_data)
data_thread.start()

# Function to draw stimuli
def draw_stimulus(stimulus, letter=None, color=None, size=None, position=None):
    screen.fill(WHITE)
    if stimulus == "plus":
        font = pygame.font.Font(None, 74)
        text = font.render("+", True, BLACK)
        screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, screen.get_height() // 2 - text.get_height() // 2))
    elif stimulus == "blue_circle":
        pygame.draw.circle(screen, BLUE, (screen.get_width() // 2, screen.get_height() // 2), 25)
    elif stimulus == "oddball":
        font = pygame.font.Font(None, size)
        text = font.render(letter, True, color)
        screen.blit(text, position)
    pygame.display.flip()

# Main loop for stimuli
running = True
flash_time = 0
current_stimulus = "plus"
last_flash_time = pygame.time.get_ticks()
flash_interval = 700
blue_duration = 400
oddball_min_duration = 150
oddball_max_duration = 300

try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        current_time = pygame.time.get_ticks()

        if current_stimulus == "plus" and current_time - last_flash_time > flash_interval:
            rand_value = random.random()
            if rand_value < 0.8:
                current_stimulus = "blue_circle"
                stimulus_duration = blue_duration
                with marker_lock:
                    marker_value = 1
                flash_time = current_time
                last_flash_time = current_time
            else:
                current_stimulus = "oddball"
                stimulus_duration = random.randint(oddball_min_duration, oddball_max_duration)
                random_index = random.randint(0, 3)
                oddball_letter = letters[random_index]
                oddball_color = colors[random_index]
                oddball_size = random.randint(400, 700)
                oddball_x = random.randint(50, screen.get_width() - 150)
                oddball_y = random.randint(50, screen.get_height() - 150)
                oddball_position = (oddball_x, oddball_y)
                with marker_lock:
                    marker_value = 2
                flash_time = current_time
                last_flash_time = current_time
        elif current_stimulus in ["oddball", "blue_circle"] and current_time - flash_time > stimulus_duration:
            current_stimulus = "plus"
            with marker_lock:
                marker_value = 0

        draw_stimulus(current_stimulus, oddball_letter if current_stimulus == "oddball" else None,
                      oddball_color if current_stimulus == "oddball" else None,
                      oddball_size if current_stimulus == "oddball" else None,
                      oddball_position if current_stimulus == "oddball" else None)

finally:
    # Stop data collection
    stop_flag = True
    data_thread.join()

    # Save data to CSV
    column_names = board.get_eeg_names(board_id) + ["Marker"]
    df = pd.DataFrame(eeg_data, columns=column_names)
    output_file = "P300.csv"
    df.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")

    # Clean up
    try:
        board.stop_stream()
        board.release_session()
    except BrainFlowError as e:
        print(f"Error stopping BrainFlow session: {e}")

    pygame.quit()
