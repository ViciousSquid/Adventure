from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from typing import Any

DICE_EXPRESSION = re.compile(r"^\s*\d+d\d+(?:\s*[+-]\s*(?:\d+d\d+|\d+))*\s*$")

TOP_LEVEL = {"schema_version", "name", "start_room", "rooms", "connections", "revisits", "metadata"}
ROOM_FIELDS = {
    "description",
    "description_html",
    "image",
    "show_map",
    "message",
    "name",
}
CONNECTION_FIELDS = {"from", "to", "label", "skill_check", "requires_item"}
SKILL_FIELDS = {"dice_type", "target", "description", "success", "failure"}
OUTCOME_FIELDS = {"description", "to"}
INVENTORY_TOP = {"schema_version", "items", "room_items", "room_requirements"}
ITEM_FIELDS = {"name"}


class StoryValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(
            "World validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        )


def validate_package_data(
    story_data: Mapping[str, Any],
    skill_checks_data: Mapping[str, Any],
    inventory_data: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    story = copy.deepcopy(dict(story_data))
    checks = copy.deepcopy(dict(skill_checks_data))
    inventory = copy.deepcopy(dict(inventory_data))
    errors: list[str] = []

    _require_schema(story, "story.schema_version", 3, errors)
    _require_schema(checks, "skill_checks.schema_version", 1, errors)
    _require_schema(inventory, "inventory.schema_version", 1, errors)

    _unknown_fields(story, TOP_LEVEL, "story", errors)
    _unknown_fields(checks, {"schema_version", "skill_checks"}, "skill_checks", errors)
    _unknown_fields(inventory, INVENTORY_TOP, "inventory", errors)

    _validate_story(story, checks, inventory, errors)
    _validate_skill_checks(checks, story, errors)
    _validate_inventory(inventory, story, errors)

    if errors:
        raise StoryValidationError(errors)
    return story, checks, inventory


def _require_schema(data: Mapping[str, Any], path: str, expected: int, errors: list[str]) -> None:
    if data.get("schema_version") != expected:
        errors.append(f"{path}: must be exactly {expected}")


def _unknown_fields(data: Mapping[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    for key in data:
        if key not in allowed:
            errors.append(f"{path}: unknown field {key!r}")


def _validate_story(
    story: dict[str, Any],
    checks: dict[str, Any],
    inventory: dict[str, Any],
    errors: list[str],
) -> None:
    name = story.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("story.name: must be a non-empty string")

    rooms = story.get("rooms")
    if not isinstance(rooms, dict) or not rooms:
        errors.append("story.rooms: must be a non-empty object")
        return

    start = story.get("start_room")
    if not isinstance(start, str) or start not in rooms:
        errors.append(f"story.start_room: room {start!r} does not exist")

    for room_id, room in rooms.items():
        path = f"story.rooms.{room_id}"
        if not isinstance(room, dict):
            errors.append(f"{path}: must be an object")
            continue
        _unknown_fields(room, ROOM_FIELDS, path, errors)
        if not isinstance(room.get("description"), str):
            errors.append(f"{path}.description: must be a string")
        if "description_html" in room:
            if not isinstance(room["description_html"], str):
                errors.append(f"{path}.description_html: must be a string")
            else:
                _validate_rich_text(
                    room["description_html"],
                    f"{path}.description_html",
                    errors,
                )
        if "image" in room and room["image"] is not None and not isinstance(room["image"], str):
            errors.append(f"{path}.image: must be a string or null")
        if "show_map" in room and not isinstance(room["show_map"], bool):
            errors.append(f"{path}.show_map: must be a boolean")
        if "message" in room and not isinstance(room["message"], str):
            errors.append(f"{path}.message: must be a string")
        if "name" in room and not isinstance(room["name"], str):
            errors.append(f"{path}.name: must be a string")

    connections = story.get("connections", {})
    if not isinstance(connections, dict):
        errors.append("story.connections: must be an object")
    else:
        for connection_id, connection in connections.items():
            path = f"story.connections.{connection_id}"
            if not isinstance(connection, dict):
                errors.append(f"{path}: must be an object")
                continue
            _unknown_fields(connection, CONNECTION_FIELDS, path, errors)
            source = connection.get("from")
            target = connection.get("to")
            label = connection.get("label")
            if source not in rooms:
                errors.append(f"{path}.from: room {source!r} does not exist")
            if target not in rooms:
                errors.append(f"{path}.to: room {target!r} does not exist")
            if not isinstance(label, str) or not label:
                errors.append(f"{path}.label: must be a non-empty string")
            if "skill_check" in connection:
                skill_id = connection["skill_check"]
                if not isinstance(skill_id, str) or skill_id not in checks.get("skill_checks", {}):
                    errors.append(f"{path}.skill_check: unknown skill check {skill_id!r}")
            if "requires_item" in connection:
                item_id = connection["requires_item"]
                if not isinstance(item_id, str) or item_id not in inventory.get("items", {}):
                    errors.append(f"{path}.requires_item: unknown item {item_id!r}")

    revisits = story.get("revisits", {})
    if not isinstance(revisits, dict):
        errors.append("story.revisits: must be an object")
    else:
        for room_id, revisit_data in revisits.items():
            path = f"story.revisits.{room_id}"
            if room_id not in rooms:
                errors.append(f"{path}: unknown room {room_id!r}")
                continue
            if not isinstance(revisit_data, dict):
                errors.append(f"{path}: must be an object")
                continue
            if set(revisit_data) - {"show_all", "entries"}:
                for key in set(revisit_data) - {"show_all", "entries"}:
                    errors.append(f"{path}: unknown field {key!r}")
            if not isinstance(revisit_data.get("show_all", False), bool):
                errors.append(f"{path}.show_all: must be a boolean")
            entries = revisit_data.get("entries", [])
            if not isinstance(entries, list):
                errors.append(f"{path}.entries: must be a list")
                continue
            for index, entry in enumerate(entries):
                entry_path = f"{path}.entries[{index}]"
                if not isinstance(entry, dict):
                    errors.append(f"{entry_path}: must be an object")
                    continue
                if set(entry) - {"count", "content"}:
                    for key in set(entry) - {"count", "content"}:
                        errors.append(f"{entry_path}: unknown field {key!r}")
                if not isinstance(entry.get("count"), int) or entry.get("count", -1) < 0:
                    errors.append(f"{entry_path}.count: must be a non-negative integer")
                if not isinstance(entry.get("content"), str):
                    errors.append(f"{entry_path}.content: must be a string")

    metadata = story.get("metadata", {})
    if not isinstance(metadata, dict):
        errors.append("story.metadata: must be an object")


def _validate_rich_text(html: str, path: str, errors: list[str]) -> None:
    lowered = html.lower()
    if "<script" in lowered or "<iframe" in lowered or "<object" in lowered:
        errors.append(f"{path}: unsupported executable HTML element")
    if "javascript:" in lowered or "vbscript:" in lowered:
        errors.append(f"{path}: executable URL is not allowed")
    if re.search(r"\son[a-z]+\s*=", lowered):
        errors.append(f"{path}: inline event handlers are not allowed")
    if "srcdoc=" in lowered:
        errors.append(f"{path}: srcdoc is not allowed")
    if "url(" in lowered:
        errors.append(f"{path}: CSS url() is not allowed")


def _validate_skill_checks(
    data: dict[str, Any],
    story: dict[str, Any],
    errors: list[str],
) -> None:
    checks = data.get("skill_checks")
    if not isinstance(checks, dict):
        errors.append("skill_checks.skill_checks: must be an object")
        return
    rooms = story.get("rooms", {})
    for skill_id, skill in checks.items():
        path = f"skill_checks.skill_checks.{skill_id}"
        if not isinstance(skill, dict):
            errors.append(f"{path}: must be an object")
            continue
        _unknown_fields(skill, SKILL_FIELDS, path, errors)
        dice_type = skill.get("dice_type", "1d20")
        if not isinstance(dice_type, str) or not DICE_EXPRESSION.fullmatch(dice_type):
            errors.append(f"{path}.dice_type: invalid dice expression {dice_type!r}")
        target = skill.get("target", 10)
        if not isinstance(target, int):
            errors.append(f"{path}.target: must be an integer")
        if "description" in skill and not isinstance(skill["description"], str):
            errors.append(f"{path}.description: must be a string")
        for branch in ("success", "failure"):
            outcome = skill.get(branch, {})
            branch_path = f"{path}.{branch}"
            if not isinstance(outcome, dict):
                errors.append(f"{branch_path}: must be an object")
                continue
            _unknown_fields(outcome, OUTCOME_FIELDS, branch_path, errors)
            destination = outcome.get("to")
            if destination is not None and destination != "" and destination not in rooms:
                errors.append(f"{branch_path}.to: destination {destination!r} does not exist")
            if "description" in outcome and not isinstance(outcome["description"], str):
                errors.append(f"{branch_path}.description: must be a string")


def _validate_inventory(
    data: dict[str, Any],
    story: dict[str, Any],
    errors: list[str],
) -> None:
    items = data.get("items")
    if not isinstance(items, dict):
        errors.append("inventory.items: must be an object")
        return

    for item_id, item in items.items():
        path = f"inventory.items.{item_id}"
        if not isinstance(item, dict):
            errors.append(f"{path}: must be an object")
            continue
        _unknown_fields(item, ITEM_FIELDS, path, errors)
        if not isinstance(item.get("name"), str) or not item["name"]:
            errors.append(f"{path}.name: must be a non-empty string")

    rooms = story.get("rooms", {})
    room_items = data.get("room_items", {})
    if not isinstance(room_items, dict):
        errors.append("inventory.room_items: must be an object")
    else:
        for room_id, item_ids in room_items.items():
            path = f"inventory.room_items.{room_id}"
            if room_id not in rooms:
                errors.append(f"{path}: unknown room {room_id!r}")
            if not isinstance(item_ids, list):
                errors.append(f"{path}: must be a list")
                continue
            for index, item_id in enumerate(item_ids):
                if item_id not in items:
                    errors.append(f"{path}[{index}]: unknown item {item_id!r}")

    requirements = data.get("room_requirements", {})
    if not isinstance(requirements, dict):
        errors.append("inventory.room_requirements: must be an object")
    else:
        for room_id, item_id in requirements.items():
            path = f"inventory.room_requirements.{room_id}"
            if room_id not in rooms:
                errors.append(f"{path}: unknown room {room_id!r}")
            if item_id not in items:
                errors.append(f"{path}: unknown item {item_id!r}")
