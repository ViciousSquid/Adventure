from __future__ import annotations

import base64
import copy
import io
import json
import random
import re
import zipfile
from dataclasses import dataclass, field
from secrets import randbits
from typing import Any, Mapping

DICE_TERM = re.compile(r"(?P<sign>[+-]?)\s*(?:(?P<count>\d+)d(?P<size>\d+)|(?P<number>\d+))")
DICE_EXPRESSION = re.compile(r"^\s*\d+d\d+(?:\s*[+-]\s*(?:\d+d\d+|\d+))*\s*$")

@dataclass(frozen=True, slots=True)
class DiceResult:
    expression: str
    individual_rolls: tuple[int, ...]
    modifier: int
    total: int
    target: int | None = None
    success: bool | None = None
    def to_dict(self) -> dict[str, Any]:
        return {"expression": self.expression, "individual_rolls": list(self.individual_rolls),
                "modifier": self.modifier, "total": self.total, "target": self.target,
                "success": self.success, "dice_notation": self.expression,
                "roll_details": list(self.individual_rolls), "roll_result": self.total}

class DiceEngine:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
    def roll(self, expression: str, target: int | None = None) -> DiceResult:
        terms = list(self._parse(expression))
        if not terms:
            raise ValueError(f"Invalid dice expression: {expression!r}")
        rolls: list[int] = []
        modifier = 0
        total = 0
        for sign, count, size, number in terms:
            direction = -1 if sign == "-" else 1
            if count is not None:
                component = [self.rng.randint(1, size) for _ in range(count)]
                rolls.extend(component)
                total += direction * sum(component)
            else:
                modifier += direction * number
                total += direction * number
        return DiceResult(expression, tuple(rolls), modifier, total, target,
                          None if target is None else total >= target)
    @staticmethod
    def _parse(expression: str):
        position = 0
        while position < len(expression):
            match = DICE_TERM.match(expression, position)
            if not match:
                if expression[position].isspace():
                    position += 1
                    continue
                raise ValueError(f"Invalid dice expression component near {expression[position:]!r}")
            sign = match.group("sign")
            if match.group("count") is not None:
                yield sign, int(match.group("count")), int(match.group("size")), None
            else:
                yield sign, None, None, int(match.group("number"))
            position = match.end()

@dataclass(frozen=True, slots=True)
class ActionRecord:
    action_id: str
    source_room: str
    resulting_room: str
    effects: tuple[dict[str, Any], ...] = ()
    dice_result: DiceResult | None = None
    def to_dict(self) -> dict[str, Any]:
        return {"action_id": self.action_id, "source_room": self.source_room,
                "resulting_room": self.resulting_room, "effects": list(self.effects),
                "dice_result": self.dice_result.to_dict() if self.dice_result else None}

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
    def new(cls, story_name: str, start_room: str) -> "GameState":
        return cls(story_name, start_room, visit_counts={start_room: 0}, random_seed=randbits(64))

    def to_dict(self) -> dict[str, Any]:
        return {"version": 2, "story_name": self.story_name, "current_room": self.current_room,
                "inventory": list(self.inventory), "action_history": [x.to_dict() for x in self.action_history],
                "visit_counts": dict(self.visit_counts), "variables": dict(self.variables),
                "collected_items": list(self.collected_items), "pending_check": copy.deepcopy(self.pending_check),
                "random_seed": self.random_seed, "roll_count": self.roll_count}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GameState":
        story_name = data.get("story_name") or data.get("current_adventure") or data.get("name")
        current_room = data.get("current_room")
        if not story_name or not current_room:
            raise ValueError("save game is missing its story or current room")
        records = []
        for raw in data.get("action_history", []):
            if not isinstance(raw, dict):
                continue
            dice_data = raw.get("dice_result")
            dice_result = None
            if dice_data:
                dice_result = DiceResult(
                    dice_data.get("expression", ""), tuple(dice_data.get("individual_rolls", [])),
                    int(dice_data.get("modifier", 0)), int(dice_data.get("total", 0)),
                    dice_data.get("target"), dice_data.get("success"))
            records.append(ActionRecord(str(raw.get("action_id", "unknown")),
                                         str(raw.get("source_room", "")),
                                         str(raw.get("resulting_room", current_room)),
                                         tuple(raw.get("effects", [])), dice_result))
        visit_counts = dict(data.get("visit_counts") or {})
        if not visit_counts:
            visit_counts = {}
            for record in records:
                visit_counts[record.resulting_room] = visit_counts.get(record.resulting_room, 0) + 1
            visit_counts.setdefault(current_room, 0)
        return cls(str(story_name), str(current_room), list(data.get("inventory") or []), records,
                   {str(k): int(v) for k, v in visit_counts.items()}, dict(data.get("variables") or {}),
                   list(data.get("collected_items") or []), copy.deepcopy(data.get("pending_check")),
                   int(data.get("random_seed", randbits(64))), int(data.get("roll_count", 0)))

