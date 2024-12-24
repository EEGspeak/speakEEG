import time
import random
import pygame

# Constants
N_KEYS = 36
FLASH_DURATION = 0.3  # 300 milliseconds
FRAMERATE_CAP = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Training phrase
TRAINING_PHRASE = "HELLOWORLD"

def Start_GUI():
    pygame.init()

    # Set up the display to get the screen size
    info = pygame.display.Info()
    screen_width = info.current_w
    screen_height = info.current_h

    # Set up scaling factors based on screen resolution
    key_width = screen_width // 12
    key_height = key_width

    # Set up the display with fullscreen mode
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("P300 Speller GUI")

    # Set up font with dynamic size
    font_size = key_width // 2
    font = pygame.font.SysFont('Calibri', font_size, True, False)

    # Initialize keys
    keys = [None] * N_KEYS

    def Init_Keys():
        # Create a list of all the characters to be displayed
        characters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

        for i, char in enumerate(characters):
            row = i // 6
            col = i % 6
            x = col * key_width + (screen_width - 6 * key_width) // 2
            y = row * key_height + (screen_height - 6 * key_height) // 2

            txt = font.render(char, True, WHITE)
            txt_size = font.size(char)
            keys[i] = (char, txt, [x, y], False, [x + (key_width - txt_size[0]) / 2, y + (key_height - txt_size[1]) / 2])

    def draw_keys():
        screen.fill(BLACK)
        for key in keys:
            label, txt, pos, _, text_pos = key
            x, y = pos
            pygame.draw.rect(screen, WHITE, [x, y, key_width, key_height], 2)
            screen.blit(txt, text_pos)

    def flash_random_row():
        row_index = random.randint(0, 5)
        for col in range(6):
            idx = row_index * 6 + col
            label, txt, pos, _, text_pos = keys[idx]
            x, y = pos
            pygame.draw.rect(screen, RED, [x, y, key_width, key_height], 2)
            screen.blit(txt, text_pos)
        print(f"Flashing row: {row_index}")

    def flash_random_column():
        col_index = random.randint(0, 5)
        for row in range(6):
            idx = row * 6 + col_index
            label, txt, pos, _, text_pos = keys[idx]
            x, y = pos
            pygame.draw.rect(screen, RED, [x, y, key_width, key_height], 2)
            screen.blit(txt, text_pos)
        print(f"Flashing column: {col_index}")

    Init_Keys()
    clock = pygame.time.Clock()
    running = True

    next_flash_time = time.time() + FLASH_DURATION
    flash_type = random.choice([True, False])  # True for row, False for column

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        current_time = time.time()

        if current_time >= next_flash_time:
            next_flash_time = current_time + FLASH_DURATION
            draw_keys()

            # Randomly choose to flash a row or column
            if random.randint(0, 1) == 0:
                flash_random_row()
            else:
                flash_random_column()

            pygame.display.flip()

        clock.tick(FRAMERATE_CAP)

    pygame.quit()

if __name__ == "__main__":
    Start_GUI()