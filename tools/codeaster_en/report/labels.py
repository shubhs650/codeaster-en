"""English wording for the report (task 4.6): glossary terms, unit systems, number format.

Every English name of a solver term comes from ``en/glossary.yaml`` (CLAUDE.md rule 3); a term
without an entry is shown by its French identifier alone, in code format. Units come from the
unit system the job declares in ``run.json`` (``docs/REPORT-SPEC.md`` §4).
"""

from __future__ import annotations

import math
from functools import cache
from pathlib import Path

from codeaster_en.results.labels import DEFAULT_GLOSSARY
from codeaster_en.validate.glossary import load as load_glossary


@cache
def _entries(path: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for entry in load_glossary(path) or []:
        fr, kind = entry.get("fr"), entry.get("kind")
        if isinstance(fr, str) and isinstance(kind, str):
            out.setdefault(fr, {}).setdefault(kind, str(entry["en"]))
    return out


class Terms:
    """Glossary lookup by French name, preferring the given kinds in order."""

    def __init__(self, glossary: str | Path | None = None) -> None:
        self._map = _entries(Path(glossary) if glossary else DEFAULT_GLOSSARY)

    def get(self, fr: str, *kinds: str) -> str | None:
        found = self._map.get(fr)
        if not found:
            return None
        for kind in kinds or ("concept", "keyword", "value", "command", "term"):
            if kind in found:
                return found[kind]
        return None if kinds else next(iter(found.values()))


# Unit systems of run.json (docs/schemas/run.schema.json). Keys are quantities the report prints.
UNIT_SYSTEMS: dict[str, dict[str, str]] = {
    "SI": {
        "length": "m",
        "force": "N",
        "stress": "Pa",
        "mass": "kg",
        "time": "s",
        "density": "kg/m³",
        "moment": "N·m",
        "force_per_length": "N/m",
        "moment_per_length": "N·m/m",
        "angle": "rad",
        "frequency": "Hz",
        "expansion": "1/K",
    },
    "SI_mm": {
        "length": "mm",
        "force": "N",
        "stress": "MPa",
        "mass": "t",
        "time": "s",
        "density": "t/mm³",
        "moment": "N·mm",
        "force_per_length": "N/mm",
        "moment_per_length": "N·mm/mm",
        "angle": "rad",
        "frequency": "Hz",
        "expansion": "1/K",
    },
}
UNIT_SYSTEM_NAMES = {"SI": "SI (m, N, Pa, kg, s)", "SI_mm": "SI-mm (mm, N, MPa, t, s)"}

# Quantity of a component, by field family.
_SHELL_FORCES = {"NXX", "NYY", "NXY", "QX", "QY"}
_SHELL_MOMENTS = {"MXX", "MYY", "MXY"}


def quantity(field: str, component: str) -> str | None:
    """The physical quantity of ``field``/``component`` (a key of :data:`UNIT_SYSTEMS`)."""
    if field.startswith("DEPL"):
        return "angle" if component.startswith("DR") else "length"
    if field.startswith(("REAC_NODA", "FORC_NODA")):
        return "moment" if component.startswith("DR") else "force"
    if field.startswith(("SIEQ", "SIGM", "SIEF")):
        if component == "TRIAX" or component.startswith("VECT_"):
            return None
        return "stress"
    if field.startswith("EFGE"):
        if component in _SHELL_FORCES:
            return "force_per_length"
        if component in _SHELL_MOMENTS:
            return "moment_per_length"
    return None


MATERIAL_QUANTITIES = {"E": "stress", "RHO": "density", "ALPHA": "expansion"}


def unit(system: str | None, qty: str | None) -> str:
    if not system or not qty or system not in UNIT_SYSTEMS:
        return ""
    return UNIT_SYSTEMS[system].get(qty, "")


def guess_system(young: float | None) -> str | None:
    """Unit system suggested by the magnitude of Young's modulus (steel: 2.1e5 MPa or
    2.1e11 Pa). A heuristic: the report flags it as an assumption."""
    if young is None or young <= 0:
        return None
    exp = math.log10(young)
    if 3 <= exp < 7:
        return "SI_mm"
    if 8 <= exp < 13:
        return "SI"
    return None


def num(value: float | int | None, digits: int = 4) -> str:
    """Engineering notation with ``digits`` significant figures: plain between 0.001 and
    99 999, otherwise mantissa and a power of ten that is a multiple of 3 (``210.0e3``)."""
    if value is None:
        return "–"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    x = float(value)
    if math.isnan(x):
        return "–"
    if x == 0:
        return "0"
    x = float(f"{x:.{digits - 1}e}")  # round to the significant figures first
    mag = math.floor(math.log10(abs(x)))
    if -3 <= mag < 5:
        return f"{x:.{max(digits - 1 - mag, 0)}f}"
    exp3 = 3 * math.floor(mag / 3)
    return f"{x / 10**exp3:.{max(digits - 1 - (mag - exp3), 0)}f}e{exp3}"


def full(value: float | None) -> str:
    """Full precision (for coordinates and traceability footnotes)."""
    return "–" if value is None else f"{value:.10g}"
