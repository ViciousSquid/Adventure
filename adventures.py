import os

def load_adventures():
    adventures = {}
    stories_dir = 'stories'

    for filename in os.listdir(stories_dir):
        if filename.endswith('.zip'):
            story_name = os.path.splitext(filename)[0]
            adventures[story_name] = os.path.join(stories_dir, filename)

    return adventures

ADVENTURES = load_adventures()