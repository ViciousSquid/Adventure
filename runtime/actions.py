from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .dice import DiceResult


@dataclass(frozen=True, slots=True)
class ActionRecord:
    action_id: str
    source_room: str
    resulting_room: str
    effects: tuple[dict[str, Any], ...] = ()
    dice_result: DiceResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "source_room": self.source_room,
            "resulting_room": self.resulting_room,
            "effects": list(self.effects),
            "dice_result": self.dice_result.to_dict() if self.dice_result else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionRecord":
        dice_data = data.get("dice_result")
        dice_result = None
        if dice_data:
            dice_result = DiceResult(
                expression=dice_data.get("expression", dice_data.get("dice_notation", "")),
                individual_rolls=tuple(
                    dice_data.get("individual_rolls", dice_data.get("roll_details", []))
                ),
                modifier=int(dice_data.get("modifier", 0)),
                total=int(dice_data.get("total", dice_data.get("roll_result", 0))),
                target=dice_data.get("target"),
                success=dice_data.get("success"),
            )
        return cls(
            action_id=str(data.get("action_id", "unknown")),
            source_room=str(data.get("source_room", "")),
            resulting_room=str(data.get("resulting_room", data.get("room", ""))),
            effects=tuple(data.get("effects", ())),
            dice_result=dice_result,
        )


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    ok: bool
    room: str
    text: str
    choices: tuple[dict[str, Any], ...] = ()
    effects: tuple[dict[str, Any], ...] = ()
    transition: str | None = None
    dice_results: tuple[DiceResult, ...] = ()
    awaiting_roll: bool = False
    error: str | None = None
    trace: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "room": self.room,
            "text": self.text,
            "choices": list(self.choices),
            "effects": list(self.effects),
            "transition": self.transition,
            "dice_results": [result.to_dict() for result in self.dice_results],
            "awaiting_roll": self.awaiting_roll,
            "error": self.error,
            "trace": list(self.trace),
        }
