### Here's how a saving throw will be handled when it is encountered in the story:

In the provided story, `"The Haunted Mansion"`, there are several instances where saving throws or skill checks are incorporated into the narrative. These saving throws are used to determine the outcome of certain actions or events based on the roll of a dice.

Let's take a closer look at one of the saving throws in the `Haunted Mansion` story.son:

```json
...
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
}
```

In this example, when the player chooses to "search for clues" in the living room, a skill check is triggered. The skill check is defined by the following parameters:

* `dice_type`: "1d20" indicates that a 20-sided dice should be rolled.
* `target`: The target value is set to 15, meaning the player needs to roll a 15 or higher to succeed.
* `success` and `failure`: These objects define the outcomes based on the result of the dice roll.

When the player reaches this point in the story and chooses to "search for clues," the game will handle the saving throw as follows:

* The game will use the `roll_dice` function from the `dicerollAPI` to roll a 20-sided dice (1d20).
* The result of the dice roll will be compared against the target value of 15.
* If the dice roll is equal to or greater than 15, the saving throw is considered a success.
*The game will display the success description, "You find an old journal that reveals the mansion's dark history," and move the player to the **"hidden_study"** room.*
* If the dice roll is less than 15, the saving throw is considered a failure.
*The game will display the failure description, "You search the room but find nothing of significance," and move the player to the **"grand_foyer"** room.*

* The dicerollAPI will handle the actual rolling of the dice based on the specified dice_type. The game logic will then interpret the result of the dice roll and determine the appropriate outcome based on the defined success and failure conditions.

* This process will be repeated for each saving throw encountered throughout the story. The success and failure descriptions, as well as the target rooms, can vary depending on the specific scenario and the desired narrative flow.

