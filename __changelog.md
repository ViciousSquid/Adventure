### changelog


* build 106

Includes the OpenDyslexia font by Abbie Gonzalez: https://antijingoist.itch.io/opendyslexic


* build 105

-----

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
