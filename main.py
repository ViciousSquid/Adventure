from __future__ import annotations

import os
import threading
import webbrowser
from pathlib import Path

from server import create_server
from storage.repository import WorldRepository

ROOT = Path(__file__).resolve().parent


def open_browser(url: str) -> None:
    webbrowser.open_new(url)


def main() -> None:
    host = os.environ.get("ADVENTURE_HOST", "127.0.0.1")
    port = int(os.environ.get("ADVENTURE_PORT", "5000"))
    trace = os.environ.get("ADVENTURE_TRACE", "").lower() in {
        "1",
        "true",
        "yes",
    }
    repository = WorldRepository(ROOT / "adventures")
    url = f"http://{host}:{port}/"
    threading.Timer(
        0.6,
        open_browser,
        args=(url,),
    ).start()
    print("Adventure server starting...")
    server = create_server(
        repository,
        host=host,
        port=port,
        trace=trace,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
