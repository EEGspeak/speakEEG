import pygame
import time
import csv
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
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
letters = ["A", "B", "C", "D"]  # Use any letters you prefer
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

# Get EEG and marker channel indices
eeg_channels = BoardShim.get_eeg_channels(board_id)
marker_channel = BoardShim.get_marker_channel(board_id)

def collect_data():
    while True:
        try:
            data = board.get_board_data()
            if data.shape[1] > 0:
                data = data.T  # Transpose to iterate over samples
                for sample in data:
                    eeg_sample = [sample[ch] for ch in eeg_channels]
                    marker = sample[marker_channel]
                    eeg_sample.append(marker)
                    eeg_data.append(eeg_sample)
            time.sleep(0.05)  # Adjusted sleep time for data collection
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
        screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2,
                           screen.get_height() // 2 - text.get_height() // 2))
    elif stimulus == "blue_circle":
        pygame.draw.circle(screen, BLUE, (screen.get_width() // 2, screen.get_height() // 2), 25)
    elif stimulus == "oddball":
        font = pygame.font.Font(None, size)
        text = font.render(letter, True, color)
        screen.blit(text, position)
        # Play the beep sound only once when the oddball is first displayed
        if not beep_sound.get_num_channels():
            beep_sound.play()
    pygame.display.flip()

# Stimuli settings - Adjusted to slightly slow down the flashing
flash_interval = 300  # Increased interval for slower flashes (was 250)
blue_duration = 200   # Increased duration for blue circle stimulus (was 150)
oddball_min_duration = 50   # Increased minimum duration for oddball stimulus (was 25)
oddball_max_duration = 150  # Increased maximum duration for oddball stimulus (was 100)

# Counters
target_marker_count = 0
non_target_marker_count = 0

# Total number of stimuli to present
total_stimuli = 250  # You can adjust this number as needed
num_target_stimuli = int(0.2 * total_stimuli)
num_non_target_stimuli = total_stimuli - num_target_stimuli

# Generate stimuli sequence
stimuli_sequence = ['oddball'] * num_target_stimuli + ['blue_circle'] * num_non_target_stimuli
random.shuffle(stimuli_sequence)

# For non-target markers, select stimuli to insert markers
non_target_marker_indices = random.sample(
    [i for i, stim in enumerate(stimuli_sequence) if stim == 'blue_circle'],
    num_target_stimuli  # Ensure equal number of markers
)

running = True
current_stimulus_index = 0
flash_time = pygame.time.get_ticks()
current_stimulus = "plus"

# Variables to store oddball properties
oddball_letter = None
oddball_color = None
oddball_size = None
oddball_position = None

while running and current_stimulus_index < len(stimuli_sequence):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = pygame.time.get_ticks()

    if current_stimulus == "plus" and current_time - flash_time > flash_interval:
        stimulus = stimuli_sequence[current_stimulus_index]
        current_stimulus = stimulus
        if stimulus == 'blue_circle':
            stimulus_duration = blue_duration
        else:
            stimulus_duration = random.randint(oddball_min_duration, oddball_max_duration)
            # Randomize oddball properties once when the oddball is first presented
            random_index = random.randint(0, len(letters) - 1)
            oddball_letter = letters[random_index]
            oddball_color = colors[random_index]
            oddball_size = random.randint(200, 400)  # Adjust size as needed
            oddball_x = random.randint(50, screen.get_width() - 150)
            oddball_y = random.randint(50, screen.get_height() - 150)
            oddball_position = (oddball_x, oddball_y)
            beep_sound.stop()  # Ensure the beep sound is not already playing

        # Insert markers
        if stimulus == 'oddball':
            board.insert_marker(2)
            target_marker_count += 1
        elif current_stimulus_index in non_target_marker_indices:
            board.insert_marker(1)
            non_target_marker_count += 1

        flash_time = current_time
        current_stimulus_index += 1

    elif current_stimulus in ["oddball", "blue_circle"] and current_time - flash_time > stimulus_duration:
        if current_stimulus == "oddball":
            beep_sound.stop()  # Stop the beep sound after the oddball duration
            # Reset oddball properties
            oddball_letter = None
            oddball_color = None
            oddball_size = None
            oddball_position = None
        current_stimulus = "plus"
        flash_time = current_time

    draw_stimulus(current_stimulus, oddball_letter, oddball_color, oddball_size, oddball_position)

# Save the EEG data to a CSV file
header = ['EEG Channel {}'.format(ch) for ch in eeg_channels]
header.append('Marker')

with open('AAROOSH_test19.csv', 'w', newline='') as csvfile:  # Change path to your liking
    writer = csv.writer(csvfile)
    writer.writerow(header)
    writer.writerows(eeg_data)

# Clean up
try:
    board.stop_stream()
    board.release_session()
except BrainFlowError as e:
    print(f"Error stopping BrainFlow session: {e}")

pygame.quit()

print(f"Total target markers: {target_marker_count}")
print(f"Total non-target markers: {non_target_marker_count}")
