## The DiceRoller Class

<code style="color : name_color">**DiceRoller**</code> class: Encapsulates the dice rolling functionality and maintains the state of the last roll.

<code style="color : name_color">**__init__**()</code> Initializes a new instance of the <code style="color : name_color">DiceRoller</code> class with the <code style="color : name_color">last_roll_total</code> and <code style="color : name_color">last_roll_details</code> set to <code style="color : name_color">none</code>

<code style="color : name_color">**roll_dice**(dice_type)</code>  Rolls one or more dice of the specified type and returns the sum of the results.
Updates the <code style="color : name_color">last_roll_total</code> and <code style="color : name_color">last_roll_details</code> attributes.
dice_type: A string representing the type of dice to roll (e.g., "2d6" or "3d8+1d4" for a combination of dice).
Returns an integer representing the sum of the dice roll results.
Raises <code style="color : name_color">ValueError</code> if an invalid dice type is provided.

<code style="color : name_color">**get_last_roll_total()**</code> function:  Returns the total of the last dice roll, or <code style="color : name_color">None</code> if no roll has been performed yet.

<code style="color : name_color">**get_last_roll_details()**</code> Returns the individual results of the last dice roll as a list, or <code style="color : name_color">None</code> if no roll has been performed yet.

### Example usage:

```python
from diceroll import DiceRoller

# Create a DiceRoller instance
roller = DiceRoller()

# Roll 2d6 dice
result = roller.roll_dice("2d6")
print(result)  # Output: 7

# Get the total of the last roll
last_roll_total = roller.get_last_roll_total()
print(last_roll_total)  # Output: 7

# Get the individual results of the last roll
last_roll_details = roller.get_last_roll_details()
print(last_roll_details)  # Output: [3, 4]
```

