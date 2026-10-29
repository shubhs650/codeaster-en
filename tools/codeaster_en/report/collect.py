"""Build the :class:`RunModel` of a job directory (task 4.6, ``docs/REPORT-SPEC.md`` §6).

The run model is everything the report shows, as plain JSON-ready data, with the source of
every number next to it. ``render`` only formats it. Inputs (REPORT-SPEC §1): the command file
(read without running it, :mod:`codeaster_en.report.comm`), the ``.export``, the ``.mess``
(parsed and rendered in English by :mod:`codeaster_en.mess`), the ``.rmed`` and printed tables
(:mod:`codeaster_en.results`) and the optional ``run.json``.

Nothing here computes physics. The only arithmetic is sums (load resultants, reaction sums),
extrema, percentages and unit labels (REPORT-SPEC §1).
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import codeaster_en
from codeaster_en import mess
from codeaster_en import results as results_module
from codeaster_en.mess.render import EnglishLog
from codeaster_en.report import comm as comm_module
from codeaster_en.report.comm import Call, CommandFile, Ref, Unevaluated, as_list
from codeaster_en.report.labels import (
    MATERIAL_QUANTITIES,
    UNIT_SYSTEM_NAMES,
    UNIT_SYSTEMS,
    Terms,
    guess_system,
    quantity,
    unit,
)
from codeaster_en.report.loads import (
    KINEMATIC,
    LOAD_COMMANDS,
    OPTIONS,
    applied_loads,
    balance,
)
from codeaster_en.results.med import MedFile

SCHEMA_VERSION = 1

# docs/schemas/run.schema.json "sections", in REPORT-SPEC order.
ALL_SECTIONS = (
    "title_block",
    "summary",
    "model",
    "materials",
    "element_properties",
    "loads_and_bcs",
    "solution",
    "displacements",
    "stresses",
    "reactions",
    "modal",
    "cut_lines",
    "diagnostics",
    "verification",
    "appendix_command_file",
    "appendix_run_parameters",
    "appendix_log",
)
# REPORT-SPEC §3: everything but cut lines and the full log is on by default.
DEFAULT_SECTIONS = tuple(s for s in ALL_SECTIONS if s not in ("cut_lines", "appendix_log"))
# REPORT-SPEC §5: a failed run keeps sections 1-7 and 13.
FAILURE_SECTIONS = (
    "title_block",
    "summary",
    "model",
    "materials",
    "element_properties",
    "loads_and_bcs",
    "solution",
    "diagnostics",
)

SOLVE_COMMANDS = {
    "MECA_STATIQUE": "linear_static",
    "STAT_NON_LINE": "nonlinear_static",
    "CALC_MODES": "modal",
}
STATIC = {"linear_static", "nonlinear_static"}

# MED cell type -> code_aster element type name (TYPE_MAILLE values; glossary entries).
MED_TO_ASTER = {
    "PO1": "POI1",
    "SE2": "SEG2",
    "SE3": "SEG3",
    "SE4": "SEG4",
    "TR3": "TRIA3",
    "TR6": "TRIA6",
    "TR7": "TRIA7",
    "QU4": "QUAD4",
    "QU8": "QUAD8",
    "QU9": "QUAD9",
    "TE4": "TETRA4",
    "T10": "TETRA10",
    "PY5": "PYRAM5",
    "P13": "PYRAM13",
    "PE6": "PENTA6",
    "P15": "PENTA15",
    "P18": "PENTA18",
    "HE8": "HEXA8",
    "H20": "HEXA20",
    "H27": "HEXA27",
}

# .export "P" parameters and "F" file types (run_aster), labelled in English.
EXPORT_PARAMETERS = {
    "time_limit": ("Time limit", "s"),
    "memory_limit": ("Memory limit", "MB"),
    "ncpus": ("OpenMP threads per process", ""),
    "mpi_nbcpu": ("MPI processes", ""),
    "mpi_nbnoeud": ("MPI nodes", ""),
    "version": ("Solver version", ""),
}
EXPORT_FILE_TYPES = {
    "comm": "command file",
    "mmed": "MED mesh",
    "mail": "mesh (code_aster format)",
    "mess": "message log",
    "resu": "text results",
    "rmed": "MED results",
    "libr": "free-format file (tables)",
    "base": "database",
    "erre": "error output",
}
EXPORT_DIRECTIONS = {"D": "input", "R": "output", "DR": "input and output"}

# Stress-like fields to report, best first, and the components to show.
STRESS_FIELDS = (
    ("SIEQ_NOEU", ("VMIS", "TRESCA", "PRIN_1", "PRIN_3")),
    ("SIEQ_ELNO", ("VMIS", "TRESCA", "PRIN_1", "PRIN_3")),
    ("SIGM_NOEU", ("SIXX", "SIYY", "SIZZ", "SIXY", "SIXZ", "SIYZ")),
    ("SIGM_ELNO", ("SIXX", "SIYY", "SIZZ", "SIXY", "SIXZ", "SIYZ")),
)
SHELL_FORCE_FIELDS = (
    ("EFGE_NOEU", ("NXX", "NYY", "NXY", "MXX", "MYY", "MXY", "QX", "QY")),
    ("EFGE_ELNO", ("NXX", "NYY", "NXY", "MXX", "MYY", "MXY", "QX", "QY")),
)
AVERAGING = {
    "NOEU": "nodal average (values of adjoining elements averaged at each node)",
    "ELNO": "at element nodes (per element, not averaged)",
    "ELGA": "at Gauss points",
}
REFERENCE_TYPES = ("ANALYTIQUE", "SOURCE_EXTERNE", "AUTRE_ASTER", "NON_DEFINI", "NON_REGRESSION")

# Messages whose arguments give solution statistics (en/messages; language independent).
MSG_LINEAR_SYSTEM = "FACTOR_1"  # i1 DOFs, i2 physical, i3 nodes, i4 Lagrange, i5 relations
MSG_MODAL_DOFS = "ALGELINE7_17"  # i1 total, i2 Lagrange, i3 active
MSG_MODAL_OPTION = "ALGELINE6_41"
MSG_MODAL_SHIFT = "ALGELINE6_42"

STATEMENT = (
    "This report was produced by software from the results of one run. It documents what the "
    "solver computed; it is not a verdict on compliance with any design code."
)


@dataclass
class Config:
    """Report options. ``sections`` overrides ``run.json`` and the defaults; ``title_block``
    entries override ``run.json``'s; ``logo`` is a path or URL shown in the title block."""

    sections: list[str] | None = None
    title_block: dict[str, str] | None = None
    logo: str | None = None
    images: bool = False
    glossary: str | None = None


