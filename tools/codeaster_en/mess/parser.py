"""Line-by-line parser for code_aster ``.mess`` logs (task 4.3).

The parser reads the log once, in order, with a few lines of look-ahead, and yields
:mod:`~codeaster_en.mess.events` as soon as each one is complete. It never drops a line: a line
that matches no rule becomes part of a ``text`` event (or ``blank`` for empty lines), so the
events always cover the whole file.

The layouts recognized here were read from the solver's own formatting code and checked on the
committed fixture logs (``tests/fixtures/*/output/run.mess``, code_aster 17.4.22, ADR-011):

- boxes: ``Utilities/strfunc.py`` ``textbox`` (``╔ ║ ╚``, 100 columns) around the text built by
  ``Messages/Utmess.py`` ``format_message`` (``<TYPE> <ID>``, blank line, body, blank line,
  comment for A/E/S/F);
- command echo and timings: ``Supervis/ExecuteCommand.py`` (``# Commande #N de <file>, ligne L``,
  ``# Résultat commande``, ``# Mémoire (Mo)``, ``# Fin commande``);
- trailer: ``run_aster/run.py`` ``FMT_DIAG`` and the states of ``run_aster/status.py``.

Long lines are wrapped at 100 columns by ``cut_long_lines``, which drops the separator at the
break. The parser re-joins the two places where that matters (a wrapped command header and a
wrapped result type); wrapped free text is kept as printed.
"""

from __future__ import annotations

import ast
import re
from collections import deque
from collections.abc import Callable, Iterable, Iterator

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

BOX_TOP = " ╔"  # " ╔"
BOX_BOTTOM = " ╚"  # " ╚"
BOX_SIDE = "║"  # "║"

RE_BOX_HEADER = re.compile(r"^<(?P<sev>[A-Za-z_]+)>(?:\s+<(?P<id>[A-Z][A-Z0-9_]*)>)?\s*$")
RE_MESSAGE_ID = re.compile(r"^(?P<family>[A-Z][A-Z0-9]*)_(?P<number>\d+)$")
RE_NOTICE = re.compile(
    r"^\s*<(?P<sev>I|A|E|F|S|INFO)>(?:\s+<(?P<tag>[A-Z][A-Z0-9_]*)>)?(?:\s+(?P<msg>.*?))?\s*$"
)

RE_ANCHOR = re.compile(r"^\.\. _stg\d+_txt\d+\s*$")
RE_RULE = re.compile(r"^# -{20,}\s*$")
RE_STAGE = re.compile(r"^# Commande #(?P<num>\d+) de (?P<file>.+), ligne (?P<line>\d+)\s*$")
RE_STAGE_PARTIAL = re.compile(r"^# Commande #\d+ de ")
RE_ECHO_HEAD = re.compile(r"^(?:(?P<concept>\w+)\s*=\s*)?(?P<command>[A-Z][A-Z0-9_]*)\(")
RE_RESULT = re.compile(
    r"^# Résultat commande #(?P<num>\d+) \((?P<cmd>[A-Z0-9_]+)\): (?P<name>\S+) \('<[^']*>'\)"
    r"(?: de type(?: (?P<type><[^>]*>))?)?\s*$"
)
RE_TYPE_CONT = re.compile(r"^<\w+>\s*$")
RE_DEPENDS = re.compile(r"^# Dépend de :\s*$")
RE_DEPENDS_ITEM = re.compile(r"^# - (?P<name>\S+) ")
RE_MEMORY = re.compile(r"^# Mémoire \(Mo\) :\s+(?P<peak>[\d.]+) /")
RE_END = re.compile(
    r"^# Fin commande #(?P<num>\d+)\s+user\+syst:\s+(?P<cpu>[\d.]+)s "
    r"\(syst:\s+(?P<sys>[\d.]+)s, elaps:\s+(?P<elaps>[\d.]+)s\)"
)
STAGE_END_STARTS = ("# Résultat commande #", "# Mémoire (Mo) :", "# Fin commande #", "# Dépend de")

RE_HEADER = re.compile(r"-- CODE_ASTER -- VERSION")
RE_KEY_VALUE = re.compile(r"^\s*(?P<key>[^:]+?)\s+:\s+(?P<value>.+?)\s*$")

