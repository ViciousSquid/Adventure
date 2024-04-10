```python
attributes = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
attr_rolls = dice_api.roll_multiple_dice(["4d6"] * 6)

character_stats = {}
for i, attr in enumerate(attributes):
    roll = attr_rolls[i]
    stat_value = sum(roll["roll_details"]) - min(roll["roll_details"])
    character_stats[attr] = stat_value
    
print("Your character's stats are:")
print(character_stats)
```
