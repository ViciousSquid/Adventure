from flask import render_template, request, redirect, url_for, jsonify, send_from_directory, flash, session
from main import app
from data.editor_stuff import story_editor, save_story, load_story, graph_view, serve_thumbnail, serve_image, upload_story, generate_thumbnail
import os
from werkzeug.utils import secure_filename

@app.route('/editor')
def editor_route():
    adventures = load_adventures()
    return render_template('editor.html', adventures=adventures)

@app.route('/load_story', methods=['POST'])
def load_story():
    story_name = request.form['story_name']
    story_data = story_editor(story_name)
    return jsonify(story_data)

@app.route('/save_story', methods=['POST'])
def save_story():
    story_name = request.form['story_name']
    story_data = request.form['story_data']
    story_data = json.loads(story_data)
    save_story(story_name, story_data)
    return jsonify({'status': 'success'})

@app.route('/editor/graph')
def graph_view():
    story_name = request.args.get('story_name')
    story_data = story_editor(story_name)
    return render_template('graph.html', story_data=story_data)

@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    return send_from_directory('thumbnails', filename)

@app.route('/images/<path:filename>', endpoint='serve_image_editor')
def serve_image_editor(filename):
    return send_from_directory('images', filename)

@app.route('/upload_story', methods=['POST'])
def upload_story():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('editor_route'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('editor_route'))
    if file and file.filename.endswith('.zip'):
        filename = secure_filename(file.filename)
        file_path = os.path.join('adventures', filename)
        file.save(file_path)
        session['story_uploaded'] = filename[:-4]  # Remove the .zip extension
        return redirect(url_for('editor_route'))
    return redirect(url_for('editor_route'))

@app.route('/generate_thumbnail', methods=['POST'])
def generate_thumbnail():
    story_name = request.form['story_name']
    generate_thumbnail(story_name)
    return jsonify({'status': 'success'})