from __future__ import annotations

from .diceroll import DiceRoller


class dicerollAPI:
    """Legacy facade; new narrative execution uses runtime.dice directly."""

    def __init__(self, save_rolls=False, log_console=None):
        self.dice_roller = DiceRoller(save_rolls=save_rolls)

    def roll_dice(self, dice_notation, dice_color="white", target_value=None, **_kwargs):
        return self.dice_roller.roll_dice(dice_notation, target=target_value)

    def roll_single_dice(self, dice_type, dice_color="white"):
        return self.roll_dice(dice_type, dice_color=dice_color)

    def roll_multiple_dice_of_same_type(self, dice_type, num_dice, dice_color="white"):
        return self.roll_dice(f"{num_dice}{dice_type}", dice_color=dice_color)

    def roll_multiple_dice(self, dice_notations, dice_colors=None, target_values=None):
        targets = target_values or [None] * len(dice_notations)
        return [
            self.roll_dice(expression, target_value=targets[index])
            for index, expression in enumerate(dice_notations)
        ]

    def get_roll_sum(self, roll_result):
        return sum(roll_result["roll_details"])

    def get_roll_average(self, roll_result):
        details = roll_result["roll_details"]
        return sum(details) / len(details)

    def get_roll_max(self, roll_result):
        return max(roll_result["roll_details"])

    def get_roll_min(self, roll_result):
        return min(roll_result["roll_details"])

    def get_roll_statistics(self, dice_notation, num_rolls):
        return self.dice_roller.get_roll_statistics(dice_notation, num_rolls)

    def get_last_roll_total(self):
        return self.dice_roller.get_last_roll_total()

    def get_last_roll_details(self):
        return self.dice_roller.get_last_roll_details()

    def get_last_5_rolls(self):
        return self.dice_roller.get_last_5_rolls()
