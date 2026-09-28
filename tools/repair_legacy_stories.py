from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile
from typing import Any


CURSE_WORLD = "Curse_of_the_Crimson_Cutlass"
ENIGMA_WORLD = "Enigma_of_the_Timekeeper"
WHISPERS_WORLD = "Whispers_of_the Forgotten_City"


ENIGMA_ROOMS: dict[str, dict[str, Any]] = {
    "chronal_engine_room": {
        "name": "The Chronal Engine Room",
        "description": (
            "The Chronal Engine towers above you, a cathedral of brass rings, "
            "glass conduits, and impossible clocks. Now that you have awakened it, "
            "the machine breathes with a slow mechanical pulse, and a doorway of "
            "shimmering light hangs in the centre of its workings."
            "\n\n"
            "The Timekeeper built this chamber as more than a laboratory. It is a "
            "hinge between moments. Beyond the portal you can feel whole centuries "
            "waiting to become real."
        ),
        "exits": {
            "Step through the chronal portal": "temporal_vortex",
            "Return to the laboratory": "laboratory",
        },
    },
    "time_sphere": {
        "name": "The Time Sphere Chamber",
        "description": (
            "The machine in the basement opens onto a hidden chamber where a "
            "crystalline sphere hangs weightless above a ring of ancient brass. "
            "Scenes flicker across its surface: empires rising, cities becoming "
            "dust, and stars burning themselves into history."
            "\n\n"
            "The Sphere is not merely an instrument. It is an invitation. "
            "For the first time, the Timekeeper's work feels less like a puzzle "
            "and more like a choice."
        ),
        "exits": {
            "Approach the Time Sphere": "time_sphere_chamber",
            "Return to the basement": "basement",
        },
    },
    "orrery_control": {
        "name": "The Orrery Control Room",
        "description": (
            "Behind the tower's final door stands the Orrery: a vast model of "
            "the heavens whose planets are made from silver, obsidian, and frozen "
            "light. Each orbit is marked with dates rather than distances."
            "\n\n"
            "At the centre waits a single control. The Timekeeper left it for "
            "someone who could finally understand that the past is not a prison "
            "and the future is not a destination. Both are doors."
        ),
        "exits": {
            "Set the Orrery in motion": "time_travel_nexus",
            "Return to the library tower": "library_tower",
        },
    },
}


CURSE_ENDINGS: dict[str, str] = {
    "curse_of_the_deep": (
        "The sea rises without a wind. The Crimson Cutlass answers with a sound "
        "like a bell heard from the bottom of the world, and the curse finally "
        "reveals its true shape: it was never bound to the blade, but to everyone "
        "who believed the ocean could be conquered."
        "\n\n"
        "You stand on the deck as the water closes over the horizon. Whether you "
        "have broken the curse or merely inherited it, the sea remembers your name."
    ),
    "free_of_the_curse": (
        "At dawn the blade lies quiet for the first time. No whisper follows your "
        "hand. No shadow moves against the sun. The curse has broken, and with it "
        "the last claim the old darkness held over your crew."
        "\n\n"
        "You cast the Crimson Cutlass into the surf. It does not sink immediately. "
        "For one long moment it floats like a dark feather, then the tide carries "
        "it away."
    ),
    "heart_of_the_island": (
        "Beneath the island you find a chamber carved around a living crystal that "
        "beats like a heart. Every pulse carries the voices of sailors who came "
        "before you. The treasure was never gold. It was memory."
        "\n\n"
        "You leave the heart untouched. Some discoveries are safer when they remain "
        "buried, and some victories are measured by what you refuse to possess."
    ),
    "redemption's_price": (
        "The sea asks for a price, and this time it does not ask in coin. To break "
        "the curse, someone must surrender the thing they most desperately want to "
        "keep. You understand the bargain only when the Cutlass goes cold in your "
        "hand."
        "\n\n"
        "You make the sacrifice. The storm breaks. Somewhere beyond the horizon, "
        "a bell rings once for the life you leave behind."
    ),
    "a_captain's_fall": (
        "The mutiny ends in silence. Your captain stares at the deck as the last "
        "challenge dies from the crew. The sea offers no judgement; it simply keeps "
        "moving."
        "\n\n"
        "You take the wheel with the uneasy knowledge that command is not a crown. "
        "It is a debt, and every sailor aboard your ship now owns a piece of it."
    ),
    "siren's_judgment": (
        "The siren circles the ship without touching it. Her song changes with every "
        "face she studies, searching for greed, fear, and the small lies people tell "
        "themselves when nobody is listening."
        "\n\n"
        "When she finally speaks, she does not curse you. She simply tells you the "
        "truth about yourself and disappears beneath the waves."
    ),
    "a_thief's_gambit": (
        "The final trap is almost laughably simple: the treasure is left where any "
        "thief can reach it, provided they are willing to ignore the door behind them."
        "\n\n"
        "You take the prize and spring the mechanism anyway, escaping by instinct and "
        "luck. When you finally reach open air, you realise the greatest theft was "
        "not the treasure. It was your own life from the trap."
    ),
    "a_pirate's_redemption": (
        "You return to the crew carrying neither gold nor excuses. You tell them what "
        "you did, what you feared, and what you are prepared to risk to make it right."
        "\n\n"
        "Nobody speaks for a long time. Then the oldest sailor removes his hat and "
        "offers you the ship's wheel. Redemption does not erase the past. It gives "
        "you a chance to sail beyond it."
    ),
    "no_honor_among_thieves": (
        "The alliance collapses in a storm of accusation and drawn steel. Every secret "
        "you kept becomes a weapon in somebody else's hand."
        "\n\n"
        "By morning the treasure is still there, but the people who came seeking it "
        "are gone. You learn the oldest lesson of piracy: a crew can survive hunger, "
        "fear, and even defeat, but not the certainty that everyone is waiting to "
        "betray everyone else."
    ),
    "a_pirate's_bond": (
        "You refuse the easy betrayal. The choice costs you the treasure you could "
        "have taken alone, but it leaves your crew standing beside you when the storm "
        "arrives."
        "\n\n"
        "Years later, sailors will tell the story as if loyalty were simple. You know "
        "better. It was a choice you made while every easier door stood open."
    ),
}


