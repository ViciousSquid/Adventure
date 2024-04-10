```python
from diceroll_api import dicerollAPI

dice_api = dicerollAPI()

player1_initiative = dice_api.roll_dice("1d20")["roll_result"] 
player2_initiative = dice_api.roll_dice("1d20")["roll_result"]

if player1_initiative > player2_initiative:
    print("Player 1 goes first!")
elif player2_initiative > player1_initiative:
    print("Player 2 goes first!")
else:
    print("Tie! Roll again.")
```
