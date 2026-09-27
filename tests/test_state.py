import unittest

from runtime.state import GameState


class StateTests(unittest.TestCase):
    def test_save_load_round_trip(self):
        state = GameState.new("RoundTrip", "start", random_seed=1234)
        state.inventory.append("key")
        state.variables["flag"] = True
        state.visit_counts["start"] = 2
        restored = GameState.from_dict(state.to_dict())
        self.assertEqual(restored.to_dict(), state.to_dict())

    def test_pending_check_is_json_serializable(self):
        state = GameState.new("Pending", "start", random_seed=9)
        state.pending_check = {"action_id": "door", "skill_check": {"success": {"room": "end"}}}
        restored = GameState.from_dict(state.to_dict())
        self.assertEqual(restored.pending_check, state.pending_check)

    def test_legacy_save_is_migrated(self):
        state = GameState.from_dict(
            {
                "current_adventure": "Legacy",
                "current_room": "room_b",
                "action_history": ["room_b", "room_c"],
            }
        )
        self.assertEqual(state.story_name, "Legacy")
        self.assertEqual(state.history_rooms, ["room_b", "room_c"])
        self.assertEqual(state.visit_counts["room_c"], 1)
