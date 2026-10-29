"""Result images for the report (task 4.7, ``docs/REPORT-SPEC.md`` §6): deformed shape, von
Mises stress and mode shapes, rendered off-screen with pyvista.

Optional and off by default (``Config.images``, ``caen report --images``). It needs pyvista
(``pip install codeaster_en[images]``) and an OpenGL context VTK can open without a display:
OSMesa or EGL (Debian/Ubuntu: ``libosmesa6``). :func:`available` probes that in a subprocess,
because a VTK build without a usable context can abort the whole process. When rendering is
not possible, each planned figure is kept with the reason and the report prints a placeholder
line instead of the image.

Geometry is drawn from the corner nodes of the highest-dimension cells of the result mesh
(quadratic cells are drawn as linear ones; this is a picture, not a post-processor). Values
come from :class:`codeaster_en.results.Results`, from the same fields the report tables use.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import warnings
from dataclasses import asdict, dataclass
from functools import cache
from pathlib import Path
from typing import Any

import numpy as np

from codeaster_en.report.labels import num, unit
from codeaster_en.results.med import Mesh

IMAGE_DIR = "images"
WINDOW = (1200, 900)
THUMBNAIL = (600, 450)
# Largest displacement drawn as this fraction of the model's bounding-box diagonal.
DEFORMATION_FRACTION = 0.1
MAX_MODE_IMAGES = 12

# MED cell type -> (topological dimension, number of corner nodes, VTK cell type).
# VTK: LINE 3, TRIANGLE 5, QUAD 9, TETRA 10, HEXAHEDRON 12, WEDGE 13, PYRAMID 14.
MED_CELLS: dict[str, tuple[int, int, int]] = {
    "SE2": (1, 2, 3),
    "SE3": (1, 2, 3),
    "SE4": (1, 2, 3),
    "TR3": (2, 3, 5),
    "TR6": (2, 3, 5),
    "TR7": (2, 3, 5),
    "QU4": (2, 4, 9),
    "QU8": (2, 4, 9),
    "QU9": (2, 4, 9),
    "TE4": (3, 4, 10),
    "T10": (3, 4, 10),
    "HE8": (3, 8, 12),
    "H20": (3, 8, 12),
    "H27": (3, 8, 12),
    "PE6": (3, 6, 13),
    "P15": (3, 6, 13),
    "P18": (3, 6, 13),
    "PY5": (3, 5, 14),
    "P13": (3, 5, 14),
}

PROBE = (
    "import pyvista as pv\n"
    "p = pv.Plotter(off_screen=True, window_size=(16, 16))\n"
    "p.add_mesh(pv.Sphere())\n"
    "p.screenshot(None, return_img=True)\n"
    "p.close()\n"
    "print('render-ok')\n"
)


@cache
def available() -> tuple[bool, str | None]:
    """Whether off-screen rendering works here, and if not, why (English, for the report)."""
    if importlib.util.find_spec("pyvista") is None:
        return False, "pyvista is not installed (pip install codeaster_en[images])"
    try:
        proc = subprocess.run(
            [sys.executable, "-c", PROBE], capture_output=True, text=True, timeout=120
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"the off-screen rendering probe did not finish ({exc.__class__.__name__})"
    if proc.returncode != 0 or "render-ok" not in proc.stdout:
        return False, (
            "VTK could not open an off-screen OpenGL context (install OSMesa or EGL, "
            "e.g. the libosmesa6 package)"
        )
    return True, None


@dataclass
class Figure:
    """One planned image. ``file`` is relative to the report directory; ``None`` with a
    ``reason`` when it was not rendered."""

    number: int
    section: str
    kind: str  # deformed_shape | von_mises | mode_shape
    med_name: str
    component: str
    caption: str
    nume_ordre: int | None = None
    scale: float | None = None
    file: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _nice(value: float) -> float:
    """Two significant figures, so the caption states a readable scale factor."""
    return float(f"{value:.2g}") if value > 0 else 0.0


def plan(model: Any) -> list[Figure]:
    """The figures the report's sections call for, numbered in section order."""
    system = model.units.get("system")
    figures: list[Figure] = []

    def add(**kw: Any) -> None:
        figures.append(Figure(number=len(figures) + 1, **kw))

    for section in model.sections:
        if section == "displacements" and model.displacements:
            d = model.displacements
            length = unit(system, "length")
            add(
                section=section,
                kind="deformed_shape",
                med_name=d["med_name"],
                component="DX DY DZ",
                caption=(
                    "deformed shape, undeformed edges in gray; color shows the displacement "
                    f"magnitude{f' [{length}]' if length else ''}"
                ),
            )
        elif section == "stresses" and model.stresses:
            table = next(
                (
                    t
                    for t in model.stresses["tables"]
                    if t["kind"] == "stress" and t["field"] == "SIEQ_NOEU"
                ),
                None,
            )
            if table is None:
                continue
            stress = unit(system, "stress")
            add(
                section=section,
                kind="von_mises",
                med_name=table["med_name"],
                component="VMIS",
                caption=(
                    "von Mises stress (`SIEQ_NOEU`, `VMIS`), nodal average, on the undeformed "
                    f"shape{f' [{stress}]' if stress else ''}"
                ),
            )
        elif section == "modal" and model.modal:
            for m in model.modal["modes"][:MAX_MODE_IMAGES]:
                add(
                    section=section,
                    kind="mode_shape",
                    med_name=f"{model.modal['result']:_<8}DEPL",
                    component="DX DY DZ",
                    nume_ordre=m["nume_ordre"],
                    caption=(
                        f"mode {m['nume_ordre']}, {num(m['frequency_hz'])} Hz; color shows the "
                        "displacement magnitude of the normalized mode (sign and amplitude of "
                        "a mode shape are arbitrary)"
                    ),
                )
    return figures


