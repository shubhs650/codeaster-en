"""Results readers (task 4.5): tables, fields, extrema, reactions, modal table, labels.

Checked against the committed fixture outputs (``tests/fixtures/*/output``): the reader must
give back the values ``TEST_RESU`` checked in the solver run (``VALE_CALC`` in ``run.comm``) and
the hand values of ``tests/fixtures/hand_values.py``. The native MED reader is also compared
with ``medcoupling`` (SALOME's MED library) when it is installed.
"""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from codeaster_en import results
from codeaster_en.cli import app
from codeaster_en.results.med import MedFile, split_med_name
from codeaster_en.results.tables import parse_tables

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"
CASES = ("solid_static", "shell_static", "modal")


def _out(case: str) -> Path:
    return FIXTURES / case / "output"


def _vale_calc(case: str) -> dict[str, float]:
    """LEGENDE -> VALE_CALC of every TEST_RESU in the case's run.comm."""
    tree = ast.parse((FIXTURES / case / "input" / "run.comm").read_text(encoding="utf-8"))
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_F":
            kw = {k.arg: k.value for k in node.keywords}
            if "LEGENDE" in kw and "VALE_CALC" in kw:
                out[ast.literal_eval(kw["LEGENDE"])] = ast.literal_eval(kw["VALE_CALC"])
    return out


def _frequencies() -> dict[str, float]:
    """The modal fixture's frequency checks (legends F1_... to F6_...)."""
    return {k: v for k, v in _vale_calc("modal").items() if k.startswith("F")}