@dataclass
class JobFiles:
    root: Path
    comm: Path | None = None
    export: Path | None = None
    run_json: Path | None = None
    mess: Path | None = None
    rmed: Path | None = None
    mesh: Path | None = None
    tables_dir: Path | None = None
    exit_code: Path | None = None

    def rel(self, path: Path | None) -> str | None:
        if path is None:
            return None
        try:
            return path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return path.name


def find_files(job: str | Path) -> JobFiles:
    """Locate the inputs in a job directory laid out as ``<job>/input`` + ``<job>/output``
    (``docs/CLEARFEA-INTEGRATION.md`` §3), or with everything in ``<job>`` itself."""
    root = Path(job)
    dirs = [d for d in (root, root / "input", root / "output") if d.is_dir()]

    def pick(pattern: str, preferred: str | None = None) -> Path | None:
        found = sorted(p for d in dirs for p in d.glob(pattern) if p.is_file())
        if preferred:
            for p in found:
                if p.name == preferred:
                    return p
        return found[0] if found else None

    tables = next((d / "tables" for d in dirs if (d / "tables").is_dir()), None)
    return JobFiles(
        root=root,
        comm=pick("*.comm", "run.comm"),
        export=pick("*.export", "run.export"),
        run_json=pick("run.json"),
        mess=pick("*.mess", "run.mess"),
        rmed=pick("*.rmed", "run.rmed"),
        mesh=pick("*.med", "mesh.med"),
        tables_dir=tables,
        exit_code=pick("exit_code"),
    )


@dataclass
class RunModel:
    """Everything the report shows. JSON-ready; golden-file tested per fixture."""

    schema_version: int
    generated_from: dict[str, Any]
    sections: list[str]
    sections_omitted: dict[str, str]
    title_block: dict[str, Any]
    units: dict[str, Any]
    outcome: dict[str, Any]
    analysis: dict[str, Any]
    summary: dict[str, Any]
    model: dict[str, Any]
    materials: list[dict[str, Any]]
    element_properties: list[dict[str, Any]]
    loads_and_bcs: dict[str, Any]
    solution: dict[str, Any]
    displacements: dict[str, Any] | None
    stresses: dict[str, Any] | None
    reactions: dict[str, Any] | None
    modal: dict[str, Any] | None
    diagnostics: dict[str, Any]
    verification: dict[str, Any]
    appendix: dict[str, Any]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"


# ---------------------------------------------------------------------------------------------


def _value_text(value: Any) -> Any:
    """A keyword value in JSON form for the run model (refs by name)."""
    return comm_module.to_jsonable(value)


def _targets(occ: dict[str, Any]) -> list[str]:
    if occ.get("TOUT") == "OUI":
        return ["TOUT"]
    out: list[str] = []
    for key in ("GROUP_MA", "GROUP_NO", "MAILLE", "NOEUD"):
        out.extend(str(v) for v in as_list(occ.get(key)) if isinstance(v, str))
    return out


def _keyword_values(occ: dict[str, Any], terms: Terms) -> list[dict[str, Any]]:
    out = []
    for key, value in occ.items():
        if key in ("GROUP_MA", "GROUP_NO", "MAILLE", "NOEUD", "TOUT"):
            continue
        out.append({"keyword": key, "label": terms.get(key), "value": _value_text(value)})
    return out


