from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from secrets import randbits
from typing import Any

from .actions import ActionRecord


@dataclass
class GameState:
    story_name: str
    current_room: str
    inventory: list[str] = field(default_factory=list)
    action_history: list[ActionRecord] = field(default_factory=list)
    visit_counts: dict[str, int] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    collected_items: list[str] = field(default_factory=list)
    pending_check: dict[str, Any] | None = None
    random_seed: int = field(default_factory=lambda: randbits(64))
    roll_count: int = 0

    @classmethod
    def new(
        cls,
        story_name: str,
        start_room: str,
        random_seed: int | None = None,
    ) -> "GameState":
        return cls(
            story_name=story_name,
            current_room=start_room,
            visit_counts={start_room: 0},
            random_seed=randbits(64) if random_seed is None else random_seed,
        )

    @property
    def history_rooms(self) -> list[str]:
        return [
            record.resulting_room
            for record in self.action_history
            if record.resulting_room
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 2,
            "story_name": self.story_name,
            "current_room": self.current_room,
            "inventory": list(self.inventory),
            "action_history": [record.to_dict() for record in self.action_history],
            "visit_counts": dict(self.visit_counts),
            "variables": dict(self.variables),
            "collected_items": list(self.collected_items),
            "pending_check": _plain(self.pending_check),
            "random_seed": self.random_seed,
            "roll_count": self.roll_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        story_name = data.get("story_name") or data.get("current_adventure") or data.get("name")
        current_room = data.get("current_room")
        if not story_name:
            raise ValueError("save game does not identify a story")
        if not current_room:
            raise ValueError("save game does not identify a current room")

        raw_history = data.get("action_history", [])
        if raw_history and isinstance(raw_history[0], dict):
            records = [ActionRecord.from_dict(entry) for entry in raw_history]
        else:
            records = [
                ActionRecord(
                    action_id="legacy",
                    source_room="",
                    resulting_room=str(room_id),
                )
                for room_id in raw_history
            ]

        visit_counts = dict(data.get("visit_counts") or {})
        if not visit_counts:
            visit_counts = {}
            for record in records:
                visit_counts[record.resulting_room] = (
                    visit_counts.get(record.resulting_room, 0) + 1
                )
            visit_counts.setdefault(current_room, 0)

        return cls(
            story_name=story_name,
            current_room=current_room,
            inventory=list(data.get("inventory") or []),
            action_history=records,
            visit_counts={str(k): int(v) for k, v in visit_counts.items()},
            variables=dict(data.get("variables") or {}),
            collected_items=list(data.get("collected_items") or []),
            pending_check=data.get("pending_check"),
            random_seed=int(data.get("random_seed", randbits(64))),
            roll_count=int(data.get("roll_count", 0)),
        )


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value
