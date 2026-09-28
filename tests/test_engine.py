import random
import unittest

from runtime.engine import AdventureEngine
from story.model import Story


def make_story():
    return Story.from_package(
        {
            "schema_version": 3,
            "name": "EngineTest",
            "start_room": "start",
            "rooms": {
                "start": {"description": "Start"},
                "end": {"description": "End"},
            },
            "connections": {
                "start__north": {
                    "from": "start",
                    "to": "end",
                    "label": "Go north",
                },
                "start__door": {
                    "from": "start",
                    "to": "start",
                    "label": "Open door",
                    "skill_check": "door",
                },
                "end__back": {
                    "from": "end",
                    "to": "start",
                    "label": "Go back",
                },
            },
            "revisits": {
                "end": {
                    "show_all": False,
                    "entries": [{"count": 2, "content": "Again."}],
                }
            },
            "metadata": {},
        },
        {
            "schema_version": 1,
            "skill_checks": {
                "door": {
                    "dice_type": "1d20",
                    "target": 10,
                    "description": "The check resolves.",
                    "success": {"description": "ignored", "to": "end"},
                    "failure": {"description": "ignored", "to": "start"},
                }
            },
        },
        {
            "schema_version": 1,
            "items": {"key": {"name": "Rusty Key"}},
            "room_items": {"start": ["key"]},
            "room_requirements": {},
        },
    )


class EngineTests(unittest.TestCase):
    def test_new_game_is_isolated(self):
        engine = AdventureEngine(make_story(), rng=random.Random(1234))
        a = engine.new_game()
        b = engine.new_game()
        engine.step(a, "start__north")
        self.assertEqual(a.current_room, "end")
        self.assertEqual(b.current_room, "start")

    def test_normal_transition_records_history_and_visits(self):
        engine = AdventureEngine(make_story())
        state = engine.new_game()
        result = engine.execute(state, "start__north")
        self.assertTrue(result.ok)
        self.assertEqual(state.current_room, "end")
        self.assertEqual(state.history_rooms, ["end"])
        self.assertEqual(state.visit_counts["end"], 1)

    def test_pending_skill_check_blocks_other_actions_until_rolled(self):
        engine = AdventureEngine(make_story())
        state = engine.new_game()
        pending = engine.step(state, "start__door")
        self.assertTrue(pending.awaiting_roll)
        blocked = engine.step(state, "start__north")
        self.assertFalse(blocked.ok)
        self.assertEqual(blocked.error, "pending_roll")
        self.assertEqual(state.current_room, "start")

    def test_skill_check_is_deterministic_from_state(self):
        engine = AdventureEngine(make_story(), rng=random.Random(7))
        a = engine.new_game()
        b = type(a).from_dict(a.to_dict())

        engine.step(a, "start__door")
        result_a = engine.step(a, "roll")
        engine.step(b, "start__door")
        result_b = engine.step(b, "roll")

        self.assertEqual(
            result_a.dice_results[0].to_dict(),
            result_b.dice_results[0].to_dict(),
        )
        self.assertEqual(a.current_room, b.current_room)

    def test_top_level_skill_description_preserves_legacy_precedence(self):
        engine = AdventureEngine(make_story(), rng=random.Random(3))
        state = engine.new_game()
        engine.step(state, "start__door")
        result = engine.step(state, "roll")
        self.assertEqual(result.text, "The check resolves.")

    def test_room_skill_check_is_armed_and_resolves(self):
        data = make_story().to_dict()
        data["story"]["rooms"]["start"]["skill_check"] = "door"
        engine = AdventureEngine(
            Story.from_package(data["story"], data["skill_checks"], data["inventory"]),
            rng=random.Random(123),
        )
        state = engine.new_game()

        observed = engine.observe(state)
        self.assertTrue(observed.awaiting_roll)
        self.assertEqual(
            state.pending_check,
            {
                "kind": "room",
                "room_id": "start",
                "skill_check_id": "door",
            },
        )

        rolled = engine.step(state, "roll")
        self.assertFalse(rolled.awaiting_roll)
        self.assertIn(state.current_room, {"start", "end"})
        self.assertIsNone(state.pending_check)

    def test_successful_room_skill_check_unlocks_legacy_exits(self):
        story_data = make_story().to_dict()
        story_data["story"]["rooms"]["start"]["skill_check"] = "door"
        story_data["skill_checks"]["skill_checks"]["door"] = {
            "dice_type": "1d20",
            "target": 10,
            "success": {
                "description": "You find the clue.",
                "exits": {"Take the clue": "end"},
            },
            "failure": {"description": "You find nothing."},
        }
        engine = AdventureEngine(
            Story.from_package(
                story_data["story"],
                story_data["skill_checks"],
                story_data["inventory"],
            )
        )
        state = engine.new_game()
        state.random_seed = 0

        pending = engine.observe(state)
        self.assertTrue(pending.awaiting_roll)

        rolled = engine.step(state, "roll")
        self.assertIsNone(state.pending_check)
        self.assertEqual(
            [choice["label"] for choice in rolled.choices],
            ["Go north", "Open door", "Take the clue"],
        )

        result = engine.step(state, "start__skill__Take the clue")
        self.assertTrue(result.ok)
        self.assertEqual(state.current_room, "end")

    def test_revisit_content_is_state_driven(self):
        engine = AdventureEngine(make_story())
        state = engine.new_game()
        engine.step(state, "start__north")
        self.assertNotIn("Again.", engine.observe(state).text)
        engine.step(state, "end__back")
        engine.step(state, "start__north")
        self.assertIn("Again.", engine.observe(state).text)
        self.assertEqual(state.visit_counts["end"], 2)

    def test_inventory_is_runtime_state_and_actions(self):
        engine = AdventureEngine(make_story())
        state = engine.new_game()
        result = engine.step(state, "acquire:key")
        self.assertTrue(result.ok)
        self.assertEqual(state.inventory, ["key"])
        self.assertEqual(engine.available_items(state), [])

        result = engine.step(state, "use:key")
        self.assertTrue(result.ok)
        self.assertEqual(state.inventory, [])

    def test_missing_required_item_blocks_connection(self):
        story = make_story()
        story = Story.from_package(
            story.data,
            story.skill_checks,
            {
                "schema_version": 1,
                "items": {"key": {"name": "Rusty Key"}},
                "room_items": {},
                "room_requirements": {},
            },
        )
        data = story.to_dict()
        data["story"]["connections"]["start__north"]["requires_item"] = "key"
        story = Story.from_package(
            data["story"], data["skill_checks"], data["inventory"]
        )
        engine = AdventureEngine(story)
        state = engine.new_game()
        result = engine.step(state, "start__north")
        self.assertFalse(result.ok)
        self.assertEqual(result.error, "missing_item")
