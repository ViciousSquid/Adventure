"""Compatibility facade at the application boundary.

Runtime code uses Story directly. These helpers remain only for older export tooling.
"""

from __future__ import annotations

import random
from pathlib import Path

from storage.repository import WorldRepository

_REPOSITORY = WorldRepository(Path(__file__).resolve().parent / "adventures")


def load_adventures():
    return _REPOSITORY.list_stories()


def get_adventure_data(adventure_name):
    return _REPOSITORY.load(adventure_name).to_legacy_dict()


def get_start_room(adventure_name):
    return _REPOSITORY.load(adventure_name).start_room


def get_room_data(adventure_name, room_name):
    return _REPOSITORY.load(adventure_name).to_legacy_dict()["rooms"].get(room_name)


def get_random_adventure():
    adventures = load_adventures()
    if not adventures:
        raise LookupError("no adventure packages are installed")
    return random.choice(list(adventures))


def get_cover_image_data(adventure_name):
    for candidate in ("assets/cover.jpg", "cover.jpg"):
        try:
            return _REPOSITORY.read_asset(adventure_name, candidate)
        except FileNotFoundError:
            continue
    return None


def get_summary_text(adventure_name):
    for candidate in ("assets/summary.txt", "summary.txt"):
        value = _REPOSITORY.read_text_asset(adventure_name, candidate)
        if value is not None:
            return value
    return None
