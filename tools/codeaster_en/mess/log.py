"""Parsed ``.mess`` log: the event list plus the views the renderer and reports need."""

from __future__ import annotations

import json
import re
import time
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from codeaster_en.mess.commlines import line_mapper
from codeaster_en.mess.events import (
    Diagnostic,
    Event,
    Notice,
    Stage,
    StageEnd,
)
from codeaster_en.mess.parser import Parser

SCHEMA_VERSION = 1

# CATAMESS_89 lists the alarms of the run: "(*) MODELISA8_14   émise    3 fois", where "(*)"
# marks an ignored alarm (upstream Messages/catamess.py and Utmess.info_alarm).
RE_ALARM_COUNT = re.compile(
    r"(?P<ignored>\(\*\))?\s*(?P<id>[A-Z][A-Z0-9]*_\d+)\s+\D+?\s+(?P<n>\d+)"
)


@dataclass
class ParsedLog:
    events: list[Event]
    path: str | None = None
    lines: int = 0
    _by_kind: dict[str, list[Event]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        for ev in self.events:
            self._by_kind.setdefault(ev.kind, []).append(ev)
        if self.events and not self.lines:
            self.lines = self.events[-1].end

    def of(self, kind: str) -> list[Any]:
        return list(self._by_kind.get(kind, []))

    @property
    def diagnostics(self) -> list[Diagnostic]:
        """Boxed messages, without the copies re-printed inside tracebacks."""
        return [d for d in self.of("diagnostic") if not d.repeat]

    @property
    def errors(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.is_error]

    def stages(self) -> list[dict[str, Any]]:
        """One record per command: start and end merged by command number."""
        out: dict[int, dict[str, Any]] = {}
        for ev in self.events:
            if isinstance(ev, Stage):
                rec = out.setdefault(ev.number, {"number": ev.number})
                rec.update(
                    command=ev.command,
                    concept=ev.concept,
                    source_line=ev.source_line,
                    comm_line=ev.comm_line,
                    start=ev.start,
                )
            elif isinstance(ev, StageEnd) and ev.number:
                rec = out.setdefault(ev.number, {"number": ev.number})
                if ev.command and not rec.get("command"):
                    rec["command"] = ev.command
                rec.update(
                    result=ev.result,
                    result_type=ev.result_type,
                    cpu_s=ev.cpu_s,
                    elapsed_s=ev.elapsed_s,
                    memory_peak_mb=ev.memory_peak_mb,
                    end=ev.end,
                )
        for ev in self.diagnostics:
            if ev.stage in out:
                out[ev.stage].setdefault("diagnostics", []).append(ev.message_id)
        for rec in out.values():
            rec["completed"] = "end" in rec
        return [out[k] for k in sorted(out)]

    def summary(self) -> dict[str, Any]:
        header = next(iter(self.of("header")), None)
        trailer = next(iter(self.of("summary")), None)
        exit_codes = [e.exit_code for e in self.of("runner") if e.exit_code is not None]
        alarms: dict[str, int] = {}
        ignored: list[str] = []
        for d in self.diagnostics:
            if d.message_id == "CATAMESS_89":
                for m in RE_ALARM_COUNT.finditer(d.body):
                    alarms[m["id"]] = int(m["n"])
                    if m["ignored"]:
                        ignored.append(m["id"])
        tests = Counter(
            row["verdict"] for t in self.of("table") if t.name == "test_resu" for row in t.rows
        )
        total = None
        for t in self.of("table"):
            if t.name == "timings":
                total = next((r for r in t.rows if r["command"] == "TOTAL_JOB"), total)
        first_error = next(iter(self.errors), None)
        tracebacks = [t for t in self.of("traceback") if t.exception]
        failed_stage = first_error.stage if first_error else None
        stages = {s["number"]: s for s in self.stages()}
        return {
            "version": header.version if header else None,
            "message_language": header.message_language if header else None,
            "diagnostic_job": trailer.diagnostic if trailer else None,
            "exit_code": exit_codes[-1] if exit_codes else None,
            "normal_end": any(
                isinstance(n, Notice) and n.tag == "FIN" and "ARRET NORMAL" in n.message
                for n in self.of("notice")
            ),
            "alarms": alarms,
            "ignored_alarms": ignored,
            "errors": list(dict.fromkeys(d.message_id or d.severity for d in self.errors)),
            "failed_stage": stages.get(failed_stage) if failed_stage else None,
            "exception": (
                {
                    "type": tracebacks[-1].exception,
                    "message": tracebacks[-1].message,
                    "source_line": tracebacks[-1].source_line,
                    "comm_line": tracebacks[-1].comm_line,
                }
                if tracebacks
                else None
            ),
            "test_resu": dict(tests),
            "total_elapsed_s": total["elapsed_s"] if total else None,
            "lines": self.lines,
            "events": dict(Counter(ev.kind for ev in self.events)),
        }

    def to_dict(self, raw: bool = True) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "path": self.path,
            "summary": self.summary(),
            "stages": self.stages(),
            "events": [ev.to_dict(raw=raw) for ev in self.events],
        }

    def to_json(self, raw: bool = True) -> str:
        return json.dumps(self.to_dict(raw=raw), ensure_ascii=False, indent=2) + "\n"


