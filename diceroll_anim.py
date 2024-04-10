import ctypes
import pygame
import pygame.display
import base64
from diceroll_enums import DiceColor, AnimationStyle
import math

try:
    from diceroll_anim import DiceAnimator
except ImportError:
    DiceAnimator = None

from diceroll import DiceRoller
from datetime import datetime
import json
import random
import time
import os
import sys
from io import BytesIO

try:
    import pygame
    pygame_available = True
except ImportError:
    pygame_available = False

class Logger(object):
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log = open(log_file, 'a')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

class DiceType:
    D4 = "d4"
    D6 = "d6"
    D8 = "d8"
    D10 = "d10"
    D12 = "d12"
    D20 = "d20"

class dicerollAPI:
    def __init__(self, save_rolls=False, log_console=None):
        self.dice_roller = DiceRoller(save_rolls=save_rolls)
        if DiceAnimator is not None:
            self.dice_animator = DiceAnimator()
        else:
            self.dice_animator = None

        if log_console is None:
            log_console = os.path.exists("debug.txt")

        self.log_console = log_console
        if self.log_console:
            logs_dir = 'logs'
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)

            current_datetime = datetime.now().strftime("%d%m_%H%M")
            log_file = os.path.join(logs_dir, f'diceroll_log_{current_datetime}.txt')

            sys.stdout = Logger(log_file)
            sys.stderr = Logger(log_file)

    def set_animation_window_size(self, width=200, height=200):
        if self.dice_animator is not None:
            self.dice_animator.set_window_size(width, height)

    def set_dice_image_path(self, path="dice_imgs"):
        if self.dice_animator is not None:
            self.dice_animator.set_dice_image_path(path)

    def roll_dice(self, dice_notation, dice_color=DiceColor.WHITE, target_value=None, animate=True):
        try:
            roll_result = self.dice_roller.roll_dice(dice_notation)
            if animate and pygame_available:
                self.animate_dice_roll(dice_notation)
            elif animate and not pygame_available:
                print("Pygame is not available. Skipping animation.")

            # Set console text color based on dice_color
            if dice_color == DiceColor.RED:
                console_color = '\033[91m'  # Red
            elif dice_color == DiceColor.BLUE:
                console_color = '\033[94m'  # Light blue
            elif dice_color == DiceColor.GREEN:
                console_color = '\033[92m'  # Green
            elif dice_color == DiceColor.BLACK:
                console_color = '\033[97m'  # White (for visibility)
            elif dice_color == 'bread':
                console_color = '\033[97m'  # White (default) for 'bread' color
            else:
                console_color = '\033[97m'  # White (default)

            print(f"{console_color}Dice Notation: {dice_notation}")
            print(f"Roll Result: {roll_result['roll_result']}")
            print(f"Roll Details: {roll_result['roll_details']}\033[0m")  # Reset color

            return roll_result
        except ValueError as e:
            print(f"\033[91mInvalid dice notation: {dice_notation}. Error: {str(e)}\033[0m")
            return None

    def roll_single_dice(self, dice_type, dice_color=DiceColor.WHITE, animate=True):
        return self.roll_dice(dice_type, dice_color=dice_color, animate=animate)

    def roll_multiple_dice_of_same_type(self, dice_type, num_dice, dice_color=DiceColor.WHITE, animate=True):
        dice_notation = f"{num_dice}{dice_type}"
        return self.roll_dice(dice_notation, dice_color=dice_color, animate=animate)

    def roll_multiple_dice(self, dice_notations, dice_colors=None, target_values=None, animate=True):
        if dice_colors is None:
            dice_colors = [DiceColor.WHITE] * len(dice_notations)
        if target_values is None:
            target_values = [None] * len(dice_notations)

        roll_results = []
        for i, dice_notation in enumerate(dice_notations):
            roll_result = self.roll_dice(dice_notation, dice_color=dice_colors[i], target_value=target_values[i], animate=animate)
            roll_results.append(roll_result)
        return roll_results

    def get_roll_sum(self, roll_result):
        return sum(roll_result['roll_details'])

    def get_roll_average(self, roll_result):
        roll_details = roll_result['roll_details']
        return sum(roll_details) / len(roll_details)

    def get_roll_max(self, roll_result):
        return max(roll_result['roll_details'])

    def get_roll_min(self, roll_result):
        return min(roll_result['roll_details'])

    def get_roll_statistics(self, dice_notation, num_rolls):
        return self.dice_roller.get_roll_statistics(dice_notation, num_rolls)

    def save_roll_history_to_file(self, file_path):
        roll_history = self.dice_roller.get_roll_history()
        with open(file_path, 'w') as file:
            json.dump(roll_history, file)

    def load_roll_history_from_file(self, file_path):
        with open(file_path, 'r') as file:
            roll_history = json.load(file)
        self.dice_roller.set_roll_history(roll_history)
        return roll_history

    def get_last_roll_total(self):
        return self.dice_roller.get_last_roll_total()

    def get_last_roll_details(self):
        return self.dice_roller.get_last_roll_details()

    def get_last_5_rolls(self):
        return self.dice_roller.get_last_5_rolls()

    def get_available_dice_colors(self):
        return [color_value for color_name, color_value in DiceColor.__dict__.items() if not color_name.startswith("__")]

    def enable_roll_saving(self):
        self.dice_roller.save_rolls = True

    def disable_roll_saving(self):
        self.dice_roller.save_rolls = False

    def set_animation_style(self, style=AnimationStyle.SHAKE):
        self.dice_animator.set_animation_style(style)

    def roll_saving_throw(self, dice_type=DiceType.D20, dice_color=DiceColor.WHITE, target_value=None, success_threshold=None, animate=True):
        if success_threshold is None:
            success_threshold = target_value

        roll_result = self.roll_dice(dice_type, dice_color=dice_color, target_value=target_value, animate=animate)

        if roll_result is not None:
            success = roll_result['roll_result'] >= success_threshold
            roll_result['success'] = success

        return roll_result

    def roll_multiple_saving_throws(self, num_throws, dice_type=DiceType.D20, dice_color=DiceColor.WHITE, target_values=None, success_thresholds=None, animate=True):
        if target_values is None:
            target_values = [None] * num_throws
        if success_thresholds is None:
            success_thresholds = target_values

        saving_throw_results = []
        for i in range(num_throws):
            saving_throw_result = self.roll_saving_throw(dice_type, dice_color=dice_color, target_value=target_values[i], success_threshold=success_thresholds[i], animate=animate)
            saving_throw_results.append(saving_throw_result)

        return saving_throw_results

    def enable_console_logging(self):
        self.log_console = True
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        current_datetime = datetime.now().strftime("%d%m_%H%M")
        log_file = os.path.join(logs_dir, f'diceroll_log_{current_datetime}.txt')

        sys.stdout = Logger(log_file)
        sys.stderr = Logger(log_file)

    def disable_console_logging(self):
        self.log_console = False
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

