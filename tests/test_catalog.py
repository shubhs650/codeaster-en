"""Tests for ``caen extract catalog`` (task 1.2).

The committed ``en/commands/*.json`` files are the snapshots: one fresh extraction must
reproduce every one of them byte for byte. The hand-written checks below pin facts read
directly from the upstream catalog source, so a snapshot cannot drift into a wrong shape
unnoticed.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from codeaster_en.cli import app
from codeaster_en.extract import catalog

REPO = Path(__file__).resolve().parents[1]
UPSTREAM = REPO / "upstream"
COMMANDS = REPO / "en" / "commands"
SCHEMA = REPO / "docs" / "schemas" / "command.schema.json"
SNAPSHOTS = ("AFFE_MODELE", "DEFI_MATERIAU", "MECA_STATIQUE")


@pytest.fixture(scope="module")
def extracted() -> dict[str, dict]:
    if not (UPSTREAM / catalog.COMMANDS_RELDIR).is_dir():
        pytest.skip("upstream/ submodule not checked out")
    docs = catalog.extract(UPSTREAM)
    provenance = catalog.upstream_provenance(REPO)
    return {name: catalog.with_provenance(doc, provenance) for name, doc in docs.items()}


def _keyword(doc: dict, path: str) -> dict:
    found = [k for k in catalog.iter_keywords(doc["keywords"]) if k["path"] == path]
    assert found, f"{doc['command']}: no keyword {path}"
    return found[0]


def _source_line(rel: str, line: int) -> str:
    return (UPSTREAM / rel).read_text(encoding="utf-8").splitlines()[line - 1]


# --- whole catalog -------------------------------------------------------------------


def test_all_commands_extracted(extracted: dict[str, dict]) -> None:
    # docs/INVENTORY.md §1: 268 commands (135 OPER, 116 MACRO, 16 PROC, 1 FORM).
    kinds = [doc["kind"] for doc in extracted.values()]
    assert len(extracted) == 268
    assert (kinds.count("OPER"), kinds.count("MACRO"), kinds.count("PROC")) == (135, 116, 16)
    assert kinds.count("FORM") == 1
    assert "VARIABLE" not in extracted


def test_keyword_counts_match_inventory(extracted: dict[str, dict]) -> None:
    # docs/INVENTORY.md §1: 17,595 SIMP, 1,322 FACT, 2,847 BLOC (Commons expanded).
    counts = {"simple": 0, "factor": 0, "bloc": 0}
    for doc in extracted.values():
        for ent in catalog.iter_keywords(doc["keywords"]):
            counts[ent["kind"]] += 1
    assert counts == {"simple": 17595, "factor": 1322, "bloc": 2847}
    assert sum(1 for doc in extracted.values() if doc["fr"]) == 258


def test_every_object_has_a_source_line(extracted: dict[str, dict]) -> None:
    for doc in extracted.values():
        assert doc["source"] is not None, doc["command"]
        for ent in catalog.iter_keywords(doc["keywords"]):
            assert ent["source"] is not None, f"{doc['command']} {ent['path']}"


def test_committed_files_are_up_to_date(extracted: dict[str, dict]) -> None:
    committed = {p.stem for p in COMMANDS.glob("*.json")}
    assert committed == set(extracted), "run `caen extract catalog`"
    stale = [
        name
        for name, doc in extracted.items()
        if (COMMANDS / f"{name}.json").read_text(encoding="utf-8") != catalog.render(doc)
    ]
    assert not stale, f"stale en/commands files (run `caen extract catalog`): {stale[:10]}"


def test_committed_files_validate_against_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    files = sorted(COMMANDS.glob("*.json"))
    assert files
    for path in files:
        errors = list(validator.iter_errors(json.loads(path.read_text(encoding="utf-8"))))
        assert not errors, f"{path.name}: {errors[0].message} at {list(errors[0].path)}"


def test_extraction_writes_nothing_under_upstream(extracted: dict[str, dict]) -> None:
    status = subprocess.run(
        ["git", "-C", str(UPSTREAM), "status", "--porcelain", "--ignored"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert status == ""


# --- snapshots: AFFE_MODELE, DEFI_MATERIAU, MECA_STATIQUE -----------------------------


@pytest.mark.parametrize("name", SNAPSHOTS)
def test_snapshot(extracted: dict[str, dict], name: str) -> None:
    expected = (COMMANDS / f"{name}.json").read_text(encoding="utf-8")
    assert catalog.render(extracted[name]) == expected


@pytest.mark.parametrize("name", SNAPSHOTS)
def test_snapshot_sources_point_at_the_definition(extracted: dict[str, dict], name: str) -> None:
    doc = extracted[name]
    assert f"{name} = " in _source_line(doc["source"]["file"], doc["source"]["line"])
    assert doc["_generated_from"]["file"] == doc["source"]["file"]
    constructor = {"simple": "SIMP(", "factor": "FACT(", "bloc": "BLOC("}
    for ent in catalog.iter_keywords(doc["keywords"]):
        line = _source_line(ent["source"]["file"], ent["source"]["line"])
        assert constructor[ent["kind"]] in line, f"{ent['path']}: {line!r}"


def test_affe_modele(extracted: dict[str, dict]) -> None:
    doc = extracted["AFFE_MODELE"]
    assert doc["kind"] == "OPER"
    assert doc["op"] == 18
    assert doc["result_types"] == ["modele_sdaster"]
    assert doc["rules"] == [{"rule": "AU_MOINS_UN", "keywords": ["AFFE", "AFFE_SOUS_STRUC"]}]
    maillage = _keyword(doc, "MAILLAGE")
    assert (maillage["status"], maillage["type"]) == ("o", ["maillage_sdaster"])
    info = _keyword(doc, "INFO")
    assert (info["default"], info["into"]) == (1, [1, 2])
    affe = _keyword(doc, "AFFE")
    assert (affe["kind"], affe["max"]) == ("factor", "**")
    assert affe["rules"] == [{"rule": "UN_PARMI", "keywords": ["TOUT", "GROUP_MA"]}]
    # Blocs do not add a path segment: MODELISATION is written directly under AFFE.
    meca = _keyword(doc, "AFFE/[b_mecanique]")
    assert meca["condition"] == "equal_to(\"PHENOMENE\", 'MECANIQUE')"
    modelisations = [k for k in meca["keywords"] if k["name"] == "MODELISATION"][0]
    assert modelisations["path"] == "AFFE/MODELISATION"
    assert {"3D", "DKT", "COQUE_3D", "POU_D_T"} <= set(modelisations["into"])
    longueur = _keyword(doc, "GRANDEUR_CARA/LONGUEUR")
    assert (longueur["val_min"], longueur["fr"]) == (0, "Longueur caractéristique")
    assert doc["translation_upstream"]["AFFE_MODELE"] == "Assign finite element"


def test_defi_materiau(extracted: dict[str, dict]) -> None:
    doc = extracted["DEFI_MATERIAU"]
    elas = _keyword(doc, "ELAS")
    assert {"rule": "UN_PARMI", "keywords": ["E", "K", "CELE_P"]} in elas["rules"]
    assert {"rule": "ENSEMBLE", "keywords": ["E", "NU"]} in elas["rules"]
    nu = _keyword(doc, "ELAS/NU")
    assert (nu["type"], nu["val_min"], nu["val_max"]) == (["R"], -1.0, 0.5)
    # enum= is kept verbatim next to into= (defi_materiau.py, DECOLLEMENT).
    decollement = [
        k
        for k in catalog.iter_keywords(doc["keywords"])
        if k["name"] == "DECOLLEMENT" and "enum" in k
    ]
    assert decollement and decollement[0]["into"] == ["OUI", "NON"]
    assert decollement[0]["enum"] == [1, 2]


def test_meca_statique(extracted: dict[str, dict]) -> None:
    doc = extracted["MECA_STATIQUE"]
    assert doc["kind"] == "MACRO"
    assert doc["reentrant"] == "f:RESULTAT"
    assert doc["result_types"] == ["evol_elas"]
    # UN_PARMI with a default value (INST=0.0 when neither INST nor LIST_INST is given).
    assert {
        "rule": "UN_PARMI",
        "keywords": ["INST", "LIST_INST"],
        "defaults": {"INST": 0.0},
    } in doc["rules"]
    # SOLVEUR comes from the shared factory C_SOLVEUR; its source is the Commons file.
    solveur = _keyword(doc, "SOLVEUR")
    assert solveur["source"]["file"] == "code_aster/Cata/Commons/c_solveur.py"
    renum = _keyword(doc, "SOLVEUR/RENUM")
    assert renum["path"] == "SOLVEUR/RENUM"
    assert _keyword(doc, "SOLVEUR/[b_mumps]")["kind"] == "bloc"


def test_unrecognised_arguments_are_kept_verbatim(extracted: dict[str, dict]) -> None:
    # post_jmod.py writes `default="JMOD"` (not `defaut=`); the extractor must not treat
    # it as a default, and must not drop it either.
    option = _keyword(extracted["POST_JMOD"], "OPTION")
    assert "default" not in option
    assert option["other"] == {"default": "JMOD"}


# --- helpers and CLI ------------------------------------------------------------------


def test_value_encoding() -> None:
    assert catalog._value((1, 2.5, "A")) == [1, 2.5, "A"]
    assert catalog._value(1 + 2j) == {"complex": [1.0, 2.0]}
    assert catalog._value(float("inf")) == {"float": "inf"}
    assert catalog._value(int) == "int"
    assert catalog._value({"A": (1,)}) == {"A": [1]}


def test_cli_extract_one_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if not (UPSTREAM / catalog.COMMANDS_RELDIR).is_dir():
        pytest.skip("upstream/ submodule not checked out")
    monkeypatch.chdir(REPO)
    result = CliRunner().invoke(app, ["extract", "catalog", "AFFE_MODELE", "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "wrote 1 command file(s)" in result.output
    written = (tmp_path / "AFFE_MODELE.json").read_text(encoding="utf-8")
    assert written == (COMMANDS / "AFFE_MODELE.json").read_text(encoding="utf-8")


def test_cli_unknown_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if not (UPSTREAM / catalog.COMMANDS_RELDIR).is_dir():
        pytest.skip("upstream/ submodule not checked out")
    monkeypatch.chdir(REPO)
    result = CliRunner().invoke(
        app, ["extract", "catalog", "NOT_A_COMMAND", "--out", str(tmp_path)]
    )
    assert result.exit_code == 1
    assert "NOT_A_COMMAND" in result.output
