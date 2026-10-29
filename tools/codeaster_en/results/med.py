"""Native MED reader over ``h5py`` (task 4.5; ADR-015).

A ``.rmed`` / ``.med`` file is HDF5 with the MED layout. The parts this reader uses, as written
by ``IMPR_RESU(FORMAT="MED")`` in our fixtures (``tests/fixtures/*/output/run.rmed``, MED 3.3):

- ``/ENS_MAA/<mesh>/<step>/NOE/COO`` node coordinates; ``NOE/NUM`` node numbers (optional);
  ``NOE/FAM`` node family numbers (optional; absent when no node group exists).
- ``/ENS_MAA/<mesh>/<step>/MAI/<type>/NOD`` connectivity (1-based node indices), ``NUM`` cell
  numbers, ``FAM`` cell family numbers; ``<type>`` is a three-letter MED type (``TE4``, ``QU4``).
- ``/FAS/<mesh>/NOEUD/<family>`` (positive numbers) and ``/FAS/<mesh>/ELEME/<family>``
  (negative numbers) list the groups of each family in ``GRO/NOM`` (80-character names).
- ``/CHA/<field>`` attributes ``MAI`` (mesh), ``NCO``/``NOM`` (component names, 16 characters
  each), ``UNI`` (units, blank in code_aster files); one subgroup per step with attributes
  ``NDT``/``NOR`` (step and order numbers) and ``PDT`` (the step value: ``INST`` for a static
  result, ``FREQ`` for a modal one). Under a step, ``NOE`` holds nodal values, ``MAI.<type>``
  values per cell (``ELEM``) or per Gauss point (``ELGA``, ``NGA`` > 1), and ``NOE.<type>``
  values at the nodes of each cell (``ELNO``). Each support has one subgroup per profile with
  ``NBR`` (entities), ``NGA`` (points per entity) and the values ``CO``.

Every dataset is stored *no-interlace*: all values of the first component, then the second, and
for cell supports, entity-major then point (checked against ``medcoupling`` in
``tests/test_results.py``). Profiles (``/PROFILS/<name>/PFL``) select a subset of entities.

``IMPR_RESU`` names a field ``<result name padded to 8 with _><field name>`` (``RESU____DEPL``,
``MODES___DEPL``; ``en/guide/fields.md``), so the result and field names are split here.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import h5py
import numpy as np

NO_PROFILE = "MED_NO_PROFILE_INTERNAL"
GROUP_NAME_LENGTH = 80
COMPONENT_NAME_LENGTH = 16

# MED type name -> number of nodes (corner and mid-side). Others are read from NOD's size.
MED_TYPES: dict[str, int] = {
    "PO1": 1,
    "SE2": 2,
    "SE3": 3,
    "SE4": 4,
    "TR3": 3,
    "TR6": 6,
    "TR7": 7,
    "QU4": 4,
    "QU8": 8,
    "QU9": 9,
    "TE4": 4,
    "T10": 10,
    "PY5": 5,
    "P13": 13,
    "PE6": 6,
    "P15": 15,
    "P18": 18,
    "HE8": 8,
    "H20": 20,
    "H27": 27,
}


def _text(value: object) -> str:
    if isinstance(value, bytes | np.bytes_):
        return bytes(value).decode("latin-1").rstrip("\x00 ").strip()
    return str(value).strip()


def _fixed(value: object, width: int) -> list[str]:
    """Split a MED fixed-width name list (``NOM`` of a field: 16 characters per component)."""
    raw = bytes(value) if isinstance(value, bytes | np.bytes_) else str(value).encode("latin-1")
    raw = raw.rstrip(b"\x00")
    names = [raw[i : i + width].decode("latin-1").strip() for i in range(0, len(raw), width)]
    return names


def _group_names(dataset: h5py.Dataset) -> list[str]:
    data = dataset[()]
    names = []
    for row in np.atleast_1d(data):
        names.append(bytes(np.asarray(row, dtype=np.int8).tobytes()).split(b"\x00")[0].decode())
    return [n.strip() for n in names]


def split_med_name(med_name: str) -> tuple[str, str]:
    """``RESU____SIEQ_NOEU`` -> (``RESU``, ``SIEQ_NOEU``). Names shorter than 9 characters are
    a field with no result prefix (a ``CHAM_GD`` printed alone): (``""``, name)."""
    if len(med_name) <= 8:
        return "", med_name
    return med_name[:8].rstrip("_"), med_name[8:]


@dataclass
class CellBlock:
    """All cells of one MED type: connectivity (0-based node indices), numbers, families."""

    med_type: str
    connectivity: np.ndarray  # (n_cells, n_nodes_per_cell)
    numbers: np.ndarray  # (n_cells,) cell numbers as code_aster prints them
    families: np.ndarray  # (n_cells,)


@dataclass
class Mesh:
    name: str
    dimension: int
    axes: list[str]
    coordinates: np.ndarray  # (n_nodes, space dimension)
    node_numbers: np.ndarray  # (n_nodes,)
    node_families: np.ndarray  # (n_nodes,)
    cells: dict[str, CellBlock]
    node_family_groups: dict[int, list[str]] = field(default_factory=dict)
    cell_family_groups: dict[int, list[str]] = field(default_factory=dict)

    @property
    def n_nodes(self) -> int:
        return int(self.coordinates.shape[0])

    def node_groups(self) -> list[str]:
        return sorted({g for gs in self.node_family_groups.values() for g in gs})

    def cell_groups(self) -> list[str]:
        return sorted({g for gs in self.cell_family_groups.values() for g in gs})

    def _families_with(self, mapping: dict[int, list[str]], group: str) -> list[int]:
        return [num for num, groups in mapping.items() if group in groups]

    def group_node_indices(self, group: str) -> np.ndarray:
        """0-based node indices of a node group, or of the nodes of an element group when no
        node group has that name. Raises ``KeyError`` for an unknown group."""
        fams = self._families_with(self.node_family_groups, group)
        if fams:
            return np.flatnonzero(np.isin(self.node_families, fams))
        if group in self.cell_groups():
            nodes = [
                block.connectivity[mask].ravel()
                for block, mask in self.group_cells(group).values()
                if mask.any()
            ]
            return np.unique(np.concatenate(nodes)) if nodes else np.array([], dtype=int)
        raise KeyError(group)

    def group_cells(self, group: str) -> dict[str, tuple[CellBlock, np.ndarray]]:
        """Per MED type, the cell block and a boolean mask of the cells in an element group."""
        fams = self._families_with(self.cell_family_groups, group)
        if not fams:
            raise KeyError(group)
        return {t: (b, np.isin(b.families, fams)) for t, b in self.cells.items()}

    def has_group(self, group: str) -> bool:
        return group in self.node_groups() or group in self.cell_groups()


@dataclass
class Step:
    """One stored step of a field: MED step/order numbers and the step value (``PDT``)."""

    number: int
    order: int
    value: float
    key: str


@dataclass
class Support:
    """Values of one step on one support. ``kind`` is ``NOE`` (nodes), ``MAI`` (per cell or per
    Gauss point) or ``NOE_MAI`` (at the nodes of each cell, MED ``NOE.<type>``)."""

    kind: str
    med_type: str | None
    entities: np.ndarray  # 0-based indices into nodes, or into the cells of med_type
    points: int
    values: np.ndarray  # (n_components, n_entities, points)


@dataclass
class MedField:
    med_name: str
    result: str
    name: str
    mesh: str
    components: list[str]
    units: list[str]
    steps: list[Step]


class MedFile:
    """Read access to one MED file. Everything is read on demand and closed by :meth:`close`."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._h5 = h5py.File(self.path, "r")
        self._meshes: dict[str, Mesh] = {}

    def close(self) -> None:
        self._h5.close()

    def __enter__(self) -> MedFile:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ---------- meshes ----------

    def mesh_names(self) -> list[str]:
        return sorted(self._h5.get("ENS_MAA", {}).keys())

    def mesh(self, name: str | None = None) -> Mesh:
        names = self.mesh_names()
        if not names:
            raise ValueError(f"{self.path}: no mesh in file")
        name = name or names[0]
        if name not in self._meshes:
            self._meshes[name] = self._read_mesh(name)
        return self._meshes[name]

    def _read_mesh(self, name: str) -> Mesh:
        group = self._h5["ENS_MAA"][name]
        space = int(group.attrs.get("ESP", group.attrs.get("DIM", 3)))
        axes = _fixed(group.attrs.get("NOM", b""), COMPONENT_NAME_LENGTH)[:space]
        steps = [k for k in group.keys() if isinstance(group[k], h5py.Group)]
        if not steps:
            raise ValueError(f"{self.path}: mesh {name} has no data")
        data = group[sorted(steps)[0]]
        noe = data["NOE"]
        coords = noe["COO"][()].reshape(space, -1).T.copy()
        n_nodes = coords.shape[0]
        numbers = noe["NUM"][()] if "NUM" in noe else np.arange(1, n_nodes + 1)
        families = noe["FAM"][()] if "FAM" in noe else np.zeros(n_nodes, dtype=np.int64)
        cells: dict[str, CellBlock] = {}
        running = 0
        for med_type, block in data["MAI"].items() if "MAI" in data else []:
            nod = block["NOD"][()]
            n_cells = int(block["FAM"].shape[0]) if "FAM" in block else None
            if n_cells is None:
                n_cells = nod.size // MED_TYPES.get(med_type, 1)
            conn = nod.reshape(-1, n_cells).T - 1
            nums = block["NUM"][()] if "NUM" in block else np.arange(1, n_cells + 1) + running
            fams = block["FAM"][()] if "FAM" in block else np.zeros(n_cells, dtype=np.int64)
            cells[med_type] = CellBlock(med_type, conn, nums, fams)
            running += n_cells
        node_fams: dict[int, list[str]] = {}
        cell_fams: dict[int, list[str]] = {}
        fas = self._h5.get(f"FAS/{name}")
        if fas is not None:
            for part, target in (("NOEUD", node_fams), ("ELEME", cell_fams)):
                for fam in fas.get(part, {}).values():
                    if "GRO" in fam:
                        target[int(fam.attrs["NUM"])] = _group_names(fam["GRO"]["NOM"])
        return Mesh(
            name=name,
            dimension=int(group.attrs.get("DIM", space)),
            axes=axes or ["X", "Y", "Z"][:space],
            coordinates=coords,
            node_numbers=np.asarray(numbers),
            node_families=np.asarray(families),
            cells=cells,
            node_family_groups=node_fams,
            cell_family_groups=cell_fams,
        )

    # ---------- fields ----------

    def fields(self) -> list[MedField]:
        out = []
        for med_name, grp in sorted(self._h5.get("CHA", {}).items()):
            ncomp = int(grp.attrs.get("NCO", 0))
            comps = _fixed(grp.attrs.get("NOM", b""), COMPONENT_NAME_LENGTH)[:ncomp]
            units = _fixed(grp.attrs.get("UNI", b""), COMPONENT_NAME_LENGTH)[:ncomp]
            steps = []
            for key, step in grp.items():
                steps.append(
                    Step(
                        number=int(step.attrs.get("NDT", -1)),
                        order=int(step.attrs.get("NOR", -1)),
                        value=float(step.attrs.get("PDT", 0.0)),
                        key=key,
                    )
                )
            steps.sort(key=lambda s: (s.number, s.order))
            result, name = split_med_name(med_name)
            out.append(
                MedField(
                    med_name=med_name,
                    result=result,
                    name=name,
                    mesh=_text(grp.attrs.get("MAI", b"")),
                    components=comps,
                    units=units,
                    steps=steps,
                )
            )
        return out

    def supports(self, med_name: str, step: Step) -> Iterator[Support]:
        """The values of one step, support by support (nodes, then each cell type)."""
        mesh = self.mesh(_text(self._h5["CHA"][med_name].attrs.get("MAI", b"")) or None)
        group = self._h5["CHA"][med_name][step.key]
        ncomp = int(self._h5["CHA"][med_name].attrs.get("NCO", 1))
        for key, sup in group.items():
            if key == "NOE":
                kind, med_type, total = "NOE", None, mesh.n_nodes
            elif key.startswith("MAI.") or key.startswith("NOE."):
                med_type = key[4:]
                kind = "MAI" if key.startswith("MAI.") else "NOE_MAI"
                block = mesh.cells.get(med_type)
                total = block.connectivity.shape[0] if block is not None else 0
            else:  # faces/edges of structured meshes (FAC, ARE) are not written by code_aster
                continue
            for pfl_name, pfl in sup.items():
                n = int(pfl.attrs["NBR"])
                points = int(pfl.attrs.get("NGA", 1))
                values = pfl["CO"][()].reshape(ncomp, n, points)
                if pfl_name == NO_PROFILE:
                    entities = np.arange(total)
                else:
                    entities = self._h5["PROFILS"][pfl_name]["PFL"][()] - 1
                yield Support(kind, med_type, np.asarray(entities), points, values)
