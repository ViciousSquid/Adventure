import tempfile
import unittest
from pathlib import Path

from storage.package import PackageLoader, PackageWriter


class PackageTests(unittest.TestCase):
    def test_package_round_trip_and_cache(self):
        story = {
            "name": "Package",
            "start_room": "start",
            "rooms": {"start": {"description": "Hello", "exits": {}}},
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Package.zip"
            PackageWriter.write(path, story, {"summary.txt": b"Hello"})
            loader = PackageLoader(tmp)
            first = loader.load("Package")
            second = loader.load("Package")
            self.assertIs(first, second)
            self.assertEqual(first.name, "Package")
            self.assertEqual(loader.read_text_asset("Package", "summary.txt"), "Hello")
