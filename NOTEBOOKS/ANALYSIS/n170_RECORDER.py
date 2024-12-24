import pygame
import time
import csv
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations
import threading
import random

pygame.init()

screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("N170 Data Collector")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

faces = [pygame.image.load(f"face{i}.png") for i in range(1, 6)]  # Load face1.png to face5.png
non_faces = [pygame.image.load(f"non_face{i}.png") for i in range(1, 6)]  # Load nonface1.png to nonface5.png

faces = [pygame.transform.scale(face, (200, 200)) for face in faces]
non_faces = [pygame.transform.scale(non_face, (200, 200)) for non_face in non_faces]

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

eeg_data = []

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

data_thread = threading.Thread(target=collect_data)
data_thread.start()

def draw_stimulus(image):
    screen.fill(WHITE)
    screen.blit(image, (screen.get_width() // 2 - image.get_width() // 2, 
                        screen.get_height() // 2 - image.get_height() // 2))
    pygame.display.flip()

running = True
flash_time = 0
last_flash_time = pygame.time.get_ticks()
stimulus_duration = 500
interstimulus_interval = 1000

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = pygame.time.get_ticks()

    if current_time - last_flash_time > interstimulus_interval:
        rand_value = random.random()
        if rand_value < 0.5:
            face_index = random.randint(0, 4)
            with marker_lock:
                marker_value = 2
            draw_stimulus(faces[face_index])
        else:
            non_face_index = random.randint(0, 4)
            with marker_lock:
                marker_value = 1
            draw_stimulus(non_faces[non_face_index])

        flash_time = current_time
        last_flash_time = current_time

    if current_time - flash_time > stimulus_duration:
        screen.fill(WHITE)
        pygame.display.flip()
        with marker_lock:
            marker_value = 0

with open('data_master/neurosity/visual-n170/N170_RISH_3.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["1-31", "CP3", "C3", "F5", "PO3", "PO4", "F6", "C4", "CP4", "Marker"])
    writer.writerows(eeg_data)

try:
    board.stop_stream()
    board.release_session()
except BrainFlowError as e:
    print(f"Error stopping BrainFlow session: {e}")

pygame.quit()
