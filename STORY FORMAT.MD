# Story file format and features

Stories are standard curly-brace json files.
They MUST be named 'story'json' and must contain at least the following:

**"name"** - Name of the story (displayed when playing)

**"button_color"** - hex color for choice buttons

**"start_room"** - initial story location

**"rooms"** - lists every 'page' of the story

**"description"** - self-explanatory

**"exits"** - links from a page to other pages - the engine assumes up to four per room but is not hard-coded and adding more should work (untested)


# EXAMPLE:


```
{
    "name": "Gadzooks!",
    "button_color": "7101AD",
    "start_room": "bedroom",
    "rooms": {
      "bedroom": {
        "description": "I woke up with a start, my heart pounding in my chest. \"Gadzooks!\" I exclaimed, looking around my bedroom in wide-eyed wonder."
        "exits": {
          "go_to_kitchen": "kitchen",
          "look_out_window": "surprise_visitor"
        }

...
```

Additional (optional) tags are also available:

**"image"** - Path to an image file stored inside the story ZIP (see below)

**"revisit_count"** - if the player is in this location for the Nth time, display additional content

**"revisit_content"** - The additional content to be displayed and/or actions to be performed


The Adventure! engine features a basic **STATE MACHINE** which can keep track of the players history and thus allows for unlocking of additional narratives when conditions are met (for example, players might see a hidden message upon visiting a previous room a second or third time, etc
Here is a secion of a story that uses this feature:

# EXAMPLE: 


```
{
  "name": "NAME", #
  "button_color": "#0047ab",
  "start_room": "prologue",
  "rooms": {
    "prologue": {
      "description": "You wake up in a dimly lit room, disoriented and unsure of where you are. The air is thick with the scent of ozone, and a faint hum seems to permeate the very walls around you. As your eyes adjust to the darkness, you notice a strange device on the table in front of you, its surface etched with intricate glyphs and pulsating with an otherworldly glow. A deep, resonant voice echoes in your mind, 'The fate of the universe rests in your hands. Choose wisely, for the consequences of your actions will ripple across the fabric of existence itself.'",
      "exits": {
        "examine": "examine_device",
        "ignore": "ignore_device"
      },
      ...

In this example, if ** "revisit_count" ** is 2 for this room then ** "revisit_content" ** will be displayed to the player. Some rooms in this story trigger additional content when they are revisited for the third time. This is in keeping with the multi-dimensional narrative of this particular story.
This will be expanded upon in future released.

# Images 

Images within stories are fully supported. Paths are relative to the story.json and live inside the ZIP archive:

```
"image": "images/prologue.jpg",
...

The example above would display prologue.jpg from the /images folder inside the story ZIP
If images are larger than 800x600 they will be scaled down automatically.

-- MORE COMING SOON --
