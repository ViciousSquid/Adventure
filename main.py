print("* Init...")
import re
import json
import zipfile
from flask import Flask, render_template, request, redirect, url_for, make_response, send_from_directory, jsonify, send_file, flash, session
from adventures import load_adventures
from editor_stuff import story_editor, save_story, editor_route, load_story, graph_view, serve_thumbnail, serve_image, upload_story, generate_thumbnail
import os
from PIL import Image
from collections import Counter
import io
import werkzeug
from werkzeug.utils import secure_filename
import sys
import datetime
import os
import atexit
import ast
import random
from diceroll import DiceRoller
from diceroll_anim import DiceAnimator
from diceroll_api import dicerollAPI

class Logger(object):
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log = open(log_file, 'a')
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def write(self, message):
        self.terminal.write(message)
        cleaned_message = self.ansi_escape.sub('', message)
        self.log.write(cleaned_message)
        self.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def close_log_file():
    if isinstance(sys.stdout, Logger):
        sys.stdout.log.close()
    if isinstance(sys.stderr, Logger):
        sys.stderr.log.close()

atexit.register(close_log_file)

debug_mode = os.path.exists('debug.txt')        #If a file named 'debug.txt' is found in the root, log all console to /logs
if debug_mode:
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    current_datetime = datetime.datetime.now().strftime("%d%m_%H%M")
    log_file = os.path.join(logs_dir, f'adventure_log_{current_datetime}.txt')

    sys.stdout = Logger(log_file)
    sys.stderr = Logger(log_file)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

current_adventure = None
current_room = None
action_history = []

print("--- Adventure! ---")

@app.route('/')
def main_menu():
    adventures = load_adventures()
    
    if 'story_uploaded' in session and session['story_uploaded']:
        story_name = session['story_uploaded']
        session.pop('story_uploaded', None)
        return redirect(url_for('new_story', story_name=story_name))
    
    return render_template('main_menu.html', adventures=adventures)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/fonts/<path:filename>')
def serve_fonts(filename):
    return send_from_directory('fonts', filename)

@app.route('/new_story', methods=['POST', 'GET'])
def new_story():
    global current_adventure, current_room, action_history

    if request.method == 'GET':
        story_name = request.args.get('story_name')
    else:
        story_name = request.form.get('story_name')

    adventures = load_adventures()
    if story_name in adventures:
        current_adventure = story_name
        print(f"Current adventure set to: {current_adventure}")
        adventure = adventures[current_adventure]
        with zipfile.ZipFile(adventure, 'r') as zip_ref:
            with zip_ref.open('story.json', 'r') as f:
                story_data = json.load(f)
        current_room = story_data['start_room']
        action_history = []  # Reset action history for new story
        print(">>Starting a New Game:")
        return redirect(url_for('adventure_game'))
    else:
        return redirect(url_for('main_menu'))

def resolve_skill_check(skill_check, player_roll):
    success_description = skill_check['success']['description']
    success_room = skill_check['success']['room']
    failure_description = skill_check['failure']['description']
    failure_room = skill_check['failure']['room']

    target_value = skill_check['target']

    # Handle cases where target_value is a dictionary or a string
    if isinstance(target_value, dict):
        target_value = resolve_nested_target(target_value)
    elif isinstance(target_value, str):
        try:
            target_value = ast.literal_eval(target_value)
            target_value = resolve_nested_target(target_value)
        except (ValueError, SyntaxError):
            raise ValueError("Invalid target value structure in skill_check.")

    # Check if target_value is an integer after resolving nested structures
    if not isinstance(target_value, int):
        raise ValueError("Invalid target value type in skill_check.")

    # Extract the roll result from the player_roll dictionary
    roll_result = player_roll['roll_result']

    if roll_result >= target_value:
        return {
            'description': success_description,
            'room': success_room
        }
    else:
        return {
            'description': failure_description,
            'room': failure_room
        }

def resolve_nested_target(target_value):
    if isinstance(target_value, dict):
        if 'value' in target_value:
            return target_value['value']
        elif 'target' in target_value:
            return target_value['target']
        else:
            raise ValueError("Invalid target value structure in skill_check.")
    else:
        return target_value

