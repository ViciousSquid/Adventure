import random
import unittest

from runtime.engine import AdventureEngine
from runtime.trace import format_trace
from story.model import Story


class TraceTests(unittest.TestCase):
    def test_trace_is_structured_and_human_readable(self):
        story = Story.from_package(
            {
                "schema_version": 3,
                "name": "Trace",
                "start_room": "start",
                "rooms": {
                    "start": {"description": "Start"},
                    "end": {"description": "End"},
                },
                "connections": {
                    "start__go": {
                        "from": "start",
                        "to": "end",
                        "label": "Go",
                    }
                },
                "revisits": {},
                "metadata": {},
            },
            {"schema_version": 1, "skill_checks": {}},
            {
                "schema_version": 1,
                "items": {},
                "room_items": {},
                "room_requirements": {},
            },
        )
        engine = AdventureEngine(
            story,
            rng=random.Random(1),
            trace=True,
        )
        state = engine.new_game()
        result = engine.step(state, "start__go")
        self.assertTrue(result.trace)
        self.assertEqual(result.trace[-1]["type"], "state")
        self.assertIn(
            "[TRANSITION]",
            format_trace(result, state),
        )
