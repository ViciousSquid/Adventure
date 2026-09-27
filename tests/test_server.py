import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from server import create_server
from storage.package import PackageWriter
from storage.repository import WorldRepository


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        story = {
            "schema_version": 3,
            "name": "Server",
            "start_room": "start",
            "rooms": {
                "start": {"description": "Start"},
                "end": {"description": "End"},
            },
            "connections": {
                "start__end": {
                    "from": "start",
                    "to": "end",
                    "label": "Go",
                }
            },
            "revisits": {},
            "metadata": {},
        }
        PackageWriter.write(
            self.root / "Server.canonical.zip",
            story,
            {"schema_version": 1, "skill_checks": {}},
            {
                "schema_version": 1,
                "items": {},
                "room_items": {},
                "room_requirements": {},
            },
        )
        self.server = create_server(
            WorldRepository(self.root),
            host="127.0.0.1",
            port=0,
        )
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()

    def request(self, method, path, payload=None):
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            self.server.server_port,
        )
        body = None
        headers = {}
        if payload is not None:
            body = json.dumps(payload)
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        connection.close()
        return response.status, raw

    def test_world_and_game_api_are_json(self):
        status, raw = self.request("GET", "/api/world/Server")
        self.assertEqual(status, 200)
        payload = json.loads(raw)
        self.assertEqual(payload["story"]["name"], "Server")
        self.assertEqual(payload["skill_checks"]["schema_version"], 1)

        status, raw = self.request(
            "POST",
            "/api/game/new",
            {"world": "Server"},
        )
        self.assertEqual(status, 200)
        payload = json.loads(raw)
        self.assertEqual(payload["state"]["current_room"], "start")

        state = payload["state"]
        status, raw = self.request(
            "POST",
            "/api/game/step",
            {
                "world": "Server",
                "state": state,
                "action": "start__end",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            json.loads(raw)["state"]["current_room"],
            "end",
        )

    def test_malformed_json_is_rejected(self):
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            self.server.server_port,
        )
        connection.request(
            "POST",
            "/api/game/new",
            body="{",
            headers={
                "Content-Type": "application/json",
                "Content-Length": "1",
            },
        )
        response = connection.getresponse()
        self.assertEqual(response.status, 400)
        connection.close()
