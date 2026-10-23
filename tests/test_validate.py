"""Tests for ``caen validate`` (task 1.6): messages, synonyms and command-reference rules.

Glossary rules are tested in ``test_glossary.py``. ``tests/validate_fixtures/good`` must pass
every rule and ``tests/validate_fixtures/broken`` must trip each one; the defects planted in
``broken/`` are listed in :data:`BROKEN_EXPECTED`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from codeaster_en.cli import app
from codeaster_en.validate import commands, messages, synonyms

FIXTURES = Path(__file__).resolve().parent / "validate_fixtures"
REPO = Path(__file__).resolve().parents[1]

BROKEN_EXPECTED = [
    # glossary
    "entry 3 (fr='maille'): duplicate 'fr'",
    # messages: placeholder equality
    "DEMO_1: en is missing %(k1)s",
    "DEMO_2: en is missing %(k1)3s",
    "DEMO_2: en has %(k1)s, which the French does not",
    "DEMO_3: en: line 1 col 20: placeholder '% f' has no name",
    "DEMO_3: en is missing %%",
    "DEMO_3: en has % f, which the French does not",
    "DEMO_4: en has %(i1)d, which the French does not",
    # messages: provenance and structure
    "DEMO_5: 'method' must be one of",
    "DEMO_6: method 'reviewed' needs 'reviewed_by' and 'reviewed_on'",
    "DEMO_7: 'placeholders' [] does not match fr ['%(k1)s']",
    "DEMO_8: 'id' is 'DEMO_80'",
    "OTHER.en.json: 'family' is 'WRONG', file name says 'OTHER'",
    # synonyms
    "notes.md:3: forbidden synonym 'reference frame'",
    "notes.md:3: forbidden synonym 'cell'",
    "notes.md:4: forbidden synonym 'modelisation'",
    "notes.md:4: forbidden synonym 'Cells'",
    # commands
    "AFFE_MODELE.md: front matter names command 'AFFE_MODELE_X'",
    "AFFE_MODELE.md:11: keyword 'AFFE/NOT_A_KEYWORD' is not in AFFE_MODELE.json",
    "AFFE_MODELE.md:12: keyword 'MODELISATION' is not in AFFE_MODELE.json",
    "AFFE_MODELE.md:13: keyword 'AFFE/[b_mecanique]' is not in AFFE_MODELE.json",
    "NO_SUCH_CMD.md: no NO_SUCH_CMD.json",
]


def _run(monkeypatch: pytest.MonkeyPatch, where: Path, *args: str):
    monkeypatch.chdir(where)
    return CliRunner().invoke(app, ["validate", *args])


# --- whole-tree runs -----------------------------------------------------------------------


def test_good_fixture_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _run(monkeypatch, FIXTURES / "good")
    assert result.exit_code == 0, result.output
    for line in (
        "glossary: OK (3 entries)",
        "messages: OK (1 families, 2 translated)",
        "synonyms: OK (2 Markdown file(s), 4 aliases)",
        "commands: OK (1 reference(s))",
    ):
        assert line in result.output


def test_broken_fixture_trips_every_rule(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _run(monkeypatch, FIXTURES / "broken")
    assert result.exit_code == 1
    problems = [ln for ln in result.output.splitlines() if not ln.split(":")[0].isalpha()]
    for expected in BROKEN_EXPECTED:
        assert any(expected in ln for ln in problems), f"not reported: {expected}"
    assert len(problems) == len(BROKEN_EXPECTED), "\n".join(problems)
    for summary in ("glossary: 1 ", "messages: 12 ", "synonyms: 4 ", "commands: 5 "):
        assert summary in result.output


@pytest.mark.parametrize(
    ("sub", "count"), [("messages", 12), ("synonyms", 4), ("commands", 5), ("glossary", 1)]
)
def test_subcommands_fail_alone(monkeypatch: pytest.MonkeyPatch, sub: str, count: int) -> None:
    result = _run(monkeypatch, FIXTURES / "broken", sub)
    assert result.exit_code == 1
    assert f"{sub}: {count} problem(s)" in result.output


@pytest.mark.parametrize("sub", ["messages", "synonyms", "commands", "glossary"])
def test_subcommands_pass_on_good(monkeypatch: pytest.MonkeyPatch, sub: str) -> None:
    assert _run(monkeypatch, FIXTURES / "good", sub).exit_code == 0


def test_repository_itself_validates(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _run(monkeypatch, REPO)
    assert result.exit_code == 0, result.output


# --- messages rule ---------------------------------------------------------------------


def _family(**fields: object) -> dict:
    msg = {"id": "DEMO_1", "fr": "Champ %(k1)s : %(r1)12.5E.", "en": None}
    msg["placeholders"] = ["%(k1)s", "%(r1)12.5E"]
    msg.update(fields)
    return {"family": "DEMO", "messages": {"1": msg}}


def test_untranslated_message_only_needs_structure() -> None:
    assert messages.check_family(_family(), "DEMO") == []


def test_translated_message_ok() -> None:
    doc = _family(en="Field %(k1)s: %(r1)12.5E.", method="assisted")
    assert messages.check_family(doc, "DEMO") == []


def test_empty_english_rejected() -> None:
    issues = messages.check_family(_family(en="  ", method="machine"), "DEMO")
    assert issues == ["DEMO_1: 'en' must be null or a non-empty string"]


def test_format_change_rejected() -> None:
    issues = messages.check_family(_family(en="Field %(k1)s: %(r1)e.", method="machine"), "DEMO")
    assert "DEMO_1: en is missing %(r1)12.5E" in issues


def test_not_an_object() -> None:
    assert messages.check_family([], "DEMO") == [
        "top level must be an object with a 'messages' object"
    ]


# --- synonyms rule ---------------------------------------------------------------------


GLOSSARY = [
    {"fr": "maille", "en": "element", "aliases_en": ["cell", "mesh element"]},
    {"fr": "repère", "en": "coordinate system", "aliases_en": ["frame"]},
]


def _scan(text: str) -> list[str]:
    return [word for _, _, word in synonyms.scan_text(text, synonyms.aliases(GLOSSARY))]


def test_synonym_whole_words_and_plurals() -> None:
    assert _scan("one cell, two cells; Cell") == ["cell", "cells", "Cell"]
    assert _scan("cellular, excellent, framework") == []


def test_synonym_longest_alias_reported_once() -> None:
    hits = synonyms.scan_text("each mesh  element", synonyms.aliases(GLOSSARY))
    assert [(a.alias, w) for _, a, w in hits] == [("mesh element", "mesh  element")]


def test_synonym_skips_code_and_uppercase() -> None:
    text = "Use `cell` and ``a cell``.\nCELL is a name.\n```\ncell\n```\n~~~python\nframe\n~~~\n"
    assert _scan(text) == []


def test_synonym_fence_must_close_with_same_marker() -> None:
    assert _scan("```\n~~~\ncell\n```\nframe\n") == ["frame"]


def test_synonym_allow_comment() -> None:
    assert _scan("the frame of the page <!-- caen-allow: frame --> and a cell") == ["cell"]
    assert _scan("a cell and a frame <!-- caen-allow: cell, frame -->") == []


def test_synonym_line_numbers() -> None:
    hits = synonyms.scan_text("ok\n\n```\ncell\n```\nbad cell\n", synonyms.aliases(GLOSSARY))
    assert [n for n, _, _ in hits] == [6]


# --- commands rule ---------------------------------------------------------------------


def test_table_keywords_paths_and_spans() -> None:
    text = """
| Keyword | Type |
|:---|---:|
| `AFFE / TOUT`, `AFFE/GROUP_MA` | x |
| MAILLAGE | x |
|  | continuation |

| Other | Type |
|---|---|
| `NOT_CHECKED` | x |

```markdown
| Keyword | Type |
|---|---|
| `IN_CODE` | x |
```
"""
    assert commands.table_keywords(text) == [
        (4, "AFFE/TOUT"),
        (4, "AFFE/GROUP_MA"),
        (5, "MAILLAGE"),
    ]


def test_real_catalog_paths_include_bloc_keywords() -> None:
    import json

    doc = json.loads((REPO / "en" / "commands" / "AFFE_MODELE.json").read_text(encoding="utf-8"))
    paths = commands.keyword_paths(doc)
    assert {"MAILLAGE", "AFFE", "AFFE/TOUT", "AFFE/MODELISATION"} <= paths
    assert not any("[" in p for p in paths)
