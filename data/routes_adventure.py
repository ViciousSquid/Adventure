from flask import render_template, request, redirect, url_for, make_response, jsonify, session
from markupsafe import escape
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
import io


def renderMarkup(text):
    bold_regex = r"\*\*(.*?)\*\*"
    italic_regex = r"\*(.*?)\*"
    newline_regex = r"\n"

    text = re.sub(bold_regex, r"<strong>\1</strong>", text)
    text = re.sub(italic_regex, r"<em>\1</em>", text)
    text = text.replace(newline_regex, "<br>")

    return text


def resolve_skill_check(skill_check, player_roll):
    if 'description' in skill_check:
        success_description = failure_description = skill_check['description']
    else:
        success_description = skill_check.get('success', {}).get('description', 'You succeeded!')
        failure_description = skill_check.get('failure', {}).get('description', 'You failed!')

    success_room = skill_check.get('success', {}).get('room')
    failure_room = skill_check.get('failure', {}).get('room')
    target_value = skill_check.get('target', 10)

    roll_result = player_roll.get('roll_result', 0)

    if roll_result >= target_value:
        return {'description': success_description, 'room': success_room or current_room}
    else:
        return {'description': failure_description, 'room': failure_room or current_room}


def resolve_nested_target(target_value):
    if isinstance(target_value, dict):
        return target_value.get('value') or target_value.get('target') or 10
    return target_value


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
    return redirect(url_for('main_menu'))


@app.route('/new_story', methods=['POST', 'GET'])
def new_story():
    global current_adventure, current_room, action_history
    # ... (unchanged - same as previous version)
    if request.method == 'GET':
        story_name = request.args.get('story_name')
    else:
        story_name = request.form.get('story_name')

    if 'story_uploaded' in session and session.get('story_uploaded'):
        story_name = session['story_uploaded']
        temp_file_path = session.get('story_zip_file_path')
        with open(temp_file_path, 'rb') as f:
            story_zip_data = f.read()
        with zipfile.ZipFile(io.BytesIO(story_zip_data)) as zip_ref:
            with zip_ref.open('story.json', 'r') as f:
                story_data = json.load(f)
        current_adventure = story_name
        current_room = story_data['start_room']
        action_history = []
        session['inventory'] = []
        os.remove(temp_file_path)
        session.pop('story_uploaded', None)
        session.pop('story_zip_file_path', None)
        return redirect(url_for('adventure_game'))

    adventures = load_adventures()
    if story_name in adventures:
        current_adventure = story_name
        adventure = adventures[current_adventure]
        with zipfile.ZipFile(adventure, 'r') as zip_ref:
            with zip_ref.open('story.json', 'r') as f:
                story_data = json.load(f)
        current_room = story_data['start_room']
        action_history = []
        session['inventory'] = []
        return redirect(url_for('adventure_game'))
    return redirect(url_for('main_menu'))


