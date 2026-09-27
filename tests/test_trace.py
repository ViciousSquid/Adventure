import random
import unittest

from runtime.engine import AdventureEngine
from runtime.trace import format_trace
from story.model import Story


class TraceTests(unittest.TestCase):
    def test_trace_is_structured_and_human_readable(self):
        story = Story.from_dict(
            {
                "name": "Trace",
                "start_room": "start",
                "rooms": {
                    "start": {"description": "Start", "exits": {"go": "end"}},
                    "end": {"description": "End", "exits": {}},
                },
            }
        )
        engine = AdventureEngine(story, rng=random.Random(1), trace=True)
        state = engine.new_game()
        result = engine.step(state, "go")
        self.assertTrue(result.trace)
        self.assertEqual(result.trace[-1]["type"], "state")
        self.assertIn("[TRANSITION]", format_trace(result, state))
