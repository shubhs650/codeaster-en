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
# Patterns such as `en/messages/<FAMILY>.en.json` are not citations.
_CITATION = re.compile(r"`((?:upstream|tests|en|docs)/[^`:\s<]+?)(?::(\d+))?`")
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


# --- task 2.5: fields guide -------------------------------------------------------------------

FIELDS = GUIDE / "fields.md"
NOM_CHAM = UPSTREAM / "code_aster" / "Cata" / "Commons" / "c_nom_cham_into.py"
_SPAN = re.compile(r"`([^`]+)`")
_PAREN_TAIL = re.compile(r"^(.*?)\s*(\([^()]*\))$")


def _glossary_en() -> dict[str, str]:
    import yaml

    entries = yaml.safe_load((REPO / "en" / "glossary.yaml").read_text(encoding="utf-8"))
    return {str(e["fr"]): str(e["en"]) for e in entries}


def _labels(cell: str, count: int) -> list[str]:
    """Split 'shear force Y, Z' into ['shear force Y', 'shear force Z'] (a trailing
    parenthesis applies to every part)."""
    tail = ""
    match = _PAREN_TAIL.match(cell)
    if match and match.group(1):
        cell, tail = match.group(1), " " + match.group(2)
    parts = [p.strip() for p in cell.split(", ")] if count > 1 else [cell.strip()]
    prefix = parts[0].rsplit(" ", 1)[0] + " " if " " in parts[0] else ""
    return [(p if " " in p or not prefix else prefix + p) + tail for p in parts]


def _label_rows(text: str) -> list[tuple[list[str], str, int]]:
    """(identifiers, label cell, line) for table rows whose first cell is code spans only."""
    rows = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.startswith("| `") or len(cells) < 2:
            continue
        names = _SPAN.findall(cells[0])
        if _SPAN.sub("", cells[0]).strip(" ,.") or not names:
            continue  # e.g. "`VECT_1_X` .. `VECT_3_Z`"
        rows.append((names, cells[1], lineno))
    return rows


def test_fields_guide_exists() -> None:
    assert FIELDS.is_file()


def test_fields_labels_are_glossary_english() -> None:
    """CLAUDE.md §2.3: a label next to an identifier that has a glossary entry is its `en`."""
    glossary = _glossary_en()
    problems, checked = [], 0
    for names, cell, lineno in _label_rows(FIELDS.read_text(encoding="utf-8")):
        if cell.startswith("("):
            continue
        labels = _labels(cell, len(names))
        if len(labels) == 1:
            labels = labels * len(names)  # one label for a family: `MASS_EFFE_DX`, `_DY`, ...
        if len(labels) != len(names):
            problems.append(f"fields.md:{lineno}: {len(names)} names, labels {labels}")
            continue
        for name, label in zip(names, labels, strict=True):
            if name in glossary:
                checked += 1
                if glossary[name] != label:
                    problems.append(f"fields.md:{lineno}: {name} {label!r} != {glossary[name]!r}")
    assert not problems, "\n".join(problems)
    assert checked >= 75


@needs_upstream
def test_fields_summary_lines_point_at_field_catalog() -> None:
    lines = NOM_CHAM.read_text(encoding="utf-8").splitlines()
    table = FIELDS.read_text(encoding="utf-8").split("## Field summary", 1)[1].split("\n## ", 1)[0]
    rows = [r for r in table.splitlines() if r.startswith("| `")]
    assert len(rows) >= 20
    for row in rows:
        match = re.match(r"\| `([^`]+)` \|.*\| (\d+) \|$", row)
        assert match, row
        name, line = match.group(1), int(match.group(2))
        assert lines[line - 1].strip().startswith(f'"{name}"'), (name, line)


# --- task 5.4: engineers' guide ---------------------------------------------------------------

ENGINEERS_GUIDE = (
    "README.md",
    "concepts.md",
    "walkthrough-solid-static.md",
    "walkthrough-shell-static.md",
    "walkthrough-modal.md",
    "reading-logs.md",
    "reading-results.md",
    "faq.md",
)
# `<!-- example: <path> -->` before a fenced block: the block is that file, byte for byte.
# `<!-- example-study: <path> -->`: the block is the study form of that fixture command file
# (same commands and keywords, except DEBUT and the TEST_RESU checks).
_EXAMPLE = re.compile(r"<!-- (example|example-study): (\S+) -->\n```\w*\n(.*?)```", re.DOTALL)
_LINK = re.compile(r"\]\(([^)#\s]+\.md)(?:#([^)\s]+))?\)")


