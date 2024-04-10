from diceroll_enums import DiceColor, AnimationStyle
from diceroll_api import dicerollAPI
from diceroll import DiceRoller
import random
import time
import os
from datetime import datetime
import pygame
import ctypes

class DiceAnimator:
    def __init__(self, window_width=200, window_height=200, dice_image_path="dice_imgs"):
        self.window_width = window_width
        self.window_height = window_height
        self.window = None
        self.dice_image_path = dice_image_path
        self.dice_sets = self.load_dice_sets()
        if not self.dice_sets:
            raise ValueError(f"No dice image sets found in the '{dice_image_path}' directory.")
        self.font = None
        self.animation_speed = 1.0
        self.custom_dice_faces = {}
        self.success_animation = None
        self.failure_animation = None
        self.animation_style = AnimationStyle.SHAKE

    def load_dice_sets(self):
        dice_sets = {}

        today = datetime.today()
        if (today.month == 10 and today.day == 31) or (today.month == 4 and today.day == 1):
            colors = ['bread']
        else:
            colors = [DiceColor.RED, DiceColor.WHITE, DiceColor.BLUE, DiceColor.BLACK]

        for color in colors:
            dice_set = []
            for i in range(1, 7):
                image_path = os.path.join(self.dice_image_path, color, f"dice{i}.jpg")
                if os.path.exists(image_path):
                    dice_set.append(pygame.image.load(image_path))
            if dice_set:
                dice_sets[color] = dice_set

        return dice_sets

    def initialize_pygame(self):
        pygame.init()
        self.font = pygame.font.Font(None, 36)

    def animate_dice_roll(self, dice_notation, dice_color, dice_roller, target=None):
        today = datetime.today()
        if (today.month == 10 and today.day == 31) or (today.month == 4 and today.day == 1):
            dice_color = 'bread'

        if dice_color not in self.dice_sets:
            raise ValueError(f"Invalid dice color: {dice_color}. Available colors are: {', '.join(self.dice_sets.keys())}")

        self.initialize_pygame()

        # Set the window to be always on top and bring it to the front
        self.window = pygame.display.set_mode((self.window_width, self.window_height), pygame.HWSURFACE | pygame.NOFRAME)
        self.window.set_alpha(None)
        pygame.display.set_caption("Dice Roll")
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{(pygame.display.Info().current_w - self.window_width) // 2},{(pygame.display.Info().current_h - self.window_height) // 2}"
        pygame.display.set_mode((self.window_width, self.window_height), pygame.HWSURFACE | pygame.NOFRAME)

        # Set the window as topmost using ctypes
        hwnd = pygame.display.get_wm_info()['window']
        ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0008)

        clock = pygame.time.Clock()
        shake_duration = 2.00 / self.animation_speed
        tumble_duration = 0.50 / self.animation_speed

        dice_and_target_text = f"{dice_notation}"
        if target:
            dice_and_target_text += f"-{target}"
        dice_and_target_render = self.font.render(dice_and_target_text, True, (0, 0, 0))
        dice_and_target_rect = dice_and_target_render.get_rect(midtop=(self.window_width // 2, 10))

        start_time = time.time()
        while time.time() - start_time < shake_duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            self.window.fill((255, 255, 255))

            self.window.blit(dice_and_target_render, dice_and_target_rect)

            if dice_notation in self.custom_dice_faces:
                dice_image = random.choice(self.custom_dice_faces[dice_notation])
            else:
                dice_image = random.choice(self.dice_sets[dice_color])
            dice_rect = dice_image.get_rect(center=(self.window_width // 2, self.window_height // 2))

            if self.animation_style == AnimationStyle.SHAKE:
                rotation_angle = random.randint(-5, 5)
                offset_x = random.randint(-5, 5)
                offset_y = random.randint(-5, 5)
                rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
                rotated_dice_rect = rotated_dice_image.get_rect(center=(self.window_width // 2 + offset_x, self.window_height // 2 + offset_y))
                self.window.blit(rotated_dice_image, rotated_dice_rect)
            elif self.animation_style == AnimationStyle.TUMBLE:
                rotation_angle = (time.time() - start_time) / tumble_duration * 360
                rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
                rotated_dice_rect = rotated_dice_image.get_rect(center=(self.window_width // 2, self.window_height // 2))
                self.window.blit(rotated_dice_image, rotated_dice_rect)
            elif self.animation_style == AnimationStyle.SPIN:
                rotation_angle = (time.time() - start_time) / shake_duration * 360
                rotated_dice_image = pygame.transform.rotate(dice_image, rotation_angle)
                rotated_dice_rect = rotated_dice_image.get_rect(center=(self.window_width // 2, self.window_height // 2))
                self.window.blit(rotated_dice_image, rotated_dice_rect)

            pygame.display.flip()
            clock.tick(30)

        roll_result = dice_roller.roll_dice(dice_notation)

        roll_details = dice_roller.get_last_roll_details()
        single_roll_result = roll_details[0]

        self.window.fill((255, 255, 255))

        self.window.blit(dice_and_target_render, dice_and_target_rect)

        if dice_notation in self.custom_dice_faces:
            final_dice_image = self.custom_dice_faces[dice_notation][single_roll_result - 1]
        else:
            try:
                final_dice_image = self.dice_sets[dice_color][single_roll_result - 1]
            except IndexError:
                final_dice_image = self.dice_sets[dice_color][0]
        final_dice_rect = final_dice_image.get_rect(center=(self.window_width // 2, self.window_height // 2))
        self.window.blit(final_dice_image, final_dice_rect)

        result_text = self.font.render(f"Result: {roll_result['roll_result']}", True, (0, 0, 0))
        result_rect = result_text.get_rect(midbottom=(self.window_width // 2, self.window_height - 10))
        self.window.blit(result_text, result_rect)

        if target:
            if roll_result['roll_result'] >= target and self.success_animation:
                self.success_animation()
            elif roll_result['roll_result'] < target and self.failure_animation:
                self.failure_animation()

        pygame.display.flip()

        pygame.time.delay(3000)

        # Print roll result with indentation
        print("\t" + str(roll_result))

        return roll_result

    def run_animation(self, dice_notation, dice_color=DiceColor.BLUE, target=None, save_rolls=False):
        today = datetime.today()
        if (today.month == 10 and today.day == 31) or (today.month == 4 and today.day == 1):
            dice_color = 'bread'

        available_colors = dicerollAPI().get_available_dice_colors()
        if dice_color not in available_colors:
            raise ValueError(f"Invalid dice color: {dice_color}. Available colors are: {', '.join(available_colors)}")

        dice_roller = DiceRoller(save_rolls=save_rolls)
        roll_result = self.animate_dice_roll(dice_notation, dice_color, dice_roller, target)
        return roll_result

    def set_window_size(self, width, height):
        self.window_width = width
        self.window_height = height

    def set_dice_image_path(self, path):
        self.dice_image_path = path
        self.dice_sets = self.load_dice_sets()

    def set_animation_style(self, style):
        self.animation_style = style

    def set_animation_speed(self, speed):
        self.animation_speed = speed

    def set_custom_dice_faces(self, dice_notation, face_images):
        self.custom_dice_faces[dice_notation] = face_images

    def set_target_success_failure_animations(self, success_animation, failure_animation):
        self.success_animation = success_animation
        self.failure_animation = failure_animation