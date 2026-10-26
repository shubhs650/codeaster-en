"""Command reference check: keywords in ``en/commands/<CMD>.md`` ⊆ ``<CMD>.json``.

A reference may only document keywords that the pinned catalog defines (CLAUDE.md §2.6,
TRANSLATION-GUIDE.md §4). Every ``.md`` needs its generated ``.json`` sibling, and a
``command:`` front-matter field, when present, must name that command.

Keyword tables are Markdown tables whose first header cell is ``Keyword``. In each row the
first cell names the keyword: each code span in it, if there are any (one keyword per span),
else the whole cell text. ``PARENT / CHILD`` is the ``path``
the catalog extractor writes (``AFFE/TOUT``); spaces around ``/`` are ignored. Bloc paths
(``AFFE/[b_name]``) are not keywords and are not accepted.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from codeaster_en.extract.catalog import iter_keywords

_FENCE = re.compile(r"^\s*(```|~~~)")
_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
_CODE_SPAN = re.compile(r"(`+)(.+?)\1")
_FRONT_COMMAND = re.compile(r"^command:\s*(\S+)\s*$", re.MULTILINE)


def _cells(line: str) -> list[str]:
    body = line.strip()
    body = body[1:] if body.startswith("|") else body
    body = body[:-1] if body.endswith("|") else body
    return [cell.strip() for cell in body.split("|")]


def table_keywords(text: str) -> list[tuple[int, str]]:
    """``(line number, keyword path)`` from every keyword table in ``text``."""
    lines = text.splitlines()
    found: list[tuple[int, str]] = []
    fence: str | None = None
    i = 0
    while i < len(lines):
        opening = _FENCE.match(lines[i])
        if fence is not None:
            if opening and opening.group(1) == fence:
                fence = None
            i += 1
            continue
        if opening:
            fence = opening.group(1)
            i += 1
            continue
        is_header = (
            lines[i].lstrip().startswith("|")
            and i + 1 < len(lines)
            and _SEPARATOR.match(lines[i + 1])
            and _cells(lines[i])[0].strip("`*").lower() == "keyword"
        )
        if not is_header:
            i += 1
            continue
        i += 2
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            first = _cells(lines[i])[0]
            spans = [m.group(2) for m in _CODE_SPAN.finditer(first)]
            for name in spans or ([first] if first else []):
                found.append((i + 1, re.sub(r"\s*/\s*", "/", name.strip())))
            i += 1
    return found


def keyword_paths(doc: dict) -> set[str]:
    return {k["path"] for k in iter_keywords(doc.get("keywords", [])) if k.get("kind") != "bloc"}


def check_reference(md: Path) -> list[str]:
    command = md.stem
    sibling = md.with_suffix(".json")
    if not sibling.is_file():
        return [f"{md}: no {sibling.name} (run `caen extract catalog`)"]
    text = md.read_text(encoding="utf-8")
    issues: list[str] = []
    if text.startswith("---"):
        front = text.split("\n---", 1)[0]
        named = _FRONT_COMMAND.search(front)
        if named and named.group(1) != command:
            issues.append(f"{md}: front matter names command {named.group(1)!r}")
    known = keyword_paths(json.loads(sibling.read_text(encoding="utf-8")))
    for number, path in table_keywords(text):
        if path not in known:
            issues.append(f"{md}:{number}: keyword {path!r} is not in {sibling.name}")
    return issues


def validate_dir(directory: Path) -> tuple[list[str], int]:
    """``(issues, references checked)`` for every ``*.md`` in ``directory``."""
    files = sorted(directory.glob("*.md")) if directory.is_dir() else []
    issues = [issue for md in files for issue in check_reference(md)]
    return issues, len(files)
