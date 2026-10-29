"""``IMPR_TABLE`` output files (task 4.5): ``read_tables(path)`` -> :class:`Table` list.

The fixtures write tables with ``IMPR_TABLE(FORMAT="TABLEAU", SEPARATEUR=",")``. Each table in
the file starts with a banner, then a header line of parameter names, then one line per row::

    #
    #--------------------------------------------------------------------------------
    ##ASTER 17.04.22 CONCEPT 0000002a CALCULE LE 29/10/2026 A 02:15:32 DE TYPE
    INTITULE,RESU,NOM_CHAM,NUME_ORDRE,INST,DX,DY,DZ
    REAC_BASE       ,00000007,REAC_NODA       ,           1, 0.00000E+00, 3.89164E+03,...

(``tests/fixtures/solid_static/output/tables/reactions.csv``). Several ``IMPR_TABLE`` calls on
the same unit append further tables to the same file. Text cells are padded with blanks; they
are stripped here. Numbers are printed with 6 significant figures by default (``FORMAT_R``), so
a table value is less precise than the same quantity read from the ``.rmed``.
Without ``SEPARATEUR`` the cells are separated by blanks; that layout is read too.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BANNER = re.compile(r"^#+ ?ASTER\s+(?P<version>\S+)\s+CONCEPT\s+(?P<concept>\S+)")
_INT = re.compile(r"^[+-]?\d+$")


@dataclass
class Table:
    """One printed table: its parameter names (French, the solver's API) and its rows."""

    columns: list[str]
    rows: list[dict[str, Any]]
    concept: str | None = None
    source: str | None = None
    banner: str | None = None
    labels: dict[str, str | None] = field(default_factory=dict)

    def column(self, name: str) -> list[Any]:
        return [row.get(name) for row in self.rows]

    def has(self, *names: str) -> bool:
        return all(n in self.columns for n in names)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "concept": self.concept,
            "columns": self.columns,
            "labels": self.labels,
            "rows": self.rows,
        }


def _cell(text: str) -> Any:
    text = text.strip()
    if text == "" or text == "-":
        return None
    if _INT.match(text):
        return int(text)
    try:
        return float(text)
    except ValueError:
        return text


def _split(line: str, sep: str | None) -> list[str]:
    return line.split(sep) if sep else line.split()


def parse_tables(text: str, source: str | None = None) -> list[Table]:
    """Every table in the text of one ``IMPR_TABLE`` unit, in file order."""
    tables: list[Table] = []
    concept: str | None = None
    banner: str | None = None
    current: Table | None = None
    sep: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        m = BANNER.match(line)
        if m:
            concept, banner, current = m.group("concept"), line.strip(), None
            continue
        if not line.strip():
            current = None
            continue
        if line.startswith("#"):
            continue
        if current is None:
            sep = "," if "," in line else None
            current = Table(
                columns=[c.strip() for c in _split(line, sep)],
                rows=[],
                concept=concept,
                source=source,
                banner=banner,
            )
            tables.append(current)
            concept = banner = None
            continue
        cells = [_cell(c) for c in _split(line, sep)]
        if len(cells) != len(current.columns):
            raise ValueError(
                f"{source or 'table'}: row has {len(cells)} cells, header has "
                f"{len(current.columns)}: {line!r}"
            )
        current.rows.append(dict(zip(current.columns, cells, strict=True)))
    return tables


def read_tables(path: str | Path) -> list[Table]:
    """Read one table file (one ``IMPR_TABLE`` unit, e.g. ``output/tables/reactions.csv``)."""
    path = Path(path)
    return parse_tables(path.read_text(encoding="utf-8", errors="replace"), source=str(path))


def read_table_dir(directory: str | Path) -> list[Table]:
    """All tables of every file in a job's ``output/tables/`` directory, files sorted by name."""
    directory = Path(directory)
    tables: list[Table] = []
    if not directory.is_dir():
        return tables
    for path in sorted(p for p in directory.iterdir() if p.is_file()):
        tables.extend(read_tables(path))
    return tables
