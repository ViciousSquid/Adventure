import sys
import tempfile
import types
import unittest
from pathlib import Path

from export.glulx import GlulxExporter
from export.zmachine import ZMachineExporter
from story.model import Story


class ExportTests(unittest.TestCase):
    def test_exporters_consume_canonical_story_model(self):
        story = Story.from_package(
            {
                "schema_version": 3,
                "name": "Export",
                "start_room": "start",
                "rooms": {"start": {"description": "Hello"}},
                "connections": {},
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

        class FakeConverter:
            seen = None

            def __init__(self):
                self.story_data = None

            def compile_to_format(
                self,
                output_path,
                format_type,
                progress=None,
            ):
                FakeConverter.seen = (
                    self.story_data,
                    output_path,
                    format_type,
                )
                Path(output_path).write_text(
                    format_type,
                    encoding="utf-8",
                )
                return True

        sys.modules["__convert_story_to_z8"] = types.SimpleNamespace(
            CYOAConverter=FakeConverter
        )
        try:
            with tempfile.TemporaryDirectory() as tmp:
                z8 = Path(tmp) / "story.z8"
                ulx = Path(tmp) / "story.ulx"
                self.assertTrue(ZMachineExporter().export(story, z8))
                self.assertTrue(GlulxExporter().export(story, ulx))
                self.assertEqual(
                    FakeConverter.seen[0]["name"],
                    "Export",
                )
                self.assertIn(
                    "exits",
                    FakeConverter.seen[0]["rooms"]["start"],
                )
        finally:
            sys.modules.pop("__convert_story_to_z8", None)
