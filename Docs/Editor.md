![image](https://github.com/ViciousSquid/Adventure/assets/161540961/1e79ca44-9425-4629-92ef-7dbf3e80b1c6)


The Story Editor offers several advanced features to enhance the storytelling experience and provide more flexibility in creating interactive adventures.

## Skill Checks

Skill checks allow you to incorporate randomized challenges into your story, adding an element of uncertainty and excitement. When configuring an exit, you can associate it with a skill check by defining the following parameters:

- **Dice Type**: Specify the type of dice to be rolled for the skill check (e.g., d6, d8, d10).
- **Target**: Set the target number that the player needs to roll equal to or higher than to succeed.
- **Success Consequence**: Define the consequence when the player succeeds the skill check, including a description and the destination room.
- **Failure Consequence**: Specify the consequence when the player fails the skill check, including a description and the destination room.

## Revisit Content

The Revisit Content feature enables you to create dynamic and responsive stories by providing unique content when the player revisits a room. When enabling revisit tracking for a room, you can configure the following:

- **Revisit Count**: Set the number of times the player must revisit the room before triggering the revisit content.
- **Revisit Content**: Enter the text or description that will be displayed when the player revisits the room after the specified revisit count.

This feature allows for seamless integration of dynamic story elements, such as revealing new information, unlocking hidden areas, or introducing plot twists based on the player's actions and exploration.

## Inventory Management

The Story Editor supports inventory management, allowing you to define items that the player can acquire or require during the adventure. When enabling inventory management for a room, you can specify the following:

- **Item**: Define the name and description of an item that the player can obtain in the room.
- **Item Needed**: Specify an item that the player must possess to progress from the room or perform a specific action.
- **Item Skill Check**: Associate a skill check with an item needed, requiring the player to succeed in the check to use or obtain the item.

Inventory management adds depth to your stories by introducing puzzles, challenges, and gated progress based on the player's item collection and usage.

## Importing and Exporting JSON Data

The Story Editor allows you to import and export story data in JSON format, enabling seamless integration with other tools or systems. You can import raw JSON data to populate the editor with existing story content, or export your current story as a JSON file for further processing or sharing.

When importing JSON data, the editor will parse the provided file and populate the corresponding fields, including rooms, exits, skill checks, revisit content, and inventory items. Exporting to JSON allows you to save your story data in a structured and portable format, making it easy to transfer or collaborate on stories across different platforms or environments.
