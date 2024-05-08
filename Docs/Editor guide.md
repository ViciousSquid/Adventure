# Story Editor User Guide

![image](https://github.com/ViciousSquid/Adventure/assets/161540961/6cc3d6ca-a4b3-4bdb-b943-6381d3abe2df)

Welcome to the Story Editor User Guide! This comprehensive guide will walk you through the process of creating and editing interactive text-based adventure stories using the Story Editor application. Let's get started!

## Getting Started

1. Launch the Story Editor application by running the `editor_core.py` file.
2. The main window will appear, displaying the various components for creating and managing your story.

## Configuring Story Settings

Begin by setting up the basic story information:

1. **Story Name**: Enter the name of your story in the provided text field.
2. **Button Color**: Click the "Button Color" button to open a color dialog and select the desired color for buttons in your story.
3. **Cover Image**: Click the "Choose Image" button to select a cover image for your story.
4. **Summary**: Enter a brief summary or description of your story in the provided text area.
5. **Start Room**: Once you've added rooms to your story, you can select the initial room where the adventure will begin from the dropdown menu.

## Creating and Managing Rooms

Rooms are the fundamental building blocks of your interactive story. Here's how to create and configure rooms:

1. Click the "Add Room" button to create a new room.
2. A new tab will appear in the "Rooms" section, representing the new room.
3. In the room tab, enter the room's name and description in the respective fields.
4. **Track Revisits**: Check this box if you want to enable revisit tracking for the room. This allows you to define unique content that will be displayed when the player revisits the room a specified number of times.
5. **Has Inventory**: Check this box if you want to enable inventory management for the room. This lets you define items that the player can acquire or require in the room.
6. **Room Image**: Click the "Choose Image" button to set an image for the room.
7. You can add or remove exits from the room using the "Add Exit" and "Remove Exit" buttons, respectively.

## Configuring Exits

Exits represent the paths between rooms that the player can take. To configure an exit:

1. In the room tab, click the "Add Exit" button to create a new exit.
2. Enter the name of the exit in the "Exit Name" field.
3. If the exit leads to another room, enter the name of the destination room in the "Exit Destination" field.
4. Alternatively, you can associate a skill check with the exit:
   - Click the "Skill Check" button to open the Skill Check dialog.
   - Configure the dice type, target number, and consequences for success and failure.
   - Click "OK" to save the skill check settings.

## Enabling Revisit Content

If you've enabled revisit tracking for a room, you can define the revisit content:

1. Click the revisit icon (circular arrow) next to the room tab to open the Revisit Dialog.
2. Enter the number of times the player must revisit the room before the revisit content is triggered.
3. Provide the revisit content in the text area.
4. Click "OK" to save the revisit settings.

## Managing Inventory Items

If you've enabled inventory management for a room, you can define items and requirements:

1. Click the inventory icon (key) next to the room tab to open the Inventory Dialog.
2. Enter the name and description of an item that the player can acquire in the room.
3. Optionally, you can specify an item that the player must possess to progress from the room or perform a specific action.
4. If an item is required, you can associate a skill check with it by configuring the skill check settings.
5. Click "OK" to save the inventory settings.

## Saving and Loading Stories

To save your story:

1. Go to the "File" menu and select "Save Story".
2. Choose a location and enter a filename for the story.
3. The story will be saved as a ZIP file, containing the story data and any associated images.

To load an existing story:

1. Go to the "File" menu and select "Load Story".
2. Navigate to the location of the story ZIP file and select it.
3. The story data will be loaded into the editor, allowing you to make further modifications.

## Importing and Exporting JSON Data

The Story Editor supports importing and exporting story data in JSON format. This can be useful for integrating with other tools or sharing story data.

To import JSON data:

1. Go to the "File" menu and select "Import" > "Import Raw JSON".
2. Select the JSON file containing the story data.
3. The editor will be populated with the imported data, including rooms, exits, skill checks, and inventory items.
4. Selecting this option also allows for syntax and formatting debugging of story json files.

## Additional Features

The Story Editor provides several other helpful features:

- **View Story Data**: Under the "View" menu, you can view various subsets of your story data, such as room count & exits