class _Collector:
    def __init__(self, job: str | Path, config: Config) -> None:
        self.config = config
        self.files = find_files(job)
        self.terms = Terms(config.glossary)
        self.labels = results_module.Labels(config.glossary)
        self.notes: list[str] = []
        f = self.files
        self.run_json: dict[str, Any] = {}
        if f.run_json:
            self.run_json = json.loads(f.run_json.read_text(encoding="utf-8"))
        self.comm_text = f.comm.read_text(encoding="utf-8") if f.comm else ""
        self.comm: CommandFile = comm_module.parse(self.comm_text)
        self.log = mess.parse(f.mess, comm=f.comm) if f.mess else None
        exit_code = None
        if f.exit_code:
            text = f.exit_code.read_text().strip()
            exit_code = int(text) if text.lstrip("-").isdigit() else None
        self.english: EnglishLog | None = (
            mess.translate(self.log, exit_code=exit_code) if self.log else None
        )
        self.classification = (
            self.english.classification if self.english else mess.classify(None, exit_code)
        )
        self.results = results_module.open(f.rmed, self.labels) if f.rmed else None
        self.tables = results_module.read_table_dir(f.tables_dir) if f.tables_dir else []
        self.mesh = None
        self.mesh_source = None
        if self.results is not None:
            self.mesh, self.mesh_source = self.results.mesh, f.rel(f.rmed)
        elif f.mesh is not None:
            with MedFile(f.mesh) as med:
                self.mesh = med.mesh()
            self.mesh_source = f.rel(f.mesh)
        self.messages = self._message_args()
        self.solve = self._solve_call()
        self.analysis_type = SOLVE_COMMANDS.get(self.solve.command) if self.solve else None

    def close(self) -> None:
        if self.results is not None:
            self.results.close()

    # ---------- helpers ----------

    def _message_args(self) -> dict[str, list[dict[str, str]]]:
        out: dict[str, list[dict[str, str]]] = {}
        if self.english is None:
            return out
        for ev in self.english.events:
            for seg in ev.segments:
                if seg.message_id:
                    out.setdefault(seg.message_id, []).append(seg.args)
        return out

    def _arg(self, message_id: str, name: str, index: int = 0) -> str | None:
        found = self.messages.get(message_id, [])
        if len(found) <= index:
            return None
        for key, value in found[index].items():
            if key.startswith(f"%({name})"):
                return value.strip()
        return None

    def _int_arg(self, message_id: str, name: str) -> int | None:
        value = self._arg(message_id, name)
        return int(value) if value and value.lstrip("-").isdigit() else None

    def _solve_call(self) -> Call | None:
        for call in self.comm.calls:
            if call.command in SOLVE_COMMANDS:
                return call
        return None

    def _echo(self, command: str) -> Call | None:
        """The solver's echo of a command (all defaults filled in), parsed like the .comm."""
        if self.log is None:
            return None
        for stage in self.log.of("stage"):
            if stage.command == command and stage.command_text:
                parsed = comm_module.parse(stage.command_text)
                if parsed.calls:
                    return parsed.calls[0]
        return None

    def group_name(self, group: str) -> dict[str, Any]:
        info = self.run_json.get("groups", {}).get(group, {})
        return {"name": group, "display_name": info.get("display_name")}

    def term(self, fr: str, *kinds: str) -> dict[str, Any]:
        return {"fr": fr, "en": self.terms.get(fr, *kinds)}

    # ---------- sections ----------

    def generated_from(self) -> dict[str, Any]:
        f = self.files
        inputs = {
            "comm": f.rel(f.comm),
            "export": f.rel(f.export),
            "run_json": f.rel(f.run_json),
            "mess": f.rel(f.mess),
            "rmed": f.rel(f.rmed),
            "mesh": f.rel(f.mesh),
            "tables": sorted(
                f.rel(p) or "" for p in (f.tables_dir.iterdir() if f.tables_dir else [])
            ),
            "exit_code": f.rel(f.exit_code),
        }
        return {
            "generator": "codeaster_en.report",
            "generator_version": codeaster_en.__version__,
            "job": f.root.resolve().name,
            "inputs": inputs,
        }

    def upstream_version(self) -> str | None:
        if self.english is not None and self.english.upstream:
            return self.english.upstream
        pinned = Path(codeaster_en.__file__).resolve().parents[2] / "UPSTREAM_VERSION"
        if pinned.is_file():
            lines = [ln.strip() for ln in pinned.read_text().splitlines()]
            return next((ln for ln in lines if ln and not ln.startswith("#")), None)
        return None

    def title_block(self) -> dict[str, Any]:
        tb = dict(self.run_json.get("title_block", {}))
        tb.update(self.config.title_block or {})
        summary = self.log.summary() if self.log else {}
        provenance = self.run_json.get("provenance", {})
        return {
            "project": tb.get("project"),
            "title": tb.get("title") or f"code_aster run {self.files.root.resolve().name}",
            "revision": tb.get("revision"),
            "author": tb.get("author"),
            "date": tb.get("date") or provenance.get("date"),
            "description": self.run_json.get("description"),
            "logo": self.config.logo,
            "solver_version": summary.get("version"),
            "overlay_version": codeaster_en.__version__,
            "upstream_version": self.upstream_version(),
            "statement": STATEMENT,
        }

    def units(self) -> dict[str, Any]:
        declared = self.run_json.get("units", {}).get("system")
        if declared in UNIT_SYSTEMS:
            return {
                "system": declared,
                "name": UNIT_SYSTEM_NAMES[declared],
                "declared": True,
                "units": UNIT_SYSTEMS[declared],
                "note": None,
            }
        young = None
        for call in self.comm.find("DEFI_MATERIAU"):
            elas = call.get("ELAS")
            if isinstance(elas, dict) and isinstance(elas.get("E"), int | float):
                young = float(elas["E"])
                break
        guess = guess_system(young)
        note = "No unit system is declared (run.json units); values are in model units."
        if guess:
            note += (
                f" Young's modulus E = {young:g} suggests {UNIT_SYSTEM_NAMES[guess]}; this is "
                "an assumption, so units are not printed."
            )
        return {
            "system": None,
            "name": "model units",
            "declared": False,
            "guess": guess,
            "units": {},
            "note": note,
        }

    def outcome(self) -> dict[str, Any]:
        c = self.classification
        summary = self.log.summary() if self.log else {}
        diag = summary.get("diagnostic_job")
        if self.log is None:
            status = "not_run"
        elif c.failed:
            status = "failed"
        elif _active_alarms(summary) or (diag and diag.startswith("<A>")):
            status = "completed_with_warnings"
        else:
            status = "completed"
        out: dict[str, Any] = {
            "status": status,
            "diagnostic_job": diag,
            "exit_code": summary.get("exit_code"),
            "classification": c.to_dict(),
            "failed_command": None,
            "failed_comm_line": None,
            "fatal_message": None,
            "fatal_message_id": None,
            "fatal_message_english": None,
            "last_lines": [],
        }
        if status == "failed" and self.english is not None:
            problems = self.english.problems()
            if problems:
                p = problems[0]
                out.update(
                    failed_command=p["command"],
                    failed_comm_line=p["comm_line"],
                    fatal_message=p["message"],
                    fatal_message_id=p["message_id"],
                    fatal_message_english=p["english"],
                )
            out["last_lines"] = english_log_lines(self.english)[-50:]
        return out

    def analysis(self) -> dict[str, Any]:
        kind = self.run_json.get("analysis") or self.analysis_type
        cmd = self.solve.command if self.solve else None
        return {
            "type": kind,
            "solve_command": self.term(cmd, "command") if cmd else None,
            "solve_comm_line": self.solve.line if self.solve else None,
            "result": self.solve.concept if self.solve else None,
        }

    def model(self) -> dict[str, Any]:
        modelings = []
        for call in self.comm.find("AFFE_MODELE"):
            for occ in call.occurrences("AFFE"):
                for m in as_list(occ.get("MODELISATION")):
                    modelings.append(
                        {
                            "targets": [self.group_name(g) for g in _targets(occ)],
                            "physics": self.term(str(occ.get("PHENOMENE")), "value"),
                            "modeling": self.term(str(m), "value"),
                            "comm_line": call.line,
                        }
                    )
        out: dict[str, Any] = {"modelings": modelings, "mesh_source": self.mesh_source}
        if self.mesh is None:
            out.update(nodes=None, elements=[], bounding_box=None)
            return out
        elements = []
        for med_type, block in sorted(self.mesh.cells.items()):
            name = MED_TO_ASTER.get(med_type, med_type)
            elements.append(
                {
                    "type": name,
                    "label": self.terms.get(name, "value"),
                    "count": len(block.numbers),
                }
            )
        coords = self.mesh.coordinates
        axes = self.mesh.axes
        out.update(
            nodes=self.mesh.n_nodes,
            elements=elements,
            element_total=sum(e["count"] for e in elements),
            bounding_box={
                a: [float(coords[:, i].min()), float(coords[:, i].max())]
                for i, a in enumerate(axes)
            },
            groups=self.results.groups() if self.results else None,
        )
        return out

    def materials(self) -> list[dict[str, Any]]:
        assigned: dict[str, list[str]] = {}
        for call in self.comm.find("AFFE_MATERIAU"):
            for occ in call.occurrences("AFFE"):
                for mat in as_list(occ.get("MATER")):
                    if isinstance(mat, Ref):
                        assigned.setdefault(mat.name, []).extend(_targets(occ))
        out = []
        for call in self.comm.find("DEFI_MATERIAU"):
            laws = []
            for key, value in call.keywords.items():
                if not isinstance(value, dict):
                    continue
                props = []
                for k, v in value.items():
                    props.append(
                        {
                            "keyword": k,
                            "label": self.terms.get(k, "keyword"),
                            "value": _value_text(v),
                            "quantity": MATERIAL_QUANTITIES.get(k),
                        }
                    )
                laws.append(
                    {"law": key, "label": self.terms.get(key, "value"), "properties": props}
                )
            name = call.concept or "?"
            out.append(
                {
                    "name": name,
                    "laws": laws,
                    "assigned_to": [self.group_name(g) for g in assigned.get(name, [])],
                    "comm_line": call.line,
                }
            )
        return out

    def element_properties(self) -> list[dict[str, Any]]:
        out = []
        for call in self.comm.find("AFFE_CARA_ELEM"):
            for key, value in call.keywords.items():
                occs = value if isinstance(value, list) else [value]
                for occ in occs:
                    if not isinstance(occ, dict):
                        continue
                    out.append(
                        {
                            "keyword": key,
                            "label": self.terms.get(key, "keyword"),
                            "targets": [self.group_name(g) for g in _targets(occ)],
                            "values": _keyword_values(occ, self.terms),
                            "comm_line": call.line,
                        }
                    )
        return out

    def loads_and_bcs(self) -> dict[str, Any]:
        in_case: dict[str, dict[str, Any]] = {}
        if self.solve is not None:
            for occ in self.solve.occurrences("EXCIT"):
                charge = occ.get("CHARGE")
                if isinstance(charge, Ref):
                    mult = occ.get("FONC_MULT")
                    in_case[charge.name] = {
                        "multiplier": _value_text(mult) if mult is not None else None
                    }
        rows = []
        for call in self.comm.calls:
            if call.command not in LOAD_COMMANDS:
                continue
            for key, value in call.keywords.items():
                if key in OPTIONS:
                    continue
                occs = value if isinstance(value, list) else [value]
                for occ in occs:
                    if not isinstance(occ, dict):
                        continue
                    kinematic = key in KINEMATIC
                    rows.append(
                        {
                            "load": call.concept,
                            "command": call.command,
                            "keyword": key,
                            "label": self.terms.get(key, "keyword"),
                            "kind": "boundary condition" if kinematic else "load",
                            "enforcement": (
                                "eliminated"
                                if call.command.startswith("AFFE_CHAR_CINE")
                                else "Lagrange multipliers"
                            )
                            if kinematic
                            else None,
                            "targets": [self.group_name(g) for g in _targets(occ)],
                            "values": _keyword_values(occ, self.terms),
                            "in_load_case": call.concept in in_case,
                            "multiplier": in_case.get(call.concept or "", {}).get("multiplier"),
                            "comm_line": call.line,
                        }
                    )
        return {
            "solve_command": self.solve.command if self.solve else None,
            "load_case": list(in_case),
            "rows": rows,
        }

    def solution(self) -> dict[str, Any]:
        out: dict[str, Any] = {"command": None}
        if self.solve is None:
            return out
        echo = self._echo(self.solve.command)
        source = echo or self.solve
        solver = source.get("SOLVEUR")
        settings = solver if isinstance(solver, dict) else {}
        out.update(
            command=self.term(self.solve.command, "command"),
            settings_source=(
                "command echo in the solver log (defaults filled in)" if echo else "command file"
            ),
            linear_solver=self.term(str(settings["METHODE"]), "value")
            if "METHODE" in settings
            else None,
            renumbering=settings.get("RENUM"),
            lagrange_elimination=settings.get("ELIM_LAGR"),
        )
        if self.analysis_type in STATIC:
            out["dofs"] = {
                "total": self._int_arg(MSG_LINEAR_SYSTEM, "i1"),
                "physical": self._int_arg(MSG_LINEAR_SYSTEM, "i2"),
                "nodes": self._int_arg(MSG_LINEAR_SYSTEM, "i3"),
                "lagrange": self._int_arg(MSG_LINEAR_SYSTEM, "i4"),
                "relations": self._int_arg(MSG_LINEAR_SYSTEM, "i5"),
                "source": f"solver log message {MSG_LINEAR_SYSTEM}",
            }
        if self.analysis_type == "modal":
            modal = source.get("SOLVEUR_MODAL")
            calc = source.get("CALC_FREQ")
            shift = self._arg(MSG_MODAL_SHIFT, "r1")
            out["dofs"] = {
                "total": self._int_arg(MSG_MODAL_DOFS, "i1"),
                "lagrange": self._int_arg(MSG_MODAL_DOFS, "i2"),
                "active": self._int_arg(MSG_MODAL_DOFS, "i3"),
                "source": f"solver log message {MSG_MODAL_DOFS}",
            }
            out["eigen"] = {
                "method": self.term(str(modal["METHODE"]), "value")
                if isinstance(modal, dict) and modal.get("METHODE")
                else None,
                "option": self.term(str(source.get("OPTION")), "value")
                if source.get("OPTION")
                else None,
                "modes_requested": calc.get("NMAX_FREQ") if isinstance(calc, dict) else None,
                "band": _value_text(calc.get("FREQ")) if isinstance(calc, dict) else None,
                "shift_hz": float(shift) if shift else None,
            }
        stage = None
        if self.log is not None:
            stage = next(
                (s for s in self.log.stages() if s.get("command") == self.solve.command), None
            )
        out["cpu_s"] = stage.get("cpu_s") if stage else None
        out["elapsed_s"] = stage.get("elapsed_s") if stage else None
        return out

    def _result_fields(self) -> dict[str, results_module.FieldInfo]:
        if self.results is None:
            return {}
        want = self.solve.concept if self.solve else None
        out = {}
        for f in self.results.fields():
            if want is None or f.result == want:
                out.setdefault(f.field, f)
        return out

    def _report_groups(self) -> list[str]:
        if self.results is None:
            return []
        groups = self.run_json.get("groups", {})
        mesh = self.results.mesh
        return [g for g, info in groups.items() if info.get("report") and mesh.has_group(g)]

    def _extrema(self, field_name: str, component: Any, groups: list[str]) -> list[dict]:
        assert self.results is not None
        rows = []
        for e in self.results.extrema(field_name, component, groups=groups):
            d = e.to_dict()
            d["group"] = self.group_name(e.group) if e.group else None
            d["component_label"] = (
                self.labels.get(e.component) if not e.component.startswith("|") else None
            )
            rows.append(d)
        return rows

    def displacements(self) -> dict[str, Any] | None:
        fields = self._result_fields()
        if "DEPL" not in fields or self.analysis_type not in STATIC:
            return None
        f = fields["DEPL"]
        groups = self._report_groups()
        trans = tuple(c for c in ("DX", "DY", "DZ") if c in f.components)
        return {
            "field": f.field,
            "med_name": f.med_name,
            "label": f.label,
            "quantity": "length",
            "magnitude": self._extrema(f.field, trans, groups),
            "components": [
                {
                    "component": c,
                    "label": self.labels.get(c),
                    "quantity": quantity(f.field, c),
                    "extrema": self._extrema(f.field, c, [])[0],
                }
                for c in f.components
            ],
            "groups": [self.group_name(g) for g in groups],
        }

    def stresses(self) -> dict[str, Any] | None:
        if self.analysis_type not in STATIC:
            return None
        fields = self._result_fields()
        groups = self._report_groups()
        out: dict[str, Any] = {"tables": [], "groups": [self.group_name(g) for g in groups]}
        chosen = next(((n, c) for n, c in STRESS_FIELDS if n in fields), None)
        shell = next(((n, c) for n, c in SHELL_FORCE_FIELDS if n in fields), None)
        for kind, pick in (("stress", chosen), ("shell_forces", shell)):
            if pick is None:
                continue
            name, comps = pick
            f = fields[name]
            rows = []
            for c in comps:
                if c not in f.components:
                    continue
                for e in self._extrema(name, c, groups):
                    e["quantity"] = quantity(name, c)
                    e["component_label"] = self.labels.get(c)
                    rows.append(e)
            out["tables"].append(
                {
                    "kind": kind,
                    "field": name,
                    "med_name": f.med_name,
                    "label": f.label,
                    "averaging": AVERAGING.get(name.rsplit("_", 1)[-1]),
                    "rows": rows,
                }
            )
        if not out["tables"]:
            out["note"] = (
                "No stress field was written to the results file. Add SIEQ_NOEU (CALC_CHAMP "
                "CRITERES) to IMPR_RESU NOM_CHAM to report von Mises and principal stresses."
            )
        if shell and not chosen:
            out["shell_note"] = (
                "Shell results are reported as stress resultants per unit length (force and "
                "moment), in the element local axes; no through-thickness stress field was "
                "written, so no layer position applies."
            )
        return out

    def reactions(self) -> dict[str, Any] | None:
        if self.analysis_type not in STATIC:
            return None
        supports = [
            g
            for g, info in self.run_json.get("groups", {}).items()
            if info.get("role") == "support"
        ]
        if not supports:
            for call in self.comm.calls:
                if call.command in LOAD_COMMANDS:
                    for key in KINEMATIC & set(call.keywords):
                        for occ in call.occurrences(key):
                            supports.extend(t for t in _targets(occ) if t not in supports)
        if self.results is not None:
            supports = [g for g in supports if g != "TOUT" and self.results.mesh.has_group(g)]
            summary = self.results.reactions(groups=supports, tables=self.tables)
        else:
            summary = None
        applied = applied_loads(self.comm, self.solve, self.mesh, self.mesh_source)
        bal = None
        reaction_source = None
        if summary is not None and summary.total:
            reaction, reaction_source = summary.total, f"rmed:{summary.field} (sum of all nodes)"
        elif summary is not None and len(summary.from_tables) == 1:
            t = summary.from_tables[0]
            reaction, reaction_source = t.components, t.source
        else:
            reaction = None
        if reaction is not None:
            bal = balance(reaction, reaction_source or "", applied)
        keywords = {i.keyword for i in applied.items}
        targets = {t for i in applied.items for t in i.targets}
        out = {
            "summary": summary.to_dict() if summary else None,
            "per_group_display": {g: self.group_name(g) for g in supports},
            "keyword_labels": {k: self.terms.get(k, "keyword") for k in sorted(keywords)},
            "target_display": {t: self.group_name(t) for t in sorted(targets)},
            "applied": applied.to_dict(),
            "balance": bal.to_dict() if bal else None,
            "snippet": None,
        }
        if summary is None or (not summary.total and not summary.from_tables):
            out["snippet"] = (
                'REAC = POST_RELEVE_T(ACTION=_F(OPERATION="EXTRACTION", INTITULE="REAC",\n'
                '    RESULTAT=RESU, NOM_CHAM="REAC_NODA", GROUP_NO="<support group>",\n'
                '    RESULTANTE=("DX", "DY", "DZ")))\n'
                'IMPR_TABLE(TABLE=REAC, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=30)'
            )
        return out

    def modal(self) -> dict[str, Any] | None:
        if self.analysis_type != "modal" or self.results is None:
            return None
        table = self.results.modal(self.tables)
        return table.to_dict()

    def diagnostics(self) -> dict[str, Any]:
        if self.english is None:
            return {"items": [], "coverage": None}
        stages = {s["number"]: s for s in self.english.log.stages()}
        items: dict[str, dict[str, Any]] = {}
        for d in self.english.diagnostics:
            if d.repeat or d.severity in ("I", "INFO"):
                continue
            key = d.message_id or d.severity
            stage = stages.get(d.stage) if d.stage else None
            item = items.setdefault(
                key,
                {
                    "message_id": d.message_id,
                    "severity": d.severity_en,
                    "count": 0,
                    "english": d.en is not None,
                    "status": d.status,
                    "text": (d.en if d.en is not None else None),
                    "commands": [],
                    "log_lines": [],
                },
            )
            item["count"] += 1
            item["log_lines"].append(d.start + 1)
            cmd = stage.get("command") if stage else None
            if cmd and cmd not in item["commands"]:
                item["commands"].append(cmd)
        order = {"fatal error": 0, "error": 1, "warning": 2}
        listed = sorted(items.values(), key=lambda i: order.get(i["severity"], 3))
        summary = self.english.log.summary()
        return {
            "items": listed,
            "ignored_warnings": summary.get("ignored_alarms", []),
            "coverage": {
                k: v
                for k, v in self.english.coverage().items()
                if k in ("diagnostics", "diagnostics_english", "diagnostics_not_english")
            },
        }

    def verification(self) -> dict[str, Any]:
        rows = []
        regression = {"count": 0, "ok": 0}
        checks = {c["legend"]: c for c in self.run_json.get("checks", []) if "legend" in c}
        if self.log is not None:
            for t in self.log.of("table"):
                if t.name != "test_resu":
                    continue
                for row in t.rows:
                    ref = row.get("REFERENCE")
                    if ref == "NON_REGRESSION":
                        regression["count"] += 1
                        regression["ok"] += row["verdict"] == "OK"
                        continue
                    ctx = row.get("context", {})
                    legend = row.get("LEGENDE")
                    check = checks.get(legend, {})
                    rows.append(
                        {
                            "legend": legend,
                            "quantity": check.get("quantity"),
                            "context": ctx,
                            "reference_type": self.term(str(ref), "value"),
                            "reference": row.get("VALE_REFE"),
                            "computed": row.get("VALE_CALC"),
                            "error": row.get("ERREUR"),
                            "tolerance": row.get("TOLE"),
                            "passed": row["verdict"] == "OK",
                        }
                    )
        return {"rows": rows, "non_regression": regression}

    def appendix(self) -> dict[str, Any]:
        purposes = {}
        for call in self.comm.calls:
            purposes[call.line] = {
                "command": call.command,
                "purpose": self.terms.get(call.command, "command"),
            }
        export = parse_export(self.files.export) if self.files.export else None
        return {
            "comm_file": self.files.rel(self.files.comm),
            "comm_text": self.comm_text,
            "comm_syntax_error": self.comm.syntax_error,
            "comm_skipped_lines": self.comm.skipped,
            "command_purposes": {str(k): v for k, v in sorted(purposes.items())},
            "export_file": self.files.rel(self.files.export),
            "export": export,
            "log_lines": english_log_lines(self.english) if self.english else [],
        }

    def summary(self, model: dict, outcome: dict, sections: dict[str, Any]) -> dict[str, Any]:
        log_summary = self.log.summary() if self.log else {}
        stages = self.log.stages() if self.log else []
        peaks = [s["memory_peak_mb"] for s in stages if s.get("memory_peak_mb")]
        cpu = [s["cpu_s"] for s in stages if s.get("cpu_s") is not None]
        headline: list[dict[str, Any]] = []
        disp = sections.get("displacements")
        if disp and disp["magnitude"]:
            m = disp["magnitude"][0]["max"]
            headline.append({"key": "max_displacement", "extremum": m, "quantity": "length"})
        stress = sections.get("stresses")
        if stress:
            for table in stress["tables"]:
                row = next(
                    (r for r in table["rows"] if r["component"] == "VMIS" and r["group"] is None),
                    None,
                )
                if row:
                    headline.append(
                        {
                            "key": "max_von_mises",
                            "field": table["field"],
                            "extremum": row["max"],
                            "quantity": "stress",
                        }
                    )
        reac = sections.get("reactions")
        if reac and reac["balance"]:
            headline.append({"key": "balance", "balance": reac["balance"]})
        modal = sections.get("modal")
        if modal and modal["modes"]:
            headline.append({"key": "first_frequency", "value": modal["modes"][0]["frequency_hz"]})
        return {
            "analysis_type": self.analysis_type or self.run_json.get("analysis"),
            "nodes": model.get("nodes"),
            "elements": model.get("element_total"),
            "outcome": outcome["status"],
            "elapsed_s": log_summary.get("total_elapsed_s"),
            "cpu_s": round(sum(cpu), 2) if cpu else None,
            "peak_memory_mb": max(peaks) if peaks else None,
            "warnings": _active_alarms(log_summary),
            "ignored_warnings": log_summary.get("ignored_alarms", []),
            "headline": headline,
        }

    def sections(self, failed: bool) -> tuple[list[str], dict[str, str]]:
        requested = list(self.config.sections or self.run_json.get("sections") or DEFAULT_SECTIONS)
        omitted: dict[str, str] = {}
        out = []
        static = self.analysis_type in STATIC
        for s in requested:
            reason = None
            if s not in ALL_SECTIONS:
                reason = "unknown section"
            elif failed and s not in FAILURE_SECTIONS:
                reason = "the run failed (REPORT-SPEC §5)"
            elif s in ("displacements", "stresses", "reactions") and not static:
                reason = "not a static analysis"
            elif s == "modal" and self.analysis_type != "modal":
                reason = "not a modal analysis"
            elif s == "element_properties" and not self.comm.find("AFFE_CARA_ELEM"):
                reason = "no AFFE_CARA_ELEM in the command file"
            elif s == "cut_lines":
                reason = "cut lines are not implemented yet (no fixture prints such tables)"
            elif s in ("displacements", "stresses", "reactions", "modal") and not self.results:
                reason = "no results file"
            if reason:
                omitted[s] = reason
            else:
                out.append(s)
        return out, omitted


