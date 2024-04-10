ANSI escape codes are specified in the `diceroll_api.py` file:

```python
 # Set console text color based on dice_color
            if dice_color == DiceColor.RED:
                console_color = '\033[91m'  # Red
            elif dice_color == DiceColor.BLUE:
                console_color = '\033[94m'  # Light blue
            elif dice_color == DiceColor.GREEN:
                console_color = '\033[92m'  # Green
            elif dice_color == DiceColor.BLACK:
                console_color = '\033[97m'  # White (for visibility)
            elif dice_color == 'bread':
                console_color = '\033[97m'  # White (default) for 'bread' color
            else:
                console_color = '\033[97m'  # White (default)
```