def _title(room_id: str) -> str:
    words = room_id.replace("_", " ").replace("-", " ").split()
    if not words:
        return "Untitled Place"
    small = {"a", "an", "and", "of", "the", "to", "in", "on", "for"}
    rendered = []
    for index, word in enumerate(words):
        lower = word.lower()
        rendered.append(
            lower if index and lower in small else lower.capitalize()
        )
    return " ".join(rendered)


def _hash_index(value: str, size: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return digest[0] % size


WHISPERS_TEMPLATES: dict[str, tuple[str, ...]] = {
    "fate": (
        "{title} waits beyond the last certainty. The prophecy does not announce what "
        "will happen; it merely shows the shape of the choice you are about to make. "
        "When you finally step into it, the whispers become quiet, as though the city "
        "has accepted your answer.",
        "You arrive at {title} expecting an ending and find a mirror instead. Every "
        "possible road is reflected there, but only one bears your own footsteps. "
        "You choose it without asking whether destiny approves.",
    ),
    "hero": (
        "At {title}, the old stones seem to remember every hero who came before you. "
        "The final trial is not strength but the willingness to stand when there is "
        "no promise of victory. You stand anyway, and the ancient city answers with "
        "silence that somehow feels like applause.",
        "The road ends at {title}, beneath a sky turning gold. You could take the "
        "title, the praise, and the story people will tell about you, but the moment "
        "passes quickly. What remains is simpler: someone needed you, and you stayed.",
    ),
    "dark": (
        "{title} is colder than the road behind you. The shadows gather as though "
        "they have been waiting for your name. You face them without pretending "
        "they can be destroyed; some darkness can only be denied a place inside you.",
        "The final door at {title} opens onto a darkness with no shape and no voice. "
        "You understand at last that the city was never asking whether you were "
        "fearless. It was asking whether fear would be allowed to choose for you.",
    ),
    "heart": (
        "In {title}, the grand mystery becomes painfully human. What you have been "
        "chasing is not buried beneath stone but carried by the people you met along "
        "the way. The answer is fragile, and that is precisely why it matters.",
        "The whispers lead you to {title}, where old promises are finally spoken aloud. "
        "You leave with no treasure except the certainty that trust, once given freely, "
        "can outlive the ruins that witnessed it.",
    ),
    "knowledge": (
        "The chamber of {title} is filled with tablets, maps, and names erased by time. "
        "You could spend a lifetime cataloguing what remains, but the city offers one "
        "last lesson: knowledge is not possession. It is responsibility.",
        "At {title}, the fragments finally fit together. The past does not become less "
        "tragic when understood; it becomes more difficult to ignore. You close the "
        "last book knowing that remembering is itself an act of courage.",
    ),
    "divine": (
        "{title} rises beyond the mortal road like a monument built from light. "
        "You are offered power enough to remake the world, and for one tempting moment "
        "you understand why so many before you accepted the bargain. Then you remember "
        "what power costs.",
        "At {title}, the ancient powers ask you to become something greater than human. "
        "You answer with the only truth you have learned on the journey: a life does "
        "not become meaningful because it lasts forever.",
    ),
    "journey": (
        "The path to {title} seems to stretch forever, yet the moment you reach it you "
        "understand that the road was part of the answer. You look back and recognise "
        "your own footsteps among the city's forgotten ones.",
        "At {title}, there is no trumpet and no gate closing behind you. Only a road "
        "leading onward. For the first time, you do not need to know where it ends.",
    ),
    "mystery": (
        "{title} is the place the whispers warned you about. The secret is real, but "
        "it refuses to become a simple answer. Some truths are doors, not destinations, "
        "and you have only just learned how to open this one.",
        "The city falls silent at {title}. In that silence you finally hear the answer "
        "you could not hear while the world was speaking over itself. It is not a name, "
        "a weapon, or a treasure. It is a question you will carry with you.",
    ),
    "artifact": (
        "The relic at {title} is older than the city and warmer than it should be. "
        "You could claim it, sell it, or hide it, but its power is bound to the story "
        "that brought you here. You choose what to do with it knowing the choice will "
        "outlive you.",
        "At {title}, the long hunt finally produces something solid: an artifact that "
        "has survived every empire around it. Holding it, you realise the object is not "
        "the prize. The promise you make with it is.",
    ),
    "general": (
        "The road ends at {title}. The ancient city offers no easy applause, only one "
        "last moment in which everything you have seen can be understood as part of a "
        "single journey. You breathe, listen to the distant whisper of the ruins, and "
        "choose to remember.",
        "You reach {title} beneath a sky full of unfamiliar stars. Whatever the city "
        "intended, you have made the place your own. The old paths fall quiet behind "
        "you, and the story finally belongs to you.",
        "At {title}, the final secret is not something you uncover but something you "
        "accept. The ruins have survived by carrying their stories forward. You will "
        "do the same.",
    ),
}


def _ending_description(world: str, room_id: str) -> str:
    if world == CURSE_WORLD and room_id in CURSE_ENDINGS:
        return CURSE_ENDINGS[room_id]

    lowered = room_id.lower()
    if any(token in lowered for token in ("fate", "destiny", "prophecy")):
        archetype = "fate"
    elif any(token in lowered for token in ("hero", "champion", "valor", "courage", "legend", "trial")):
        archetype = "hero"
    elif any(token in lowered for token in ("shadow", "dark", "terror", "mad", "devil", "vengeance", "doom", "void")):
        archetype = "dark"
    elif any(token in lowered for token in ("heart", "love", "trust", "peace", "harmony", "companion", "friend")):
        archetype = "heart"
    elif any(token in lowered for token in ("knowledge", "scholar", "loremaster", "history", "wisdom", "learning")):
        archetype = "knowledge"
    elif any(token in lowered for token in ("god", "divine", "divinity", "deity", "heaven")):
        archetype = "divine"
    elif any(token in lowered for token in ("path", "journey", "road", "wandering", "traveler", "travel")):
        archetype = "journey"
    elif any(token in lowered for token in ("relic", "artifact", "treasure", "weapon")):
        archetype = "artifact"
    elif any(token in lowered for token in ("secret", "mystery", "truth", "mirror", "dream")):
        archetype = "mystery"
    else:
        archetype = "general"

    title = _title(room_id)
    templates = WHISPERS_TEMPLATES[archetype]
    return templates[_hash_index(room_id, len(templates))].format(title=title)


def _collect_missing_destinations(story: dict[str, Any]) -> list[str]:
    rooms = story.get("rooms") or {}
    missing: set[str] = set()

    def visit_destination(value: Any) -> None:
        if isinstance(value, str):
            if value not in rooms:
                missing.add(value)
            return
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"room", "to"}:
                    visit_destination(child)
                elif key == "skill_check":
                    visit_destination(child)
            return
        if isinstance(value, list):
            for child in value:
                visit_destination(child)

    for room in rooms.values():
        if not isinstance(room, dict):
            continue
        exits = room.get("exits", {})
        if isinstance(exits, dict):
            for target in exits.values():
                visit_destination(target)

    return sorted(missing)


