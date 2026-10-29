"""Applied-load resultant and reaction balance (task 4.6, ``docs/REPORT-SPEC.md`` §3 item 10).

The report may only sum, never compute physics (REPORT-SPEC §1). The resultant of a uniform
load is such a sum: value times the vector area (faces), length (edges) or node count (nodal
forces) of the cells it is applied to, read from the mesh the solver used (the ``.rmed`` mesh,
written after ``MODI_MAILLAGE``). Loads whose resultant is not a plain sum (gravity needs the
mass, a function of space needs integration, a load multiplier function needs the time) are
listed as "not evaluated", and the balance check then says it is incomplete.

Conventions, with their sources:

- ``PRES_REP``: a positive pressure pushes against the face normal, so the force on a face is
  ``-PRES * A * n``; ``ORIE_PEAU`` makes skin normals point out of the solid and
  ``ORIE_NORM_COQUE`` sets shell normals (``en/commands/AFFE_CHAR_MECA.md``; checked by the
  ``solid_static`` and ``shell_static`` fixtures, whose reaction sums the solver tested with
  ``TEST_RESU``).
- ``FORCE_NODALE``: the full force is applied at every node of the group, not shared
  (``upstream/bibfor/load/cafono.F90:271``, ``en/commands/AFFE_CHAR_MECA.md``).
- ``FORCE_FACE`` / ``FORCE_ARETE``: ``FX``, ``FY``, ``FZ`` are per unit area / length, in global
  axes (catalog ``affe_char_meca.py``; glossary).
- ``REAC_NODA`` is the force the supports exert on the structure (glossary), so in equilibrium
  the reaction sum plus the applied resultant is zero.

When two occurrences of the same load keyword in one load touch the same element or node, the
resultant is not evaluated: which value the solver keeps is not checked here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from codeaster_en.report.comm import Call, CommandFile, Ref, Unevaluated, as_list
from codeaster_en.results.med import Mesh

AXES = ("DX", "DY", "DZ")
FORCE_KEYS = ("FX", "FY", "FZ")

# Keywords of AFFE_CHAR_MECA that impose kinematic conditions: they add no external load (their
# reactions are part of REAC_NODA).
KINEMATIC = {
    "DDL_IMPO",
    "FACE_IMPO",
    "ARETE_IMPO",
    "DDL_POUTRE",
    "LIAISON_DDL",
    "LIAISON_OBLIQUE",
    "LIAISON_GROUP",
    "LIAISON_MAIL",
    "LIAISON_PROJ",
    "LIAISON_SOLIDE",
    "LIAISON_ELEM",
    "LIAISON_UNIF",
    "LIAISON_CHAMNO",
    "LIAISON_RBE3",
    "LIAISON_INTERF",
    "LIAISON_COQUE",
    "LIAISON_CYCL",
    "MECA_IMPO",
}
# Keywords that set options, not loads.
OPTIONS = {"MODELE", "INFO", "VERI_NORM", "VERI_AFFE", "DOUBLE_LAGRANGE", "SYNTAXE", "reuse"}
EVALUATED = ("PRES_REP", "FORCE_NODALE", "FORCE_FACE", "FORCE_ARETE")
# Body loads: their resultant needs the mass distribution, which is physics, not a sum
# (REPORT-SPEC §1), so they are never evaluated.
BODY_LOADS = ("PESANTEUR", "ROTATION", "FORCE_INTERNE")
LOAD_COMMANDS = ("AFFE_CHAR_MECA", "AFFE_CHAR_MECA_F", "AFFE_CHAR_CINE", "AFFE_CHAR_CINE_F")

# Node order around the boundary of a face (corner and mid-side nodes, MED numbering).
FACE_LOOPS = {
    "TR3": (0, 1, 2),
    "TR6": (0, 3, 1, 4, 2, 5),
    "TR7": (0, 3, 1, 4, 2, 5),
    "QU4": (0, 1, 2, 3),
    "QU8": (0, 4, 1, 5, 2, 6, 3, 7),
    "QU9": (0, 4, 1, 5, 2, 6, 3, 7),
}
EDGE_PATHS = {"SE2": (0, 1), "SE3": (0, 2, 1), "SE4": (0, 2, 3, 1)}


@dataclass
class LoadItem:
    """One occurrence of a load keyword in a load of the load case."""

    load: str  # result object name of the load (AFFE_CHAR_MECA concept)
    command: str
    keyword: str
    occurrence: int  # 1-based
    status: str  # "evaluated" | "kinematic" | "not_evaluated"
    targets: list[str] = field(default_factory=list)  # groups, or ["TOUT"]
    values: dict[str, Any] = field(default_factory=dict)
    resultant: dict[str, float] | None = None
    basis: str | None = None
    comm_line: int | None = None


@dataclass
class AppliedLoads:
    """Resultant force of the loads of one load case (``EXCIT`` of the solve command)."""

    solve_command: str | None
    loads: list[str] = field(default_factory=list)
    items: list[LoadItem] = field(default_factory=list)
    total: dict[str, float] | None = None
    complete: bool = False
    mesh_source: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Balance:
    """Reaction sum against the applied resultant: ``residual = reaction + applied``."""

    reaction: dict[str, float]
    reaction_source: str
    applied: dict[str, float]
    residual: dict[str, float]
    error_percent: float | None  # |residual| / |applied| * 100
    complete: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _cell_masks(mesh: Mesh, occ: dict[str, Any]) -> tuple[dict[str, np.ndarray], list[str]]:
    """Per MED type, a mask of the cells an occurrence names (``GROUP_MA`` or ``TOUT``)."""
    if occ.get("TOUT") == "OUI":
        return {t: np.ones(len(b.numbers), dtype=bool) for t, b in mesh.cells.items()}, ["TOUT"]
    groups = [g for g in as_list(occ.get("GROUP_MA")) if isinstance(g, str)]
    masks = {t: np.zeros(len(b.numbers), dtype=bool) for t, b in mesh.cells.items()}
    for g in groups:
        for t, (_block, mask) in mesh.group_cells(g).items():
            masks[t] |= mask
    return masks, groups


def _face_vectors(mesh: Mesh, med_type: str, mask: np.ndarray) -> np.ndarray:
    loop = FACE_LOOPS[med_type]
    conn = mesh.cells[med_type].connectivity[mask][:, loop]
    pts = mesh.coordinates[conn]
    if pts.shape[-1] == 2:
        pts = np.concatenate([pts, np.zeros(pts.shape[:-1] + (1,))], axis=-1)
    rel = pts - pts[:, :1, :]
    return 0.5 * np.cross(rel, np.roll(rel, -1, axis=1)).sum(axis=1)


def _edge_lengths(mesh: Mesh, med_type: str, mask: np.ndarray) -> np.ndarray:
    path = EDGE_PATHS[med_type]
    pts = mesh.coordinates[mesh.cells[med_type].connectivity[mask][:, path]]
    return np.linalg.norm(np.diff(pts, axis=1), axis=-1).sum(axis=1)


def _vec(v: np.ndarray) -> dict[str, float]:
    return {a: float(x) for a, x in zip(AXES, v, strict=False)}


class _Evaluator:
    def __init__(self, mesh: Mesh) -> None:
        self.mesh = mesh

    def item(self, occ: dict[str, Any], keyword: str) -> tuple[np.ndarray | None, str, Any]:
        """(resultant, basis, touched entities) of one occurrence, or (None, reason, None)."""
        mesh = self.mesh
        if keyword == "FORCE_NODALE":
            forces = [_number(occ.get(k, 0.0)) for k in FORCE_KEYS]
            if any(f is None for f in forces):
                return None, "force value is not a number", None
            if occ.get("TOUT") == "OUI":
                nodes = np.arange(mesh.n_nodes)
            else:
                names = [*as_list(occ.get("GROUP_NO")), *as_list(occ.get("GROUP_MA"))]
                if not names or "NOEUD" in occ or "MAILLE" in occ:
                    return None, "nodes not given by group", None
                nodes = np.unique(np.concatenate([mesh.group_node_indices(str(g)) for g in names]))
            total = np.array(forces) * nodes.size
            return total, f"force × {nodes.size} nodes (full force at every node)", set(nodes)
        if "MAILLE" in occ or "GROUP_MA" not in occ and occ.get("TOUT") != "OUI":
            return None, "elements not given by group", None
        masks, _ = _cell_masks(mesh, occ)
        touched = {(t, int(i)) for t, m in masks.items() for i in np.flatnonzero(m)}
        if keyword in ("PRES_REP", "FORCE_FACE"):
            faces = {t: m for t, m in masks.items() if t in FACE_LOOPS and m.any()}
            others = [t for t, m in masks.items() if t not in FACE_LOOPS and m.any()]
            if not faces:
                return None, "no face elements in the groups (2D models are not evaluated)", None
            if keyword == "PRES_REP":
                pres = _number(occ.get("PRES"))
                extra = [k for k in occ if k not in ("PRES", "GROUP_MA", "TOUT")]
                if pres is None or extra:
                    return None, "only a constant PRES is evaluated", None
                area = sum(_face_vectors(mesh, t, m).sum(axis=0) for t, m in faces.items())
                count = sum(int(m.sum()) for m in faces.values())
                basis = f"-PRES × vector area of {count} faces"
                total = -pres * np.asarray(area)
            else:
                forces = [_number(occ.get(k, 0.0)) for k in FORCE_KEYS]
                if any(f is None for f in forces):
                    return None, "force value is not a number", None
                area = sum(
                    float(np.linalg.norm(_face_vectors(mesh, t, m), axis=1).sum())
                    for t, m in faces.items()
                )
                count = sum(int(m.sum()) for m in faces.values())
                basis = f"force per unit area × area {area:.6g} of {count} faces"
                total = np.array(forces) * area
            if others:
                basis += f" ({', '.join(sorted(others))} elements in the groups ignored)"
            return total, basis, touched
        if keyword == "FORCE_ARETE":
            edges = {t: m for t, m in masks.items() if t in EDGE_PATHS and m.any()}
            forces = [_number(occ.get(k, 0.0)) for k in FORCE_KEYS]
            if not edges or any(f is None for f in forces):
                return None, "no edge elements, or force value is not a number", None
            length = sum(float(_edge_lengths(mesh, t, m).sum()) for t, m in edges.items())
            count = sum(int(m.sum()) for m in edges.values())
            total = np.array(forces) * length
            return total, f"force per unit length × length {length:.6g} of {count} edges", touched
        return None, "load type not evaluated", None


def _excit_loads(solve: Call) -> tuple[list[str], list[str]]:
    loads: list[str] = []
    notes: list[str] = []
    for occ in solve.occurrences("EXCIT"):
        charge = occ.get("CHARGE")
        if isinstance(charge, Ref):
            loads.append(charge.name)
        if "FONC_MULT" in occ:
            name = charge.name if isinstance(charge, Ref) else "?"
            notes.append(f"load {name} has a multiplier function (FONC_MULT): not evaluated")
    for charge in as_list(solve.get("CHARGE")):
        if isinstance(charge, Ref):
            loads.append(charge.name)
    return loads, notes


def applied_loads(
    comm: CommandFile, solve: Call | None, mesh: Mesh | None, mesh_source: str | None
) -> AppliedLoads:
    """Resultant of the loads applied by ``solve`` (a solve command call with ``EXCIT``)."""
    out = AppliedLoads(solve_command=solve.command if solve else None, mesh_source=mesh_source)
    if solve is None:
        out.notes.append("no solve command with applied loads")
        return out
    out.loads, notes = _excit_loads(solve)
    out.notes.extend(notes)
    multiplied = {n.split()[1] for n in notes}
    evaluator = _Evaluator(mesh) if mesh is not None else None
    total = np.zeros(3)
    complete = not notes
    for name in out.loads:
        load = comm.producer(name, before=solve.line)
        if load is None or load.command not in LOAD_COMMANDS:
            out.notes.append(f"load {name}: definition not found in the command file")
            complete = False
            continue
        for keyword, value in load.keywords.items():
            if keyword in OPTIONS:
                continue
            occs = value if isinstance(value, list) else [value]
            seen: set = set()
            for i, occ in enumerate(occs, start=1):
                if not isinstance(occ, dict):
                    continue
                item = LoadItem(
                    load=name,
                    command=load.command,
                    keyword=keyword,
                    occurrence=i,
                    status="not_evaluated",
                    targets=[str(g) for g in _targets(occ)],
                    values={
                        k: v
                        for k, v in occ.items()
                        if k not in ("GROUP_MA", "GROUP_NO", "TOUT", "MAILLE", "NOEUD")
                        and not isinstance(v, Unevaluated | Ref)
                    },
                    comm_line=load.line,
                )
                out.items.append(item)
                if keyword in KINEMATIC:
                    item.status = "kinematic"
                    continue
                if load.command.endswith("_F"):
                    item.basis = "values are functions: not evaluated"
                    complete = False
                    continue
                if name in multiplied:
                    item.basis = "multiplied by a function of time (FONC_MULT): not evaluated"
                    continue
                if keyword in BODY_LOADS:
                    item.basis = "body load: needs the mass distribution, not summed"
                    complete = False
                    continue
                if keyword not in EVALUATED or evaluator is None:
                    item.basis = (
                        "no mesh to sum over" if evaluator is None else "load type not evaluated"
                    )
                    complete = False
                    continue
                try:
                    vec, basis, touched = evaluator.item(occ, keyword)
                except KeyError as exc:
                    vec, basis, touched = None, f"group {exc} not in the result mesh", None
                if vec is not None and touched & seen:
                    vec, basis = None, "overlaps an earlier occurrence of the same keyword"
                item.basis = basis
                if vec is None:
                    complete = False
                    continue
                seen |= touched
                item.status = "evaluated"
                item.resultant = _vec(vec)
                total += vec
    out.total = _vec(total)
    out.complete = complete
    return out


def _targets(occ: dict[str, Any]) -> list[Any]:
    if occ.get("TOUT") == "OUI":
        return ["TOUT"]
    return [*as_list(occ.get("GROUP_MA")), *as_list(occ.get("GROUP_NO"))]


def balance(
    reaction: dict[str, float], reaction_source: str, applied: AppliedLoads
) -> Balance | None:
    """Reaction sum against the applied resultant, force components only."""
    if applied.total is None:
        return None
    r = np.array([reaction.get(a, 0.0) for a in AXES])
    f = np.array([applied.total[a] for a in AXES])
    residual = r + f
    norm = float(np.linalg.norm(f))
    notes = []
    if not applied.complete:
        notes.append(
            "some loads were not evaluated, so the applied resultant is partial and the "
            "balance is indicative only"
        )
    return Balance(
        reaction=_vec(r),
        reaction_source=reaction_source,
        applied=_vec(f),
        residual=_vec(residual),
        error_percent=float(np.linalg.norm(residual)) / norm * 100.0 if norm > 0 else None,
        complete=applied.complete,
        notes=notes,
    )
