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
    """Immutable authored story data kept as plain nested data."""

    data: Mapping[str, Any]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Story":
        return cls(_freeze(dict(data)))

    @property
    def name(self) -> str:
        return self.data["name"]

    @property
    def start_room(self) -> str:
        return self.data["start_room"]

    @property
    def rooms(self) -> Mapping[str, Any]:
        return self.data["rooms"]

    def room(self, room_id: str) -> Mapping[str, Any]:
        return self.rooms[room_id]

    def to_dict(self) -> dict[str, Any]:
        return _thaw(self.data)
