from flask import render_template, send_from_directory, session, request, make_response, jsonify
from main import app, load_adventures
from adventures import get_cover_image_data, get_summary_text
import base64

@app.route('/', methods=['GET', 'POST'])
def main_menu():
    adventures = load_adventures()
    
    if request.method == 'POST':
        selected_story = request.form.get('story_name')
        return redirect(url_for('play', story_name=selected_story))
    else:
        selected_story = 'Cosmic_paradox'
    
    if 'story_uploaded' in session and session['story_uploaded']:
        story_name = session['story_uploaded']
        session.pop('story_uploaded', None)
        return redirect(url_for('play', story_name=story_name))
    
    cover_image_data = get_cover_image_data('Cosmic_paradox')
    summary_text = get_summary_text('Cosmic_paradox')

    return render_template('main_menu.html', adventures=adventures, selected_story=selected_story, cover_image_data=cover_image_data, summary_text=summary_text)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/fonts/<path:filename>')
def serve_fonts(filename):
    return send_from_directory('fonts', filename)

@app.route('/get_story_data')
def get_story_data():
    story_name = request.args.get('story_name')
    cover_image_data = get_cover_image_data(story_name)
    summary_text = get_summary_text(story_name)

    if cover_image_data:
        cover_image_data = base64.b64encode(cover_image_data).decode('utf-8')

    data = {
        'cover_image_data': cover_image_data,
        'summary_text': summary_text
    }

    return jsonify(data)