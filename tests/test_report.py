"""Report generator (task 4.6): run model, Markdown golden files, tripwire, loads, balance.

The golden files under ``tests/golden/report/<case>/`` are the expected ``report.md`` and
``run_model.json`` of each fixture. After an intended change, regenerate them with::

    UPDATE_GOLDEN=1 pytest tests/test_report.py

and review the diff like any other change.
"""

from __future__ import annotations

import ast
import json
import math
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from codeaster_en import report, results
from codeaster_en.cli import app
from codeaster_en.report import comm, loads
from codeaster_en.report.collect import FAILURE_SECTIONS, english_log_lines, parse_export
from codeaster_en.report.labels import num
from codeaster_en.report.tripwire import french_words

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"
GOLDEN = REPO / "tests" / "golden" / "report"
CASES = ("solid_static", "shell_static", "modal")
BROKEN = (
    "broken_missing_group",
    "broken_python_syntax",
    "broken_singular_matrix",
    "broken_bad_keyword",
)
UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"


@pytest.fixture(scope="module")
def models() -> dict[str, report.RunModel]:
    return {case: report.collect(FIXTURES / case) for case in CASES + BROKEN}


def _vale_calc(case: str) -> dict[str, float]:
    tree = ast.parse((FIXTURES / case / "input" / "run.comm").read_text(encoding="utf-8"))
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_F":
            kw = {k.arg: k.value for k in node.keywords}
            if "LEGENDE" in kw and "VALE_CALC" in kw:
                out[ast.literal_eval(kw["LEGENDE"])] = ast.literal_eval(kw["VALE_CALC"])
    return out


def _close(a: object, b: object, path: str = "") -> None:
    """JSON equality with a tolerance on floats (sums depend on the summation order)."""
    if isinstance(a, float) or isinstance(b, float):
        assert isinstance(a, int | float) and isinstance(b, int | float), path
        assert math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9), f"{path}: {a} != {b}"
    elif isinstance(a, dict):
        assert isinstance(b, dict) and a.keys() == b.keys(), f"{path}: keys differ"
        for k in a:
            _close(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b), f"{path}: lengths differ"
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            _close(x, y, f"{path}[{i}]")
    else:
        assert a == b, f"{path}: {a!r} != {b!r}"


# ---------- golden files ----------


@pytest.mark.parametrize("case", CASES + BROKEN)
def test_markdown_golden(models: dict, case: str) -> None:
    md = report.render_markdown(models[case])
    golden = GOLDEN / case / "report.md"
    if UPDATE:
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_text(md, encoding="utf-8")
    assert golden.is_file(), f"missing {golden}: run with UPDATE_GOLDEN=1"
    assert md == golden.read_text(encoding="utf-8")


@pytest.mark.parametrize("case", CASES + BROKEN)
def test_run_model_golden(models: dict, case: str) -> None:
    data = json.loads(models[case].to_json())
    golden = GOLDEN / case / "run_model.json"
    if UPDATE:
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_text(models[case].to_json(), encoding="utf-8")
    _close(data, json.loads(golden.read_text(encoding="utf-8")))


def test_run_model_has_no_absolute_paths(models: dict) -> None:
    for case, model in models.items():
        text = model.to_json()
        assert str(REPO) not in text, case


# ---------- English only ----------


@pytest.mark.parametrize("case", CASES + BROKEN)
def test_markdown_is_english(models: dict, case: str) -> None:
    md = report.render_markdown(models[case])
    assert french_words(md) == [], case


def test_tripwire_catches_french() -> None:
    assert french_words("Le calcul est terminé.") == ["Le", "calcul", "est", "terminé"]
    assert french_words("Mesh check failed: déplacement imposé") == ["déplacement", "imposé"]


def test_tripwire_ignores_code_and_identifiers() -> None:
    md = (
        "The load `CHARGE_REPARTIE` uses `GROUP_MA`.\n\n"
        "Set keyword NPREC of the factor keyword SOLVEUR.\n\n"
        "```python\n# maillage du modèle\nMAIL = LIRE_MAILLAGE()\n```\n"
    )
    assert french_words(md) == []


