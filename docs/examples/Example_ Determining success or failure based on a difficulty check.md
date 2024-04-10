```python
difficulty = 15
roll_result = dice_api.roll_dice("1d20", target_value=difficulty)

if roll_result["roll_result"] >= difficulty:
    print("Success! You pick the lock.")
else:
    print("Failure. The lock remains jammed.")
```