RE_TB_START = "Traceback (most recent call last):"
RE_TB_CHAINED = re.compile(r"^During handling of the above exception|^The above exception was")
RE_TB_FRAME = re.compile(r'^\s+File "(?P<file>[^"]+)", line (?P<line>\d+)')
RE_TB_EXC = re.compile(r"^(?P<exc>[A-Za-z_][\w.]*)(?::\s?(?P<msg>.*))?$")

RE_DIAG_RULE = re.compile(r"^-{60}\s*$")
RE_DIAG = re.compile(r"^--- DIAGNOSTIC JOB : (?P<diag>.+?)\s*$")
RE_DASHES = re.compile(r"^-{20,}\s*$")

RE_TEST_RULE = re.compile(r"^-{80}\s*$")
RE_TEST_LINE = re.compile(r"^( ---- | {6}\S| (OK|NOOK) | +$)")
RE_MODES_HEAD = re.compile(r"^numéro\s+fréquence \(HZ\)\s+norme d'erreur\s*$")
RE_MODES_ROW = re.compile(r"^\s*(?P<n>\d+)\s+(?P<f>[-+0-9.Ee]+)\s+(?P<err>[-+0-9.Ee]+)\s*$")
RE_MODES_TAIL = re.compile(r"^Norme d'erreur moyenne\s*:")
RE_STARS = re.compile(r"^ \*{20,}\s*$")
RE_TIMING_ROW = re.compile(
    r"^ \* (?P<name>.+?)\s*:\s*(?P<user>[\d.]+) :\s*(?P<sys>[\d.]+) :\s*(?P<tot>[\d.]+) :"
    r"\s*(?P<elaps>[\d.]+) \*\s*$"
)

RE_EXIT = re.compile(r"^EXECUTION_CODE_ASTER_EXIT_\d+=(?P<rc>-?\d+)\s*$")
RUNNER_LINES = tuple(
    re.compile(p)
    for p in (
        r"^setting '--\w+' value to ",
        r"^copying \(\w+\) '",
        r"^checking MPI initialization",
        r"^using COMM_WORLD\.",
        r"^MPI is initialized\.",
        r"^starting the execution\.\.\.",
        r"^INFO '[^']*' deleted",
        r"^Deleting '[^']*': ",
        r"^End of the Code_Aster execution",
        r"^Code_Aster MPI exits normally",
        r"^Exited\s*$",
        r"^Exception: Trying to close the database after an uncaught exception",
        r"^EXECUTION_CODE_ASTER_EXIT_\d+=",
    )
)

# Comments appended by Utmess.format_message (upstream Messages/Utmess.py, ``dcomm``).
UTMESS_FOOTERS = (
    "Ceci est une alarme. Si vous ne comprenez pas le sens de cette alarme, "
    "vous pouvez obtenir des résultats inattendus !",
    "Cette erreur sera suivie d'une erreur fatale.",
    "Cette erreur est fatale. Le code s'arrête. Toutes les étapes du calcul ont été sauvées "
    "dans la base jusqu'au moment de l'arret.",
    "Cette erreur est fatale. Le code s'arrête.",
)

_WS = re.compile(r"\s+")


def _collapse(text: str) -> str:
    return _WS.sub(" ", text).strip()


_FOOTERS = {_collapse(f) for f in UTMESS_FOOTERS}


class _Reader:
    """Line source with look-ahead; ``lineno`` is the number of the last consumed line."""

    def __init__(self, lines: Iterable[str]) -> None:
        self._it = iter(lines)
        self._buf: deque[str] = deque()
        self.lineno = 0

    def peek(self, k: int = 0) -> str | None:
        while len(self._buf) <= k:
            try:
                line = next(self._it)
            except StopIteration:
                return None
            self._buf.append(line.rstrip("\r\n"))
        return self._buf[k]

    def take(self) -> str:
        if self.peek() is None:
            raise EOFError
        self.lineno += 1
        return self._buf.popleft()


