"""English rendering of a parsed ``.mess`` log (task 4.4).

:func:`translate` joins every message the solver printed to ``en/messages`` and fills the
English text with the arguments recovered from the French (:mod:`codeaster_en.mess.catalog`):

- ``diagnostic`` boxes are joined by their ``<TYPE> <ID>``; when the box holds more than its
  own message (``CATAMESS_89`` lists the alarms after its text), the rest is matched like free
  text, with the box's own family tried first;
- informational messages carry no ID in the log, so ``text``, ``header``, ``notice``,
  ``runner``, ``table`` and ``stage_end`` lines, and the ``#`` lines of ``stage`` events, are
  matched against the French templates line by line (longest match wins);
- the command echo of a ``stage``, ``traceback`` and the ``summary`` trailer are kept as
  printed: the echo is the user's command (French names are the solver's API) and the other
  two are already English.

Anything that cannot be rendered keeps its French text and says why: ``untranslated`` (the
message has no English yet), ``unknown-id`` (not in ``en/messages``), ``no-args`` (the text
did not match the French template, so the arguments could not be recovered) or, for free
text, simply no match (output the solver prints without going through the message catalog).

The result renders as an English ``.mess`` (same layout, boxes redrawn at 100 columns) and as
JSON with the diagnostics, an English account of what stopped the run, and coverage counts.
"""

from __future__ import annotations

import json
import re
import textwrap
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from codeaster_en.mess.catalog import MessageCatalog, Template
from codeaster_en.mess.classify import Classification, classify
from codeaster_en.mess.events import Diagnostic, Event, Stage
from codeaster_en.mess.log import ParsedLog
from codeaster_en.mess.parser import FOOTERS_EN

SCHEMA_VERSION = 1
RENDERER = "codeaster_en.mess.render"
RENDERER_VERSION = "1"

MAXLENGTH = 100  # Messages/Utmess.py MAXLENGTH
BOX_TEXT = MAXLENGTH - 6  # Utilities/strfunc.py textbox: width of the text inside the box

# Severity in English (glossary: alarme -> warning, erreur fatale -> fatal error).
SEVERITY_EN = {
    "I": "information",
    "INFO": "information",
    "A": "warning",
    "E": "error",
    "F": "fatal error",
    "S": "fatal error (database saved)",
    "EXCEPTION": "error",
}

_FOOTER_FR = {
    "Ceci est une alarme.": "A",
    "Cette erreur sera suivie": "E",
    "Cette erreur est fatale. Le code s'arrête. Toutes": "S",
    "Cette erreur est fatale. Le code s'arrête.": "F",
}
# A run with our gettext catalog prints FOOTERS_EN itself (task 3.4).
_FOOTER_FR.update({text: key for key, text in FOOTERS_EN.items()})

# Messages the supervisor prints inside another message's argument, or inside lines it formats
# itself: SUPERVIS2_76 (" de type <...>") goes into SUPERVIS2_72's %(k3)s and into the
# "# - <name> <type>" dependency lines (upstream code_aster/Supervis/ExecuteCommand.py lines
# 431 and 968).
NESTED_IDS = ("SUPERVIS2_76",)

# Event kinds whose lines are matched against message templates.
_MATCHED_KINDS = {"text", "header", "notice", "runner", "table", "stage_end", "stage"}
_RE_WS = re.compile(r"\s+")


@dataclass
class Segment:
    """A run of lines of one event and its English, if any."""

    first: int  # index into the event's lines
    last: int
    message_id: str | None = None
    args: dict[str, str] = field(default_factory=dict)
    en: str | None = None
    status: str = "verbatim"  # english | untranslated | verbatim (not a catalog message) | kept
    centered: bool = False


@dataclass
class RenderedDiagnostic:
    start: int
    end: int
    stage: int | None
    severity: str
    severity_en: str
    message_id: str | None
    status: str  # english | untranslated | unknown-id | no-args
    en: str | None
    fr: str
    args: dict[str, str]
    footer_en: str | None
    repeat: bool
    method: str | None = None
    extra: list[dict[str, Any]] = field(default_factory=list)  # other messages in the box
    already_english: bool = False  # printed in English by the solver (gettext, task 3.4)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _footer_key(footer: str | None) -> str | None:
    if not footer:
        return None
    flat = _RE_WS.sub(" ", footer).strip()
    for prefix, key in sorted(_FOOTER_FR.items(), key=lambda kv: -len(kv[0])):
        if flat.startswith(prefix):
            return key
    return None


def _offsets(lines: list[str]) -> list[int]:
    offs = [0]
    for line in lines:
        offs.append(offs[-1] + len(line) + 1)
    return offs


