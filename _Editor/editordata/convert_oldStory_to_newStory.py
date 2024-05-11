import json
import tkinter as tk
from tkinter import filedialog, messagebox

def load_old_story():
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if file_path:
        with open(file_path, 'r') as file:
            old_story_data = json.load(file)
        old_story_text.delete(1.0, tk.END)
        old_story_text.insert(tk.END, json.dumps(old_story_data, indent=2))
        convert_story(old_story_data)

def convert_story(old_story_data):
    new_story_data = {
        "name": old_story_data.get("name", ""),
        "button_color": old_story_data.get("button_color", ""),
        "start_room": old_story_data.get("start_room", ""),
        "rooms": {}
    }

    for room_name, room_data in old_story_data.get("rooms", {}).items():
        new_room_data = {
            "description": room_data.get("description", ""),
            "exits": {},
            "image": room_data.get("image", None),
            "item": None,
            "item_needed": None
        }

        for exit_name, exit_data in room_data.get("exits", {}).items():
            if isinstance(exit_data, str):
                new_room_data["exits"][exit_name] = exit_data
            elif isinstance(exit_data, dict):
                new_room_data["exits"][exit_name] = {
                    "skill_check": {
                        "dice_type": exit_data.get("skill_check", {}).get("dice_type", None),
                        "target": exit_data.get("skill_check", {}).get("target", None),
                        "success": exit_data.get("skill_check", {}).get("success", None),
                        "failure": exit_data.get("skill_check", {}).get("failure", None)
                    }
                }

        new_story_data["rooms"][room_name] = new_room_data

    new_story_text.delete(1.0, tk.END)
    new_story_text.insert(tk.END, json.dumps(new_story_data, indent=2))

def save_new_story():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if file_path:
        new_story_data = json.loads(new_story_text.get(1.0, tk.END))
        with open(file_path, 'w') as file:
            json.dump(new_story_data, file, indent=2)
        messagebox.showinfo("Story Saved", "The new story has been saved successfully.")

# Create the main window
window = tk.Tk()
window.title("Story Converter")

# Create the old story frame
old_story_frame = tk.Frame(window)
old_story_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

old_story_label = tk.Label(old_story_frame, text="Old Story")
old_story_label.pack()

old_story_text = tk.Text(old_story_frame, wrap=tk.WORD, width=50, height=30)
old_story_text.pack(fill=tk.BOTH, expand=True)

load_button = tk.Button(old_story_frame, text="Load Old Story", command=load_old_story)
load_button.pack()

# Create the new story frame
new_story_frame = tk.Frame(window)
new_story_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

new_story_label = tk.Label(new_story_frame, text="New Story")
new_story_label.pack()

new_story_text = tk.Text(new_story_frame, wrap=tk.WORD, width=50, height=30)
new_story_text.pack(fill=tk.BOTH, expand=True)

save_button = tk.Button(new_story_frame, text="Save New Story", command=save_new_story)
save_button.pack()

# Start the main event loop
window.mainloop()