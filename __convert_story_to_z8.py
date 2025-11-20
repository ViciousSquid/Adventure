#!/usr/bin/env python3
"""
CYOA to Interactive Fiction Converter
Converts Choose-Your-Own-Adventure JSON files to Z-Machine or Glulx formats
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional
import threading
import zipfile
import io


class CYOAConverter:
    """Handles conversion logic from CYOA JSON to Inform 7 to compiled IF"""
    
    def __init__(self):
        self.story_data = None
        self.source_filename = None
        
    def load_json(self, filepath: str) -> bool:
        """Load and validate CYOA JSON file (supports both loose JSON and ZIP archives)"""
        try:
            file_path = Path(filepath)
            self.source_filename = file_path.name
            
            # Check if it's a ZIP file
            if file_path.suffix.lower() == '.zip':
                return self._load_from_zip(filepath)
            else:
                return self._load_from_json(filepath)
            
        except Exception as e:
            raise Exception(f"Failed to load file: {str(e)}")
    
    def _load_from_json(self, filepath: str) -> bool:
        """Load JSON from a regular file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.story_data = json.load(f)
        
        self._validate_story_data()
        return True
    
    def _load_from_zip(self, filepath: str) -> bool:
        """Load JSON from inside a ZIP archive"""
        with zipfile.ZipFile(filepath, 'r') as zip_file:
            # Find JSON files in the archive
            json_files = [name for name in zip_file.namelist() 
                         if name.lower().endswith('.json') and not name.startswith('__MACOSX')]
            
            if not json_files:
                raise ValueError("No JSON files found in ZIP archive")
            
            if len(json_files) > 1:
                # If multiple JSON files, try to find one with 'story' or 'cyoa' in name
                candidates = [f for f in json_files if any(
                    keyword in f.lower() for keyword in ['story', 'cyoa', 'adventure']
                )]
                json_file = candidates[0] if candidates else json_files[0]
            else:
                json_file = json_files[0]
            
            # Read and parse the JSON
            with zip_file.open(json_file) as f:
                content = f.read().decode('utf-8')
                self.story_data = json.loads(content)
            
            self.source_filename = f"{Path(filepath).stem} ({json_file})"
        
        self._validate_story_data()
        return True
    
    def _validate_story_data(self):
        """Validate that the loaded JSON has required fields"""
        # Detect format type
        if 'rooms' in self.story_data:
            # Room-based format (new format)
            if 'name' not in self.story_data:
                raise ValueError("JSON must contain 'name' field")
            if not self.story_data['rooms']:
                raise ValueError("Story must contain at least one room")
            # Normalize to internal format
            self.story_data['title'] = self.story_data.get('name', 'Untitled')
            self.story_data['start'] = self.story_data.get('start_room', list(self.story_data['rooms'].keys())[0])
            self.story_data['scenes'] = self._convert_rooms_to_scenes(self.story_data['rooms'])
        elif 'scenes' in self.story_data:
            # Scene-based format (original format)
            if 'title' not in self.story_data:
                raise ValueError("JSON must contain 'title' field")
            if not self.story_data['scenes']:
                raise ValueError("Story must contain at least one scene")
        else:
            raise ValueError("JSON must contain either 'scenes' or 'rooms' field")
    
    def _convert_rooms_to_scenes(self, rooms: dict) -> dict:
        """Convert room-based format to scene-based format"""
        scenes = {}
        
        for room_id, room_data in rooms.items():
            scene = {
                'text': room_data.get('description', 'You are here.'),
                'choices': []
            }
            
            exits = room_data.get('exits', {})
            
            for exit_text, exit_target in exits.items():
                if exit_target is None:
                    # Ending choice
                    continue
                
                # Handle skill checks
                if isinstance(exit_target, dict) and 'skill_check' in exit_target:
                    skill_check = exit_target['skill_check']
                    # Create choices for both success and failure
                    scene['choices'].append({
                        'text': self._humanize_text(exit_text),
                        'next': room_id + '_skill_check_' + exit_text,
                        'skill_check': skill_check
                    })
                    
                    # Create intermediate scenes for skill check outcomes
                    # Success scene
                    success_data = skill_check.get('success', {})
                    success_scene_id = room_id + '_skill_check_' + exit_text + '_success'
                    scenes[success_scene_id] = {
                        'text': success_data.get('description', 'You succeeded!'),
                        'choices': [{
                            'text': 'Continue',
                            'next': success_data.get('room', room_id)
                        }]
                    }
                    
                    # Failure scene
                    failure_data = skill_check.get('failure', {})
                    failure_scene_id = room_id + '_skill_check_' + exit_text + '_failure'
                    scenes[failure_scene_id] = {
                        'text': failure_data.get('description', 'You failed!'),
                        'choices': [{
                            'text': 'Continue',
                            'next': failure_data.get('room', room_id)
                        }]
                    }
                    
                    # Create skill check scene
                    skill_scene_id = room_id + '_skill_check_' + exit_text
                    dice_type = skill_check.get('dice_type', '1d20')
                    target = skill_check.get('target', 10)
                    scenes[skill_scene_id] = {
                        'text': f"You attempt to {self._humanize_text(exit_text)}. Roll {dice_type} (target: {target} or higher).",
                        'choices': [
                            {
                                'text': f'Roll dice (success: {target}+)',
                                'next': success_scene_id
                            },
                            {
                                'text': f'Roll dice (failure: <{target})',
                                'next': failure_scene_id
                            }
                        ],
                        'skill_check_info': True
                    }
                    
                else:
                    # Regular choice
                    scene['choices'].append({
                        'text': self._humanize_text(exit_text),
                        'next': exit_target if isinstance(exit_target, str) else room_id
                    })
            
            scenes[room_id] = scene
        
        return scenes
    
    def _humanize_text(self, text: str) -> str:
        """Convert snake_case or other formats to readable text"""
        # Replace underscores with spaces
        text = text.replace('_', ' ')
        # Capitalize first letter of each word
        text = ' '.join(word.capitalize() for word in text.split())
        return text
    
    def generate_inform7_code(self) -> str:
        """Generate Inform 7 source code from CYOA JSON"""
        title = self.story_data.get('title', 'Untitled Story')
        author = self.story_data.get('author', 'Anonymous')
        scenes = self.story_data.get('scenes', {})
        start_scene = self.story_data.get('start', list(scenes.keys())[0] if scenes else 'start')
        
        # Start building the Inform 7 code
        code = f'"{title}" by {author}\n\n'
        
        # Create rooms for each scene
        for scene_id, scene_data in scenes.items():
            room_name = self._sanitize_name(scene_id)
            description = scene_data.get('text', 'You are here.')
            
            code += f'{room_name} is a room. '
            code += f'"{self._escape_text(description)}"\n\n'
        
        # Set the starting location
        start_room = self._sanitize_name(start_scene)
        code += f'The player is in {start_room}.\n\n'
        
        # Create choices as actions/commands
        for scene_id, scene_data in scenes.items():
            choices = scene_data.get('choices', [])
            
            if not choices:
                # This is an ending
                continue
            
            current_room = self._sanitize_name(scene_id)
            
            for i, choice in enumerate(choices):
                choice_text = choice.get('text', f'Choice {i+1}')
                next_scene = choice.get('next', '')
                
                if not next_scene or next_scene not in scenes:
                    continue
                
                next_room = self._sanitize_name(next_scene)
                action_name = self._sanitize_action_name(choice_text)
                
                # Create custom action
                code += f'Choosing {action_name} is an action applying to nothing.\n'
                code += f'Understand "{choice_text}" as choosing {action_name}.\n\n'
                
                code += f'Check choosing {action_name}:\n'
                code += f'\tif the player is not in {current_room}:\n'
                code += f'\t\tsay "You can\'t do that right now." instead.\n\n'
                
                code += f'Carry out choosing {action_name}:\n'
                code += f'\tnow the player is in {next_room};\n'
                code += f'\ttry looking.\n\n'
        
        # Add a hint system showing available choices
        code += 'After looking:\n'
        for scene_id, scene_data in scenes.items():
            choices = scene_data.get('choices', [])
            if choices:
                current_room = self._sanitize_name(scene_id)
                code += f'\tif the player is in {current_room}:\n'
                code += f'\t\tsay "[line break]You can: '
                choice_texts = [f'"{c.get("text", "")}"' for c in choices]
                code += ' or '.join(choice_texts)
                code += '.";\n'
        
        code += '\tcontinue the action.\n\n'
        
        # Handle win/lose conditions for endings
        code += 'Every turn:\n'
        for scene_id, scene_data in scenes.items():
            if not scene_data.get('choices'):  # It's an ending
                room_name = self._sanitize_name(scene_id)
                code += f'\tif the player is in {room_name}:\n'
                code += f'\t\tsay "[line break]THE END[line break]";\n'
                code += f'\t\tend the story.\n'
        
        return code
    
    def _sanitize_name(self, name: str) -> str:
        """Convert scene ID to valid Inform 7 room name"""
        # Replace invalid characters with spaces
        sanitized = ''.join(c if c.isalnum() or c == ' ' else ' ' for c in name)
        # Capitalize each word
        sanitized = ' '.join(word.capitalize() for word in sanitized.split())
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = 'Scene ' + sanitized
        return sanitized or 'Scene'
    
    def _sanitize_action_name(self, text: str) -> str:
        """Convert choice text to valid Inform 7 action name"""
        # Keep only alphanumeric and convert to lowercase
        sanitized = ''.join(c if c.isalnum() else ' ' for c in text.lower())
        sanitized = '_'.join(sanitized.split())
        return sanitized or 'action'
    
    def _escape_text(self, text: str) -> str:
        """Escape text for Inform 7"""
        # Replace quotes with single quotes
        text = text.replace('"', "'")
        return text
    
    def compile_to_format(self, output_path: str, format_type: str, progress_callback=None) -> bool:
        """
        Compile Inform 7 code to Z-Machine or Glulx
        
        Args:
            output_path: Where to save the compiled file
            format_type: Either 'z8' for Z-Machine or 'glulx' for Glulx
            progress_callback: Optional function to call with progress messages
        """
        if not self.story_data:
            raise Exception("No story loaded. Load JSON first.")
        
        # Generate Inform 7 code
        if progress_callback:
            progress_callback("Generating Inform 7 code...")
        
        inform_code = self.generate_inform7_code()
        
        # Create temporary directory for Inform project
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create Inform project structure
            source_dir = temp_path / "Source"
            source_dir.mkdir()
            
            story_file = source_dir / "story.ni"
            story_file.write_text(inform_code, encoding='utf-8')
            
            if progress_callback:
                progress_callback(f"Compiling to {format_type.upper()}...")
            
            # Try to compile using ni and inform6
            try:
                # Check if inform7 compiler is available
                result = subprocess.run(
                    ['ni', '--help'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode != 0:
                    raise FileNotFoundError("Inform 7 compiler not found")
                
                # Compile with ni (Inform 7 compiler)
                format_flag = '--format=' + format_type
                compile_result = subprocess.run(
                    ['ni', '--internal', str(temp_path), '--project', str(temp_path), format_flag],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if compile_result.returncode != 0:
                    raise Exception(f"Compilation failed: {compile_result.stderr}")
                
                # Find the output file
                build_dir = temp_path / "Build"
                if format_type == 'z8':
                    output_file = build_dir / "output.z8"
                else:  # glulx
                    output_file = build_dir / "output.ulx"
                
                if not output_file.exists():
                    raise Exception("Compiled file not found in Build directory")
                
                # Copy to destination
                import shutil
                shutil.copy(output_file, output_path)
                
                if progress_callback:
                    progress_callback("Compilation successful!")
                
                return True
                
            except FileNotFoundError:
                # Inform 7 not installed, just save the source code
                if progress_callback:
                    progress_callback("Inform 7 compiler not found. Saving source code instead...")
                
                output_ni = Path(output_path).with_suffix('.ni')
                output_ni.write_text(inform_code, encoding='utf-8')
                
                raise Exception(
                    "Inform 7 compiler (ni) not found on system.\n\n"
                    f"Source code has been saved to: {output_ni}\n\n"
                    "To compile this file:\n"
                    "1. Install Inform 7 from https://ganelson.github.io/inform-website/\n"
                    "2. Open the .ni file in Inform 7 IDE\n"
                    "3. Click 'Go!' to compile"
                )


class HelpDialog:
    """Help and documentation dialog"""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Help - CYOA Converter")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        
        # Create notebook for tabbed help sections
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add help sections
        self._add_getting_started(notebook)
        self._add_formats_info(notebook)
        self._add_compilation_modes(notebook)
        self._add_json_format(notebook)
        self._add_playing_stories(notebook)
        self._add_troubleshooting(notebook)
        self._add_about(notebook)
        
        # Close button
        ttk.Button(self.dialog, text="Close", command=self.dialog.destroy).pack(pady=10)
    
    def _add_getting_started(self, notebook):
        """Getting started guide"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Getting Started")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=30)
        text.pack(fill=tk.BOTH, expand=True)
        
        content = """
GETTING STARTED WITH CYOA CONVERTER

This application converts Choose-Your-Own-Adventure stories from JSON format into 
playable Interactive Fiction games.

QUICK START:
1. Click "Browse..." to select your story file (JSON or ZIP)
2. Choose your output format (Z-Machine or Glulx)
3. Click "Preview Source" to see the generated code (optional)
4. Click "Convert & Compile" to create your playable story
5. Save the file and play it with an IF interpreter!

WHAT YOU NEED:

Input File:
  • A JSON file containing your story structure
  • OR a ZIP archive containing a JSON file
  • The JSON should have 'title', 'scenes', and choice structure

Output Options:
  • Z-Machine (.z8) - Classic format, works everywhere
  • Glulx (.ulx) - Modern format, no size restrictions

HOW IT WORKS:

The converter transforms your story through these steps:
1. Loads and validates your JSON story structure
2. Generates Inform 7 source code with rooms and actions
3. Compiles the code into a playable interactive fiction file
4. You get a .z8 or .ulx file you can share and play!

TIPS FOR BEST RESULTS:

• Make sure your JSON is properly formatted with all required fields
• Test your story logic before converting to catch any issues
• Use descriptive scene names - they become room names in the game
• Keep choice text clear and action-oriented
• Preview the source code to see how your story translates

NEXT STEPS:

After conversion, you can:
• Play your story immediately with an interpreter
• Share the file with others to play
• Make changes to your JSON and re-convert
• Try both formats to see which you prefer
"""
        
        text.insert(1.0, content)
        text.config(state='disabled')
    
    def _add_formats_info(self, notebook):
        """Format comparison information"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Output Formats")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=30)
        text.pack(fill=tk.BOTH, expand=True)
        
        content = """
OUTPUT FORMAT COMPARISON

This converter supports two Interactive Fiction formats:

═══════════════════════════════════════════════════════════════

Z-MACHINE (.z8)

The Z-Machine is the classic Interactive Fiction format, originally created by 
Infocom in the 1970s-80s for games like Zork.

ADVANTAGES:
  ✓ Universal compatibility - plays on virtually any device
  ✓ Tiny file sizes - perfect for sharing
  ✓ Battle-tested and rock-solid
  ✓ Works on retro computers and modern systems alike
  ✓ Many interpreters available (Frotz, Gargoyle, etc.)

LIMITATIONS:
  ✗ Size limit of approximately 512KB
  ✗ Limited to 255 rooms/objects in Version 8
  ✗ No multimedia support (text only)

BEST FOR:
  • Stories with moderate size (under a few hundred scenes)
  • Maximum compatibility and portability
  • When file size matters
  • Retro gaming aesthetics

═══════════════════════════════════════════════════════════════

GLULX (.ulx)

Glulx is a modern Interactive Fiction format designed to overcome the limitations 
of the Z-Machine while maintaining compatibility with the IF ecosystem.

ADVANTAGES:
  ✓ No practical size limits
  ✓ Support for graphics and sound
  ✓ Can handle massive, complex stories
  ✓ Modern features and capabilities
  ✓ Full Unicode support

LIMITATIONS:
  ✗ Slightly larger file sizes
  ✗ Fewer interpreters available (though all major ones support it)
  ✗ Not compatible with vintage systems

BEST FOR:
  • Large, complex stories with many scenes
  • Stories that might grow over time
  • When you want room to expand
  • Modern IF development

═══════════════════════════════════════════════════════════════

WHICH SHOULD YOU CHOOSE?

Start with Z-Machine (.z8) unless:
  • Your story has more than 200-300 scenes
  • You plan to add lots of content later
  • You specifically need Glulx features

Both formats play the same way and work with popular interpreters like Gargoyle 
and Lectrote. Most players won't notice a difference for typical stories.

You can always convert to the other format later if needed!
"""
        
        text.insert(1.0, content)
        text.config(state='disabled')
    
    def _add_compilation_modes(self, notebook):
        """Compilation modes explanation"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Compilation Modes")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=30)
        text.pack(fill=tk.BOTH, expand=True)
        
        content = """
HOW COMPILATION WORKS

This converter operates in two different modes depending on whether you have the 
Inform 7 compiler installed on your system.

═══════════════════════════════════════════════════════════════

MODE 1: WITH INFORM 7 INSTALLED (Full Compilation)

If you have Inform 7 installed, the converter will:
  1. Generate Inform 7 source code from your JSON
  2. Automatically compile it to .z8 or .ulx format
  3. Give you a ready-to-play game file
  4. Complete the process in seconds

This is the recommended way to use the converter for the smoothest experience.

═══════════════════════════════════════════════════════════════

MODE 2: WITHOUT INFORM 7 (Source Code Only)

If Inform 7 is not installed, the converter will:
  1. Generate Inform 7 source code from your JSON
  2. Save it as a .ni file with instructions
  3. Provide guidance on how to compile manually

You'll then need to:
  • Install Inform 7 (see below)
  • Open the .ni file in Inform 7
  • Click "Go!" to compile

═══════════════════════════════════════════════════════════════

INSTALLING INFORM 7

To get full compilation support:

Official Website:
  https://ganelson.github.io/inform-website/

Download for your platform:
  • Windows: Download the Windows IDE
  • macOS: Download the macOS app
  • Linux: Install from package manager or source

After Installation:
  1. The 'ni' compiler should be in your PATH
  2. Restart this converter application
  3. Try converting again - it should now compile automatically!

═══════════════════════════════════════════════════════════════

CHECKING YOUR INSTALLATION

To verify Inform 7 is properly installed:

Open a terminal/command prompt and type:
  ni --help

If you see help information, it's installed correctly!
If you get "command not found", you need to:
  • Install Inform 7, or
  • Add it to your system PATH

═══════════════════════════════════════════════════════════════

MANUAL COMPILATION STEPS

If you have a .ni source file:

1. Open Inform 7 IDE
2. Choose File → Open or Create → Open Existing Project
3. Select the .ni file
4. Click the "Go!" button
5. Find your compiled game in the Build folder

The IDE will show any errors and help you fix them.

═══════════════════════════════════════════════════════════════

WHY USE INFORM 7?

Inform 7 is the industry-standard tool for creating Interactive Fiction:
  • Free and open source
  • Powers thousands of published IF games
  • Excellent documentation and community
  • Cross-platform support
  • Both graphical IDE and command-line tools

Even if you only plan to convert JSON stories, having Inform 7 installed gives 
you the full power of IF development if you ever want to customize your games!
"""
        
        text.insert(1.0, content)
        text.config(state='disabled')
    
    def _add_json_format(self, notebook):
        """JSON format specification"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="JSON Format")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=30)
        text.pack(fill=tk.BOTH, expand=True)
        
        content = """
SUPPORTED JSON FORMATS

This converter supports MULTIPLE JSON story formats, automatically detecting which
format you're using!

═══════════════════════════════════════════════════════════════

FORMAT 1: SIMPLE CYOA FORMAT (Original)

{
  "title": "Your Story Title",
  "author": "Your Name",
  "start": "opening_scene",
  "scenes": {
    "scene_id": {
      "text": "Scene description",
      "choices": [
        {
          "text": "Choice description",
          "next": "next_scene_id"
        }
      ]
    }
  }
}

BEST FOR:
  • Simple branching narratives
  • Quick story prototyping
  • Straightforward choice-based stories

═══════════════════════════════════════════════════════════════

FORMAT 2: ROOM-BASED FORMAT (Advanced)

{
  "name": "Your Story Title",
  "button_color": "#FF5733",
  "start_room": "first_room",
  "rooms": {
    "room_id": {
      "description": "Room description",
      "exits": {
        "exit_name": "target_room",
        "skill_check_exit": {
          "skill_check": {
            "dice_type": "1d20",
            "target": 15,
            "success": {
              "description": "Success text",
              "room": "success_room"
            },
            "failure": {
              "description": "Failure text",
              "room": "failure_room"
            }
          }
        }
      }
    }
  }
}

BEST FOR:
  • RPG-style adventures
  • Stories with skill checks
  • Complex branching with dice rolls
  • Game-like experiences

FEATURES:
  • Dice roll skill checks
  • Success/failure branches
  • Room-based navigation
  • RPG mechanics

═══════════════════════════════════════════════════════════════

FORMAT 1 DETAILED: SIMPLE CYOA

Required Fields:
  • title (string) - Story title
  • scenes (object) - All story scenes

Optional Fields:
  • author (string) - Your name
  • start (string) - First scene ID

Scene Object:
  • text (string) - Scene description
  • choices (array) - Available choices

Choice Object:
  • text (string) - Choice description
  • next (string) - Target scene ID

EXAMPLE:

{
  "title": "The Haunted House",
  "author": "Anonymous",
  "start": "entrance",
  "scenes": {
    "entrance": {
      "text": "You stand before a spooky mansion.",
      "choices": [
        {
          "text": "Enter the house",
          "next": "hallway"
        },
        {
          "text": "Run away",
          "next": "escape"
        }
      ]
    },
    "hallway": {
      "text": "The hallway is dark and dusty.",
      "choices": [
        {
          "text": "Go upstairs",
          "next": "bedroom"
        }
      ]
    },
    "escape": {
      "text": "You run to safety. THE END.",
      "choices": []
    }
  }
}

═══════════════════════════════════════════════════════════════

FORMAT 2 DETAILED: ROOM-BASED

Required Fields:
  • name (string) - Story title
  • rooms (object) - All story rooms

Optional Fields:
  • button_color (string) - UI color hint
  • start_room (string) - First room ID

Room Object:
  • description (string) - Room description
  • exits (object) - Available exits

Exit Types:
  1. Simple Exit:
     "exit_name": "target_room"
     
  2. Ending Exit:
     "exit_name": null
     
  3. Skill Check Exit:
     "exit_name": {
       "skill_check": {
         "dice_type": "1d20",
         "target": 15,
         "success": {
           "description": "Success text",
           "room": "success_room"
         },
         "failure": {
           "description": "Failure text",
           "room": "failure_room"
         }
       }
     }

EXAMPLE:

{
  "name": "The Forgotten Temple",
  "button_color": "#8B4513",
  "start_room": "entrance",
  "rooms": {
    "entrance": {
      "description": "You stand before an ancient temple.",
      "exits": {
        "enter_temple": "main_hall",
        "turn_back": null
      }
    },
    "main_hall": {
      "description": "The hall is vast and mysterious.",
      "exits": {
        "search_for_clues": {
          "skill_check": {
            "dice_type": "1d20",
            "target": 14,
            "success": {
              "description": "You find a hidden map!",
              "room": "secret_passage"
            },
            "failure": {
              "description": "You find nothing.",
              "room": "main_hall"
            }
          }
        },
        "leave": "entrance"
      }
    }
  }
}

═══════════════════════════════════════════════════════════════

SKILL CHECKS EXPLAINED

Skill checks add RPG mechanics to your story:

dice_type:
  • "1d20" - Roll one 20-sided die
  • "2d6" - Roll two 6-sided dice
  • "1d100" - Roll one 100-sided die
  • etc.

target:
  • Number player must roll or exceed
  • Example: target 15 means roll 15+ to succeed

success/failure:
  • Each has description text
  • Each leads to a different room
  • Creates branching based on luck/skill

HOW IT WORKS IN THE GAME:
1. Player chooses skill check action
2. Game presents the challenge and target
3. Player chooses to roll (success or failure branch)
4. Story continues based on outcome

NOTE: The converter presents skill checks as player choices between
success and failure paths, since IF games don't have built-in dice
rolling. Players can roll physical/virtual dice and choose accordingly!

═══════════════════════════════════════════════════════════════

CREATING ENDINGS

Format 1 (Scenes):
  • Empty choices array = ending
  • Example: "choices": []

Format 2 (Rooms):
  • Exit with null target = ending
  • Example: "turn_back": null
  • OR room with empty exits
  • OR room with no exits object

Both formats support multiple endings!

═══════════════════════════════════════════════════════════════

TIPS FOR BOTH FORMATS

1. Use descriptive IDs
   ✓ "throne_room", "dark_forest"
   ✗ "room1", "r2"

2. Test your JSON syntax
   • Use jsonlint.com
   • Check for missing commas
   • Verify brackets match

3. Plan your structure
   • Map out your story flow
   • Create multiple paths
   • Include several endings

4. Write engaging descriptions
   • Set the scene vividly
   • Create atmosphere
   • Guide player actions

5. Balance difficulty (for skill checks)
   • Don't make everything require 20
   • Vary the challenges
   • Make failure interesting too

═══════════════════════════════════════════════════════════════

CONVERTING BETWEEN FORMATS

The converter handles both automatically! You don't need to convert
between them manually. Just use whichever format suits your story:

Simple narrative? → Use Format 1 (scenes)
RPG-style adventure? → Use Format 2 (rooms)

═══════════════════════════════════════════════════════════════

LOADING FROM ZIP FILES

You can package your JSON in a ZIP archive:
  • Place your .json file in a .zip
  • The converter automatically finds it
  • Works with both formats
  • Useful for bundling multiple assets
"""
        
        text.insert(1.0, content)
        text.config(state='disabled')
    
    def _add_playing_stories(self, notebook):
        """Information about playing converted stories"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Playing Stories")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=30)
        text.pack(fill=tk.BOTH, expand=True)
        
        content = """
PLAYING YOUR CONVERTED STORIES

After converting your CYOA story, you'll have a .z8 or .ulx file. Here's how 
to play it!

═══════════════════════════════════════════════════════════════

RECOMMENDED INTERPRETERS:

Gargoyle (Best All-Around)
  • Cross-platform (Windows, Mac, Linux)
  • Supports both Z-Machine and Glulx
  • Clean, modern interface
  • Download: https://github.com/garglk/garglk

Lectrote (Modern & Stylish)
  • Built on Electron, very modern UI
  • Cross-platform
  • Great for Glulx stories
  • Download: https://github.com/erkyrath/lectrote

Frotz (Classic Choice)
  • Available everywhere
  • Command-line and GUI versions
  • Rock-solid Z-Machine support
  • Download: https://davidgriffith.gitlab.io/frotz/

═══════════════════════════════════════════════════════════════

HOW TO PLAY:

1. Download and install an interpreter (see above)
2. Open your .z8 or .ulx file in the interpreter
3. Read the story text
4. Look for available choices at the end of each section
5. Type the choice text exactly as shown
6. Press Enter to make your choice
7. The story continues to the next scene

═══════════════════════════════════════════════════════════════

BASIC COMMANDS:

Your converted stories support these commands:

Story Commands (from your choices):
  • Type the exact choice text shown
  • Example: if you see "Enter the house", type that

Standard IF Commands:
  • LOOK - Read the current scene again
  • QUIT - Exit the game
  • SAVE - Save your progress
  • RESTORE - Load a saved game
  • RESTART - Start over from the beginning
  • UNDO - Take back your last move

═══════════════════════════════════════════════════════════════

EXAMPLE PLAY SESSION:

The Haunted House
An Interactive Fiction by Anonymous

Entrance
You stand before a spooky old mansion. The door creaks open.

You can: "Enter the house" or "Run away".

> enter the house

Hallway
The hallway is dark and dusty. You hear strange noises.

You can: "Go upstairs" or "Check the kitchen".

> go upstairs

[... story continues ...]

═══════════════════════════════════════════════════════════════

SHARING YOUR STORIES:

Once converted, you can share your story files:

  • Email the .z8 or .ulx file
  • Host on websites (itch.io, IF Archive, etc.)
  • Share on USB drives or cloud storage
  • Post in IF communities

Players just need an interpreter to play - no installation needed!

═══════════════════════════════════════════════════════════════

TROUBLESHOOTING GAMEPLAY:

"I typed a choice but nothing happened"
  → Make sure you typed it exactly as shown
  → Check for typos
  → Type LOOK to see choices again

"The game won't recognize my command"
  → Only use the exact choice text from the story
  → This isn't a parser game - stick to the choices

"I want to go back"
  → Type UNDO to reverse your last move
  → Or RESTORE to load a saved game

"How do I save?"
  → Type SAVE anytime
  → Give it a filename
  → Type RESTORE to load it later

═══════════════════════════════════════════════════════════════

PLATFORM-SPECIFIC NOTES:

Windows:
  • Gargoyle and Frotz work great
  • .z8/.ulx files may need to be opened with "Open With..."

macOS:
  • Lectrote highly recommended
  • Gargoyle also available
  • Double-click to open with default interpreter

Linux:
  • All interpreters available via package managers
  • Frotz available in most distros
  • Gargoyle can be compiled from source

iOS/Android:
  • Frotz available on both platforms
  • Text Fiction (Android)
  • Spatterlight (iOS)
  • Play your stories on mobile!

Web:
  • Parchment (browser-based Z-Machine)
  • Quixe (browser-based Glulx)
  • Upload to itch.io for web play
"""
        
        text.insert(1.0, content)
        text.config(state='disabled')
    
    def _add_troubleshooting(self, notebook):
        """Troubleshooting guide"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Troubleshooting")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=30)
        text.pack(fill=tk.BOTH, expand=True)
        
        content = """
TROUBLESHOOTING GUIDE

Common issues and how to fix them:

═══════════════════════════════════════════════════════════════

"JSON must contain 'title' field"
"JSON must contain 'scenes' field"

CAUSE: Your JSON file is missing required fields

FIX:
  1. Open your JSON file in a text editor
  2. Make sure it has both "title" and "scenes" at the top level
  3. Example structure:
     {
       "title": "My Story",
       "scenes": { ... }
     }

═══════════════════════════════════════════════════════════════

"No JSON files found in ZIP archive"

CAUSE: The ZIP file doesn't contain any .json files

FIX:
  1. Open the ZIP file and verify there's a JSON inside
  2. Make sure the file extension is .json (not .txt)
  3. The JSON file can be in the root or a subfolder
  4. Try extracting the JSON and loading it directly

═══════════════════════════════════════════════════════════════

"Failed to load file: [JSON parsing error]"

CAUSE: The JSON file has syntax errors

FIX:
  1. Copy your JSON content
  2. Paste it into jsonlint.com or another JSON validator
  3. Fix any syntax errors shown (missing commas, brackets, etc.)
  4. Common issues:
     • Missing quotes around strings
     • Extra comma after last item
     • Mismatched brackets { } or [ ]
     • Unescaped quotes inside strings

═══════════════════════════════════════════════════════════════

"Inform 7 compiler not found"

CAUSE: Inform 7 is not installed or not in your PATH

FIX:
  Option 1 - Install Inform 7:
    1. Visit: https://ganelson.github.io/inform-website/
    2. Download for your platform
    3. Install following the instructions
    4. Restart this converter application
  
  Option 2 - Use the generated source file:
    1. The converter will save a .ni file
    2. Open it in the Inform 7 IDE
    3. Click "Go!" to compile manually

═══════════════════════════════════════════════════════════════

"Compilation failed: [error message]"

CAUSE: The generated Inform 7 code has an issue

FIX:
  1. Check if your scene IDs have special characters
     → Use only letters, numbers, and underscores
  2. Make sure choice "next" fields point to valid scenes
  3. Verify scene text doesn't have weird characters
  4. Try the "Preview Source" button to see the code
  5. If the issue persists, check your JSON structure

═══════════════════════════════════════════════════════════════

"Compiled file not found in Build directory"

CAUSE: Compilation may have succeeded but file wasn't found

FIX:
  1. Check the log for actual compiler errors
  2. Try compiling again
  3. Look in your temp directory for the Build folder
  4. Try using the other format (Z-Machine ↔ Glulx)

═══════════════════════════════════════════════════════════════

Application is frozen / not responding

CAUSE: Large story taking time to compile

FIX:
  1. Wait a bit longer - complex stories take time
  2. Check the log for progress messages
  3. For very large stories, consider breaking into chapters
  4. Use Glulx format for large stories (no size limit)

═══════════════════════════════════════════════════════════════

Story plays but choices don't work

CAUSE: Choice text may not match what you're typing

FIX:
  1. Type choices EXACTLY as shown in the story
  2. Check for extra spaces or punctuation
  3. Type LOOK to see choices again
  4. Choices are case-sensitive - match the capitalization

═══════════════════════════════════════════════════════════════

Can't open the compiled .z8/.ulx file

CAUSE: No interpreter installed or wrong file association

FIX:
  1. Install an IF interpreter (see Playing Stories tab)
  2. Right-click the file → Open With → Choose interpreter
  3. Or drag and drop the file onto the interpreter
  4. Set the interpreter as default for .z8/.ulx files

═══════════════════════════════════════════════════════════════

Story text looks garbled or has weird characters

CAUSE: Character encoding issues in the JSON

FIX:
  1. Save your JSON file as UTF-8 encoding
  2. Avoid fancy Unicode characters if possible
  3. Test special characters in a simple story first
  4. Use plain ASCII for best compatibility

═══════════════════════════════════════════════════════════════

STILL HAVING ISSUES?

If none of these solutions work:

1. Check the Log
   • Read the entire error message carefully
   • Look for specific file names or line numbers
   • Screenshot the error for reference

2. Verify Your JSON
   • Test with a minimal example first
   • Build up complexity gradually
   • Validate syntax with online tools

3. Test Inform 7
   • Make sure 'ni --help' works in terminal
   • Try creating a simple project in the Inform 7 IDE
   • Verify your installation is complete

4. Try Different Approaches
   • Convert to the other format
   • Extract JSON from ZIP and load directly
   • Simplify your story to isolate the issue

5. Check File Permissions
   • Make sure you can write to the output location
   • Verify input files are readable
   • Try saving to a different folder
"""
        
        text.insert(1.0, content)
        text.config(state='disabled')
    
    def _add_about(self, notebook):
        """About information"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="About")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=30)
        text.pack(fill=tk.BOTH, expand=True)
        
        content = """