def _headings(text: str) -> list[str]:
    """ATX heading lines outside fenced code blocks."""
    found, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,6} ", line):
            found.append(line)
    return found


def _examples() -> list[tuple[str, str, str, str]]:
    found = []
    for name in ENGINEERS_GUIDE:
        for kind, path, body in _EXAMPLE.findall((GUIDE / name).read_text(encoding="utf-8")):
            found.append((name, kind, path, body))
    return found


def test_engineers_guide_pages_exist() -> None:
    for name in ENGINEERS_GUIDE:
        text = (GUIDE / name).read_text(encoding="utf-8")
        assert text.startswith("---\n"), name
        assert sum(1 for line in _headings(text) if line.startswith("# ")) == 1, name
    # The three walkthroughs carry the fixture files; the solid one is the full study.
    kinds = {(name, kind) for name, kind, _, _ in _examples()}
    assert ("walkthrough-solid-static.md", "example-study") in kinds
    assert ("walkthrough-shell-static.md", "example") in kinds
    assert ("walkthrough-modal.md", "example") in kinds


@pytest.mark.parametrize("example", _examples(), ids=lambda e: f"{e[0]}:{e[2]}")
def test_guide_examples_match_fixtures(example: tuple[str, str, str, str]) -> None:
    _, kind, path, body = example
    source = (REPO / path).read_text(encoding="utf-8")
    if kind == "example":
        assert body == source
        return

    def calls(text: str) -> list[str]:
        """Each top-level command call, as its AST dump, minus DEBUT's keywords and TEST_RESU."""
        out = []
        for node in __import__("ast").parse(text).body:
            value = getattr(node, "value", None)
            if not isinstance(value, __import__("ast").Call):
                continue
            name = getattr(value.func, "id", "")
            if name == "TEST_RESU":
                continue
            if name == "DEBUT":
                value.keywords = []
            out.append(__import__("ast").dump(node))
        return out

    assert calls(body) == calls(source)
    assert "CODE=" not in body and "TEST_RESU" not in body


def _catalog_namespace() -> dict:
    import sys

    sys.dont_write_bytecode = True  # never write into upstream/
    sys.path.insert(0, str(UPSTREAM))
    try:
        from code_aster.Cata.Commands import commandStore
    finally:
        sys.path.remove(str(UPSTREAM))
    return dict(commandStore)


@needs_upstream
def test_guide_study_comm_passes_catalog_check() -> None:
    """The walkthrough's study command file runs through the pinned catalog's syntax checker."""
    pytest.importorskip("numpy")
    for _, kind, _, body in _examples():
        if kind == "example-study":
            namespace = _catalog_namespace() | {"_F": dict}
            exec(compile(body, "walkthrough.comm", "exec"), namespace)


def _slug(heading: str) -> str:
    """GitHub's anchor for a Markdown heading."""
    text = heading.strip().lower().replace("`", "")
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def test_guide_links_resolve() -> None:
    """Relative links between guide pages and to command references point at real files and
    headings."""
    problems = []
    for name in ENGINEERS_GUIDE:
        text = (GUIDE / name).read_text(encoding="utf-8")
        for target, anchor in _LINK.findall(text):
            if target.startswith("http"):
                continue
            path = (GUIDE / target).resolve()
            if not path.is_file():
                problems.append(f"{name}: {target} does not exist")
                continue
            if anchor:
                slugs = {_slug(h.lstrip("#")) for h in _headings(path.read_text(encoding="utf-8"))}
                if anchor not in slugs:
                    problems.append(f"{name}: {target}#{anchor} has no such heading")
    assert not problems, "\n".join(problems)


def test_faq_entries_are_seen_in_fixture_logs() -> None:
    """Every message ID the FAQ table lists was printed by a committed fixture log, or is
    recorded in the fixture notes as seen on a first run."""
    text = (GUIDE / "faq.md").read_text(encoding="utf-8")
    ids = re.findall(r"^\| \[`([A-Z0-9]+_\d+)`\]", text, re.MULTILINE)
    assert len(ids) >= 7
    logs = "".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in (REPO / "tests" / "fixtures").glob("*/output*/run.mess")
    )
    notes = (REPO / "tests" / "fixtures" / "README.md").read_text(encoding="utf-8")
    for message_id in ids:
        assert f"<{message_id}>" in logs or message_id in notes, message_id
        family, number = message_id.rsplit("_", 1)
        messages = json.loads(
            (REPO / "en" / "messages" / f"{family}.en.json").read_text(encoding="utf-8")
        )["messages"]
        assert number in messages, message_id
