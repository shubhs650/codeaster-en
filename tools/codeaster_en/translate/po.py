"""Minimal gettext ``.po`` reader for upstream's ``i18n/en-US/aster_messages.po`` (ADR-004).

Only what the seed step needs: ``msgid`` → ``msgstr`` for singular, non-fuzzy entries with a
non-empty translation. ``msgctxt`` and plural entries are skipped (the 17.4.26 file has no
``msgctxt``; message texts are never plural forms). Strings are decoded with the C escapes
gettext uses (``\\n``, ``\\t``, ``\\"``, ``\\\\``).
"""

from __future__ import annotations

import re
from pathlib import Path

PO_RELPATH = Path("i18n/en-US/aster_messages.po")
SOURCE_LABEL = "upstream:i18n/en-US/aster_messages.po"

_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\", "r": "\r", "a": "\a", "b": "\b"}
_ESCAPE = re.compile(r"\\(.)")
_KEYWORD = re.compile(r"^(msgctxt|msgid|msgid_plural|msgstr(?:\[\d+\])?)\s+(\".*\")\s*$")


class PoError(ValueError):
    """The file is not a .po file this reader understands."""


def _unquote(token: str, where: str) -> str:
    if len(token) < 2 or not (token.startswith('"') and token.endswith('"')):
        raise PoError(f"{where}: expected a quoted string, got {token!r}")
    return _ESCAPE.sub(lambda m: _ESCAPES.get(m.group(1), m.group(0)), token[1:-1])


def parse(text: str, where: str = "<po>") -> dict[str, str]:
    """``{msgid: msgstr}`` for the usable entries of a .po file's text."""
    result: dict[str, str] = {}
    fields: dict[str, str] = {}
    fuzzy = False
    current: str | None = None

    def flush() -> None:
        nonlocal fields, fuzzy, current
        msgid, msgstr = fields.get("msgid"), fields.get("msgstr")
        if (
            msgid
            and msgstr
            and not fuzzy
            and "msgctxt" not in fields
            and "msgid_plural" not in fields
        ):
            result[msgid] = msgstr
        fields, fuzzy, current = {}, False, None

    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        here = f"{where}:{number}"
        if not line:
            flush()
        elif line.startswith("#"):
            if fields:
                flush()
            if line.startswith("#,") and "fuzzy" in [f.strip() for f in line[2:].split(",")]:
                fuzzy = True
        elif line.startswith('"'):
            if current is None:
                raise PoError(f"{here}: continuation line outside an entry")
            fields[current] += _unquote(line, here)
        else:
            match = _KEYWORD.match(line)
            if not match:
                raise PoError(f"{here}: cannot parse {line[:40]!r}")
            keyword, token = match.groups()
            if keyword == "msgid" and "msgid" in fields:
                flush()
            current = "msgstr" if keyword == "msgstr[0]" else keyword
            fields[current] = _unquote(token, here)
    flush()
    return result


def load(path: Path) -> dict[str, str]:
    return parse(path.read_text(encoding="utf-8"), str(path))
