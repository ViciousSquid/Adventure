"""Compatibility facade for the legacy adventures helper module."""

from __future__ import annotations

import random
from pathlib import Path

from storage.package import PackageLoader

_LOADER = PackageLoader(Path(__file__).resolve().parent / "adventures")


def load_adventures():
    return _LOADER.list_stories()


def get_adventure_data(adventure_name):
    return _LOADER.load(adventure_name).to_dict()


def get_start_room(adventure_name):
    return _LOADER.load(adventure_name).start_room


def get_room_data(adventure_name, room_name):
    return _LOADER.load(adventure_name).rooms.get(room_name)


def get_random_adventure():
    adventures = load_adventures()
    if not adventures:
        raise LookupError("no adventure packages are installed")
    return random.choice(list(adventures))


def get_cover_image_data(adventure_name):
    try:
        return _LOADER.read_asset(adventure_name, "cover.jpg")
    except FileNotFoundError:
        return None


def get_summary_text(adventure_name):
    return _LOADER.read_text_asset(adventure_name, "summary.txt")
