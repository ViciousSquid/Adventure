from diceroll_api import dicerollAPI, DiceColor

def main():
    # Create an instance of the dicerollAPI class
    api = dicerollAPI()

    # Set the dice color (optional)
    dice_color = DiceColor.BLUE

    # Set the target value
    target_value = 15

    # Roll 2d6 with animation and target value
    roll_result = api.roll_dice("2d6", dice_color=dice_color, target_value=target_value, animate=True)

    # Save the roll result to a text file
    if roll_result is not None:
        with open("test_result.txt", "w") as file:
            file.write(f"Dice Notation: 2d6\n")
            file.write(f"Target Value: {target_value}\n")
            file.write(f"Roll Result: {roll_result['roll_result']}\n")
            file.write(f"Roll Details: {roll_result['roll_details']}\n")

            # Check if the roll result meets or exceeds the target value
            if roll_result['roll_result'] >= target_value:
                file.write("Success")
            else:
                file.write("Fail")
    else:
        print("Invalid roll result.")

if __name__ == "__main__":
    main()