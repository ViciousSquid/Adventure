import json
import datetime
import zipfile
import io
import os
import werkzeug
import datetime
from flask import render_template, request, redirect, url_for, jsonify, send_file, send_from_directory, flash, session
from adventures import load_adventures
from PIL import Image
from werkzeug.utils import secure_filename

def story_editor(current_adventure):
    adventures = load_adventures()
    adventure = adventures[current_adventure]
    with zipfile.ZipFile(adventure, 'r') as zip_ref:
        with zip_ref.open('story.json', 'r') as f:
            story_data = json.load(f)
    return story_data

def save_story():
    try:
        story_data = json.loads(request.form['story'])
        print("> Story JSON received from editor.")

        story_name = story_data['name']
        print("Story name:", story_name)

        # Save the story JSON data to a file in the /logs folder if logging is enabled
        debug_mode = os.path.exists('debug.txt')
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

def graph_view():
    return send_from_directory('static/editor', 'graph.html')

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