import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from storage.converter import (
    ConversionError,
    LegacyConverter,
)
from storage.repository import WorldRepository


class ConverterTests(unittest.TestCase):
    def write_legacy(self, path):
        story = {
            "name": "Legacy",
            "start_room": "hall",
            "button_color": "#8844aa",
            "rooms": {
                "hall": {
                    "description": "A hall",
                    "image": "hall.jpg",
                    "items": ["key"],
                    "exits": {
                        "cellar": "cellar",
                        "door": {
                            "skill_check": {
                                "description": "The old check text.",
                                "dice_type": "1d20",
                                "target": 10,
                                "success": {
                                    "description": "Success",
                                    "room": "cellar",
                                },
                                "failure": {
                                    "description": "Failure",
                                    "room": "hall",
                                },
                            },
                            "requires_item": "key",
                        },
                    },
                    "revisits": [
                        {"count": 1, "content": "You remember this place."}
                    ],
                    "show_all_revisits": False,
                },
                "cellar": {
                    "description": "A cellar",
                    "exits": {"up": "hall"},
                },
            },
        }
        with ZipFile(path, "w") as archive:
            archive.writestr(
                "story.json",
                json.dumps(story).encode("utf-8"),
            )
            archive.writestr("hall.jpg", b"jpeg")
            archive.writestr("summary.txt", b"A summary")

    def test_conversion_is_non_destructive_and_deterministic(self):
        converter = LegacyConverter()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Legacy.zip"
            self.write_legacy(source)
            original = source.read_bytes()
            source_sha = hashlib.sha256(original).hexdigest()

            first = converter.convert_file(source)
            output = Path(first.output)
            self.assertTrue(output.exists())
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(first.source_sha256, source_sha)

            payload_one = output.read_bytes()
            output.unlink()
            second = converter.convert_file(source)
            payload_two = Path(second.output).read_bytes()
            self.assertEqual(
                payload_one,
                payload_two,
                "same legacy source should produce stable canonical bytes",
            )

    def test_conversion_splits_domains_and_preserves_assets(self):
        converter = LegacyConverter()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Legacy.zip"
            self.write_legacy(source)
            converted = converter.convert_to_world(source)

            self.assertEqual(
                set(converted.story["rooms"]["hall"]),
                {"description", "image"},
            )
            self.assertIn("hall__door", converted.story["connections"])
            check = converted.skill_checks["skill_checks"]["skill__hall__door"]
            self.assertEqual(check["description"], "The old check text.")
            self.assertEqual(
                converted.inventory["room_items"]["hall"],
                ["key"],
            )
            self.assertEqual(
                converted.inventory["room_requirements"],
                {},
            )
            self.assertEqual(
                converted.story["metadata"]["button_color"],
                "#8844aa",
            )
            self.assertEqual(
                converted.assets["assets/hall.jpg"],
                b"jpeg",
            )
            self.assertEqual(
                converted.assets["assets/summary.txt"],
                b"A summary",
            )

    def test_legacy_revisit_fields_are_converted(self):
        converter = LegacyConverter()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "LegacyRevisit.zip"
            story = {
                "name": "LegacyRevisit",
                "start_room": "prologue",
                "rooms": {
                    "prologue": {
                        "description": "A prologue",
                        "revisit_content": "You have been here before.",
                        "revisit_count": 2,
                        "exits": {},
                    },
                },
            }
            with ZipFile(source, "w") as archive:
                archive.writestr("story.json", json.dumps(story))

            converted = converter.convert_to_world(source)

            self.assertEqual(
                converted.story["revisits"]["prologue"],
                {
                    "show_all": False,
                    "entries": [
                        {
                            "count": 2,
                            "content": "You have been here before.",
                        }
                    ],
                },
            )

    def test_unknown_fields_fail_by_default(self):
        converter = LegacyConverter()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Legacy.zip"
            self.write_legacy(source)
            with ZipFile(source, "r") as archive:
                story = json.loads(archive.read("story.json"))
            story["rooms"]["hall"]["mysterious_field"] = True
            source.unlink()
            with ZipFile(source, "w") as archive:
                archive.writestr("story.json", json.dumps(story))

            with self.assertRaises(ConversionError):
                converter.convert_to_world(source)

    def test_repository_prefers_verified_canonical_world(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Legacy.zip"
            self.write_legacy(source)
            repository = WorldRepository(tmp)
            self.assertEqual(repository.source_format("Legacy"), "legacy")
            canonical = Path(repository.save(
                repository.converter.convert_to_world(source).story,
                repository.converter.convert_to_world(source).skill_checks,
                repository.converter.convert_to_world(source).inventory,
                preserve_from="Legacy",
            ))
            self.assertTrue(canonical.name.endswith(".canonical.zip"))
            self.assertEqual(repository.source_format("Legacy"), "canonical")
            self.assertEqual(repository.load("Legacy").name, "Legacy")
            self.assertIn(
                "assets/hall.jpg",
                repository.package_members("Legacy"),
            )
