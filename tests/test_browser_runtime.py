import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "static" / "py" / "browser_runtime.py"

spec = importlib.util.spec_from_file_location("adventure_browser_runtime", MODULE_PATH)
browser_runtime = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = browser_runtime
assert spec.loader is not None
spec.loader.exec_module(browser_runtime)


def make_package():
    return {
        "world": "BrowserTest",
        "source_format": "canonical",
        "story": {
            "schema_version": 3,
            "name": "BrowserTest",
            "start_room": "start",
            "rooms": {
                "start": {"description": "Start"},
                "end": {"description": "End"},
            },
            "connections": {
                "start__end": {
                    "from": "start",
                    "to": "end",
                    "label": "Go",
                }
            },
            "revisits": {},
            "metadata": {},
        },
        "skill_checks": {"schema_version": 1, "skill_checks": {}},
        "inventory": {
            "schema_version": 1,
            "items": {},
            "room_items": {},
            "room_requirements": {},
        },
        "assets": {},
    }


class BrowserRuntimeTests(unittest.TestCase):
    def test_python_runtime_can_start_and_step(self):
        package = make_package()
        state = browser_runtime.GameState.new("BrowserTest", "start")
        result = browser_runtime.AdventureEngine(package).step(state, "start__end")
        self.assertTrue(result["ok"])
        self.assertEqual(state.current_room, "end")

    def test_room_skill_check_unlocks_legacy_exits(self):
        package = make_package()
        package["story"]["rooms"]["start"]["skill_check"] = "door"
        package["skill_checks"]["skill_checks"]["door"] = {
            "dice_type": "1d20",
            "target": 10,
            "success": {
                "description": "You find the clue.",
                "exits": {"Take the clue": "end"},
            },
            "failure": {"description": "You find nothing."},
        }

        state = browser_runtime.AdventureEngine(package).new_game()
        state.random_seed = 0
        self.assertTrue(
            browser_runtime.AdventureEngine(package).observe(state)["awaiting_roll"]
        )

        result = browser_runtime.AdventureEngine(package).step(state, "roll")
        self.assertIn(
            {"id": "start__skill__Take the clue", "label": "Take the clue", "to": "end"},
            result["choices"],
        )

        stepped = browser_runtime.AdventureEngine(package).step(
            state,
            "start__skill__Take the clue",
        )
        self.assertTrue(stepped["ok"])
        self.assertEqual(state.current_room, "end")

    def test_canonical_zip_round_trip(self):
        package = make_package()
        payload = browser_runtime.package_to_zip(package)
        loaded = browser_runtime.package_from_zip(payload)
        self.assertEqual(loaded["story"], package["story"])
        self.assertEqual(loaded["skill_checks"], package["skill_checks"])
        self.assertEqual(loaded["inventory"], package["inventory"])


if __name__ == "__main__":
    unittest.main()
