from __future__ import annotations

import threading
import webbrowser

from app import create_app

app = create_app()


def open_browser() -> None:
    webbrowser.open_new("http://127.0.0.1:5000/")


if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    print("Server starting... Browser will open automatically.")
    app.run(debug=False)
