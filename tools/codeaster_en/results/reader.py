"""Results of a code_aster run (task 4.5): fields, extrema, reactions, modal table.

``open(path)`` gives a :class:`Results` over one ``.rmed`` file. Everything it returns is a plain
dataclass with ``to_dict()``, so ClearFEA can store it as JSON (``docs/CLEARFEA-INTEGRATION.md``
§2). French names (``DEPL``, ``VMIS``, ``REAC_NODA``) stay as they are; each carries its English
label from the glossary next to it (:mod:`codeaster_en.results.labels`).

What a ``.rmed`` file does not say, and how it is handled:

- **Units.** code_aster has no unit system; the unit attribute is blank (``en/guide/fields.md``).
  Units come from the job (``run.json`` ``units``), not from here.
- **Step parameter.** MED stores one value per step. ``IMPR_RESU`` writes ``INST`` when the
  result has it, otherwise ``FREQ``, otherwise ``CHAR_CRIT`` (``upstream/bibfor/prepost/
  irchme.F90:160``), and the step number is ``NUME_ORDRE``. A static result therefore shows its
  time and a modal result its frequency in Hz; the file does not say which.
- **Node and element IDs.** Node IDs are the 1-based node numbers (``NOE/NUM`` when written,
  otherwise the position: code_aster 17 numbers nodes in MED order). Element IDs are ``MAI/NUM``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from codeaster_en.results.labels import Labels
from codeaster_en.results.med import MedField, MedFile, Mesh, Support
from codeaster_en.results.tables import Table

LOCATIONS = {
    "NOE": "nodes",
    "NOE_MAI": "element nodes",
    "MAI": "elements",
    "MAI_GAUSS": "Gauss points",
}
TRANSLATIONS = ("DX", "DY", "DZ")
ROTATIONS = ("DRX", "DRY", "DRZ")


@dataclass
class StepInfo:
    """One stored step: ``NUME_ORDRE`` and the step value (``INST`` or ``FREQ``, see module)."""

    nume_ordre: int
    value: float


@dataclass
class FieldInfo:
    result: str
    field: str
    med_name: str
    label: str | None
    locations: list[str]
    components: list[str]
    component_labels: dict[str, str | None]
    steps: list[StepInfo]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Extremum:
    """The smallest or largest value of a component over a group (or the whole model).

    ``entity`` is ``node`` (``entity_id`` = node number) for nodal fields, ``element`` for
    element fields (``entity_id`` = element number; ``node_id`` too for values at element nodes).
    ``xyz`` is the node position, or the element centroid for per-element and Gauss-point
    values (the Gauss point position is not in the file)."""

    kind: str  # "min" | "max"
    value: float
    entity: str
    entity_id: int
    xyz: tuple[float, ...]
    node_id: int | None = None
    point: int | None = None


@dataclass
class GroupExtrema:
    field: str
    component: str
    label: str
    group: str | None  # None = whole model
    nume_ordre: int
    count: int  # values considered
    min: Extremum | None
    max: Extremum | None
    location: str
    note: str | None = None

    @property
    def max_abs(self) -> Extremum | None:
        if self.min is None or self.max is None:
            return None
        return self.max if abs(self.max.value) >= abs(self.min.value) else self.min

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["max_abs"] = asdict(self.max_abs) if self.max_abs else None
        return data


@dataclass
class ReactionGroup:
    """Sum of nodal reactions over a group, from the ``.rmed`` field or a printed table."""

    group: str | None  # None = whole model
    source: str  # "rmed:<med field name>" or "table:<file>:<INTITULE>"
    nume_ordre: int
    nodes: int | None
    components: dict[str, float]


@dataclass
class ReactionSummary:
    """Support reactions. ``total`` sums the whole ``REAC_NODA`` field: only nodes with imposed
    DOFs carry a reaction (glossary, ``REAC_NODA``), so it is the reaction of all supports
    together. The applied-load resultant and the balance check (``docs/REPORT-SPEC.md`` §3
    item 10) need the loads of the ``.comm`` and are the report's job (task 4.6)."""

    field: str | None
    per_group: list[ReactionGroup] = field(default_factory=list)
    from_tables: list[ReactionGroup] = field(default_factory=list)
    total: dict[str, float] = field(default_factory=dict)
    labels: dict[str, str | None] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Mode:
    nume_ordre: int
    frequency_hz: float
    period_s: float | None
    generalized_mass: float | None = None
    effective_mass: dict[str, float] = field(default_factory=dict)
    effective_mass_fraction: dict[str, float] = field(default_factory=dict)
    cumulative_fraction: dict[str, float] = field(default_factory=dict)


