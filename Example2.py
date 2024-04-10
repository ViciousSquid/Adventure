from diceroll_api import dicerollAPI
from diceroll_enums import DiceColor

# Create a dicerollAPI instance
dice_api = dicerollAPI()

# Roll 2d6 dice with one blue and one green
result = dice_api.roll_multiple_dice(["1d6", "1d6"], dice_colors=[DiceColor.BLUE, DiceColor.GREEN])
print("\n2d6 Roll Result (Blue and Green):")

# Set the console color for the first (blue) die
print('\033[94m', end='')
print(f"Dice 1: {result[0]['roll_result']}")
print('\033[0m', end='')  # Reset the color

# Set the console color for the second (green) die
print('\033[92m', end='')
print(f"Dice 2: {result[1]['roll_result']}")
print('\033[0m', end='')  # Reset the color

print(f"Total: {sum(result[0]['roll_result'] + result[1]['roll_result'])}")