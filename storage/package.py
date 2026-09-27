from __future__ import annotations

import io
import json
import os
import tempfile
import zipfile
from pathlib import Path
from threading import RLock
from typing import Any, Mapping

from story.model import Story
from story.validator import validate_package_data

JSON_FILES = ("story.json", "skill_checks.json", "inventory.json")


class PackageLoader:
    """Load canonical world ZIPs into immutable Story programs."""

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root)
        self._cache: dict[tuple[str, int], Story] = {}
        self._lock = RLock()

    def list_stories(self) -> dict[str, str]:
        result: dict[str, str] = {}
        if not self.root.exists():
            return result
        for path in sorted(self.root.glob("*.zip")):
            if path.is_file() and self._looks_canonical(path):
                result[path.stem] = str(path)
        return result

    def load(self, story_name: str) -> Story:
        path = self.list_stories().get(story_name)
        if not path:
            raise FileNotFoundError(
                f"canonical world {story_name!r} does not exist"
            )
        return self.load_path(path)

    def load_path(self, path: str | os.PathLike[str]) -> Story:
        path_obj = Path(path)
        resolved = str(path_obj.resolve())
        key = (resolved, path_obj.stat().st_mtime_ns)

        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                return cached

            story_data, checks, inventory = _read_json_members(path_obj)
            canonical = validate_package_data(story_data, checks, inventory)
            story = Story.from_package(*canonical)
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
            key: value for key, value in self._cache.items()
            if key[0] != resolved
        }

    def read_asset_path(
        self,
        path: str | os.PathLike[str],
        asset_name: str,
    ) -> bytes:
        safe_name = _safe_member_name(asset_name)
        with zipfile.ZipFile(path, "r") as archive:
            try:
                return archive.read(safe_name)
            except KeyError as exc:
                raise FileNotFoundError(asset_name) from exc

    def read_asset(self, story_name: str, asset_name: str) -> bytes:
        path = self.list_stories().get(story_name)
        if not path:
            raise FileNotFoundError(story_name)
        return self.read_asset_path(path, asset_name)

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

    @staticmethod
    def _looks_canonical(path: Path) -> bool:
        try:
            with zipfile.ZipFile(path, "r") as archive:
                names = set(archive.namelist())
        except (OSError, zipfile.BadZipFile):
            return False
        return set(JSON_FILES).issubset(names)


class PackageWriter:
    @staticmethod
    def build_zip(
        story_data: Mapping[str, Any],
        skill_checks_data: Mapping[str, Any],
        inventory_data: Mapping[str, Any],
        assets: Mapping[str, bytes] | None = None,
    ) -> bytes:
        canonical = validate_package_data(
            story_data,
            skill_checks_data,
            inventory_data,
        )
        buffer = io.BytesIO()
        with zipfile.ZipFile(
            buffer,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            for name, payload in zip(JSON_FILES, canonical):
                archive.writestr(
                    name,
                    json.dumps(
                        payload,
                        indent=2,
                        ensure_ascii=False,
                    ) + "\n",
                )
            for name, data in (assets or {}).items():
                archive.writestr(_safe_asset_name(name), data)
        return buffer.getvalue()

    @staticmethod
    def write(
        path: str | os.PathLike[str],
        story_data: Mapping[str, Any],
        skill_checks_data: Mapping[str, Any],
        inventory_data: Mapping[str, Any],
        assets: Mapping[str, bytes] | None = None,
    ) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = PackageWriter.build_zip(
            story_data,
            skill_checks_data,
            inventory_data,
            assets,
        )
        fd, temporary = tempfile.mkstemp(
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            PackageLoader(destination.parent).load_path(temporary)
            os.replace(temporary, destination)
        finally:
            Path(temporary).unlink(missing_ok=True)


def _safe_member_name(name: str) -> str:
    path = Path(name)
    if not name or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe package member: {name!r}")
    return name.replace("\\", "/")


def _safe_asset_name(name: str) -> str:
    normalized = _safe_member_name(name)
    if normalized in JSON_FILES:
        raise ValueError(
            f"asset collides with canonical data file: {name!r}"
        )
    if not normalized.startswith("assets/"):
        normalized = f"assets/{normalized.lstrip('/')}"
    return normalized


def _read_json_members(
    path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    with zipfile.ZipFile(path, "r") as archive:
        payloads: list[dict[str, Any]] = []
        for member in JSON_FILES:
            try:
                raw = archive.read(member)
                payloads.append(json.loads(raw.decode("utf-8")))
            except KeyError as exc:
                raise ValueError(
                    f"{path.name}: package does not contain {member}"
                ) from exc
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"{path.name}: {member} is not valid UTF-8 JSON"
                ) from exc
    return payloads[0], payloads[1], payloads[2]
