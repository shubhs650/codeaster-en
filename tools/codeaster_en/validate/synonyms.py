"""Forbidden-synonym scan over ``en/**/*.md`` (CLAUDE.md §2.3, ARCHITECTURE.md §4.1).

Every ``aliases_en`` string in the glossary is an English word we must not use for that
French term. The scan reports each one found in Markdown prose, case-insensitively, as a whole
word (a plural ``s``/``es`` counts too).

Not scanned: fenced code blocks and inline code spans (they hold ``.comm`` fragments and
French identifiers), and matches written entirely in upper case (``MODELISATION`` is a
keyword, not prose). A line can allow one word on purpose with an HTML comment
``<!-- caen-allow: reference -->``, for the cases where the word is right in its own sense.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_FENCE = re.compile(r"^\s*(```|~~~)")
_CODE_SPAN = re.compile(r"(`+)(.+?)\1")
_ALLOW = re.compile(r"<!--\s*caen-allow:\s*([^>]*?)\s*-->", re.IGNORECASE)


@dataclass(frozen=True)
class Alias:
    alias: str
    fr: str
    en: str
    pattern: re.Pattern[str]


def aliases(entries: Any) -> list[Alias]:
    """Every forbidden synonym in a parsed glossary, longest first."""
    found: list[Alias] = []
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        for alias in entry.get("aliases_en") or []:
            if not isinstance(alias, str) or not alias.strip():
                continue
            words = r"\s+".join(re.escape(w) for w in alias.split())
            pattern = re.compile(rf"(?<!\w){words}(?:e?s)?(?!\w)", re.IGNORECASE)
            found.append(Alias(alias, str(entry.get("fr")), str(entry.get("en")), pattern))
    return sorted(found, key=lambda a: -len(a.alias))


def _prose_lines(text: str) -> list[tuple[int, str]]:
    """``(line number, text)`` outside fenced code, with inline code blanked out."""
    lines: list[tuple[int, str]] = []
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        opening = _FENCE.match(line)
        if fence is not None:
            if opening and opening.group(1) == fence:
                fence = None
            continue
        if opening:
            fence = opening.group(1)
            continue
        lines.append((number, _CODE_SPAN.sub(lambda m: " " * len(m.group(0)), line)))
    return lines


def scan_text(text: str, forbidden: list[Alias]) -> list[tuple[int, Alias, str]]:
    """``(line, alias, matched text)`` for every forbidden synonym in ``text``."""
    hits: list[tuple[int, Alias, str]] = []
    for number, line in _prose_lines(text):
        allowed = {w.strip().lower() for m in _ALLOW.finditer(line) for w in m.group(1).split(",")}
        taken: list[tuple[int, int]] = []
        for alias in forbidden:
            if alias.alias.lower() in allowed:
                continue
            for match in alias.pattern.finditer(line):
                word = match.group(0)
                if word.isupper():
                    continue
                if any(s < match.end() and match.start() < e for s, e in taken):
                    continue  # already reported as part of a longer alias
                taken.append(match.span())
                hits.append((number, alias, word))
    return hits


def scan_tree(root: Path, forbidden: list[Alias]) -> tuple[list[str], int]:
    """``(issues, files scanned)`` for ``root/**/*.md``."""
    issues: list[str] = []
    files = sorted(root.rglob("*.md")) if root.is_dir() else []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for number, alias, word in scan_text(text, forbidden):
            issues.append(
                f"{path}:{number}: forbidden synonym {word!r} "
                f"(glossary {alias.fr!r} -> {alias.en!r})"
            )
    return issues, len(files)
