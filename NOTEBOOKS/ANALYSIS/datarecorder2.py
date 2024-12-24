import pygame
import time
import csv
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations
import threading
import random

# Initialize Pygame
pygame.init()

# Initialize the mixer module
pygame.mixer.init()

# Load the beep sound
beep_sound = pygame.mixer.Sound("beep.wav")  # Ensure you have a beep.wav file in your directory

# Screen dimensions
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("P300 Data Collector")

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
BLACK = (0, 0, 0)

# Different letters and colors for the oddball stimulus
letters = ["X", "Y", "Z", "W"]
colors = [RED, GREEN, YELLOW, PURPLE]

# Initialize BrainFlow
params = BrainFlowInputParams()
board_id = BoardIds.CROWN_BOARD.value
board = BoardShim(board_id, params)

try:
    board.prepare_session()
    board.start_stream()
    print("BrainFlow board session started successfully.")
except BrainFlowError as e:
    print(f"Error initializing BrainFlow: {e}")
    pygame.quit()
    exit()

# EEG Data Collection
eeg_data = []

# Marker values
marker_value = 0
marker_lock = threading.Lock()

channels = ['1-31', 'CP3', 'C3', 'F5', 'PO3', 'PO4', 'F6', 'C4', 'CP4']

def collect_data():
    global marker_value
    while True:
        try:
            data = board.get_board_data()
            with marker_lock:
                if marker_value != 0:
                    markers = [marker_value] + [0] * (len(data[0]) - 1)
                else:
                    markers = [0] * len(data[0])
                eeg_data.extend(zip(data[0],
                                    data[channels.index('CP3')],
                                    data[channels.index('C3')],
                                    data[channels.index('F5')],
                                    data[channels.index('PO3')],
                                    data[channels.index('PO4')],
                                    data[channels.index('F6')],
                                    data[channels.index('C4')],
                                    data[channels.index('CP4')],
                                    markers))
                marker_value = 0
            time.sleep(0.1)
        except BrainFlowError as e:
            print(f"Error collecting data: {e}")
            break

# Start data collection thread
data_thread = threading.Thread(target=collect_data)
data_thread.start()

# Function to draw stimuli and play beep sound if oddball is displayed
def draw_stimulus(stimulus, letter=None, color=None, size=None, position=None):
    screen.fill(WHITE)
    if stimulus == "plus":
        font = pygame.font.Font(None, 74)
        text = font.render("+", True, BLACK)
        screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, screen.get_height() // 2 - text.get_height() // 2))
    elif stimulus == "blue_circle":
        pygame.draw.circle(screen, BLUE, (screen.get_width() // 2, screen.get_height() // 2), 25)  # Smaller circle
    elif stimulus == "oddball":
        font = pygame.font.Font(None, size)
        text = font.render(letter, True, color)
        screen.blit(text, position)
        beep_sound.play()  # Play the beep sound
    pygame.display.flip()

running = True
flash_time = 0
current_stimulus = "plus"
last_flash_time = pygame.time.get_ticks()
flash_interval = 1000  # Set interval for flashes
blue_duration = 300  # Longer duration for blue circle stimulus
oddball_min_duration = 50  # Minimum duration for oddball stimulus
oddball_max_duration = 200  # Maximum duration for oddball stimulus

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = pygame.time.get_ticks()

    if current_stimulus == "plus" and current_time - last_flash_time > flash_interval:
        rand_value = random.random()
        if rand_value < 0.8:  # 80% chance for blue circle
            current_stimulus = "blue_circle"
            stimulus_duration = blue_duration
            with marker_lock:
                marker_value = 1
            flash_time = current_time
            last_flash_time = current_time
        else:  # 20% chance for oddball letter
            current_stimulus = "oddball"
            stimulus_duration = random.randint(oddball_min_duration, oddball_max_duration)  # Varying duration
            random_index = random.randint(0, 3)
            oddball_letter = letters[random_index]
            oddball_color = colors[random_index]
            oddball_size = random.randint(400, 700)  # Varying sizes
            oddball_x = random.randint(50, screen.get_width() - 150)
            oddball_y = random.randint(50, screen.get_height() - 150)
            oddball_position = (oddball_x, oddball_y)
            with marker_lock:
                marker_value = 2
            flash_time = current_time
            last_flash_time = current_time
    elif current_stimulus in ["oddball", "blue_circle"] and current_time - flash_time > stimulus_duration:
        if current_stimulus == "oddball":
            beep_sound.stop()  # Stop the beep sound after the oddball duration
        current_stimulus = "plus"
        with marker_lock:
            marker_value = 0

    draw_stimulus(current_stimulus, oddball_letter if current_stimulus == "oddball" else None,
                  oddball_color if current_stimulus == "oddball" else None,
                  oddball_size if current_stimulus == "oddball" else None,
                  oddball_position if current_stimulus == "oddball" else None)

# Save the EEG data to a CSV file
with open('rish_nov_19_1.csv', 'w', newline='') as csvfile:  # Change path to your liking
    writer = csv.writer(csvfile)
    writer.writerow(["1-31", "CP3", "C3", "F5", "PO3", "PO4", "F6", "C4", "CP4", "Marker"])
    writer.writerows(eeg_data)

# Clean up
try:
    board.stop_stream()
    board.release_session()
except BrainFlowError as e:
    print(f"Error stopping BrainFlow session: {e}")

pygame.quit()
