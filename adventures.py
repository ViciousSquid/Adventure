import os

ADVENTURES = {}
STORIES_DIR = 'stories'

# Scan the 'stories' folder for story files and populate the ADVENTURES dictionary

for filename in os.listdir(STORIES_DIR):
    if filename.endswith('.zip'):
        story_name = os.path.splitext(filename)[0]
        ADVENTURES[story_name] = os.path.join(STORIES_DIR, filename)