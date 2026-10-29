"""Render a :class:`RunModel` as Markdown, HTML and PDF (task 4.6, ``docs/REPORT-SPEC.md`` §2).

``report.md`` is the source of truth and is golden-file tested: it is deterministic (no
clock, no absolute paths) and English only outside code (``tripwire.py``). French solver names
are kept in code format and, in each table, shown once in parentheses after their English
label (REPORT-SPEC §4). ``report.html`` is the Markdown converted with Python-Markdown and
placed in a Jinja2 page with a print stylesheet; ``report.pdf`` is that page printed by
WeasyPrint, which is an optional dependency (``pip install codeaster_en[report]``).
"""

from __future__ import annotations

import html
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jinja2
import markdown as markdown_lib

from codeaster_en import results as results_module
from codeaster_en.report import images as images_module
from codeaster_en.report.collect import Config, RunModel, collect, find_files
from codeaster_en.report.labels import full, num, unit

TEMPLATES = Path(__file__).resolve().parent / "templates"

SECTION_TITLES = {
    "summary": "Summary",
    "model": "Model",
    "materials": "Materials",
    "element_properties": "Element properties",
    "loads_and_bcs": "Loads and boundary conditions",
    "solution": "Solution",
    "displacements": "Results: displacements",
    "stresses": "Results: stresses",
    "reactions": "Results: reactions",
    "modal": "Results: natural modes",
    "diagnostics": "Diagnostics",
    "verification": "Verification",
    "appendix_command_file": "Appendix A: command file",
    "appendix_run_parameters": "Appendix B: run parameters",
    "appendix_log": "Appendix C: solver log in English",
}
ANALYSIS_LABELS = {
    "linear_static": "linear static",
    "nonlinear_static": "nonlinear static",
    "modal": "modal (natural frequencies)",
}
OUTCOME_LABELS = {
    "completed": "completed",
    "completed_with_warnings": "completed with warnings",
    "failed": "failed",
    "not_run": "not run (no solver log)",
}