def _last_line(offs: list[int], start: int, end: int) -> int:
    """Index of the line holding character ``end - 1``."""
    j = start
    while j + 1 < len(offs) - 1 and offs[j + 1] < end:
        j += 1
    return j


def _nested(catalog: MessageCatalog, text: str) -> str:
    for mid in NESTED_IDS:
        tpl = catalog.get(mid)
        if tpl is not None:
            text = tpl.replace_inside(text)
    return text


def _fill(tpl: Template, args: dict[str, str], catalog: MessageCatalog) -> str | None:
    """English text of ``tpl`` with ``args``, nested messages in arguments translated too."""
    return tpl.fill({k: _nested(catalog, v) if k.endswith("s") else v for k, v in args.items()})


def match_lines(
    lines: list[str],
    catalog: MessageCatalog,
    eligible: list[bool] | None = None,
    family: str | None = None,
) -> list[Segment]:
    """Split ``lines`` into segments, each a catalog message or a verbatim line.

    ``eligible[i]`` false keeps line ``i`` as printed (``kept``) without trying to match it.
    ``family`` adds that family's templates as candidates for every line (used inside a box,
    where the following messages usually come from the same family).
    """
    text = "\n".join(lines)
    offs = _offsets(lines)
    extra: list[Template] = []
    if family:
        prefix = family + "_"
        extra = [t for i, t in catalog.templates.items() if i.startswith(prefix)]
    segs: list[Segment] = []
    i = 0
    while i < len(lines):
        if eligible is not None and not eligible[i]:
            segs.append(Segment(i, i, status="kept"))
            i += 1
            continue
        if not lines[i].strip():
            segs.append(Segment(i, i, status="blank"))
            i += 1
            continue
        hit = catalog.match_text(text, offs[i])
        if hit is None and extra:
            for tpl in extra:
                got = tpl.match_at(text, offs[i])
                if got and (hit is None or got[0] > hit[1]):
                    hit = (tpl, got[0], got[1])
        if hit is None:
            nested = _nested(catalog, lines[i])
            if nested != lines[i]:
                segs.append(Segment(i, i, NESTED_IDS[0], en=nested.lstrip(), status="english"))
            else:
                segs.append(Segment(i, i))
            i += 1
            continue
        tpl, end, args = hit
        j = _last_line(offs, i, end)
        if eligible is not None and not all(eligible[i : j + 1]):
            segs.append(Segment(i, i))
            i += 1
            continue
        en = _fill(tpl, args, catalog)
        segs.append(
            Segment(
                i,
                j,
                tpl.id,
                args,
                en,
                "english" if en is not None else "untranslated",
                centered=bool(tpl.flags and "CENTER" in tpl.flags),
            )
        )
        i = j + 1
    return segs


def render_diagnostic(diag: Diagnostic, catalog: MessageCatalog) -> RenderedDiagnostic:
    tpl = catalog.get(diag.message_id)
    footer_key = _footer_key(diag.footer)
    rd = RenderedDiagnostic(
        start=diag.start,
        end=diag.end,
        stage=diag.stage,
        severity=diag.severity,
        severity_en=SEVERITY_EN.get(diag.severity, f"error ({diag.severity})"),
        message_id=diag.message_id,
        status="unknown-id",
        en=None,
        fr=diag.body,
        args={},
        footer_en=FOOTERS_EN.get(footer_key) if footer_key else None,
        repeat=diag.repeat,
    )
    if tpl is None:
        return rd
    rd.method = tpl.method
    args = tpl.recover(diag.body)
    rest: list[str] = []
    if args is None:
        # The box may hold further messages after its own (Utmess "I+" continuation).
        hit = tpl.match_at(diag.body, 0)
        if hit is not None:
            end, args = hit
            rest = diag.body[end:].lstrip("\n").split("\n")
    if args is None:
        # A run with our gettext catalog (DEBUT(LANG='EN'), ADR-004) printed the English.
        args = tpl.recover_en(diag.body)
        if args is None:
            hit = tpl.match_at_en(diag.body, 0)
            if hit is not None:
                end, args = hit
                rest = diag.body[end:].lstrip("\n").split("\n")
        rd.already_english = args is not None
    if args is None:
        rd.status = "no-args"
        return rd
    rd.args = args
    en = _fill(tpl, args, catalog)
    rd.status = "english" if en is not None else "untranslated"
    if rest and rd.already_english:
        # Continuation messages were printed in English too: keep them as printed.
        for line in rest:
            if line.strip():
                rd.extra.append(
                    {"message_id": None, "status": "kept", "args": {}, "en": line, "fr": line}
                )
    elif rest:
        for seg in match_lines(rest, catalog, family=diag.family):
            if seg.status == "blank":
                continue
            fr = "\n".join(rest[seg.first : seg.last + 1])
            rd.extra.append(
                {
                    "message_id": seg.message_id,
                    "status": seg.status if seg.message_id else "verbatim",
                    "args": seg.args,
                    "en": seg.en,
                    "fr": fr,
                }
            )
        if any(e["en"] is None for e in rd.extra):
            rd.status = "partial" if en is not None else rd.status
    rd.en = en
    return rd


