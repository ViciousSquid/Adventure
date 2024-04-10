## The OutcomeDeterminer Class

<code style="color : name_color">**OutcomeDeterminer**</code> class determines the outcome of a dice roll based on the target number and outcome details. It provides the following method:

<code style="color : name_color">**determine_outcome(roll_result, target, success_outcome, failure_outcome)**</code> Determines the outcome based on the dice roll result and the target number. Checks for critical success or failure based on the maximum or minimum dice roll value.

<code style="color : name_color">roll_result</code> : An integer representing the result of the dice roll.
<code style="color : name_color">target</code> : An integer representing the target number to beat.
<code style="color : name_color">success_outcome</code> : A dictionary containing the outcome details if the roll is successful.
<code style="color : name_color">failure_outcome</code> : A dictionary containing the outcome details if the roll is a failure.

<code style="color : name_color">Returns</code> : A dictionary containing the outcome details based on the dice roll result.

Raises <code style="color : name_color">ValueError</code> if the <code style="color : name_color">target</code> , <code style="color : name_color">success_outcome</code>, or <code style="color : name_color">failure_outcome</code> is not provided.

### Example usage:

```
from diceroll import OutcomeDeterminer

# Create an instance of OutcomeDeterminer (not necessary since its method is static)
outcome_determiner = OutcomeDeterminer()

# Determine the outcome for a roll of 15 with a target of 10
result = outcome_determiner.determine_outcome(15, 10, {"details": "Success!"}, {"details": "Failure."})
print(result)  # Output: {'details': 'Success!', 'roll_result': 15}
```
