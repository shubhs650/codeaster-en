"""Job directory helpers for a solver worker (task 6.3, docs/CLEARFEA-INTEGRATION.md §3–§5).

``write_export`` writes ``input/run.export`` with the logical units the builder and the report
expect, and ``precheck`` finds, before any machine time is spent, the two ``user-model``
faults that need no solver: a command file that is not Python, and a group the command file
names that the mesh does not have (``MODELISA7_77`` at run time). Running ``run_aster`` stays
with the worker: it owns the container, the queue, timeouts and cancellation.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from codeaster_en.results.med import MedFile

# Logical units of the job layout. The builder's defaults use the same numbers
# (``read_mesh(unit=20)``, ``write_med(unit=80)``); tables start at 30 (``print_table(unit=...)``).
UNIT_COMM = 1
UNIT_MESH = 20
UNIT_MESS = 6
UNIT_RESU = 8
UNIT_RMED = 80
FIRST_TABLE_UNIT = 30

INPUT = "input"
OUTPUT = "output"
REPORT = "report"


def export_text(
    tables: Mapping[int, str] | None = None,
    *,
    time_limit_s: int = 600,
    memory_mb: int = 2048,
    ncpus: int = 1,
) -> str:
    """Text of ``run.export`` for the layout of §3, run from ``input/``.

    ``tables`` maps an ``IMPR_TABLE`` unit (the ``unit`` given to ``Builder.print_table``) to
    a file name under ``output/tables/``. ``ncpus`` is threads in one process; MPI stays at
    one process (§8).
    """
    tables = dict(tables or {})
    for unit, name in tables.items():
        if not FIRST_TABLE_UNIT <= unit < UNIT_RMED:
            raise ValueError(f"table unit {unit} is outside {FIRST_TABLE_UNIT}..{UNIT_RMED - 1}")
        if "/" in name or not name:
            raise ValueError(f"table file name {name!r} must be a plain file name")
    lines = [
        f"P time_limit {int(time_limit_s)}",
        f"P memory_limit {int(memory_mb)}",
        f"P ncpus {int(ncpus)}",
        "P mpi_nbcpu 1",
        "P mpi_nbnoeud 1",
        f"F comm run.comm D {UNIT_COMM}",
        f"F mmed mesh.med D {UNIT_MESH}",
        f"F mess ../{OUTPUT}/run.mess R {UNIT_MESS}",
        f"F resu ../{OUTPUT}/run.resu R {UNIT_RESU}",
        *(f"F libr ../{OUTPUT}/tables/{tables[u]} R {u}" for u in sorted(tables)),
        f"F rmed ../{OUTPUT}/run.rmed R {UNIT_RMED}",
    ]
    return "\n".join(lines) + "\n"


def write_export(
    job: str | Path,
    tables: Mapping[int, str] | None = None,
    *,
    time_limit_s: int = 600,
    memory_mb: int = 2048,
    ncpus: int = 1,
) -> Path:
    """Write ``<job>/input/run.export`` and create ``<job>/output/tables/``; return the path."""
    job = Path(job)
    (job / INPUT).mkdir(parents=True, exist_ok=True)
    (job / OUTPUT / "tables").mkdir(parents=True, exist_ok=True)
    path = job / INPUT / "run.export"
    path.write_text(
        export_text(tables, time_limit_s=time_limit_s, memory_mb=memory_mb, ncpus=ncpus),
        encoding="utf-8",
    )
    return path


@dataclass(frozen=True)
class Problem:
    """A fault found before the run. ``kind`` is ``syntax`` or ``missing_group``."""

    kind: str
    message: str
    line: int | None = None
    command: str | None = None
    keyword: str | None = None
    group: str | None = None
    failure_class: str = "user-model"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _strings(node: ast.expr) -> list[str] | None:
    """The group names of a literal value (a string or a tuple/list of strings), else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.Tuple | ast.List):
        names = [_strings(e) for e in node.elts]
        if all(n is not None and len(n) == 1 for n in names):
            return [n[0] for n in names]  # type: ignore[index]
    return None


def _is_group_keyword(name: str | None, prefix: str) -> bool:
    return name is not None and (name == prefix or name.startswith(prefix + "_"))