class DiceAnimator:
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

    def __init__(self, window_width=200, window_height=270, dice_image_path="dice_imgs"):
        self.window_width = window_width
        self.window_height = window_height
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

    def display_shake_animation(self, surface, dice_images, roll_results, start_time, animation_duration):
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - start_time) / 1000  # Convert milliseconds to seconds
        shake_magnitude = 5 * math.sin(elapsed_time * 10)  # Adjust the magnitude and frequency of the shake as desired

        surface.fill((255, 255, 255))  # Fill the surface with white

        offset_x = 50  # Offset to move the dice images 50 pixels to the left

        for i, result in enumerate(roll_results):
            dice_image = dice_images[result - 1]
            x = surface.get_width() // 2 + shake_magnitude - i * dice_image.get_width() * 1.2 - offset_x
            y = surface.get_height() // 2
            surface.blit(dice_image, (x, y))

    def display_tumble_animation(self, surface, dice_images, roll_results, start_time, animation_duration):
        elapsed_time = (pygame.time.get_ticks() - start_time) / 1000  # Convert milliseconds to seconds
        tumble_speed = 360 / animation_duration  # Degrees per second
        tumble_angle = elapsed_time * tumble_speed

        surface.fill((255, 255, 255))  # Fill the surface with white

        offset_x = 50  # Offset to move the dice images 50 pixels to the left

        for i, result in enumerate(roll_results):
            dice_image = dice_images[result - 1]
            x = surface.get_width() // 2 - i * dice_image.get_width() * 1.2 - offset_x
            y = surface.get_height() // 2
            rotated_image = pygame.transform.rotate(dice_image, tumble_angle)
            rotated_rect = rotated_image.get_rect(center=(x, y))
            surface.blit(rotated_image, rotated_rect)

    def display_spin_animation(self, surface, dice_images, roll_results, start_time, animation_duration):
        elapsed_time = (pygame.time.get_ticks() - start_time) / 1000  # Convert milliseconds to seconds
        spin_speed = 360 / animation_duration  # Degrees per second
        spin_angle = elapsed_time * spin_speed

        surface.fill((255, 255, 255))  # Fill the surface with white

        offset_x = 50  # Offset to move the dice images 50 pixels to the left

        for i, result in enumerate(roll_results):
            dice_image = dice_images[result - 1]
            x = surface.get_width() // 2 - i * dice_image.get_width() * 1.2 - offset_x
            y = surface.get_height() // 2
            rotated_image = pygame.transform.rotate(dice_image, spin_angle)
            rotated_rect = rotated_image.get_rect(center=(x, y))
            surface.blit(rotated_image, rotated_rect)

    def animate_dice_roll(self, dice_notation, dice_color, dice_roller):
        # Initialize Pygame
        pygame.init()

        # Create a surface for rendering the animation
        surface = pygame.Surface((self.window_width, self.window_height))

        # Load dice images
        dice_images = self.dice_sets[dice_color]

        # Set up the clock
        clock = pygame.time.Clock()

        # Perform the dice roll
        num_dice = int(dice_notation.split("d")[0])
        roll_results = [random.randint(1, 6) for _ in range(num_dice)]
        roll_sum = sum(roll_results)

        # Animation loop
        start_time = pygame.time.get_ticks()
        animation_duration = 1000  # Animation duration in milliseconds
        frames = []

        while pygame.time.get_ticks() - start_time < animation_duration:
            # Clear the surface
            surface.fill((255, 255, 255))

            # Display the dice roll animation
            if self.animation_style == AnimationStyle.SHAKE:
                self.display_shake_animation(surface, dice_images, roll_results, start_time, animation_duration)
            elif self.animation_style == AnimationStyle.TUMBLE:
                self.display_tumble_animation(surface, dice_images, roll_results, start_time, animation_duration)
            elif self.animation_style == AnimationStyle.SPIN:
                self.display_spin_animation(surface, dice_images, roll_results, start_time, animation_duration)

            # Convert the surface to an image data URI and add it to the frames list
            image_data = pygame.image.tostring(surface, "RGB")
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            frame_uri = f"data:image/png;base64,{image_base64}"
            frames.append(frame_uri)

            # Update the clock
            clock.tick(60)

        pygame.quit()
        print(f"\t{{'roll_result': {roll_sum}, 'roll_details': {roll_results}}}")

        return frames