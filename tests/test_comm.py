"""``.comm`` builder (task 6.1): fixtures regenerate byte for byte, layout, catalog checks.

The three fixture command files are written by ``tests/fixtures/comm_inputs.py`` with the
English API and must equal the committed ``input/run.comm``. Builder output is also checked
against ``ruff format`` (same layout), read back with the report's ``.comm`` reader (same
values) and run through upstream's own syntax checker (``tests/test_fixtures.py`` does that for
the fixture files).
"""

from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from codeaster_en.comm import (
    Builder,
    CatalogError,
    CommandFile,
    Commented,
    CommSyntaxError,
    Concept,
    Number,
    Param,
    Restraint,
    catalog,
    literal,
)
from codeaster_en.comm.syntax import render_call
from codeaster_en.report import comm as comm_reader

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"
sys.path.insert(0, str(FIXTURES))
import comm_inputs  # noqa: E402

sys.path.remove(str(FIXTURES))

CASES = list(comm_inputs.CASES)


# ---------- fixtures regenerate from the builder ----------


@pytest.mark.parametrize("case", CASES)
def test_fixture_comm_is_builder_output(case: str) -> None:
    committed = (FIXTURES / case / "input" / "run.comm").read_text(encoding="utf-8")
    assert comm_inputs.CASES[case]() == committed


def _ruff() -> list[str]:
    exe = shutil.which("ruff")
    if exe is None:
        pytest.skip("ruff not installed")
    return [exe]


