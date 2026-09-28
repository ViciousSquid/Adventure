from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class Story:
    """Immutable canonical world program consumed by the narrative VM."""

    data: Mapping[str, Any]
    skill_checks: Mapping[str, Any]
    inventory: Mapping[str, Any]

    @classmethod
    def from_package(
        cls,
        story_data: Mapping[str, Any],
        skill_checks: Mapping[str, Any],
        inventory: Mapping[str, Any],
    ) -> "Story":
        return cls(
            _freeze(dict(story_data)),
            _freeze(dict(skill_checks)),
            _freeze(dict(inventory)),
        )

    @property
    def name(self) -> str:
        return self.data["name"]

    @property
    def start_room(self) -> str:
        return self.data["start_room"]

    @property
    def rooms(self) -> Mapping[str, Any]:
        return self.data["rooms"]

    @property
    def connections(self) -> Mapping[str, Any]:
        return self.data.get("connections", {})

    @property
    def revisits(self) -> Mapping[str, Any]:
        return self.data.get("revisits", {})

    @property
    def metadata(self) -> Mapping[str, Any]:
        return self.data.get("metadata", {})

    @property
    def items(self) -> Mapping[str, Any]:
        return self.inventory.get("items", {})

    @property
    def room_items(self) -> Mapping[str, Any]:
        return self.inventory.get("room_items", {})

    @property
    def room_requirements(self) -> Mapping[str, Any]:
        return self.inventory.get("room_requirements", {})

    def room(self, room_id: str) -> Mapping[str, Any]:
        return self.rooms[room_id]

    def connection(self, connection_id: str) -> Mapping[str, Any]:
        return self.connections[connection_id]

    def skill_check(self, skill_check_id: str) -> Mapping[str, Any]:
        return self.skill_checks["skill_checks"][skill_check_id]

    def item(self, item_id: str) -> Mapping[str, Any]:
        return self.items[item_id]

    def to_dict(self) -> dict[str, Any]:
        return {
            "story": _thaw(self.data),
            "skill_checks": _thaw(self.skill_checks),
            "inventory": _thaw(self.inventory),
        }

    def to_legacy_dict(self) -> dict[str, Any]:
        """Materialize the old room-centric form for legacy exporters only."""
        data = _thaw(self.data)
        legacy = {
            "name": data["name"],
            "start_room": data["start_room"],
            "rooms": {},
        }
        metadata = data.get("metadata", {})
        if "button_color" in metadata:
            legacy["button_color"] = metadata["button_color"]

        room_items = _thaw(self.inventory.get("room_items", {}))
        room_requirements = _thaw(self.inventory.get("room_requirements", {}))
        revisits = _thaw(data.get("revisits", {}))
        connections = _thaw(data.get("connections", {}))
        checks = _thaw(self.skill_checks.get("skill_checks", {}))

        for room_id, room in data["rooms"].items():
            result = {
                key: room[key]
                for key in ("description", "image", "show_map", "message", "name")
                if key in room
            }
            exits: dict[str, Any] = {}
            for connection in connections.values():
                if connection.get("from") != room_id:
                    continue
                action_id = connection.get("label") or connection.get("id") or ""
                target = connection.get("to")
                if connection.get("skill_check"):
                    check = checks[connection["skill_check"]]
                    legacy_check = {
                        key: value
                        for key, value in check.items()
                        if key in ("description", "dice_type", "target")
                    }
                    legacy_check["success"] = {
                        "description": check.get("success", {}).get("description", ""),
                        "room": check.get("success", {}).get("to"),
                    }
                    legacy_check["failure"] = {
                        "description": check.get("failure", {}).get("description", ""),
                        "room": check.get("failure", {}).get("to"),
                    }
                    target_data: Any = {"skill_check": legacy_check}
                    if connection.get("requires_item"):
                        target_data["requires_item"] = connection["requires_item"]
                    exits[action_id] = target_data
                else:
                    exits[action_id] = target
            result["exits"] = exits
            if room.get("skill_check"):
                check = checks[room["skill_check"]]
                legacy_check = {
                    key: value
                    for key, value in check.items()
                    if key in ("description", "dice_type", "target")
                }
                legacy_check["success"] = {
                    "description": check.get("success", {}).get("description", ""),
                    "room": check.get("success", {}).get("to"),
                }
                legacy_check["failure"] = {
                    "description": check.get("failure", {}).get("description", ""),
                    "room": check.get("failure", {}).get("to"),
                }
                result["skill_check"] = legacy_check
            if room_id in room_items:
                result["items"] = list(room_items[room_id])
            if room_id in room_requirements:
                result["item_needed"] = room_requirements[room_id]
            if room_id in revisits:
                revisit_data = revisits[room_id]
                result["show_all_revisits"] = bool(revisit_data.get("show_all", False))
                result["revisits"] = list(revisit_data.get("entries", []))
            legacy["rooms"][room_id] = result

        return legacy