def _hand(case: str) -> dict[str, float]:
    import importlib.util

    spec = importlib.util.spec_from_file_location("hand_values", FIXTURES / "hand_values.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.ALL[case]()


@pytest.fixture(scope="module")
def opened():
    handles = {case: results.open(_out(case) / "run.rmed") for case in CASES}
    yield handles
    for h in handles.values():
        h.close()


@pytest.fixture(scope="module")
def tables():
    return {case: results.read_table_dir(_out(case) / "tables") for case in CASES}


# ---------- tables ----------


def test_reaction_table_parsed(tables) -> None:
    (table,) = tables["solid_static"]
    assert table.concept == "0000002a"
    assert table.columns == ["INTITULE", "RESU", "NOM_CHAM", "NUME_ORDRE", "INST", "DX", "DY", "DZ"]
    (row,) = table.rows
    assert row["INTITULE"] == "REAC_BASE"
    assert row["NOM_CHAM"] == "REAC_NODA"
    assert row["NUME_ORDRE"] == 1
    assert row["DX"] == pytest.approx(3891.64)


def test_modal_tables_parsed(tables) -> None:
    by_file = {Path(t.source).name: t for t in tables["modal"]}
    assert set(by_file) == {"mass_inertia.csv", "modal_parameters.csv"}
    params = by_file["modal_parameters.csv"]
    assert params.column("NUME_ORDRE") == [1, 2, 3, 4, 5, 6]
    assert params.has("FREQ", "MASS_GENE", "MASS_EFFE_UN_DZ")
    mass = by_file["mass_inertia.csv"]
    assert mass.rows[0]["ENTITE"] == "TOUT"


def test_parse_several_tables_and_blank_separated() -> None:
    text = (
        "#\n##ASTER 17.04.22 CONCEPT 00000001 CALCULE LE x DE TYPE\n"
        "A,B\n1, 2.5\n\n"
        "#\n##ASTER 17.04.22 CONCEPT 00000002 CALCULE LE x DE TYPE\n"
        "NOM   VALE\nabc   -1.0E+00\ndef   -\n"
    )
    first, second = parse_tables(text)
    assert first.concept == "00000001" and first.rows == [{"A": 1, "B": 2.5}]
    assert second.concept == "00000002"
    assert second.rows == [{"NOM": "abc", "VALE": -1.0}, {"NOM": "def", "VALE": None}]


def test_ragged_row_is_an_error() -> None:
    with pytest.raises(ValueError, match="2 cells"):
        parse_tables("A,B,C\n1,2\n")


# ---------- fields and groups ----------


def test_split_med_name() -> None:
    assert split_med_name("RESU____SIEQ_NOEU") == ("RESU", "SIEQ_NOEU")
    assert split_med_name("MODES___DEPL") == ("MODES", "DEPL")
    assert split_med_name("DEPL") == ("", "DEPL")


def test_fields_listed(opened) -> None:
    fields = {f.field: f for f in opened["solid_static"].fields()}
    assert set(fields) == {"DEPL", "SIGM_NOEU", "SIEQ_NOEU", "REAC_NODA"}
    sieq = fields["SIEQ_NOEU"]
    assert sieq.result == "RESU" and sieq.med_name == "RESU____SIEQ_NOEU"
    assert sieq.locations == ["nodes"]
    assert sieq.label == "equivalent stress (nodal average)"
    assert sieq.components[:3] == ["VMIS", "TRESCA", "PRIN_1"]
    assert sieq.component_labels["VMIS"] == "von Mises"
    assert [(s.nume_ordre, s.value) for s in sieq.steps] == [(1, 0.0)]
    shell = {f.field for f in opened["shell_static"].fields()}
    assert shell == {"DEPL", "EFGE_NOEU", "REAC_NODA"}


def test_modal_steps_are_frequencies(opened) -> None:
    (depl,) = opened["modal"].fields()
    calc = _frequencies()
    legends = sorted(calc, key=lambda k: int(k[1]))
    assert [s.nume_ordre for s in depl.steps] == [1, 2, 3, 4, 5, 6]
    for step, legend in zip(depl.steps, legends, strict=True):
        assert step.value == pytest.approx(calc[legend], rel=1e-12)


def test_groups(opened) -> None:
    assert opened["solid_static"].groups() == {
        "node": ["BASE"],
        "element": ["BASE", "NOZ_END", "P_NOZZLE", "P_SHELL", "SOLID", "TOP"],
    }
    assert opened["modal"].groups()["node"] == []
    mesh = opened["shell_static"].mesh
    assert mesh.group_node_indices("CENTER").tolist() == [4]
    assert mesh.coordinates[4].tolist() == [500.0, 500.0, 0.0]
    # 20 x 20 QUAD4 plate: 80 boundary nodes.
    assert mesh.group_node_indices("EDGES").size == 80
    # Element group without a node group: the nodes of its elements (cantilever tip face).
    tip = opened["modal"].mesh.group_node_indices("TIP")
    assert np.allclose(opened["modal"].mesh.coordinates[tip][:, 0], 400.0)


def test_unknown_names_raise(opened) -> None:
    r = opened["solid_static"]
    with pytest.raises(KeyError, match="no field"):
        r.extrema("EFGE_NOEU", "MXX")
    with pytest.raises(KeyError, match="no component"):
        r.extrema("DEPL", "DRX")
    with pytest.raises(KeyError, match="no group"):
        r.extrema("DEPL", "DX", groups=["NOPE"])
    with pytest.raises(KeyError, match="NUME_ORDRE"):
        r.extrema("DEPL", "DX", nume_ordre=2)


# ---------- extrema ----------


def test_shell_centre_values_match_test_resu(opened) -> None:
    calc = _vale_calc("shell_static")
    r = opened["shell_static"]
    whole, centre = r.extrema("DEPL", "DZ", groups=["CENTER"])
    assert centre.count == 1
    assert centre.min.value == pytest.approx(calc["W_CENTER"], rel=1e-12)
    # The plate sags most at its centre.
    assert whole.min.value == centre.min.value
    assert whole.min.entity == "node" and whole.min.entity_id == 5
    assert whole.min.xyz == (500.0, 500.0, 0.0)
    assert whole.max_abs is whole.min
    (_, mxx) = r.extrema("EFGE_NOEU", "MXX", groups=["CENTER"])
    assert mxx.max.value == pytest.approx(calc["MXX_CENTER"], rel=1e-12)
    assert mxx.label == "bending moment XX (MXX)"


def test_magnitude_and_location(opened) -> None:
    r = opened["solid_static"]
    whole, base = r.extrema("DEPL", ("DX", "DY", "DZ"), groups=["BASE"])
    assert whole.component == "|DX,DY,DZ|"
    assert whole.label == "magnitude of DX, DY, DZ"
    assert whole.count == r.mesh.n_nodes
    assert base.count == 144
    assert base.max.value < 1e-12  # fixed base
    node = whole.max.entity_id
    assert np.allclose(r.mesh.coordinates[node - 1], whole.max.xyz)
    u = r.nodal_values("DEPL", ("DX", "DY", "DZ"))
    assert whole.max.value == pytest.approx(float(np.nanmax(u)))


def test_solid_von_mises_peak(opened) -> None:
    r = opened["solid_static"]
    whole, nozzle, shell = r.extrema("SIEQ_NOEU", "VMIS", groups=["P_NOZZLE", "P_SHELL"])
    # The peak is at the nozzle-shell junction (fields guide: 34.7 MPa), on both skins' nodes.
    assert whole.max.value == pytest.approx(34.738, abs=1e-3)
    assert nozzle.max.entity_id == whole.max.entity_id
    assert shell.max.value <= whole.max.value
    assert whole.min.value >= 0.0
    assert whole.location == "nodes"


def test_mode_shapes_are_normalized(opened, tables) -> None:
    # Since task 6.4c the fixture runs NORM_MODE NORME="MASS_GENE": unit generalized mass, so
    # the largest component is no longer 1 (CALC_MODES' own scaling, fields guide).
    r = opened["modal"]
    for mode in r.modal(tables["modal"]).modes:
        assert mode.generalized_mass == pytest.approx(1.0, rel=1e-9)
    (_, tip) = r.extrema("DEPL", "DZ", groups=["TIP"], nume_ordre=1)
    (whole,) = r.extrema("DEPL", "DZ", nume_ordre=1)
    # First bending mode in Z: largest at the tip.
    assert abs(tip.max_abs.value) == pytest.approx(abs(whole.max_abs.value))
    assert abs(tip.max_abs.value) > 1.0


# ---------- reactions ----------


def test_reactions_solid(opened, tables) -> None:
    calc = _vale_calc("solid_static")["REAC_DX_SUM"]
    summary = opened["solid_static"].reactions(groups=["BASE"], tables=tables["solid_static"])
    assert summary.field == "RESU____REAC_NODA"
    assert summary.total["DX"] == pytest.approx(calc, rel=1e-9)
    (base,) = summary.per_group
    assert base.group == "BASE" and base.nodes == 144
    assert base.components["DX"] == pytest.approx(calc, rel=1e-9)
    assert abs(base.components["DY"]) < 1e-6 and abs(base.components["DZ"]) < 1e-6
    (printed,) = summary.from_tables
    assert printed.source == "table:reactions.csv:REAC_BASE"
    assert printed.components["DX"] == pytest.approx(calc, rel=1e-5)
    assert summary.labels["DX"] == "X translation"
    # Balance against the hand value of the applied pressure resultant (0.00007 % error).
    assert summary.total["DX"] == pytest.approx(_hand("solid_static")["REAC_DX_SUM"], rel=1e-5)


def test_reactions_shell(opened, tables) -> None:
    summary = opened["shell_static"].reactions(groups=["EDGES"], tables=tables["shell_static"])
    assert set(summary.total) == {"DX", "DY", "DZ", "DRX", "DRY", "DRZ"}
    assert summary.total["DZ"] == pytest.approx(10000.0, rel=1e-9)
    assert summary.per_group[0].components["DZ"] == pytest.approx(10000.0, rel=1e-9)
    assert summary.from_tables[0].components["DZ"] == pytest.approx(10000.0)


def test_reactions_without_field(opened) -> None:
    summary = opened["modal"].reactions()
    assert summary.field is None and summary.total == {}
    assert "REAC_NODA is not in run.rmed" in summary.notes[0]


# ---------- modal ----------


def test_modal_table(opened, tables) -> None:
    table = opened["modal"].modal(tables["modal"])
    calc = _frequencies()
    hand = _hand("modal")
    assert table.result == "MODES"
    assert table.total_mass == pytest.approx(hand["mass"], rel=1e-5)
    assert [m.nume_ordre for m in table.modes] == [1, 2, 3, 4, 5, 6]
    freqs = [calc[k] for k in sorted(calc, key=lambda k: int(k[1]))]
    for mode, f in zip(table.modes, freqs, strict=True):
        assert mode.frequency_hz == pytest.approx(f, rel=1e-12)  # .rmed precision, not table
        assert mode.period_s == pytest.approx(1.0 / f)
        assert mode.generalized_mass is not None
    assert not table.notes
    # Bending modes in Z are 1, 3, 5 and in Y are 2, 4 (run.comm): their effective mass
    # fractions match the Euler-Bernoulli cantilever (61.3 %, 18.8 %, 6.5 %) within 1 %.
    z = [table.modes[i].effective_mass_fraction["DZ"] for i in (0, 2, 4)]
    y = [table.modes[i].effective_mass_fraction["DY"] for i in (1, 3)]
    for n, value in enumerate(z, start=1):
        assert value == pytest.approx(hand[f"mass_fraction_bending_{n}"], rel=1e-2)
    for n, value in enumerate(y, start=1):
        assert value == pytest.approx(hand[f"mass_fraction_bending_{n}"], rel=1e-2)
    last = table.modes[-1].cumulative_fraction
    assert last["DZ"] == pytest.approx(sum(z), rel=1e-9)
    assert last["DX"] < 1e-20  # no axial mode below 1.5 kHz
    # The printed fraction equals the effective mass over the POST_ELEM total mass.
    m1 = table.modes[0]
    assert m1.effective_mass["DZ"] / table.total_mass == pytest.approx(
        m1.effective_mass_fraction["DZ"], rel=1e-4
    )
    assert table.labels["MASS_EFFE_UN_DZ"] == "effective mass fraction (Z)"


def test_modal_table_without_tables(opened) -> None:
    table = opened["modal"].modal()
    assert table.result == "MODES"
    assert len(table.modes) == 6 and table.modes[0].effective_mass_fraction == {}
    assert table.total_mass is None
    assert "step values" in table.notes[0]


def test_modal_fraction_computed_from_total_mass(opened, tables) -> None:
    """A parameter table without MASS_EFFE_UN_* still gives fractions via POST_ELEM mass."""
    params = next(t for t in tables["modal"] if t.has("MASS_EFFE_DZ"))
    mass = next(t for t in tables["modal"] if t.has("MASSE"))
    trimmed = results.Table(
        columns=[c for c in params.columns if "_UN_" not in c],
        rows=[{k: v for k, v in r.items() if "_UN_" not in k} for r in params.rows],
        source=params.source,
    )
    table = opened["modal"].modal([trimmed, mass])
    assert table.modes[0].effective_mass_fraction["DZ"] == pytest.approx(0.612263, rel=1e-4)


# ---------- labels ----------


def test_labels() -> None:
    labels = results.Labels()
    assert labels.get("VMIS") == "von Mises"
    assert labels.get("DEPL") == "displacement"
    assert labels.get("MASS_EFFE_DX") == "effective modal mass (X)"
    assert labels.get("VECT_1_X") == "1st principal direction (X)"
    assert labels.get("CDG_Y") == "center of gravity (Y)"
    assert labels.get("MASSE") == "mass"
    assert labels.get("NO_SUCH_NAME") is None
    assert labels.describe("NO_SUCH_NAME") == "NO_SUCH_NAME"
    assert labels.describe("TRESCA") == "Tresca (TRESCA)"


def test_every_fixture_component_has_a_label(opened) -> None:
    for case in CASES:
        for f in opened[case].fields():
            assert f.label, f.med_name
            missing = [c for c, label in f.component_labels.items() if not label]
            assert not missing, (f.med_name, missing)


# ---------- element fields (synthetic file) and medcoupling cross-check ----------


def _write_elno_file(path: Path) -> None:
    """Two QUAD4 and one TRIA3 with an ELNO field, an element group and a node group."""
    mc = pytest.importorskip("medcoupling")
    mesh = mc.MEDCouplingUMesh("MAIL", 2)
    mesh.setCoords(mc.DataArrayDouble([0, 0, 1, 0, 2, 0, 0, 1, 1, 1, 2, 1], 6, 2))
    mesh.allocateCells()
    mesh.insertNextCell(mc.NORM_QUAD4, [0, 1, 4, 3])
    mesh.insertNextCell(mc.NORM_QUAD4, [1, 2, 5, 4])
    mesh.insertNextCell(mc.NORM_TRI3, [3, 4, 0])
    mesh.finishInsertingCells()
    mesh.sortCellsInMEDFileFrmt()  # TRI3 first, then QUAD4
    umesh = mc.MEDFileUMesh()
    umesh.setMeshAtLevel(0, mesh)
    right = mc.DataArrayInt([2])  # the second QUAD4 after sorting
    right.setName("RIGHT")
    umesh.setGroupsAtLevel(0, [right])
    corner = mc.DataArrayInt([5])
    corner.setName("CORNER")
    umesh.setGroupsAtLevel(1, [corner])
    umesh.write(str(path), 2)
    field = mc.MEDCouplingFieldDouble(mc.ON_GAUSS_NE, mc.ONE_TIME)
    field.setMesh(mesh)
    field.setName("RESU____SIGM_ELNO")
    n = 3 + 4 + 4
    values = mc.DataArrayDouble([float(v) for v in range(2 * n)], n, 2)
    values.setInfoOnComponents(["SIXX", "SIYY"])
    field.setArray(values)
    field.setTime(0.0, 1, 1)
    one = mc.MEDFileField1TS()
    one.setFieldNoProfileSBT(field)
    one.write(str(path), 0)


def test_element_node_field(tmp_path: Path) -> None:
    path = tmp_path / "elno.rmed"
    _write_elno_file(path)
    with results.open(path) as r:
        (info,) = r.fields()
        assert info.field == "SIGM_ELNO" and info.locations == ["element nodes"]
        whole, right, corner = r.extrema("SIGM_ELNO", "SIYY", groups=["RIGHT", "CORNER"])
        # SIYY of value k is 2k + 1; values 0..2 on the TRI3, 3..6 and 7..10 on the QUAD4s.
        assert whole.count == 11
        assert whole.min.value == 1.0 and whole.max.value == 21.0
        assert whole.max.entity == "element"
        assert whole.max.point == 4  # last node of the second QUAD4: node 5 (index 4)
        assert whole.max.node_id == 5
        assert whole.max.xyz == (1.0, 1.0)
        assert right.count == 4 and right.min.value == 15.0
        # Node group on an element-node field: the values of all elements at that node.
        assert corner.count == 1 and corner.max.value == 2 * 9 + 1


@pytest.mark.parametrize("case", CASES)
def test_native_reader_matches_medcoupling(case: str) -> None:
    mc = pytest.importorskip("medcoupling")
    path = _out(case) / "run.rmed"
    umesh = mc.MEDFileMesh.New(str(path))
    fields = mc.MEDFileFields(str(path))
    with MedFile(path) as med:
        mesh = med.mesh()
        coords = umesh.getCoords().toNumPyArray()
        assert np.array_equal(mesh.coordinates, coords)
        for group in mesh.node_groups():
            ref = sorted(umesh.getNodeGroupArr(group).getValues())
            assert mesh.group_node_indices(group).tolist() == ref, group
        for f in med.fields():
            multi = fields[f.med_name]
            assert list(multi.getInfo()) == f.components
            for step in f.steps:
                ref = multi.getFieldOnMeshAtLevel(
                    mc.ON_NODES, step.number, step.order, 0, umesh
                ).getArray()
                (sup,) = list(med.supports(f.med_name, step))
                assert np.array_equal(sup.values[:, :, 0].T, ref.toNumPyArray())


# ---------- CLI ----------


def test_cli_results() -> None:
    runner = CliRunner()
    out = str(_out("shell_static"))
    res = runner.invoke(app, ["results", "fields", out])
    assert res.exit_code == 0, res.output
    assert "EFGE_NOEU (shell/beam resultants (nodal average))" in res.output
    res = runner.invoke(app, ["results", "extrema", out, "DEPL", "DZ", "-g", "CENTER", "--json"])
    assert res.exit_code == 0, res.output
    data = json.loads(res.output)
    assert data[1]["group"] == "CENTER"
    assert math.isclose(data[1]["min"]["value"], _vale_calc("shell_static")["W_CENTER"])
    res = runner.invoke(app, ["results", "reactions", out, "-g", "EDGES"])
    assert res.exit_code == 0 and "EDGES: DX 0, DY 0, DZ 1e+04" in res.output
    res = runner.invoke(app, ["results", "modal", str(_out("modal"))])
    assert res.exit_code == 0 and "61.2" in res.output
    res = runner.invoke(app, ["results", "extrema", out, "DEPL", "VMIS"])
    assert res.exit_code == 1 and "no component" in res.output
    res = runner.invoke(app, ["results", "fields", str(FIXTURES / "nowhere")])
    assert res.exit_code == 1