@dataclass
class ModalTable:
    """Mode, frequency, period and, when the job printed them, effective masses.

    Frequencies come from the modal parameter table when there is one (``RECU_TABLE`` of the
    ``CALC_MODES`` result: ``FREQ``, ``MASS_GENE``, ``MASS_EFFE_D*``, ``MASS_EFFE_UN_D*``), else
    from the step values of the mode shapes in the ``.rmed``. ``total_mass`` comes from a
    ``POST_ELEM`` ``MASS_INER`` table (row ``ENTITE`` = ``TOUT``). The period assumes the model
    time unit is the second (``units.system`` of ``run.json``)."""

    result: str | None
    modes: list[Mode] = field(default_factory=list)
    total_mass: float | None = None
    sources: list[str] = field(default_factory=list)
    labels: dict[str, str | None] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Results:
    """One ``.rmed`` file. Use as a context manager or call :meth:`close`."""

    def __init__(self, path: str | Path, labels: Labels | None = None) -> None:
        self.path = Path(path)
        self.med = MedFile(self.path)
        self.labels = labels or Labels()
        self._fields = {f.med_name: f for f in self.med.fields()}

    def close(self) -> None:
        self.med.close()

    def __enter__(self) -> Results:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ---------- inventory ----------

    @property
    def mesh(self) -> Mesh:
        return self.med.mesh()

    def groups(self) -> dict[str, list[str]]:
        """Node groups and element groups of the mesh as written in the result file."""
        return {"node": self.mesh.node_groups(), "element": self.mesh.cell_groups()}

    def _locations(self, f: MedField) -> list[str]:
        if not f.steps:
            return []
        found = []
        for sup in self.med.supports(f.med_name, f.steps[0]):
            loc = _location(sup)
            if loc not in found:
                found.append(loc)
        return found

    def fields(self) -> list[FieldInfo]:
        out = []
        for f in self._fields.values():
            out.append(
                FieldInfo(
                    result=f.result,
                    field=f.name,
                    med_name=f.med_name,
                    label=self.labels.get(f.name),
                    locations=self._locations(f),
                    components=f.components,
                    component_labels=self.labels.many(f.components),
                    steps=[StepInfo(s.number, s.value) for s in f.steps],
                )
            )
        return out

    def find(self, name: str, result: str | None = None) -> MedField:
        """A field by its code_aster name (``SIEQ_NOEU``) or its MED name (``RESU____SIEQ_NOEU``).
        With several results holding the same field, ``result`` picks one."""
        if name in self._fields:
            return self._fields[name]
        hits = [f for f in self._fields.values() if f.name == name]
        if result is not None:
            hits = [f for f in hits if f.result == result]
        if not hits:
            raise KeyError(f"no field {name!r} in {self.path.name}")
        if len(hits) > 1:
            names = ", ".join(f.med_name for f in hits)
            raise KeyError(f"field {name!r} is in several results ({names}); pass result=")
        return hits[0]

    # ---------- values ----------

    def _step(self, f: MedField, nume_ordre: int | None):
        if not f.steps:
            raise KeyError(f"field {f.med_name} has no stored step")
        if nume_ordre is None:
            return f.steps[-1]
        for s in f.steps:
            if s.number == nume_ordre:
                return s
        raise KeyError(f"field {f.med_name} has no NUME_ORDRE {nume_ordre}")

    def nodal_values(
        self, name: str, component: str | tuple[str, ...], nume_ordre: int | None = None
    ) -> np.ndarray:
        """Values of a nodal field for every node (NaN where the field is not defined).
        A tuple of components gives their Euclidean norm (e.g. ``("DX", "DY", "DZ")``)."""
        f = self.find(name)
        step = self._step(f, nume_ordre)
        comps = (component,) if isinstance(component, str) else tuple(component)
        idx = [_component_index(f, c) for c in comps]
        out = np.full(self.mesh.n_nodes, np.nan)
        for sup in self.med.supports(f.med_name, step):
            if sup.kind == "NOE":
                vals = sup.values[idx, :, 0]
                out[sup.entities] = vals[0] if len(idx) == 1 else np.sqrt((vals**2).sum(axis=0))
        return out

    def extrema(
        self,
        name: str,
        component: str | tuple[str, ...],
        groups: list[str] | None = None,
        nume_ordre: int | None = None,
        whole_model: bool = True,
    ) -> list[GroupExtrema]:
        """Min and max of one component (or of the norm of several) for the whole model and
        for each group. A group may be a node group or an element group: for nodal fields an
        element group means the nodes of its elements; for element fields a node group means
        the values at those nodes (element-node fields only)."""
        f = self.find(name)
        step = self._step(f, nume_ordre)
        comps = (component,) if isinstance(component, str) else tuple(component)
        idx = [_component_index(f, c) for c in comps]
        if len(comps) == 1:
            comp_name = comps[0]
            label = self.labels.describe(comp_name)
        else:
            comp_name = "|" + ",".join(comps) + "|"
            label = "magnitude of " + ", ".join(comps)
        rows = _collect(self.mesh, list(self.med.supports(f.med_name, step)), idx)
        targets: list[str | None] = ([None] if whole_model else []) + list(groups or [])
        out = []
        for group in targets:
            sel, note = _select(self.mesh, rows, group)
            out.append(_extrema_of(rows, sel, f.name, comp_name, label, group, step.number, note))
        return out

    # ---------- reactions ----------

    def reactions(
        self,
        groups: list[str] | None = None,
        tables: list[Table] | None = None,
        field_name: str = "REAC_NODA",
        nume_ordre: int | None = None,
    ) -> ReactionSummary:
        """Reaction sums per group from the ``REAC_NODA`` field (if written to the ``.rmed``) and
        from ``POST_RELEVE_T`` ``RESULTANTE`` tables (any printed table with ``INTITULE`` and
        ``NOM_CHAM`` = ``REAC_NODA``)."""
        summary = ReactionSummary(field=None)
        comps: list[str] = []
        try:
            f = self.find(field_name)
        except KeyError:
            f = None
            summary.notes.append(
                f"{field_name} is not in {self.path.name}: add it to IMPR_RESU NOM_CHAM "
                "(after CALC_CHAMP FORCE='REAC_NODA') to get reaction sums per group."
            )
        if f is not None:
            summary.field = f.med_name
            step = self._step(f, nume_ordre)
            comps = [c for c in f.components if c in TRANSLATIONS + ROTATIONS]
            values = {c: self.nodal_values(f.med_name, c, step.number) for c in comps}
            summary.total = {c: float(np.nansum(v)) for c, v in values.items()}
            for group in groups or []:
                nodes = self.mesh.group_node_indices(group)
                summary.per_group.append(
                    ReactionGroup(
                        group=group,
                        source=f"rmed:{f.med_name}",
                        nume_ordre=step.number,
                        nodes=int(nodes.size),
                        components={c: float(np.nansum(v[nodes])) for c, v in values.items()},
                    )
                )
        for table in tables or []:
            if not table.has("INTITULE", "NOM_CHAM"):
                continue
            for row in table.rows:
                if str(row.get("NOM_CHAM", "")).strip() != field_name:
                    continue
                values = {
                    c: float(row[c])
                    for c in TRANSLATIONS + ROTATIONS
                    if c in table.columns and isinstance(row.get(c), int | float)
                }
                summary.from_tables.append(
                    ReactionGroup(
                        group=None,
                        source=f"table:{Path(table.source or '').name}:{row['INTITULE']}",
                        nume_ordre=int(row.get("NUME_ORDRE") or 1),
                        nodes=None,
                        components=values,
                    )
                )
                comps = comps or list(values)
        summary.labels = self.labels.many(list(TRANSLATIONS + ROTATIONS))
        return summary

    # ---------- modal ----------

    def modal(self, tables: list[Table] | None = None, result: str | None = None) -> ModalTable:
        """Modal table: from a modal parameter table if one was printed, else from the
        ``.rmed`` step values; effective-mass fractions from the table, or computed from
        ``MASS_EFFE_D*`` and the ``POST_ELEM`` total mass."""
        table = ModalTable(result=result)
        tables = tables or []
        param = next((t for t in tables if t.has("NUME_ORDRE", "FREQ")), None)
        mass = next((t for t in tables if t.has("MASSE", "ENTITE")), None)
        if mass is not None:
            row = next((r for r in mass.rows if str(r.get("ENTITE")).strip() == "TOUT"), None)
            if row is not None and isinstance(row.get("MASSE"), int | float):
                table.total_mass = float(row["MASSE"])
                table.sources.append(f"table:{Path(mass.source or '').name}:MASSE")
        shapes = self._modal_field(result)
        exact = {s.number: s.value for s in shapes.steps} if shapes is not None else {}
        if param is not None:
            table.sources.append(f"table:{Path(param.source or '').name}")
            if exact:
                table.sources.append(f"rmed:{shapes.med_name} step values (frequencies)")
            for row in param.rows:
                # The .rmed keeps full precision; the printed table has 6 significant figures.
                freq = exact.get(int(row["NUME_ORDRE"]), float(row["FREQ"]))
                if abs(freq - float(row["FREQ"])) > 1e-5 * abs(freq):
                    table.notes.append(
                        f"mode {row['NUME_ORDRE']}: table FREQ {row['FREQ']} differs from the "
                        f".rmed step value {freq}; check that both come from the same result"
                    )
                mode = Mode(
                    nume_ordre=int(row["NUME_ORDRE"]),
                    frequency_hz=freq,
                    period_s=1.0 / freq if freq > 0 else None,
                    generalized_mass=_num(row.get("MASS_GENE")),
                )
                for axis in TRANSLATIONS:
                    eff = _num(row.get(f"MASS_EFFE_{axis}"))
                    frac = _num(row.get(f"MASS_EFFE_UN_{axis}"))
                    if eff is not None:
                        mode.effective_mass[axis] = eff
                    if frac is None and eff is not None and table.total_mass:
                        frac = eff / table.total_mass
                    if frac is not None:
                        mode.effective_mass_fraction[axis] = frac
                table.modes.append(mode)
        else:
            f = shapes
            if f is None:
                table.notes.append(f"no modal result in {self.path.name} and no modal table")
                return table
            table.result = f.result
            table.sources.append(f"rmed:{f.med_name} step values")
            table.notes.append(
                "frequencies from the .rmed step values; print RECU_TABLE(CO=<modes>, "
                "NOM_PARA=(...MASS_EFFE_UN_DX...)) with IMPR_TABLE for effective masses"
            )
            for s in f.steps:
                table.modes.append(
                    Mode(
                        nume_ordre=s.number,
                        frequency_hz=s.value,
                        period_s=1.0 / s.value if s.value > 0 else None,
                    )
                )
        table.modes.sort(key=lambda m: m.nume_ordre)
        running: dict[str, float] = {}
        for mode in table.modes:
            for axis, frac in mode.effective_mass_fraction.items():
                running[axis] = running.get(axis, 0.0) + frac
                mode.cumulative_fraction[axis] = running[axis]
        if table.result is None and shapes is not None:
            table.result = shapes.result
        names = ["NUME_ORDRE", "FREQ", "MASS_GENE", "MASSE"]
        names += [f"MASS_EFFE_{a}" for a in TRANSLATIONS]
        names += [f"MASS_EFFE_UN_{a}" for a in TRANSLATIONS]
        table.labels = self.labels.many(names)
        return table

    def _modal_field(self, result: str | None) -> MedField | None:
        """The ``DEPL`` field of a result with several steps (mode shapes)."""
        cands = [
            f
            for f in self._fields.values()
            if f.name == "DEPL" and (result is None or f.result == result)
        ]
        cands.sort(key=lambda f: len(f.steps), reverse=True)
        return cands[0] if cands else None


