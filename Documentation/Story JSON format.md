# Story file format and features

Stories are standard curly-brace json files packaged inside ZIP files.

Story MUST be named **'story.json'** and contain at least the following **required flags**

# required flags

**"name"** - Name of the story (displayed when playing)

**"button_color"** - hex color for choice buttons

**"start_room"** - initial story location

**"rooms"** -  every 'page' of a story book

**"description"** - self-explanatory

**"exits"** - links from a page to other pages - the editor allows up to 4 per room but is not hard-coded and adding more should work (untested)


# Example json:


```json
{
  "name": "The Haunted Mansion",
  "button_color": "#D3D3D3",
  "start_room": "mansion_entrance",
  "rooms": {
    "mansion_entrance": {
      "description": "You stand before the gates of an old, dilapidated mansion. Rumors say it's haunted by restless spirits. Will you dare to enter?",
      "exits": {
        "enter_the_mansion": "grand_foyer",
        "turn_back": null
      }
    },
    "grand_foyer": {
      "description": "The grand foyer is dimly lit, with dusty chandeliers hanging from the ceiling. Eerie portraits line the walls, their eyes seeming to follow your every move.",
      "exits": {
        "explore_the_living_room": "living_room",
        "climb_the_grand_staircase": "second_floor_hallway"
      }
    },
    "living_room": {
      "description": "The living room is filled with old, decaying furniture. A strange presence lingers in the air, making you feel uneasy.",
      "exits": {
        "search_for_clues": {
          "skill_check": {
            "dice_type": "1d20",
            "target": 15,
            "success": {
              "description": "You find an old journal that reveals the mansion's dark history.",
              "room": "hidden_study"
            },
            "failure": {
              "description": "You search the room but find nothing of significance.",
              "room": "grand_foyer"
            }
          }
        },
        "return_to_foyer": "grand_foyer"
      }
    },
    "second_floor_hallway": {
      "description": "The second-floor hallway is lined with doors leading to various rooms. The floorboards creak beneath your feet, and the air grows colder as you proceed.",
      "exits": {
        "enter_the_master_bedroom": "master_bedroom",
        "descend_the_staircase": "grand_foyer"
      }
    },
    "hidden_study": {
      "description": "The hidden study is filled with ancient tomes and mysterious artifacts. A sense of unease permeates the room, as if the secrets contained within are not meant for mortal eyes.",
      "exits": {
        "read_the_ancient_tome": {
          "skill_check": {
            "dice_type": "1d20",
            "target": 18,
            "success": {
              "description": "You decipher the ancient text and learn the secret to banishing the spirits.",
              "room": "ritual_chamber"
            },
            "failure": {
              "description": "The text is written in an unknown language, and you fail to comprehend its meaning.",
              "room": "living_room"
            }
          }
        },
        "leave_the_study": "living_room"
      }
    },
    "master_bedroom": {
      "description": "The master bedroom is lavishly decorated, but an oppressive atmosphere fills the room. A ghostly figure appears, its eyes filled with sorrow and anger.",
      "exits": {
        "confront_the_ghost": {
          "skill_check": {
            "dice_type": "1d20",
            "target": 20,
            "success": {
              "description": "You successfully communicate with the ghost and learn the key to its unrest.",
              "room": "ritual_chamber"
            },
            "failure": {
              "description": "The ghost attacks you, forcing you to flee the room.",
              "room": "second_floor_hallway"
            }
          }
        },
        "flee_the_room": "second_floor_hallway"
      }
    },
    "ritual_chamber": {
      "description": "The ritual chamber is hidden deep within the mansion. Ancient symbols adorn the walls, and a mysterious altar stands at the center. This is where you must confront the spirits and banish them.",
      "exits": {
        "perform_the_ritual": {
          "skill_check": {
            "dice_type": "1d20",
            "target": 25,
            "success": {
              "description": "You successfully perform the ritual, banishing the spirits and freeing the mansion from its curse.",
              "room": "mansion_entrance"
            },
            "failure": {
              "description": "The ritual goes wrong, and the spirits' power grows stronger. You barely manage to escape the mansion with your life.",
              "room": "mansion_entrance"
            }
          }
        },
        "abandon_the_ritual": "second_floor_hallway"
      }
    }
  }
}

```




# Additional flags 

In addition to the required flags above, "special" optional flags are also available:

`**"image"**` - Path to an image file stored inside the story ZIP (see below)

`**"revisit_count"**` - if the player is in this location for the Nth time, display additional content

`**"revisit_content"**` - The additional content to be displayed and/or actions to be performed


The Adventure! engine features a basic **STATE MACHINE** which can keep track of the players history and thus allows for unlocking of additional narratives when conditions are met (for example, players might see a hidden message upon visiting a previous room a second or third time, etc

# Image flag 

Images within stories are fully supported. Paths are relative to the story.json and live inside the ZIP archive:


```
"image": "images/prologue.jpg",
```


The example above would display prologue.jpg from the /images folder inside the story ZIP

Please do not include huge or uncompressed images in story archives.

If images are larger than 800x600 they will be scaled down to that size automatically.




-- MORE COMING SOON --