def _active_alarms(summary: dict[str, Any]) -> dict[str, int]:
    """Warnings the run printed, without those the command file chose to ignore."""
    ignored = set(summary.get("ignored_alarms", []))
    return {k: v for k, v in summary.get("alarms", {}).items() if k not in ignored}


def default_sections(job: str | Path) -> list[str]:
    """The sections ``run.json`` asks for, or the REPORT-SPEC defaults."""
    run_json = find_files(job).run_json
    if run_json is not None:
        listed = json.loads(run_json.read_text(encoding="utf-8")).get("sections")
        if listed:
            return list(listed)
    return list(DEFAULT_SECTIONS)


def parse_export(path: Path) -> dict[str, Any]:
    """``run_aster`` ``.export``: ``P`` parameters and ``F`` files, labelled in English."""
    params, files = [], []
    for raw in path.read_text(encoding="utf-8").splitlines():
        parts = raw.split()
        if len(parts) >= 3 and parts[0] == "P":
            label, unit_text = EXPORT_PARAMETERS.get(parts[1], (None, ""))
            params.append(
                {"key": parts[1], "label": label, "value": " ".join(parts[2:]), "unit": unit_text}
            )
        elif len(parts) >= 5 and parts[0] == "F":
            files.append(
                {
                    "type": parts[1],
                    "label": EXPORT_FILE_TYPES.get(parts[1]),
                    "path": parts[2],
                    "direction": EXPORT_DIRECTIONS.get(parts[3], parts[3]),
                    "unit": int(parts[4]) if parts[4].isdigit() else parts[4],
                }
            )
    return {"parameters": params, "files": files}