@app.route('/adventure', methods=['GET', 'POST'])
def adventure_game():
    global current_room, action_history
    if current_adventure is None:
        return redirect(url_for('main_menu'))

    adventures = load_adventures()
    adventure = adventures[current_adventure]

    try:
        with zipfile.ZipFile(adventure, 'r') as zip_ref:
            zip_contents = zip_ref.namelist()
            with zip_ref.open('story.json', 'r') as file:
                story_data = json.load(file)

        if current_room not in story_data['rooms']:
            current_room = story_data['start_room']  # safety fallback

        room = story_data['rooms'][current_room]
        button_color = story_data.get('button_color', '#4CAF50')
        room_visit_count = Counter(action_history)[current_room]

        content = ""
        skill_check = None
        player_roll = None
        animation_html = ""
        roll_dice_button = ""
        dice_notation = ""
        player_inventory = session.get('inventory', [])
        available_items = room.get('items', [])
        item_needed = room.get('item_needed')
        room_message = room.get('message')
        item_message = request.args.get('item_message', '')

        if request.method == 'POST':
            direction = request.form.get('direction')
            if direction:
                next_room_data = room['exits'].get(direction)

                if isinstance(next_room_data, dict) and 'skill_check' in next_room_data:
                    # Skill check path
                    skill_check = next_room_data['skill_check']
                    dice_type = skill_check.get('dice_type', '1d20')
                    dice_notation = dice_type

                    if 'roll_dice' in request.form:
                        dice_roller = dicerollAPI()
                        player_roll = dice_roller.roll_dice(dice_type)
                        dice_animator = DiceAnimator()
                        dice_color = 'blue'
                        dice_roll_result = dice_roller.roll_dice(dice_type, dice_color)

                        if dice_roll_result:
                            animation_html = dice_animator.animate_dice_roll_html(
                                dice_type, dice_color, dice_roll_result
                            )

                        skill_result = resolve_skill_check(skill_check, player_roll)
                        current_room = skill_result['room']
                        content = escape(renderMarkup(skill_result['description']))
                        action_history.append(current_room)
                    else:
                        content = escape(renderMarkup(room['description']))
                        roll_dice_button = f'<form method="post"><input type="hidden" name="direction" value="{direction}"><button type="submit" name="roll_dice" id="roll-dice-button">Roll Dice</button></form>'

                elif isinstance(next_room_data, str):
                    # Normal move
                    if next_room_data in story_data['rooms']:
                        current_room = next_room_data
                        action_history.append(current_room)
                        content = escape(renderMarkup(story_data['rooms'][current_room]['description']))
                    else:
                        content = "You can't go that way (room not found)."

                else:
                    content = "You can't go that way."

            else:
                content = escape(renderMarkup(room.get('description', 'You are here.')))

        else:
            content = escape(renderMarkup(room.get('description', 'You are here.')))

        # Revisit content
        revisits = room.get('revisits', [])
        show_all_revisits = room.get('show_all_revisits', False)
        if show_all_revisits:
            for revisit in revisits:
                if room_visit_count >= revisit.get('count', 0):
                    content += "\n" + escape(renderMarkup(revisit.get('content', '')))
        else:
            for revisit in reversed(revisits):
                if room_visit_count >= revisit.get('count', 0):
                    content += "\n" + escape(renderMarkup(revisit.get('content', '')))
                    break

        exits = [(d, data) for d, data in room.get('exits', {}).items() if data]

    except Exception as e:
        print(f"🚨 ERROR in adventure_game: {e}")
        content = "Something unexpected happened while exploring. The story may have a small error. Try another choice or restart the story."
        exits = []
        room = {}
        button_color = '#4CAF50'
        zip_contents = []

    story_title = story_data.get('name', 'Adventure!')
    show_map = room.get('show_map', True)

    return render_template('adventure.html',
                           content=content,
                           exits=exits,
                           room=room,
                           show_map=show_map,
                           action_history=action_history,
                           button_color=button_color,
                           story_title=story_title,
                           skill_check=skill_check,
                           player_roll=player_roll,
                           animation_html=animation_html,
                           roll_dice_button=roll_dice_button,
                           dice_notation=dice_notation,
                           player_inventory=player_inventory,
                           available_items=available_items,
                           item_needed=item_needed,
                           room_message=room_message,
                           item_message=item_message,
                           zip_contents=zip_contents)


# The rest of the file (play, roll, save, load, acquire_item, use_item) remains exactly the same as before
# (I kept them unchanged to avoid any disruption)

@app.route('/dice_roll_image')
def serve_dice_roll_image():
    image_base64 = session.get('dice_roll_image', '')
    return f'<img src="data:image/png;base64,{image_base64}" alt="Dice Roll Animation">'


