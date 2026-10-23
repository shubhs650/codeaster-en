"""``caen extract messages``: message catalogs → ``en/messages/<FAMILY>.en.json``.

Each ``upstream/code_aster/Messages/<family>.py`` assigns one literal dict ``cata_msg``. The
package cannot be imported without the solver (its ``__init__`` imports ``Utmess``, which
imports ``aster_core``; docs/INVENTORY.md §2), so the files are parsed with :mod:`ast`.

Value forms found in 17.4.26 (``Utmess.get_message`` reads both the plain and the dict form):

- ``N: _("…")`` — the usual form;
- ``N: {"message": _("…"), "flags": "DECORATED"}`` — ``flags`` is recorded verbatim;
- ``N: "…"`` — not wrapped in ``_()``: recorded with ``"gettext": false``;
- ``N: _(f"…{name}…")`` — an f-string over module-level string constants (``post0.py``):
  the constants are substituted, and the message is recorded with ``"gettext": false`` and
  ``"fstring_names"``, since xgettext cannot extract it.

The family is the file name in upper case (``mecanonline10.py`` → ``MECANONLINE10``); a message
ID is ``<FAMILY>_<N>``. ``Utmess.decode_idmess`` only accepts ``0 < N < 100``, so messages
numbered 100 or more are kept but marked ``"reachable": false``.

Re-extraction keeps the translation fields of an existing file (:data:`TRANSLATION_KEYS`). If
the French text of a translated message changed upstream, the translation is kept and the
message is marked ``"stale": true`` (TRANSLATION-GUIDE.md §3.6). Messages that disappeared
upstream are dropped. Output layout: ``docs/schemas/messages.schema.json``.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from codeaster_en import placeholders
from codeaster_en.extract.catalog import upstream_provenance

EXTRACTOR = "codeaster_en.extract.messages"
# Bump when the output layout or content changes (see catalog.EXTRACTOR_VERSION).
EXTRACTOR_VERSION = "1"
SCHEMA_VERSION = 1

MESSAGES_RELDIR = Path("code_aster/Messages")
NOT_FAMILIES = frozenset({"__init__.py", "Utmess.py"})
SUFFIX = ".en.json"

# Fields owned by translators and the translate tool; the extractor carries them over.
TRANSLATION_KEYS = (
    "en",
    "method",
    "severity_hint",
    "translation_source",
    "reviewed_by",
    "reviewed_on",
    "note",
    "stale",
)
MAX_REACHABLE = 99  # Utmess.decode_idmess: assert 0 < num < 100


class MessageFileError(ValueError):
    """A message file has a shape the extractor does not understand."""


def family_of(path: Path) -> str:
    return path.stem.upper()


def family_files(upstream: Path) -> list[Path]:
    directory = upstream / MESSAGES_RELDIR
    if not directory.is_dir():
        raise FileNotFoundError(f"{directory} not found (run `git submodule update --init`)")
    return sorted(p for p in directory.glob("*.py") if p.name not in NOT_FAMILIES)


def _module_strings(tree: ast.Module) -> dict[str, str]:
    """Module-level ``NAME = "constant"`` assignments, for f-string substitution."""
    found: dict[str, str] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            found[node.targets[0].id] = node.value.value
    return found


def _where(path: Path, node: ast.AST) -> str:
    return f"{path.name}:{getattr(node, 'lineno', '?')}"


def _text(node: ast.expr, path: Path, consts: dict[str, str]) -> tuple[str, dict[str, Any]]:
    """French text of one message value and the extra fields its form implies."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value, {"gettext": False}
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_"
        and len(node.args) == 1
        and not node.keywords
    ):
        raise MessageFileError(f'{_where(path, node)}: expected _("...") or a string')
    arg = node.args[0]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value, {}
    if isinstance(arg, ast.JoinedStr):
        parts: list[str] = []
        names: list[str] = []
        for value in arg.values:
            if isinstance(value, ast.Constant):
                parts.append(value.value)
            elif (
                isinstance(value, ast.FormattedValue)
                and isinstance(value.value, ast.Name)
                and value.value.id in consts
                and value.conversion == -1
                and value.format_spec is None
            ):
                parts.append(consts[value.value.id])
                names.append(value.value.id)
            else:
                raise MessageFileError(
                    f"{_where(path, value)}: f-string field is not a module-level string"
                )
        return "".join(parts), {"gettext": False, "fstring_names": names}
    raise MessageFileError(f"{_where(path, arg)}: _() argument is not a string")


