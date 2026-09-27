from __future__ import annotations

import hashlib
import random
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

        if state.pending_check:
            return self._result(
                state,
                ok=False,
                text="Resolve the pending skill check before choosing another action.",
                error="pending_roll",
            )

        if action.startswith("acquire:"):
            return self.acquire_item(state, action.partition(":")[2])

        if action.startswith("use:"):
            return self.use_item(state, action.partition(":")[2])

        return self._execute_action(state, action)

    def observe(self, state: GameState) -> ExecutionResult:
        self._validate_state(state)
        return self._result(state, ok=True, text=self._room_text(state))

    def acquire_item(self, state: GameState, item_id: str) -> ExecutionResult:
        self._validate_state(state)
        if item_id not in self.available_items(state):
            return self._result(
                state,
                ok=False,
                text="Item not available.",
                error="item_not_available",
            )

        state.inventory.append(item_id)
        state.collected_items.append(item_id)
        effect = {"type": "item_acquired", "item": item_id}
        state.action_history.append(
            ActionRecord(
                action_id=f"acquire:{item_id}",
                source_room=state.current_room,
                resulting_room=state.current_room,
                effects=(effect,),
            )
        )
        name = self.story.items[item_id].get("name", item_id)
        return self._result(
            state,
            text=f"You acquired the {name}.",
            effects=(effect,),
        )

    def use_item(self, state: GameState, item_id: str) -> ExecutionResult:
        self._validate_state(state)
        if item_id not in state.inventory:
            return self._result(
                state,
                ok=False,
                text="Item not in inventory.",
                error="item_not_in_inventory",
            )

        state.inventory.remove(item_id)
        effect = {"type": "item_used", "item": item_id}
        state.action_history.append(
            ActionRecord(
                action_id=f"use:{item_id}",
                source_room=state.current_room,
                resulting_room=state.current_room,
                effects=(effect,),
            )
        )
        name = self.story.items[item_id].get("name", item_id)
        return self._result(
            state,
            text=f"You used the {name}.",
            effects=(effect,),
        )

    def available_items(self, state: GameState) -> list[str]:
        item_ids = self.story.room_items.get(state.current_room, ())
        return [
            item_id
            for item_id in item_ids
            if item_id not in state.collected_items
            and item_id not in state.inventory
        ]

    def _execute_action(self, state: GameState, action: str) -> ExecutionResult:
        connection = self._connection_for_action(state.current_room, action)
        if connection is None:
            return self._result(
                state,
                ok=False,
                text="You can't go that way.",
                error="invalid_action",
            )

        required = connection.get("requires_item")
        if required and required not in state.inventory:
            name = self.story.items[required].get("name", required)
            return self._result(
                state,
                ok=False,
                text=f"You need the {name}.",
                error="missing_item",
            )

        skill_id = connection.get("skill_check")
        if skill_id:
            check = self.story.skill_check(skill_id)
            state.pending_check = {
                "connection_id": action,
                "source_room": state.current_room,
                "skill_check_id": skill_id,
            }
            return self._result(
                state,
                text=(
                    f"Roll {check.get('dice_type', '1d20')} "
                    f"(target {check.get('target', 10)} or higher)."
                ),
                awaiting_roll=True,
            )

        return self._transition(state, action, connection["to"])

    def _resolve_pending_check(self, state: GameState) -> ExecutionResult:
        pending = state.pending_check or {}
        connection = self.story.connection(pending["connection_id"])
        check = self.story.skill_check(pending["skill_check_id"])
        target = int(check.get("target", 10))
        seed_material = f"{state.random_seed}:{state.roll_count}".encode("utf-8")
        seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:16], "big")
        state.roll_count += 1
        roll = DiceEngine(random.Random(seed)).roll(
            check.get("dice_type", "1d20"),
            target=target,
        )

        success = bool(roll.success)
        branch = check.get("success" if success else "failure", {})
        destination = branch.get("to") or connection["to"] or connection["from"]
        description = (
            check.get("description")
            or branch.get("description")
            or ("You succeeded!" if success else "You failed!")
        )

        state.pending_check = None
        return self._transition(
            state,
            pending["connection_id"],
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
            text = self.story.room(destination).get(
                "description", "You are here."
            )

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
        revisit_data = self.story.revisits.get(state.current_room, {})
        count = state.visit_counts.get(state.current_room, 0)
        entries = revisit_data.get("entries", ())

        if revisit_data.get("show_all", False):
            parts.extend(
                entry.get("content", "")
                for entry in entries
                if count >= entry.get("count", 0)
            )
        else:
            for entry in reversed(entries):
                if count >= entry.get("count", 0):
                    parts.append(entry.get("content", ""))
                    break

        return "\n".join(part for part in parts if part)

    def _choices(self, state: GameState) -> tuple[dict[str, Any], ...]:
        choices: list[dict[str, Any]] = []
        for connection_id, connection in self.story.connections.items():
            if connection.get("from") != state.current_room:
                continue
            choice = {
                "id": connection_id,
                "label": connection["label"],
                "to": connection["to"],
            }
            if connection.get("requires_item"):
                choice["requires_item"] = connection["requires_item"]
            skill_id = connection.get("skill_check")
            if skill_id:
                check = self.story.skill_check(skill_id)
                choice["skill_check"] = {
                    "id": skill_id,
                    "dice_type": check.get("dice_type", "1d20"),
                    "target": check.get("target", 10),
                }
            choices.append(choice)
        return tuple(choices)

    def _connection_for_action(
        self,
        room_id: str,
        action: str,
    ) -> dict[str, Any] | None:
        connection = self.story.connections.get(action)
        if connection and connection.get("from") == room_id:
            return connection
        return None

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
            trace.append(
                {
                    "type": "check",
                    "expression": dice.expression,
                    "rolls": list(dice.individual_rolls),
                    "modifier": dice.modifier,
                    "total": dice.total,
                    "target": dice.target,
                    "success": dice.success,
                }
            )
        if transition:
            trace.append({"type": "transition", "to": transition})
        trace.append(
            {
                "type": "state",
                "current_room": state.current_room,
                "inventory": list(state.inventory),
                "visit_counts": dict(state.visit_counts),
            }
        )
        return replace(result, trace=tuple(trace))

    def _validate_state(self, state: GameState) -> None:
        if state.story_name != self.story_id:
            raise ValueError(
                f"GameState belongs to {state.story_name!r}, engine runs {self.story_id!r}"
            )
        if state.current_room not in self.story.rooms:
            raise ValueError(f"current room {state.current_room!r} does not exist")
