"""
TODO lower chance for oddball
! 0: no red OR blue
! 1: red + (not oddball)
! 2: blue (oddball)
"""


import pygame
import time
import csv
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations
import threading
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("P300 Data Collector")

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Initialize BrainFlow
params = BrainFlowInputParams()
board_id = BoardIds.CROWN_BOARD.value
board = BoardShim(board_id, params)
board.prepare_session()
board.start_stream()

# EEG Data Collection
eeg_data = []

# Marker values
marker_value = 0
marker_lock = threading.Lock()

channels = ['1-31', 'CP3', 'C3', 'F5', 'PO3', 'PO4', 'F6', 'C4', 'CP4']

def collect_data():
    global marker_value
    while True:
        data = board.get_board_data()
        with marker_lock:
            markers = [marker_value] * len(data[0])
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
        time.sleep(0.1)

# Start data collection thread
data_thread = threading.Thread(target=collect_data)
data_thread.start()

# Function to draw stimuli
def draw_stimulus(stimulus):
    screen.fill(WHITE)
    if stimulus == "plus":
        font = pygame.font.Font(None, 74)
        text = font.render("+", True, BLACK)
        screen.blit(text, (375, 275))
    elif stimulus == "blue_circle":
        pygame.draw.circle(screen, BLUE, (400, 300), 100)
    elif stimulus == "red_x":
        font = pygame.font.Font(None, 200)
        text = font.render("X", True, RED)
        screen.blit(text, (300, 200))
    pygame.display.flip()

running = True
flash_time = 0
current_stimulus = "plus"
last_flash_time = pygame.time.get_ticks()
flash_interval = 1000

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = pygame.time.get_ticks()

    if current_stimulus == "plus" and current_time - last_flash_time > flash_interval:
        if random.random() < 0.5:  # 50% chance to flash a blue circle or red X
            if random.random() < 0.2: #! made it 20% chance of being a blue circle
                current_stimulus = "blue_circle"
                with marker_lock:
                    marker_value = 2
            else:
                current_stimulus = "red_x"
                with marker_lock:
                    marker_value = 1
            flash_time = current_time
            last_flash_time = current_time
        else:
            with marker_lock:
                marker_value = 0
    elif current_stimulus in ["blue_circle", "red_x"] and current_time - flash_time > 300:
        current_stimulus = "plus"
        with marker_lock:
            marker_value = 0

    draw_stimulus(current_stimulus)

# Save the EEG data to a CSV file
with open('eeg_data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["1-31", "CP3", "C3", "F5", "PO3", "PO4", "F6", "C4", "CP4", "Marker"])
    writer.writerows(eeg_data)

# Clean up
board.stop_stream()
board.release_session()
pygame.quit()