class AdventureEngine:
    def __init__(self, package: Mapping[str, Any]):
        self.package = package
        self.story = package["story"]
        self.checks = package.get("skill_checks", {}).get("skill_checks", {})
        self.inventory = package.get("inventory", {})
        self.story_id = str(self.story["name"])

    def new_game(self) -> GameState:
        state = GameState.new(self.story_id, self.story["start_room"])
        self._arm_room_skill_check(state)
        return state

    def observe(self, state: GameState) -> dict[str, Any]:
        self._validate_state(state)
        pending = state.pending_check or {}
        if pending.get("kind") == "room":
            check = self.checks[pending["skill_check_id"]]
            return self._result(
                state,
                text=f"Roll {check.get('dice_type', '1d20')} (target {check.get('target', 10)} or higher).",
                awaiting_roll=True,
            )
        return self._result(state, text=self._room_text(state))

    def step(self, state: GameState, action: str) -> dict[str, Any]:
        self._validate_state(state)
        if action == "roll":
            if not state.pending_check:
                return self._result(state, ok=False, text="There is no pending skill check.", error="no_pending_check")
            return self._resolve_pending_check(state)
        if state.pending_check:
            return self._result(state, ok=False, text="Resolve the pending skill check before choosing another action.",
                                error="pending_roll")
        if action.startswith("acquire:"):
            return self.acquire_item(state, action.partition(":")[2])
        if action.startswith("use:"):
            return self.use_item(state, action.partition(":")[2])
        return self._execute_action(state, action)

    def acquire_item(self, state: GameState, item_id: str) -> dict[str, Any]:
        if item_id not in self.available_items(state):
            return self._result(state, ok=False, text="Item not available.", error="item_not_available")
        state.inventory.append(item_id)
        state.collected_items.append(item_id)
        effect = {"type": "item_acquired", "item": item_id}
        state.action_history.append(ActionRecord(f"acquire:{item_id}", state.current_room, state.current_room, (effect,)))
        name = self.inventory.get("items", {}).get(item_id, {}).get("name", item_id)
        return self._result(state, text=f"You acquired the {name}.", effects=(effect,))

    def use_item(self, state: GameState, item_id: str) -> dict[str, Any]:
        if item_id not in state.inventory:
            return self._result(state, ok=False, text="Item not in inventory.", error="item_not_in_inventory")
        state.inventory.remove(item_id)
        effect = {"type": "item_used", "item": item_id}
        state.action_history.append(ActionRecord(f"use:{item_id}", state.current_room, state.current_room, (effect,)))
        name = self.inventory.get("items", {}).get(item_id, {}).get("name", item_id)
        return self._result(state, text=f"You used the {name}.", effects=(effect,))

    def available_items(self, state: GameState) -> list[str]:
        item_ids = self.inventory.get("room_items", {}).get(state.current_room, [])
        return [x for x in item_ids if x not in state.collected_items and x not in state.inventory]

    def _execute_action(self, state: GameState, action: str) -> dict[str, Any]:
        connection = self.story.get("connections", {}).get(action)
        if not connection or connection.get("from") != state.current_room:
            return self._result(state, ok=False, text="You can't go that way.", error="invalid_action")
        required = connection.get("requires_item")
        if required and required not in state.inventory:
            name = self.inventory.get("items", {}).get(required, {}).get("name", required)
            return self._result(state, ok=False, text=f"You need the {name}.", error="missing_item")
        skill_id = connection.get("skill_check")
        if skill_id:
            check = self.checks[skill_id]
            state.pending_check = {"kind": "connection", "connection_id": action, "source_room": state.current_room, "skill_check_id": skill_id}
            return self._result(state, text=f"Roll {check.get('dice_type', '1d20')} (target {check.get('target', 10)} or higher).",
                                awaiting_roll=True)
        return self._transition(state, action, connection["to"])

    def _resolve_pending_check(self, state: GameState) -> dict[str, Any]:
        pending = state.pending_check
        check = self.checks[pending["skill_check_id"]]
        target = int(check.get("target", 10))
        seed_material = f"{state.random_seed}:{state.roll_count}".encode("utf-8")
        seed = int.from_bytes(__import__("hashlib").sha256(seed_material).digest()[:16], "big")
        state.roll_count += 1
        roll = DiceEngine(random.Random(seed)).roll(check.get("dice_type", "1d20"), target=target)
        success = bool(roll.success)
        branch = check.get("success" if success else "failure", {})
        description = check.get("description") or branch.get("description") or ("You succeeded!" if success else "You failed!")
        state.pending_check = None

        if pending.get("kind") == "room":
            room_id = pending["room_id"]
            destination = branch.get("to") or room_id
            if destination == room_id:
                return self._result(state, text=description, dice_results=(roll,))
            return self._transition(
                state,
                f"room_skill_check:{room_id}",
                destination,
                text_override=description,
                dice_result=roll,
            )

        connection = self.story["connections"][pending["connection_id"]]
        destination = branch.get("to") or connection["to"] or connection["from"]
        return self._transition(state, pending["connection_id"], destination, text_override=description, dice_result=roll)

    def _arm_room_skill_check(self, state: GameState) -> None:
        room = self.story["rooms"][state.current_room]
        skill_id = room.get("skill_check")
        if not skill_id or state.pending_check:
            return
        state.pending_check = {
            "kind": "room",
            "room_id": state.current_room,
            "skill_check_id": skill_id,
        }

    def _transition(self, state: GameState, action: str, destination: str, *,
                    text_override: str | None = None, dice_result: DiceResult | None = None) -> dict[str, Any]:
        if destination not in self.story.get("rooms", {}):
            return self._result(state, ok=False, text=f"Destination {destination!r} does not exist.", error="invalid_destination")
        source = state.current_room
        state.current_room = destination
        state.visit_counts[destination] = state.visit_counts.get(destination, 0) + 1
        effects = ({"type": "transition", "from": source, "to": destination},)
        state.action_history.append(ActionRecord(action, source, destination, effects, dice_result))
        text = text_override if text_override is not None else self.story["rooms"][destination].get("description", "You are here.")
        self._arm_room_skill_check(state)
        awaiting_roll = bool(state.pending_check and state.pending_check.get("kind") == "room")
        return self._result(state, text=text, effects=effects, transition=destination,
                            dice_results=(dice_result,) if dice_result else (),
                            awaiting_roll=awaiting_roll)

    def _room_text(self, state: GameState) -> str:
        room = self.story["rooms"][state.current_room]
        parts = [room.get("description", "You are here.")]
        revisit = self.story.get("revisits", {}).get(state.current_room, {})
        count = state.visit_counts.get(state.current_room, 0)
        entries = revisit.get("entries", [])
        if revisit.get("show_all", False):
            parts.extend(e.get("content", "") for e in entries if count >= e.get("count", 0))
        else:
            for entry in reversed(entries):
                if count >= entry.get("count", 0):
                    parts.append(entry.get("content", ""))
                    break
        return "\n".join(x for x in parts if x)

    def _choices(self, state: GameState) -> list[dict[str, Any]]:
        choices = []
        for connection_id, connection in self.story.get("connections", {}).items():
            if connection.get("from") != state.current_room:
                continue
            choice = {"id": connection_id, "label": connection["label"], "to": connection["to"]}
            if connection.get("requires_item"):
                choice["requires_item"] = connection["requires_item"]
            skill_id = connection.get("skill_check")
            if skill_id:
                check = self.checks[skill_id]
                choice["skill_check"] = {"id": skill_id, "dice_type": check.get("dice_type", "1d20"),
                                          "target": check.get("target", 10)}
            choices.append(choice)
        return choices

    def _result(self, state: GameState, *, ok: bool = True, text: str = "",
                effects: tuple[dict[str, Any], ...] = (), transition: str | None = None,
                dice_results: tuple[DiceResult, ...] = (), awaiting_roll: bool = False,
                error: str | None = None) -> dict[str, Any]:
        return {"ok": ok, "room": state.current_room, "text": text, "choices": self._choices(state),
                "effects": list(effects), "transition": transition,
                "dice_results": [x.to_dict() for x in dice_results],
                "awaiting_roll": awaiting_roll, "error": error, "trace": []}

    def _validate_state(self, state: GameState) -> None:
        if state.story_name != self.story_id:
            raise ValueError(f"GameState belongs to {state.story_name!r}, engine runs {self.story_id!r}")
        if state.current_room not in self.story.get("rooms", {}):
            raise ValueError(f"current room {state.current_room!r} does not exist")

