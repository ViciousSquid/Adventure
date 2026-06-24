# Adventure!

A modern interactive story engine for designing, editing, and playing branching narrative games. Write with rich mechanics like skill checks, dice rolls, and room state-tracking, then compile your stories directly to legacy interactive fiction formats.

<img src="https://github.com/user-attachments/assets/699cb5cb-abbf-46dc-8ab0-f4e0a1c72f34" width="300">



(  DOWNLOAD HERE: https://github.com/ViciousSquid/Adventure/releases )

![image](https://github.com/ViciousSquid/Adventure/assets/161540961/7d236ef0-9129-4b63-8e12-9b104d54bc01)



#### Key Features
- Modern Editor, Retro Deployments: Features a built-in story editor with full load/save support, plus an automated compiler tool to export straight to Z-Machine (v8) and Andrew Plotkin's Glulx format.

- TTRPG Mechanics: Native support for skill-checks, saving-throws, and randomized dice rolls with built-in animations.

- Dynamic State Tracking: Track room re-visits to seamlessly trigger extra content or alternate paths based on player history.

- Accessible Reading: Light/Dark modes and an optional Dyslexia-friendly font.

- Portable & Open Source: 100% free and open-source. Story files are packaged as simple .zip archives that are easy to download and share.

- Active Development: A basic inventory system is currently in active development.

### 🕹️ Included Stories
Launch the engine and try the following built-in examples:

- Three Choices – A quick introduction to basic branching.

- NOIR – A deeper look at narrative choices and atmosphere.

#### ⚠️ Note: Cosmic Paradox is currently undergoing a mechanical overhaul and is temporarily broken

### Quick Start
Adventure structures games using clean, manageable data layouts. Here is a quick look at how a branching room with a stat check is defined:

```json
{
  "room_id": "dark_corridor",
  "text": "The air is thick with dust. A heavy wooden door stands before you, locked from the inside.",
  "choices": [
    {
      "text": "Try to force the door open [Strength Check]",
      "type": "skill_check",
      "stat": "strength",
      "difficulty": 12,
      "on_success": "secret_chamber",
      "on_failure": "sore_shoulder"
    },
    {
      "text": "Turn back to the main hall",
      "type": "standard",
      "destination": "main_hall"
    }
  ]
}
}
```

#### Community & Contributions

Love books? Love reading? If you want to craft your own interactive worlds, you are highly encouraged to submit your stories via a Pull Request to be featured directly in this repository!

