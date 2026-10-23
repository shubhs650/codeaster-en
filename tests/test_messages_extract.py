"""Tests for ``caen extract messages`` (task 1.3).

The committed ``en/messages/*.en.json`` files are the snapshots: one fresh extraction (with
the translation fields of the committed files carried over) must reproduce every one of them
byte for byte. The hand-written checks pin facts read directly from the upstream files.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from codeaster_en.cli import app
from codeaster_en.extract import messages
from codeaster_en.placeholders import parse

REPO = Path(__file__).resolve().parents[1]
UPSTREAM = REPO / "upstream"
MESSAGES = REPO / "en" / "messages"
SCHEMA = REPO / "docs" / "schemas" / "messages.schema.json"


@pytest.fixture(scope="module")
def extracted() -> dict[str, dict]:
    if not (UPSTREAM / messages.MESSAGES_RELDIR).is_dir():
        pytest.skip("upstream/ submodule not checked out")
    return messages.extract(UPSTREAM)


def _all(extracted: dict[str, dict]) -> dict[str, dict]:
    return {m["id"]: m for doc in extracted.values() for m in doc["messages"].values()}


def _source_line(rel: str, line: int) -> str:
    return (UPSTREAM / rel).read_text(encoding="utf-8").splitlines()[line - 1]


# --- counts against docs/INVENTORY.md §2 ------------------------------------------------


def test_family_and_message_counts(extracted: dict[str, dict]) -> None:
    assert len(extracted) == 277
    assert sum(len(doc["messages"]) for doc in extracted.values()) == 6890
    assert max(extracted, key=lambda f: len(extracted[f]["messages"])) == "ALGELINE6"
    assert len(extracted["ALGELINE6"]["messages"]) == 99


def test_special_forms(extracted: dict[str, dict]) -> None:
    every = _all(extracted).values()
    assert sum("flags" in m for m in every) == 41  # dict form
    not_gettext = [m for m in every if m.get("gettext") is False]
    assert len([m for m in not_gettext if "fstring_names" not in m]) == 15
    assert sorted(m["id"] for m in not_gettext if "fstring_names" in m) == [
        "POST0_55",
        "POST0_56",
    ]
    assert sorted(m["id"] for m in every if m.get("reachable") is False) == [
        "ALGORITH9_100",
        "CALCULEL3_100",
        "CALCULEL3_101",
        "XFEM_100",
    ]


def test_placeholder_occurrences(extracted: dict[str, dict]) -> None:
    # INVENTORY §2 counted 3,744 k / 1,520 i / 1,211 r and 45 %%, with a regex that needs a
    # digit in the key and skipped the two f-strings. Here: + 5 %(ktout)s, + 3 %(kN)s in
    # POST0_55/56.
    counts = {"k": 0, "i": 0, "r": 0, "%": 0}
    for msg in _all(extracted).values():
        for p in parse(msg["fr"]).placeholders:
            counts["%" if p.key is None else p.key[0]] += 1
    assert counts == {"k": 3744 + 5 + 3, "i": 1520, "r": 1211, "%": 45}


def test_every_french_text_parses(extracted: dict[str, dict]) -> None:
    for msg in _all(extracted).values():
        assert parse(msg["fr"]).errors == [], msg["id"]
        assert msg["en"] is None


# --- hand checks against the source -----------------------------------------------------


def test_plain_message(extracted: dict[str, dict]) -> None:
    msg = extracted["MECANONLINE"]["messages"]["9"]
    assert msg["id"] == "MECANONLINE_9"
    assert msg["placeholders"] == ["%(k1)s"]
    assert msg["fr"].startswith("\nVous voulez poursuivre un calcul non-linéaire")
    assert msg["fr"].endswith("sur les mailles communes.\n")
    assert _source_line("code_aster/Messages/mecanonline.py", msg["source"]["line"]) == (
        "    9: _("
    )
    assert set(msg) == {"id", "fr", "placeholders", "source", "en"}


def test_dict_form_and_tricky_widths(extracted: dict[str, dict]) -> None:
    msg = extracted["CATAMESS"]["messages"]["90"]
    assert msg["fr"] == "       %(k1)3s %(k2)-20s émise %(i1)4d fois\n"
    assert msg["placeholders"] == ["%(k1)3s", "%(k2)-20s", "%(i1)4d"]
    assert msg["flags"] == "DECORATED"
    assert "gettext" not in msg


def test_unwrapped_message(extracted: dict[str, dict]) -> None:
    msg = extracted["COUPURE"]["messages"]["4"]
    assert msg["gettext"] is False
    assert msg["placeholders"] == ["%(i1)i", "%(i2)i"]


def test_fstring_message_is_resolved(extracted: dict[str, dict]) -> None:
    msg = extracted["POST0"]["messages"]["55"]
    assert msg["fstring_names"] == ["_nota_lign_coupe_axis"]
    assert "{" not in msg["fr"]
    assert "À noter que MACR_LIGN_COUPE ne sait pas récupérer le repère" in msg["fr"]


def test_ktout_and_literal_percent(extracted: dict[str, dict]) -> None:
    every = _all(extracted)
    assert "%(ktout)s" in every["FONCT0_54"]["placeholders"]
    with_percent = [m for m in every.values() if "%%" in m["placeholders"]]
    assert with_percent and all("%%" in m["fr"] for m in with_percent)


# --- snapshots, schema, merge ----------------------------------------------------------


def test_committed_files_match_fresh_extraction(extracted: dict[str, dict]) -> None:
    provenance = messages.upstream_provenance(REPO)
    committed = sorted(p.name for p in MESSAGES.glob(f"*{messages.SUFFIX}"))
    assert committed == sorted(f"{f}{messages.SUFFIX}" for f in extracted)
    for family, doc in extracted.items():
        path = MESSAGES / f"{family}{messages.SUFFIX}"
        old = json.loads(path.read_text(encoding="utf-8"))
        fresh = messages.render(
            messages.with_provenance(messages.merge_translations(doc, old), provenance)
        )
        assert fresh == path.read_text(encoding="utf-8"), f"{path.name} is out of date"


def test_committed_files_match_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for path in sorted(MESSAGES.glob(f"*{messages.SUFFIX}")):
        errors = list(validator.iter_errors(json.loads(path.read_text(encoding="utf-8"))))
        assert not errors, f"{path.name}: {errors[0].message}"


def _doc(**fields: object) -> dict:
    entry = {"id": "DEMO_1", "fr": "Champ %(k1)s.", "placeholders": ["%(k1)s"], "en": None}
    return {"family": "DEMO", "messages": {"1": {**entry, **fields}}}


def test_merge_keeps_translation_fields() -> None:
    old = _doc(en="Field %(k1)s.", method="machine", note="check")
    merged = messages.merge_translations(_doc(), old)["messages"]["1"]
    assert (merged["en"], merged["method"], merged["note"]) == ("Field %(k1)s.", "machine", "check")
    assert "stale" not in merged


def test_merge_marks_changed_french_as_stale() -> None:
    old = _doc(en="Field %(k1)s.", method="machine")
    new = _doc(fr="Le champ %(k1)s.")
    merged = messages.merge_translations(new, old)["messages"]["1"]
    assert merged["en"] == "Field %(k1)s." and merged["stale"] is True


def test_merge_drops_removed_messages() -> None:
    old = _doc(en="Field %(k1)s.", method="machine")
    old["messages"]["2"] = {**old["messages"]["1"], "id": "DEMO_2"}
    assert list(messages.merge_translations(_doc(), old)["messages"]) == ["1"]


def test_parse_rejects_unknown_shapes(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("cata_msg = {1: tr('x')}\n", encoding="utf-8")
    with pytest.raises(messages.MessageFileError, match="bad.py:1"):
        messages.parse_file(bad)
    bad.write_text("cata_msg = {1: _('a'), 1: _('b')}\n", encoding="utf-8")
    with pytest.raises(messages.MessageFileError, match="duplicate message 1"):
        messages.parse_file(bad)
    bad.write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(messages.MessageFileError, match="cata_msg"):
        messages.parse_file(bad)


# --- CLI ---------------------------------------------------------------------------------


def test_cli_writes_selected_family_and_keeps_upstream_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not (UPSTREAM / messages.MESSAGES_RELDIR).is_dir():
        pytest.skip("upstream/ submodule not checked out")
    monkeypatch.chdir(REPO)
    result = CliRunner().invoke(app, ["extract", "messages", "catamess", "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert [p.name for p in tmp_path.iterdir()] == ["CATAMESS.en.json"]
    assert (tmp_path / "CATAMESS.en.json").read_text(encoding="utf-8") == (
        MESSAGES / "CATAMESS.en.json"
    ).read_text(encoding="utf-8")
    status = subprocess.run(
        ["git", "-C", str(UPSTREAM), "status", "--porcelain", "--ignored"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert status == ""


def test_cli_unknown_family(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    if not (UPSTREAM / messages.MESSAGES_RELDIR).is_dir():
        pytest.skip("upstream/ submodule not checked out")
    monkeypatch.chdir(REPO)
    result = CliRunner().invoke(app, ["extract", "messages", "NOPE", "--out", str(tmp_path)])
    assert result.exit_code == 1
    assert "no message family: NOPE" in result.output