def validate_package(package: Mapping[str, Any]) -> dict[str, Any]:
    story = copy.deepcopy(package["story"])
    checks = copy.deepcopy(package.get("skill_checks", {}))
    inventory = copy.deepcopy(package.get("inventory", {}))
    errors = []
    if story.get("schema_version") != 3: errors.append("story.schema_version must be 3")
    if checks.get("schema_version") != 1: errors.append("skill_checks.schema_version must be 1")
    if inventory.get("schema_version") != 1: errors.append("inventory.schema_version must be 1")
    if not isinstance(story.get("name"), str) or not story["name"].strip(): errors.append("story.name must be a non-empty string")
    rooms = story.get("rooms")
    if not isinstance(rooms, dict) or not rooms: errors.append("story.rooms must be a non-empty object"); rooms = {}
    if story.get("start_room") not in rooms: errors.append("story.start_room does not exist")
    for room_id, room in rooms.items():
        if not isinstance(room, dict):
            continue
        skill_id = room.get("skill_check")
        if skill_id and skill_id not in checks.get("skill_checks", {}):
            errors.append(f"room {room_id!r} references unknown skill check {skill_id!r}")
    connections = story.get("connections", {})
    if not isinstance(connections, dict): errors.append("story.connections must be an object"); connections = {}
    items = inventory.get("items", {})
    for connection_id, connection in connections.items():
        if not isinstance(connection, dict): errors.append(f"connection {connection_id!r} must be an object"); continue
        if connection.get("from") not in rooms: errors.append(f"connection {connection_id!r}.from does not exist")
        if connection.get("to") not in rooms: errors.append(f"connection {connection_id!r}.to does not exist")
        if not isinstance(connection.get("label"), str) or not connection.get("label"): errors.append(f"connection {connection_id!r}.label must be a non-empty string")
        skill_id = connection.get("skill_check")
        if skill_id and skill_id not in checks.get("skill_checks", {}): errors.append(f"connection {connection_id!r} references unknown skill check {skill_id!r}")
        item_id = connection.get("requires_item")
        if item_id and item_id not in items: errors.append(f"connection {connection_id!r} references unknown item {item_id!r}")
    if errors: raise ValueError("\n".join(errors))
    return {"world": story["name"], "source_format": "canonical", "story": story, "skill_checks": checks, "inventory": inventory}

