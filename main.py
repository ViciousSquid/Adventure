import re

print("* Init...")
import json
import zipfile
from flask import Flask, render_template, request, redirect, url_for, make_response, send_from_directory, jsonify, send_file, flash, session
from adventures import load_adventures
from story_editor import story_editor
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
        print("\033[94m>encountered a choice point\033[0m")

    if request.method == 'POST':
        direction = request.form.get('direction')
        if direction:
            next_room = room['exits'].get(direction, None)
            if next_room:
                current_room = next_room
                room = story_data['rooms'][current_room]
                action_history.append(current_room)
            else:
                return render_template('adventure.html', content="You can't go that way.", room=room, action_history=action_history, button_color=button_color)
        
        # Check if the player has reached an ending
        if not room['exits']:
            print("\033[92m>Player reached an ending\033[0m")

    content = room['description']
    exits = [direction for direction, room_name in room['exits'].items() if room_name]
    show_map = room.get('show_map', True)
    story_title = story_data['name']

    # Check if the player has visited the current room enough times to unlock a new branch
    revisit_count = room.get('revisit_count', 0)
    if room_visit_count >= revisit_count:
        # Add additional content or options from the story.json file
        additional_content = room.get('revisit_content', "")
        content += "\n" + additional_content

    return render_template('adventure.html', content=content, exits=exits, room=room, show_map=show_map, action_history=action_history, button_color=button_color, story_title=story_title)

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
            print(">>Editor")
            print("Rendering editor/index.html template")
            return render_template('editor/index.html', story_data=story_data)

@app.route('/load_story', methods=['POST'])
def load_story():
    global current_adventure, current_room, action_history
    story_name = request.form.get('story_name')
    adventures = load_adventures()
    if story_name in adventures:
        current_adventure = story_name
        adventure = adventures[current_adventure]
        with zipfile.ZipFile(adventure, 'r') as zip_ref:
            with zip_ref.open('story.json', 'r') as f:
                story_data = json.load(f)
        current_room = story_data['start_room']
        action_history = []
        print(">>Load story")
        return redirect(url_for('play_story'))
    else:
        return redirect(url_for('main_menu'))

@app.route('/save_story', methods=['POST'])
def save_story():
    try:
        story_data = json.loads(request.form['story'])
        print("> Story JSON received from editor.")

        story_name = story_data['name']
        print("Story name:", story_name)

        # Save the story JSON data to a file in the /logs folder if logging is enabled
        if debug_mode:
            logs_dir = 'logs'
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)

            current_datetime = datetime.datetime.now().strftime("%d%m_%H%M")
            story_json_file = os.path.join(logs_dir, f'story_{story_name}_{current_datetime}.json')

            with open(story_json_file, 'w') as file:
                json.dump(story_data, file, indent=2)
        print("> The json has been saved to the /logs folder.")

        # Create a BytesIO object to hold the zip file data
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr('story.json', json.dumps(story_data, indent=2))
            for room_name, room_data in story_data['rooms'].items():
                if room_data['image']:
                    image_filename = room_data['image']
                    for file_name, file_data in request.files.items():
                        if file_name == f"room-{image_filename}":
                            zip_file.writestr(image_filename, file_data.read())
                            break
        print("> ZIP was created and sent to the browser window")

        # Move the buffer pointer to the beginning
        zip_buffer.seek(0)

        # Send the zip file as a response for download
        return send_file(zip_buffer, as_attachment=True, download_name=f"story_{story_name}.zip", mimetype="application/zip")
    except Exception as e:
        print("Error saving the story:", str(e))
        return jsonify({'error': 'An error occurred while saving the story.'}), 500

@app.route('/editor/graph')
def graph_view():
    return send_from_directory('static/editor', 'graph.html')

@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    if current_adventure is None:
        return redirect(url_for('main_menu'))

    adventures = load_adventures()
    adventure = adventures[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        try:
            thumbnail_path = os.path.join('stories', f'thumbnail_{filename}')
            if not os.path.exists(thumbnail_path):
                # Generate the thumbnail on the fly
                image_path = os.path.join('stories', filename)
                generate_thumbnail(image_path, thumbnail_path)
            return send_from_directory('stories', f'thumbnail_{filename}')
        except werkzeug.exceptions.NotFound:
            return redirect(url_for('main_menu'))

@app.route('/images/<path:filename>')
def serve_image(filename):
    adventures = load_adventures()
    if current_adventure not in adventures:
        return redirect(url_for('main_menu'))

    adventure = adventures[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        try:
            image_data = zip_ref.read(filename)
            response = make_response(image_data)
            response.headers.set('Content-Type', 'image/jpeg')  # Read the image
            return response
        except KeyError:
            return redirect(url_for('main_menu'))

@app.route('/upload_story', methods=['POST'])
def upload_story():
    if 'story_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    print("> Upload a story")

    story_file = request.files['story_file']
    if story_file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if story_file and story_file.filename.endswith('.zip'):
        filename = secure_filename(story_file.filename)
        story_file.save(os.path.join('stories', filename))
        flash('Story uploaded successfully')
        story_name = os.path.splitext(filename)[0]
        session['story_uploaded'] = story_name
    else:
        flash('Invalid file type. Please upload a ZIP file.')

    return redirect(url_for('main_menu'))

def generate_thumbnail(image_path, thumbnail_path, size=(100, 100)):
    from PIL import Image
    image = Image.open(image_path)
    image.thumbnail(size)
    image.save(thumbnail_path)

if __name__ == '__main__':
    app.run(debug=False)