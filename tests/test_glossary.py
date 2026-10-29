"""Glossary validator: the committed glossary passes, and each rule catches its violation."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from codeaster_en.cli import app
from codeaster_en.validate import glossary

REPO = Path(__file__).resolve().parents[1]
GLOSSARY = REPO / "en" / "glossary.yaml"


def _entry(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {"fr": "MAILLAGE", "en": "mesh", "kind": "term", "status": "proposed"}
    base.update(overrides)
    return base


def _messages(entries: object) -> list[str]:
    return [issue.message for issue in glossary.check(entries)]


def test_committed_glossary_is_valid() -> None:
    assert glossary.validate(GLOSSARY) == []


def test_committed_glossary_keeps_yaml11_booleans_as_strings() -> None:
    # `fr: NO` (noeud) would load as False under PyYAML's default YAML 1.1 resolver.
    entries = glossary.load(GLOSSARY)
    assert "NO" in {e["fr"] for e in entries}
    assert all(isinstance(e["fr"], str) for e in entries)


def test_committed_glossary_has_no_reviewed_entries_without_owner() -> None:
    # Only the owner marks entries reviewed; this guards against agents doing it silently.
    reviewed = [e["fr"] for e in glossary.load(GLOSSARY) if e.get("status") == "reviewed"]
    assert reviewed == []


def test_valid_minimal_glossary() -> None:
    assert glossary.check([_entry(), _entry(fr="NOEUD", en="node")]) == []


def test_top_level_must_be_list() -> None:
    assert _messages({"fr": "x"}) == ["top level must be a list of entries"]


def test_entry_must_be_mapping() -> None:
    assert _messages(["MAILLAGE"]) == ["entry must be a mapping"]


def test_duplicate_fr_rejected() -> None:
    msgs = _messages([_entry(), _entry(en="grid")])
    assert msgs == ["duplicate 'fr' (first at entry 0)"]


@pytest.mark.parametrize("fr", [None, "", "   ", False, 3])
def test_fr_must_be_nonempty_string(fr: object) -> None:
    msgs = _messages([_entry(fr=fr)])
    assert len(msgs) == 1 and msgs[0].startswith("'fr' must be a non-empty string")


@pytest.mark.parametrize("en", [None, "", "  "])
def test_en_must_be_nonempty(en: object) -> None:
    msgs = _messages([_entry(en=en)])
    assert len(msgs) == 1 and msgs[0].startswith("'en' must be a non-empty string")


def test_missing_en_rejected() -> None:
    entry = _entry()
    del entry["en"]
    assert _messages([entry])[0].startswith("'en' must be a non-empty string")


@pytest.mark.parametrize("kind", [None, "keywords", "Command", "verb"])
def test_kind_must_be_allowed(kind: object) -> None:
    msgs = _messages([_entry(kind=kind)])
    assert len(msgs) == 1 and msgs[0].startswith("'kind' must be one of")


@pytest.mark.parametrize("kind", sorted(glossary.KINDS))
def test_every_allowed_kind_accepted(kind: str) -> None:
    assert glossary.check([_entry(kind=kind)]) == []


def test_status_must_be_allowed() -> None:
    msgs = _messages([_entry(status="approved")])
    assert len(msgs) == 1 and msgs[0].startswith("'status' must be one of")


def test_aliases_must_not_contain_en() -> None:
    msgs = _messages([_entry(aliases_en=["grid", "mesh"])])
    assert msgs == ["'aliases_en' forbids the entry's own 'en' 'mesh'"]


def test_duplicate_en_within_commands_rejected() -> None:
    entries = [
        _entry(fr="DEBUT", en="begin study", kind="command"),
        _entry(fr="POURSUITE", en="begin study", kind="command"),
    ]
    assert _messages(entries) == ["duplicate command 'en' 'begin study' (first at entry 0)"]


def test_duplicate_en_allowed_outside_commands() -> None:
    # The seed glossary maps both raideur and rigidité to "stiffness"; that is legitimate.
    entries = [
        _entry(fr="raideur", en="stiffness"),
        _entry(fr="rigidité", en="stiffness"),
        _entry(fr="RIGI", en="stiffness", kind="abbrev"),
    ]
    assert glossary.check(entries) == []


def test_issue_reports_position_and_fr() -> None:
    (issue,) = glossary.check([_entry(), _entry(en="grid")])
    assert str(issue) == "entry 1 (fr='MAILLAGE'): duplicate 'fr' (first at entry 0)"


def test_unreadable_file_reported(tmp_path: Path) -> None:
    (issue,) = glossary.validate(tmp_path / "missing.yaml")
    assert issue.index == -1 and "cannot read" in issue.message


def test_cli_validate_glossary_ok() -> None:
    result = CliRunner().invoke(app, ["validate", "glossary", str(GLOSSARY)])
    assert result.exit_code == 0, result.output
    assert "glossary: OK" in result.output


def test_cli_validate_glossary_fails_on_bad_file(tmp_path: Path) -> None:
    bad = tmp_path / "glossary.yaml"
    bad.write_text(
        "- {fr: DEBUT, en: begin study, kind: command}\n- {fr: DEBUT, en: '', kind: verb}\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(app, ["validate", "glossary", str(bad)])
    assert result.exit_code == 1
    assert "3 problem(s)" in result.output


def test_cli_lists_stub_subcommands() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("extract", "translate", "validate", "mess", "report", "upstream", "bundle"):
        assert name in result.output


def test_cli_stub_exits_nonzero() -> None:
    result = CliRunner().invoke(app, ["mess"])
    assert result.exit_code == 2
    assert "not implemented yet" in result.output