def package_from_zip(data: bytes) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
        members = set(archive.namelist())
        required = {"story.json", "skill_checks.json", "inventory.json"}
        missing = required - members
        if missing: raise ValueError("This browser build accepts canonical world packages; missing: " + ", ".join(sorted(missing)))
        package = validate_package({
            "story": json.loads(archive.read("story.json").decode("utf-8")),
            "skill_checks": json.loads(archive.read("skill_checks.json").decode("utf-8")),
            "inventory": json.loads(archive.read("inventory.json").decode("utf-8"))})
        assets = {}
        for name in archive.namelist():
            if not name.startswith("assets/") or name.endswith("/"): continue
            suffix = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            mime = {"png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg","gif":"image/gif","webp":"image/webp","svg":"image/svg+xml","txt":"text/plain"}.get(suffix, "application/octet-stream")
            assets[name] = "data:%s;base64,%s" % (mime, base64.b64encode(archive.read(name)).decode("ascii"))
        package["assets"] = assets
        return package

def package_to_zip(package: Mapping[str, Any]) -> bytes:
    canonical = validate_package(package)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("story.json", json.dumps(canonical["story"], indent=2, ensure_ascii=False) + "\n")
        archive.writestr("skill_checks.json", json.dumps(canonical["skill_checks"], indent=2, ensure_ascii=False) + "\n")
        archive.writestr("inventory.json", json.dumps(canonical["inventory"], indent=2, ensure_ascii=False) + "\n")
        for name, value in (package.get("assets") or {}).items():
            if isinstance(value, str) and "," in value:
                archive.writestr(name, base64.b64decode(value.split(",", 1)[1]))
    return buffer.getvalue()

def json_call(operation: str, payload: Any) -> Any:
    # Pyodide may pass JavaScript objects through as JsProxy instances.
    # Normalize JSON-shaped JavaScript objects before using Python mapping syntax.
    if hasattr(payload, "as_py_json"):
        payload = payload.as_py_json()
    elif hasattr(payload, "to_py"):
        payload = payload.to_py()

    if operation == "new_game":
        return AdventureEngine(payload["package"]).new_game().to_dict()
    if operation == "observe":
        return AdventureEngine(payload["package"]).observe(GameState.from_dict(payload["state"]))
    if operation in {"step", "roll"}:
        state = GameState.from_dict(payload["state"])
        action = "roll" if operation == "roll" else payload["action"]
        result = AdventureEngine(payload["package"]).step(state, action)
        return {"state": state.to_dict(), "result": result}
    if operation == "validate":
        return validate_package(payload)
    if operation == "zip_read":
        return package_from_zip(bytes(payload))
    if operation == "zip_write":
        return list(package_to_zip(payload))
    raise ValueError(f"Unknown browser runtime operation: {operation}")