@app.route('/adventure', methods=['GET', 'POST'])
def adventure_game():
    global current_room, action_history
    if current_adventure is None:
        return redirect(url_for('main_menu'))

    adventures = load_adventures()
    adventure = adventures[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        with zip_ref.open('story.json', 'r') as f:
            story_data = json.load(f)
    room = story_data['rooms'][current_room]
    button_color = story_data.get('button_color', '#4CAF50')

    # Count the number of times the player has visited the current room
    room_visit_count = Counter(action_history)[current_room]

    if len(room['exits']) > 1:
        print("\033[94m>choice point\033[0m")

    content = ""  # Initialize content with a default value
    skill_check = None  # Initialize skill_check with None
    player_roll = None  # Initialize player_roll with None
    animation_html = ""  # Initialize animation_html with an empty string

    if request.method == 'POST':
        direction = request.form.get('direction')
        if direction:
            next_room = room['exits'].get(direction, None)
            if isinstance(next_room, str):
                # Simple room transition
                current_room = next_room
                room = story_data['rooms'][current_room]
                action_history.append(current_room)
                content = room['description']  # Assign the content from the room description
            elif isinstance(next_room, dict):
                # Skill check
                skill_check = next_room['skill_check']
                dice_type = skill_check['dice_type']
                target_value = skill_check['target']

                dice_roller = dicerollAPI()
                player_roll = dice_roller.roll_dice(dice_type)

                # Trigger the dice roll animation
                dice_animator = DiceAnimator()
                dice_color = 'blue'  # Set the desired dice color
                image_base64 = dice_animator.animate_dice_roll(dice_type, dice_color, dice_roller)

                # Create the animation HTML
                animation_html = f'''
                    <div id="dice-animation-container">
                        <div>
                            <p>Dice Notation: {dice_type}</p>
                            <img src="data:image/png;base64,{image_base64}" alt="Dice Roll Animation">
                            <p>Roll Result: {player_roll['roll_result']}</p>
                        </div>
                    </div>
                '''

                skill_check_result = resolve_skill_check(skill_check, player_roll)
                current_room = skill_check_result['room']
                content = skill_check_result['description']

                room = story_data['rooms'][current_room]
                action_history.append(current_room)
            else:
                content = "You can't go that way."  # Assign the content for invalid direction
        else:
            content = room['description']  # Assign the content from the room description
    else:
        content = room['description']  # Assign the content from the room description

    # Check if the player has reached an ending
    if not room['exits']:
        print("\033[92m>Player reached an ending\033[0m")

    exits = [(direction, room_data) for direction, room_data in room['exits'].items() if room_data]
    show_map = room.get('show_map', True)
    story_title = story_data['name']

    # Check if the player has visited the current room enough times to unlock a new branch
    revisit_count = room.get('revisit_count', 0)
    if room_visit_count >= revisit_count:
        # Add additional content or options from the story.json file
        additional_content = room.get('revisit_content', "")
        content += "\n" + additional_content

    return render_template('adventure.html', content=content, exits=exits, room=room, show_map=show_map,
                           action_history=action_history, button_color=button_color, story_title=story_title,
                           skill_check=skill_check, player_roll=player_roll, animation_html=animation_html)

@app.route('/dice_roll_image')
def serve_dice_roll_image():
    image_base64 = session.get('dice_roll_image', '')
    return f'<img src="data:image/png;base64,{image_base64}" alt="Dice Roll Animation">'

@app.route('/play')
def play_story():
    if current_adventure is None:
        return redirect(url_for('main_menu'))

    adventures = load_adventures()
    adventure = adventures[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        with zip_ref.open('story.json', 'r') as f:
            story_data = json.load(f)
    current_room_id = story_data['start_room']
    action_history = []
    current_room = story_data['rooms'][current_room_id]['name']  # Get the room name
    room = story_data['rooms'][current_room_id]  # Get the current room data

    return render_template('play.html', adventure=story_data, current_room=current_room, action_history=action_history, content=room['description'], exits=[direction for direction, room_name in room['exits'].items() if room_name])

@app.route('/play_action', methods=['POST'])
def play_action():
    global current_room, action_history
    if current_adventure is None:
        return redirect(url_for('main_menu'))

    adventures = load_adventures()
    adventure = adventures[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        with zip_ref.open('story.json', 'r') as f:
            story_data = json.load(f)
    direction = request.form.get('direction')
    if direction:
        current_room_id = current_room
        room = story_data['rooms'][current_room_id]
        next_room_id = room['exits'].get(direction, None)
        if next_room_id:
            current_room_id = next_room_id
            action_history.append(current_room_id)
            current_room = story_data['rooms'][current_room_id]['name']  # Get the new room name
            room = story_data['rooms'][current_room_id]  # Get the new current room data
            content = room['description']
            exits = [direction for direction, room_name in room['exits'].items() if room_name]
            return render_template('play.html', adventure=story_data, current_room=current_room, action_history=action_history, content=content, exits=exits)
        else:
            return render_template('play.html', adventure=story_data, current_room=current_room, action_history=action_history, content="You can't go that way.")
    else:
        return redirect(url_for('play_story'))

@app.route('/roll', methods=['POST'])
def roll_dice():
    dice_notation = request.form.get('dice_notation')
    dice_color = request.form.get('dice_color')
    target_value = request.form.get('target_value')

    dice_roller = dicerollAPI()
    roll_result = dice_roller.roll_dice(dice_notation, dice_color=dice_color, target_value=int(target_value), animate=False)

    # Get the base64-encoded image of the dice roll animation
    image_base64 = dice_roller.dice_animator.animate_dice_roll(dice_notation, dice_color, dice_roller)

    return jsonify({'image_base64': image_base64, 'roll_result': str(roll_result['roll_result'])})

@app.route('/save', methods=['POST'])
def save_game():
    if current_adventure is None:
        return redirect(url_for('main_menu'))

    game_state = {
        'current_adventure': current_adventure,
        'current_room': current_room,
        'action_history': action_history
    }
    response = make_response(json.dumps(game_state))
    response.headers.set('Content-Type', 'application/json')
    response.headers.set('Content-Disposition', 'attachment', filename='game_state.json')
    return response

@app.route('/load', methods=['POST'])
def load_game():
    global current_adventure, current_room, action_history
    file = request.files['file']
    data = json.load(file)

    # Check if the JSON data has a 'name' key
    if 'name' in data:
        current_adventure = data['name']
    else:
        # Assume the JSON data represents an adventure directly
        adventures = load_adventures()
        current_adventure = next(iter(adventures))  # Get the first adventure name
        with zipfile.ZipFile(adventures[current_adventure], 'r') as zip_ref:
            with zip_ref.open('story.json', 'r') as f:
                data = json.load(f)

    adventures = load_adventures()
    with zipfile.ZipFile(adventures[current_adventure], 'r') as zip_ref:
        with zip_ref.open('story.json', 'r') as f:
            story_data = json.load(f)
    current_room = story_data['start_room']
    action_history = data.get('action_history', [])

    room = story_data['rooms'][current_room]
    content = room['description']
    exits = [direction for direction, room_name in room['exits'].items() if room_name]
    show_map = room.get('show_map', True)
    button_color = story_data.get('button_color', '#4CAF50')
    return render_template('adventure.html', content=content, exits=exits, room=room, show_map=show_map, action_history=action_history, button_color=button_color)

# Editor routes
app.add_url_rule('/editor', methods=['GET'], view_func=editor_route)
app.add_url_rule('/load_story', methods=['POST'], view_func=load_story)
app.add_url_rule('/save_story', methods=['POST'], view_func=save_story)
app.add_url_rule('/editor/graph', 'graph_view', view_func=graph_view)
app.add_url_rule('/thumbnails/<path:filename>', 'serve_thumbnail', view_func=serve_thumbnail)
app.add_url_rule('/images/<path:filename>', 'serve_image', view_func=serve_image)
app.add_url_rule('/upload_story', methods=['POST'], view_func=upload_story)

if __name__ == '__main__':
    app.run(debug=False)