import os
import json
import zipfile
from adventures import ADVENTURES

def story_editor(current_adventure):
    if current_adventure is None:
        return None

    adventure_zip = ADVENTURES[current_adventure]

    adventure = None
    images_folder = None

    try:
        with zipfile.ZipFile(adventure_zip, 'r') as zip_ref:
            # Extract the story JSON file
            json_file = zip_ref.extract(zip_ref.namelist()[0], 'temp')

            with open(json_file, 'r') as f:
                adventure = json.load(f)

            # Extract the images folder
            images_folder = os.path.splitext(json_file)[0] + '_images'
            zip_ref.extractall(images_folder)

            adventure['images_folder'] = images_folder

            os.remove(json_file)
    except (IndexError, zipfile.BadZipFile):
        # Handle the case when the ZIP file is empty or corrupted
        print(f"Error: Unable to extract story data from '{adventure_zip}'")

    if adventure is None:
        return None

    nodes = []
    edges = []

    for room_name, room_data in adventure['rooms'].items():
        node = {
            'id': room_name,
            'label': room_name,
            'title': room_data['description']
        }
        nodes.append(node)

        for direction, connected_room in room_data['exits'].items():
            if connected_room:
                edge = {
                    'from': room_name,
                    'to': connected_room,
                    'label': direction.capitalize()
                }
                edges.append(edge)

    return {
        'nodes': nodes,
        'edges': edges,
        'adventure_name': current_adventure,
        'images_folder': images_folder
    }