def _grid_arrays(mesh: Mesh) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Points (n, 3), VTK cell array and cell types of the highest-dimension cells."""
    blocks = [
        (MED_CELLS[t], b)
        for t, b in sorted(mesh.cells.items())
        if t in MED_CELLS and len(b.numbers)
    ]
    if not blocks:
        raise ValueError("the results mesh has no cell type that can be drawn")
    top = max(dim for (dim, _, _), _ in blocks)
    cells, types = [], []
    for (dim, corners, vtk_type), block in blocks:
        if dim != top:
            continue
        conn = block.connectivity[:, :corners]
        cells.append(np.hstack([np.full((conn.shape[0], 1), corners), conn]).ravel())
        types.append(np.full(conn.shape[0], vtk_type, dtype=np.uint8))
    points = np.zeros((mesh.n_nodes, 3))
    points[:, : mesh.coordinates.shape[1]] = mesh.coordinates
    return points, np.concatenate(cells).astype(np.int64), np.concatenate(types)


def _vectors(results: Any, med_name: str, nume_ordre: int | None) -> np.ndarray:
    """Translation vectors per node (n, 3); missing components and undefined nodes are 0."""
    f = results.find(med_name)
    out = np.zeros((results.mesh.n_nodes, 3))
    for i, c in enumerate(("DX", "DY", "DZ")):
        if c in f.components:
            out[:, i] = results.nodal_values(med_name, c, nume_ordre)
    return np.nan_to_num(out)


def _quiet_vtk() -> None:
    try:
        from vtkmodules.vtkCommonCore import vtkLogger

        vtkLogger.SetStderrVerbosity(vtkLogger.VERBOSITY_OFF)
    except ImportError:  # pragma: no cover - older VTK
        pass


def _draw(
    pv: Any,
    grid: Any,
    values: np.ndarray,
    bar_title: str,
    path: Path,
    size: tuple[int, int],
    vectors: np.ndarray | None = None,
    scale: float = 0.0,
) -> None:
    plotter = pv.Plotter(off_screen=True, window_size=list(size))
    try:
        plotter.set_background("white")
        shown = grid.copy()
        if vectors is not None:
            with warnings.catch_warnings():  # pyvista >= 0.47 warns of a future default
                warnings.simplefilter("ignore")
                edges = grid.extract_surface().extract_feature_edges(feature_angle=30)
            plotter.add_mesh(edges, color="gray", line_width=1)
            shown.points = grid.points + scale * vectors
        shown.point_data["value"] = values
        plotter.add_mesh(
            shown,
            scalars="value",
            cmap="viridis",
            nan_color="lightgray",
            scalar_bar_args={
                "title": bar_title,
                "color": "black",
                "fmt": "%.3g",
                "n_labels": 6,
                "vertical": True,
                "position_x": 0.85,
                "position_y": 0.1,
                "height": 0.8,
                "width": 0.06,
            },
        )
        plotter.view_isometric()
        plotter.reset_camera()
        plotter.screenshot(str(path))
    finally:
        plotter.close()


def render(figures: list[Figure], results: Any, out_dir: str | Path, model: Any) -> list[Figure]:
    """Render ``figures`` into ``<out_dir>/images``; on failure set each figure's ``reason``."""
    if not figures:
        return figures
    ok, reason = available()
    if not ok or results is None:
        for f in figures:
            f.reason = reason or "no results file"
        return figures
    import pyvista as pv

    _quiet_vtk()
    image_dir = Path(out_dir) / IMAGE_DIR
    image_dir.mkdir(parents=True, exist_ok=True)
    try:
        points, cells, types = _grid_arrays(results.mesh)
    except ValueError as exc:
        for f in figures:
            f.reason = str(exc)
        return figures
    grid = pv.UnstructuredGrid(cells, types, points)
    diagonal = float(np.linalg.norm(points.max(axis=0) - points.min(axis=0)))
    system = model.units.get("system")
    for f in figures:
        name = f.kind if f.nume_ordre is None else f"{f.kind}_{f.nume_ordre}"
        path = image_dir / f"{name}.png"
        try:
            if f.kind == "von_mises":
                values = results.nodal_values(f.med_name, "VMIS")
                stress = unit(system, "stress")
                title = f"von Mises{f' [{stress}]' if stress else ''}"
                _draw(pv, grid, values, title, path, WINDOW)
            else:
                vectors = _vectors(results, f.med_name, f.nume_ordre)
                magnitude = np.linalg.norm(vectors, axis=1)
                peak = float(magnitude.max())
                f.scale = _nice(DEFORMATION_FRACTION * diagonal / peak) if peak > 0 else 0.0
                if f.kind == "mode_shape":
                    title, size = "Mode shape (normalized)", THUMBNAIL
                else:
                    length = unit(system, "length")
                    title, size = f"Displacement{f' [{length}]' if length else ''}", WINDOW
                _draw(pv, grid, magnitude, title, path, size, vectors, f.scale)
        except (KeyError, ValueError, RuntimeError) as exc:
            f.reason = f"rendering failed ({exc})"
            continue
        f.file = f"{IMAGE_DIR}/{path.name}"
    return figures


__all__ = ["Figure", "available", "plan", "render"]
