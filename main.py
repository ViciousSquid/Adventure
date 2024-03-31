print ("  ____  ___    __ __    ___  ____   ______  __ __  ____     ___  __ ")
print (" /    ||   \  |  |  |  /  _]|    \ |      ||  |  ||    \   /  _]|  |")
print ("|  o  ||    \ |  |  | /  [_ |  _  ||      ||  |  ||  D  ) /  [_ |  |")
print ("|     ||  D  ||  |  ||    _]|  |  ||_|  |_||  |  ||    / |    _]|__|")
print ("|  _  ||     ||  :  ||   [_ |  |  |  |  |  |  :  ||    \ |   [_  __ ")
print ("|  |  ||     | \   / |     ||  |  |  |  |  |     ||  .  \|     ||  |")
print ("|__|__||_____|  \_/  |_____||__|__|  |__|   \__,_||__|\_||_____||__|")
print ("")
print ("            https://github.com/ViciousSquid/Adventure")
print ("")
print ("* Initialising libraries")
print ("")

import json
import zipfile
from flask import Flask, render_template, request, redirect, url_for, make_response, send_from_directory, jsonify
from adventures import ADVENTURES, STORIES_DIR
from story_editor import story_editor
import os
from PIL import Image


app = Flask(__name__)

current_adventure = None
current_room = None
action_history = []

print ("* Serving webpage via HTTP on port 5000")

@app.route('/')
def main_menu():
    return render_template('main_menu.html', adventures=ADVENTURES)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/new_story', methods=['POST'])
def new_story():
    global current_adventure, current_room, action_history
    story_name = request.form.get('story_name')
    if story_name in ADVENTURES:
        current_adventure = story_name
        print(f"Current adventure set to: {current_adventure}")  # Add this line
        adventure = ADVENTURES[current_adventure]
        with zipfile.ZipFile(adventure, 'r') as zip_ref:
            with zip_ref.open('story.json', 'r') as f:
                story_data = json.load(f)
        current_room = story_data['start_room']
        action_history = []  # Reset action history for new story
        return redirect(url_for('adventure_game'))
    else:
        return redirect(url_for('main_menu'))

