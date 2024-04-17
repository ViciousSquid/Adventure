print("* Init...")
import re
import json
import zipfile
from flask import Flask, render_template, request, redirect, url_for, make_response, send_from_directory, jsonify, send_file, flash, session
from adventures import load_adventures
from data.editor_stuff import story_editor, save_story, editor_route, load_story, graph_view, serve_thumbnail, serve_image, upload_story, generate_thumbnail
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
import ast
import random
from dicerollAPI.diceroll import DiceRoller
from dicerollAPI.diceroll_anim import DiceAnimator
from dicerollAPI.diceroll_api import dicerollAPI

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

# Import routes from data/routes_*
from data.routes_main import *
from data.routes_adventure import *
from data.routes_editor import *
from data.routes_utility import *

if __name__ == '__main__':
    app.run(debug=False)