from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from flask import Flask

from storage.package import PackageLoader
from web.routes_adventure import register_adventure_routes
from web.routes_editor import register_editor_routes
from web.routes_main import register_main_routes

ROOT = Path(__file__).resolve().parents[1]


@dataclass(slots=True)
class AdventureServices:
    repository: PackageLoader
    trace_enabled: bool = False


def create_app(story_dir: str | os.PathLike[str] | None = None) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(ROOT / "static"),
        template_folder=str(ROOT / "templates"),
    )
    app.secret_key = os.environ.get("ADVENTURE_SECRET_KEY", "development-only-secret")

    services = AdventureServices(
        repository=PackageLoader(story_dir or (ROOT / "adventures")),
        trace_enabled=os.environ.get("ADVENTURE_TRACE", "").lower() in {"1", "true", "yes"},
    )
    app.extensions["adventure_services"] = services

    register_main_routes(app, services)
    register_adventure_routes(app, services)
    register_editor_routes(app, services)
    return app