@app.route('/adventure', methods=['GET', 'POST'])
def adventure_game():
    global current_room, action_history
    if current_adventure is None:
        return redirect(url_for('main_menu'))

    adventure = ADVENTURES[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        with zip_ref.open('story.json', 'r') as f:
            story_data = json.load(f)
    room = story_data['rooms'][current_room]
    button_color = story_data.get('button_color', '#4CAF50')  # Default color if not specified in the story

    if request.method == 'POST':
        direction = request.form.get('direction')
        if direction:
            next_room = room['exits'].get(direction, None)
            if next_room:
                current_room = next_room
                room = story_data['rooms'][current_room]
                action_history.append(direction)
            else:
                return render_template('adventure.html', content="You can't go that way.", room=room, action_history=action_history, button_color=button_color)

    content = room['description']
    exits = [direction for direction, room_name in room['exits'].items() if room_name]
    show_map = room.get('show_map', True)
    return render_template('adventure.html', content=content, exits=exits, room=room, show_map=show_map, action_history=action_history, button_color=button_color)

@app.route('/play')
def play_story():
    if current_adventure is None:
        return redirect(url_for('main_menu'))

    adventure = ADVENTURES[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        with zip_ref.open('story.json', 'r') as f:
            story_data = json.load(f)
    current_room = story_data['start_room']
    action_history = []

    return render_template('play.html', adventure=story_data, current_room=current_room, action_history=action_history)

@app.route('/play_action', methods=['POST'])
def play_action():
    global current_room, action_history
    if current_adventure is None:
        return redirect(url_for('main_menu'))

    adventure = ADVENTURES[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        with zip_ref.open('story.json', 'r') as f:
            story_data = json.load(f)
    direction = request.form.get('direction')
    if direction:
        room = story_data['rooms'][current_room]
        next_room = room['exits'].get(direction, None)
        if next_room:
            current_room = next_room
            action_history.append(direction)
            room = story_data['rooms'][current_room]
            content = room['description']
            exits = [direction for direction, room_name in room['exits'].items() if room_name]
            return render_template('play.html', adventure=story_data, current_room=current_room, action_history=action_history, content=content, exits=exits)
        else:
            return render_template('play.html', adventure=story_data, current_room=current_room, action_history=action_history, content="You can't go that way.")
    else:
        return redirect(url_for('play_story'))

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
        current_adventure = next(iter(ADVENTURES))  # Get the first adventure name
        with zipfile.ZipFile(ADVENTURES[current_adventure], 'r') as zip_ref:
            with zip_ref.open('story.json', 'r') as f:
                data = json.load(f)

    with zipfile.ZipFile(ADVENTURES[current_adventure], 'r') as zip_ref:
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

@app.route('/editor', methods=['GET'])
def editor_route():
    print("Editor route called")
    if current_adventure is None:
        print("Current adventure is None")
        return redirect(url_for('main_menu'))
    else:
        print(f"Current adventure: {current_adventure}")
        story_data = story_editor(current_adventure)
        if story_data is None:
            print("Error: Unable to load story data for the current adventure.")
            return redirect(url_for('main_menu'))
        else:
            print("Rendering editor/index.html template")
            return render_template('editor/index.html', story_data=story_data)

@app.route('/load_story', methods=['POST'])
def load_story():
    global current_adventure, current_room, action_history
    story_name = request.form.get('story_name')
    if story_name in ADVENTURES:
        current_adventure = story_name
        adventure = ADVENTURES[current_adventure]
        with zipfile.ZipFile(adventure, 'r') as zip_ref:
            with zip_ref.open('story.json', 'r') as f:
                story_data = json.load(f)
        current_room = story_data['start_room']
        action_history = []
        return redirect(url_for('play_story'))
    else:
        return redirect(url_for('main_menu'))

@app.route('/save_story', methods=['POST'])
def save_story():
    story_data = request.get_json()
    story_name = story_data['name']
    story_path = os.path.join(STORIES_DIR, f"{story_name}.zip")

    with zipfile.ZipFile(story_path, 'w') as zip_file:
        zip_file.writestr('story.json', json.dumps(story_data, indent=2))
        for room_name, room_data in story_data['rooms'].items():
            if room_data['image']:
                image_filename = f"room-{room_name}-image.{room_data['image'].filename.split('.')[-1]}"
                zip_file.writestr(image_filename, room_data['image'].read())

    return jsonify({'message': 'Story saved successfully'}), 200

@app.route('/editor/graph')
def graph_view():
    return send_from_directory('static/editor', 'graph.html')

@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    if current_adventure is None:
        return redirect(url_for('main_menu'))

    adventure = ADVENTURES[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        try:
            thumbnail_path = os.path.join(STORIES_DIR, f'thumbnail_{filename}')
            if not os.path.exists(thumbnail_path):
                # Generate the thumbnail on the fly
                image_path = os.path.join(STORIES_DIR, filename)
                generate_thumbnail(image_path, thumbnail_path)
            return send_from_directory(STORIES_DIR, f'thumbnail_{filename}')
        except werkzeug.exceptions.NotFound:
            return redirect(url_for('main_menu'))

@app.route('/images/<path:filename>')
def serve_image(filename):
    if current_adventure is None:
        return redirect(url_for('main_menu'))

    adventure = ADVENTURES[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        try:
            return send_from_directory(STORIES_DIR, filename)
        except werkzeug.exceptions.NotFound:
            return redirect(url_for('main_menu'))

def generate_thumbnail(image_path, thumbnail_path, size=(100, 100)):
    from PIL import Image
    image = Image.open(image_path)
    image.thumbnail(size)
    image.save(thumbnail_path)

if __name__ == '__main__':
    app.run(debug=True)