def _num(value: Any) -> float | None:
    return float(value) if isinstance(value, int | float) else None


def _location(sup: Support) -> str:
    if sup.kind == "MAI" and sup.points > 1:
        return LOCATIONS["MAI_GAUSS"]
    return LOCATIONS[sup.kind]


def _component_index(f: MedField, component: str) -> int:
    try:
        return f.components.index(component)
    except ValueError:
        raise KeyError(
            f"field {f.name} has no component {component!r} (has {', '.join(f.components)})"
        ) from None


@dataclass
class _Rows:
    """Every value of one step, flattened: one row per (entity, point)."""

    values: np.ndarray
    entity: str  # node | element
    entity_ids: np.ndarray
    node_index: np.ndarray  # -1 when not at a node
    node_ids: np.ndarray  # node numbers (-1 when not at a node)
    cell_type: np.ndarray  # MED type per row ("" for nodes)
    cell_index: np.ndarray  # index within the type block (-1 for nodes)
    point: np.ndarray
    xyz: np.ndarray
    location: str


def _collect(mesh: Mesh, supports: list[Support], idx: list[int]) -> _Rows:
    nodal = [s for s in supports if s.kind == "NOE"]
    chosen = nodal or supports
    vals, ids, nodes, node_ids, types, cells, points, xyz = [], [], [], [], [], [], [], []
    locations = []
    for sup in chosen:
        v = sup.values[idx]  # (ncomp, n, points)
        v = v[0] if len(idx) == 1 else np.sqrt((v**2).sum(axis=0))
        n, p = v.shape
        locations.append(_location(sup))
        if sup.kind == "NOE":
            vals.append(v[:, 0])
            ids.append(mesh.node_numbers[sup.entities])
            nodes.append(sup.entities)
            node_ids.append(mesh.node_numbers[sup.entities])
            types.append(np.full(n, "", dtype=object))
            cells.append(np.full(n, -1))
            points.append(np.zeros(n, dtype=int))
            xyz.append(mesh.coordinates[sup.entities])
            continue
        block = mesh.cells[sup.med_type]
        conn = block.connectivity[sup.entities]
        vals.append(v.ravel())
        ids.append(np.repeat(block.numbers[sup.entities], p))
        types.append(np.full(n * p, sup.med_type, dtype=object))
        cells.append(np.repeat(sup.entities, p))
        points.append(np.tile(np.arange(p), n))
        if sup.kind == "NOE_MAI":
            node_idx = conn[:, :p].ravel()
            nodes.append(node_idx)
            node_ids.append(mesh.node_numbers[node_idx])
            xyz.append(mesh.coordinates[node_idx])
        else:
            nodes.append(np.full(n * p, -1))
            node_ids.append(np.full(n * p, -1))
            centroids = mesh.coordinates[conn].mean(axis=1)
            xyz.append(np.repeat(centroids, p, axis=0))
    if not vals:
        empty = np.array([])
        return _Rows(empty, "node", empty, empty, empty, empty, empty, empty, np.zeros((0, 3)), "")
    return _Rows(
        values=np.concatenate(vals),
        entity="node" if nodal else "element",
        entity_ids=np.concatenate(ids),
        node_index=np.concatenate(nodes),
        node_ids=np.concatenate(node_ids),
        cell_type=np.concatenate(types),
        cell_index=np.concatenate(cells),
        point=np.concatenate(points),
        xyz=np.concatenate(xyz),
        location=", ".join(dict.fromkeys(locations)),
    )


