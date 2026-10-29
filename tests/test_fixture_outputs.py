"""Committed solver outputs (task 4.2): every fixture ran clean and every TEST_RESU passed.

The outputs under tests/fixtures/<case>/output/ come from scripts/run-fixture.sh (in a session
or in .github/workflows/solver-fixtures.yml, which runs this file after regenerating them).
No solver is run here.
"""

from __future__ import annotations

import ast
import csv
import json
import math
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"
CASES = ("solid_static", "shell_static", "modal", "solid_loads")
TEST_LINE = re.compile(r"^ (OK|NOOK) +(\S+) +(\S+) +(\S+) +(\S+)")
EXPECTED_FIELDS = {
    "solid_static": {"DEPL", "SIGM_NOEU", "SIEQ_NOEU", "REAC_NODA"},
    "shell_static": {"DEPL", "EFGE_NOEU", "REAC_NODA"},
    "modal": {"DEPL"},
    "solid_loads": {"DEPL", "SIEQ_NOEU", "REAC_NODA"},
}


def _output(case: str) -> Path:
    return FIXTURES / case / "output"


def _test_lines(case: str) -> list[tuple[str, str, str, float]]:
    """(verdict, reference type, legend, computed value) for each TEST_RESU result line."""
    rows = []
    for line in (_output(case) / "run.mess").read_text(encoding="utf-8").splitlines():
        m = TEST_LINE.match(line)
        if m:
            verdict, ref, legend, _refe, calc = m.groups()
            rows.append((verdict, ref, legend, float(calc)))
    return rows


def _vale_calc(case: str) -> dict[str, float]:
    """LEGENDE -> VALE_CALC literal of each TEST_RESU occurrence in run.comm."""
    tree = ast.parse((FIXTURES / case / "input" / "run.comm").read_text())
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_F":
            kws = {k.arg: k.value for k in node.keywords}
            if "LEGENDE" in kws and "VALE_CALC" in kws:
                out[ast.literal_eval(kws["LEGENDE"])] = ast.literal_eval(kws["VALE_CALC"])
    return out


@pytest.mark.parametrize("case", CASES)
def test_job_ran_clean(case: str) -> None:
    out = _output(case)
    assert (out / "exit_code").read_text().strip() == "0"
    assert "--- DIAGNOSTIC JOB : OK" in (out / "run_aster.stdout").read_text(encoding="utf-8")
    mess = (out / "run.mess").read_text(encoding="utf-8")
    assert "EXECUTION_CODE_ASTER_EXIT_" in mess
    # No alarm, error or fatal message box (ignored alarms are not printed).
    assert not re.search(r"║ <[AEFS]> <", mess)


@pytest.mark.parametrize("case", CASES)
def test_every_test_resu_ok(case: str) -> None:
    rows = _test_lines(case)
    vale_calc = _vale_calc(case)
    # One NON_REGRESSION and one ANALYTIQUE line per occurrence.
    assert len(rows) == 2 * len(vale_calc)
    assert [r for r in rows if r[0] != "OK"] == []
    assert {r[2] for r in rows} == set(vale_calc)
    assert {r[1] for r in rows} == {"NON_REGRESSION", "ANALYTIQUE"}


@pytest.mark.parametrize("case", CASES)
def test_vale_calc_is_solver_value(case: str) -> None:
    vale_calc = _vale_calc(case)
    for _verdict, _ref, legend, calc in _test_lines(case):
        assert math.isclose(calc, vale_calc[legend], rel_tol=1e-6), legend


@pytest.mark.parametrize("case", CASES)
def test_rmed_has_fields(case: str) -> None:
    h5py = pytest.importorskip("h5py")
    with h5py.File(_output(case) / "run.rmed", "r") as f:
        # MED field names are the result concept name padded to 8 characters + the field name.
        fields = {name[8:] for name in f["CHA"]}
    assert fields == EXPECTED_FIELDS[case]


@pytest.mark.parametrize("case", CASES)
def test_tables_written(case: str) -> None:
    lines = (FIXTURES / case / "input" / "run.export").read_text().splitlines()
    tables = [ln.split()[2] for ln in lines if ln.startswith("F libr ")]
    assert tables
    for rel in tables:
        text = (FIXTURES / case / "input" / rel).read_text(encoding="utf-8")
        rows = [r for r in csv.reader(text.splitlines()) if r and not r[0].startswith("#")]
        assert len(rows) >= 2, rel  # header + at least one row


