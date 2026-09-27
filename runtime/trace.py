from __future__ import annotations

from .actions import ExecutionResult
from .state import GameState


def format_trace(result: ExecutionResult, state: GameState) -> str:
    lines = ["[STEP]", f"Room: {state.current_room}"]
    if result.text:
        lines += ["", "Action:", result.text]

    for event in result.trace:
        kind = event.get("type")
        if kind == "check":
            lines += [
                "",
                "[CHECK]",
                f"Expression: {event.get('expression')}",
                f"Rolls: {event.get('rolls')}",
                f"Modifier: {event.get('modifier')}",
                f"Total: {event.get('total')}",
                f"Target: {event.get('target')}",
                f"Result: {'SUCCESS' if event.get('success') else 'FAILURE'}",
            ]
        elif kind == "transition":
            lines += ["", "[TRANSITION]", f"-> {event.get('to')}"]
        elif kind == "state":
            lines += [
                "",
                "[STATE]",
                f"Inventory: {', '.join(event.get('inventory', [])) or '(empty)'}",
                "Visit count:",
            ]
            lines.extend(
                f"    {room} = {count}"
                for room, count in event.get("visit_counts", {}).items()
            )
    return "\n".join(lines)
