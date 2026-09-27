from __future__ import annotations

import html
import re

from markupsafe import Markup


def render_markup(text: str) -> Markup:
    safe = html.escape(text or "")
    safe = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"\*(.*?)\*", r"<em>\1</em>", safe)
    return Markup(safe.replace("\n", "<br>"))