ABOUT CYOA TO IF CONVERTER

═══════════════════════════════════════════════════════════════

VERSION: 1.0

A tool for converting Choose-Your-Own-Adventure stories from JSON format into 
playable Interactive Fiction games.

═══════════════════════════════════════════════════════════════

WHAT IT DOES:

This converter bridges the gap between simple CYOA formats and the rich world 
of Interactive Fiction. It takes your story structure and transforms it into a 
proper IF game that can be played with standard interpreters.

Features:
  • Supports both Z-Machine and Glulx output formats
  • Handles JSON files and ZIP archives
  • Generates clean, readable Inform 7 source code
  • Automatic compilation when Inform 7 is available
  • User-friendly GUI with helpful feedback
  • Preview generated source code before compiling

═══════════════════════════════════════════════════════════════

HOW IT WORKS:

The conversion process:

1. JSON Parsing
   Your story structure is loaded and validated

2. Code Generation
   Inform 7 source code is created with:
   • Rooms for each scene
   • Custom actions for each choice
   • Automatic navigation between scenes
   • Help text showing available choices
   • Ending detection and game completion

3. Compilation
   The Inform 7 code is compiled to:
   • Z-Machine format (.z8) - classic IF
   • Glulx format (.ulx) - modern IF

4. Output
   You get a playable game file that works in any IF interpreter!

