"""Read code_aster results (task 4.5): ``open(path)`` -> :class:`Results` over a ``.rmed`` file
(fields, per-group extrema, reaction sums, modal table) and ``read_tables`` /
``read_table_dir`` for ``IMPR_TABLE`` outputs. Native MED reader over ``h5py`` (ADR-015).
"""

from codeaster_en.results.labels import Labels
from codeaster_en.results.reader import (
    Extremum,
    FieldInfo,
    GroupExtrema,
    ModalTable,
    Mode,
    ReactionGroup,
    ReactionSummary,
    Results,
    StepInfo,
    open,
)
from codeaster_en.results.tables import Table, parse_tables, read_table_dir, read_tables

__all__ = [
    "Extremum",
    "FieldInfo",
    "GroupExtrema",
    "Labels",
    "ModalTable",
    "Mode",
    "ReactionGroup",
    "ReactionSummary",
    "Results",
    "StepInfo",
    "Table",
    "open",
    "parse_tables",
    "read_table_dir",
    "read_tables",
]
