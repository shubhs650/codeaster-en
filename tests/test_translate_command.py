"""Tests for ``caen translate command`` (task 2.2).

The committed Tier 1 drafts (``en/commands/<CMD>.md`` whose status is still ``machine``) are
the snapshots: one fresh run must reproduce them byte for byte. A reference an author has
taken over (``assisted``, ``reviewed``) is no longer a snapshot. The unit tests build a small
catalog document by hand so the table, rule and scope logic is pinned independently of
upstream.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from codeaster_en.cli import app
from codeaster_en.translate import command as drafts

REPO = Path(__file__).resolve().parents[1]
COMMANDS = REPO / "en" / "commands"
UPSTREAM_ASTEST = REPO / "upstream" / "astest"


@pytest.fixture(scope="module")
def sources() -> drafts.Sources:
    return drafts.load_sources(REPO)


# --- committed drafts -----------------------------------------------------------------


def test_every_tier1_command_with_a_catalog_has_a_reference(sources: drafts.Sources) -> None:
    tier1 = drafts.resolve(sources, None, "1")
    missing = [c for c in tier1 if c in sources.commands and not (COMMANDS / f"{c}.md").is_file()]
    assert missing == []
    # POURSUITE has no catalog of its own (it reuses DEBUT's), so it gets no draft.
    assert "POURSUITE" in tier1 and "POURSUITE" not in sources.commands


def test_machine_drafts_are_up_to_date(sources: drafts.Sources, tmp_path: Path) -> None:
    if not UPSTREAM_ASTEST.is_dir():
        pytest.skip("upstream/ submodule not checked out (patterns need it)")
    tier1 = [c for c in drafts.resolve(sources, None, "1") if c in sources.commands]
    machine = [c for c in tier1 if drafts.draft_status(COMMANDS / f"{c}.md") == "machine"]
    drafts.write(sources, machine, tmp_path)
    stale = [
        c
        for c in machine
        if (tmp_path / f"{c}.md").read_text(encoding="utf-8")
        != (COMMANDS / f"{c}.md").read_text(encoding="utf-8")
    ]
    assert stale == [], "re-run `caen translate command --tier 1`"


def test_tier1_help_strings_all_translated(sources: drafts.Sources) -> None:
    assert drafts.untranslated(sources, drafts.resolve(sources, None, "1")) == []


def test_drafts_front_matter(sources: drafts.Sources) -> None:
    for md in sorted(COMMANDS.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        if drafts.draft_status(md) != "machine":
            continue
        front = text.split("\n---", 1)[0]
        assert f"command: {md.stem}\n" in front
        examples = re.search(r"^examples: \[(.*)\]$", front, re.MULTILINE)
        assert examples is not None
        for case in filter(None, (c.strip() for c in examples.group(1).split(","))):
            assert md.stem in sources.index["testcases"][case]["commands"], (md.name, case)


# --- data files -----------------------------------------------------------------------


def _yaml(path: Path) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_catalog_help_entries() -> None:
    entries = _yaml(REPO / drafts.HELP_RELPATH)
    frs = [e["fr"] for e in entries]
    assert len(frs) == len(set(frs))
    for entry in entries:
        assert set(entry) <= {"fr", "en", "method", "note"}, entry
        assert entry["en"].strip() and entry["method"] in {"machine", "assisted", "reviewed"}


def test_doc_ids_entries(sources: drafts.Sources) -> None:
    for entry in _yaml(REPO / drafts.DOC_IDS_RELPATH):
        assert re.fullmatch(r"U[0-9]\.[0-9]{2}\.[0-9]{2}", entry["doc_id"]), entry
        assert entry["status"] in {"proposed", "verified"}, entry
        assert entry["command"] in sources.commands or entry["command"] == "POURSUITE"


def test_catalog_docu_wins_over_doc_ids(sources: drafts.Sources) -> None:
    doc = sources.commands["POST_RELEVE_T"]
    assert drafts.doc_id(doc, sources) == (
        "U4.81.21",
        "catalog docu= (code_aster/Cata/Commands/post_releve_t.py)",
    )


# --- unit tests on a hand-made catalog ------------------------------------------------


def _kw(path: str, kind: str = "simple", **extra) -> dict:
    return {"name": path.split("/")[-1], "kind": kind, "path": path, "fr": None, **extra}


DOC = {
    "_generated_from": {"upstream": "17.4.26", "upstream_commit": "abc"},
    "command": "DEMO",
    "kind": "OPER",
    "fr": "Commande de démonstration",
    "reentrant": "o:MAILLAGE",
    "result_types": ["maillage_sdaster"],
    "result_type_depends_on_keywords": False,
    "rules": [{"rule": "AU_MOINS_UN", "keywords": ["AFFE", "TOUT"]}],
    "source": {"file": "code_aster/Cata/Commands/demo.py", "line": 3},
    "keywords": [
        _kw("MAILLAGE", status="o", type=["maillage_sdaster"]),
        _kw("CACHE", status="c", type=["I"]),
        _kw(
            "AFFE",
            "factor",
            status="f",
            max="**",
            rules=[
                {"rule": "UN_PARMI", "keywords": ["TOUT", "GROUP_MA"], "defaults": {"TOUT": "OUI"}}
            ],
            keywords=[
                _kw("AFFE/TOUT", status="f", type=["TXM"], into=["OUI"]),
                _kw("AFFE/GROUP_MA", status="f", type=["grma"], max="**"),
            ],
        ),
        _kw("AUTRE", "factor", status="f", fr="Autre chose", keywords=[_kw("AUTRE/X")]),
        {
            "name": "b_med",
            "kind": "bloc",
            "path": "[b_med]",
            "condition": " ( equal_to(\"FORMAT\", 'MED') ) ",
            "fr": None,
            "keywords": [_kw("UNITE", status="f", type=["I"], default=20, val_min=2)],
        },
        {
            "name": "b_ideas",
            "kind": "bloc",
            "path": "[b_ideas]",
            "condition": "equal_to(\"FORMAT\", 'IDEAS')",
            "fr": None,
            "keywords": [_kw("UNITE", status="f", type=["I"], default=20, val_min=2)],
        },
    ],
}


def _sources(tmp: Path, key: list[str], help_en: dict[str, str] | None = None) -> drafts.Sources:
    return drafts.Sources(
        repo=tmp,
        commands={"DEMO": DOC},
        glossary={"MAILLAGE": {"fr": "MAILLAGE", "en": "mesh", "kind": "keyword"}},
        help_en=help_en or {},
        doc_ids={},
        index={},
        key_keywords={"DEMO": key},
        tiers={"1": ["DEMO"]},
    )


def test_table_scope_hidden_and_merged_conditions(tmp_path: Path) -> None:
    src = _sources(tmp_path, ["AFFE"])
    table = drafts.build_table(DOC, src)
    assert table.expanded_all  # 7 paths <= SMALL_COMMAND
    assert [r.path for r in table.rows] == [
        "MAILLAGE",
        "AFFE",
        "AFFE/TOUT",
        "AFFE/GROUP_MA",
        "AUTRE",
        "AUTRE/X",
        "UNITE",
    ]
    assert table.hidden == 1
    unite = table.rows[-1]
    assert unite.conditions == ["equal_to(\"FORMAT\", 'MED')", "equal_to(\"FORMAT\", 'IDEAS')"]
    assert "Range: ≥ 2." in unite.meaning and "; or " in unite.meaning
    assert table.rows[0].meaning == "*mesh*. TODO(2.3): when to use."
    assert table.rows[3].type_text == "element group, optional, list"


def test_table_large_command_keeps_key_factors_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(drafts, "SMALL_COMMAND", 3)
    src = _sources(tmp_path, ["AFFE"], {"Autre chose": "Something else."})
    table = drafts.build_table(DOC, src)
    assert not table.expanded_all
    assert "AUTRE" not in [r.path for r in table.rows]
    assert [(o.name, o.help_text) for o in table.others] == [("AUTRE", "Something else.")]
    assert drafts.build_table(DOC, src, all_keywords=True).expanded_all


def test_rules_text(tmp_path: Path) -> None:
    table = drafts.build_table(DOC, _sources(tmp_path, []))
    assert [(r.scope, r.text) for r in table.rules] == [
        ("command", "at least one of `AFFE`, `TOUT` must be given (`AU_MOINS_UN`)"),
        (
            "`AFFE`",
            "exactly one of `TOUT`, `GROUP_MA` must be given; "
            "if none is given, `TOUT='OUI'` is assumed (`UN_PARMI`)",
        ),
    ]


def test_render_marks_untranslated_help(tmp_path: Path) -> None:
    text = drafts.render("DEMO", _sources(tmp_path, []))
    assert text.startswith("---\ncommand: DEMO\n")
    assert "status: machine\n" in text
    assert "TODO(translate): «Commande de démonstration»" in text
    assert "yes (the object given in `MAILLAGE`); catalog `reentrant='o:MAILLAGE'`" in text
    assert "TODO(verify): U4 document ID unknown" in text
    assert "\n\n\n" not in text


def test_write_respects_authored_references(tmp_path: Path) -> None:
    src = _sources(tmp_path, [])
    out = tmp_path / "out"
    out.mkdir()
    authored = out / "DEMO.md"
    authored.write_text("---\ncommand: DEMO\nstatus: assisted\n---\n# DEMO\n", encoding="utf-8")
    [outcome] = drafts.write(src, ["DEMO"], out)
    assert outcome.action == "skipped" and "assisted" in outcome.reason
    assert authored.read_text(encoding="utf-8").endswith("# DEMO\n")
    assert drafts.write(src, ["DEMO"], out, force=True)[0].action == "written"
    assert drafts.write(src, ["DEMO"], out)[0].action == "unchanged"
    assert drafts.write(src, ["NOPE"], out)[0].action == "skipped"


def test_call_snippet(tmp_path: Path) -> None:
    comm = tmp_path / "case.comm"
    comm.write_text(
        "DEBUT()\nMA = LIRE_MAILLAGE(\n    FORMAT='MED',\n)\nIMPR_RESU(RESU=_F(MAILLAGE=MA))\n",
        encoding="utf-8",
    )
    assert (
        drafts.call_snippet(comm, "LIRE_MAILLAGE", 2) == "MA = LIRE_MAILLAGE(\n    FORMAT='MED',\n)"
    )
    assert drafts.call_snippet(comm, "IMPR_RESU", 5) == "IMPR_RESU(RESU=_F(MAILLAGE=MA))"
    assert drafts.call_snippet(comm, "IMPR_RESU", 2) is None


def test_pick_examples_skips_error_and_parallel_cases(tmp_path: Path) -> None:
    src = _sources(tmp_path, [])
    calls = {"DEMO": [3]}
    src.index = {
        "commands": {"DEMO": {"testcases": ["erreu01a", "par01a", "big01a", "small01a"]}},
        "testcases": {
            "erreu01a": {
                "commands": ["DEMO"],
                "command_files": [{"path": "e.comm", "calls": calls}],
            },
            "par01a": {
                "parallel": True,
                "commands": ["DEMO"],
                "command_files": [{"path": "p.comm", "calls": calls}],
            },
            "big01a": {
                "commands": ["DEMO", "X", "Y"],
                "command_files": [{"path": "b.comm", "calls": calls}],
            },
            "small01a": {
                "commands": ["DEMO"],
                "command_files": [{"path": "s.comm", "calls": calls}],
            },
        },
    }
    assert [e.case for e in drafts.pick_examples(src, "DEMO")] == ["small01a", "big01a"]


# --- CLI ------------------------------------------------------------------------------


def test_cli_needs_commands_or_tier(monkeypatch) -> None:
    monkeypatch.chdir(REPO)
    result = CliRunner().invoke(app, ["translate", "command"])
    assert result.exit_code == 1
    assert "--tier" in result.output


def test_cli_list_untranslated(monkeypatch) -> None:
    monkeypatch.chdir(REPO)
    result = CliRunner().invoke(app, ["translate", "command", "--tier", "1", "--list-untranslated"])
    assert result.exit_code == 0
    assert "0 untranslated string(s)" in result.output


def test_cli_writes_draft(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(REPO)
    result = CliRunner().invoke(app, ["translate", "command", "FIN", "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "1 written" in result.output
    assert json.loads((COMMANDS / "FIN.json").read_text(encoding="utf-8"))["command"] == "FIN"
    assert (tmp_path / "FIN.md").read_text(encoding="utf-8").startswith("---\ncommand: FIN\n")


def test_cli_messages_and_doc_are_stubs() -> None:
    for sub in ("messages", "doc"):
        result = CliRunner().invoke(app, ["translate", sub])
        assert result.exit_code == 2


def test_literal_escapes_control_characters() -> None:
    # IMPR_TABLE / FIN_LIGNE defaults to "\n"; a raw newline would split the table row.
    assert drafts._literal("\n") == "`'\\n'`"
    assert drafts._literal("a\tb") == "`'a\\tb'`"
