"""English labels for result names (task 4.5): fields, components and table parameters.

The labels come from ``en/glossary.yaml`` only (CLAUDE.md rule 3); the French name is always
kept next to the label, never replaced. A name the glossary does not define is labelled by
composition when it is a defined stem plus an axis suffix (``MASS_EFFE_DX`` -> "effective modal
mass (X)", ``CDG_Y`` -> "center of gravity (Y)"), otherwise it has no label (``None``) and the
caller shows the French name alone.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from codeaster_en import data
from codeaster_en.validate.glossary import load as load_glossary

DEFAULT_GLOSSARY = data.glossary_path()

# Kinds that hold names of solver quantities. `abbrev` is kept out: SIGM alone means "stress",
# but as a label for a bare token like NO ("node") it would mislead.
_KINDS = ("concept", "keyword", "value")
_AXIS_SUFFIXES = {"_DX": "X", "_DY": "Y", "_DZ": "Z", "_X": "X", "_Y": "Y", "_Z": "Z"}


@cache
def _table(path: Path) -> dict[str, str]:
    entries = load_glossary(path) or []
    out: dict[str, str] = {}
    for kind in _KINDS:  # first kind wins: a concept label beats a keyword label
        for entry in entries:
            if entry.get("kind") == kind and isinstance(entry.get("fr"), str):
                out.setdefault(entry["fr"], str(entry["en"]))
    return out


class Labels:
    """Looks up English labels in a glossary file (default: the overlay's own)."""

    def __init__(self, glossary: str | Path | None = None) -> None:
        self.path = Path(glossary) if glossary else DEFAULT_GLOSSARY
        self._map = _table(self.path)

    def get(self, name: str) -> str | None:
        """The English label of a French name, or ``None`` when the glossary has none."""
        if name in self._map:
            return self._map[name]
        for suffix, axis in _AXIS_SUFFIXES.items():
            if name.endswith(suffix):
                stem = self._map.get(name[: -len(suffix)])
                if stem:
                    return f"{stem} ({axis})"
        return None

    def many(self, names: list[str]) -> dict[str, str | None]:
        return {n: self.get(n) for n in names}

    def describe(self, name: str) -> str:
        """``"von Mises (VMIS)"``, or the French name alone when there is no label."""
        label = self.get(name)
        return f"{label} ({name})" if label else name
