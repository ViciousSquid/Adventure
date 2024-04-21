import os
import glob
import json
import random
import zipfile
from flask import url_for

def load_adventures():
    adventures = {}
    adventure_files = glob.glob('adventures/*.zip')

    for file_path in adventure_files:
        adventure_name = os.path.splitext(os.path.basename(file_path))[0]
        adventures[adventure_name] = file_path

    return adventures

def get_adventure_data(adventure_name):
    adventures = load_adventures()
    if adventure_name in adventures:
        adventure_path = adventures[adventure_name]
        with zipfile.ZipFile(adventure_path, 'r') as zip_ref:
            with zip_ref.open('story.json', 'r') as file:
                adventure_data = json.load(file)
                return adventure_data
    return None

def get_start_room(adventure_name):
    adventure_data = get_adventure_data(adventure_name)
    if adventure_data:
        return adventure_data['start_room']
    return None

def get_room_data(adventure_name, room_name):
    adventure_data = get_adventure_data(adventure_name)
    if adventure_data and room_name in adventure_data['rooms']:
        return adventure_data['rooms'][room_name]
    return None

def get_room_image_url(adventure_name, room_name):
    room_data = get_room_data(adventure_name, room_name)
    if room_data and 'image' in room_data:
        return url_for('serve_image', filename=room_data['image'])
    return None

def get_random_adventure():
    adventures = load_adventures()
    return random.choice(list(adventures.keys()))

def get_cover_image_data(adventure_name):
    adventure_path = load_adventures()[adventure_name]
    with zipfile.ZipFile(adventure_path, 'r') as zip_ref:
        try:
            with zip_ref.open('cover.jpg', 'r') as file:
                cover_image_data = file.read()
                return cover_image_data
        except KeyError:
            return None

def get_summary_text(adventure_name):
    adventure_path = load_adventures()[adventure_name]
    with zipfile.ZipFile(adventure_path, 'r') as zip_ref:
        try:
            with zip_ref.open('summary.txt', 'r') as file:
                summary_text = file.read().decode('utf-8')
                return summary_text
        except KeyError:
            return None