def test_reaction_tables_match_test_resu() -> None:
    """POST_RELEVE_T resultants agree with the TEST_RESU sums (and carry the same sign)."""
    for case, comp, legend in (
        ("solid_static", "DX", "REAC_DX_SUM"),
        ("shell_static", "DZ", "REAC_DZ_SUM"),
        ("solid_loads", "DX", "REAC_DX_SUM"),
        ("solid_loads", "DY", "REAC_DY_SUM"),
        ("solid_loads", "DZ", "REAC_DZ_SUM"),
    ):
        text = (_output(case) / "tables" / "reactions.csv").read_text(encoding="utf-8")
        rows = [r for r in csv.reader(text.splitlines()) if r and not r[0].startswith("#")]
        header = [h.strip() for h in rows[0]]
        value = float(rows[1][header.index(comp)])
        assert math.isclose(value, _vale_calc(case)[legend], rel_tol=1e-5), case


def _table_row(case: str, name: str) -> dict[str, str]:
    text = (_output(case) / "tables" / name).read_text(encoding="utf-8")
    rows = [r for r in csv.reader(text.splitlines()) if r and not r[0].startswith("#")]
    return dict(zip([h.strip() for h in rows[0]], rows[1], strict=True))


def test_solid_loads_support_moments() -> None:
    """Moment of the support reactions about (100, 50, 0) against the hand value.

    MX is exact. MY and MZ also hold the couple of the finite-length spring: a translational
    two-node spring (DIS_T, K_T_D_L) passes equal and opposite forces at its two ends, 50 mm
    apart along X, and no moment, so its end forces F leave a couple (0, -50 FZ, 50 FY) out of
    the balance (about 2 N.mm here, F about 0.04 N; seen in the first run, task 6.4c).
    """
    sys.path.insert(0, str(FIXTURES))
    try:
        import hand_values
    finally:
        sys.path.remove(str(FIXTURES))
    hand = hand_values.solid_loads()
    row = _table_row("solid_loads", "moments.csv")
    for axis, rel_tol in (("X", 1e-5), ("Y", 1e-4), ("Z", 2e-4)):
        value = float(row[f"MOMENT_{axis}"])
        assert math.isclose(value, hand[f"REAC_M{axis}"], rel_tol=rel_tol), axis
    for comp, axis in (("DX", "X"), ("DY", "Y"), ("DZ", "Z")):
        assert math.isclose(float(row[f"RESULT_{axis}"]), hand[f"REAC_{comp}_SUM"], rel_tol=1e-5)


def test_solid_loads_mass_matches_geometry() -> None:
    row = _table_row("solid_loads", "mass_inertia.csv")
    assert math.isclose(float(row["MASSE"]), 7.85e-9 * 200.0 * 100.0 * 100.0, rel_tol=1e-5)
    assert [float(row[f"CDG_{a}"]) for a in "XYZ"] == [100.0, 50.0, 50.0]


def test_modal_mass_matches_geometry() -> None:
    text = (_output("modal") / "tables" / "mass_inertia.csv").read_text(encoding="utf-8")
    rows = [r for r in csv.reader(text.splitlines()) if r and not r[0].startswith("#")]
    header = [h.strip() for h in rows[0]]
    mass = float(rows[1][header.index("MASSE")])
    assert math.isclose(mass, 7.85e-9 * 400.0 * 20.0 * 10.0, rel_tol=1e-9)


@pytest.mark.parametrize("case", CASES)
def test_provenance(case: str) -> None:
    prov = json.loads((_output(case) / "provenance.json").read_text())
    image = (REPO / "CONTAINER_IMAGE").read_text().splitlines()
    image = [ln.strip() for ln in image if ln.strip() and not ln.startswith("#")][0]
    assert prov["case"] == case
    assert prov["image"] == image
    assert prov["exit_code"] == 0
    assert prov["upstream_version"] == (REPO / "UPSTREAM_VERSION").read_text().split()[0]
    assert prov["solver_version"].startswith("code_aster ")
