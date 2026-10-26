"""Message catalogue validator: ``en/messages/<FAMILY>.en.json``.

Rules (CLAUDE.md §2.4–2.5, TRANSLATION-GUIDE.md §3):

- the file parses, ``family`` matches the file name and each ``id`` is ``<FAMILY>_<N>``;
- ``placeholders`` is what :func:`codeaster_en.placeholders.parse` finds in ``fr`` (catches a
  hand-edited ``fr``; the extractor owns both);
- when ``en`` is set: it is a non-empty string, a valid mapping format (no stray ``%``), and
  uses exactly the same set of specifiers as ``fr``, each character for character;
- when ``en`` is set, ``method`` is ``machine``, ``assisted`` or ``reviewed``; ``reviewed``
  also needs ``reviewed_by`` and ``reviewed_on`` (provenance, ADR-006).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from codeaster_en import placeholders
from codeaster_en.extract.messages import SUFFIX

METHODS = frozenset({"machine", "assisted", "reviewed"})


def check_family(doc: Any, family: str) -> list[str]:
    """Problems in one parsed family document; ``family`` comes from the file name."""
    if not isinstance(doc, dict) or not isinstance(doc.get("messages"), dict):
        return ["top level must be an object with a 'messages' object"]
    issues: list[str] = []
    if doc.get("family") != family:
        issues.append(f"'family' is {doc.get('family')!r}, file name says {family!r}")
    for number, msg in doc["messages"].items():
        where = f"{family}_{number}"
        if not isinstance(msg, dict) or not isinstance(msg.get("fr"), str):
            issues.append(f"{where}: message must be an object with a string 'fr'")
            continue
        if msg.get("id") != where:
            issues.append(f"{where}: 'id' is {msg.get('id')!r}")
        parsed_fr = placeholders.parse(msg["fr"])
        issues.extend(f"{where}: fr: {err}" for err in parsed_fr.errors)
        if msg.get("placeholders") != parsed_fr.tokens:
            issues.append(
                f"{where}: 'placeholders' {msg.get('placeholders')!r} does not match fr "
                f"{parsed_fr.tokens!r} (re-run `caen extract messages`)"
            )
        en = msg.get("en")
        if en is None:
            continue
        if not isinstance(en, str) or not en.strip():
            issues.append(f"{where}: 'en' must be null or a non-empty string")
            continue
        issues.extend(f"{where}: {p}" for p in placeholders.compare(msg["fr"], en))
        method = msg.get("method")
        if method not in METHODS:
            issues.append(f"{where}: 'method' must be one of {sorted(METHODS)}, got {method!r}")
        elif method == "reviewed" and not (msg.get("reviewed_by") and msg.get("reviewed_on")):
            issues.append(f"{where}: method 'reviewed' needs 'reviewed_by' and 'reviewed_on'")
    return issues


def validate_dir(directory: Path) -> tuple[list[str], int, int]:
    """``(issues, families, translated)`` for every ``*.en.json`` file in ``directory``."""
    issues: list[str] = []
    families = translated = 0
    for path in sorted(directory.glob(f"*{SUFFIX}")):
        families += 1
        family = path.name[: -len(SUFFIX)]
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            issues.append(f"{path}: cannot read: {exc}")
            continue
        issues.extend(f"{path}: {issue}" for issue in check_family(doc, family))
        if isinstance(doc, dict) and isinstance(doc.get("messages"), dict):
            translated += sum(
                1 for m in doc["messages"].values() if isinstance(m, dict) and m.get("en")
            )
    return issues, families, translated
