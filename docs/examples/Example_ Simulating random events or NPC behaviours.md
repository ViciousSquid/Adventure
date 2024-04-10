```python
event_table = {
    2: "A mysterious stranger approaches.",
    3: "You find a hidden treasure!",
    4: "Nothing happens.",
    5: "Nothing happens.",  
    6: "You are ambushed by goblins!",
    7: "Nothing happens."
}

event_roll = dice_api.roll_single_dice("1d6")
event = event_table[event_roll["roll_result"]]
print(event)
```
