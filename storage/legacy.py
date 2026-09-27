from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any


def read_legacy_zip(path: str | Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    source = Path(path)
    with zipfile.ZipFile(source, "r") as archive:
        try:
            story = json.loads(archive.read("story.json").decode("utf-8"))
        except KeyError as exc:
            raise ValueError(f"{source.name}: legacy package does not contain story.json") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"{source.name}: story.json is not valid UTF-8 JSON") from exc

        assets: dict[str, bytes] = {}
        for info in archive.infolist():
            if info.is_dir() or info.filename == "story.json":
                continue
            assets[info.filename] = archive.read(info.filename)
    if not isinstance(story, dict):
        raise ValueError(f"{source.name}: legacy story.json must contain an object")
    return story, assets