_UNTRANSLATED_RUN = "[{n} line(s) printed by the solver outside the message catalog]"


def english_log_lines(english: EnglishLog) -> list[str]:
    """The English rendering of the log, with lines the renderer could not translate (printed
    outside the message catalog, so possibly French) replaced by a one-line marker, so the
    report stays English. The full rendering is ``caen mess translate``'s ``run.en.mess``."""
    out: list[str] = []
    for ev in english.events:
        if ev.diagnostic is not None or not ev.segments:
            lines = ev.lines()
            if ev.diagnostic is None and ev.event.kind in ("text", "notice", "table"):
                lines = [_UNTRANSLATED_RUN.format(n=len(lines))] if lines else []
            out.extend(lines)
            continue
        covered = set()
        for seg in ev.segments:
            covered.update(range(seg.first, seg.last + 1))
        i = 0
        raw = ev.event.lines
        segs = {s.first: s for s in ev.segments}
        while i < len(raw):
            seg = segs.get(i)
            if seg is not None:
                if seg.en is not None:
                    out.extend(_segment_lines(seg, raw))
                else:
                    out.append(_UNTRANSLATED_RUN.format(n=seg.last - seg.first + 1))
                i = seg.last + 1
                continue
            j = i
            while j < len(raw) and j not in covered:
                j += 1
            chunk = raw[i:j]
            if ev.event.kind == "stage":
                out.extend(chunk)  # command echo: French keywords are the solver's API
            elif any(line.strip() for line in chunk):
                out.append(_UNTRANSLATED_RUN.format(n=len(chunk)))
            else:
                out.extend(chunk)
            i = j
    # collapse consecutive markers
    merged: list[str] = []
    for line in out:
        m = re.fullmatch(
            r"\[(\d+) line\(s\) printed by the solver outside the message catalog\]", line
        )
        if m and merged:
            prev = re.fullmatch(
                r"\[(\d+) line\(s\) printed by the solver outside the message catalog\]",
                merged[-1],
            )
            if prev:
                merged[-1] = _UNTRANSLATED_RUN.format(n=int(prev[1]) + int(m[1]))
                continue
        merged.append(line)
    return merged


