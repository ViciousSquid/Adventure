import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from storage.package import PackageLoader, PackageWriter
from story.validator import StoryValidationError


class PackageTests(unittest.TestCase):
    def package_data(self):
        return (
            {
                "schema_version": 3,
                "name": "Package",
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

    def test_canonical_round_trip_and_cache(self):
        story, checks, inventory = self.package_data()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Package.canonical.zip"
            PackageWriter.write(
                path,
                story,
                checks,
                inventory,
                {"assets/readme.txt": b"Hello"},
            )
            loader = PackageLoader(tmp)
            first = loader.load_path(path)
            second = loader.load_path(path)
            self.assertIs(first, second)
            self.assertEqual(first.name, "Package")
            self.assertEqual(
                loader.read_text_asset("Package.canonical", "assets/readme.txt"),
                "Hello",
            )
            with ZipFile(path) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {
                        "story.json",
                        "skill_checks.json",
                        "inventory.json",
                        "assets/readme.txt",
                    },
                )

    def test_missing_canonical_file_is_rejected(self):
        story, checks, inventory = self.package_data()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Package.canonical.zip"
            PackageWriter.write(path, story, checks, inventory)
            payload = path.read_bytes()
            # Rewrite only for this negative fixture; normal PackageWriter is atomic.
            with ZipFile(path, "w") as archive:
                archive.writestr("story.json", payload)
            loader = PackageLoader(tmp)
            with self.assertRaises(ValueError):
                loader.load_path(path)

    def test_invalid_cross_reference_never_enters_cache(self):
        story, checks, inventory = self.package_data()
        story["connections"]["broken"] = {
            "from": "start",
            "to": "missing",
            "label": "broken",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Broken.canonical.zip"
            with self.assertRaises(StoryValidationError):
                PackageWriter.write(path, story, checks, inventory)
            self.assertFalse(path.exists())

    def test_writer_never_leaves_temporary_file_after_success(self):
        story, checks, inventory = self.package_data()
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "Package.canonical.zip"
            PackageWriter.write(destination, story, checks, inventory)
            self.assertEqual(
                list(Path(tmp).glob(".Package.canonical.zip.*.tmp")),
                [],
            )
