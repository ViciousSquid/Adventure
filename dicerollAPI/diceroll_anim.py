import random
from .diceroll_enums import DiceColor, AnimationStyle
from flask import url_for
from datetime import datetime

class DiceType:
    D4 = "d4"
    D6 = "d6"
    D8 = "d8"
    D10 = "d10"
    D12 = "d12"
    D20 = "d20"

class DiceAnimator:
    def __init__(self, dice_image_path="static/dice_imgs"):
        self.dice_image_path = dice_image_path
        self.animation_style = AnimationStyle.SHAKE

    def animate_dice_roll_html(self, dice_notation, dice_color, roll_result):
        number_of_dice = int(dice_notation.split("d")[0])
        dice_type = dice_notation.split("d")[1]

        roll_results = roll_result['roll_details']
        roll_sum = roll_result['roll_result']

        dice_images = []
        for result in roll_results:
            if dice_type == "6":
                png_file = url_for('static', filename=f'dice_imgs/d6_{result}.png')
                dice_image = f'<div class="dice-image" style="background-image: url(\'{png_file}\');"></div>'
            else:
                png_file = url_for('static', filename=f'dice_imgs/blank_d{dice_type}.png')
                dice_image = f'<div class="dice-image" style="background-image: url(\'{png_file}\');"><div class="dice-number">{result}</div></div>'
            dice_images.append(dice_image)

        animation_html = f"""
        <div class="dice-animation">
            <style>
                .dice-animation {{
                    position: relative;
                    width: 280px;
                    height: 280px;
                    background-color: rgba(255,255,255,0);
                    border: 1px solid black;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                .dice-image {{
                    position: relative;
                    width: 150px;
                    height: 171px;
                    background-size: cover;
                    animation: shake 0.75s ease-in-out 0s 1, roll 1s ease-in-out 1s forwards;
                }}
                .dice-number {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    font-size: 40px;
                    font-weight: bold;
                    color: black;
                    opacity: 0;
                    animation: fade-in 1.25s ease-in-out 1.25s forwards;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
                }}
                .dice-notation {{
                    position: absolute;
                    top: 10px;
                    left: 50%;
                    transform: translateX(-50%);
                    font-size: 14px;
                    font-weight: bold;
                    color: black;
                }}
                @keyframes shake {{
                    0% {{ transform: translate(0, 0) rotate(0deg); }}
                    10% {{ transform: translate(-10px, 0) rotate(-10deg); }}
                    20% {{ transform: translate(10px, 0) rotate(10deg); }}
                    30% {{ transform: translate(-10px, 0) rotate(-10deg); }}
                    40% {{ transform: translate(10px, 0) rotate(10deg); }}
                    50% {{ transform: translate(-10px, 0) rotate(-10deg); }}
                    60% {{ transform: translate(10px, 0) rotate(10deg); }}
                    70% {{ transform: translate(-10px, 0) rotate(-10deg); }}
                    80% {{ transform: translate(10px, 0) rotate(10deg); }}
                    90% {{ transform: translate(-10px, 0) rotate(-10deg); }}
                    100% {{ transform: translate(0, 0) rotate(0deg); }}
                }}
                @keyframes roll {{
                    0% {{ transform: translate(0, 0) rotate(0deg); }}
                    100% {{ transform: translate(0, 0) rotate(360deg); }}
                }}
                @keyframes fade-in {{
                    0% {{ opacity: 0; }}
                    100% {{ opacity: 1; }}
                }}
            </style>
            <div class="dice-container">
                {''.join(dice_images)}
            </div>
            <div class="dice-notation">{dice_notation}</div>
        </div>
        """

        return animation_html