def test_log_excerpt_hides_untranslated_lines(models: dict) -> None:
    lines = models["broken_missing_group"].outcome["last_lines"]
    assert len(lines) <= 50
    text = "\n".join(lines)
    assert "MODELISA7_77" in text
    assert "STATISTIQUES" not in text
    assert "printed by the solver outside the message catalog" in text


# ---------- content ----------


def test_sections_follow_run_json(models: dict) -> None:
    assert models["solid_static"].sections == [
        "title_block",
        "summary",
        "model",
        "materials",
        "loads_and_bcs",
        "solution",
        "displacements",
        "stresses",
        "reactions",
        "diagnostics",
        "verification",
        "appendix_command_file",
        "appendix_run_parameters",
    ]
    modal = models["modal"]
    assert "modal" in modal.sections and "reactions" not in modal.sections


@pytest.mark.parametrize("case", BROKEN)
def test_failure_report(models: dict, case: str) -> None:
    m = models[case]
    assert m.outcome["status"] == "failed"
    assert set(m.sections) <= set(FAILURE_SECTIONS)
    assert m.outcome["classification"]["failure_class"] == "user-model"
    md = report.render_markdown(m)
    assert "**Run failed" in md
    assert "Cause classification: **user-model**" in md


def test_failure_names_command_and_line(models: dict) -> None:
    o = models["broken_missing_group"].outcome
    assert o["failed_command"] == "AFFE_CHAR_MECA"
    assert o["failed_comm_line"] == 33
    assert o["fatal_message_id"] == "MODELISA7_77"
    o = models["broken_singular_matrix"].outcome
    assert o["failed_command"] == "MECA_STATIQUE" and o["fatal_message_id"] == "FACTOR_11"


def test_syntax_error_is_reported(models: dict) -> None:
    m = models["broken_python_syntax"]
    assert m.appendix["comm_syntax_error"].startswith("line ")
    assert any("not valid Python" in n for n in m.notes)


def test_headline_numbers_match_solver(models: dict) -> None:
    disp = models["shell_static"].displacements
    assert disp is not None
    dz = next(c for c in disp["components"] if c["component"] == "DZ")["extrema"]["min"]
    assert math.isclose(dz["value"], _vale_calc("shell_static")["W_CENTER"], rel_tol=1e-12)
    modal = models["modal"].summary["headline"]
    first = next(h for h in modal if h["key"] == "first_frequency")["value"]
    assert math.isclose(first, _vale_calc("modal")["F1_BENDING_Z1"], rel_tol=1e-12)


def test_verification_rows(models: dict) -> None:
    v = models["modal"].verification
    assert len(v["rows"]) == 6 and all(r["passed"] for r in v["rows"])
    assert v["non_regression"] == {"count": 6, "ok": 6}
    assert v["rows"][0]["reference_type"] == {"fr": "ANALYTIQUE", "en": "analytical"}


def test_solution_statistics_from_messages(models: dict) -> None:
    dofs = models["solid_static"].solution["dofs"]
    assert (dofs["total"], dofs["physical"], dofs["lagrange"]) == (14730, 13866, 864)
    eigen = models["modal"].solution["eigen"]
    assert eigen["modes_requested"] == 6 and eigen["method"]["fr"] == "SORENSEN"


def test_units(models: dict) -> None:
    assert models["solid_static"].units["system"] == "SI_mm"
    broken = models["broken_missing_group"].units
    assert broken["declared"] is False and broken["guess"] == "SI_mm"


def test_ignored_alarms_are_not_warnings(models: dict) -> None:
    m = models["shell_static"]
    assert m.outcome["status"] == "completed"
    assert m.summary["warnings"] == {} and m.summary["ignored_warnings"] == ["MODELISA8_14"]


def test_export_parsing() -> None:
    e = parse_export(FIXTURES / "solid_static" / "input" / "run.export")
    assert {"key": "time_limit", "label": "Time limit", "value": "600", "unit": "s"} in e[
        "parameters"
    ]
    rmed = next(f for f in e["files"] if f["type"] == "rmed")
    assert rmed["direction"] == "output" and rmed["unit"] == 80


