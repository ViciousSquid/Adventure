import random
import unittest

from runtime.engine import AdventureEngine
from runtime.state import GameState
from story.model import Story


def make_story():
    return Story.from_dict(
        {
            "name": "EngineTest",
            "start_room": "start",
            "rooms": {
                "start": {
                    "description": "Start",
                    "exits": {
                        "north": "end",
                        "door": {
                            "skill_check": {
                                "dice_type": "1d20",
                                "target": 10,
                                "success": {"description": "Success", "room": "end"},
                                "failure": {"description": "Failure", "room": "start"},
                            }
                        },
                        "legacy_check": {
                            "skill_check": {
                                "dice_type": "1d20",
                                "target": 10,
                                "description": "The check resolves.",
                                "success": {"room": "end"},
                                "failure": {"room": "start"},
                            }
                        },
                    },
                    "items": ["key"],
                },
                "end": {
                    "description": "End",
                    "exits": {"back": "start"},
                    "revisits": [{"count": 2, "content": "Again."}],
                },
            },
        }
    )


class EngineTests(unittest.TestCase):
    def test_new_game_is_isolated(self):
        engine = AdventureEngine(make_story(), rng=random.Random(1234))
        a = engine.new_game()
        b = engine.new_game()
        engine.step(a, "north")
        self.assertEqual(a.current_room, "end")
        self.assertEqual(b.current_room, "start")

    def test_normal_transition_records_history_and_visits(self):
        engine = AdventureEngine(make_story())
        state = engine.new_game()
        result = engine.execute(state, "north")
        self.assertTrue(result.ok)
        self.assertEqual(state.current_room, "end")
        self.assertEqual(state.history_rooms, ["end"])
        self.assertEqual(state.visit_counts["end"], 1)

    def test_skill_check_is_deterministic_from_state(self):
        engine = AdventureEngine(make_story(), rng=random.Random(7))
        a = engine.new_game()
        b = GameState.from_dict(a.to_dict())

        engine.step(a, "door")
        result_a = engine.step(a, "roll")
        engine.step(b, "door")
        result_b = engine.step(b, "roll")

        self.assertEqual(result_a.dice_results[0].to_dict(), result_b.dice_results[0].to_dict())
        self.assertEqual(a.current_room, b.current_room)

    def test_legacy_skill_description_is_preserved(self):
        engine = AdventureEngine(make_story(), rng=random.Random(3))
        state = engine.new_game()
        engine.step(state, "legacy_check")
        result = engine.step(state, "roll")
        self.assertEqual(result.text, "The check resolves.")

    def test_revisit_content_is_state_driven(self):
        engine = AdventureEngine(make_story())
        state = engine.new_game()
        engine.step(state, "north")
        self.assertNotIn("Again.", engine.observe(state).text)
        engine.step(state, "back")
        engine.step(state, "north")
        self.assertIn("Again.", engine.observe(state).text)
        self.assertEqual(state.visit_counts["end"], 2)

    def test_inventory_is_runtime_state(self):
        engine = AdventureEngine(make_story())
        state = engine.new_game()
        result = engine.acquire_item(state, "key")
        self.assertTrue(result.ok)
        self.assertEqual(state.inventory, ["key"])
        self.assertEqual(engine.available_items(state), [])
