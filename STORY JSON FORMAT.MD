# An overview of the Adventure! Story Format

The game engine contains a STATE MACHINE that can be used to keep track of a players position within a story and allows for other features
The following is an excerpt from a story utilising advanced features:

```
{
  "name": "The Cosmic Paradox",
  "button_color": "#0047ab",
  "start_room": "prologue",
  "rooms": {
    "prologue": {
      "description": "You wake up in a dimly lit room, disoriented and unsure of where you are. The air is thick with the scent of ozone, and a faint hum seems to permeate the very walls around you. As your eyes adjust to the darkness, you notice a strange device on the table in front of you, its surface etched with intricate glyphs and pulsating with an otherworldly glow. A deep, resonant voice echoes in your mind, 'The fate of the universe rests in your hands. Choose wisely, for the consequences of your actions will ripple across the fabric of existence itself.'",
      "exits": {
        "examine": "examine_device",
        "ignore": "ignore_device"
      },
      "revisit_count": 2,
      "revisit_content": "The voice echoes once more, its tone laced with a sense of urgency. 'Tread carefully, for the consequences of your actions will ripple across the multiverse in ways you cannot fathom. The delicate balance of existence hangs by a thread, and your choices will determine whether it unravels or remains intact.'"
    },
    "examine_device": {
      "description": "You examine the device closely, its surface seeming to shift and undulate beneath your gaze. It appears to be a quantum entanglement manipulator, capable of altering the very fabric of reality itself. A panel on the device displays two options: 'Preserve Timeline' and 'Alter Timeline'. As you study the device, you can't shake the sense that you are holding the fate of the cosmos in your hands, a power both exhilarating and terrifying.",
      "exits": {
        "preserve": "preserve_timeline",
        "alter": "alter_timeline"
      },
      "revisit_count": 1,
      "revisit_content": "As you examine the device again, you notice strange glyphs etched onto its surface, pulsating with an energy that seems to defy the laws of physics. The glyphs seem to shift and rearrange themselves, as if trying to convey a message lost to the ages – a cosmic warning about the power you now wield."
    },
    "ignore_device": {
      "description": "You decide to ignore the strange device, your instincts warning you against tampering with forces beyond your comprehension. As you search for a way out of the room, you can't shake the nagging feeling that you're missing something crucial – a piece of the puzzle that could unravel the mysteries of the universe itself. Just as you're about to give up, your foot catches on a loose panel, revealing a hidden compartment. Inside, you find another quantum entanglement manipulator, its surface thrumming with energy. The voice echoes again, its tone laced with a sense of finality, 'The choice is yours, but the consequences will be profound, rippling across the fabric of existence like a cosmic shockwave.'",
      "exits": {
        "examine": "examine_device"
      }
    },
    "preserve_timeline": {
      "description": "You choose to preserve the current timeline, believing that altering reality could have disastrous consequences that even your wildest imagination cannot fathom. The device powers down, and you find yourself transported back to your normal life, the familiar sights and sounds a welcome respite from the cosmic madness you've just encountered. However, as the days pass, strange occurrences begin to unfold around you, casting doubt on the notion that you truly preserved the timeline. Reality seems to warp and distort, as if the delicate fabric of existence is fraying at the seams, and you can't shake the feeling that something isn't quite right – a cosmic omen that your actions have set in motion a chain of events too vast and incomprehensible to foresee.",
      "exits": {
        "continue": "anomaly_detected"
      },
      "revisit_count": 1
    },
    "alter_timeline": {
      "description": "Driven by an insatiable curiosity and a thirst for knowledge that borders on hubris, you decide to alter the timeline, consequences be damned. The device hums to life, its energy pulsating through your very being as reality begins to shift and distort around you. In a cosmic blink of an eye, you find yourself in a parallel universe where the laws of physics have been rewritten, and strange beings roam the cosmos – entities whose very existence seems to defy the natural order of things. As you gaze upon this alien landscape, you can't help but wonder if you've made a grave mistake, or if this is merely the first step on a journey that will unravel the secrets of the multiverse itself.",
      "exits": {
        "explore": "parallel_universe"
      },
      "revisit_count": 1
    },
```