═══════════════════════════════════════════════════════════════

TECHNOLOGIES USED:

• Python 3 - Core application logic
• Tkinter - Cross-platform GUI framework
• Inform 7 - Interactive Fiction compilation
• Z-Machine - Classic IF virtual machine
• Glulx - Modern IF virtual machine
• JSON - Story data format

═══════════════════════════════════════════════════════════════

INTERACTIVE FICTION HERITAGE:

This tool builds on decades of IF development:

• Infocom (1979-1989) - Created Z-Machine for Zork and other classics
• Inform (1993-present) - Graham Nelson's IF development system
• Glulx (1999) - Andrew Plotkin's modern IF format
• Open-source IF community - Ongoing development and support

═══════════════════════════════════════════════════════════════

FILE FORMATS:

Input Formats:
  • .json - JSON story structure
  • .zip - ZIP archive containing JSON

Output Formats:
  • .z8 - Z-Machine version 8 (recommended for most stories)
  • .ulx - Glulx (for large or complex stories)
  • .ni - Inform 7 source code (when compiler unavailable)

═══════════════════════════════════════════════════════════════

SYSTEM REQUIREMENTS:

Minimum:
  • Python 3.7 or higher
  • Tkinter (usually included with Python)
  • 50 MB free disk space

Recommended:
  • Inform 7 compiler installed
  • JSON validator for checking story files
  • IF interpreter for testing (Gargoyle, Frotz, Lectrote)