# -- text layout ----------------------------------------------------------------------------


def _wrap(text: str, width: int) -> list[str]:
    """Break lines longer than ``width`` at spaces, keeping each line's indentation."""
    out: list[str] = []
    for line in text.split("\n"):
        if len(line) <= width:
            out.append(line.rstrip())
            continue
        indent = line[: len(line) - len(line.lstrip())]
        out.extend(
            textwrap.wrap(
                line,
                width,
                subsequent_indent=indent,
                break_long_words=False,
                break_on_hyphens=False,
            )
        )
    return out


def _box(lines: list[str]) -> list[str]:
    """``Utilities/strfunc.py`` ``textbox`` with ``maxlen=100``."""
    inner = []
    for line in lines:
        inner.extend(_wrap(line, BOX_TEXT))
    head = " ╔" + "=" * (BOX_TEXT + 2) + "╗"
    foot = " ╚" + "=" * (BOX_TEXT + 2) + "╝"
    return [head, *[f" ║ {line:<{BOX_TEXT}} ║" for line in inner], foot]


def _box_text(rd: RenderedDiagnostic) -> list[str]:
    header = f"<{rd.severity}> <{rd.message_id}>" if rd.message_id else f"<{rd.severity}>"
    body: list[str] = [header, ""]
    if rd.en is not None:
        body.append(rd.en)
        for e in rd.extra:
            body.append(e["en"] if e["en"] is not None else e["fr"])
    else:
        body.append(rd.fr)
        reason = {
            "untranslated": "this message has no English translation yet",
            "unknown-id": "this message ID is not in en/messages",
            "no-args": "the text does not match the message's French template",
        }.get(rd.status, rd.status)
        body.extend(["", f"[French text as printed: {reason}.]"])
    if rd.footer_en:
        body.extend(["", rd.footer_en])
    return _box("\n".join(body).split("\n"))


def _segment_text(seg: Segment, lines: list[str]) -> list[str]:
    if seg.en is None:
        return lines[seg.first : seg.last + 1]
    if seg.centered:
        return [
            f"{line.strip():^{MAXLENGTH}}".rstrip() if line.strip() else ""
            for line in seg.en.split("\n")
        ]
    # Keep the indentation the solver printed the first line with.
    first = lines[seg.first]
    indent = first[: len(first) - len(first.lstrip())]
    return _wrap(
        "\n".join(indent + line if line else line for line in seg.en.split("\n")), MAXLENGTH
    )


# -- whole log ------------------------------------------------------------------------------


@dataclass
class EnglishEvent:
    event: Event
    segments: list[Segment] = field(default_factory=list)
    diagnostic: RenderedDiagnostic | None = None

    def lines(self) -> list[str]:
        if self.diagnostic is not None:
            return _box_text(self.diagnostic)
        if not self.segments:
            return list(self.event.lines)
        out: list[str] = []
        for seg in self.segments:
            out.extend(_segment_text(seg, self.event.lines))
        return out