def _segment_lines(seg: Any, raw: list[str]) -> list[str]:
    from codeaster_en.mess.render import _segment_text

    return _segment_text(seg, raw)


def collect(job: str | Path, config: Config | None = None) -> RunModel:
    """Read a job directory and build its :class:`RunModel`."""
    config = config or Config()
    c = _Collector(job, config)
    try:
        outcome = c.outcome()
        failed = outcome["status"] in ("failed", "not_run")
        sections, omitted = c.sections(failed)
        model = c.model()
        built: dict[str, Any] = {}
        if not failed:
            built["displacements"] = c.displacements()
            built["stresses"] = c.stresses()
            built["reactions"] = c.reactions()
            built["modal"] = c.modal()
        if c.comm.syntax_error:
            c.notes.append(
                f"The command file is not valid Python ({c.comm.syntax_error}); the model, "
                "material and load tables could not be read from it."
            )
        if c.comm.skipped:
            c.notes.append(
                "Command file statements not read (not a plain command call or constant): "
                f"lines {', '.join(map(str, c.comm.skipped))}."
            )
        return RunModel(
            schema_version=SCHEMA_VERSION,
            generated_from=c.generated_from(),
            sections=sections,
            sections_omitted=omitted,
            title_block=c.title_block(),
            units=c.units(),
            outcome=outcome,
            analysis=c.analysis(),
            summary=c.summary(model, outcome, built),
            model=model,
            materials=c.materials(),
            element_properties=c.element_properties(),
            loads_and_bcs=c.loads_and_bcs(),
            solution=c.solution(),
            displacements=built.get("displacements"),
            stresses=built.get("stresses"),
            reactions=built.get("reactions"),
            modal=built.get("modal"),
            diagnostics=c.diagnostics(),
            verification=c.verification(),
            appendix=c.appendix(),
            notes=c.notes,
        )
    finally:
        c.close()


__all__ = [
    "ALL_SECTIONS",
    "Config",
    "JobFiles",
    "RunModel",
    "Unevaluated",
    "collect",
    "english_log_lines",
    "find_files",
    "parse_export",
    "unit",
]