@pytest.mark.parametrize("case", CASES)
def test_builder_layout_is_ruff_format(case: str) -> None:
    text = comm_inputs.CASES[case]()
    out = subprocess.run(
        [*_ruff(), "format", "--config", str(REPO / "ruff.toml"), "--stdin-filename", "run.py"],
        input=text,
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout == text


# ---------- round trip: builder values == values read back from the file ----------


def _expected(value: Any) -> Any:
    if isinstance(value, Concept):
        return comm_reader.Ref(value.name)
    if isinstance(value, Param):
        return _expected(value.value)
    if isinstance(value, Number):
        return value.value
    if isinstance(value, Commented):
        return _expected(value.value)
    if isinstance(value, dict):
        return {k: _expected(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_expected(v) for v in value]
    return value


@pytest.mark.parametrize("case", CASES)
def test_round_trip(case: str, monkeypatch: pytest.MonkeyPatch) -> None:
    built: list[Builder] = []
    real_init = Builder.__post_init__

    def spy(self: Builder) -> None:
        real_init(self)
        built.append(self)

    monkeypatch.setattr(Builder, "__post_init__", spy)
    text = comm_inputs.CASES[case]()
    statements = [s for s in built[0].file.statements if s.command]
    parsed = comm_reader.parse(text)
    assert not parsed.skipped
    assert [c.command for c in parsed.calls] == [s.command for s in statements]
    for call, st in zip(parsed.calls, statements, strict=True):
        assert call.concept == st.target
        expected = _expected(st.keywords)
        if st.target and call.keywords.get("reuse") is not None:
            expected = {"reuse": comm_reader.Ref(st.target), **expected}
        assert call.keywords == expected, st.command


# ---------- layout ----------


def test_short_call_stays_on_one_line() -> None:
    assert render_call("FIN", {}) == ["FIN()"]
    assert render_call("X", {"A": 1, "B": (1.0, 2.0)}, target="R") == ["R = X(A=1, B=(1.0, 2.0))"]


def test_one_tuple_keeps_its_comma() -> None:
    assert render_call("DEBUT", {"IGNORE_ALARM": ("MODELISA8_14",)}) == [
        'DEBUT(IGNORE_ALARM=("MODELISA8_14",))'
    ]


def test_split_tuple_puts_one_item_per_line() -> None:
    names = tuple(f"PARAMETER_{i}" for i in range(8))
    lines = render_call("RECU_TABLE", {"CO": Concept("MODES"), "NOM_PARA": names}, target="PARA")
    assert lines[0] == "PARA = RECU_TABLE("
    assert lines[1] == "    CO=MODES,"
    assert lines[2] == "    NOM_PARA=("
    assert lines[3:11] == [f'        "PARAMETER_{i}",' for i in range(8)]
    assert lines[11:] == ["    ),", ")"]


def test_single_keyword_call_splits_inside_without_comma() -> None:
    occ = {f"KEYWORD_{i}": "VALUE_WITH_SOME_LENGTH" for i in range(4)}
    lines = render_call("POST_RELEVE_T", {"ACTION": occ}, target="T")
    assert lines[:2] == ["T = POST_RELEVE_T(", "    ACTION=_F("]
    assert lines[-2:] == ["    )", ")"]


def test_comment_forces_split() -> None:
    lines = render_call("TEST_RESU", {"RESU": (Commented({"A": 1}, "why"),)})
    assert lines == ["TEST_RESU(", "    RESU=(", "        # why", "        _F(A=1),", "    )", ")"]


def test_strings_and_numbers() -> None:
    line = render_call("X", {"A": 'say "hi"', "B": 1e-9, "C": literal("1.0e-3"), "D": -2})[0]
    assert line == "X(A='say \"hi\"', B=1e-09, C=1.0e-3, D=-2)"
    with pytest.raises(CommSyntaxError):
        Number(0.001, "1.0E-3")
    with pytest.raises(CommSyntaxError):
        render_call("X", {"A": True})


# ---------- catalog checks ----------


def _file() -> CommandFile:
    f = CommandFile()
    f.call("DEBUT")
    return f


def test_unknown_command_and_keyword() -> None:
    f = _file()
    with pytest.raises(CatalogError, match="unknown command"):
        f.call("AFFE_MODELE_EN", "M")
    mesh = f.call("LIRE_MAILLAGE", "MAIL", FORMAT="MED", UNITE=20)
    model = f.call(
        "AFFE_MODELE",
        "MODE",
        MAILLAGE=mesh,
        AFFE={"TOUT": "OUI", "PHENOMENE": "MECANIQUE", "MODELISATION": "3D"},
    )
    with pytest.raises(CatalogError, match="AFFE_CHAR_MECA/PRES_REP/PRESSION: unknown"):
        f.call("AFFE_CHAR_MECA", "P", MODELE=model, PRES_REP={"GROUP_MA": "S", "PRESSION": 1.0})


def test_into_type_and_mandatory() -> None:
    f = _file()
    with pytest.raises(CatalogError, match="'XML' is not one of"):
        f.call("LIRE_MAILLAGE", "MAIL", FORMAT="XML")
    mesh = f.call("LIRE_MAILLAGE", "MAIL", FORMAT="MED", UNITE=20)
    with pytest.raises(CatalogError, match="AFFE_MODELE/AFFE/PHENOMENE: mandatory"):
        f.call("AFFE_MODELE", "MODE", MAILLAGE=mesh, AFFE={"TOUT": "OUI"})
    with pytest.raises(CatalogError, match="expects R"):
        f.call("DEFI_MATERIAU", "ACIER", ELAS={"E": "steel", "NU": 0.3})


def test_rules() -> None:
    f = _file()
    mesh = f.call("LIRE_MAILLAGE", "MAIL", FORMAT="MED", UNITE=20)
    with pytest.raises(CatalogError, match="exactly one of TOUT, GROUP_MA"):
        f.call(
            "AFFE_MODELE",
            "MODE",
            MAILLAGE=mesh,
            AFFE={"PHENOMENE": "MECANIQUE", "MODELISATION": "3D"},
        )


def test_block_conditions_follow_defaults() -> None:
    # SOLVEUR's keywords depend on METHODE, whose default is MUMPS.
    f = _file()
    mesh = f.call("LIRE_MAILLAGE", "MAIL", FORMAT="MED", UNITE=20)
    model = f.call(
        "AFFE_MODELE",
        "MODE",
        MAILLAGE=mesh,
        AFFE={"TOUT": "OUI", "PHENOMENE": "MECANIQUE", "MODELISATION": "3D"},
    )
    acier = f.call("DEFI_MATERIAU", "ACIER", ELAS={"E": 2.0e5, "NU": 0.3})
    mate = f.call("AFFE_MATERIAU", "MATE", MAILLAGE=mesh, AFFE={"TOUT": "OUI", "MATER": acier})
    load = f.call("AFFE_CHAR_MECA", "FIXE", MODELE=model, DDL_IMPO={"TOUT": "OUI", "DX": 0.0})
    common = {"MODELE": model, "CHAM_MATER": mate, "EXCIT": {"CHARGE": load}}
    with pytest.raises(CatalogError, match="'RCMK' is not one of"):
        f.call("MECA_STATIQUE", "R1", **common, SOLVEUR={"RENUM": "RCMK"})
    f.call("MECA_STATIQUE", "R2", **common, SOLVEUR={"METHODE": "LDLT", "RENUM": "RCMK"})
    with pytest.raises(CatalogError, match="NIVE_REMPLISSAGE: unknown"):
        f.call("MECA_STATIQUE", "R3", **common, SOLVEUR={"NIVE_REMPLISSAGE": 1})


def test_results_reuse_and_concept_types() -> None:
    f = _file()
    with pytest.raises(CatalogError, match="returns a result"):
        f.call("LIRE_MAILLAGE", FORMAT="MED")
    with pytest.raises(CatalogError, match="returns no result"):
        f.call("FIN", "X")
    mesh = f.call("LIRE_MAILLAGE", "MAIL", result_type="maillage_sdaster", FORMAT="MED")
    assert mesh is not None
    with pytest.raises(CatalogError, match="not reentrant"):
        f.call("LIRE_MAILLAGE", mesh, reuse=True, FORMAT="MED")
    with pytest.raises(CatalogError, match="expects modele_sdaster"):
        f.call("AFFE_CHAR_MECA", "F", MODELE=mesh, DDL_IMPO={"TOUT": "OUI", "DX": 0.0})
    with pytest.raises(CommSyntaxError, match="already used"):
        f.call("LIRE_MAILLAGE", "MAIL", FORMAT="MED", UNITE=20)


def test_ds_parents_match_upstream() -> None:
    path = REPO / "upstream" / "code_aster" / "Cata" / "Language" / "DataStructure.py"
    if not path.is_file():
        pytest.skip("upstream/ submodule not checked out")
    bases = {
        node.name: [b.id for b in node.bases if isinstance(b, ast.Name)]
        for node in ast.parse(path.read_text(encoding="utf-8")).body
        if isinstance(node, ast.ClassDef)
    }
    for child, parent in catalog.DS_PARENTS.items():
        assert bases.get(child) == [parent], child


# ---------- English API ----------


def test_builder_defaults_and_names() -> None:
    b = Builder()
    mesh = b.read_mesh()
    model = b.model(mesh, "thin_shell")
    f1 = b.fix(model, "A")
    f2 = b.fix(model, "B", kinematic=True)
    assert (f1.name, f2.name) == ("FIXE", "FIXE2")
    text = b.text()
    assert text.startswith('DEBUT(LANG="EN")\n')
    assert 'MODELISATION="DKT"' in text
    assert "DRX=0.0, DRY=0.0, DRZ=0.0" in text
    assert "FIXE2 = AFFE_CHAR_CINE(" in text
    assert text.endswith("\nFIN()\n")


def test_builder_refuses_mixed_or_wrong_modeling() -> None:
    b = Builder()
    mesh = b.read_mesh()
    with pytest.raises(CommSyntaxError, match="ADR-013"):
        b.model(mesh, "solid", modelisation="DKT")
    with pytest.raises(CommSyntaxError, match="unknown body kind"):
        b.model(mesh, "beam")
    solid = b.model(mesh, "solid")
    with pytest.raises(CommSyntaxError, match="shell properties"):
        b.shell_properties(solid, {"PLATE": 1.0})


def test_builder_session_options() -> None:
    b = Builder()
    with pytest.raises(CommSyntaxError, match="alarms_as_errors"):
        b.start(alarms_as_errors=True, ignore_alarms=["X_1"])
    b.start(language=None)
    with pytest.raises(CommSyntaxError, match="already written"):
        b.start()
    b.end()
    with pytest.raises(CommSyntaxError, match="already ended"):
        b.read_mesh()


def test_restraint_needs_one_location() -> None:
    with pytest.raises(CommSyntaxError):
        Restraint({"DX": 0.0}).keywords()
    with pytest.raises(CommSyntaxError):
        Restraint({"DX": 0.0}, groups="A", node_groups="B").keywords()


def test_builder_output_passes_upstream_checker(tmp_path: Path) -> None:
    """A file using the options the fixtures do not (kinematic fix, several materials,
    plane stress) is accepted by upstream's own syntax checker."""
    if not (REPO / "upstream" / "code_aster" / "Cata").is_dir():
        pytest.skip("upstream/ submodule not checked out")
    b = Builder()
    b.start()
    mesh = b.read_mesh()
    model = b.model(mesh, "plane_stress", groups=("A", "B"))
    s1 = b.material("S1", E=2.0e5, nu=0.3, rho=7.85e-9, alpha=1.2e-5)
    s2 = b.material("S2", E=7.0e4, nu=0.33)
    mate = b.assign_materials(mesh, {"A": s1, "B": s2})
    fixed = b.fix(model, ["L1", "L2"], kinematic=True)
    press = b.pressure(model, "EDGE", 1.0)
    resu = b.linear_static(model, mate, [fixed, press], solver="MULT_FRONT")
    b.compute_fields(resu, stress="SIGM_NOEU", strain=("EPSI_ELNO",), forces="REAC_NODA")
    b.write_med(resu, ["DEPL", "SIGM_NOEU"])
    text = b.text()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(REPO / "upstream"))
    try:
        from code_aster.Cata.Commands import commandStore
    finally:
        sys.path.remove(str(REPO / "upstream"))
    exec(compile(text, "built.comm", "exec"), dict(commandStore) | {"_F": dict})
