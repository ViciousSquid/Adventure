```python
damage_die = "2d6"
damage_bonus = 3

attack_roll = dice_api.roll_dice("1d20")
if attack_roll["roll_result"] >= enemy.armor_class:
    print("Hit!")
    damage_roll = dice_api.roll_dice(damage_die)
    total_damage = damage_roll["roll_result"] + damage_bonus
    print(f"You deal {total_damage} damage!")
else:
    print("Miss!")
```
