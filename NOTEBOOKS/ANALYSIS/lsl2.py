import time
import random
import pygame

# Constants
N_KEYS = 36
N_KEYS_PER_FLASH = 6
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
            keys[i] = (
            char, txt, [x, y], False, [x + (key_width - txt_size[0]) / 2, y + (key_height - txt_size[1]) / 2])

    def draw_keys():
        screen.fill(BLACK)
        for key in keys:
            label, txt, pos, _, text_pos = key
            x, y = pos
            pygame.draw.rect(screen, WHITE, [x, y, key_width, key_height], 2)
            screen.blit(txt, text_pos)

    def flash_keys(flash_rows, flash_cols):
        for row in flash_rows:
            for col in range(6):
                idx = row * 6 + col
                label, txt, pos, _, text_pos = keys[idx]
                x, y = pos
                pygame.draw.rect(screen, RED, [x, y, key_width, key_height], 2)
                screen.blit(txt, text_pos)

        for col in flash_cols:
            for row in range(6):
                idx = row * 6 + col
                label, txt, pos, _, text_pos = keys[idx]
                x, y = pos
                pygame.draw.rect(screen, RED, [x, y, key_width, key_height], 2)
                screen.blit(txt, text_pos)

    Init_Keys()
    clock = pygame.time.Clock()
    running = True
    last_flash_time = time.time()

    training_index = 0
    training_mode = True
    training_start_time = time.time()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        current_time = time.time()
        if training_mode:
            if current_time - training_start_time > FLASH_DURATION:
                training_start_time = current_time
                draw_keys()

                # Highlight the current training character
                current_char = TRAINING_PHRASE[training_index]
                current_char_idx = [i for i, key in enumerate(keys) if key[0] == current_char][0]
                row, col = divmod(current_char_idx, 6)
                flash_keys([row], [col])

                pygame.display.flip()
                training_index = (training_index + 1) % len(TRAINING_PHRASE)
        else:
            if current_time - last_flash_time > FLASH_DURATION:
                last_flash_time = current_time
                draw_keys()
                flash_rows = random.sample(range(6), N_KEYS_PER_FLASH // 2)
                flash_cols = random.sample(range(6), N_KEYS_PER_FLASH // 2)
                flash_keys(flash_rows, flash_cols)
                pygame.display.flip()

        clock.tick(FRAMERATE_CAP)

    pygame.quit()


if __name__ == "__main__":
    Start_GUI()