def repair_story(world: str, story: dict[str, Any]) -> int:
    rooms = story.get("rooms")
    if not isinstance(rooms, dict):
        raise ValueError(f"{world}: story.rooms must be an object")

    added = 0

    if world == ENIGMA_WORLD:
        for room_id, room in ENIGMA_ROOMS.items():
            if room_id not in rooms:
                rooms[room_id] = room
                added += 1

    if world in {CURSE_WORLD, WHISPERS_WORLD}:
        for room_id in _collect_missing_destinations(story):
            if room_id in rooms:
                continue
            rooms[room_id] = {
                "name": _title(room_id),
                "description": _ending_description(world, room_id),
                "exits": {},
            }
            added += 1

    return added


def repair_archive(path: Path, world: str) -> int:
    with ZipFile(path, "r") as source:
        story = json.loads(
            source.read("story.json").decode("utf-8"),
            strict=False,
        )
        added = repair_story(world, story)
        if not added:
            return 0

        members = [
            (info.filename, source.read(info.filename))
            for info in source.infolist()
            if not info.is_dir() and info.filename != "story.json"
        ]

    story_text = json.dumps(story, indent=2, ensure_ascii=False) + "\n"
    with NamedTemporaryFile(
        prefix=f".{path.stem}.",
        suffix=".zip",
        dir=path.parent,
        delete=False,
    ) as handle:
        temporary = Path(handle.name)

    try:
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as target:
            target.writestr("story.json", story_text.encode("utf-8"))
            for name, payload in members:
                target.writestr(name, payload)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

    return added


def repair_worlds(root: Path) -> dict[str, int]:
    results: dict[str, int] = {}
    for world in (CURSE_WORLD, ENIGMA_WORLD, WHISPERS_WORLD):
        path = root / "adventures" / f"{world}.zip"
        if not path.exists():
            raise FileNotFoundError(path)
        results[world] = repair_archive(path, world)
    return results


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    results = repair_worlds(root)
    for world, count in results.items():
        print(f"REPAIRED {world}: added {count} room(s)")
