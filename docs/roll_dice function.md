## roll_dice function

The <code style="color : name_color">**roll_dice**</code> function is a utility function that performs a dice roll and returns the roll result and outcome details if a target is provided.
 It uses the <code style="color : name_color">DiceRoller</code> and <code style="color : name_color">OutcomeDeterminer</code> classes internally.

 <code style="color : name_color">roll_dice(dice_type, target=None, success_outcome=None, failure_outcome=None, use_animation=False)</code>

* <code style="color : name_color">dice_type</code> : A string representing the type of dice to roll (e.g., "2d6" or "3d8+1d4" for a combination of dice).
* <code style="color : name_color">target</code> (optional): An integer representing the target number to beat. If provided, the function will return the outcome details.
* <code style="color : name_color">success_outcome</code> (optional): A dictionary containing the outcome details if the roll is successful. Required if <code style="color : name_color">target</code> is provided.
* <code style="color : name_color">failure_outcome</code> (optional): A dictionary containing the outcome details if the roll is a failure. Required if <code style="color : name_color">target</code> is provided.
  
* <code style="color : name_color">use_animation</code>  (optional): A boolean indicating whether to use the dice roll animation. 
Default is <code style="color : name_color">False</code>.
If <code style="color : name_color">True</code> , The <code style="color : name_color">DiceAnimator</code> class is used (provided the <code style="color : name_color">diceroll_anim</code> module is available).

<code style="color : name_color">Returns</code> : A dictionary containing the roll result and, if target is provided, the outcome details.

Raises <code style="color : name_color">ValueError</code> if <code style="color : name_color">target</code> is provided but <code style="color : name_color">success_outcome</code> or <code style="color : name_color">failure_outcome</code> is missing.

Raises <code style="color : name_color">ImportError</code> if <code style="color : name_color">use_animation</code> is <code style="color : name_color">True</code> but the <code style="color : name_color">diceroll_anim</code> module is not available.

### Example usage:

```python
from diceroll import roll_dice

# Roll 2d6 dice with a target of 7, success outcome, and failure outcome
result = roll_dice("2d6", target=7, success_outcome={"details": "Success!"}, failure_outcome={"details": "Failure."})
print(result)  # Output: {'roll_result': 8, 'outcome': {'details': 'Success!', 'roll_result': 8}}

# Roll 1d20 dice without a target
result = roll_dice("1d20")
print(result)  # Output: {'roll_result': 15}
```
