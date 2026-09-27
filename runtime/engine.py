from __future__ import annotations

import hashlib
import random
from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from story.model import Story

from .actions import ActionRecord, ExecutionResult
from .dice import DiceEngine, DiceResult
from .state import GameState


class AdventureEngine:
    """The narrative VM: Story is the program, GameState is memory."""

    def __init__(
        self,
        story: Story,
        rng: random.Random | None = None,
        trace: bool = False,
        story_id: str | None = None,
    ):
        self.story = story
        self.story_id = story_id or story.name
        self._seed_rng = rng or random.SystemRandom()
        self.trace_enabled = trace

    def new_game(self) -> GameState:
        return GameState.new(
            self.story_id,
            self.story.start_room,
            random_seed=self._seed_rng.getrandbits(64),
        )

    def execute(self, state: GameState, action: str) -> ExecutionResult:
        return self.step(state, action)

    def step(self, state: GameState, action: str) -> ExecutionResult:
        self._validate_state(state)

        if action == "roll":
            if not state.pending_check:
                return self._result(
                    state,
                    ok=False,
                    text="There is no pending skill check.",
                    error="no_pending_check",
                )
            return self._resolve_pending_check(state)

        return self._execute_action(state, action)

    def observe(self, state: GameState) -> ExecutionResult:
        self._validate_state(state)
        return self._result(state, ok=True, text=self._room_text(state))

    def acquire_item(self, state: GameState, item_name: str) -> ExecutionResult:
        self._validate_state(state)
        if item_name not in self.available_items(state):
            return self._result(state, ok=False, text="Item not available.", error="item_not_available")

        state.inventory.append(item_name)
        state.collected_items.append(item_name)
        effect = {"type": "item_acquired", "item": item_name}
        state.action_history.append(
            ActionRecord(
                action_id=f"acquire:{item_name}",
                source_room=state.current_room,
                resulting_room=state.current_room,
                effects=(effect,),
            )
        )
        return self._result(state, text=f"You acquired the {item_name}.", effects=(effect,))

    def use_item(self, state: GameState, item_name: str) -> ExecutionResult:
        self._validate_state(state)
        if item_name not in state.inventory:
            return self._result(state, ok=False, text="Item not in inventory.", error="item_not_in_inventory")

        state.inventory.remove(item_name)
        effect = {"type": "item_used", "item": item_name}
        state.action_history.append(
            ActionRecord(
                action_id=f"use:{item_name}",
                source_room=state.current_room,
                resulting_room=state.current_room,
                effects=(effect,),
            )
        )
        return self._result(state, text=f"You used the {item_name}.", effects=(effect,))

    def available_items(self, state: GameState) -> list[str]:
        room = self.story.room(state.current_room)
        return [
            item for item in room.get("items", ())
            if item not in state.collected_items and item not in state.inventory
        ]

    def _execute_action(self, state: GameState, action: str) -> ExecutionResult:
        room = self.story.room(state.current_room)
        target = room.get("exits", {}).get(action)

        if not target:
            return self._result(state, ok=False, text="You can't go that way.", error="invalid_action")

        if isinstance(target, str):
            return self._transition(state, action, target)

        skill_check = target.get("skill_check") if isinstance(target, Mapping) else None
        if skill_check is None:
            return self._result(state, ok=False, text="You can't go that way.", error="invalid_transition")

        state.pending_check = {
            "action_id": action,
            "source_room": state.current_room,
            "skill_check": _plain(skill_check),
        }
        dice_type = skill_check.get("dice_type", "1d20")
        target_value = skill_check.get("target", 10)
        return self._result(
            state,
            text=f"Roll {dice_type} (target {target_value} or higher).",
            awaiting_roll=True,
        )

    def _resolve_pending_check(self, state: GameState) -> ExecutionResult:
        pending = state.pending_check or {}
        check = pending["skill_check"]
        target = int(check.get("target", 10))
        seed_material = f"{state.random_seed}:{state.roll_count}".encode("utf-8")
        seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:16], "big")
        state.roll_count += 1
        roll = DiceEngine(random.Random(seed)).roll(check.get("dice_type", "1d20"), target=target)

        success = bool(roll.success)
        branch = check.get("success" if success else "failure", {})
        destination = branch.get("room") or pending["source_room"]
        description = (
            check.get("description")
            or branch.get("description")
            or ("You succeeded!" if success else "You failed!")
        )

        state.pending_check = None
        return self._transition(
            state,
            pending["action_id"],
            destination,
            text_override=description,
            dice_result=roll,
        )

    def _transition(
        self,
        state: GameState,
        action: str,
        destination: str,
        *,
        text_override: str | None = None,
        dice_result: DiceResult | None = None,
    ) -> ExecutionResult:
        if destination not in self.story.rooms:
            return self._result(
                state,
                ok=False,
                text=f"Destination {destination!r} does not exist.",
                error="invalid_destination",
            )

        source = state.current_room
        state.current_room = destination
        state.visit_counts[destination] = state.visit_counts.get(destination, 0) + 1
        effects = ({"type": "transition", "from": source, "to": destination},)

        state.action_history.append(
            ActionRecord(
                action_id=action,
                source_room=source,
                resulting_room=destination,
                effects=effects,
                dice_result=dice_result,
            )
        )

        text = text_override
        if text is None:
            text = self.story.room(destination).get("description", "You are here.")

        return self._result(
            state,
            text=text,
            effects=effects,
            transition=destination,
            dice_results=(dice_result,) if dice_result else (),
        )

    def _room_text(self, state: GameState) -> str:
        room = self.story.room(state.current_room)
        parts = [room.get("description", "You are here.")]
        revisits = room.get("revisits", [])
        count = state.visit_counts.get(state.current_room, 0)

        if room.get("show_all_revisits", False):
            parts.extend(
                revisit.get("content", "")
                for revisit in revisits
                if count >= revisit.get("count", 0)
            )
        else:
            for revisit in reversed(revisits):
                if count >= revisit.get("count", 0):
                    parts.append(revisit.get("content", ""))
                    break

        return "\n".join(part for part in parts if part)

    def _choices(self, state: GameState) -> tuple[dict[str, Any], ...]:
        exits = self.story.room(state.current_room).get("exits", {})
        choices: list[dict[str, Any]] = []
        for action_id, target in exits.items():
            if not target:
                continue
            choice = {"id": action_id, "label": str(action_id).replace("_", " ")}
            if isinstance(target, Mapping) and target.get("skill_check"):
                skill = target["skill_check"]
                choice["skill_check"] = {
                    "dice_type": skill.get("dice_type", "1d20"),
                    "target": skill.get("target", 10),
                }
            choices.append(choice)
        return tuple(choices)

    def _result(
        self,
        state: GameState,
        *,
        ok: bool = True,
        text: str = "",
        choices: tuple[dict[str, Any], ...] | None = None,
        effects: tuple[dict[str, Any], ...] = (),
        transition: str | None = None,
        dice_results: tuple[DiceResult, ...] = (),
        awaiting_roll: bool = False,
        error: str | None = None,
    ) -> ExecutionResult:
        result = ExecutionResult(
            ok=ok,
            room=state.current_room,
            text=text,
            choices=self._choices(state) if choices is None else choices,
            effects=effects,
            transition=transition,
            dice_results=dice_results,
            awaiting_roll=awaiting_roll,
            error=error,
        )
        if not self.trace_enabled:
            return result

        trace = [
            {"type": "step", "room": result.room, "ok": result.ok},
            {"type": "action", "text": result.text},
        ]
        for dice in dice_results:
            trace.append({
                "type": "check",
                "expression": dice.expression,
                "rolls": list(dice.individual_rolls),
                "modifier": dice.modifier,
                "total": dice.total,
                "target": dice.target,
                "success": dice.success,
            })
        if transition:
            trace.append({"type": "transition", "to": transition})
        trace.append({
            "type": "state",
            "current_room": state.current_room,
            "inventory": list(state.inventory),
            "visit_counts": dict(state.visit_counts),
        })
        return replace(result, trace=tuple(trace))

    def _validate_state(self, state: GameState) -> None:
        if state.story_name != self.story_id:
            raise ValueError(
                f"GameState belongs to {state.story_name!r}, engine runs {self.story_id!r}"
            )
        if state.current_room not in self.story.rooms:
            raise ValueError(f"current room {state.current_room!r} does not exist")


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value
