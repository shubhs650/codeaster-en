"""Read code_aster ``.mess`` logs (task 4.3): ``parse(path)`` -> :class:`ParsedLog`,
``stream(path)`` for a log that is still being written, ``classify(log)`` for the failure class
of a run. The English renderer is task 4.4.
"""

from codeaster_en.mess.classify import Classification, FailureClass, classify
from codeaster_en.mess.events import (
    Blank,
    Diagnostic,
    Event,
    Header,
    Notice,
    Runner,
    Stage,
    StageEnd,
    Summary,
    Table,
    Text,
    Traceback,
)
from codeaster_en.mess.log import ParsedLog, parse, parse_lines, stream

__all__ = [
    "Blank",
    "Classification",
    "Diagnostic",
    "Event",
    "FailureClass",
    "Header",
    "Notice",
    "ParsedLog",
    "Runner",
    "Stage",
    "StageEnd",
    "Summary",
    "Table",
    "Text",
    "Traceback",
    "classify",
    "parse",
    "parse_lines",
    "stream",
]
