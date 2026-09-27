# Adventure Narrative VM Architecture

The story package is executable narrative data.

    ZIP -> PackageLoader -> validation -> Story
                                    |
                                    v
                            AdventureEngine + GameState
                                    |
                                    v
                              ExecutionResult
                                    |
                                    v
                              presentation

    Story -> Z-Machine / Glulx exporters

Story is immutable authored content. GameState is mutable execution memory. AdventureEngine is the interpreter and owns no player state. ExecutionResult is structured VM output and contains no HTML.

The existing room-based story.json representation remains the canonical language. Historical top-level aliases title -> name and start -> start_room are normalised once at load time.

Runtime vocabulary is deliberately small: JUMP, CHOICE, CHECK/ROLL, conditional display, state effects and DISPLAY. These remain data operations rather than a class hierarchy.

ActionRecord is the common history boundary for replay/debug/save features. DiceResult carries expression, individual rolls, modifier, total, target and success. Each GameState carries a seed and roll count so future dice are deterministic after save/load.

PackageLoader caches validated Story instances. PackageWriter validates before writing. Exporters receive Story directly. The browser editor continues to author the same room-based representation and the graph is generated from canonical Story data.

The refactor deliberately uses the useful Fio principle of explicit data boundaries without importing Fio's spatial/numerical machinery into a narrative domain that does not need it.