def _message(node: ast.expr, path: Path, consts: dict[str, str]) -> tuple[str, dict[str, Any]]:
    if isinstance(node, ast.Dict):
        fields: dict[str, ast.expr] = {}
        for key, value in zip(node.keys, node.values, strict=True):
            if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                raise MessageFileError(f"{_where(path, node)}: dict message with a non-string key")
            fields[key.value] = value
        unknown = sorted(set(fields) - {"message", "flags"})
        if "message" not in fields or unknown:
            raise MessageFileError(
                f"{_where(path, node)}: dict message needs 'message' and only 'flags' besides "
                f"(found {sorted(fields)})"
            )
        text, extra = _text(fields["message"], path, consts)
        if "flags" in fields:
            flags = fields["flags"]
            if not (isinstance(flags, ast.Constant) and isinstance(flags.value, str)):
                raise MessageFileError(f"{_where(path, flags)}: 'flags' is not a string")
            extra["flags"] = flags.value
        return text, extra
    return _text(node, path, consts)


def parse_file(path: Path) -> dict[int, dict[str, Any]]:
    """``{N: {"fr", "line", ...extra}}`` for one family file, in file order."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    consts = _module_strings(tree)
    tables = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "cata_msg" for t in node.targets)
    ]
    if len(tables) != 1 or not isinstance(tables[0].value, ast.Dict):
        raise MessageFileError(f"{path.name}: expected exactly one literal `cata_msg = {{...}}`")
    table = tables[0].value
    messages: dict[int, dict[str, Any]] = {}
    for key, value in zip(table.keys, table.values, strict=True):
        if not (isinstance(key, ast.Constant) and type(key.value) is int):
            raise MessageFileError(f"{_where(path, value)}: message number is not an int")
        if key.value in messages:
            raise MessageFileError(f"{_where(path, key)}: duplicate message {key.value}")
        text, extra = _message(value, path, consts)
        messages[key.value] = {"fr": text, "line": key.lineno, **extra}
    return messages


def _entry(family: str, number: int, raw: dict[str, Any]) -> dict[str, Any]:
    parsed = placeholders.parse(raw["fr"])
    if parsed.errors:
        raise MessageFileError(f"{family}_{number}: {'; '.join(parsed.errors)}")
    entry: dict[str, Any] = {
        "id": f"{family}_{number}",
        "fr": raw["fr"],
        "placeholders": parsed.tokens,
        "source": {"line": raw["line"]},
    }
    for optional in ("flags", "gettext", "fstring_names"):
        if optional in raw:
            entry[optional] = raw[optional]
    if not 0 < number <= MAX_REACHABLE:
        entry["reachable"] = False
    entry["en"] = None
    return entry


def extract_family(path: Path, upstream: Path) -> dict[str, Any]:
    family = family_of(path)
    raw = parse_file(path)
    return {
        "family": family,
        "source": {"file": path.relative_to(upstream).as_posix()},
        "messages": {str(n): _entry(family, n, raw[n]) for n in sorted(raw)},
    }


def merge_translations(new: dict[str, Any], old: dict[str, Any] | None) -> dict[str, Any]:
    """Carry translation fields from ``old`` (a previous output file) into ``new``."""
    if not old:
        return new
    previous = old.get("messages", {})
    for number, entry in new["messages"].items():
        before = previous.get(number)
        if not before:
            continue
        for key in TRANSLATION_KEYS:
            if before.get(key) is not None:
                entry[key] = before[key]
        if entry.get("en") is not None and before.get("fr") != entry["fr"]:
            entry["stale"] = True
    return new


def with_provenance(doc: dict, provenance: dict[str, str | None]) -> dict:
    header = {
        "_generated_from": {
            **provenance,
            "file": doc["source"]["file"],
            "extractor": EXTRACTOR,
            "extractor_version": EXTRACTOR_VERSION,
        },
        "schema_version": SCHEMA_VERSION,
    }
    return {**header, **doc}


def render(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def extract(upstream: Path) -> dict[str, dict]:
    """``{FAMILY: document}`` for every message file, without provenance."""
    return {family_of(p): extract_family(p, upstream) for p in family_files(upstream)}


def write(repo: Path, outdir: Path, only: list[str] | None = None) -> list[Path]:
    """Extract every family (or ``only`` those) and write ``outdir/<FAMILY>.en.json``."""
    upstream = repo / "upstream"
    files = {family_of(p): p for p in family_files(upstream)}
    if only:
        wanted = [name.upper() for name in only]
        missing = sorted(set(wanted) - set(files))
        if missing:
            raise KeyError(f"no message family: {', '.join(missing)}")
        files = {name: files[name] for name in wanted}
    provenance = upstream_provenance(repo)
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    for family, path in files.items():
        target = outdir / f"{family}{SUFFIX}"
        old = json.loads(target.read_text(encoding="utf-8")) if target.is_file() else None
        doc = merge_translations(extract_family(path, upstream), old)
        target.write_text(render(with_provenance(doc, provenance)), encoding="utf-8")
        written.append(target)
    return written