def test_appendix_comments_every_command(models: dict) -> None:
    md = report.render_markdown(models["solid_static"])
    assert "# >> MECA_STATIQUE: linear static analysis\nRESU = MECA_STATIQUE(" in md


# ---------- loads and balance ----------


@pytest.mark.parametrize(
    ("case", "legend", "axis"),
    [("solid_static", "REAC_DX_SUM", "DX"), ("shell_static", "REAC_DZ_SUM", "DZ")],
)
def test_balance_against_solver(models: dict, case: str, legend: str, axis: str) -> None:
    r = models[case].reactions
    assert r is not None
    applied, bal = r["applied"], r["balance"]
    assert applied["complete"] and bal["complete"]
    # The solver's own reaction sum (TEST_RESU VALE_CALC) balances the summed applied load.
    assert math.isclose(-applied["total"][axis], _vale_calc(case)[legend], rel_tol=1e-9)
    assert bal["error_percent"] < 1e-6


def _comm(text: str) -> comm.CommandFile:
    return comm.parse(text)


def _shell_mesh():
    return results.open(FIXTURES / "shell_static" / "output" / "run.rmed")


SHELL_HEAD = """
MODE = AFFE_MODELE(MAILLAGE=MAIL, AFFE=_F(GROUP_MA="PLATE", PHENOMENE="MECANIQUE",
                   MODELISATION="DKT"))
FIX = AFFE_CHAR_MECA(MODELE=MODE, DDL_IMPO=_F(GROUP_MA="EDGES", DZ=0.0))
"""


def _applied(body: str, excit: str = "_F(CHARGE=FIX), _F(CHARGE=LOAD)") -> loads.AppliedLoads:
    cf = _comm(SHELL_HEAD + body + f"\nRESU = MECA_STATIQUE(MODELE=MODE, EXCIT=({excit}))\n")
    with _shell_mesh() as r:
        return loads.applied_loads(cf, cf.find("MECA_STATIQUE")[0], r.mesh, "rmed")


def test_force_nodale_full_force_at_every_node() -> None:
    a = _applied(
        'LOAD = AFFE_CHAR_MECA(MODELE=MODE, FORCE_NODALE=_F(GROUP_NO="CORNER_A", FZ=-5.0))'
    )
    assert a.complete and a.total == {"DX": 0.0, "DY": 0.0, "DZ": -5.0}
    a = _applied('LOAD = AFFE_CHAR_MECA(MODELE=MODE, FORCE_NODALE=_F(GROUP_NO="EDGES", FX=1.0))')
    assert a.total["DX"] == 80.0  # 80 edge nodes of the 20 x 20 plate


def test_force_face_and_arete() -> None:
    a = _applied('LOAD = AFFE_CHAR_MECA(MODELE=MODE, FORCE_FACE=_F(GROUP_MA="PLATE", FY=2.0))')
    assert math.isclose(a.total["DY"], 2.0 * 1000.0 * 1000.0)
    a = _applied('LOAD = AFFE_CHAR_MECA(MODELE=MODE, FORCE_ARETE=_F(GROUP_MA="EDGES", FZ=1.0))')
    assert math.isclose(a.total["DZ"], 4000.0)


def test_constants_and_arithmetic_are_evaluated() -> None:
    a = _applied(
        "Q = 0.01\nA = 1000.0\n"
        'LOAD = AFFE_CHAR_MECA(MODELE=MODE, PRES_REP=_F(GROUP_MA="PLATE", PRES=2 * Q))'
    )
    assert math.isclose(a.total["DZ"], -0.02 * 1.0e6)


def test_unevaluated_loads_make_balance_partial() -> None:
    a = _applied(
        "LOAD = AFFE_CHAR_MECA(MODELE=MODE, PESANTEUR=_F(GRAVITE=9.81, DIRECTION=(0, 0, -1)))"
    )
    assert not a.complete
    item = next(i for i in a.items if i.keyword == "PESANTEUR")
    assert item.status == "not_evaluated"
    bal = loads.balance({"DX": 0.0, "DY": 0.0, "DZ": 1.0}, "test", a)
    assert bal is not None and not bal.complete and bal.notes


