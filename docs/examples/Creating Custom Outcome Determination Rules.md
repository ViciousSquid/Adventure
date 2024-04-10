### Creating Custom Outcome Determination Rules

You can create your own custom outcome determination rules by subclassing the <code style="color : name_color">OutcomeDeterminer</code> class and overriding the <code style="color : name_color">determine_outcome</code> method.

Here's an example:

```python
from diceroll import OutcomeDeterminer

class CustomOutcomeDeterminer(OutcomeDeterminer):
    @staticmethod
    def determine_outcome(roll_result, target, success_outcome, failure_outcome):
        # Implement your custom outcome determination logic here
        pass
```
