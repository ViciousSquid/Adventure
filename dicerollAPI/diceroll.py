import random
import logging
import re
from collections import defaultdict
import os

print("+ diceroll engine 105")

class DiceRoller:
    def __init__(self, save_rolls=False, save_format="txt"):
        self.last_roll_total = None
        self.last_roll_details = None
        self.last_5_rolls = []
        self.save_rolls = save_rolls
        self.roll_history = []
        self.save_format = save_format
        self.log_formatter = logging.Formatter('%(asctime)s\t%(message)s', '%Y-%m-%d %H:%M:%S')
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        log_file = os.path.join(logs_dir, 'diceroll.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(self.log_formatter)
        self.logger.addHandler(file_handler)

    def roll_dice(self, dice_notation, target=None, success_outcome=None, failure_outcome=None):
        self.last_roll_total = None
        self.last_roll_details = None
        roll_results = []
        roll_sum = 0

        components = re.split(r'(\d+d\d+)', dice_notation)
        for component in components:
            if component.startswith('+'):
                component = component[1:]
            match = re.match(r"(\d+)d(\d+)", component)
            if match:
                number_of_dice, dice_size = int(match.group(1)), int(match.group(2))
                component_results = [random.randint(1, dice_size) for _ in range(number_of_dice)]
                roll_results.extend(component_results)
                roll_sum += sum(component_results)
                self.logger.info(f"\t{match.group(0)}: {', '.join(map(str, component_results))}")
            elif component.strip():
                raise ValueError(f"Invalid dice notation: {component}")

        roll_data = {
            "dice_notation": dice_notation,
            "roll_result": roll_sum,
            "roll_details": roll_results
        }

        if target is not None:
            if success_outcome is None or failure_outcome is None:
                raise ValueError("Success and failure outcome details must be provided when target is specified.")
            if roll_sum >= target:
                outcome = success_outcome
            else:
                outcome = failure_outcome
            outcome["roll_result"] = roll_sum
            roll_data["outcome"] = outcome

        self.last_5_rolls.append(roll_data)
        self.last_5_rolls = self.last_5_rolls[-5:]

        if self.save_rolls:
            self.roll_history.append(roll_data)
            self.save_last_5_rolls()

        if not self.last_roll_total:
            self.last_roll_total = roll_sum
            self.last_roll_details = roll_results

        self.logger.info(f"\tTotal: {roll_sum}")
        return roll_data

    def get_last_roll_total(self):
        return self.last_roll_total

    def get_last_roll_details(self):
        return self.last_roll_details

    def get_last_5_rolls(self):
        return self.last_5_rolls

    def get_roll_history(self):
        return self.roll_history

    def set_roll_history(self, roll_history):
        self.roll_history = roll_history

    def save_last_5_rolls(self):
        if self.save_format == "json":
            self.save_last_5_rolls_json()
        else:
            self.save_last_5_rolls_txt()

    def save_last_5_rolls_txt(self):
        with open("last_5_rolls.txt", "w") as file:
            for i, roll_data in enumerate(self.last_5_rolls, 1):
                file.write(f"Result {i}:\n")
                file.write(f"  Dice Notation: {roll_data['dice_notation']}\n")
                file.write(f"  Roll Result: {roll_data['roll_result']}\n")
                file.write(f"  Roll Details: {roll_data['roll_details']}\n")
                file.write("\n")

    def save_last_5_rolls_json(self):
        with open("last_5_rolls.json", "w") as file:
            json.dump(self.last_5_rolls, file, indent=2)

    def get_roll_statistics(self, dice_notation, num_rolls):
        roll_results = []
        for _ in range(num_rolls):
            roll_data = self.roll_dice(dice_notation)
            roll_results.append(roll_data["roll_result"])

        statistics = {
            "dice_notation": dice_notation,
            "num_rolls": num_rolls,
            "average": sum(roll_results) / num_rolls,
            "min": min(roll_results),
            "max": max(roll_results),
            "frequency": self.calculate_frequency(roll_results)
        }
        return statistics

    def calculate_frequency(self, roll_results):
        frequency = defaultdict(int)
        for result in roll_results:
            frequency[result] += 1
        return dict(frequency)

    def roll_with_advantage(self, dice_notation, dice_colour='blue', animate=True):
        roll_data_1 = self.roll_dice(dice_notation)
        roll_data_2 = self.roll_dice(dice_notation)
        if roll_data_1["roll_result"] >= roll_data_2["roll_result"]:
            return roll_data_1
        else:
            return roll_data_2

    def roll_with_disadvantage(self, dice_notation, dice_colour='blue', animate=True):
        roll_data_1 = self.roll_dice(dice_notation)
        roll_data_2 = self.roll_dice(dice_notation)
        if roll_data_1["roll_result"] <= roll_data_2["roll_result"]:
            return roll_data_1
        else:
            return roll_data_2

    def get_dice_probabilities(self, dice_notation):
        match = re.match(r"(\d+)d(\d+)", dice_notation)
        if not match:
            raise ValueError(f"Invalid dice notation: {dice_notation}")

        number_of_dice, dice_size = int(match.group(1)), int(match.group(2))

        probabilities = {}
        for i in range(number_of_dice, number_of_dice * dice_size + 1):
            probability = self.calculate_probability(i, number_of_dice, dice_size)
            probabilities[i] = probability

        return probabilities

    def calculate_probability(self, target_sum, number_of_dice, dice_size):
        if target_sum < number_of_dice or target_sum > number_of_dice * dice_size:
            return 0

        table = [[0] * (number_of_dice * dice_size + 1) for _ in range(number_of_dice + 1)]
        table[0][0] = 1

        for i in range(1, number_of_dice + 1):
            for j in range(i, i * dice_size + 1):
                table[i][j] = sum(table[i - 1][j - k] for k in range(1, min(j, dice_size) + 1))

        total_combinations = dice_size ** number_of_dice
        favorable_combinations = table[number_of_dice][target_sum]
        probability = favorable_combinations / total_combinations

        return probability