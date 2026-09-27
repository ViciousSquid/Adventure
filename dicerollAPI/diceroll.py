from __future__ import annotations

import json
import logging
import random

from runtime.dice import DiceEngine


class DiceRoller:
    """Legacy compatibility wrapper around the deterministic core dice engine."""

    def __init__(self, save_rolls=False, save_format="txt", rng=None):
        self.save_rolls = save_rolls
        self.save_format = save_format
        self._engine = DiceEngine(rng or random.Random())
        self.last_roll_total = None
        self.last_roll_details = None
        self.last_5_rolls = []
        self.roll_history = []
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())

    def roll_dice(self, dice_notation, target=None, success_outcome=None, failure_outcome=None):
        result = self._engine.roll(dice_notation, target=target)
        data = result.to_dict()

        if target is not None and success_outcome is not None and failure_outcome is not None:
            data["outcome"] = success_outcome if result.success else failure_outcome
            data["outcome"]["roll_result"] = result.total

        self.last_roll_total = result.total
        self.last_roll_details = list(result.individual_rolls)
        self.last_5_rolls.append(data)
        self.last_5_rolls = self.last_5_rolls[-5:]

        if self.save_rolls:
            self.roll_history.append(data)
        return data

    def get_last_roll_total(self):
        return self.last_roll_total

    def get_last_roll_details(self):
        return self.last_roll_details

    def get_last_5_rolls(self):
        return self.last_5_rolls

    def get_roll_history(self):
        return self.roll_history

    def set_roll_history(self, roll_history):
        self.roll_history = list(roll_history)

    def save_last_5_rolls(self):
        path = "last_5_rolls.json" if self.save_format == "json" else "last_5_rolls.txt"
        if self.save_format == "json":
            with open(path, "w", encoding="utf-8") as file:
                json.dump(self.last_5_rolls, file, indent=2)
        else:
            with open(path, "w", encoding="utf-8") as file:
                for index, roll in enumerate(self.last_5_rolls, 1):
                    file.write(f"Result {index}:\n")
                    file.write(f"  Dice Notation: {roll['dice_notation']}\n")
                    file.write(f"  Roll Result: {roll['roll_result']}\n")
                    file.write(f"  Roll Details: {roll['roll_details']}\n\n")

    def roll_with_advantage(self, dice_notation, dice_colour="blue", animate=True):
        a = self.roll_dice(dice_notation)
        b = self.roll_dice(dice_notation)
        return a if a["roll_result"] >= b["roll_result"] else b

    def roll_with_disadvantage(self, dice_notation, dice_colour="blue", animate=True):
        a = self.roll_dice(dice_notation)
        b = self.roll_dice(dice_notation)
        return a if a["roll_result"] <= b["roll_result"] else b

    def get_roll_statistics(self, dice_notation, num_rolls):
        values = [self.roll_dice(dice_notation)["roll_result"] for _ in range(num_rolls)]
        return {
            "dice_notation": dice_notation,
            "num_rolls": num_rolls,
            "average": sum(values) / num_rolls,
            "min": min(values),
            "max": max(values),
        }
