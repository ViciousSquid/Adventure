from __future__ import annotations

import base64
import json
import mimetypes
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from runtime.engine import AdventureEngine
from runtime.state import GameState
from story.validator import StoryValidationError, validate_package_data
from storage.repository import WorldRepository

ROOT = Path(__file__).resolve().parent
STATIC_ROOT = ROOT / "static"
MAX_REQUEST_BYTES = 16 * 1024 * 1024


class AdventureServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(
        self,
        address: tuple[str, int],
        repository: WorldRepository,
        trace: bool,
    ):
        super().__init__(address, AdventureHandler)
        self.repository = repository
        self.trace_enabled = trace


def create_server(
    repository: WorldRepository,
    *,
    host: str = "127.0.0.1",
    port: int = 5000,
    trace: bool = False,
) -> AdventureServer:
    return AdventureServer((host, port), repository, trace)


class AdventureHandler(BaseHTTPRequestHandler):
    server_version = "AdventureHTTP/1.0"

    @property
    def server_ref(self) -> AdventureServer:
        return self.server  # type: ignore[return-value]

    @property
    def repository(self) -> WorldRepository:
        return self.server_ref.repository

    def do_GET(self) -> None:
        try:
            path = urllib.parse.urlsplit(self.path).path
            if path == "/api/stories":
                self._json_response(
                    200,
                    {
                        "stories": [
                            {
                                "id": name,
                                "source_format": self.repository.source_format(name),
                            }
                            for name in self.repository.list_stories()
                        ]
                    },
                )
                return

            parts = [
                urllib.parse.unquote(part)
                for part in path.split("/")
                if part
            ]
            if len(parts) >= 3 and parts[:2] == ["api", "world"]:
                world = parts[2]
                if len(parts) == 3:
                    story = self.repository.load(world)
                    self._json_response(
                        200,
                        {
                            "world": world,
                            "source_format": self.repository.source_format(world),
                            **story.to_dict(),
                        },
                    )
                    return
                if parts[3] == "asset" and len(parts) >= 5:
                    self._asset_response(
                        world,
                        "/".join(parts[4:]),
                    )
                    return

            self._serve_static(path)
        except (FileNotFoundError, ValueError, StoryValidationError) as exc:
            self._json_response(404, {"error": str(exc)})

    def do_POST(self) -> None:
        try:
            path = urllib.parse.urlsplit(self.path).path
            payload = self._read_json()

            if path == "/api/game/new":
                self._game_new(payload)
            elif path == "/api/game/step":
                self._game_step(payload, roll=False)
            elif path == "/api/game/roll":
                self._game_step(payload, roll=True)
            elif path == "/api/editor/validate":
                validate_package_data(
                    _object(payload, "story"),
                    _object(payload, "skill_checks"),
                    _object(payload, "inventory"),
                )
                self._json_response(200, {"valid": True})
            elif path == "/api/editor/save":
                self._editor_save(payload)
            else:
                self._json_response(
                    404,
                    {"error": "unknown API endpoint"},
                )
        except (FileNotFoundError, ValueError, StoryValidationError) as exc:
            self._json_response(400, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        if os.environ.get("ADVENTURE_HTTP_LOG"):
            super().log_message(format, *args)

    def _game_new(self, payload: dict[str, Any]) -> None:
        world = _string(payload, "world")
        story = self.repository.load(world)
        engine = AdventureEngine(
            story,
            trace=self.server_ref.trace_enabled,
            story_id=world,
        )
        state = engine.new_game()
        self._json_response(
            200,
            {
                "state": state.to_dict(),
                "result": engine.observe(state).to_dict(),
            },
        )

    def _game_step(
        self,
        payload: dict[str, Any],
        *,
        roll: bool,
    ) -> None:
        world = _string(payload, "world")
        state_data = _object(payload, "state")
        action = "roll" if roll else _string(payload, "action")
        story = self.repository.load(world)
        engine = AdventureEngine(
            story,
            trace=self.server_ref.trace_enabled,
            story_id=world,
        )
        state = GameState.from_dict(state_data)
        result = engine.step(state, action)
        self._json_response(
            200,
            {
                "state": state.to_dict(),
                "result": result.to_dict(),
            },
        )

    def _editor_save(self, payload: dict[str, Any]) -> None:
        story = _object(payload, "story")
        checks = _object(payload, "skill_checks")
        inventory = _object(payload, "inventory")
        preserve_from = payload.get("preserve_from")
        if preserve_from is not None and not isinstance(
            preserve_from,
            str,
        ):
            raise ValueError("preserve_from must be a string or null")

        raw_assets = payload.get("assets", {})
        if not isinstance(raw_assets, dict):
            raise ValueError("assets must be an object")

        assets: dict[str, bytes] = {}
        for name, encoded in raw_assets.items():
            if not isinstance(encoded, str):
                raise ValueError(
                    f"assets.{name}: must be base64 text"
                )
            try:
                assets[str(name)] = base64.b64decode(
                    encoded,
                    validate=True,
                )
            except ValueError as exc:
                raise ValueError(
                    f"assets.{name}: invalid base64"
                ) from exc

        path = self.repository.save(
            story,
            checks,
            inventory,
            assets,
            preserve_from=preserve_from,
        )
        self._json_response(
            200,
            {
                "saved": True,
                "path": str(path),
                "world": story["name"],
                "source_format": "canonical",
            },
        )

    def _asset_response(
        self,
        world: str,
        asset_name: str,
    ) -> None:
        data = self.repository.read_asset(
            world,
            asset_name,
        )
        content_type = (
            mimetypes.guess_type(asset_name)[0]
            or "application/octet-stream"
        )
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header(
            "Content-Length",
            str(len(data)),
        )
        self.end_headers()
        self.wfile.write(data)

    def _serve_static(self, path: str) -> None:
        relative = (
            urllib.parse.unquote(path.lstrip("/"))
            or "index.html"
        )
        candidate = (STATIC_ROOT / relative).resolve()
        root = STATIC_ROOT.resolve()
        if not candidate.is_relative_to(root) or not candidate.is_file():
            raise FileNotFoundError(path)

        data = candidate.read_bytes()
        content_type = (
            mimetypes.guess_type(candidate.name)[0]
            or "application/octet-stream"
        )
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header(
            "Content-Length",
            str(len(data)),
        )
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(
                self.headers.get("Content-Length", "0")
            )
        except ValueError as exc:
            raise ValueError(
                "invalid Content-Length"
            ) from exc

        if length <= 0 or length > MAX_REQUEST_BYTES:
            raise ValueError(
                "request body is missing or too large"
            )

        try:
            payload = json.loads(
                self.rfile.read(length).decode("utf-8")
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                "request body is not valid JSON"
            ) from exc

        if not isinstance(payload, dict):
            raise ValueError(
                "request body must be a JSON object"
            )
        return payload

    def _json_response(
        self,
        status: int,
        payload: dict[str, Any],
    ) -> None:
        raw = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )
        self.send_header(
            "Content-Length",
            str(len(raw)),
        )
        self.end_headers()
        self.wfile.write(raw)


def _string(
    payload: dict[str, Any],
    key: str,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"{key} must be a non-empty string"
        )
    return value


def _object(
    payload: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value
