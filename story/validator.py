from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from typing import Any

DICE_EXPRESSION = re.compile(r"^\s*\d+d\d+(?:\s*[+-]\s*(?:\d+d\d+|\d+))*\s*$")


class StoryValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(
            "Story validation failed:\n"
            + "\n".join(f"  - {error}" for error in errors)
        )


def normalize_story(data: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise StoryValidationError(["story must be a JSON object"])

    normalized = copy.deepcopy(dict(data))
    if "name" not in normalized and "title" in normalized:
        normalized["name"] = normalized["title"]
    if "start_room" not in normalized and "start" in normalized:
        normalized["start_room"] = normalized["start"]
    normalized.pop("title", None)
    normalized.pop("start", None)
    return normalized


def validate_story_data(data: Mapping[str, Any]) -> dict[str, Any]:
    normalized = normalize_story(data)
    errors: list[str] = []

    name = normalized.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name: must be a non-empty string")

    rooms = normalized.get("rooms")
    if not isinstance(rooms, dict) or not rooms:
        errors.append("rooms: must be a non-empty object")
        return _raise_or_return(normalized, errors)

    start_room = normalized.get("start_room")
    if not isinstance(start_room, str) or start_room not in rooms:
        errors.append(f"start_room: room {start_room!r} does not exist")

    item_names: set[str] = set()

    for room_id, room in rooms.items():
        base = f"rooms.{room_id}"
        if not isinstance(room, dict):
            errors.append(f"{base}: must be an object")
            continue

        if "description" not in room or not isinstance(room.get("description"), str):
            errors.append(f"{base}.description: must be a string")

        exits = room.get("exits", {})
        if not isinstance(exits, dict):
            errors.append(f"{base}.exits: must be an object")
        else:
            for exit_id, target in exits.items():
                path = f"{base}.exits.{exit_id}"
                if target is None:
                    continue
                if isinstance(target, str):
                    if target not in rooms:
                        errors.append(f"{path}: destination {target!r} does not exist")
                    continue
                if not isinstance(target, dict) or "skill_check" not in target:
                    errors.append(f"{path}: must be a destination string or skill_check object")
                    continue
                _validate_skill_check(
                    target["skill_check"], path + ".skill_check", rooms, errors
                )

        items = room.get("items", [])
        if items is not None:
            if not isinstance(items, list) or any(not isinstance(item, str) for item in items):
                errors.append(f"{base}.items: must be a list of strings")
            else:
                item_names.update(items)

        if "revisits" in room:
            revisits = room["revisits"]
            if not isinstance(revisits, list):
                errors.append(f"{base}.revisits: must be a list")
            else:
                for index, revisit in enumerate(revisits):
                    path = f"{base}.revisits[{index}]"
                    if not isinstance(revisit, dict):
                        errors.append(f"{path}: must be an object")
                        continue
                    count = revisit.get("count", 0)
                    if not isinstance(count, int) or count < 0:
                        errors.append(f"{path}.count: must be a non-negative integer")
                    if not isinstance(revisit.get("content", ""), str):
                        errors.append(f"{path}.content: must be a string")

    for room_id, room in rooms.items():
        item_needed = room.get("item_needed") if isinstance(room, dict) else None
        if item_needed and item_needed not in item_names:
            errors.append(
                f"rooms.{room_id}.item_needed: item {item_needed!r} "
                "is not declared in any room's items"
            )

    return _raise_or_return(normalized, errors)


def _validate_skill_check(skill_check: Any, path: str, rooms: dict[str, Any], errors: list[str]) -> None:
    if not isinstance(skill_check, dict):
        errors.append(f"{path}: must be an object")
        return

    if "description" in skill_check and not isinstance(skill_check["description"], str):
        errors.append(f"{path}.description: must be a string")

    dice_type = skill_check.get("dice_type", "1d20")
    if not isinstance(dice_type, str) or not DICE_EXPRESSION.fullmatch(dice_type):
        errors.append(f"{path}.dice_type: invalid dice expression {dice_type!r}")

    target = skill_check.get("target", 10)
    if not isinstance(target, int):
        errors.append(f"{path}.target: must be an integer")

    for branch in ("success", "failure"):
        outcome = skill_check.get(branch, {})
        branch_path = f"{path}.{branch}"
        if not isinstance(outcome, dict):
            errors.append(f"{branch_path}: must be an object")
            continue
        room = outcome.get("room")
        if room is not None and room != "" and room not in rooms:
            errors.append(f"{branch_path}.room: destination {room!r} does not exist")
        if "description" in outcome and not isinstance(outcome.get("description"), str):
            errors.append(f"{branch_path}.description: must be a string")


def _raise_or_return(normalized: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    if errors:
        raise StoryValidationError(errors)
    return normalized
