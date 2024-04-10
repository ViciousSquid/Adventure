### The `dice_color` parameter is used to determine the console text color 

The appropriate ANSI escape code is assigned to `console_color` based on the `dice_color` value.
* 'red': '\033[91m' for red text
* 'blue': '\033[94m' for light blue text
* 'black': '\033[97m' for white text (to ensure visibility)
* Default or 'white': '\033[97m' for white text

After printing the roll details, the color is reset using \033[0m to ensure subsequent console outputs are not affected.


-----

Note that the console output and the Pygame animation are independent of each other. 
