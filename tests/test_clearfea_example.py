"""The worked example of docs/CLEARFEA-INTEGRATION.md §9 runs as written (task 6.3).

The block between the ``worked-example`` markers is executed; ``run_solver`` (ClearFEA's part)
is replaced by a copy of the ``shell_static`` fixture's committed solver output, whose input
is the same plate, mesh and load.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

pytest.importorskip("h5py")
pytest.importorskip("markdown")

from codeaster_en import report  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "CLEARFEA-INTEGRATION.md"
CASE = REPO / "tests" / "fixtures" / "shell_static"


def _example() -> dict:
    text = DOC.read_text()
    block = re.search(
        r"<!-- worked-example:start -->\n```python\n(.*?)```\n<!-- worked-example:end -->",
        text,
        re.S,
    )
    assert block, "worked example block not found"
    namespace: dict = {}
    # Pad with blank lines so tracebacks point at the right line of the doc.
    code = "\n" * text[: block.start(1)].count("\n") + block.group(1)
    exec(compile(code, str(DOC), "exec"), namespace)  # noqa: S102
    return namespace


def _run_json() -> dict:
    data = json.loads((CASE / "input" / "run.json").read_text())
    data.pop("checks")  # the example writes no TEST_RESU
    data["case"] = "clearfea_example"
    return data


def _fake_solver(job_dir: Path) -> int:
    out = job_dir / "output"
    for path in (CASE / "output").rglob("*"):
        if path.is_file():
            target = out / path.relative_to(CASE / "output")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, target)
    return int((out / "exit_code").read_text())


def test_example_comm_matches_fixture_model() -> None:
    ns = _example()
    text, tables = ns["build_plate"](pressure_mpa=0.01, thickness_mm=10.0)
    assert tables == {30: "reactions.csv"}
    assert text.startswith("# ClearFEA job")
    assert re.search(r'^DEBUT\(.*LANG="EN"', text, re.M)
    for call in ('PRES_REP=_F(GROUP_MA="PLATE", PRES=0.01)', 'MODELISATION="DKT"', "UNITE=30"):
        assert call in text
    assert ns["job"].precheck(text, CASE / "input" / "mesh.med") == []


def test_example_end_to_end(tmp_path: Path) -> None:
    ns = _example()
    out = ns["submit"](tmp_path / "job", CASE / "input" / "mesh.med", _run_json(), _fake_solver)
    json.dumps(out)  # what ClearFEA stores is JSON
    assert out["status"] == "ok" and out["billing"] == "charge"
    assert out["classification"]["failure_class"] is None
    assert out["max_displacement"]["value"] == pytest.approx(2.1123, rel=1e-3)
    assert out["reactions"]["total"]["DZ"] == pytest.approx(10000.0, rel=1e-6)
    md = Path(out["report"]["markdown"]).read_text()
    assert report.french_words(md) == []
    export = (tmp_path / "job" / "input" / "run.export").read_text()
    assert export == (CASE / "input" / "run.export").read_text()


def test_example_rejects_missing_group_before_billing(tmp_path: Path) -> None:
    ns = _example()
    original = ns["build_plate"]

    def typo(**kwargs):
        text, tables = original(**kwargs)
        return text.replace('GROUP_MA="EDGES"', 'GROUP_MA="EDGE"'), tables

    ns["build_plate"] = typo
    ran = []
    out = ns["submit"](tmp_path / "job", CASE / "input" / "mesh.med", _run_json(), ran.append)
    assert ran == []
    assert out["status"] == "rejected" and out["billing"] == "none"
    assert {p["group"] for p in out["problems"]} == {"EDGE"}


def test_example_classifies_solver_failure(tmp_path: Path) -> None:
    ns = _example()
    broken = REPO / "tests" / "fixtures" / "broken_singular_matrix" / "output"

    def solver(job_dir: Path) -> int:
        shutil.copytree(broken, job_dir / "output", dirs_exist_ok=True)
        return int((broken / "exit_code").read_text())

    out = ns["submit"](tmp_path / "job", CASE / "input" / "mesh.med", _run_json(), solver)
    assert out["status"] == "failed" and out["billing"] == "charge"
    assert out["classification"]["message_id"] == "FACTOR_11"
    assert out["problems"] and out["problems"][0]["message_id"] == "FACTOR_11"
