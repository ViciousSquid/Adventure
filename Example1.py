from diceroll_api import dicerollAPI
from diceroll_enums import DiceColor

print("\n++ diceroll demo")

# Create a dicerollAPI instance
dice_api = dicerollAPI()



# Enable roll saving
dice_api.enable_roll_saving()
# This will save the last 5 roll results to a file named "last_5_rolls.txt"



# Roll 2d6 dice
print("\n++ Rolling 2d6...")
# This will roll two six-sided dice and return the result
result = dice_api.roll_dice("2d6", dice_color=DiceColor.RED)
print("2d6 Roll Result:")
print(result)



# Roll 1d20 dice with blue color
print("\n++ Rolling 1d20...")
# This will roll one blue twenty-sided die and return the result
result = dice_api.roll_dice("1d20", dice_color=DiceColor.BLUE)
print("\n1d20 Roll Result (Blue):")
print(result)




# Roll 3d8+1d4 dice
print("\n++ Rolling 3d8+1d4...")
# This will roll three eight-sided dice and one four-sided die, and return the total sum
result = dice_api.roll_dice("3d8+1d4")
print("\n3d8+1d4 Roll Result:")
print(result)



# Roll 2d10 green dice with a target of 15
print("\n++ Rolling 2d10 with a target of 15...")
# This will roll two ten-sided dice and compare the result against the target value of 15
# If the roll result is greater than or equal to 15, it will be considered a success
# Otherwise, it will be considered a failure
result = dice_api.roll_dice("2d10", dice_color=DiceColor.GREEN)
print("\n2d10 Roll Result (Target: 15):")
print(result)
if result["roll_result"] >= 15:
    print("Success!")
else:
    print("Failure.")



# Get the last 5 roll results
# This will retrieve the last 5 roll results saved by the DiceRoller
last_5_rolls = dice_api.get_last_5_rolls()
print("\nLast 5 Roll Results:")
for i, roll_data in enumerate(last_5_rolls, 1):
    print(f"Result {i}:")
    print(f"  Dice Notation: {roll_data['dice_notation']}")
    print(f"  Roll Result: {roll_data['roll_result']}")
    print(f"  Roll Details: {roll_data['roll_details']}")



# Disable roll saving
# This will stop saving the roll results to the file
dice_api.disable_roll_saving()


# Roll 1d6 dice
print("\n++ Rolling 1d6...")
# This roll result will not be saved to the file
result = dice_api.roll_dice("1d6")
print("\n1d6 Roll Result (Not Saved):")
print(result)





# Get the available dice colors
# This will retrieve the list of available dice colors for the dice animation
available_colors = dice_api.get_available_dice_colors()
print("\nAvailable Dice Colors:")
print(available_colors)