def _esc(text: Any) -> str:
    """Text for a Markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ")


def _pct(fraction: float | None) -> str:
    """A mass fraction as a percentage with two decimals (tiny values print as 0.00)."""
    return "–" if fraction is None else f"{fraction * 100:.2f}"


def _axis_header(component: str) -> str:
    """Reaction column header: the axis, with the DOF name the field uses for it."""
    if component.startswith("DR"):
        return f"Moment about {component[-1]} ({code(component)})"
    return f"Force {component[-1]} ({code(component)})"


def _reaction_source(source: str) -> str:
    kind, _, rest = source.partition(":")
    if kind == "rmed":
        name, _, extra = rest.partition(" ")
        return f"results file field {code(name)} {extra}".rstrip()
    if kind == "table":
        file, _, entry = rest.partition(":")
        return f"table {code(entry)} in {code(file)}"
    return code(source)


AXES = ("DX", "DY", "DZ")
# Sums of nodal values carry round-off of about 1e-15 of the largest term; values below this
# fraction of the table's largest magnitude print as 0 so the report does not depend on the
# order the sums were taken in (CPU vector width, numpy version).
ROUNDOFF = 1e-9


def _scale(values: dict[str, float] | None) -> float:
    return max((abs(v) for v in (values or {}).values() if v is not None), default=0.0)


def _force(value: float | None, scale: float) -> str:
    if value is not None and abs(value) <= ROUNDOFF * scale:
        return "0"
    return num(value)


def _percent(value: float | None) -> str:
    if value is None:
        return "–"
    if value < 1e-6:
        return "less than 0.000001 %"
    return f"{num(value)} %"


def code(name: Any) -> str:
    return f"`{name}`"


class _Names:
    """French names in one table: English label with the French name in parentheses the first
    time, the label alone afterwards (REPORT-SPEC §4)."""

    def __init__(self) -> None:
        self.seen: set[str] = set()

    def __call__(self, fr: str, en: str | None) -> str:
        if not en:
            return code(fr)
        if fr in self.seen:
            return _esc(en)
        self.seen.add(fr)
        return f"{_esc(en)} ({code(fr)})"


def _group(g: dict[str, Any] | None) -> str:
    if g is None:
        return "whole model"
    if g["name"] == "TOUT":
        return f"whole mesh ({code('TOUT')})"
    if g.get("display_name"):
        return f"{_esc(g['display_name'])} ({code(g['name'])})"
    return code(g["name"])


def _groups(gs: list[dict[str, Any]]) -> str:
    return ", ".join(_group(g) for g in gs) if gs else "–"


def _value(v: Any) -> str:
    if isinstance(v, bool):
        return code(v)
    if isinstance(v, int | float):
        return num(v)
    if isinstance(v, str):
        return code(repr(v).replace("'", '"'))
    if isinstance(v, dict) and "ref" in v:
        return code(v["ref"])
    if isinstance(v, dict) and "expr" in v:
        return code(v["expr"])
    if isinstance(v, list):
        return "(" + ", ".join(_value(x) for x in v) + ")"
    if isinstance(v, dict):
        return code(json.dumps(v))
    return code(v)


def _keyword_values(values: list[dict[str, Any]], names: _Names | None = None) -> str:
    parts = []
    for kv in values:
        if isinstance(kv["value"], dict) and "ref" not in kv["value"] and "expr" not in kv["value"]:
            inner = ", ".join(f"{code(k)} = {_value(v)}" for k, v in kv["value"].items())
            parts.append(f"{code(kv['keyword'])}: {inner}")
        else:
            parts.append(f"{code(kv['keyword'])} = {_value(kv['value'])}")
    return "; ".join(parts) if parts else "–"


def _table(header: list[str], rows: list[list[str]], align: list[str] | None = None) -> list[str]:
    align = align or ["l"] * len(header)
    marks = {"l": "---", "r": "---:", "c": ":---:"}
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(marks[a] for a in align) + " |"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out


class _Writer:
    def __init__(self, model: RunModel) -> None:
        self.m = model
        self.system = model.units.get("system")
        self.lines: list[str] = []

    def u(self, qty: str | None) -> str:
        return unit(self.system, qty)

    def bracket(self, qty: str | None) -> str:
        text = self.u(qty)
        return f" [{text}]" if text else ""

    def with_unit(self, value: float | None, qty: str | None) -> str:
        text = self.u(qty)
        return f"{num(value)} {text}".rstrip()

    def add(self, *lines: str) -> None:
        self.lines.extend(lines)

    def para(self, text: str) -> None:
        self.lines.extend([text, ""])

    def table(self, header: list[str], rows: list[list[str]], align: list[str] | None = None):
        self.lines.extend([*_table(header, rows, align), ""])

    def source(self, text: str) -> None:
        self.para(f"*Source: {text}.*")

    def where(self, e: dict[str, Any] | None) -> str:
        if not e:
            return "–"
        xyz = ", ".join(num(c) for c in e["xyz"])
        if e["entity"] == "node":
            return f"node {e['entity_id']} ({xyz})"
        text = f"element {e['entity_id']}"
        if e.get("node_id"):
            text += f", node {e['node_id']}"
        return f"{text} ({xyz})"

    # ---------- sections ----------

    def title_block(self) -> None:
        tb = self.m.title_block
        self.add(f"# {_esc(tb['title'])}", "")
        if tb.get("logo"):
            self.para(f"![Logo]({tb['logo']})")
        rows = []
        for key, label in (
            ("project", "Project"),
            ("revision", "Revision"),
            ("author", "Author"),
            ("date", "Date"),
        ):
            if tb.get(key):
                rows.append([label, _esc(tb[key])])
        solver = f"code_aster {tb['solver_version']}" if tb.get("solver_version") else "–"
        rows.append(["Solver", solver])
        if tb.get("upstream_version"):
            rows.append(["English overlay pinned to", f"code_aster {tb['upstream_version']}"])
        rows.append(["Report generator", f"codeaster-en {tb['overlay_version']}"])
        rows.append(["Units", _esc(self.m.units["name"])])
        self.table(["Item", "Value"], rows)
        if tb.get("description"):
            self.para(_esc(tb["description"]))
        self.para(f"*{tb['statement']}*")

    def summary(self) -> None:
        s, o = self.m.summary, self.m.outcome
        self.add("## Summary", "")
        if o["status"] in ("failed", "not_run"):
            self.failure()
        rows = [
            ["Analysis", ANALYSIS_LABELS.get(s["analysis_type"] or "", s["analysis_type"] or "–")],
            ["Outcome", OUTCOME_LABELS[o["status"]]],
        ]
        if s.get("nodes") is not None:
            rows.append(["Model size", f"{s['nodes']} nodes, {s['elements']} elements"])
        if s.get("elapsed_s") is not None:
            rows.append(["Elapsed time (whole job)", f"{num(s['elapsed_s'])} s"])
        if s.get("cpu_s") is not None:
            rows.append(["CPU time (sum of commands)", f"{num(s['cpu_s'])} s"])
        if s.get("peak_memory_mb") is not None:
            rows.append(["Peak memory", f"{num(s['peak_memory_mb'])} MB"])
        if s.get("warnings"):
            rows.append(
                [
                    "Warnings",
                    ", ".join(f"{code(k)} × {v}" for k, v in sorted(s["warnings"].items())),
                ]
            )
        if s.get("ignored_warnings"):
            rows.append(
                [
                    "Warnings ignored by the command file",
                    ", ".join(code(x) for x in s["ignored_warnings"]),
                ]
            )
        self.table(["Item", "Value"], rows)
        if s["headline"]:
            self.add("Headline results:", "")
            for h in s["headline"]:
                self.add(f"- {self.headline(h)}")
            self.add("")
        if not self.m.units["declared"]:
            self.para(f"**Units.** {_esc(self.m.units['note'])}")
        self.source(
            "solver log (outcome, times, memory), results file (model size, extrema), command "
            "file and results file (balance)"
        )

    def headline(self, h: dict[str, Any]) -> str:
        if h["key"] == "max_displacement":
            e = h["extremum"]
            return (
                f"Maximum displacement magnitude: {self.with_unit(e['value'], 'length')} at "
                f"{self.where(e)}."
            )
        if h["key"] == "max_von_mises":
            e = h["extremum"]
            return (
                f"Maximum von Mises stress ({code(h['field'])}): "
                f"{self.with_unit(e['value'], 'stress')} at {self.where(e)}."
            )
        if h["key"] == "balance":
            b = h["balance"]
            if not b["complete"]:
                return (
                    "Equilibrium check: not made, because some applied loads are not summed by "
                    "this report (see Results: reactions)."
                )
            return (
                "Equilibrium check: support reactions balance the applied loads to "
                f"{_percent(b['error_percent'])} of the applied resultant."
            )
        if h["key"] == "first_frequency":
            return f"First natural frequency: {num(h['value'])} Hz."
        return _esc(h)

    def failure(self) -> None:
        o = self.m.outcome
        c = o["classification"]
        if o["status"] == "not_run":
            self.para("**The solver did not run: no solver log was found.**")
        else:
            where = f" at command {code(o['failed_command'])}" if o["failed_command"] else ""
            if o["failed_comm_line"]:
                where += f" (command file line {o['failed_comm_line']})"
            self.para(f"**Run failed{where}.**")
            if o["fatal_message"]:
                tag = f" [{code(o['fatal_message_id'])}]" if o["fatal_message_id"] else ""
                if o["fatal_message_english"]:
                    self.para(f"Fatal message{tag}:")
                    for chunk in re.split(r"\n\s*\n", o["fatal_message"].strip()):
                        self.para("> " + " ".join(chunk.split()).replace("|", "\\|"))
                else:
                    self.para(f"Fatal message{tag}: no English translation yet.")
        self.para(
            f"Cause classification: **{c['failure_class']}**, {_esc(c['reason'])}."
            + (f" Solver diagnostic: {code(o['diagnostic_job'])}." if o["diagnostic_job"] else "")
        )
        if o["last_lines"]:
            self.add("Last lines of the solver log (English rendering):", "", "```text")
            self.add(*o["last_lines"], "```", "")

    def model(self) -> None:
        md = self.m.model
        self.add("## Model", "")
        if md["modelings"]:
            names = _Names()
            rows = [
                [
                    _groups(r["targets"]),
                    names(r["physics"]["fr"], r["physics"]["en"]),
                    names(r["modeling"]["fr"], r["modeling"]["en"]),
                    str(r["comm_line"]),
                ]
                for r in md["modelings"]
            ]
            self.table(["Applied to", "Physics", "Modeling type", "Command file line"], rows)
        else:
            self.para("No model assignment (`AFFE_MODELE`) could be read from the command file.")
        if md.get("nodes") is not None:
            names = _Names()
            rows = [[names(e["type"], e["label"]), str(e["count"])] for e in md["elements"]] + [
                ["**Total**", f"**{md['element_total']}**"]
            ]
            self.para(f"The mesh has {md['nodes']} nodes and {md['element_total']} elements.")
            self.table(["Element type", "Count"], rows, ["l", "r"])
            box = md["bounding_box"]
            rows = [[a, num(lo), num(hi), num(hi - lo)] for a, (lo, hi) in box.items()]
            b = self.bracket("length")
            self.table(["Axis", f"Min{b}", f"Max{b}", f"Extent{b}"], rows, ["l", "r", "r", "r"])
            self.source(
                f"mesh in {code(md['mesh_source'])}; model assignment from the command file"
            )

    def materials(self) -> None:
        self.add("## Materials", "")
        if not self.m.materials:
            self.para("No material (`DEFI_MATERIAU`) could be read from the command file.")
            return
        for mat in self.m.materials:
            self.add(f"### Material {code(mat['name'])}", "")
            self.para(f"Assigned to: {_groups(mat['assigned_to'])}.")
            for law in mat["laws"]:
                label = law["label"] or "material law"
                self.para(f"Law: {_esc(label)} ({code(law['law'])}).")
                names = _Names()
                rows = []
                for p in law["properties"]:
                    rows.append(
                        [
                            names(p["keyword"], p["label"]),
                            _value(p["value"]),
                            self.u(p["quantity"]) or "–",
                        ]
                    )
                self.table(["Property", "Value", "Unit"], rows, ["l", "r", "l"])
            self.source(f"command file line {mat['comm_line']}")

    def element_properties(self) -> None:
        self.add("## Element properties", "")
        names = _Names()
        rows = [
            [names(p["keyword"], p["label"]), _groups(p["targets"]), _keyword_values(p["values"])]
            for p in self.m.element_properties
        ]
        self.table(["Property", "Applied to", "Values"], rows)
        lines = sorted({str(p["comm_line"]) for p in self.m.element_properties})
        self.source(f"command file line {', '.join(lines)}; values in model units")

    def loads_and_bcs(self) -> None:
        lb = self.m.loads_and_bcs
        self.add("## Loads and boundary conditions", "")
        if not lb["rows"]:
            self.para("No load or boundary condition could be read from the command file.")
            return
        names = _Names()
        rows = []
        for r in lb["rows"]:
            kind = r["kind"] + (" ¹" if r["enforcement"] else "")
            case = "yes" if r["in_load_case"] else "no"
            if r["multiplier"] is not None:
                case += f", multiplied by {_value(r['multiplier'])}"
            rows.append(
                [
                    code(r["load"]),
                    names(r["keyword"], r["label"]),
                    kind,
                    _groups(r["targets"]),
                    _keyword_values(r["values"]),
                    case,
                ]
            )
        header = ["Load", "Type", "Kind", "Applied to", "Values", "In load case"]
        self.table(header, rows)
        if lb["solve_command"]:
            self.para(
                f"The load case is the {code('EXCIT')} list of {code(lb['solve_command'])}: "
                + (", ".join(code(x) for x in lb["load_case"]) or "none")
                + "."
            )
        enforcement = {r["enforcement"] for r in lb["rows"] if r["enforcement"]}
        if enforcement:
            text = " and ".join(sorted(enforcement))
            self.para(
                f"¹ Boundary conditions are enforced by {text} "
                f"({code('AFFE_CHAR_MECA')}: Lagrange multipliers; "
                f"{code('AFFE_CHAR_CINE')}: eliminated)."
            )
        for f in lb.get("functions", []):
            params = ", ".join(code(p) for p in f["parameters"]) or "no parameter"
            expr = code(f["expression"]) if f["expression"] else "an expression not read"
            self.para(f"{code(f['name'])} is a formula ({code(f['command'])}) of {params}: {expr}.")
        lines = sorted(
            {r["comm_line"] for r in lb["rows"]} | {f["comm_line"] for f in lb.get("functions", [])}
        )
        self.source(f"command file line {', '.join(map(str, lines))}; values in model units")

    def solution(self) -> None:
        sol = self.m.solution
        self.add("## Solution", "")
        if not sol.get("command"):
            self.para("No solve command was found in the command file.")
            return
        names = _Names()
        cmd = sol["command"]
        rows = [["Solve command", names(cmd["fr"], cmd["en"])]]
        if sol.get("linear_solver"):
            ls = sol["linear_solver"]
            rows.append(["Linear solver", names(ls["fr"], ls["en"])])
        if sol.get("renumbering"):
            rows.append(["Renumbering", code(sol["renumbering"])])
        dofs = sol.get("dofs") or {}
        if dofs.get("total") is not None:
            rows.append(["Equations (degrees of freedom)", str(dofs["total"])])
        if dofs.get("physical") is not None:
            rows.append(
                ["Physical degrees of freedom", f"{dofs['physical']} on {dofs['nodes']} nodes"]
            )
        if dofs.get("active") is not None:
            rows.append(["Active degrees of freedom", str(dofs["active"])])
        if dofs.get("lagrange") is not None:
            text = str(dofs["lagrange"])
            if dofs.get("relations") is not None:
                text += f" for {dofs['relations']} dualized linear relations"
            rows.append(["Lagrange multipliers", text])
        eigen = sol.get("eigen")
        if eigen:
            if eigen.get("method"):
                rows.append(["Eigensolver", names(eigen["method"]["fr"], eigen["method"]["en"])])
            if eigen.get("option"):
                rows.append(["Modes sought", names(eigen["option"]["fr"], eigen["option"]["en"])])
            if eigen.get("modes_requested") is not None:
                rows.append(["Number of modes requested", str(eigen["modes_requested"])])
            if eigen.get("band"):
                rows.append(["Frequency band [Hz]", _value(eigen["band"])])
            if eigen.get("shift_hz") is not None:
                rows.append(["Frequency shift [Hz]", num(eigen["shift_hz"])])
        if sol.get("cpu_s") is not None:
            rows.append(
                ["Solve time", f"{num(sol['cpu_s'])} s CPU, {num(sol['elapsed_s'])} s elapsed"]
            )
        self.table(["Item", "Value"], rows)
        src = f"solver settings from the {sol['settings_source']}"
        if dofs.get("source"):
            src += f"; degrees of freedom from the {dofs['source']}"
        self.source(src)

    def _extrema_table(self, rows: list[dict], qty_of: Callable[[dict], str | None]) -> None:
        names = _Names()
        out = []
        for r in rows:
            unit_text = self.u(qty_of(r)) or "–"
            comp = r["component"]
            label = r.get("component_label") or r.get("label")
            if comp.startswith("|"):
                comp_text = "magnitude"
            else:
                comp_text = names(comp, label if label and label != comp else None)
            out.append(
                [
                    _group(r["group"]),
                    comp_text,
                    num(r["min"]["value"]) if r["min"] else "–",
                    self.where(r["min"]),
                    num(r["max"]["value"]) if r["max"] else "–",
                    self.where(r["max"]),
                    unit_text,
                ]
            )
        self.table(
            ["Group", "Component", "Min", "At", "Max", "At", "Unit"],
            out,
            ["l", "l", "r", "l", "r", "l", "l"],
        )

    def displacements(self) -> None:
        d = self.m.displacements
        assert d is not None
        self.add("## Results: displacements", "")
        mag = d["magnitude"]
        if mag:
            top = mag[0]["max"]
            self.para(
                f"Maximum displacement magnitude: **{self.with_unit(top['value'], 'length')}** "
                f"at {self.where(top)}."
            )
        self.add(f"Displacement magnitude ({code(d['field'])}, translations), per group:", "")
        self._extrema_table(mag, lambda r: "length")
        self.add("Displacement components, whole model:", "")
        self._extrema_table(
            [c["extrema"] for c in d["components"]],
            lambda r: "angle" if r["component"].startswith("DR") else "length",
        )
        self.source(f"results file field {code(d['med_name'])}, last stored step")
        self.figures("displacements")

    def stresses(self) -> None:
        s = self.m.stresses
        assert s is not None
        self.add("## Results: stresses", "")
        if s.get("note"):
            self.para(s["note"])
        if s.get("shell_note"):
            self.para(s["shell_note"])
        for t in s["tables"]:
            kind = "Stresses" if t["kind"] == "stress" else "Shell stress resultants"
            label = f"{t['label']} " if t["label"] else ""
            self.para(
                f"{kind}: {_esc(label)}({code(t['field'])}), "
                f"{t['averaging'] or 'location as written'}."
            )
            self._extrema_table(t["rows"], lambda r: r.get("quantity"))
            self.source(f"results file field {code(t['med_name'])}, last stored step")
        self.figures("stresses")

    def reactions(self) -> None:
        r = self.m.reactions
        assert r is not None
        self.add("## Results: reactions", "")
        summary = r["summary"]
        if summary and summary["per_group"]:
            comps = list(summary["total"])
            scale = max(
                [_scale(summary["total"])] + [_scale(g["components"]) for g in summary["per_group"]]
            )
            rows = []
            for g in summary["per_group"]:
                display = r["per_group_display"].get(g["group"], {"name": g["group"]})
                rows.append(
                    [_group(display), str(g["nodes"])]
                    + [_force(g["components"].get(c), scale) for c in comps]
                )
            totals = [f"**{_force(summary['total'][c], scale)}**" for c in comps]
            rows.append(["**All supports**", "–", *totals])
            header = ["Group", "Nodes"] + [
                _axis_header(c) + self.bracket("moment" if c.startswith("DR") else "force")
                for c in comps
            ]
            self.para(
                "Sum of nodal reactions per support group (the force each support exerts on the "
                "structure):"
            )
            self.table(header, rows, ["l", "r"] + ["r"] * len(comps))
            if r.get("relations"):
                self.para(
                    "Nodes tied by linear relations ("
                    + ", ".join(code(k) for k in r["relations"])
                    + ") also carry reactions, the relation forces. They cancel in the force "
                    "sums, so the totals are still the support reactions; the rotation columns "
                    "of the totals hold the reaction of a remote point to its applied moment, "
                    "not a support moment."
                )
            self.source(f"results file field {code(summary['field'])}, sum over the group's nodes")
        if summary and summary["from_tables"]:
            rows = []
            for t in summary["from_tables"]:
                rows.append(
                    [code(t["source"].split(":")[-1]), code(t["source"].split(":")[1])]
                    + [
                        _force(t["components"].get(c), _scale(t["components"]))
                        for c in ("DX", "DY", "DZ")
                    ]
                )
            b = self.bracket("force")
            self.para(f"Reaction resultants printed by {code('POST_RELEVE_T')}:")
            self.table(
                ["Table entry", "File", f"X{b}", f"Y{b}", f"Z{b}"], rows, ["l", "l", "r", "r", "r"]
            )
        if r.get("snippet"):
            self.para(
                "No reaction field or table was written. To get reaction sums, add "
                f"{code('REAC_NODA')} to {code('IMPR_RESU')} or print a table like this:"
            )
            self.add("```python", r["snippet"], "```", "")
        self.applied(r["applied"], r["keyword_labels"], r["target_display"])
        bal = r["balance"]
        if bal:
            scale = max(_scale(bal["reaction"]), _scale(bal["applied"]))
            b = self.bracket("force")
            rows = [
                ["Support reactions (sum)"] + [_force(bal["reaction"][a], scale) for a in AXES],
                ["Applied loads (resultant)"] + [_force(bal["applied"][a], scale) for a in AXES],
                ["Residual (reactions + applied)"]
                + [_force(bal["residual"][a], scale) for a in AXES],
            ]
            self.add("### Equilibrium check", "")
            self.table(["", f"X{b}", f"Y{b}", f"Z{b}"], rows, ["l", "r", "r", "r"])
            if bal["error_percent"] is not None and bal["complete"]:
                self.para(
                    f"Balance error: **{_percent(bal['error_percent'])}** "
                    "(magnitude of the residual over the magnitude of the applied resultant)."
                )
            for note in bal["notes"]:
                self.para(f"Note: {note}.")
            self.source(
                f"reactions from {_reaction_source(bal['reaction_source'])}; applied loads summed "
                "from the command file over the result mesh"
            )

    def applied(
        self, a: dict[str, Any], a_labels: dict[str, str | None], a_targets: dict[str, dict]
    ) -> None:
        items = [i for i in a["items"] if i["status"] != "kinematic"]
        if not items:
            return
        self.add("### Applied loads", "")
        names = _Names()
        rows = []
        b = self.bracket("force")
        for i in items:
            res = i["resultant"] or {}
            rows.append(
                [
                    code(i["load"]),
                    names(i["keyword"], a_labels.get(i["keyword"])),
                    _groups([a_targets.get(t, {"name": t}) for t in i["targets"]]),
                    "summed" if i["status"] == "evaluated" else "not evaluated",
                    _esc(i["basis"] or "–"),
                ]
                + [_force(res.get(ax), _scale(res)) if res else "–" for ax in AXES]
            )
        self.table(
            ["Load", "Type", "Applied to", "Status", "Basis", f"X{b}", f"Y{b}", f"Z{b}"],
            rows,
            ["l", "l", "l", "l", "l", "r", "r", "r"],
        )
        for note in a["notes"]:
            self.para(f"Note: {note}.")
        if a.get("mesh_source"):
            self.source(
                "load values from the command file; areas, lengths and node counts from the "
                f"mesh in {code(a['mesh_source'])}"
            )

    def modal(self) -> None:
        t = self.m.modal
        assert t is not None
        self.add("## Results: natural modes", "")
        axes = [
            a
            for a in ("DX", "DY", "DZ")
            if any(a in m["effective_mass_fraction"] for m in t["modes"])
        ]
        header = ["Mode", "Frequency [Hz]", f"Period{self.bracket('time')}"]
        for a in axes:
            header += [f"Effective mass {a[-1]} [%]", f"Cumulative {a[-1]} [%]"]
        rows = []
        for m in t["modes"]:
            row = [str(m["nume_ordre"]), num(m["frequency_hz"]), num(m["period_s"])]
            for a in axes:
                frac = m["effective_mass_fraction"].get(a)
                cum = m["cumulative_fraction"].get(a)
                row += [_pct(frac), _pct(cum)]
            rows.append(row)
        self.table(header, rows, ["r"] * len(header))
        if t.get("total_mass") is not None:
            self.para(f"Total mass of the model: {self.with_unit(t['total_mass'], 'mass')}.")
        for note in t["notes"]:
            self.para(f"Note: {note}.")
        self.source(", ".join(code(s) for s in t["sources"]))
        self.figures("modal")

    def figures(self, section: str) -> None:
        """Images of task 4.7 for a section, or one placeholder line per image not rendered."""
        for f in self.m.images or []:
            if f["section"] != section:
                continue
            caption = f["caption"]
            if f["kind"] == "deformed_shape" and f["scale"]:
                caption = f"{caption}; displacements scaled by {f['scale']:g}"
            elif f["kind"] == "mode_shape" and f["scale"]:
                caption = f"{caption}; drawn scaled by {f['scale']:g}"
            if f["file"]:
                alt = f"Figure {f['number']}, {f['kind'].replace('_', ' ')}"
                self.add(f"![{alt}]({f['file']})", "")
                self.para(f"*Figure {f['number']}: {caption}.*")
            else:
                self.para(f"*Figure {f['number']} not generated ({caption}): {_esc(f['reason'])}.*")

    def diagnostics(self) -> None:
        d = self.m.diagnostics
        self.add("## Diagnostics", "")
        if not d["items"]:
            self.para("The solver issued no warning or error.")
        else:
            rows = []
            for i in d["items"]:
                text = (
                    _esc(" ".join(i["text"].split()))
                    if i["english"]
                    else "**no English translation yet**"
                )
                rows.append(
                    [
                        i["severity"],
                        code(i["message_id"] or "–"),
                        str(i["count"]),
                        ", ".join(code(c) for c in i["commands"]) or "–",
                        text,
                    ]
                )
            self.table(["Severity", "Message", "Count", "Command", "Text (first occurrence)"], rows)
        if d.get("ignored_warnings"):
            self.para(
                "Warnings the command file chose to ignore: "
                + ", ".join(code(x) for x in d["ignored_warnings"])
                + "."
            )
        self.source("solver log, rendered in English from the overlay's message catalog")

    def verification(self) -> None:
        v = self.m.verification
        self.add("## Verification", "")
        if not v["rows"] and not v["non_regression"]["count"]:
            self.para(f"No verification checks ({code('TEST_RESU')}) were requested.")
            return
        if v["rows"]:
            names = _Names()
            rows = []
            for r in v["rows"]:
                ctx = r["context"]
                what = r["quantity"] or " ".join(
                    f"{k} {v}" for k, v in ctx.items() if k != "RESULTAT"
                )
                rows.append(
                    [
                        code(r["legend"]),
                        _esc(what),
                        names(r["reference_type"]["fr"], r["reference_type"]["en"]),
                        full(r["reference"])
                        if isinstance(r["reference"], float)
                        else _esc(r["reference"]),
                        full(r["computed"])
                        if isinstance(r["computed"], float)
                        else _esc(r["computed"]),
                        _esc(r["error"]),
                        _esc(r["tolerance"]),
                        "pass" if r["passed"] else "**FAIL**",
                    ]
                )
            self.table(
                [
                    "Check",
                    "Quantity",
                    "Reference type",
                    "Reference",
                    "Computed",
                    "Error",
                    "Tolerance",
                    "Verdict",
                ],
                rows,
                ["l", "l", "l", "r", "r", "r", "r", "l"],
            )
        nr = v["non_regression"]
        if nr["count"]:
            self.para(
                f"{nr['ok']} of {nr['count']} non-regression checks (computed value against the "
                "value stored in the command file) passed."
            )
        self.source(
            f"{code('TEST_RESU')} output in the solver log; pass or fail by the solver's own "
            "tolerance"
        )

    def appendix_command_file(self) -> None:
        a = self.m.appendix
        self.add("## Appendix A: command file", "")
        if not a["comm_text"]:
            self.para("No command file was found.")
            return
        self.para(
            f"{code(a['comm_file'])} as run, verbatim. Command and keyword names are the "
            "solver's own (French) API. Lines starting with `# >>` are added by this report: "
            "an English one-line description of the command below."
        )
        lines = a["comm_text"].rstrip("\n").split("\n")
        purposes = a["command_purposes"]
        out = []
        for n, line in enumerate(lines, start=1):
            p = purposes.get(str(n))
            if p and p["purpose"]:
                out.append(f"# >> {p['command']}: {p['purpose']}")
            out.append(line)
        self.add("```python", *out, "```", "")

    def appendix_run_parameters(self) -> None:
        a = self.m.appendix
        self.add("## Appendix B: run parameters", "")
        e = a["export"]
        if not e:
            self.para("No run parameter file (`.export`) was found.")
            return
        rows = [
            [
                _esc(p["label"]) if p["label"] else code(p["key"]),
                code(p["key"]),
                _esc(p["value"]),
                p["unit"] or "–",
            ]
            for p in e["parameters"]
        ]
        self.table(["Parameter", "Name", "Value", "Unit"], rows, ["l", "l", "r", "l"])
        rows = [
            [
                _esc(f["label"]) if f["label"] else code(f["type"]),
                code(f["path"]),
                f["direction"],
                str(f["unit"]),
            ]
            for f in e["files"]
        ]
        self.table(["File", "Path", "Direction", "Logical unit"], rows, ["l", "l", "l", "r"])
        self.source(code(a["export_file"]))

    def appendix_log(self) -> None:
        a = self.m.appendix
        self.add("## Appendix C: solver log in English", "")
        self.para(
            "Lines the solver printed outside its message catalog are summarized in brackets; "
            "the complete rendering is written by `caen mess translate`."
        )
        self.add("```text", *a["log_lines"], "```", "")

    def notes(self) -> None:
        if not self.m.notes and not self.m.sections_omitted:
            return
        self.add("## Report notes", "")
        for n in self.m.notes:
            self.add(f"- {_esc(n)}")
        for s, reason in self.m.sections_omitted.items():
            title = SECTION_TITLES.get(s, s.replace("_", " "))
            self.add(f"- Section \u201c{title}\u201d omitted: {reason}.")
        self.add("- Full-precision values and the source of every number are in `run_model.json`.")
        self.add("")

    def render(self) -> str:
        sections = self.m.sections
        if "title_block" in sections:
            self.title_block()
        else:
            self.add(f"# {_esc(self.m.title_block['title'])}", "")
        for s in sections:
            if s != "title_block":
                getattr(self, s)()
        self.notes()
        while self.lines and not self.lines[-1]:
            self.lines.pop()
        return "\n".join(self.lines) + "\n"


def render_markdown(model: RunModel) -> str:
    """The Markdown report (source of truth)."""
    return _Writer(model).render()


def _env() -> jinja2.Environment:
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATES),
        autoescape=jinja2.select_autoescape(["html"]),
        keep_trailing_newline=True,
    )


def render_html(model: RunModel, markdown_text: str | None = None) -> str:
    """A print-ready HTML page from the Markdown report."""
    md = markdown_text if markdown_text is not None else render_markdown(model)
    body = markdown_lib.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    css = (TEMPLATES / "report.css").read_text(encoding="utf-8")
    tb = model.title_block
    footer = " · ".join(
        x
        for x in (
            tb.get("project"),
            tb.get("title"),
            tb.get("revision") and f"rev. {tb['revision']}",
        )
        if x
    )
    return (
        _env()
        .get_template("report.html.j2")
        .render(
            title=tb["title"], body=jinja2.utils.markupsafe.Markup(body), css=css, footer=footer
        )
    )


def write_pdf(html_text: str, path: str | Path, base_url: str | Path | None = None) -> Path:
    """Print the HTML report to PDF with WeasyPrint (raises ``ImportError`` without it)."""
    import weasyprint  # optional dependency: pip install codeaster_en[report]

    path = Path(path)
    weasyprint.HTML(string=html_text, base_url=str(base_url) if base_url else None).write_pdf(path)
    return path


def _figures(job: Path, model: RunModel, out_dir: Path) -> list[dict[str, Any]]:
    """Plan and render the report images (task 4.7) from the job's results file."""
    figures = images_module.plan(model)
    rmed = find_files(job).rmed
    if not figures:
        return []
    if rmed is None:
        return [f.to_dict() for f in images_module.render(figures, None, out_dir, model)]
    with results_module.open(rmed) as res:
        return [f.to_dict() for f in images_module.render(figures, res, out_dir, model)]


