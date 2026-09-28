from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from story.validator import DICE_EXPRESSION, validate_package_data

from .legacy import read_legacy_zip
from .package import PackageLoader, PackageWriter


class ConversionError(ValueError):
    pass


@dataclass
class ConversionReport:
    source: str
    source_sha256: str
    output: str | None = None
    output_sha256: str | None = None
    result: str = "failed"
    counts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    discarded: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "source_sha256": self.source_sha256,
            "output": self.output,
            "output_sha256": self.output_sha256,
            "result": self.result,
            "counts": dict(self.counts),
            "warnings": list(self.warnings),
            "discarded": list(self.discarded),
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class ConvertedWorld:
    story: dict[str, Any]
    skill_checks: dict[str, Any]
    inventory: dict[str, Any]
    assets: dict[str, bytes]
    report: ConversionReport


class LegacyConverter:
    """Deterministic, auditable converter from the historical room schema."""

    def convert_to_world(
        self,
        source: str | Path,
        *,
        allow_lossy: bool = False,
    ) -> ConvertedWorld:
        source_path = Path(source)
        source_bytes = source_path.read_bytes()
        report = ConversionReport(
            source=str(source_path),
            source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        )

        try:
            legacy, legacy_assets = read_legacy_zip(source_path)
            story, checks, inventory, assets = self._convert_data(
                legacy,
                legacy_assets,
                report,
                allow_lossy=allow_lossy,
            )
            validate_package_data(story, checks, inventory)
            report.result = "success"
            return ConvertedWorld(
                story,
                checks,
                inventory,
                assets,
                report,
            )
        except Exception as exc:
            report.errors.append(str(exc))
            raise

    def convert_file(
        self,
        source: str | Path,
        destination: str | Path | None = None,
        *,
        allow_lossy: bool = False,
        force: bool = False,
    ) -> ConversionReport:
        source_path = Path(source)
        destination_path = (
            Path(destination)
            if destination is not None
            else source_path.with_name(
                f"{source_path.stem}.canonical.zip"
            )
        )

        if (
            source_path.resolve() == destination_path.resolve()
        ):
            raise ValueError("source and destination must be different files")

        if destination_path.exists() and not force:
            raise FileExistsError(
                f"conversion output already exists: {destination_path}; "
                "use force=True to replace it"
            )

        converted = self.convert_to_world(
            source_path,
            allow_lossy=allow_lossy,
        )
        payload = PackageWriter.build_zip(
            converted.story,
            converted.skill_checks,
            converted.inventory,
            converted.assets,
        )

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{destination_path.name}.",
            suffix=".tmp",
            dir=destination_path.parent,
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())

            # Validate the complete archive that is about to be finalized.
            PackageLoader(destination_path.parent).load_path(temp_name)

            with open(temp_name, "rb") as handle:
                final_sha = hashlib.sha256(handle.read()).hexdigest()

            os.replace(temp_name, destination_path)
        except Exception as exc:
            converted.report.errors.append(str(exc))
            raise
        finally:
            Path(temp_name).unlink(missing_ok=True)

        converted.report.output = str(destination_path)
        converted.report.output_sha256 = final_sha
        converted.report.result = "success"
        return converted.report

    def _convert_data(
        self,
        legacy: dict[str, Any],
        legacy_assets: dict[str, bytes],
        report: ConversionReport,
        *,
        allow_lossy: bool,
    ) -> tuple[
        dict[str, Any],
        dict[str, Any],
        dict[str, Any],
        dict[str, bytes],
    ]:
        self._check_unknown(
            legacy,
            {
                "name",
                "title",
                "start_room",
                "start",
                "rooms",
                "button_color",
                "metadata",
                "schema_version",
            },
            "story.json",
            report,
            allow_lossy,
        )

        name = legacy.get("name", legacy.get("title"))
        start_room = legacy.get("start_room", legacy.get("start"))
        rooms = legacy.get("rooms")

        if not isinstance(name, str) or not name.strip():
            raise ConversionError(
                "legacy story: missing non-empty name/title"
            )
        if not isinstance(start_room, str):
            raise ConversionError(
                "legacy story: missing start_room/start"
            )
        if not isinstance(rooms, dict) or not rooms:
            raise ConversionError(
                "legacy story: rooms must be a non-empty object"
            )

        story = {
            "schema_version": 3,
            "name": name,
            "start_room": start_room,
            "rooms": {},
            "connections": {},
            "revisits": {},
            "metadata": dict(legacy.get("metadata") or {}),
        }
        if "button_color" in legacy:
            story["metadata"]["button_color"] = legacy["button_color"]

        checks: dict[str, Any] = {
            "schema_version": 1,
            "skill_checks": {},
        }
        item_values: set[str] = set()
        room_items: dict[str, list[str]] = {}
        room_requirements: dict[str, str] = {}
        connection_ids: set[str] = set()

        for room_id, room in rooms.items():
            room_path = f"rooms.{room_id}"
            if not isinstance(room, dict):
                raise ConversionError(f"{room_path}: must be an object")

            self._check_unknown(
                room,
                {
                    "description",
                    "exits",
                    "image",
                    "show_map",
                    "message",
                    "name",
                    "items",
                    "item_needed",
                    "revisits",
                    "revisit_content",
                    "revisit_count",
                    "show_all_revisits",
                    "skill_check",
                },
                room_path,
                report,
                allow_lossy,
            )

            canonical_room = {
                key: room[key]
                for key in (
                    "description",
                    "image",
                    "show_map",
                    "message",
                    "name",
                )
                if key in room
            }
            if not isinstance(
                canonical_room.get("description"),
                str,
            ):
                raise ConversionError(
                    f"{room_path}.description: must be a string"
                )

            if canonical_room.get("image"):
                canonical_room["image"] = self._canonical_asset_name(
                    canonical_room["image"]
                )

            if "skill_check" in room:
                skill_id = f"skill__room__{room_id}"
                if skill_id in checks["skill_checks"]:
                    raise ConversionError(
                        f"{room_path}.skill_check: duplicate generated skill check id"
                    )
                canonical_room["skill_check"] = skill_id
                checks["skill_checks"][skill_id] = self._convert_skill_check(
                    room["skill_check"],
                    f"{room_path}.skill_check",
                    report,
                    allow_lossy,
                )

            story["rooms"][room_id] = canonical_room

            raw_items = room.get("items", [])
            if raw_items is None:
                raw_items = []
            if (
                not isinstance(raw_items, list)
                or any(not isinstance(item, str) for item in raw_items)
            ):
                raise ConversionError(
                    f"{room_path}.items: must be a list of strings"
                )
            if raw_items:
                room_items[room_id] = list(dict.fromkeys(raw_items))
                item_values.update(raw_items)

            required = room.get("item_needed")
            if required:
                if not isinstance(required, str):
                    raise ConversionError(
                        f"{room_path}.item_needed: must be a string"
                    )
                room_requirements[room_id] = required
                item_values.add(required)

            raw_revisits = room.get("revisits", [])
            legacy_revisit_present = (
                "revisit_content" in room or "revisit_count" in room
            )
            if raw_revisits or legacy_revisit_present:
                if raw_revisits and not isinstance(raw_revisits, list):
                    raise ConversionError(
                        f"{room_path}.revisits: must be a list"
                    )
                story["revisits"][room_id] = {
                    "show_all": bool(
                        room.get("show_all_revisits", False)
                    ),
                    "entries": [],
                }
                for index, revisit in enumerate(raw_revisits or []):
                    entry_path = (
                        f"{room_path}.revisits[{index}]"
                    )
                    if not isinstance(revisit, dict):
                        raise ConversionError(
                            f"{entry_path}: must be an object"
                        )
                    self._check_unknown(
                        revisit,
                        {"count", "content"},
                        entry_path,
                        report,
                        allow_lossy,
                    )
                    count = revisit.get("count", 0)
                    content = revisit.get("content", "")
                    if not isinstance(count, int) or count < 0:
                        raise ConversionError(
                            f"{entry_path}.count: invalid count"
                        )
                    if not isinstance(content, str):
                        raise ConversionError(
                            f"{entry_path}.content: must be a string"
                        )
                    story["revisits"][room_id]["entries"].append(
                        {"count": count, "content": content}
                    )

                if legacy_revisit_present:
                    count = room.get("revisit_count", 0)
                    content = room.get("revisit_content", "")
                    if not isinstance(count, int) or count < 0:
                        raise ConversionError(
                            f"{room_path}.revisit_count: must be a non-negative integer"
                        )
                    if not isinstance(content, str):
                        raise ConversionError(
                            f"{room_path}.revisit_content: must be a string"
                        )
                    story["revisits"][room_id]["entries"].append(
                        {"count": count, "content": content}
                    )

            exits = room.get("exits", {})
            if not isinstance(exits, dict):
                raise ConversionError(
                    f"{room_path}.exits: must be an object"
                )

            for action_id, target in exits.items():
                connection_id = self._unique_connection_id(
                    room_id,
                    str(action_id),
                    connection_ids,
                )
                if not target:
                    report.discarded.append(
                        f"{room_path}.exits.{action_id}: inactive/null exit"
                    )
                    continue

                connection: dict[str, Any] = {
                    "from": room_id,
                    "to": None,
                    "label": str(action_id),
                }

                if isinstance(target, str):
                    connection["to"] = target
                elif isinstance(target, dict):
                    self._check_unknown(
                        target,
                        {"skill_check", "requires_item", "to", "room"},
                        f"{room_path}.exits.{action_id}",
                        report,
                        allow_lossy,
                    )
                    destination = target.get("to", target.get("room"))
                    if isinstance(target.get("to"), str) and isinstance(target.get("room"), str):
                        if target["to"] != target["room"]:
                            raise ConversionError(
                                f"{room_path}.exits.{action_id}: "
                                "conflicting 'to' and legacy 'room' destinations"
                            )
                    if isinstance(destination, str):
                        connection["to"] = destination

                    required_item = target.get("requires_item")
                    if required_item:
                        if not isinstance(required_item, str):
                            raise ConversionError(
                                f"{room_path}.exits.{action_id}.requires_item: "
                                "must be a string"
                            )
                        connection["requires_item"] = required_item
                        item_values.add(required_item)

                    if "skill_check" in target:
                        skill_id = f"skill__{connection_id}"
                        connection["skill_check"] = skill_id
                        checks["skill_checks"][skill_id] = (
                            self._convert_skill_check(
                                target["skill_check"],
                                f"{room_path}.exits.{action_id}.skill_check",
                                report,
                                allow_lossy,
                            )
                        )
                else:
                    raise ConversionError(
                        f"{room_path}.exits.{action_id}: unsupported target"
                    )

                if (
                    connection["to"] is None
                    and not connection.get("skill_check")
                ):
                    raise ConversionError(
                        f"{room_path}.exits.{action_id}: missing destination"
                    )

                # Canonical connections always carry a fallback destination;
                # skill-check branches may override it during execution.
                if connection["to"] is None:
                    connection["to"] = room_id

                story["connections"][connection_id] = connection

        inventory = {
            "schema_version": 1,
            "items": {
                item: {"name": item}
                for item in sorted(item_values)
            },
            "room_items": room_items,
            "room_requirements": room_requirements,
        }

        assets: dict[str, bytes] = {}
        for name, payload in legacy_assets.items():
            if name == "story.json":
                continue
            canonical_name = self._canonical_asset_name(name)
            assets[canonical_name] = payload

        report.counts = {
            "rooms": len(story["rooms"]),
            "connections": len(story["connections"]),
            "skill_checks": len(checks["skill_checks"]),
            "items": len(inventory["items"]),
            "revisits": sum(
                len(value.get("entries", []))
                for value in story["revisits"].values()
            ),
            "assets": len(assets),
        }
        return story, checks, inventory, assets

    def _convert_skill_check(
        self,
        raw: Any,
        path: str,
        report: ConversionReport,
        allow_lossy: bool,
    ) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise ConversionError(f"{path}: must be an object")

        self._check_unknown(
            raw,
            {
                "description",
                "dice_type",
                "dice_notation",
                "target",
                "success",
                "failure",
            },
            path,
            report,
            allow_lossy,
        )

        expression = raw.get(
            "dice_type",
            raw.get("dice_notation", "1d20"),
        )
        if (
            not isinstance(expression, str)
            or not DICE_EXPRESSION.fullmatch(expression)
        ):
            raise ConversionError(
                f"{path}.dice_type: invalid dice expression {expression!r}"
            )

        target = raw.get("target", 10)
        if isinstance(target, dict):
            target = target.get(
                "value",
                target.get("target", 10),
            )
        if not isinstance(target, int):
            raise ConversionError(
                f"{path}.target: must be an integer"
            )

        result: dict[str, Any] = {
            "dice_type": expression,
            "target": target,
        }
        if "description" in raw:
            if not isinstance(raw["description"], str):
                raise ConversionError(
                    f"{path}.description: must be a string"
                )
            result["description"] = raw["description"]

        for branch in ("success", "failure"):
            outcome = raw.get(branch, {})
            if not isinstance(outcome, dict):
                raise ConversionError(
                    f"{path}.{branch}: must be an object"
                )
            self._check_unknown(
                outcome,
                {"description", "room", "to"},
                f"{path}.{branch}",
                report,
                allow_lossy,
            )
            branch_result = {
                "description": outcome.get("description", ""),
                "to": outcome.get(
                    "to",
                    outcome.get("room"),
                ),
            }
            if not isinstance(
                branch_result["description"],
                str,
            ):
                raise ConversionError(
                    f"{path}.{branch}.description: must be a string"
                )
            result[branch] = branch_result

        return result

    @staticmethod
    def _unique_connection_id(
        room_id: str,
        action_id: str,
        existing: set[str],
    ) -> str:
        base = (
            f"{room_id}__{action_id}"
            .replace("/", "_")
            .replace("\\", "_")
        )
        candidate = base
        if candidate in existing:
            digest = hashlib.sha256(
                f"{room_id}\0{action_id}".encode("utf-8")
            ).hexdigest()[:8]
            candidate = f"{base}__{digest}"
        if candidate in existing:
            raise ConversionError(
                f"deterministic connection ID collision for "
                f"{room_id!r}/{action_id!r}"
            )
        existing.add(candidate)
        return candidate

    @staticmethod
    def _canonical_asset_name(name: str) -> str:
        value = name.replace("\\", "/").lstrip("/")
        parts = [
            part for part in value.split("/")
            if part not in ("", ".")
        ]
        if any(part == ".." for part in parts):
            raise ConversionError(
                f"unsafe legacy asset path {name!r}"
            )
        if not parts:
            raise ConversionError(
                f"empty legacy asset path {name!r}"
            )
        return "assets/" + "/".join(parts)

    @staticmethod
    def _check_unknown(
        data: dict[str, Any],
        allowed: set[str],
        path: str,
        report: ConversionReport,
        allow_lossy: bool,
    ) -> None:
        unknown = sorted(set(data) - allowed)
        if not unknown:
            return
        messages = [
            f"{path}.{key}"
            for key in unknown
        ]
        report.discarded.extend(messages)
        if not allow_lossy:
            raise ConversionError(
                "lossy conversion refused; unsupported legacy fields: "
                + ", ".join(messages)
            )


def write_conversion_report(
    report: ConversionReport,
    path: str | Path,
) -> None:
    Path(path).write_text(
        __import__("json").dumps(
            report.to_dict(),
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )


def write_human_report(
    report: ConversionReport,
    path: str | Path,
) -> None:
    lines = [
        "Adventure world conversion report",
        "",
        f"Source: {report.source}",
        f"Source SHA-256: {report.source_sha256}",
        f"Output: {report.output or '(none)'}",
        f"Output SHA-256: {report.output_sha256 or '(none)'}",
        f"Result: {report.result}",
        "",
        "Counts:",
    ]
    lines.extend(
        f"  {key}: {value}"
        for key, value in sorted(report.counts.items())
    )
    lines.append("")
    lines.append("Warnings:")
    if report.warnings:
        lines.extend(f"  - {item}" for item in report.warnings)
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("Discarded:")
    if report.discarded:
        lines.extend(f"  - {item}" for item in report.discarded)
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("Errors:")
    if report.errors:
        lines.extend(f"  - {item}" for item in report.errors)
    else:
        lines.append("  (none)")

    Path(path).write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
