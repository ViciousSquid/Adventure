from __future__ import annotations

import importlib
from pathlib import Path

from story.model import Story


class ZMachineExporter:
    format_name = "z8"

    def export(self, story: Story, output_path: str | Path, progress=None) -> bool:
        converter = importlib.import_module("__convert_story_to_z8").CYOAConverter
        backend = converter()
        backend.story_data = story.to_legacy_dict()
        return backend.compile_to_format(str(output_path), self.format_name, progress)