@dataclass
class BuildResult:
    model: RunModel
    markdown: Path
    html: Path
    run_model: Path
    pdf: Path | None = None
    warnings: list[str] = field(default_factory=list)


def build(
    job: str | Path, config: Config | None = None, out: str | Path | None = None, pdf: bool = True
) -> BuildResult:
    """Write ``report.md``, ``report.html``, ``run_model.json`` and (with WeasyPrint)
    ``report.pdf`` to ``out`` (default ``<job>/report``)."""
    job = Path(job)
    out_dir = Path(out) if out is not None else job / "report"
    out_dir.mkdir(parents=True, exist_ok=True)
    model = collect(job, config)
    if config is not None and config.images:
        model.images = _figures(job, model, out_dir)
    md = render_markdown(model)
    page = render_html(model, md)
    md_path = out_dir / "report.md"
    html_path = out_dir / "report.html"
    json_path = out_dir / "run_model.json"
    md_path.write_text(md, encoding="utf-8")
    html_path.write_text(page, encoding="utf-8")
    json_path.write_text(model.to_json(), encoding="utf-8")
    result = BuildResult(model, md_path, html_path, json_path)
    if pdf:
        try:
            # Images sit next to the report while relative links (the logo) are from the job.
            image_uri = (out_dir / images_module.IMAGE_DIR).resolve().as_uri()
            printable = page.replace(f'src="{images_module.IMAGE_DIR}/', f'src="{image_uri}/')
            result.pdf = write_pdf(printable, out_dir / "report.pdf", base_url=job.resolve())
        except (ImportError, OSError) as exc:
            result.warnings.append(f"PDF not written: {html.escape(str(exc))}")
    return result
