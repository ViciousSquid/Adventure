from flask import render_template, request, redirect, url_for, session
from main import app
from adventures import load_adventures
from werkzeug.utils import secure_filename
from data.editor_stuff import story_editor, save_story, editor_route, load_story, graph_view, serve_thumbnail, serve_image, upload_story, generate_thumbnail
import os
import zipfile
import tempfile
import json

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'zip'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/editor')
def editor_route():
    return render_template('editor/index.html')

@app.route('/editor/stories')
def stories_route():
    adventures = load_adventures()
    return render_template('editor/stories.html', adventures=adventures)

@app.route('/editor/edit')
def edit_route():
    story_name = request.args.get('story')
    story_data = story_editor(story_name)
    return render_template('editor/edit.html', story=story_data, story_name=story_name)

@app.route('/editor/save', methods=['POST'])
def save_route():
    story_name = request.form['story_name']
    story_data = request.form['story_data']
    save_story(story_name, story_data)
    return redirect(url_for('stories_route'))

@app.route('/editor/load')
def load_route():
    story_name = request.args.get('story')
    story_data = load_story(story_name)
    return story_data

@app.route('/editor/graph')
def graph_route():
    story_name = request.args.get('story')
    graph_data = graph_view(story_name)
    return render_template('editor/graph.html', graph_data=graph_data, story_name=story_name)

@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    return serve_thumbnail(filename)

@app.route('/upload_story', methods=['POST'])
def upload_story():
    print("Entering upload_story function")

    if 'story_file' not in request.files:
        print("No story file found in request")
        return redirect(url_for('main_menu'))

    story_file = request.files['story_file']
    if story_file.filename == '':
        print("Empty story filename")
        return redirect(url_for('main_menu'))

    if story_file and allowed_file(story_file.filename):
        print("Processing story file:", story_file.filename)
        filename = secure_filename(story_file.filename)
        story_name = os.path.splitext(filename)[0]  # Get the filename without extension

        # Save the file with the .zip extension in the adventures directory
        story_file.save(os.path.join('adventures', filename))

        # Store the ZIP file data in a temporary file
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, filename)
        story_file.save(temp_file_path)

        # Store the temporary file path in the session
        session['story_zip_file_path'] = temp_file_path

        print("Redirecting to new_story with story_name:", story_name)
        return redirect(url_for('new_story', story_name=story_name))
    else:
        print("Invalid story file")

    print("Redirecting to main_menu")
    return redirect(url_for('main_menu'))

@app.route('/editor/generate_thumbnail', methods=['POST'])
def generate_thumbnail_route():
    room_id = request.form['room_id']
    story_name = request.form['story_name']
    generate_thumbnail(room_id, story_name)
    return 'OK'