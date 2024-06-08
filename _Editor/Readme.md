## Story Editor

![image](https://github.com/ViciousSquid/Adventure/assets/161540961/e6e581c9-b6e2-4cea-b92e-5ef45acff7ba)

*  Placeholder for Readme  *

  Editor is still under heavy development. Manual is coming soon.

## Validator.py

After creating a story you should run it through `Validator.py` before playing:

You don't have to but it's strongly recommended 

`Validator.py` will scan through the room descriptions to detect invalid characters that might break the json formatting. It will also replace new lines with the `\n` character. 

This will ensure that stories are structured and formatted in a way that the game engine expects.

Launch with the `-help` argument to get a full list of arguments for this tool.

----------

Available launch arguments:

            -file [path]    Opens the specified file for viewing
            
            -validate [path]  Opens a file, performs the validation and saves a new file with the changes
            
            -onlyjson [path]  Opens a, performs the validation and saves only the story.json file (does not create a zip)
            
            -analyse [path]  Prints a debugging analysis of a story file to the console
