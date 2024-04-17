from flask import render_template, send_from_directory, session
from main import app, load_adventures


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