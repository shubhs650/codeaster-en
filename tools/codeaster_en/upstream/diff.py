"""Compare two extractions of upstream (commands and messages) and render the diff report.

Inputs are the documents the extractors write (``en/commands/<CMD>.json`` and
``en/messages/<FAMILY>.en.json``), keyed by command name and by family. Source lines are
ignored: they move on every upstream commit and say nothing about the API.

Keywords are compared by their user-visible path (``AFFE/GROUP_MA``; a bloc is
``AFFE/[b_name]``). One path can be defined several times, once per bloc that declares it
(2,216 such paths in 17.4.26), so each path holds the list of its definitions and two paths
differ when those lists differ as multisets.

Messages are compared by ID. A message whose French text changed is listed with whether it
had an English text; the message extractor (``merge_translations``) marks those ``stale``.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any

# Fields that do not describe the API: where the definition sits, and the tree structure
# (children are compared through their own paths).
_IGNORED = frozenset({"_generated_from", "schema_version", "source", "keywords", "name", "path"})
_WIDTH = 70


@dataclass
class KeywordChange:
    path: str
    kind: str
    changes: list[str]


@dataclass
class CommandChange:
    command: str
    fields: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[KeywordChange] = field(default_factory=list)


@dataclass
class CatalogDiff:
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[CommandChange] = field(default_factory=list)
    unchanged: int = 0


@dataclass
class MessageChange:
    id: str
    old_fr: str
    new_fr: str
    method: str | None  # method of the existing English, None if untranslated
    placeholders_changed: bool


@dataclass
class MessagesDiff:
    families_added: list[str] = field(default_factory=list)
    families_removed: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    removed: list[tuple[str, str | None]] = field(default_factory=list)  # (id, method)
    changed: list[MessageChange] = field(default_factory=list)
    unchanged: int = 0

    @property
    def stale(self) -> list[MessageChange]:
        return [c for c in self.changed if c.method is not None]


# --------------------------------------------------------------------------------------
# Catalog
# --------------------------------------------------------------------------------------


def _walk(entities: Iterable[dict]) -> Iterator[dict]:
    for ent in entities:
        yield ent
        yield from _walk(ent.get("keywords", []))


def _definition(entity: dict) -> dict:
    return {k: v for k, v in entity.items() if k not in _IGNORED}


def _canon(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def keyword_paths(doc: dict) -> dict[str, list[dict]]:
    """``{path: [definition, ...]}`` for every keyword and bloc of a command document."""
    paths: dict[str, list[dict]] = {}
    for ent in _walk(doc.get("keywords", [])):
        paths.setdefault(ent["path"], []).append(_definition(ent))
    return paths


def _short(value: Any) -> str:
    text = _canon(value)
    return text if len(text) <= _WIDTH else text[: _WIDTH - 1] + "…"


def field_changes(old: dict, new: dict) -> list[str]:
    """One line per field that differs, e.g. ``default: 1 → 2`` or ``into: +["X"] −["Y"]``."""
    lines = []
    for key in sorted(set(old) | set(new)):
        if key in _IGNORED:
            continue
        before, after = old.get(key), new.get(key)
        if _canon(before) == _canon(after):
            continue
        if key not in old:
            lines.append(f"{key}: added {_short(after)}")
        elif key not in new:
            lines.append(f"{key}: removed (was {_short(before)})")
        elif isinstance(before, list) and isinstance(after, list):
            gone = [x for x in before if _canon(x) not in {_canon(y) for y in after}]
            come = [x for x in after if _canon(x) not in {_canon(y) for y in before}]
            if gone or come:
                parts = ([f"+{_short(come)}"] if come else []) + (
                    [f"−{_short(gone)}"] if gone else []
                )
                lines.append(f"{key}: {' '.join(parts)}")
            else:
                lines.append(f"{key}: reordered")
        else:
            lines.append(f"{key}: {_short(before)} → {_short(after)}")
    return lines


def _keyword_change(path: str, old: list[dict], new: list[dict]) -> KeywordChange | None:
    common = Counter(_canon(d) for d in old) & Counter(_canon(d) for d in new)
    if sum(common.values()) == len(old) == len(new):
        return None
    left, right = list(old), list(new)
    for text, count in common.items():
        for side in (left, right):
            for _ in range(count):
                side.remove(next(d for d in side if _canon(d) == text))
    kind = (new or old)[0].get("kind", "?")
    changes: list[str] = []
    if len(old) != len(new):
        changes.append(f"definitions: {len(old)} → {len(new)}")
    lines = Counter(
        line
        for before, after in zip(left, right, strict=False)
        for line in field_changes(before, after)
    )
    changes += [line if n == 1 else f"{line} (in {n} definitions)" for line, n in lines.items()]
    return KeywordChange(path, kind, changes or ["definitions differ"])


def compare_command(name: str, old: dict, new: dict) -> CommandChange | None:
    change = CommandChange(name, fields=field_changes(_definition(old), _definition(new)))
    before, after = keyword_paths(old), keyword_paths(new)
    change.added = sorted(set(after) - set(before))
    change.removed = sorted(set(before) - set(after))
    for path in sorted(set(before) & set(after)):
        kw = _keyword_change(path, before[path], after[path])
        if kw is not None:
            change.changed.append(kw)
    if change.fields or change.added or change.removed or change.changed:
        return change
    return None


def compare_catalog(old: dict[str, dict], new: dict[str, dict]) -> CatalogDiff:
    diff = CatalogDiff(added=sorted(set(new) - set(old)), removed=sorted(set(old) - set(new)))
    for name in sorted(set(old) & set(new)):
        change = compare_command(name, old[name], new[name])
        if change is None:
            diff.unchanged += 1
        else:
            diff.changed.append(change)
    return diff


# --------------------------------------------------------------------------------------
# Messages
# --------------------------------------------------------------------------------------


def _messages(docs: dict[str, dict]) -> dict[str, dict]:
    return {m["id"]: m for doc in docs.values() for m in doc.get("messages", {}).values()}


def _method(msg: dict) -> str | None:
    return (msg.get("method") or "unknown") if msg.get("en") is not None else None


def _id_key(ident: str) -> tuple[str, int]:
    family, _, number = ident.rpartition("_")
    return family, int(number) if number.isdigit() else 0


def compare_messages(old: dict[str, dict], new: dict[str, dict]) -> MessagesDiff:
    """``old`` and ``new`` are ``{FAMILY: document}``; ``old`` carries the translations."""
    diff = MessagesDiff(
        families_added=sorted(set(new) - set(old)),
        families_removed=sorted(set(old) - set(new)),
    )
    before, after = _messages(old), _messages(new)
    diff.added = sorted(set(after) - set(before), key=_id_key)
    diff.removed = [(i, _method(before[i])) for i in sorted(set(before) - set(after), key=_id_key)]
    for ident in sorted(set(before) & set(after), key=_id_key):
        a, b = before[ident], after[ident]
        if a["fr"] == b["fr"]:
            diff.unchanged += 1
            continue
        diff.changed.append(
            MessageChange(
                ident,
                a["fr"],
                b["fr"],
                _method(a),
                a.get("placeholders") != b.get("placeholders"),
            )
        )
    return diff


# --------------------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------------------


@dataclass
class Report:
    old: dict[str, str | None]  # {"upstream": tag, "upstream_commit": sha}
    new: dict[str, str | None]
    catalog: CatalogDiff
    messages: MessagesDiff
    applied: bool
    date: str
    references: dict[str, str] = field(default_factory=dict)  # command → .md status
    glossary_orphans: list[tuple[str, str]] = field(default_factory=list)  # (fr, kind)
    notes: list[str] = field(default_factory=list)
    follow_up: list[str] = field(default_factory=list)


def _cell(text: str) -> str:
    """Text safe inside a Markdown table cell (one line, pipes escaped)."""
    flat = " ".join(text.split()).replace("|", "\\|")
    return flat if len(flat) <= 100 else flat[:99] + "…"


def changed_span(old: str, new: str, context: int = 30) -> tuple[str, str]:
    """The part of ``old`` and ``new`` that differs, with ``context`` characters around it."""
    start = 0
    while start < min(len(old), len(new)) and old[start] == new[start]:
        start += 1
    end = 0
    while end < min(len(old), len(new)) - start and old[-1 - end] == new[-1 - end]:
        end += 1
    lo = max(start - context, 0)

    def cut(text: str) -> str:
        hi = min(len(text) - end + context, len(text))
        return ("…" if lo else "") + text[lo:hi] + ("…" if hi < len(text) else "")

    return cut(old), cut(new)


def _code_list(items: Iterable[str]) -> str:
    return ", ".join(f"`{i}`" for i in items) or "none"


def _ref(prov: dict[str, str | None]) -> str:
    commit = prov.get("upstream_commit") or "unknown"
    return f"`{prov.get('upstream')}` (commit `{commit[:9]}`)"


def render(report: Report) -> str:
    cat, msg = report.catalog, report.messages
    old, new = report.old["upstream"], report.new["upstream"]
    mode = "applied" if report.applied else "dry run, the pin was not moved"
    out = [
        f"# Upstream diff {old} → {new}",
        "",
        f"Generated by `caen upstream bump` on {report.date} ({mode}). From {_ref(report.old)} "
        f'to {_ref(report.new)} in the upstream mirror. The "from" side is the extraction '
        'committed in `en/`; the "to" side is a fresh extraction of the new tag. Source line '
        "numbers are ignored.",
        "",
    ]
    for note in report.notes:
        out += [f"> {note}", ""]
    out += [
        "## Summary",
        "",
        "| Item | Added | Removed | Changed | Unchanged |",
        "|---|---:|---:|---:|---:|",
        f"| Commands | {len(cat.added)} | {len(cat.removed)} | {len(cat.changed)} | "
        f"{cat.unchanged} |",
        f"| Keywords (paths, in commands present on both sides) | "
        f"{sum(len(c.added) for c in cat.changed)} | {sum(len(c.removed) for c in cat.changed)} | "
        f"{sum(len(c.changed) for c in cat.changed)} | |",
        f"| Message families | {len(msg.families_added)} | {len(msg.families_removed)} | | |",
        f"| Messages | {len(msg.added)} | {len(msg.removed)} | {len(msg.changed)} | "
        f"{msg.unchanged} |",
        "",
        f"Translated messages whose French changed (marked `stale`): **{len(msg.stale)}**, of "
        f"which {sum(c.placeholders_changed for c in msg.stale)} changed placeholders (`caen "
        "validate` fails on those until the English is redone). Translated messages removed: "
        f"**{sum(1 for _, m in msg.removed if m)}**.",
        "",
        "## Commands",
        "",
        f"Added: {_code_list(cat.added)}.",
        "",
        f"Removed: {_code_list(cat.removed)}.",
        "",
    ]
    if cat.changed:
        out += ["### Changed commands", ""]
    for change in cat.changed:
        out += [f"#### {change.command}", ""]
        if change.fields:
            out += ["Command definition:", ""] + [f"- {_cell(f)}" for f in change.fields] + [""]
        if change.added:
            out += [f"Keywords added: {_code_list(change.added)}.", ""]
        if change.removed:
            out += [f"Keywords removed: {_code_list(change.removed)}.", ""]
        if change.changed:
            out += ["| Keyword | Kind | Change |", "|---|---|---|"]
            for kw in change.changed:
                out.append(
                    f"| `{kw.path}` | {kw.kind} | {'<br>'.join(_cell(c) for c in kw.changes)} |"
                )
            out.append("")
    out += [
        "## Messages",
        "",
        f"Families added: {_code_list(msg.families_added)}.",
        "",
        f"Families removed: {_code_list(msg.families_removed)}.",
        "",
        f"Messages added (no English yet): {_code_list(msg.added)}.",
        "",
    ]
    if msg.removed:
        out += ["### Removed messages", "", "| ID | English dropped |", "|---|---|"]
        out += [f"| `{i}` | {m or 'none'} |" for i, m in msg.removed] + [""]
    else:
        out += ["Messages removed: none.", ""]
    if msg.changed:
        out += [
            "### Messages whose French changed",
            "",
            "`stale` = the existing English was kept and marked `stale: true`; it needs a new "
            "translation (`caen translate messages` picks stale messages up).",
            "",
            "Only the part that differs is shown, with some context.",
            "",
            "| ID | English | Placeholders changed | Old French | New French |",
            "|---|---|---|---|---|",
        ]
        for c in msg.changed:
            english = f"stale ({c.method})" if c.method else "none"
            before, after = changed_span(c.old_fr, c.new_fr)
            out.append(
                f"| `{c.id}` | {english} | {'**yes**' if c.placeholders_changed else 'no'} | "
                f"{_cell(before)} | {_cell(after)} |"
            )
        out.append("")
    else:
        out += ["Messages whose French changed: none.", ""]
    out += ["## English artefacts to revisit", ""]
    if report.references:
        out += [
            "Command references (`en/commands/<CMD>.md`) whose command changed or was removed. "
            "Their front matter keeps the tag they were written against.",
            "",
            "| Command | Reference status | Change |",
            "|---|---|---|",
        ]
        removed = set(cat.removed)
        for name, status in sorted(report.references.items()):
            what = "removed upstream" if name in removed else "changed"
            out.append(f"| `{name}` | {status} | {what} |")
        out.append("")
    else:
        out += ["Command references: none affected.", ""]
    if report.glossary_orphans:
        out += [
            "Glossary entries whose French identifier no longer exists in the catalog:",
            "",
        ]
        out += [f"- `{fr}` ({kind})" for fr, kind in report.glossary_orphans] + [""]
    else:
        out += ["Glossary: no entry lost its command or keyword.", ""]
    if report.follow_up:
        out += ["## Follow-up", ""] + [f"- {item}" for item in report.follow_up] + [""]
    return "\n".join(out).rstrip("\n") + "\n"