Supported Platforms:
  • Windows 7 and higher
  • macOS 10.12 and higher
  • Linux (most distributions)

═══════════════════════════════════════════════════════════════

LIMITATIONS:

Current limitations:
  • Stories must follow the JSON structure specified
  • No multimedia support (text only)
  • Choices must be typed exactly as shown
  • No state variables or conditional logic
  • Linear scene progression only

These are inherent to the CYOA→IF conversion process. For more complex 
interactive fiction, consider learning Inform 7 directly!

═══════════════════════════════════════════════════════════════

FUTURE ENHANCEMENTS:

Possible future features:
  • Batch conversion of multiple stories
  • Story validation and structure analysis
  • Built-in JSON editor
  • Template story library
  • Export to additional IF formats
  • Story flow visualization
  • Testing and debugging tools

═══════════════════════════════════════════════════════════════

LEARNING MORE:

Interactive Fiction Resources:
  • Inform 7: https://ganelson.github.io/inform-website/
  • IF Archive: https://ifarchive.org/
  • IFWiki: https://www.ifwiki.org/
  • IFDB: https://ifdb.org/
  • Intfiction.org - Active community forum

Development Resources:
  • Inform 7 Documentation (included with Inform 7)
  • "The Inform 7 Handbook" by Jim Aikin
  • "Creating Interactive Fiction with Inform 7" by Aaron Reed

