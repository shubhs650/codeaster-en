"""English guide checks (task 2.4): cited files and lines exist, modeling values are real."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
GUIDE = REPO / "en" / "guide"
UPSTREAM = REPO / "upstream"
MODELISATIONS = GUIDE / "modelisations.md"
# The values PLAN.md task 2.4 asks the guide to cover.
PLAN_VALUES = {"3D", "3D_SI", "DKT", "DST", "COQUE_3D", "C_PLAN", "D_PLAN", "AXIS", "POU_D_T"}

# `path:line` or `path:line`, `:line2` inside a code span; paths start at the repo root.
_CITATION = re.compile(r"`((?:upstream|tests|en|docs)/[^`:\s]+?)(?::(\d+))?`")
_EXTRA_LINES = re.compile(r"`:(\d+)`")

needs_upstream = pytest.mark.skipif(
    not (UPSTREAM / "code_aster").is_dir(), reason="upstream submodule not checked out"
)


def _guides() -> list[Path]:
    return sorted(GUIDE.glob("*.md"))


def _citations(text: str) -> list[tuple[str, int | None, int]]:
    """(path, line or None, guide line number) for every cited repository path."""
    found = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in _CITATION.finditer(line):
            found.append((match.group(1), int(match.group(2)) if match.group(2) else None, lineno))
    return found


def test_guides_exist() -> None:
    assert MODELISATIONS.is_file()


@needs_upstream
@pytest.mark.parametrize("guide", _guides(), ids=lambda p: p.name)
def test_cited_files_and_lines_exist(guide: Path) -> None:
    problems = []
    for path, line, at in _citations(guide.read_text(encoding="utf-8")):
        target = REPO / path
        if not target.exists():
            problems.append(f"{guide.name}:{at}: {path} does not exist")
            continue
        if line is not None and target.is_file():
            count = len(target.read_text(encoding="utf-8", errors="replace").splitlines())
            if line > count:
                problems.append(f"{guide.name}:{at}: {path}:{line} beyond {count} lines")
    assert not problems, "\n".join(problems)


def _mechanical_modelisations() -> set[str]:
    data = json.loads((REPO / "en" / "commands" / "AFFE_MODELE.json").read_text(encoding="utf-8"))
    values: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("name") == "MODELISATION" and node.get("into"):
                values.update(node["into"])
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(data)
    return values


def test_summary_table_values_are_catalog_modelisations() -> None:
    text = MODELISATIONS.read_text(encoding="utf-8")
    table = text.split("## Summary table", 1)[1].split("\n## ", 1)[0]
    rows = [r for r in table.splitlines() if r.startswith("| `")][1:]  # skip the header
    values = {re.match(r"\| `([^`]+)`", r).group(1) for r in rows}  # type: ignore[union-attr]
    assert values == PLAN_VALUES
    assert values <= _mechanical_modelisations()


@needs_upstream
def test_summary_table_lines_point_at_catalog_entries() -> None:
    catalog = UPSTREAM / "catalo" / "cataelem" / "Commons" / "phenomenons_modelisations.py"
    lines = catalog.read_text(encoding="utf-8").splitlines()
    text = MODELISATIONS.read_text(encoding="utf-8")
    table = text.split("## Summary table", 1)[1].split("\n## ", 1)[0]
    for row in table.splitlines():
        match = re.match(r"\| `([^`]+)` \|.*\| (\d+) \|$", row)
        if match:
            value, line = match.group(1), int(match.group(2))
            assert lines[line - 1].strip() == f'"{value}",', (value, line)