def _select(mesh: Mesh, rows: _Rows, group: str | None) -> tuple[np.ndarray, str | None]:
    if group is None:
        return np.ones(rows.values.shape[0], dtype=bool), None
    if not mesh.has_group(group):
        raise KeyError(f"no group {group!r} in the result mesh")
    if rows.entity == "node":
        nodes = mesh.group_node_indices(group)
        return np.isin(rows.node_index, nodes), None
    if group in mesh.cell_groups():
        sel = np.zeros(rows.values.shape[0], dtype=bool)
        for med_type, (_block, mask) in mesh.group_cells(group).items():
            in_type = rows.cell_type == med_type
            sel |= in_type & np.isin(rows.cell_index, np.flatnonzero(mask))
        return sel, None
    nodes = mesh.group_node_indices(group)
    sel = np.isin(rows.node_index, nodes)
    note = None if sel.any() else "node group: values of this field are not at nodes"
    return sel, note


def _extrema_of(
    rows: _Rows,
    sel: np.ndarray,
    field_name: str,
    comp: str,
    label: str,
    group: str | None,
    nume_ordre: int,
    note: str | None,
) -> GroupExtrema:
    mask = sel & np.isfinite(rows.values)
    result = GroupExtrema(
        field=field_name,
        component=comp,
        label=label,
        group=group,
        nume_ordre=nume_ordre,
        count=int(mask.sum()),
        min=None,
        max=None,
        location=rows.location,
        note=note,
    )
    if not mask.any():
        result.note = note or "no value of this field in the group"
        return result
    where = np.flatnonzero(mask)
    for kind, pick in (("min", np.argmin), ("max", np.argmax)):
        i = int(where[pick(rows.values[where])])
        node_id = int(rows.node_ids[i])
        ext = Extremum(
            kind=kind,
            value=float(rows.values[i]),
            entity=rows.entity,
            entity_id=int(rows.entity_ids[i]),
            xyz=tuple(float(x) for x in rows.xyz[i]),
            node_id=node_id if rows.entity == "element" and node_id >= 0 else None,
            point=int(rows.point[i]) + 1 if rows.entity == "element" else None,
        )
        setattr(result, kind, ext)
    return result


def open(path: str | Path, labels: Labels | None = None) -> Results:  # noqa: A001
    """Open a ``.rmed`` / ``.med`` result file."""
    return Results(path, labels=labels)
