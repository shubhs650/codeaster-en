"""Tests for ``caen extract astest-index`` (task 1.4).

The committed ``en/astest-index.json`` is the snapshot: a fresh extraction must reproduce it
byte for byte. The five hand checks were made against the upstream files with ``grep`` (see
the PROGRESS entry for 1.4); each pins a different shape of test case.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from codeaster_en.cli import app
from codeaster_en.extract import astest
from codeaster_en.extract.catalog import upstream_provenance

REPO = Path(__file__).resolve().parents[1]
UPSTREAM = REPO / "upstream"
COMMANDS = REPO / "en" / "commands"
INDEX = REPO / astest.INDEX_RELPATH
SCHEMA = REPO / "docs" / "schemas" / "astest-index.schema.json"


@pytest.fixture(scope="module")
def index() -> dict:
    if not (UPSTREAM / astest.ASTEST_RELDIR).is_dir():
        pytest.skip("upstream/ submodule not checked out")
    return astest.extract(UPSTREAM, COMMANDS)


def _calls(case: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for cfile in case["command_files"]:
        for name, lines in cfile["calls"].items():
            counts[name] = counts.get(name, 0) + len(lines)
    return counts


def test_counts(index: dict) -> None:
    summary = index["summary"]
    assert summary["testcases"] == 4496
    assert summary["command_files"] == 4708
    assert summary["parse"] == {"ast": 4708}
    assert summary["parallel_testcases"] == 320
    assert summary["known_commands"] == 280
    # Every catalog command has at least one test case.
    unused = [name for name, info in index["commands"].items() if not info["testcases"]]
    assert unused == ["MACRO_AC_PERMUTE"]


def test_committed_index_is_up_to_date(index: dict) -> None:
    doc = astest.with_provenance(index, upstream_provenance(REPO))
    assert INDEX.read_text(encoding="utf-8") == astest.render(doc), (
        "run `caen extract astest-index`"
    )


def test_committed_index_validates_against_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    errors = list(
        jsonschema.Draft202012Validator(schema).iter_errors(
            json.loads(INDEX.read_text(encoding="utf-8"))
        )
    )
    assert not errors, f"{errors[0].message} at {list(errors[0].path)}"


def test_both_directions_agree(index: dict) -> None:
    forward = {(c, t) for t, case in index["testcases"].items() for c in case["commands"]}
    backward = {(c, t) for c, info in index["commands"].items() for t in info["testcases"]}
    assert forward == backward
    for name, info in index["commands"].items():
        assert info["calls"] == sum(_calls(c).get(name, 0) for c in index["testcases"].values())


def test_non_catalog_commands(index: dict) -> None:
    commands = index["commands"]
    assert commands["POURSUITE"]["source"] == "code_commands"
    assert commands["POURSUITE"]["defined_in"] == "code_aster/CodeCommands/debut.py"
    assert commands["DEFI_CONT"] == {
        **commands["DEFI_CONT"],
        "source": "user_macro",
        "defined_in": "code_aster/MacroCommands/defi_cont.py:215",
    }
    for name in ("CO", "VARIABLE", "_F", "MACRO_TEST"):
        assert name not in commands
    for name, info in commands.items():
        if info["source"] == "catalog":
            assert (COMMANDS / f"{name}.json").is_file()
            assert "defined_in" not in info


def test_extraction_writes_nothing_under_upstream(index: dict) -> None:
    status = subprocess.run(
        ["git", "-C", str(UPSTREAM), "status", "--porcelain", "--ignored"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert status == ""


# --- hand checks --------------------------------------------------------------------------


def test_ssls101a_shell(index: dict) -> None:
    case = index["testcases"]["ssls101a"]
    assert case["export"] == "astest/ssls101a.export"
    assert case["params"] == {
        "time_limit": 60,
        "memory_limit": 512,
        "ncpus": 1,
        "mpi_nbcpu": 1,
        "mpi_nbnoeud": 1,
        "testlist": ["verification", "sequential"],
    }
    assert case["parallel"] is False
    assert [f["path"] for f in case["command_files"]] == ["ssls101a.comm"]
    calls = case["command_files"][0]["calls"]
    assert calls["DEBUT"] == [20]
    assert calls["AFFE_MODELE"] == [47]
    assert calls["MECA_STATIQUE"] == [67]
    assert calls["FIN"] == [1337]
    assert _calls(case)["TEST_TABLE"] == 28
    assert len(case["commands"]) == 24
    assert {"kind": "F", "type": "mmed", "path": "ssls101a.mmed", "mode": "D", "unit": 20} in (
        case["files"]
    )


def test_sdll100a_dynamics(index: dict) -> None:
    case = index["testcases"]["sdll100a"]
    assert _calls(case) == {
        "AFFE_CARA_ELEM": 1, "AFFE_CHAR_MECA": 1, "AFFE_MATERIAU": 1, "AFFE_MODELE": 1,
        "ASSE_MATRICE": 2, "ASSE_VECTEUR": 1, "CALC_MATR_ELEM": 2, "CALC_VECT_ELEM": 1,
        "COMB_MATR_ASSE": 1, "DEBUT": 1, "DEFI_FONCTION": 1, "DEFI_GROUP": 1,
        "DEFI_LIST_ENTI": 1, "DEFI_LIST_REEL": 2, "DEFI_MATERIAU": 1, "DYNA_VIBRA": 4,
        "FIN": 1, "FORMULE": 1, "IMPR_RESU": 1, "LIRE_MAILLAGE": 1, "LIRE_RESU": 2,
        "NUME_DDL": 1, "TEST_RESU": 3,
    }  # fmt: skip
    assert "sdll100a" in index["commands"]["DYNA_VIBRA"]["testcases"]


def test_adlv101a_two_command_files(index: dict) -> None:
    case = index["testcases"]["adlv101a"]
    assert [f["path"] for f in case["command_files"]] == ["adlv101a.comm", "adlv101a.com1"]
    first, second = (f["calls"] for f in case["command_files"])
    assert "DEBUT" in first and "POURSUITE" not in first
    assert "POURSUITE" in second and "DEBUT" not in second
    assert first["FIN"] and second["FIN"]
    assert _calls(case)["CALC_MODES"] == 4
    assert case["params"]["testlist"] == ["submit", "verification", "sequential"]


def test_cont001b_python_script(index: dict) -> None:
    case = index["testcases"]["cont001b"]
    assert [f["path"] for f in case["command_files"]] == ["cont001b.py"]
    assert _calls(case) == {
        "AFFE_MODELE": 2,
        "DEBUT": 1,
        "DEFI_CONT": 5,
        "FIN": 1,
        "LIRE_MAILLAGE": 1,
    }
    assert case["params"]["memory_limit"] == 524


def test_zzzz100g_ignores_comments_strings_and_local_macros(index: dict) -> None:
    calls = _calls(index["testcases"]["zzzz100g"])
    # DEFI_FONCTION is only in a comment (line 316), IMPR_RESU only in a string (line 487),
    # MACRO_TEST is a UserMacro defined by the test's own zzzz100g.py.
    for name in ("DEFI_FONCTION", "IMPR_RESU", "MACRO_TEST"):
        assert name not in calls
    assert calls["DEFI_PROP_ALEA"] == 11


def test_parallel_case(index: dict) -> None:
    parallel = [c for c in index["testcases"].values() if c["parallel"]]
    assert len(parallel) == 320
    assert all("parallel" in c["params"]["testlist"] for c in parallel)
    assert any(c["params"].get("mpi_nbcpu", 1) > 1 for c in parallel)


# --- units ----------------------------------------------------------------------------------


def test_parse_export(tmp_path: Path) -> None:
    export = tmp_path / "x.export"
    export.write_text(
        "P time_limit 60.5\nP testlist ci parallel\nP no-mpiexec\nA args --max_base=100\n"
        "# comment\n\nF comm x.comm D 1\nR nom out D 0\n",
        encoding="utf-8",
    )
    meta = astest.parse_export(export)
    assert meta["params"] == {
        "time_limit": 60.5,
        "testlist": ["ci", "parallel"],
        "no-mpiexec": True,
    }
    assert meta["args"] == ["args", "--max_base=100"]
    assert meta["files"] == [
        {"kind": "F", "type": "comm", "path": "x.comm", "mode": "D", "unit": 1},
        {"kind": "R", "type": "nom", "path": "out", "mode": "D", "unit": 0},
    ]


def test_regex_fallback(tmp_path: Path) -> None:
    path = tmp_path / "bad.comm"
    path.write_text(
        "DEBUT()\nM = LIRE_MAILLAGE(  # not python: (\n# AFFE_MODELE()\nx.FIN()\nFIN()\n",
        encoding="utf-8",
    )
    scanned = astest.scan_command_file(path, {"DEBUT", "LIRE_MAILLAGE", "AFFE_MODELE", "FIN"})
    assert scanned == {"parse": "regex", "calls": {"DEBUT": [1], "FIN": [5], "LIRE_MAILLAGE": [2]}}


def test_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if not (UPSTREAM / astest.ASTEST_RELDIR).is_dir():
        pytest.skip("upstream/ submodule not checked out")
    monkeypatch.chdir(REPO)
    out = tmp_path / "index.json"
    result = CliRunner().invoke(app, ["extract", "astest-index", "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert "4496 test case(s)" in result.output
    assert out.read_text(encoding="utf-8") == INDEX.read_text(encoding="utf-8")
