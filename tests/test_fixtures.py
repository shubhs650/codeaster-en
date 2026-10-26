"""Solver fixture inputs (task 4.1): consistent with each other, the schema and the catalog.

No solver is run here. The checks cover what can go wrong before a run:
run.json against docs/schemas/run.schema.json, run.export file references, mesh groups used
by run.comm present in mesh.med, TEST_RESU references equal to the hand values, and the
run.comm syntax against the pinned upstream command catalog.
"""

from __future__ import annotations

import ast
import json
import math
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"
SCHEMA = REPO / "docs" / "schemas" / "run.schema.json"
CASES = ("solid_static", "shell_static", "modal")
GROUP_KEYWORDS = {"GROUP_MA", "GROUP_NO", "GROUP_MA_PEAU"}

pytest.importorskip("numpy")
pytest.importorskip("h5py")
sys.path.insert(0, str(FIXTURES))
import hand_values  # noqa: E402


def _input(case: str) -> Path:
    return FIXTURES / case / "input"


def _run_json(case: str) -> dict:
    return json.loads((_input(case) / "run.json").read_text())


def _calls(case: str, name: str) -> list[ast.Call]:
    tree = ast.parse((_input(case) / "run.comm").read_text())
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name
    ]


def _literal_groups(case: str) -> set[str]:
    """Every string given to a GROUP_* keyword anywhere in run.comm."""
    tree = ast.parse((_input(case) / "run.comm").read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg in GROUP_KEYWORDS:
            value = ast.literal_eval(node.value)
            names.update([value] if isinstance(value, str) else value)
    return names


def _test_resu_occurrences(case: str) -> dict[str, dict]:
    """LEGENDE -> keywords of each TEST_RESU/RESU occurrence (values must be literals)."""
    out: dict[str, dict] = {}
    for call in _calls(case, "TEST_RESU"):
        for kw in call.keywords:
            assert kw.arg == "RESU"
            occurrences = kw.value.elts if isinstance(kw.value, ast.Tuple) else [kw.value]
            for occ in occurrences:
                assert isinstance(occ, ast.Call) and occ.func.id == "_F"
                values = {
                    k.arg: ast.literal_eval(k.value)
                    for k in occ.keywords
                    if isinstance(k.value, ast.Constant | ast.UnaryOp)
                }
                out[values["LEGENDE"]] = values
    return out


@pytest.mark.parametrize("case", CASES)
def test_run_json_matches_schema(case: str) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text())
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = [e.message for e in validator.iter_errors(_run_json(case))]
    assert errors == []
    assert _run_json(case)["case"] == case


@pytest.mark.parametrize("case", CASES)
def test_export_references(case: str) -> None:
    lines = (_input(case) / "run.export").read_text().splitlines()
    params = dict(line.split()[1:3] for line in lines if line.startswith("P "))
    assert params["ncpus"] == "1" and params["mpi_nbcpu"] == "1"
    solver = _run_json(case)["solver"]
    assert int(params["time_limit"]) == solver["time_limit_s"]
    assert int(params["memory_limit"]) == solver["memory_limit_mb"]
    files = [line.split() for line in lines if line.startswith("F ")]
    units = [int(f[4]) for f in files]
    assert len(units) == len(set(units)), "logical unit used twice"
    for _, _kind, path, mode, _unit in files:
        if mode == "D":
            assert (_input(case) / path).is_file(), path
        else:
            assert mode == "R" and path.startswith("../output/"), path
    assert {f[1] for f in files} >= {"comm", "mmed", "mess", "resu", "rmed"}


@pytest.mark.parametrize("case", CASES)
def test_comm_groups_exist_in_mesh(case: str) -> None:
    in_mesh = hand_values.med_group_names(_input(case) / "mesh.med")
    assert _literal_groups(case) <= in_mesh
    assert set(_run_json(case)["groups"]) == in_mesh


@pytest.mark.parametrize("case", CASES)
def test_comm_reads_units_from_export(case: str) -> None:
    lines = (_input(case) / "run.export").read_text().splitlines()
    units = {int(line.split()[4]) for line in lines if line.startswith("F ")}
    comm = (_input(case) / "run.comm").read_text()
    used = {int(u) for u in re.findall(r"UNITE=(\d+)", comm)}
    assert used <= units


@pytest.mark.parametrize("case", CASES)
def test_test_resu_matches_checks(case: str) -> None:
    occurrences = _test_resu_occurrences(case)
    checks = {c["legend"]: c for c in _run_json(case)["checks"]}
    assert set(occurrences) == set(checks)
    for legend, occ in occurrences.items():
        check = checks[legend]
        assert occ["REFERENCE"] == "ANALYTIQUE"
        assert math.isclose(occ["VALE_REFE"], check["reference"], rel_tol=1e-5), legend
        assert occ["PRECISION"] == check["precision"], legend
        assert (occ.get("VALE_ABS") == "OUI") == check.get("absolute_value", False), legend
        # Until task 4.2 records the solver's value, VALE_CALC is the hand value too.
        assert math.isclose(occ["VALE_CALC"], occ["VALE_REFE"], rel_tol=1e-9), legend
        assert occ["TOLE_MACHINE"] == occ["PRECISION"], legend


@pytest.mark.parametrize("case", CASES)
def test_checks_equal_hand_values(case: str) -> None:
    computed = hand_values.ALL[case]()
    for check in _run_json(case)["checks"]:
        assert math.isclose(check["reference"], computed[check["legend"]], rel_tol=1e-5), check


def test_solid_pressure_resultant_is_along_x() -> None:
    values = hand_values.solid_static()
    assert abs(values["applied_FY"]) < 1e-6 and abs(values["applied_FZ"]) < 1e-6
    # The faceted bore opening is slightly smaller than the true circle.
    assert 0.98 < values["REAC_DX_SUM"] / values["analytic_P_pi_ri2"] < 1.0


def test_modal_order() -> None:
    # Modes 1-5 bend and mode 6 twists only if the next bending and the axial mode are higher.
    values = hand_values.modal()
    assert values["F5_BENDING_Z3"] < values["F6_TORSION_1"]
    assert 1.1 * values["F6_TORSION_1"] < min(values["next_bending"], values["axial_1"])
    # J for a 2:1 rectangle is 0.229 b h^3 in the usual tables.
    assert math.isclose(hand_values.torsion_constant(20.0, 10.0) / 2e4, 0.229, rel_tol=2e-3)


def _catalog_namespace() -> dict:
    if not (REPO / "upstream" / "code_aster" / "Cata").is_dir():
        pytest.skip("upstream/ submodule not checked out")
    sys.dont_write_bytecode = True  # never write into upstream/
    sys.path.insert(0, str(REPO / "upstream"))
    try:
        from code_aster.Cata.Commands import commandStore
    finally:
        sys.path.remove(str(REPO / "upstream"))
    return dict(commandStore)


@pytest.mark.parametrize("case", CASES)
def test_comm_syntax_against_catalog(case: str) -> None:
    """Execute run.comm with the catalog's own syntax checker standing in for each command."""
    namespace = _catalog_namespace() | {"_F": dict}
    path = _input(case) / "run.comm"
    exec(compile(path.read_text(), str(path), "exec"), namespace)


def test_catalog_check_rejects_bad_keyword() -> None:
    namespace = _catalog_namespace() | {"_F": dict}
    comm = (_input("shell_static") / "run.comm").read_text().replace("PRES=Q", "PRESSION=Q")
    with pytest.raises(Exception, match="PRESSION|PRES"):
        exec(compile(comm, "broken.comm", "exec"), namespace)