def _comm_mapper(mess: Path, comm: Path | str | None):
    if comm is None:
        # A job directory laid out like the fixtures: <case>/input/run.comm next to output/.
        guess = mess.parent.parent / "input" / "run.comm"
        comm = guess if guess.is_file() else None
    if comm is None:
        return None
    return line_mapper(Path(comm).read_text(encoding="utf-8", errors="replace"))


def parse_lines(lines: Iterable[str], comm_text: str | None = None) -> ParsedLog:
    mapper = line_mapper(comm_text) if comm_text is not None else None
    return ParsedLog(list(Parser(mapper).events(lines)))


def parse(path: str | Path, comm: str | Path | None = None) -> ParsedLog:
    """Parse a whole ``.mess`` file. ``comm`` (default: ``../input/run.comm`` when present)
    lets stages and tracebacks report the line of the user's command file."""
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    events = list(Parser(_comm_mapper(path, comm)).events(text.splitlines()))
    return ParsedLog(events, path=str(path), lines=len(text.splitlines()))


def _follow(path: Path, poll: float, idle_timeout: float | None) -> Iterator[str]:
    """Yield complete lines of a growing file; stop after ``run_aster``'s trailer or when the
    file has not grown for ``idle_timeout`` seconds."""
    waited = 0.0
    while not path.exists():
        if idle_timeout is not None and waited >= idle_timeout:
            return
        time.sleep(poll)
        waited += poll
    with path.open(encoding="utf-8", errors="replace") as fobj:
        partial = ""
        idle = 0.0
        trailer = False
        while True:
            chunk = fobj.readline()
            if chunk:
                idle = 0.0
                partial += chunk
                if not partial.endswith("\n"):
                    continue
                line, partial = partial[:-1], ""
                yield line
                if line.startswith("--- DIAGNOSTIC JOB :"):
                    trailer = True
                continue
            if trailer:
                # The trailer is followed by one rule line; give it a moment, then stop.
                if idle >= max(poll, 0.5):
                    if partial:
                        yield partial
                    return
            elif idle_timeout is not None and idle >= idle_timeout:
                if partial:
                    yield partial
                return
            time.sleep(poll)
            idle += poll


def stream(
    path: str | Path,
    comm: str | Path | None = None,
    follow: bool = True,
    poll: float = 0.5,
    idle_timeout: float | None = 600.0,
) -> Iterator[Event]:
    """Yield events from a ``.mess`` file, following it while the solver writes it.

    Each event is yielded once it is complete (at most a few lines behind the writer). With
    ``follow=False`` the file is read as it is now. Following stops after ``run_aster``'s
    ``DIAGNOSTIC JOB`` trailer, or after ``idle_timeout`` seconds without new output.
    """
    path = Path(path)
    parser = Parser(_comm_mapper(path, comm))
    if not follow:
        text = path.read_text(encoding="utf-8", errors="replace")
        yield from parser.events(text.splitlines())
        return
    yield from parser.events(_follow(path, poll, idle_timeout))
