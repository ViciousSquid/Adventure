from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import Any, Mapping

from story.model import Story

from .converter import LegacyConverter
from .legacy import read_legacy_zip
from .package import PackageLoader, PackageWriter


class WorldRepository:
    """Application boundary for canonical worlds and legacy source packages."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.canonical = PackageLoader(self.root)
        self.converter = LegacyConverter()

    def list_stories(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for path in sorted(self.root.glob("*.zip")):
            if not path.is_file() or not path.name.endswith(".canonical.zip"):
                continue
            logical = path.name[: -len(".canonical.zip")]
            result[logical] = str(path)

        for path in sorted(self.root.glob("*.zip")):
            if not path.is_file() or path.name.endswith(".canonical.zip"):
                continue
            try:
                with zipfile.ZipFile(path, "r") as archive:
                    if "story.json" not in archive.namelist():
                        continue
            except (OSError, zipfile.BadZipFile):
                continue
            result.setdefault(path.stem, str(path))
        return result

    def load(self, story_name: str) -> Story:
        canonical = self.root / f"{story_name}.canonical.zip"
        if canonical.exists():
            return self.canonical.load_path(canonical)

        legacy = self.root / f"{story_name}.zip"
        if not legacy.exists():
            raise FileNotFoundError(f"world {story_name!r} does not exist")

        converted = self.converter.convert_to_world(legacy)
        return Story.from_package(
            converted.story,
            converted.skill_checks,
            converted.inventory,
        )

    def source_format(self, story_name: str) -> str:
        canonical = self.root / f"{story_name}.canonical.zip"
        if canonical.exists():
            return "canonical"
        legacy = self.root / f"{story_name}.zip"
        if legacy.exists():
            return "legacy"
        raise FileNotFoundError(story_name)

    def read_asset(self, story_name: str, asset_name: str) -> bytes:
        canonical = self.root / f"{story_name}.canonical.zip"
        if canonical.exists():
            return self.canonical.read_asset_path(canonical, asset_name)

        legacy = self.root / f"{story_name}.zip"
        if not legacy.exists():
            raise FileNotFoundError(story_name)

        _, assets = read_legacy_zip(legacy)
        candidates = [asset_name]
        if asset_name.startswith("assets/"):
            candidates.append(asset_name[7:])
        for candidate in candidates:
            if candidate in assets:
                return assets[candidate]
        raise FileNotFoundError(asset_name)

    def read_text_asset(self, story_name: str, asset_name: str) -> str | None:
        try:
            return self.read_asset(story_name, asset_name).decode("utf-8")
        except FileNotFoundError:
            return None

    def package_members(self, story_name: str) -> list[str]:
        canonical = self.root / f"{story_name}.canonical.zip"
        if canonical.exists():
            with zipfile.ZipFile(canonical, "r") as archive:
                return archive.namelist()

        legacy = self.root / f"{story_name}.zip"
        if not legacy.exists():
            raise FileNotFoundError(story_name)
        with zipfile.ZipFile(legacy, "r") as archive:
            return archive.namelist()

    def save(
        self,
        story_data: Mapping[str, Any],
        skill_checks_data: Mapping[str, Any],
        inventory_data: Mapping[str, Any],
        assets: Mapping[str, bytes] | None = None,
        preserve_from: str | None = None,
    ) -> Path:
        name = str(story_data.get("name", "")).strip()
        if not name:
            raise ValueError("story.name is required")

        merged_assets = self._preserved_assets(preserve_from) if preserve_from else {}
        for asset_name, payload in (assets or {}).items():
            merged_assets[asset_name] = payload

        destination = self.root / f"{_safe_filename(name)}.canonical.zip"
        PackageWriter.write(
            destination,
            story_data,
            skill_checks_data,
            inventory_data,
            merged_assets,
        )
        self.canonical.invalidate()
        return destination

    def _preserved_assets(self, story_name: str) -> dict[str, bytes]:
        canonical = self.root / f"{story_name}.canonical.zip"
        if canonical.exists():
            with zipfile.ZipFile(canonical, "r") as archive:
                return {
                    name: archive.read(name)
                    for name in archive.namelist()
                    if name.startswith("assets/") and not name.endswith("/")
                }

        legacy = self.root / f"{story_name}.zip"
        if legacy.exists():
            _, assets = read_legacy_zip(legacy)
            return {
                (
                    name if name.startswith("assets/")
                    else f"assets/{name}"
                ): payload
                for name, payload in assets.items()
            }

        raise FileNotFoundError(story_name)


def _safe_filename(value: str) -> str:
    cleaned = "".join(
        char if char.isalnum() or char in "._-" else "_"
        for char in value
    )
    cleaned = cleaned.strip("._")
    if not cleaned:
        raise ValueError("world name does not produce a valid filename")
    return cleaned
