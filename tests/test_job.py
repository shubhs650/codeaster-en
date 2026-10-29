"""Job directory helpers (task 6.3): ``run.export`` writer and the pre-run check.

The fixtures' committed ``run.export`` files are the reference layout
(docs/CLEARFEA-INTEGRATION.md §3); the broken fixtures are the reference faults (§5).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codeaster_en import job

pytest.importorskip("h5py")

FIXTURES = Path(__file__).resolve().parent / "fixtures"

TABLES = {
    "solid_static": ["reactions.csv"],
    "shell_static": ["reactions.csv"],
    "modal": ["mass_inertia.csv", "modal_parameters.csv"],
    "broken_missing_group": ["reactions.csv"],
}
CASES = sorted(p.name for p in FIXTURES.iterdir() if (p / "input" / "run.comm").is_file())


def _input(case: str) -> Path:
    return FIXTURES / case / "input"


@pytest.mark.parametrize("case", sorted(TABLES))
def test_export_matches_fixture(case: str) -> None:
    text = job.export_text(job.table_units(TABLES[case]))
    assert text == (_input(case) / "run.export").read_text()


def test_write_export_creates_layout(tmp_path: Path) -> None:
    path = job.write_export(tmp_path, {31: "b.csv", 30: "a.csv"}, time_limit_s=60, ncpus=4)
    assert path == tmp_path / "input" / "run.export"
    assert (tmp_path / "output" / "tables").is_dir()
    lines = path.read_text().splitlines()
    assert "P time_limit 60" in lines and "P ncpus 4" in lines
    libr = [ln for ln in lines if ln.startswith("F libr")]
    assert libr == ["F libr ../output/tables/a.csv R 30", "F libr ../output/tables/b.csv R 31"]


@pytest.mark.parametrize("bad", [{20: "x.csv"}, {80: "x.csv"}, {30: "sub/x.csv"}, {30: ""}])
def test_export_rejects_bad_tables(bad: dict[int, str]) -> None:
    with pytest.raises(ValueError):
        job.export_text(bad)


@pytest.mark.parametrize("case", CASES)
def test_precheck_fixtures(case: str) -> None:
    comm = (_input(case) / "run.comm").read_text()
    problems = job.precheck(comm, _input(case) / "mesh.med")
    kinds = [p.kind for p in problems]
    if case == "broken_python_syntax":
        assert kinds == ["syntax"]
        assert problems[0].line is not None
    elif case == "broken_missing_group":
        assert kinds == ["missing_group"]
        p = problems[0]
        assert (p.command, p.keyword, p.group) == ("AFFE_CHAR_MECA", "GROUP_MA", "EDGE")
        assert p.failure_class == "user-model"
        assert comm.splitlines()[p.line - 1].count("EDGE")
    else:
        # Faults that need the solver (bad keyword, singular matrix) pass, as do good files.
        assert problems == []


def test_precheck_node_groups(tmp_path: Path) -> None:
    mesh = _input("shell_static") / "mesh.med"
    # No DEFI_GROUP: the Gmsh mesh has element groups only, so a GROUP_NO name is missing.
    comm = 'DEBUT()\nX = MODI_MAILLAGE(ORIE_NORM_COQUE=_F(GROUP_MA="PLATE", GROUP_NO="CENTER"))\n'
    [p] = job.precheck(comm, mesh)
    assert (p.keyword, p.group) == ("GROUP_NO", "CENTER")
    created = 'M = DEFI_GROUP(CREA_GROUP_NO=_F(GROUP_MA=("CENTER", "EDGES")))\n'
    assert job.precheck(created + comm, mesh) == []
    named = 'M = DEFI_GROUP(CREA_GROUP_NO=_F(NOM="MID", GROUP_MA="CENTER"))\n'
    use = 'L = AFFE_CHAR_MECA(DDL_IMPO=_F(GROUP_NO=("MID", "NOPE"), DX=0.0))\n'
    assert [p.group for p in job.precheck(named + use, mesh)] == ["NOPE"]


def test_precheck_without_mesh_checks_syntax_only() -> None:
    assert job.precheck('A = AFFE_MODELE(AFFE=_F(GROUP_MA="ANY"))\n') == []
    assert [p.kind for p in job.precheck("A = (\n")] == ["syntax"]