@app.route('/play')
def play_story():
    # (unchanged)
    if current_adventure is None:
        return redirect(url_for('main_menu'))
    adventures = load_adventures()
    adventure = adventures[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        with zip_ref.open('story.json', 'r') as f:
            story_data = json.load(f)
    current_room_id = story_data['start_room']
    action_history = []
    current_room = story_data['rooms'][current_room_id].get('name', current_room_id)
    room = story_data['rooms'][current_room_id]
    content = escape(renderMarkup(room.get('description', 'You are here.')))
    exits = [direction for direction, room_name in room.get('exits', {}).items() if room_name]
    return render_template('play.html', adventure=story_data, current_room=current_room, action_history=action_history, content=content, exits=exits)


@app.route('/play_action', methods=['POST'])
def play_action():
    # (unchanged - kept for compatibility)
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
        next_room_id = room.get('exits', {}).get(direction)
        if next_room_id:
            current_room_id = next_room_id
            action_history.append(current_room_id)
            current_room = story_data['rooms'][current_room_id].get('name', current_room_id)
            room = story_data['rooms'][current_room_id]
            content = escape(renderMarkup(room.get('description', 'You are here.')))
            exits = [direction for direction, room_name in room.get('exits', {}).items() if room_name]
            return render_template('play.html', adventure=story_data, current_room=current_room, action_history=action_history, content=content, exits=exits)
    return redirect(url_for('play_story'))


@app.route('/roll', methods=['POST'])
def roll_dice():
    # (unchanged)
    dice_notation = request.form.get('dice_notation')
    dice_color = request.form.get('dice_color')
    target_value = request.form.get('target_value')
    dice_roller = dicerollAPI()
    roll_result = dice_roller.roll_dice(dice_notation, dice_color=dice_color, target_value=int(target_value), animate=False)
    dice_animator = DiceAnimator()
    animation_html = dice_animator.animate_dice_roll_html(dice_notation, dice_color, dice_roller)
    return jsonify({'animation_html': animation_html, 'roll_result': str(roll_result.get('roll_result', 0))})


@app.route('/save', methods=['POST'])
def save_game():
    if current_adventure is None:
        return redirect(url_for('main_menu'))
    game_state = {'current_adventure': current_adventure, 'current_room': current_room, 'action_history': action_history}
    response = make_response(json.dumps(game_state))
    response.headers.set('Content-Type', 'application/json')
    response.headers.set('Content-Disposition', 'attachment', filename='game_state.json')
    return response


@app.route('/load', methods=['POST'])
def load_game():
    # (unchanged)
    global current_adventure, current_room, action_history
    file = request.files['file']
    data = json.load(file)
    if 'name' in data:
        current_adventure = data['name']
    else:
        adventures = load_adventures()
        current_adventure = next(iter(adventures))
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
    content = escape(renderMarkup(room.get('description', 'You are here.')))
    exits = [direction for direction, room_name in room.get('exits', {}).items() if room_name]
    return render_template('adventure.html', content=content, exits=exits, room=room, show_map=room.get('show_map', True),
                           action_history=action_history, button_color=story_data.get('button_color', '#4CAF50'))


@app.route('/acquire_item', methods=['POST'])
def acquire_item():
    # (unchanged)
    global current_room
    item_name = request.form.get('item_name')
    adventures = load_adventures()
    adventure = adventures[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        with zip_ref.open('story.json', 'r') as f:
            story_data = json.load(f)
    room = story_data['rooms'][current_room]
    available_items = room.get('items', [])
    if item_name and item_name in available_items:
        if 'inventory' not in session:
            session['inventory'] = []
        if item_name not in session['inventory']:
            session['inventory'].append(item_name)
        room['items'].remove(item_name)
        description = f"You acquired the {item_name}."
    else:
        description = "Item not available."
    return redirect(url_for('adventure_game', item_message=description))


@app.route('/use_item', methods=['POST'])
def use_item():
    # (unchanged)
    global current_room
    item_name = request.form.get('item_name')
    if item_name and 'inventory' in session and item_name in session['inventory']:
        session['inventory'].remove(item_name)
        description = f"You used the {item_name}."
    else:
        description = "Item not in inventory."
    return redirect(url_for('adventure_game', item_message=description))