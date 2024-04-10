* All functions and classes documented: https://github.com/ViciousSquid/Adventure/tree/main/docs in the `functions & classes` folder
* Please refer to demo files `Example1.py`, `Example2.py`, and `Example3_gui.py` for quick feature overview.



# dicerollAPI![image](https://github.com/ViciousSquid/diceroll/assets/161540961/86d8abe9-3153-4cbc-b3d9-0c4b1b20c166)

The `dicerollAPI` class provides a high-level interface for rolling dice, performing animations, and managing roll history. 

Here's a summary of the functions exposed by the API:
_____

#### `__init__(self, save_rolls=False, log_console=None)`
Initializes the dicerollAPI instance with optional parameters to enable saving rolls and logging to the console.
* `save_rolls` (bool): Optional parameter to enable saving rolls. Default is False.
* `log_console` (bool): Optional parameter to enable logging to the console. Default is None.

_____

#### `set_animation_window_size(self, width=300, height=300)`
Initializes the dicerollAPI instance with optional parameters to enable saving rolls and logging to the console.
* `width` (int): Width of the animation window. Default is 300.
* `height` (int): Height of the animation window. Default is 300.

_____

#### `set_dice_image_path(self, path="dice_imgs")`
Initializes the dicerollAPI instance with optional parameters to enable saving rolls and logging to the console.
* `save_rolls` (bool): Optional parameter to enable saving rolls. Default is False.
* `log_console` (bool): Optional parameter to enable logging to the console. Default is None.

_____

#### `roll_dice(self, dice_notation, dice_color=DiceColor.WHITE, target_value=None, animate=True)`
* `dice_notation` (str): The dice notation specifying the number and type of dice to roll (e.g., "2d6").
* `dice_color` (DiceColor): The color of the dice. Default is DiceColor.WHITE.
* `target_value` (int): Optional target value for the roll. Default is None.
* `animate` (bool): Flag to enable or disable animation. Default is True.
_____

#### `roll_single_dice(self, dice_type, dice_color=DiceColor.WHITE, animate=True)`
* dice_type (str): The type of dice to roll (e.g., "d6", "d20").
* dice_color (DiceColor): The color of the dice. Default is DiceColor.WHITE.
* animate (bool): Flag to enable or disable animation. Default is True.

_____

#### `roll_multiple_dice_of_same_type(self, dice_type, num_dice, dice_color=DiceColor.WHITE, animate=True)`
* `dice_type` (str): The type of dice to roll (e.g., "d6", "d20").
* `num_dice` (int): The number of dice to roll.
* `dice_color` (DiceColor): The color of the dice. Default is DiceColor.WHITE.
* `animate` (bool): Flag to enable or disable animation. Default is True.

_____

#### `roll_multiple_dice(self, dice_notations, dice_colors=None, target_values=None, animate=True)`
* dice_notations (list): A list of dice notations specifying the number and type of dice to roll for each set.
* dice_colors (list): Optional list of dice colors corresponding to each set of dice. Default is None.
* target_values (list): Optional list of target values for each set of dice. Default is None.
* animate (bool): Flag to enable or disable animation. Default is True.


_____

#### `get_roll_sum(self, roll_result)`
* `roll_result` (dict): The result of a dice roll.


_____

#### `get_roll_average(self, roll_result)`
* `roll_result` (dict): The result of a dice roll.

_____

#### `get_roll_max(self, roll_result)`
* `roll_result` (dict): The result of a dice roll.


_____

#### `get_roll_min(self, roll_result)`
* `roll_result` (dict): The result of a dice roll.


_____

#### `get_roll_statistics(self, dice_notation, num_rolls)`
* `dice_notation` (str): The dice notation specifying the number and type of dice to roll.
* `num_rolls` (int): The number of rolls to perform for calculating statistics.


_____

#### `save_roll_history_to_file(self, file_path)`
* `file_path` (str): The path to the file where the roll history will be saved.


_____

#### `load_roll_history_from_file(self, file_path)`
* `file_path` (str): The path to the file from which the roll history will be loaded.v


_____

#### `get_last_roll_total(self)`
* No arguments.


_____

#### `get_last_roll_details(self)`
* No arguments.


_____

#### `get_last_5_rolls(self)`
* No arguments.


_____

#### `get_available_dice_colors(self)`
* No arguments.

_____

#### `enable_roll_saving(self)`
* No arguments.


_____

#### `disable_roll_saving(self)`
* No arguments.

_____

#### `set_animation_style(self, style=AnimationStyle.SHAKE)`
* `style` (AnimationStyle): The animation style to set. Default is `AnimationStyle.SHAKE`


_____

#### `roll_saving_throw(self, dice_type=DiceType.D20, dice_color=DiceColor.WHITE, target_value=None, success_threshold=None, animate=True)`
* `dice_type` (DiceType): The type of dice to roll for the saving throw. Default is `DiceType.D20`.
* `dice_color` (DiceColor): The color of the dice. Default is `DiceColor.WHITE`
* `target_value` (int): Optional target value for the saving throw. Default is `None`
* `success_threshold` (int): Optional success threshold for the saving throw. Default is `None`
* `animate` (bool): Flag to enable or disable animation. Default is `True`

_____

#### `roll_multiple_saving_throws(self, num_throws, dice_type=DiceType.D20, dice_color=DiceColor.WHITE, target_values=None, success_thresholds=None, animate=True)`
* `num_throws` (int): The number of saving throws to roll.
* `dice_type` (DiceType): The type of dice to roll for each saving throw. Default is `DiceType.D20`
* `dice_color` (DiceColor): The color of the dice. Default is `DiceColor.WHITE`
* `target_values` (list): Optional list of target values for each saving throw. Default is `None`
* `success_thresholds` (list): Optional list of success thresholds for each saving throw. Default is `None`
* `animate` (bool): Flag to enable or disable animation. Default is `True`

_____


#### `enable_console_logging(self)`
* No arguments.

  _____


#### `disable_console_logging(self)`
* No arguments.
#### `animate_dice_roll(self, dice_notation)`
* `dice_notation` (str): The dice notation specifying the number and type of dice to roll.