═══════════════════════════════════════════════════════════════

ACKNOWLEDGMENTS:

This tool stands on the shoulders of giants:

• Graham Nelson - Creator of Inform
• Andrew Plotkin - Glulx design and implementation
• Infocom - Pioneers of interactive fiction
• The IF community - Decades of development and support

Thank you to all who have contributed to making Interactive Fiction 
accessible and enjoyable for creators and players alike!

═══════════════════════════════════════════════════════════════

LICENSE:

This converter is provided as-is for personal and educational use.

Interactive Fiction formats:
  • Z-Machine specification is public domain
  • Glulx specification is freely available
  • Inform 7 is freely licensed

Your stories remain your own - use the converted files however you like!
"""
        
        text.insert(1.0, content)
        text.config(state='disabled')


class ConverterGUI:
    """GUI application for CYOA converter"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("CYOA to Interactive Fiction Converter")
        self.root.geometry("900x700")
        
        self.converter = CYOAConverter()
        self.current_file = None
        
        self._create_menu()
        self._create_widgets()
        self._show_welcome_message()
        
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open JSON/ZIP...", command=self._browse_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Preview Source", command=self._preview_source, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Getting Started", command=lambda: self._show_help(0))
        help_menu.add_command(label="Output Formats", command=lambda: self._show_help(1))
        help_menu.add_command(label="Compilation Modes", command=lambda: self._show_help(2))
        help_menu.add_command(label="JSON Format", command=lambda: self._show_help(3))
        help_menu.add_command(label="Playing Stories", command=lambda: self._show_help(4))
        help_menu.add_command(label="Troubleshooting", command=lambda: self._show_help(5))
        help_menu.add_separator()
        help_menu.add_command(label="About", command=lambda: self._show_help(6))
        
        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self._browse_file())
        self.root.bind('<Control-p>', lambda e: self._preview_source())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
    
    def _show_help(self, tab_index=0):
        """Show help dialog with specified tab"""
        dialog = HelpDialog(self.root)
        # Note: We can't directly select tabs after creation, but they're organized logically
        
    def _show_welcome_message(self):
        """Show welcome message in the log"""
        welcome = """Welcome to CYOA to Interactive Fiction Converter!

This tool converts Choose-Your-Own-Adventure JSON stories into playable Interactive Fiction games.

Quick Start:
  1. Click 'Browse...' to select your story (JSON or ZIP file)
  2. Choose your output format (Z-Machine or Glulx)
  3. Click 'Convert & Compile' to create your game!

Need help? Check the Help menu above for:
  • Getting Started guide
  • Output format comparison
  • JSON format specification
  • Troubleshooting tips
  • And much more!

Ready to begin? Click Browse to select your story file.
"""
        self._log(welcome)
        
    def _create_widgets(self):
        """Create GUI widgets"""
        # Main container with better padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # File selection frame with better styling
        file_frame = ttk.LabelFrame(main_frame, text="📁 Input File", padding="10")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        file_frame.columnconfigure(1, weight=1)
        
        info_text = "Select a CYOA story file (supports multiple JSON formats and ZIP archives)"
        ttk.Label(file_frame, text=info_text, foreground="gray").grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 8)
        )
        
        self.file_label = ttk.Label(file_frame, text="No file selected", font=('TkDefaultFont', 9, 'bold'))
        self.file_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 8))
        
        ttk.Button(file_frame, text="Browse...", command=self._browse_file, width=12).grid(
            row=2, column=0, padx=(0, 8)
        )
        
        self.file_path = tk.StringVar()
        path_entry = ttk.Entry(file_frame, textvariable=self.file_path, state='readonly')
        path_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 8))
        
        ttk.Button(file_frame, text="Clear", command=self._clear_file, width=8).grid(
            row=2, column=2
        )
        
        # Output format frame with better descriptions
        format_frame = ttk.LabelFrame(main_frame, text="🎮 Output Format", padding="10")
        format_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        format_info = "Choose the Interactive Fiction format for your compiled story"
        ttk.Label(format_frame, text=format_info, foreground="gray").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 8)
        )
        
        self.format_var = tk.StringVar(value='z8')
        
        z8_frame = ttk.Frame(format_frame)
        z8_frame.grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Radiobutton(
            z8_frame,
            text="Z-Machine (.z8)",
            variable=self.format_var,
            value='z8'
        ).pack(side=tk.LEFT)
        ttk.Label(
            z8_frame,
            text="  Classic format • Universal compatibility • Recommended for most stories",
            foreground="gray"
        ).pack(side=tk.LEFT)
        
        glulx_frame = ttk.Frame(format_frame)
        glulx_frame.grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Radiobutton(
            glulx_frame,
            text="Glulx (.ulx)",
            variable=self.format_var,
            value='glulx'
        ).pack(side=tk.LEFT)
        ttk.Label(
            glulx_frame,
            text="  Modern format • No size limits • Best for large stories",
            foreground="gray"
        ).pack(side=tk.LEFT)
        
        # Preview/Log frame with better title
        log_frame = ttk.LabelFrame(main_frame, text="📋 Output Log", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Add scrolled text with better font
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=18,
            state='disabled',
            wrap=tk.WORD,
            font=('Courier', 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Buttons frame with better layout
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(
            button_frame,
            text="📄 Preview Source",
            command=self._preview_source,
            width=20
        ).grid(row=0, column=0, padx=(0, 8))
        
        self.convert_button = ttk.Button(
            button_frame,
            text="🚀 Convert & Compile",
            command=self._convert,
            state='disabled',
            width=20
        )
        self.convert_button.grid(row=0, column=1, padx=(0, 8))
        
        ttk.Button(
            button_frame,
            text="🗑️ Clear Log",
            command=self._clear_log,
            width=15
        ).grid(row=0, column=2)
        
        # Add spacer
        button_frame.columnconfigure(3, weight=1)
        
        # Help button on the right
        ttk.Button(
            button_frame,
            text="❓ Help",
            command=self._show_help,
            width=12
        ).grid(row=0, column=4)
        
        # Status bar with better styling
        status_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=1)
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(15, 0))
        
        self.status_var = tk.StringVar(value="Ready • Select a file to begin")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, padding=5)
        status_label.pack(fill=tk.X)
    
    def _clear_file(self):
        """Clear the current file selection"""
        self.current_file = None
        self.file_path.set("")
        self.file_label.config(text="No file selected")
        self.convert_button.config(state='disabled')
        self.status_var.set("Ready • Select a file to begin")
        self._log("\nFile selection cleared.\n")
    
    def _browse_file(self):
        """Open file browser to select CYOA JSON file"""
        filename = filedialog.askopenfilename(
            title="Select CYOA Story File",
            filetypes=[
                ("Story files", "*.json;*.zip"),
                ("JSON files", "*.json"),
                ("ZIP archives", "*.zip"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.current_file = filename
            self.file_path.set(filename)
            
            try:
                self.converter.load_json(filename)
                
                # Display file info
                file_name = Path(filename).name
                self.file_label.config(text=f"✓ {file_name}")
                
                # Log detailed information
                self._clear_log()
                self._log("═" * 70)
                self._log(f"FILE LOADED SUCCESSFULLY: {file_name}")
                self._log("═" * 70)
                self._log(f"\nTitle: {self.converter.story_data.get('title', 'Unknown')}")
                self._log(f"Author: {self.converter.story_data.get('author', 'Anonymous')}")
                
                scenes = self.converter.story_data.get('scenes', {})
                self._log(f"Total Scenes: {len(scenes)}")
                
                # Count endings
                endings = sum(1 for scene in scenes.values() if not scene.get('choices'))
                self._log(f"Endings: {endings}")
                
                # Count total choices
                total_choices = sum(len(scene.get('choices', [])) for scene in scenes.values())
                self._log(f"Total Choices: {total_choices}")
                
                start_scene = self.converter.story_data.get('start', list(scenes.keys())[0] if scenes else 'unknown')
                self._log(f"Starting Scene: {start_scene}")
                
                self._log("\n" + "─" * 70)
                self._log("Ready to convert! Choose an output format and click 'Convert & Compile'.")
                self._log("Or click 'Preview Source' to see the generated Inform 7 code.")
                self._log("─" * 70)
                
                self.convert_button.config(state='normal')
                self.status_var.set(f"✓ Loaded: {file_name} ({len(scenes)} scenes)")
                
            except Exception as e:
                self._clear_log()
                self._log("═" * 70)
                self._log("ERROR LOADING FILE")
                self._log("═" * 70)
                self._log(f"\n{str(e)}\n", error=True)
                self._log("Please check:")
                self._log("  • Is the file a valid JSON or ZIP containing JSON?")
                self._log("  • Does it have required fields (title, scenes)?")
                self._log("  • Is the JSON syntax correct?")
                self._log("\nFor help with JSON format, see Help → JSON Format")
                
                self.convert_button.config(state='disabled')
                self.status_var.set("✗ Error loading file")
                self.file_label.config(text=f"✗ Error: {Path(filename).name}")
                messagebox.showerror("Error Loading File", f"Failed to load file:\n\n{str(e)}\n\nCheck the log for details.")
    
    def _preview_source(self):
        """Preview the generated Inform 7 source code"""
        if not self.current_file:
            messagebox.showwarning("No File Selected", "Please select a story file first.\n\nClick 'Browse...' to choose a JSON or ZIP file.")
            return
        
        try:
            self.converter.load_json(self.current_file)
            source = self.converter.generate_inform7_code()
            
            self._clear_log()
            self._log("═" * 70)
            self._log("GENERATED INFORM 7 SOURCE CODE PREVIEW")
            self._log("═" * 70)
            self._log(f"\nTitle: {self.converter.story_data.get('title', 'Unknown')}")
            self._log(f"Lines of code: {len(source.splitlines())}")
            self._log("\n" + "─" * 70 + "\n")
            self._log(source)
            self._log("\n" + "─" * 70)
            self._log("\nThis is the Inform 7 code that will be compiled.")
            self._log("Ready to compile? Click 'Convert & Compile'!")
            self._log("─" * 70)
            
            self.status_var.set(f"✓ Preview generated ({len(source.splitlines())} lines)")
            
        except Exception as e:
            self._clear_log()
            self._log("═" * 70)
            self._log("ERROR GENERATING PREVIEW")
            self._log("═" * 70)
            self._log(f"\n{str(e)}\n", error=True)
            self._log("Check your JSON structure and try again.")
            self.status_var.set("✗ Preview generation failed")
            messagebox.showerror("Preview Error", f"Failed to generate preview:\n\n{str(e)}")
    
    def _convert(self):
        """Convert and compile the story"""
        if not self.current_file:
            messagebox.showwarning("No File Selected", "Please select a story file first.\n\nClick 'Browse...' to choose a JSON or ZIP file.")
            return
        
        format_type = self.format_var.get()
        extension = '.z8' if format_type == 'z8' else '.ulx'
        format_name = 'Z-Machine' if format_type == 'z8' else 'Glulx'
        
        # Suggest a filename based on story title
        story_title = self.converter.story_data.get('title', 'story') if self.converter.story_data else 'story'
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in story_title)
        suggested_name = safe_title.replace(' ', '_').lower() + extension
        
        output_file = filedialog.asksaveasfilename(
            title=f"Save {format_name} Story File",
            defaultextension=extension,
            initialfile=suggested_name,
            filetypes=[
                (f"{format_name} files", f"*{extension}"),
                ("All files", "*.*")
            ]
        )
        
        if not output_file:
            return
        
        # Run compilation in separate thread to keep GUI responsive
        self._clear_log()
        self._log("═" * 70)
        self._log(f"STARTING CONVERSION TO {format_name.upper()}")
        self._log("═" * 70)
        self._log(f"\nInput: {Path(self.current_file).name}")
        self._log(f"Output: {Path(output_file).name}")
        self._log(f"Format: {format_name} ({extension})")
        self._log("\n" + "─" * 70 + "\n")
        
        self.convert_button.config(state='disabled')
        self.status_var.set(f"⏳ Compiling to {format_name}...")
        
        def compile_thread():
            try:
                self.converter.load_json(self.current_file)
                
                def progress(msg):
                    self.root.after(0, lambda m=msg: self._log(m))
                
                self.converter.compile_to_format(output_file, format_type, progress)
                
                success_msg = f"""
{'═' * 70}
COMPILATION SUCCESSFUL!
{'═' * 70}

Your story has been compiled and saved to:
{output_file}

Format: {format_name} ({extension})

NEXT STEPS:
1. Get an IF interpreter if you don't have one:
   • Gargoyle (recommended): https://github.com/garglk/garglk
   • Lectrote: https://github.com/erkyrath/lectrote
   • Frotz: https://davidgriffith.gitlab.io/frotz/

2. Open your {extension} file in the interpreter

3. Play your story!

For more information, see Help → Playing Stories

{'═' * 70}
"""
                self.root.after(0, lambda: self._log(success_msg))
                self.root.after(0, lambda: self.status_var.set(f"✓ Compilation successful!"))
                self.root.after(0, lambda: messagebox.showinfo(
                    "Compilation Successful! 🎉",
                    f"Your story has been compiled successfully!\n\n"
                    f"Format: {format_name} ({extension})\n"
                    f"Saved to: {Path(output_file).name}\n\n"
                    f"You can now play this file with any {format_name} interpreter.\n\n"
                    f"Need an interpreter? See Help → Playing Stories"
                ))
                
            except Exception as e:
                error_msg = f"""
{'═' * 70}
COMPILATION ERROR
{'═' * 70}

{str(e)}

"""
                # Check if it's the "no compiler" error
                if "compiler (ni) not found" in str(e):
                    error_msg += """
INFORM 7 NOT FOUND

This converter needs the Inform 7 compiler to create playable game files.

TWO OPTIONS:

1. INSTALL INFORM 7 (Recommended)
   • Visit: https://ganelson.github.io/inform-website/
   • Download for your platform
   • Install and restart this converter
   • Try converting again

2. USE THE SOURCE FILE
   A .ni source file has been saved with your story code.
   You can open it in Inform 7 IDE and click 'Go!' to compile.

For detailed instructions, see Help → Compilation Modes

"""
                else:
                    error_msg += """
TROUBLESHOOTING TIPS:
• Check that your JSON structure is correct
• Verify all scene IDs are valid
• Make sure 'next' fields point to existing scenes
• Try the 'Preview Source' button to check the code

For more help, see Help → Troubleshooting

"""
                error_msg += "═" * 70
                
                self.root.after(0, lambda: self._log(error_msg, error=True))
                self.root.after(0, lambda: self.status_var.set("✗ Compilation failed"))
                self.root.after(0, lambda: messagebox.showerror(
                    "Compilation Failed",
                    f"{str(e)}\n\nCheck the log for details and see Help → Troubleshooting"
                ))
            
            finally:
                self.root.after(0, lambda: self.convert_button.config(state='normal'))
        
        threading.Thread(target=compile_thread, daemon=True).start()
    
    def _log(self, message: str, error: bool = False):
        """Add message to log"""
        self.log_text.config(state='normal')
        if error:
            self.log_text.insert(tk.END, message + '\n', 'error')
            self.log_text.tag_config('error', foreground='red')
        else:
            self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def _clear_log(self):
        """Clear the log"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()