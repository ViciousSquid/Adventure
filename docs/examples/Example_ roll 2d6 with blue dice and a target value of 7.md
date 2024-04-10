Here's an example of how you can make a call through the `dicerollAPI` to roll **2d6** with **blue** dice and a target value of **7**:

```python
from diceroll_api import dicerollAPI, DiceColor

# Create an instance of the dicerollAPI
api = dicerollAPI()

# Set the dice color to blue
dice_color = DiceColor.BLUE

# Specify the dice notation and target value
dice_notation = "2d6"
target_value = 7

# Roll the dice
roll_result = api.roll_dice(dice_notation, dice_color=dice_color, target_value=target_value)

# Print the roll result
print(roll_result)
```

### Explanation:

* We import the `dicerollAPI` and `DiceColor` from the `diceroll_api` module.
* We create an instance of the dicerollAPI called `api`.
* We set the `dice_color` variable to `DiceColor.BLUE` to specify the blue color for the dice.
* We define the `dice_notation` as `"2d6"`, which represents rolling two six-sided dice.
* We set the `target_value` to `7`, indicating that we want to check if the roll result meets or exceeds this target.
* We call the `roll_dice()` method of the `api` instance, passing the `dice_notation`, `dice_color`, and `target_value` as arguments.
* The `roll_dice()` method returns a dictionary containing the roll result, which we store in the `roll_result` variable.
* Finally, we print the `roll_result` to see the outcome of the roll.

The roll_result dictionary will contain the following information:
* `"dice_notation"`: The dice notation used for the roll (e.g., "2d6").
* `"roll_result"`: The total value of the roll.
* `"roll_details"`: A list of individual roll values for each die.
* `"success"`: A boolean value indicating whether the roll result meets or exceeds the target value (only present if a target value was specified).

____


### Example output:

```python
{
    "dice_notation": "2d6",
    "roll_result": 9,
    "roll_details": [4, 5],
    "success": True
}
```

In this example, the roll result is 9 (4 + 5), which meets the target value of 7, so `"success"` is `True`.
