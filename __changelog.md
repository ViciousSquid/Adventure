### changelog


### build 106 - 19/04/2024
-----
* Editor has been completely rewritten to support skill checks and saving-throws.
* Example story `dice roll test` can be loaded into the editor
* Backwards compatibility with old story files (pre 106) has been retained.
* Added 'summary' field which will appear on main menu in future update.
* Includes the OpenDyslexia font by Abbie Gonzalez: https://antijingoist.itch.io/opendyslexic
-----

### build 105


Integration of `dicerollAPI` :
Read more about diceroll here: https://github.com/ViciousSquid/diceroll

This allows all-new support for skill checks, saving-throws etc within story.json files

* Focus of this build is to ensure stable integration with the new api
* Functionality remains the same as main branch
* No new content yet, all changes are under-the-hood

-----

### **Debug mode** 
The presence of `debug.txt` triggers debug mode: all console output is saved to /logs

* This has been included by default. This means logging on ON by default.
* To disable logging, delete the `debug.txt` file
* For production deployment it is recommended that debug mode is disabled.
* Please include logs when error reporting
