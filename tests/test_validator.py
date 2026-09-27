import unittest

from story.validator import StoryValidationError, validate_package_data


def valid_package():
    return (
        {
            "schema_version": 3,
            "name": "Test",
            "start_room": "start",
            "rooms": {
                "start": {"description": "Start"},
                "end": {"description": "End"},
            },
            "connections": {
                "start__north": {
                    "from": "start",
                    "to": "end",
                    "label": "north",
                }
            },
            "revisits": {},
            "metadata": {},
        },
        {"schema_version": 1, "skill_checks": {}},
        {
            "schema_version": 1,
            "items": {"key": {"name": "Key"}},
            "room_items": {"start": ["key"]},
            "room_requirements": {},
        },
    )


class StoryValidationTests(unittest.TestCase):
    def test_valid_package_loads(self):
        story, checks, inventory = valid_package()
        validated = validate_package_data(
            story,
            checks,
            inventory,
        )
        self.assertEqual(
            validated[0]["start_room"],
            "start",
        )

    def test_schema_versions_are_required(self):
        story, checks, inventory = valid_package()
        story["schema_version"] = 2
        with self.assertRaisesRegex(
            StoryValidationError,
            "story.schema_version",
        ):
            validate_package_data(story, checks, inventory)

    def test_connection_cross_reference_errors_are_path_specific(self):
        story, checks, inventory = valid_package()
        story["connections"]["bad"] = {
            "from": "start",
            "to": "missing",
            "label": "bad",
            "skill_check": "missing_check",
            "requires_item": "missing_item",
        }
        with self.assertRaisesRegex(
            StoryValidationError,
            r"story\.connections\.bad\.to",
        ) as context:
            validate_package_data(
                story,
                checks,
                inventory,
            )
        self.assertIn(
            "story.connections.bad.skill_check: unknown skill check 'missing_check'",
            context.exception.errors,
        )
        self.assertIn(
            "story.connections.bad.requires_item: unknown item 'missing_item'",
            context.exception.errors,
        )

    def test_skill_check_destinations_and_inventory_references_are_checked(self):
        story, checks, inventory = valid_package()
        checks["skill_checks"]["door"] = {
            "dice_type": "1d20",
            "target": 10,
            "success": {
                "to": "end",
                "description": "Open",
            },
            "failure": {
                "to": "missing",
                "description": "Fail",
            },
        }
        story["connections"]["start__door"] = {
            "from": "start",
            "to": "end",
            "label": "door",
            "skill_check": "door",
        }
        with self.assertRaisesRegex(
            StoryValidationError,
            r"skill_checks\.skill_checks\.door\.failure\.to",
        ):
            validate_package_data(
                story,
                checks,
                inventory,
            )


    def test_rich_description_html_is_validated(self):
        story, checks, inventory = valid_package()
        story["rooms"]["start"]["description_html"] = (
            "<p><strong>Hello</strong></p>"
            '<img src="assets/rich_text/door.png" style="width:320px">'
        )
        validated = validate_package_data(story, checks, inventory)
        self.assertIn(
            "description_html",
            validated[0]["rooms"]["start"],
        )

    def test_executable_rich_description_html_is_rejected(self):
        story, checks, inventory = valid_package()
        story["rooms"]["start"]["description_html"] = "<script>alert(1)</script>"
        with self.assertRaisesRegex(
            StoryValidationError,
            "unsupported executable HTML element",
        ):
            validate_package_data(story, checks, inventory)

    def test_unknown_fields_are_rejected(self):
        story, checks, inventory = valid_package()
        story["rooms"]["start"]["exits"] = {}
        with self.assertRaisesRegex(
            StoryValidationError,
            r"story\.rooms\.start: unknown field 'exits'",
        ):
            validate_package_data(
                story,
                checks,
                inventory,
            )

    def test_item_room_reference_is_checked(self):
        story, checks, inventory = valid_package()
        inventory["room_items"]["missing"] = ["key"]
        with self.assertRaisesRegex(
            StoryValidationError,
            r"inventory\.room_items\.missing: unknown room",
        ):
            validate_package_data(
                story,
                checks,
                inventory,
            )