class Parser:
    """Turns an iterable of lines into events. One instance per log.

    ``comm_line`` optionally maps a line of the executed file (``run.comm.changed.py``) back to
    the user's ``.comm``; see :func:`codeaster_en.mess.commlines.line_mapper`.
    """

    def __init__(self, comm_line: Callable[[int], int | None] | None = None) -> None:
        self._comm_line = comm_line
        self._stage: int | None = None
        self._seen_boxes: set[tuple[str, str | None, str]] = set()

    # -- public -----------------------------------------------------------------------------

    def events(self, lines: Iterable[str]) -> Iterator[Event]:
        r = _Reader(lines)
        pending: list[str] = []
        pending_start = 0
        pending_blank = False
        pending_stage: int | None = None  # stage open when the first loose line was read
        while (line := r.peek()) is not None:
            event = self._match(r, line)
            if event is not None:
                if pending:
                    yield self._loose(pending_start, pending, pending_blank, pending_stage)
                    pending = []
                yield event
                continue
            blank = not line.strip()
            if pending and blank != pending_blank:
                yield self._loose(pending_start, pending, pending_blank, pending_stage)
                pending = []
            if not pending:
                pending_start, pending_blank, pending_stage = r.lineno + 1, blank, self._stage
            pending.append(r.take())
        if pending:
            yield self._loose(pending_start, pending, pending_blank, pending_stage)

    # -- dispatch ---------------------------------------------------------------------------

    def _match(self, r: _Reader, line: str) -> Event | None:
        if line.startswith(BOX_TOP):
            return self._box(r)
        if (
            RE_ANCHOR.match(line)
            or (RE_RULE.match(line) and RE_STAGE_PARTIAL.match(r.peek(1) or ""))
            or RE_STAGE_PARTIAL.match(line)
        ):
            return self._stage_start(r)
        if line.startswith(STAGE_END_STARTS):
            return self._stage_end(r)
        if RE_HEADER.search(line):
            return self._header(r)
        if line == RE_TB_START or RE_TB_CHAINED.match(line):
            return self._traceback(r)
        if RE_DIAG_RULE.match(line) and RE_DIAG.match(r.peek(1) or ""):
            return self._summary(r)
        if RE_TEST_RULE.match(line) and (r.peek(1) or "").startswith(" ---- "):
            return self._test_resu(r)
        if RE_MODES_HEAD.match(line):
            return self._modes(r)
        if RE_STARS.match(line) and (r.peek(1) or "").startswith(" * COMMAND"):
            return self._timings(r)
        if RE_DASHES.match(line) and "MPI" in (r.peek(1) or ""):
            return self._mpi_block(r)
        if any(p.match(line) for p in RUNNER_LINES):
            start = r.lineno + 1
            text = r.take()
            m = RE_EXIT.match(text)
            return Runner(start, [text], self._stage, exit_code=int(m["rc"]) if m else None)
        m = RE_NOTICE.match(line)
        if m:
            start = r.lineno + 1
            return Notice(
                start,
                [r.take()],
                self._stage,
                severity=m["sev"],
                tag=m["tag"],
                message=m["msg"] or "",
            )
        return None

    @staticmethod
    def _loose(start: int, lines: list[str], blank: bool, stage: int | None) -> Event:
        cls = Blank if blank else Text
        return cls(start, list(lines), stage)

    # -- constructs -------------------------------------------------------------------------

    def _box(self, r: _Reader) -> Diagnostic:
        start = r.lineno + 1
        lines = [r.take()]
        while (nxt := r.peek()) is not None:
            lines.append(r.take())
            if nxt.startswith(BOX_BOTTOM):
                break
        inner = []
        for raw in lines[1:-1] if lines[-1].startswith(BOX_BOTTOM) else lines[1:]:
            s = raw.strip()
            if s.startswith(BOX_SIDE):
                s = s[1:]
            if s.endswith(BOX_SIDE):
                s = s[:-1]
            inner.append(s[1:].rstrip() if s.startswith(" ") else s.rstrip())
        severity, message_id = "", None
        if inner and (h := RE_BOX_HEADER.match(inner[0])):
            severity, message_id = h["sev"], h["id"]
            inner = inner[1:]
        while inner and not inner[0]:
            inner.pop(0)
        while inner and not inner[-1]:
            inner.pop()
        footer = None
        for k in range(1, min(4, len(inner)) + 1):
            if _collapse(" ".join(inner[-k:])) in _FOOTERS:
                footer = "\n".join(inner[-k:])
                inner = inner[:-k]
                while inner and not inner[-1]:
                    inner.pop()
                break
        body = "\n".join(inner)
        family = number = None
        if message_id and (m := RE_MESSAGE_ID.match(message_id)):
            family, number = m["family"], int(m["number"])
        key = (severity, message_id, body)
        repeat = key in self._seen_boxes
        self._seen_boxes.add(key)
        return Diagnostic(
            start,
            lines,
            self._stage,
            severity=severity,
            message_id=message_id,
            family=family,
            number=number,
            body=body,
            footer=footer,
            repeat=repeat,
        )

    def _stage_start(self, r: _Reader) -> Event:
        start = r.lineno + 1
        lines: list[str] = []
        while (nxt := r.peek()) is not None and (RE_ANCHOR.match(nxt) or RE_RULE.match(nxt)):
            lines.append(r.take())
        head = r.peek()
        if head is None or not RE_STAGE_PARTIAL.match(head):
            # An anchor or rule without a command header: keep it verbatim.
            return Text(start, lines, self._stage)
        lines.append(r.take())
        joined = head
        if not RE_STAGE.match(joined) and (cont := r.peek()) is not None:
            # cut_long_lines broke a long path and dropped the "." at the break.
            if RE_STAGE.match(f"{head}.{cont}"):
                lines.append(r.take())
                joined = f"{head}.{cont}"
        m = RE_STAGE.match(joined)
        echo: list[str] = []
        while (nxt := r.peek()) is not None and nxt.strip():
            if nxt.startswith(BOX_TOP) or nxt.startswith(STAGE_END_STARTS):
                break
            echo.append(r.take())
            try:
                ast.parse("\n".join(echo))
            except SyntaxError:
                continue
            break
        lines.extend(echo)
        number = int(m["num"]) if m else 0
        command = concept = None
        if echo and (e := RE_ECHO_HEAD.match(echo[0])):
            command, concept = e["command"], e["concept"]
        source_line = int(m["line"]) if m else None
        source_file = m["file"] if m else None
        self._stage = number
        return Stage(
            start,
            lines,
            number,
            number=number,
            command=command,
            concept=concept,
            source_file=source_file,
            source_line=source_line,
            comm_line=self._map_line(source_file, source_line),
            command_text="\n".join(echo),
        )

    def _stage_end(self, r: _Reader) -> StageEnd | None:
        start = r.lineno + 1
        stage = self._stage
        ev = StageEnd(start, [], stage)
        while (nxt := r.peek()) is not None:
            if nxt.startswith("# Résultat commande #"):
                ev.lines.append(r.take())
                text = nxt
                if (cont := r.peek()) is not None and RE_TYPE_CONT.match(cont):
                    ev.lines.append(r.take())
                    text = f"{nxt.rstrip()} {cont.strip()}"
                if m := RE_RESULT.match(text):
                    ev.number, ev.command = int(m["num"]), m["cmd"]
                    ev.result, ev.result_type = m["name"], (m["type"] or "").strip("<>") or None
            elif RE_DEPENDS.match(nxt):
                ev.lines.append(r.take())
            elif m := RE_DEPENDS_ITEM.match(nxt):
                ev.lines.append(r.take())
                ev.depends_on.append(m["name"])
            elif m := RE_MEMORY.match(nxt):
                ev.lines.append(r.take())
                ev.memory_peak_mb = float(m["peak"])
            elif m := RE_END.match(nxt):
                ev.lines.append(r.take())
                ev.number = int(m["num"])
                ev.cpu_s, ev.sys_s, ev.elapsed_s = (
                    float(m["cpu"]),
                    float(m["sys"]),
                    float(m["elaps"]),
                )
            elif RE_RULE.match(nxt) and ev.cpu_s is not None:
                ev.lines.append(r.take())
                break
            else:
                break
        if not ev.lines:  # a line that starts like a stage end but is not one
            return None
        if ev.number and ev.stage is None:
            ev.stage = ev.number
        self._stage = None
        return ev

    def _header(self, r: _Reader) -> Header:
        start = r.lineno + 1
        lines = [r.take()]
        # The banner is centered; its empty rows are spaces, the line after it is empty.
        while (nxt := r.peek()) is not None and nxt != "":
            lines.append(r.take())
        ev = Header(start, lines, self._stage)
        for raw in lines[1:]:
            text = raw.strip()
            if m := RE_KEY_VALUE.match(text):
                ev.fields[m["key"]] = m["value"]
            elif text.startswith("Version ") and ev.version is None:
                ev.version = text.split()[1]
        ev.executed_on = ev.fields.get("Exécution du")
        ev.message_language = ev.fields.get("Langue des messages")
        return ev

    def _traceback(self, r: _Reader) -> Traceback:
        start = r.lineno + 1
        lines: list[str] = []
        chained = False
        if RE_TB_CHAINED.match(r.peek() or ""):
            chained = True
            lines.append(r.take())
            while (nxt := r.peek()) is not None and not nxt.strip():
                lines.append(r.take())
        ev = Traceback(start, lines, self._stage, chained=chained)
        if r.peek() != RE_TB_START:
            return ev
        lines.append(r.take())
        while (nxt := r.peek()) is not None and nxt.startswith(" "):
            lines.append(r.take())
            if (m := RE_TB_FRAME.match(nxt)) and not m["file"].startswith(("/", "<")):
                ev.source_file, ev.source_line = m["file"], int(m["line"])
        if (nxt := r.peek()) is not None and (m := RE_TB_EXC.match(nxt)):
            lines.append(r.take())
            ev.exception, ev.message = m["exc"], (m["msg"] or "").strip()
        ev.comm_line = self._map_line(ev.source_file, ev.source_line)
        return ev

    def _summary(self, r: _Reader) -> Summary:
        start = r.lineno + 1
        lines = [r.take(), r.take()]
        diag = RE_DIAG.match(lines[1])
        if (nxt := r.peek()) is not None and RE_DIAG_RULE.match(nxt):
            lines.append(r.take())
        return Summary(start, lines, self._stage, diagnostic=diag["diag"] if diag else "")

    def _test_resu(self, r: _Reader) -> Table:
        start = r.lineno + 1
        lines = [r.take()]
        while (nxt := r.peek()) is not None and RE_TEST_LINE.match(nxt):
            lines.append(r.take())
        rows: list[dict] = []
        context_keys: list[str] = []
        context: dict[str, str] = {}
        row_keys: list[str] = []
        expect_context = False
        for raw in lines[1:]:
            tokens = raw.split()
            if raw.startswith(" ---- "):
                context_keys, expect_context = tokens[1:], True
            elif raw.startswith("      ") and tokens and tokens[0] == "REFERENCE":
                row_keys = tokens
            elif raw.startswith("      ") and expect_context:
                context, expect_context = dict(zip(context_keys, tokens, strict=False)), False
            elif tokens and tokens[0] in ("OK", "NOOK"):
                row: dict = {"verdict": tokens[0]}
                row.update(zip(row_keys, tokens[1:], strict=False))
                for key in ("VALE_REFE", "VALE_CALC"):
                    if key in row:
                        row[key] = _number(row[key])
                row["context"] = dict(context)
                rows.append(row)
        columns = ["verdict", *row_keys]
        return Table(start, lines, self._stage, name="test_resu", columns=columns, rows=rows)

    def _modes(self, r: _Reader) -> Table:
        start = r.lineno + 1
        lines = [r.take()]
        rows: list[dict] = []
        while True:
            k = 0
            while (nxt := r.peek(k)) is not None and not nxt.strip():
                k += 1
            if nxt is None:
                break
            row = RE_MODES_ROW.match(nxt)
            if not row and not RE_MODES_TAIL.match(nxt):
                break
            for _ in range(k + 1):
                lines.append(r.take())
            if not row:
                break
            rows.append(
                {
                    "mode": int(row["n"]),
                    "frequency_hz": float(row["f"]),
                    "error_norm": float(row["err"]),
                }
            )
        return Table(
            start,
            lines,
            self._stage,
            name="modes",
            columns=["mode", "frequency_hz", "error_norm"],
            rows=rows,
        )

    def _timings(self, r: _Reader) -> Table:
        start = r.lineno + 1
        lines: list[str] = []
        while (nxt := r.peek()) is not None and nxt.startswith(" *"):
            lines.append(r.take())
        rows = []
        for raw in lines:
            if m := RE_TIMING_ROW.match(raw):
                rows.append(
                    {
                        "command": m["name"].strip(),
                        "user_s": float(m["user"]),
                        "system_s": float(m["sys"]),
                        "user_system_s": float(m["tot"]),
                        "elapsed_s": float(m["elaps"]),
                    }
                )
        columns = ["command", "user_s", "system_s", "user_system_s", "elapsed_s"]
        return Table(start, lines, self._stage, name="timings", columns=columns, rows=rows)

    def _mpi_block(self, r: _Reader) -> Runner:
        start = r.lineno + 1
        lines = [r.take()]
        while (nxt := r.peek()) is not None:
            lines.append(r.take())
            if RE_DASHES.match(nxt):
                break
        return Runner(start, lines, self._stage)

    def _map_line(self, source_file: str | None, line: int | None) -> int | None:
        if self._comm_line is None or line is None or source_file is None:
            return None
        if source_file.startswith("/"):
            return None
        return self._comm_line(line)


def _number(text: str) -> float | str:
    try:
        return float(text)
    except ValueError:
        return text