def test_fonc_mult_is_not_evaluated() -> None:
    a = _applied(
        'LOAD = AFFE_CHAR_MECA(MODELE=MODE, PRES_REP=_F(GROUP_MA="PLATE", PRES=1.0))',
        excit="_F(CHARGE=FIX), _F(CHARGE=LOAD, FONC_MULT=RAMPE)",
    )
    assert not a.complete and any("FONC_MULT" in n for n in a.notes)


def test_overlapping_occurrences_are_not_evaluated() -> None:
    a = _applied(
        'LOAD = AFFE_CHAR_MECA(MODELE=MODE, PRES_REP=(_F(GROUP_MA="PLATE", PRES=1.0),'
        ' _F(GROUP_MA="PLATE", PRES=2.0)))'
    )
    assert not a.complete
    assert [i.status for i in a.items if i.keyword == "PRES_REP"] == ["evaluated", "not_evaluated"]


# ---------- command file reader ----------


def test_comm_reader() -> None:
    cf = comm.parse(
        "import math\nP = 2.0\nN = -P * 3\nX = math.pi\n"
        "M = LIRE_MAILLAGE(UNITE=20)\n"
        "C = AFFE_CHAR_MECA(MODELE=M, PRES_REP=_F(GROUP_MA=('A', 'B'), PRES=N), F=X)\n"
        "for i in range(2):\n    pass\n"
    )
    assert cf.constants == {"P": 2.0, "N": -6.0}
    call = cf.find("AFFE_CHAR_MECA")[0]
    assert call.get("MODELE") == comm.Ref("M")
    assert call.occurrences("PRES_REP") == [{"GROUP_MA": ["A", "B"], "PRES": -6.0}]
    assert isinstance(call.get("F"), comm.Unevaluated)
    assert cf.skipped == [4, 7]
    assert comm.parse("A = (").syntax_error is not None


# ---------- formatting ----------


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (0.0, "0"),
        (3891.6428, "3892"),
        (2.112263, "2.112"),
        (0.007749, "0.007749"),
        (210000.0, "210.0e3"),
        (-9.185e-15, "-9.185e-15"),
        (6.28e-4, "628.0e-6"),
        (99999.9, "100.0e3"),
        (9.99996, "10.00"),
        (7, "7"),
        (None, "–"),
    ],
)
def test_num(value: float | None, text: str) -> None:
    assert num(value) == text


# ---------- outputs ----------


def test_build_writes_outputs(tmp_path: Path) -> None:
    result = report.build(FIXTURES / "solid_static", out=tmp_path, pdf=False)
    md = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert md == (GOLDEN / "solid_static" / "report.md").read_text(encoding="utf-8")
    page = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert page.startswith("<!DOCTYPE html>") and "<table>" in page
    assert json.loads((tmp_path / "run_model.json").read_text())["schema_version"] == 1
    assert result.pdf is None


def test_pdf(tmp_path: Path) -> None:
    pytest.importorskip("weasyprint")
    result = report.build(FIXTURES / "modal", out=tmp_path)
    if result.pdf is None:  # WeasyPrint installed without its system libraries
        pytest.skip("; ".join(result.warnings))
    assert result.pdf.read_bytes().startswith(b"%PDF")


def test_cli(tmp_path: Path) -> None:
    out = tmp_path / "r"
    res = CliRunner().invoke(
        app, ["report", str(FIXTURES / "modal"), "--out", str(out), "--no-pdf", "--log"]
    )
    assert res.exit_code == 0, res.output
    md = (out / "report.md").read_text(encoding="utf-8")
    assert "## Appendix C: solver log in English" in md
    assert french_words(md) == []
    res = CliRunner().invoke(app, ["report", str(FIXTURES / "modal"), "--section", "nope"])
    assert res.exit_code == 2


def test_english_log_lines_cover_whole_log(models: dict) -> None:
    assert models["modal"].appendix["log_lines"]
    log = report.collect_module.mess.translate(
        report.collect_module.mess.parse(FIXTURES / "modal" / "output" / "run.mess")
    )
    assert english_log_lines(log) == models["modal"].appendix["log_lines"]
