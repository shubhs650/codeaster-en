"""Event model for a code_aster ``.mess`` log (task 4.3).

A parsed log is a flat list of events in file order. Every line of the file belongs to exactly
one event, so concatenating ``event.lines`` gives the file back (the parser's invariant, checked
by the tests on every fixture log). Events are complete when they are yielded, which is what
lets :func:`codeaster_en.mess.stream` follow a log that is still being written.

Kinds (``Event.kind``):

``runner``      a line printed by ``run_aster`` or MPI around the solver (copying files, exit
                code, ``MPI_ABORT``), not by code_aster itself.
``header``      the startup banner (version, date, host, message language, libraries).
``stage``       the start of a command: ``# Commande #N de <file>, ligne L`` and the echoed
                command text.
``stage_end``   the end of a command: result concept and type, memory, CPU and elapsed times.
``diagnostic``  a boxed message ``<TYPE> <FAMILY_N>``: alarms, errors, exceptions, decorated
                information messages. The join key for the English renderer (task 4.4).
``notice``      a one-line tagged message such as ``<I> <FIN> ARRET NORMAL ...``.
``table``       a table the parser understands: ``TEST_RESU`` results, ``CALC_MODES``
                frequencies, the end-of-run timings.
``traceback``   a Python traceback (syntax errors, exceptions re-raised after a diagnostic).
``summary``     ``run_aster``'s trailer ``--- DIAGNOSTIC JOB : <state>``.
``text``        anything else, kept verbatim: informational solver output, which code_aster
                prints without a message ID. This is the unknown-line fallback; it never loses
                text and ``stage`` says which command printed it.
``blank``       a run of empty lines between events.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar

# Box header severities written by ``Utmess.format_message`` / ``get_type_message``
# (upstream code_aster/Messages/Utmess.py): I, A, E, F, S, EXCEPTION, or the name of the
# exception class for code "Z" (AsterError, ConvergenceError, TimeLimitError, ...).
SEVERITY_LABELS = {
    "I": "information",
    "INFO": "information",
    "A": "alarm",
    "E": "error",
    "F": "fatal error",
    "S": "fatal error (base saved)",
    "EXCEPTION": "error (raised as exception)",
}


@dataclass
class Event:
    """Base class: ``start`` is the 1-based number of the first line, ``lines`` the raw text."""

    kind: ClassVar[str] = "event"

    start: int
    lines: list[str]
    stage: int | None = None

    @property
    def end(self) -> int:
        """1-based number of the last line."""
        return self.start + len(self.lines) - 1

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    def to_dict(self, raw: bool = True) -> dict[str, Any]:
        data = {"kind": self.kind, "start": self.start, "end": self.end}
        data.update(asdict(self))
        del data["lines"]
        if raw:
            data["lines"] = list(self.lines)
        return data


@dataclass
class Runner(Event):
    kind: ClassVar[str] = "runner"

    exit_code: int | None = None


@dataclass
class Header(Event):
    kind: ClassVar[str] = "header"

    version: str | None = None
    executed_on: str | None = None
    message_language: str | None = None
    fields: dict[str, str] = field(default_factory=dict)


@dataclass
class Stage(Event):
    kind: ClassVar[str] = "stage"

    number: int = 0
    command: str | None = None
    concept: str | None = None
    source_file: str | None = None
    source_line: int | None = None
    comm_line: int | None = None  # line in the user's .comm, when the parser was given it
    command_text: str = ""


@dataclass
class StageEnd(Event):
    kind: ClassVar[str] = "stage_end"

    number: int = 0
    command: str | None = None
    result: str | None = None
    result_type: str | None = None
    depends_on: list[str] = field(default_factory=list)
    cpu_s: float | None = None
    sys_s: float | None = None
    elapsed_s: float | None = None
    memory_peak_mb: float | None = None


@dataclass
class Diagnostic(Event):
    kind: ClassVar[str] = "diagnostic"

    severity: str = ""
    message_id: str | None = None
    family: str | None = None
    number: int | None = None
    body: str = ""  # text inside the box, header and Utmess footer removed
    footer: str | None = None  # Utmess comment for A/E/F/S ("Ceci est une alarme. ...")
    repeat: bool = False  # same box printed earlier (re-printed inside a traceback)

    @property
    def severity_label(self) -> str:
        return SEVERITY_LABELS.get(self.severity, f"error ({self.severity})")

    @property
    def is_error(self) -> bool:
        return self.severity not in ("I", "INFO", "A")


@dataclass
class Notice(Event):
    kind: ClassVar[str] = "notice"

    severity: str = ""
    tag: str | None = None
    message: str = ""


@dataclass
class Table(Event):
    kind: ClassVar[str] = "table"

    name: str = ""  # test_resu | modes | timings
    columns: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Traceback(Event):
    kind: ClassVar[str] = "traceback"

    exception: str | None = None
    message: str = ""
    chained: bool = False  # starts with "During handling of the above exception ..."
    source_file: str | None = None
    source_line: int | None = None
    comm_line: int | None = None


@dataclass
class Summary(Event):
    kind: ClassVar[str] = "summary"

    diagnostic: str = ""


@dataclass
class Text(Event):
    kind: ClassVar[str] = "text"


@dataclass
class Blank(Event):
    kind: ClassVar[str] = "blank"


EVENT_TYPES: tuple[type[Event], ...] = (
    Runner,
    Header,
    Stage,
    StageEnd,
    Diagnostic,
    Notice,
    Table,
    Traceback,
    Summary,
    Text,
    Blank,
)
