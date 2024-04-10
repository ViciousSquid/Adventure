## DiceAnimator Class (Optional)

The <code style="color : name_color">**DiceAnimator**</code> class provides a visual animation of the dice roll using the Pygame library. It requires the <code style="color : name_color">diceroll_anim</code> module to be available.

### <code style="color : name_color">__init__(window_width=300, window_height=300, dice_image_path="images")</code>

* <code style="color : name_color">window_width</code> (optional): An integer representing the width of the Pygame window. Default is 300.
* <code style="color : name_color">window_height</code> (optional): An integer representing the height of the Pygame window. Default is 300.

* <code style="color : name_color">dice_image_path</code>  (optional): A string representing the path to the directory containing the dice images. Default is "images".

(Raises <code style="color : name_color">ValueError</code> if no dice image sets are found in the specified directory)

* <code style="color : name_color">load_dice_sets()</code> : Loads dice images from the specified directory and returns a dictionary containing the loaded dice sets, with colors as keys and lists of dice images as values.



### <code style="color : name_color">animate_dice_roll(dice_type, dice_color, dice_roller, target=None)</code>

Animates the dice roll in the Pygame window. Uses the <code style="color : name_color">DiceRoller</code> instance to perform the actual roll. Always displays the animation for a single die, regardless of the number of dice specified.

* <code style="color : name_color">dice_type</code> : A string representing the type of dice to roll (e.g., "2d6" or "3d8+1d4" for a combination of dice).
* <code style="color : name_color">dice_color</code> : A string representing the color of the dice set to use (e.g., "red", "white", "blue", or "black").
* <code style="color : name_color">dice_roller</code> : An instance of the <code style="color : name_color">DiceRoller</code> class.
* <code style="color : name_color">target</code> (optional): An integer representing the target number to beat. If provided, the function will display the dice type and target.
* <code style="color : name_color">returns</code> :An integer representing the result of the dice roll.
Raises <code style="color : name_color">ValueError</code> if an invalid dice color is provided.

### <code style="color : name_color">run_animation(dice_type, dice_color='blue', target=None)</code>
Runs the dice roll animation and returns the roll result.

* <code style="color : name_color">dice_type</code> : A string representing the type of dice to roll (e.g., "2d6" or "3d8+1d4" for a combination of dice).
* <code style="color : name_color">dice_color</code> : (optional): A string representing the color of the dice set to use (e.g., "red", "white", "blue", or "black"). Default is 'blue'.
* <code style="color : name_color">target</code> : (optional): An integer representing the target number to beat. If provided, the function will display the dice type and target.

### Example usage:

```python
from diceroll import DiceRoller
from diceroll_anim import DiceAnimator

# Create a DiceRoller instance
dice_roller = DiceRoller()

# Create a DiceAnimator instance
dice_animator = DiceAnimator()

# Animate the roll of 2d6 dice with a target of 7
roll_result = dice_animator.run_animation("2d6", target=7)
print(roll_result)
```


