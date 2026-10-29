"""Report images (task 4.7): figure plan, mesh conversion, placeholder lines, rendering.

Rendering needs pyvista and an off-screen OpenGL context (OSMesa or EGL); without them the
rendering tests skip and the placeholder path is still tested by forcing ``available()``.
"""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from codeaster_en import report, results
from codeaster_en.cli import app
from codeaster_en.report import images
from codeaster_en.report.tripwire import french_words

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"
CASES = ("solid_static", "shell_static", "modal")


@pytest.fixture(scope="module")
def models() -> dict[str, report.RunModel]:
    return {c: report.collect(FIXTURES / c) for c in (*CASES, "broken_missing_group")}


@pytest.fixture
def no_gl(monkeypatch: pytest.MonkeyPatch) -> str:
    reason = "VTK could not open an off-screen OpenGL context (test)"
    monkeypatch.setattr(images, "available", lambda: (False, reason))
    return reason


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def _rendering() -> None:
    ok, reason = images.available()
    if not ok:
        pytest.skip(f"no off-screen rendering: {reason}")


# ---------- plan ----------


def test_plan(models: dict) -> None:
    kinds = {c: [f.kind for f in images.plan(models[c])] for c in models}
    assert kinds["solid_static"] == ["deformed_shape", "von_mises"]
    # The shell fixture writes no SIEQ field, so there is no von Mises image.
    assert kinds["shell_static"] == ["deformed_shape"]
    assert kinds["modal"] == ["mode_shape"] * 6
    assert kinds["broken_missing_group"] == []
    modal = images.plan(models["modal"])
    assert [f.number for f in modal] == [1, 2, 3, 4, 5, 6]
    assert [f.nume_ordre for f in modal] == [1, 2, 3, 4, 5, 6]
    with results.open(FIXTURES / "modal" / "output" / "run.rmed") as res:
        assert res.find(modal[0].med_name).name == "DEPL"


def test_plan_follows_requested_sections(models: dict) -> None:
    model = models["solid_static"]
    trimmed = report.RunModel(**{**model.__dict__, "sections": ["summary", "stresses"]})
    assert [f.kind for f in images.plan(trimmed)] == ["von_mises"]


def test_captions_carry_units(models: dict) -> None:
    deformed, vmis = images.plan(models["solid_static"])
    assert deformed.caption.endswith("[mm]") and vmis.caption.endswith("[MPa]")


# ---------- mesh conversion ----------


def test_grid_uses_corner_nodes_of_highest_dimension() -> None:
    with results.open(FIXTURES / "modal" / "output" / "run.rmed") as res:
        points, cells, types = images._grid_arrays(res.mesh)  # H20 volumes + QU8 faces
        assert points.shape == (res.mesh.n_nodes, 3)
    assert set(types) == {12} and len(types) == 640
    assert cells.reshape(640, 9)[:, 0].tolist() == [8] * 640
    with results.open(FIXTURES / "shell_static" / "output" / "run.rmed") as res:
        _, cells, types = images._grid_arrays(res.mesh)  # QU4 shells + SE2 edges + PO1
    assert set(types) == {9} and len(types) == 400


def test_nice_scale() -> None:
    assert images._nice(6634.2) == 6600.0
    assert images._nice(0.01234) == 0.012
    assert images._nice(0.0) == 0.0


# ---------- placeholders (no rendering) ----------


def test_images_off_by_default(tmp_path: Path) -> None:
    result = report.build(FIXTURES / "solid_static", out=tmp_path, pdf=False)
    assert result.model.images is None
    assert "Figure" not in result.markdown.read_text(encoding="utf-8")
    assert not (tmp_path / "images").exists()


def test_placeholder_without_rendering(tmp_path: Path, no_gl: str) -> None:
    config = report.Config(images=True)
    result = report.build(FIXTURES / "solid_static", config, out=tmp_path, pdf=False)
    md = result.markdown.read_text(encoding="utf-8")
    assert "*Figure 1 not generated (deformed shape, undeformed edges in gray; " in md
    assert f": {no_gl}.*" in md
    assert "*Figure 2 not generated (von Mises stress" in md
    assert "![" not in md.split("## Diagnostics")[0].split("## Results")[1]
    assert french_words(md) == []
    assert [f["reason"] for f in result.model.images] == [no_gl, no_gl]
    assert not (tmp_path / "images").exists()


def test_no_figures_for_failed_run(tmp_path: Path, no_gl: str) -> None:
    config = report.Config(images=True)
    result = report.build(FIXTURES / "broken_missing_group", config, out=tmp_path, pdf=False)
    assert result.model.images == []
    assert "Figure" not in result.markdown.read_text(encoding="utf-8")


def test_cli_images_flag(tmp_path: Path, no_gl: str) -> None:
    out = tmp_path / "r"
    res = CliRunner().invoke(
        app, ["report", str(FIXTURES / "shell_static"), "--out", str(out), "--no-pdf", "--images"]
    )
    assert res.exit_code == 0, res.output
    assert "*Figure 1 not generated" in (out / "report.md").read_text(encoding="utf-8")


# ---------- rendering ----------


def test_render_static(tmp_path: Path) -> None:
    _rendering()
    config = report.Config(images=True)
    result = report.build(FIXTURES / "solid_static", config, out=tmp_path, pdf=False)
    md = result.markdown.read_text(encoding="utf-8")
    figs = result.model.images
    assert [f["file"] for f in figs] == ["images/deformed_shape.png", "images/von_mises.png"]
    assert all(f["reason"] is None for f in figs)
    for f in figs:
        assert _png_size(tmp_path / f["file"]) == images.WINDOW
        assert f"]({f['file']})" in md
    # Largest displacement drawn at a tenth of the bounding-box diagonal.
    with results.open(FIXTURES / "solid_static" / "output" / "run.rmed") as res:
        diag = np.linalg.norm(np.ptp(res.mesh.coordinates, axis=0))
        umax = np.nanmax(res.nodal_values("DEPL", ("DX", "DY", "DZ")))
    assert figs[0]["scale"] == images._nice(0.1 * diag / umax)
    assert f"displacements scaled by {figs[0]['scale']:g}" in md
    assert french_words(md) == []
    page = result.html.read_text(encoding="utf-8")
    assert '<img alt="Figure 1, deformed shape" src="images/deformed_shape.png"' in page


def test_render_modes(tmp_path: Path) -> None:
    _rendering()
    config = report.Config(images=True)
    result = report.build(FIXTURES / "modal", config, out=tmp_path, pdf=False)
    files = [f["file"] for f in result.model.images]
    assert files == [f"images/mode_shape_{n}.png" for n in range(1, 7)]
    for f in files:
        assert _png_size(tmp_path / f) == images.THUMBNAIL
    md = result.markdown.read_text(encoding="utf-8")
    assert "*Figure 1: mode 1, 52.34 Hz;" in md


def test_render_into_pdf(tmp_path: Path) -> None:
    _rendering()
    pytest.importorskip("weasyprint")
    config = report.Config(images=True)
    result = report.build(FIXTURES / "shell_static", config, out=tmp_path)
    if result.pdf is None:
        pytest.skip("; ".join(result.warnings))
    # The PNG is embedded: WeasyPrint resolves images/ from the report directory.
    assert b"/Subtype /Image" in result.pdf.read_bytes()