@dataclass
class _Reference:
    command: str
    keyword: str
    group: str
    line: int
    on_nodes: bool


def _command_of(call: ast.Call) -> str | None:
    return call.func.id if isinstance(call.func, ast.Name) else None


def _scan(tree: ast.Module) -> tuple[list[_Reference], set[str], set[str], bool]:
    """References, created element groups, created node groups, and whether every node group
    of every element group is created (``CREA_GROUP_NO=_F(TOUT_GROUP_MA="OUI")``)."""
    refs: list[_Reference] = []
    made_cells: set[str] = set()
    made_nodes: set[str] = set()
    all_nodes = False
    for top in ast.walk(tree):
        if not isinstance(top, ast.Call) or _command_of(top) in (None, "_F"):
            continue
        command = _command_of(top) or ""
        stack: list[tuple[str | None, ast.expr]] = [(kw.arg, kw.value) for kw in top.keywords]
        while stack:
            parent, value = stack.pop()
            occurrences = value.elts if isinstance(value, ast.Tuple | ast.List) else [value]
            for occ in occurrences:
                if not (isinstance(occ, ast.Call) and _command_of(occ) == "_F"):
                    continue
                kws = {kw.arg: kw.value for kw in occ.keywords}
                if command == "DEFI_GROUP" and parent in ("CREA_GROUP_NO", "CREA_GROUP_MA"):
                    target = made_nodes if parent == "CREA_GROUP_NO" else made_cells
                    if "NOM" in kws:
                        target.update(_strings(kws["NOM"]) or [])
                    elif parent == "CREA_GROUP_NO" and "GROUP_MA" in kws:
                        made_nodes.update(_strings(kws["GROUP_MA"]) or [])
                    if parent == "CREA_GROUP_NO" and "TOUT_GROUP_MA" in kws:
                        all_nodes = True
                stack.extend((kw.arg, kw.value) for kw in occ.keywords)
            if parent is None:
                continue
            on_nodes = _is_group_keyword(parent, "GROUP_NO")
            if not (on_nodes or _is_group_keyword(parent, "GROUP_MA")):
                continue
            for name in _strings(value) or []:
                refs.append(_Reference(command, parent, name, value.lineno, on_nodes))
    return refs, made_cells, made_nodes, all_nodes


def _mesh_groups(mesh: str | Path) -> tuple[set[str], set[str]]:
    with MedFile(mesh) as med:
        m = med.mesh()
        return set(m.cell_groups()), set(m.node_groups())


def precheck(comm: str, mesh: str | Path | None = None) -> list[Problem]:
    """Faults in a command file (its text) that need no solver, in file order.

    With ``mesh`` (the job's ``mesh.med``), every literal group name given to a ``GROUP_MA*``
    or ``GROUP_NO*`` keyword must be in the mesh or created by a ``DEFI_GROUP`` of the file.
    Names held in variables are not followed. Order inside the file is not checked: a group
    used before the ``DEFI_GROUP`` that creates it passes here and fails at run time.
    """
    try:
        tree = ast.parse(comm)
    except SyntaxError as exc:
        return [
            Problem(
                "syntax",
                f"the command file is not valid Python: {exc.msg}",
                line=exc.lineno,
            )
        ]
    if mesh is None:
        return []
    cells, nodes = _mesh_groups(mesh)
    refs, made_cells, made_nodes, all_nodes = _scan(tree)
    cells |= made_cells
    nodes |= made_nodes | (cells if all_nodes else set())
    problems = []
    for ref in sorted(refs, key=lambda r: r.line):
        known = nodes if ref.on_nodes else cells
        if ref.group in known:
            continue
        what = "node group" if ref.on_nodes else "element group"
        problems.append(
            Problem(
                "missing_group",
                f"{ref.command} {ref.keyword}: {what} {ref.group!r} is not in the mesh",
                line=ref.line,
                command=ref.command,
                keyword=ref.keyword,
                group=ref.group,
            )
        )
    return problems


def table_units(names: Iterable[str]) -> dict[int, str]:
    """Units for table files, in order from ``FIRST_TABLE_UNIT``: ``{30: names[0], ...}``."""
    return {FIRST_TABLE_UNIT + i: name for i, name in enumerate(names)}
