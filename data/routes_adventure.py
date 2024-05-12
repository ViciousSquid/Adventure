from flask import render_template, request, redirect, url_for, make_response, jsonify, session
from markupsafe import escape  # Import escape from markupsafe
from main import app, current_adventure, current_room, action_history, load_adventures
from dicerollAPI.diceroll_api import dicerollAPI
from .editor_stuff import story_editor
from dicerollAPI.diceroll_anim import DiceAnimator
from collections import Counter
import zipfile
import os
import json
import ast
import re

def renderMarkup(text):
    bold_regex = r"\*\*(.*?)\*\*"
    italic_regex = r"\*(.*?)\*"
    newline_regex = r"\n"

    text = re.sub(bold_regex, r"<strong>\1</strong>", text)
    text = re.sub(italic_regex, r"<em>\1</em>", text)
    text = text.replace(newline_regex, "<br>")

    return text

@app.route('/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    adventures = load_adventures()
    if current_adventure not in adventures:
        return redirect(url_for('main_menu'))

    story_data = story_editor(current_adventure)
    room = story_data['rooms'].get(current_room, {})
    if room.get('image') == filename:
        adventure = adventures[current_adventure]
        with zipfile.ZipFile(adventure, 'r') as zip_ref:
            try:
                image_data = zip_ref.read(filename)
                response = make_response(image_data)
                response.headers.set('Content-Type', 'image/jpeg')
                return response
            except KeyError:
                return redirect(url_for('main_menu'))
    else:
        return redirect(url_for('main_menu'))

@app.route('/new_story', methods=['POST', 'GET'])
def new_story():
    global current_adventure, current_room, action_history

    if request.method == 'GET':
        story_name = request.args.get('story_name')
    else:
        story_name = request.form.get('story_name')

    if 'story_uploaded' in session and session['story_uploaded']:
        story_name = session['story_uploaded']
        temp_file_path = session['story_zip_file_path']

        # Read the ZIP file data from the temporary file
        with open(temp_file_path, 'rb') as f:
            story_zip_data = f.read()

        with zipfile.ZipFile(io.BytesIO(story_zip_data)) as zip_ref:
            with zip_ref.open('story.json', 'r') as f:
                story_data = json.load(f)
        current_adventure = story_name
        current_room = story_data['start_room']
        action_history = []  # Reset action history for new story
        session['inventory'] = []  # Clear the player's inventory
        print(">>Starting a New Game:")

        # Remove the temporary file and clear the session data
        os.remove(temp_file_path)
        session.pop('story_uploaded', None)
        session.pop('story_zip_file_path', None)

        return redirect(url_for('adventure_game'))

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
        session['inventory'] = []  # Clear the player's inventory
        print(">>Starting a New Game:")
        return redirect(url_for('adventure_game'))
    else:
        return redirect(url_for('main_menu'))

def resolve_skill_check(skill_check, player_roll):
    # Check if the 'description' key is directly under the skill_check dictionary
    if 'description' in skill_check:
        success_description = skill_check['description']
        failure_description = skill_check['description']
    else:
        # The 'description' key is nested under 'success' and 'failure' dictionaries
        success_description = skill_check['success']['description']
        failure_description = skill_check['failure']['description']

    success_room = skill_check['success']['room']
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
        zip_contents = zip_ref.namelist()  # Get a list of filenames in the zip file
        with zip_ref.open('story.json', 'r') as file:
            story_data = json.load(file)
    room = story_data['rooms'][current_room]
    button_color = story_data.get('button_color', '#4CAF50')

    # Count the number of times the player has visited the current room
    room_visit_count = Counter(action_history)[current_room]

    content = ""  # Initialize content with a default value
    skill_check = None  # Initialize skill_check with None
    player_roll = None  # Initialize player_roll with None
    animation_html = ""  # Initialize animation_html with an empty string
    roll_dice_button = ""  # Initialize roll_dice_button with an empty string
    dice_notation = ""  # Initialize dice_notation with an empty string

    # Retrieve the player's inventory from the session, or an empty list if not present
    player_inventory = session.get('inventory', [])

    # Retrieve the available items and required items for the current room, or empty lists if not present
    available_items = room.get('items', [])
    item_needed = room.get('item_needed', None)

    # Retrieve the room message if available
    room_message = room.get('message')

    # Retrieve the item message if available
    item_message = request.args.get('item_message', '')

    # Check if the room has an "exits" key
    if "exits" in room:
        if len(room['exits']) > 1:
            print("\033[94m>choice point\033[0m")

        # Handle room transitions and skill checks
        if request.method == 'POST':
            direction = request.form.get('direction')
            if direction:
                next_room = room['exits'].get(direction)
                if isinstance(next_room, dict) and 'skill_check' in next_room:
                    # Nested skill check
                    skill_check = next_room['skill_check']
                    dice_type = skill_check['dice_type']
                    target_value = skill_check['target']
                    dice_notation = dice_type  # Get the dice notation from the skill check

                    if 'roll_dice' in request.form:
                        # Perform the dice roll and handle the result
                        dice_roller = dicerollAPI()
                        player_roll = dice_roller.roll_dice(dice_type)

                        # Trigger the dice roll animation
                        dice_animator = DiceAnimator()
                        dice_color = 'blue'  # Set the desired dice color
                        dice_roll_result = dice_roller.roll_dice(dice_type, dice_color)
                        if dice_roll_result is not None:
                            animation_html = dice_animator.animate_dice_roll_html(dice_type, dice_color, dice_roll_result)

                        skill_check_result = resolve_skill_check(skill_check, player_roll)
                        current_room = skill_check_result['room']
                        content = escape(renderMarkup(skill_check_result['description']))  # Use escape and renderMarkup here

                        room = story_data['rooms'][current_room]
                        action_history.append(current_room)
                    else:
                        # Display the room description and the "Roll Dice" button
                        content = escape(renderMarkup(room['description']))  # Use escape and renderMarkup here
                        roll_dice_button = f'<form method="post"><input type="hidden" name="direction" value="{direction}"><button type="submit" name="roll_dice" id="roll-dice-button">Roll Dice</button></form>'
                elif isinstance(next_room, str):
                    # Simple room transition
                    current_room = next_room
                    room = story_data['rooms'][current_room]
                    action_history.append(current_room)
                    content = escape(renderMarkup(room['description']))  # Use escape and renderMarkup here
                else:
                    content = "You can't go that way."
            else:
                content = escape(renderMarkup(room['description']))  # Use escape and renderMarkup here
        else:
            content = escape(renderMarkup(room['description']))  # Use escape and renderMarkup here

    else:
        # This room is the end of the story
        print("! Player reached the end of the story")
        content = escape(renderMarkup(room['description']))

    exits = [(direction, room_data) for direction, room_data in room['exits'].items() if room_data]
    show_map = room.get('show_map', True)
    story_title = story_data['name']

    # Check if the player has visited the current room enough times to unlock a new branch
    revisit_count = room.get('revisit_count', 0)
    if room_visit_count >= revisit_count:
        # Add additional content or options from the story.json file
        additional_content = room.get('revisit_content', "")
        content += "\n" + escape(renderMarkup(additional_content))  # Use escape and renderMarkup here

    return render_template('adventure.html', content=content, exits=exits, room=room, show_map=show_map,
                           action_history=action_history, button_color=button_color, story_title=story_title,
                           skill_check=skill_check, player_roll=player_roll, animation_html=animation_html,
                           roll_dice_button=roll_dice_button, dice_notation=dice_notation,
                           player_inventory=player_inventory, available_items=available_items,
                           item_needed=item_needed, room_message=room_message, item_message=item_message,
                           zip_contents=zip_contents)  # Pass the zip_contents list to the template

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

    content = escape(renderMarkup(room['description']), False)
    exits = [direction for direction, room_name in room['exits'].items() if room_name]
    return render_template('play.html', adventure=story_data, current_room=current_room, action_history=action_history, content=content, exits=exits)

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
            content = escape(renderMarkup(room['description']), False)
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

    # Get the HTML string for the dice roll animation
    dice_animator = DiceAnimator()
    animation_html = dice_animator.animate_dice_roll_html(dice_notation, dice_color, dice_roller)

    return jsonify({'animation_html': animation_html, 'roll_result': str(roll_result['roll_result'])})

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
    content = escape(renderMarkup(room['description']), False)
    exits = [direction for direction, room_name in room['exits'].items() if room_name]
    show_map = room.get('show_map', True)
    button_color = story_data.get('button_color', '#4CAF50')
    return render_template('adventure.html', content=content, exits=exits, room=room, show_map=show_map, action_history=action_history, button_color=button_color)

@app.route('/acquire_item', methods=['POST'])
def acquire_item():
    global current_room
    item_name = request.form.get('item_name')
    
    # Load the story data
    adventures = load_adventures()
    adventure = adventures[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        with zip_ref.open('story.json', 'r') as f:
            story_data = json.load(f)
    
    if item_name:
        # Check if the item is available in the current room
        room = story_data['rooms'][current_room]
        available_items = room.get('items', [])
        
        if item_name in available_items:
            # Add the item to the player's inventory
            if 'inventory' not in session:
                session['inventory'] = []
            if item_name not in session['inventory']:
                session['inventory'].append(item_name)
            
            # Remove the item from the room's available items
            room['items'].remove(item_name)
            
            # Check if the item acquisition requires a skill check
            item_skill_check = room.get('item_skill_check')
            if item_skill_check:
                # Perform the skill check
                dice_type = item_skill_check['dice_type']
                target_value = item_skill_check['target']
                
                # Roll the dice and compare the result with the target value
                dice_roller = dicerollAPI()
                roll_result = dice_roller.roll_dice(dice_type)
                
                if roll_result['roll_result'] >= target_value:
                    # Skill check success
                    description = item_skill_check['success']['description']
                    item_acquired = item_skill_check['success']['item']
                    session['inventory'].append(item_acquired)
                else:
                    # Skill check failure
                    description = item_skill_check['failure']['description']
            else:
                description = f"You acquired the {item_name}."
        else:
            description = f"The {item_name} is not available in this room."
    else:
        description = "No item specified."
    
    # Redirect back to the current room with the updated description
    return redirect(url_for('adventure_game', item_message=description))

@app.route('/use_item', methods=['POST'])
def use_item():
    global current_room, player_inventory, player_health
    item_name = request.form.get('item_name')
    
    # Load the story data
    adventures = load_adventures()
    adventure = adventures[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        with zip_ref.open('story.json', 'r') as f:
            story_data = json.load(f)
    
    # Load the item data (if available)
    item_data = {}
    try:
        with zipfile.ZipFile(adventure, 'r') as zip_ref:
            with zip_ref.open('items.json', 'r') as f:
                item_data = json.load(f)
    except KeyError:
        pass
    
    if item_name:
        # Check if the item is in the player's inventory
        if item_name in player_inventory:
            # Check if the item has a usage scenario in the current room
            item_usage = item_data.get(item_name, {}).get('usage', {}).get(current_room, {})
            
            if item_usage:
                if 'reveal_object' in item_usage:
                    hidden_object = item_usage['reveal_object']
                    
                    room = story_data['rooms'][current_room]
                    room['items'].append(hidden_object)
                    player_inventory.remove(item_name)
                    
                    item_message = item_usage.get('message', f"Using the {item_name} revealed a {hidden_object} in the room.")
                    return redirect(url_for('adventure_game', item_message=item_message))
                
                elif 'trigger_event' in item_usage:
                    event_id = item_usage['trigger_event']
                    
                    room = story_data['rooms'][current_room]
                    if event_id == 'change_room_state':
                        new_state = item_usage.get('new_state', '')
                        room['state'] = new_state
                        item_message = item_usage.get('message', f"Using the {item_name} changed the room's state to {new_state}.")
                    elif event_id == 'enable_room_exit':
                        exit_direction = item_usage.get('exit_direction', '')
                        exit_room = item_usage.get('exit_room', '')
                        room['exits'][exit_direction] = exit_room
                        item_message = item_usage.get('message', f"Using the {item_name} enabled a new exit to the {exit_direction}.")
                    
                    player_inventory.remove(item_name)
                    return redirect(url_for('adventure_game', item_message=item_message))
                
                elif 'restore_health' in item_usage:
                    health_restored = item_usage.get('health_restored', 0)
                    
                    player_health += health_restored
                    player_inventory.remove(item_name)
                    
                    item_message = item_usage.get('message', f"Using the {item_name} restored {health_restored} health points.")
                    return redirect(url_for('adventure_game', item_message=item_message))
                
                else:
                    item_message = "This item has no use in the current room."
                    return redirect(url_for('adventure_game', item_message=item_message))
            
            else:
                item_message = "This item has no use in the current room."
                return redirect(url_for('adventure_game', item_message=item_message))
        
        else:
            item_message = "You don't have this item in your inventory."
            return redirect(url_for('adventure_game', item_message=item_message))
    
    else:
        item_message = "No item specified."
        return redirect(url_for('adventure_game', item_message=item_message))