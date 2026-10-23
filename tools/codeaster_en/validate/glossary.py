"""Glossary validator: structural checks on ``en/glossary.yaml``.

Rules (CLAUDE.md §2.3, ARCHITECTURE.md §4.1):

- every entry is a mapping with a non-empty string ``fr``, unique across the file;
- ``en`` is a non-empty string;
- ``kind`` is one of :data:`KINDS`;
- ``status`` (if present) is one of :data:`STATUSES`;
- ``aliases_en`` (if present) is a list of strings and does not contain ``en`` itself;
- no two ``kind: command`` entries share the same ``en``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

KINDS = frozenset({"command", "keyword", "value", "concept", "term", "abbrev"})
STATUSES = frozenset({"proposed", "machine", "reviewed"})


class _Yaml12Loader(yaml.SafeLoader):
    """SafeLoader that only treats ``true``/``false`` as booleans (YAML 1.2 core schema).

    PyYAML follows YAML 1.1, where bare ``NO``, ``ON``, ``Y``… become booleans. The glossary
    has French abbreviations such as ``fr: NO`` (noeud) that must stay strings.
    """


_Yaml12Loader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:bool"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_Yaml12Loader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


@dataclass(frozen=True)
class Issue:
    """One validation problem. ``index`` is the 0-based entry position, -1 for file-level."""

    index: int
    fr: str | None
    message: str

    def __str__(self) -> str:
        where = f"entry {self.index}" if self.index >= 0 else "file"
        if self.fr is not None:
            where += f" (fr={self.fr!r})"
        return f"{where}: {self.message}"


def load(path: Path) -> Any:
    """Parse a glossary file with YAML 1.2 boolean semantics."""
    with path.open(encoding="utf-8") as fh:
        return yaml.load(fh, Loader=_Yaml12Loader)


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def check(entries: Any) -> list[Issue]:
    """Return every problem found in already-parsed glossary data (empty list = valid)."""
    if not isinstance(entries, list):
        return [Issue(-1, None, "top level must be a list of entries")]

    issues: list[Issue] = []
    first_fr: dict[str, int] = {}
    first_command_en: dict[str, int] = {}

    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            issues.append(Issue(i, None, "entry must be a mapping"))
            continue

        fr = entry.get("fr")
        label = fr if isinstance(fr, str) else None
        if not _is_text(fr):
            issues.append(Issue(i, label, f"'fr' must be a non-empty string, got {fr!r}"))
        elif fr in first_fr:
            issues.append(Issue(i, label, f"duplicate 'fr' (first at entry {first_fr[fr]})"))
        else:
            first_fr[fr] = i

        en = entry.get("en")
        if not _is_text(en):
            issues.append(Issue(i, label, f"'en' must be a non-empty string, got {en!r}"))

        kind = entry.get("kind")
        if kind not in KINDS:
            issues.append(Issue(i, label, f"'kind' must be one of {sorted(KINDS)}, got {kind!r}"))

        if "status" in entry and entry["status"] not in STATUSES:
            issues.append(
                Issue(
                    i, label, f"'status' must be one of {sorted(STATUSES)}, got {entry['status']!r}"
                )
            )

        aliases = entry.get("aliases_en", [])
        if not isinstance(aliases, list) or not all(_is_text(a) for a in aliases):
            issues.append(Issue(i, label, "'aliases_en' must be a list of non-empty strings"))
        elif _is_text(en) and en in aliases:
            issues.append(Issue(i, label, f"'aliases_en' forbids the entry's own 'en' {en!r}"))

        if kind == "command" and _is_text(en):
            if en in first_command_en:
                issues.append(
                    Issue(
                        i,
                        label,
                        f"duplicate command 'en' {en!r} (first at entry {first_command_en[en]})",
                    )
                )
            else:
                first_command_en[en] = i

    return issues


def validate(path: Path) -> list[Issue]:
    """Load and check a glossary file."""
    try:
        data = load(path)
    except (OSError, yaml.YAMLError) as exc:
        return [Issue(-1, None, f"cannot read {path}: {exc}")]
    return check(data)
