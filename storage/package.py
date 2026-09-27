from __future__ import annotations

import io
import json
import os
import zipfile
from pathlib import Path
from threading import RLock
from typing import Mapping

from story.model import Story
from story.validator import validate_story_data


class PackageLoader:
    """Load and validate story packages once, then reuse the Story program."""

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root)
        self._cache: dict[tuple[str, int], Story] = {}
        self._lock = RLock()

    def list_stories(self) -> dict[str, str]:
        return {
            path.stem: str(path)
            for path in sorted(self.root.glob("*.zip"))
            if path.is_file()
        }

    def load(self, story_name: str) -> Story:
        path = self.list_stories().get(story_name)
        if not path:
            raise FileNotFoundError(f"story package {story_name!r} does not exist")
        return self.load_path(path)

    def load_path(self, path: str | os.PathLike[str]) -> Story:
        path_obj = Path(path)
        resolved = str(path_obj.resolve())
        key = (resolved, path_obj.stat().st_mtime_ns)

        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                return cached

            with zipfile.ZipFile(path_obj, "r") as archive:
                try:
                    raw = archive.read("story.json")
                except KeyError as exc:
                    raise ValueError(
                        f"{path_obj.name}: package does not contain story.json"
                    ) from exc

            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"{path_obj.name}: story.json is not valid UTF-8 JSON"
                ) from exc

            story = Story.from_dict(validate_story_data(data))
            self._cache = {
                cache_key: value
                for cache_key, value in self._cache.items()
                if cache_key[0] != resolved
            }
            self._cache[key] = story
            return story

    def invalidate(self, story_name: str | None = None) -> None:
        if story_name is None:
            self._cache.clear()
            return

        path = self.list_stories().get(story_name)
        if not path:
            return
        resolved = str(Path(path).resolve())
        self._cache = {
            key: value for key, value in self._cache.items() if key[0] != resolved
        }

    def read_asset(self, story_name: str, asset_name: str) -> bytes:
        if not asset_name or Path(asset_name).name != asset_name:
            raise ValueError("asset name must be a package-relative filename")
        path = self.list_stories().get(story_name)
        if not path:
            raise FileNotFoundError(story_name)

        with zipfile.ZipFile(path, "r") as archive:
            try:
                return archive.read(asset_name)
            except KeyError as exc:
                raise FileNotFoundError(asset_name) from exc

    def read_text_asset(self, story_name: str, asset_name: str) -> str | None:
        try:
            return self.read_asset(story_name, asset_name).decode("utf-8")
        except FileNotFoundError:
            return None

    def package_members(self, story_name: str) -> list[str]:
        path = self.list_stories().get(story_name)
        if not path:
            raise FileNotFoundError(story_name)
        with zipfile.ZipFile(path, "r") as archive:
            return archive.namelist()


class PackageWriter:
    @staticmethod
    def build_zip(
        story_data: Mapping,
        assets: Mapping[str, bytes] | None = None,
    ) -> bytes:
        canonical = validate_story_data(story_data)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "story.json",
                json.dumps(canonical, indent=2, ensure_ascii=False),
            )
            for name, data in (assets or {}).items():
                if Path(name).name != name:
                    raise ValueError(f"invalid asset filename: {name!r}")
                archive.writestr(name, data)
        return buffer.getvalue()

    @staticmethod
    def write(
        path: str | os.PathLike[str],
        story_data: Mapping,
        assets: Mapping[str, bytes] | None = None,
    ) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(PackageWriter.build_zip(story_data, assets))
