import json
import zipfile
import sys
import tempfile
import shutil
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

def escape_json_characters(json_data):
    try:
        # Escape double quotes, backslashes, speech marks, and question marks
        escaped_data = json_data.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('?', '\\?')
        # Replace new lines with \n
        escaped_data = escaped_data.replace('\n', '\\n')
        return escaped_data, True
    except Exception as e:
        return str(e), False

def highlight_escaped_characters(text_widget, escaped_data):
    # Highlight escaped characters in the text widget
    text_widget.tag_configure("escaped", background="yellow")
    text_widget.tag_configure("newline", background="lightblue")

    for char in ['\\"', '\\\\', "\\'", '\\?', '\\t']:
        start = "1.0"
        while True:
            start = text_widget.search(char, start, tk.END)
            if not start:
                break
            end = f"{start}+{len(char)}c"
            text_widget.tag_add("escaped", start, end)
            start = end

    # Highlight \n escape sequences
    start = "1.0"
    while True:
        start = text_widget.search("\\n", start, tk.END)
        if not start:
            break
        end = f"{start}+2c"
        text_widget.tag_add("newline", start, end)
        start = end

def show_room_descriptions(story_data, zip_file_path):
    # Create a window to display room descriptions
    window = tk.Tk()
    window.title("Validator v1.0")
    window.geometry("1024x800")

    # Create a scrollable text widget
    text_widget = scrolledtext.ScrolledText(window, wrap=tk.WORD)
    text_widget.pack(expand=True, fill=tk.BOTH)

    all_escaped_successfully = True

    for room_name, room_data in story_data.get('rooms', {}).items():
        description = room_data.get('description', '')

        # Remove leading newline characters from the description
        description = description.lstrip('\n')

        # Insert the room title in white text on a black background
        text_widget.insert(tk.END, f"Room: {room_name}\n", "title")
        text_widget.tag_configure("title", background="black", foreground="white")

        # Insert the original description in a separate box with a light grey background
        text_widget.insert(tk.END, "Original:\n", "original_title")
        text_widget.tag_configure("original_title", font=("TkDefaultFont", 10, "bold"))
        text_widget.insert(tk.END, f"{description}\n\n", "original")
        text_widget.tag_configure("original", background="lightgrey")

        # Insert the modified description in a separate box
        escaped_description, escaped_successfully = escape_json_characters(description)
        text_widget.insert(tk.END, "Modified:\n", "modified_title")
        text_widget.tag_configure("modified_title", font=("TkDefaultFont", 10, "bold"))
        text_widget.insert(tk.END, f"{escaped_description}\n\n")
        highlight_escaped_characters(text_widget, escaped_description)

        all_escaped_successfully = all_escaped_successfully and escaped_successfully

    # Count the total number of rooms
    total_rooms = len(story_data.get('rooms', {}))

    # Count the number of rooms with no 'exits'
    endings = sum(1 for room_data in story_data.get('rooms', {}).values() if 'exits' not in room_data)

    # Count the total number of highlighted characters
    highlighted_characters = text_widget.tag_ranges("escaped") + text_widget.tag_ranges("newline")
    total_highlighted = len(highlighted_characters) // 2  # Each range is represented by two indices

    # Create a label to display the statistics
    stats_label = tk.Label(window, text=f"Rooms: {total_rooms} | Endings: {endings} | Highlights: {total_highlighted}")
    stats_label.pack(side=tk.BOTTOM)

    # Create a Save button
    save_button = tk.Button(window, text="Save", command=lambda: save_edited_json(text_widget, zip_file_path))
    save_button.pack()

    if not all_escaped_successfully:
        save_button.config(state=tk.DISABLED)

    window.mainloop()

def save_edited_json(text_widget, zip_file_path):
    # Extract the edited descriptions from the text widget
    edited_descriptions = {}
    text = text_widget.get("1.0", tk.END)
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].startswith("Room: "):
            room_name = lines[i].replace("Room: ", "")
            i += 2  # Skip "Original:" line
            original_description = lines[i]
            i += 2  # Skip empty line
            modified_description = lines[i]
            edited_descriptions[room_name] = modified_description
        i += 1

    # Load the original JSON data from the ZIP file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
        with zip_file.open('story.json') as json_file:
            json_data = json.loads(json_file.read().decode('utf-8'))

    # Update the descriptions in the JSON data with the edited descriptions
    for room_name, edited_description in edited_descriptions.items():
        json_data['rooms'][room_name]['description'] = edited_description

    # Create a temporary directory to store the updated ZIP file
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save the updated JSON data to a temporary file
        temp_json_file = os.path.join(temp_dir, 'story.json')
        with open(temp_json_file, 'w') as json_file:
            json.dump(json_data, json_file, indent=2)

        # Create a new ZIP file with the updated story.json
        temp_zip_file = os.path.join(temp_dir, 'updated.zip')
        with zipfile.ZipFile(temp_zip_file, 'w') as zip_file:
            zip_file.write(temp_json_file, 'story.json')

        # Replace the original ZIP file with the updated one
        shutil.move(temp_zip_file, zip_file_path)

    messagebox.showinfo("Success", "The story has been successfully updated.")

def main():
    # Prompt the user to select a story ZIP file
    selected_file = filedialog.askopenfilename(filetypes=[("ZIP Files", "*.zip")])

    if selected_file:
        try:
            # Extract the story.json file from the ZIP file
            with zipfile.ZipFile(selected_file, 'r') as zip_file:
                with zip_file.open('story.json') as json_file:
                    json_data = json_file.read().decode('utf-8')

            # Load the JSON data
            story_data = json.loads(json_data)

            # Show the room descriptions in a window
            show_room_descriptions(story_data, selected_file)

        except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as e:
            messagebox.showerror("Error", f"Failed to load the story JSON: {str(e)}")

    else:
        messagebox.showerror("Error", "No file selected.")

if __name__ == '__main__':
    main()
