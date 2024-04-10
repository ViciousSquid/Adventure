Here's a simple example of how to call the API for a saving throw:

```python
from diceroll_api import dicerollAPI, DiceType, DiceColor

# Create an instance of the dicerollAPI
dice_api = dicerollAPI()

# Define the target value for the saving throw
target_value = 15

# Define the success threshold (rolls equal to or above this value are considered successful)
success_threshold = 10

# Roll a saving throw using the D20 dice type, blue dice color, the specified target value, and success threshold
# The animate=True parameter will display the animation if Pygame is available
saving_throw_result = dice_api.roll_saving_throw(dice_type=DiceType.D20, dice_color=DiceColor.BLUE, target_value=target_value, success_threshold=success_threshold, animate=True)

# Check if the saving throw was successful
if saving_throw_result['success']:
    print("Saving throw was successful!")
    print(f"Roll result: {saving_throw_result['roll_result']}")
else:
    print("Saving throw failed.")
    print(f"Roll result: {saving_throw_result['roll_result']}")
```
