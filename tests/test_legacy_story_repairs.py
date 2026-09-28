import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from tools.repair_legacy_stories import (
    CURSE_WORLD,
    ENIGMA_ROOMS,
    ENIGMA_WORLD,
    WHISPERS_WORLD,
    repair_archive,
    repair_story,
)


class LegacyStoryRepairTests(unittest.TestCase):
    def test_enigma_adds_real_intermediate_rooms(self):
        story = {
            "rooms": {
                "laboratory": {"description": "Lab", "exits": {
                    "activate": "chronal_engine_room",
                }},
                "basement": {"description": "Basement", "exits": {
                    "activate": "time_sphere",
                }},
                "library_tower": {"description": "Tower", "exits": {
                    "activate": "orrery_control",
                }},
                "temporal_vortex": {"description": "Vortex", "exits": {}},
                "time_sphere_chamber": {"description": "Sphere", "exits": {}},
                "time_travel_nexus": {"description": "Nexus", "exits": {}},
            }
        }
        added = repair_story(ENIGMA_WORLD, story)

        self.assertEqual(added, 3)
        self.assertEqual(set(ENIGMA_ROOMS), {
            key for key in story["rooms"] if key in ENIGMA_ROOMS
        })
        self.assertEqual(
            story["rooms"]["chronal_engine_room"]["exits"]["Step through the chronal portal"],
            "temporal_vortex",
        )
        self.assertEqual(
            story["rooms"]["time_sphere"]["exits"]["Approach the Time Sphere"],
            "time_sphere_chamber",
        )
        self.assertEqual(
            story["rooms"]["orrery_control"]["exits"]["Set the Orrery in motion"],
            "time_travel_nexus",
        )

    def test_curse_dangling_destinations_become_written_endings(self):
        story = {
            "rooms": {
                "siren": {
                    "description": "The sea.",
                    "exits": {
                        "accept": "siren's_judgment",
                        "break": "free_of_the_curse",
                    },
                }
            }
        }
        added = repair_story(CURSE_WORLD, story)

        self.assertEqual(added, 2)
        self.assertIn("siren's_judgment", story["rooms"])
        self.assertIn("free_of_the_curse", story["rooms"])
        self.assertTrue(story["rooms"]["free_of_the_curse"]["description"])
        self.assertEqual(story["rooms"]["free_of_the_curse"]["exits"], {})

    def test_whispers_repairs_all_missing_targets_as_endings(self):
        story = {
            "rooms": {
                "crossroads": {
                    "description": "The crossroads.",
                    "exits": {
                        "fate": "embracing_destiny",
                        "wisdom": "the_scholar's_path",
                    },
                }
            }
        }
        added = repair_story(WHISPERS_WORLD, story)

        self.assertEqual(added, 2)
        for room_id in ("embracing_destiny", "the_scholar's_path"):
            room = story["rooms"][room_id]
            self.assertEqual(room["name"], "Embracing Destiny" if room_id == "embracing_destiny" else "The Scholar's Path")
            self.assertTrue(room["description"])
            self.assertEqual(room["exits"], {})

    def test_archive_repair_preserves_non_story_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Curse_of_the_Crimson_Cutlass.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr(
                    "story.json",
                    json.dumps(
                        {
                            "rooms": {
                                "start": {
                                    "description": "Start",
                                    "exits": {"finish": "free_of_the_curse"},
                                }
                            }
                        }
                    ),
                )
                archive.writestr("assets/ship.txt", b"ship asset")

            added = repair_archive(path, CURSE_WORLD)

            self.assertEqual(added, 1)
            with ZipFile(path) as archive:
                repaired = json.loads(archive.read("story.json"))
                self.assertIn("free_of_the_curse", repaired["rooms"])
                self.assertEqual(archive.read("assets/ship.txt"), b"ship asset")


if __name__ == "__main__":
    unittest.main()
