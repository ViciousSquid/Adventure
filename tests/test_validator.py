import unittest

from story.validator import StoryValidationError, validate_story_data


class StoryValidationTests(unittest.TestCase):
    def base_story(self):
        return {
            "name": "Test",
            "start_room": "start",
            "rooms": {
                "start": {
                    "description": "Start",
                    "exits": {"north": "end"},
                    "items": ["key"],
                },
                "end": {"description": "End", "exits": {}},
            },
        }

    def test_valid_story_loads(self):
        self.assertEqual(validate_story_data(self.base_story())["start_room"], "start")

    def test_historical_aliases_are_normalised(self):
        story = {"title": "Old", "start": "start", "rooms": {"start": {"description": "Start", "exits": {}}}}
        canonical = validate_story_data(story)
        self.assertEqual(canonical["name"], "Old")
        self.assertEqual(canonical["start_room"], "start")
        self.assertNotIn("title", canonical)
        self.assertNotIn("start", canonical)

    def test_missing_start_room_rejected(self):
        story = self.base_story()
        story["start_room"] = "missing"
        with self.assertRaises(StoryValidationError):
            validate_story_data(story)

    def test_missing_destination_rejected(self):
        story = self.base_story()
        story["rooms"]["start"]["exits"]["north"] = "roof"
        with self.assertRaisesRegex(StoryValidationError, "rooms.start.exits.north"):
            validate_story_data(story)

    def test_malformed_skill_check_rejected(self):
        story = self.base_story()
        story["rooms"]["start"]["exits"]["north"] = {
            "skill_check": {
                "dice_type": "banana",
                "target": "hard",
                "success": {"room": "end"},
                "failure": {"room": "start"},
            }
        }
        with self.assertRaises(StoryValidationError):
            validate_story_data(story)

    def test_bad_item_reference_rejected(self):
        story = self.base_story()
        story["rooms"]["end"]["item_needed"] = "missing"
        with self.assertRaises(StoryValidationError):
            validate_story_data(story)