@dataclass
class EnglishLog:
    log: ParsedLog
    events: list[EnglishEvent]
    classification: Classification
    upstream: str | None = None

    @property
    def diagnostics(self) -> list[RenderedDiagnostic]:
        return [e.diagnostic for e in self.events if e.diagnostic is not None]

    def coverage(self) -> dict[str, Any]:
        diags = [d for d in self.diagnostics if not d.repeat]
        seg_status: dict[str, int] = {}
        verbatim_lines = 0
        ids: dict[str, str] = {}
        for ev in self.events:
            for seg in ev.segments:
                n = seg.last - seg.first + 1
                seg_status[seg.status] = seg_status.get(seg.status, 0) + n
                if seg.status == "verbatim":
                    verbatim_lines += n
                if seg.message_id:
                    ids[seg.message_id] = seg.status
        for d in diags:
            if d.message_id:
                ids[d.message_id] = d.status
        return {
            "diagnostics": len(diags),
            "diagnostics_english": sum(d.status == "english" for d in diags),
            "diagnostics_not_english": sorted(
                {d.message_id or d.severity for d in diags if d.status != "english"}
            ),
            "text_lines": seg_status,
            "messages": dict(sorted(ids.items())),
            "untranslated_messages": sorted(i for i, s in ids.items() if s != "english"),
        }

    def problems(self) -> list[dict[str, Any]]:
        """What stopped the run, in English, with where it happened in the command file."""
        stages = {s["number"]: s for s in self.log.stages()}
        out: list[dict[str, Any]] = []
        for d in self.diagnostics:
            if d.repeat or d.severity in ("I", "INFO", "A"):
                continue
            stage = stages.get(d.stage) if d.stage else None
            out.append(
                {
                    "kind": "diagnostic",
                    "severity": d.severity_en,
                    "message_id": d.message_id,
                    "command": stage.get("command") if stage else None,
                    "concept": stage.get("concept") if stage else None,
                    "comm_line": stage.get("comm_line") if stage else None,
                    "log_line": d.start,
                    "message": (d.en if d.en is not None else d.fr).strip(),
                    "english": d.en is not None,
                    "headline": _headline(d, stage),
                }
            )
        if not out:
            exc = self.log.summary()["exception"]
            if exc and self.classification.failed:
                where = (
                    f" at line {exc['comm_line']} of the command file" if exc["comm_line"] else ""
                )
                out.append(
                    {
                        "kind": "exception",
                        "severity": "error",
                        "message_id": None,
                        "command": None,
                        "concept": None,
                        "comm_line": exc["comm_line"],
                        "log_line": None,
                        "message": f"{exc['type']}: {exc['message']}".rstrip(": "),
                        "english": True,
                        "headline": f"Python {exc['type']}{where}: {exc['message']}",
                    }
                )
        return out

    def to_dict(self) -> dict[str, Any]:
        summary = self.log.summary()
        return {
            "schema_version": SCHEMA_VERSION,
            "_generated_from": {
                "renderer": RENDERER,
                "renderer_version": RENDERER_VERSION,
                "messages_upstream": self.upstream,
                "log": self.log.path,
            },
            "language": "en",
            "summary": {
                "diagnostic_job": summary["diagnostic_job"],
                "exit_code": summary["exit_code"],
                "closed_normally": summary["closed_normally"],
                "warnings": summary["alarms"],
                "ignored_warnings": summary["ignored_alarms"],
                "errors": summary["errors"],
                "test_resu": summary["test_resu"],
                "total_elapsed_s": summary["total_elapsed_s"],
            },
            "classification": self.classification.to_dict(),
            "problems": self.problems(),
            "coverage": self.coverage(),
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "messages": [
                {
                    "log_lines": [ev.event.start + s.first, ev.event.start + s.last],
                    "message_id": s.message_id,
                    "status": s.status,
                    "args": s.args,
                    "en": s.en,
                }
                for ev in self.events
                for s in ev.segments
                if s.message_id
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"

    def to_text(self) -> str:
        name = Path(self.log.path).name if self.log.path else "the log"
        out = [
            f"# English rendering of {name} by codeaster-en (caen mess translate). "
            "Command and keyword",
            "# names stay French: they are the solver's API. Lines without a translation are "
            "printed as the solver wrote them.",
        ]
        for ev in self.events:
            out.extend(ev.lines())
        return "\n".join(out) + "\n"


def _headline(d: RenderedDiagnostic, stage: dict[str, Any] | None) -> str:
    where = ""
    if stage and stage.get("command"):
        where = f"{stage['command']}"
        if stage.get("comm_line"):
            where += f" (command file line {stage['comm_line']})"
        where += " failed: "
    text = d.en if d.en is not None else d.fr
    first = next((p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()), "")
    first = _RE_WS.sub(" ", first).strip()
    tag = f"{d.severity_en} {d.message_id}" if d.message_id else d.severity_en
    return f"{where}{first} [{tag}]"


def _stage_eligible(ev: Stage) -> list[bool]:
    """Only the ``#`` lines of a stage are solver messages; the rest is the command echo."""
    return [line.startswith("#") for line in ev.lines]


def render_event(ev: Event, catalog: MessageCatalog) -> EnglishEvent:
    """English form of one event; with :func:`codeaster_en.mess.stream` this renders a log
    while the solver is still writing it."""
    if isinstance(ev, Diagnostic):
        return EnglishEvent(ev, diagnostic=render_diagnostic(ev, catalog))
    if ev.kind in _MATCHED_KINDS:
        eligible = _stage_eligible(ev) if isinstance(ev, Stage) else None
        return EnglishEvent(ev, match_lines(ev.lines, catalog, eligible))
    return EnglishEvent(ev)


def translate(
    log: ParsedLog,
    catalog: MessageCatalog | None = None,
    exit_code: int | None = None,
) -> EnglishLog:
    """Render a whole parsed log in English (``catalog`` defaults to the overlay's
    ``en/messages``; ``exit_code`` overrides the one in the log for the classification)."""
    catalog = catalog or MessageCatalog()
    out = [render_event(ev, catalog) for ev in log.events]
    return EnglishLog(log, out, classify(log, exit_code), catalog.upstream)
