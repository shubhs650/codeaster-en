"""``caen extract astest-index``: test cases → ``en/astest-index.json``.

A test case is one ``upstream/astest/<name>.export`` file. Its ``F comm`` lines name the
command files the case runs, in order (``.comm``, ``.com1``…, or a ``.py`` script that does
``from code_aster.Commands import *``). Every command file is plain Python, so it is parsed with
:mod:`ast` and each call ``NAME(...)`` whose ``NAME`` is a known command is recorded with its
line. The catalog itself offers no parser for command files: running one needs the built
solver. If a file does not parse, a regular expression over the source is used instead and the
file is marked ``"parse": "regex"`` (no file needs it in 17.4.26).

Known commands are:

- every catalog command, i.e. every ``en/commands/<CMD>.json`` written by ``caen extract
  catalog`` (re-run this extractor after that one);
- names that ``code_aster/CodeCommands/__init__.py`` exports but the catalog does not define
  (``POURSUITE``, which runs ``DEBUT``'s catalog: ``CodeCommands/debut.py``);
- ``NAME = UserMacro("NAME", …)`` definitions anywhere under ``code_aster/`` that are not in
  the catalog (``DEFI_CONT``, ``CALC_SPEC``…), which test cases import by hand.

Calls through an attribute (``table.EXTR_TABLE()``) are methods, not commands, and are not
counted. Python modules that a command file imports are not followed.

The ``.export`` metadata is kept: ``P`` parameters (``time_limit``, ``memory_limit``,
``ncpus``, ``mpi_nbcpu``, ``testlist``…), ``A`` arguments and every ``F``/``R`` file line.
Output layout: ``docs/schemas/astest-index.schema.json``.
"""

from __future__ import annotations

import ast
import json
import re
import warnings
from collections import Counter
from pathlib import Path
from typing import Any

from codeaster_en.extract.catalog import upstream_provenance

EXTRACTOR = "codeaster_en.extract.astest"
# Bump when the output layout or content changes (see catalog.EXTRACTOR_VERSION).
EXTRACTOR_VERSION = "1"
SCHEMA_VERSION = 1

ASTEST_RELDIR = Path("astest")
CODE_ASTER_RELDIR = Path("code_aster")
CODE_COMMANDS_INIT = CODE_ASTER_RELDIR / "CodeCommands" / "__init__.py"
INDEX_RELPATH = Path("en/astest-index.json")

# Exports of CodeCommands/__init__.py that are not commands.
NOT_COMMANDS = frozenset({"CO", "VARIABLE", "define_operators"})
USER_MACRO = re.compile(r'^([A-Z][A-Z0-9_]*)\s*=\s*UserMacro\(\s*"\1"', re.MULTILINE)
CALL = re.compile(r"(?<![\w.])([A-Z][A-Z0-9_]*)\s*\(")
LIST_PARAMS = frozenset({"testlist"})


def known_commands(upstream: Path, catalog_dir: Path) -> dict[str, dict[str, str]]:
    """``{NAME: {"source": "catalog" | "code_commands" | "user_macro", ...}}``."""
    found: dict[str, dict[str, str]] = {
        p.stem: {"source": "catalog"} for p in sorted(catalog_dir.glob("*.json"))
    }
    if not found:
        raise FileNotFoundError(f"no command files in {catalog_dir} (run `caen extract catalog`)")

    init = upstream / CODE_COMMANDS_INIT
    for node in ast.parse(init.read_text(encoding="utf-8")).body:
        if not isinstance(node, ast.ImportFrom):
            continue
        for alias in node.names:
            name = alias.asname or alias.name
            if name in found or name in NOT_COMMANDS or not name.isupper():
                continue
            module = (node.module or "").replace(".", "/")
            defined = (init.parent / f"{module}.py").relative_to(upstream).as_posix()
            found[name] = {"source": "code_commands", "defined_in": defined}

    for path in sorted((upstream / CODE_ASTER_RELDIR).rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in USER_MACRO.finditer(text):
            name = match.group(1)
            if name not in found:
                line = text.count("\n", 0, match.start()) + 1
                rel = path.relative_to(upstream).as_posix()
                found[name] = {"source": "user_macro", "defined_in": f"{rel}:{line}"}
    return dict(sorted(found.items()))


def _number(value: str) -> int | float | str:
    for kind in (int, float):
        try:
            return kind(value)
        except ValueError:
            pass
    return value


def parse_export(path: Path) -> dict[str, Any]:
    """Parameters, arguments and file lines of one ``.export`` file."""
    params: dict[str, Any] = {}
    args: list[str] = []
    files: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = raw.split()
        if not fields or fields[0].startswith("#"):
            continue
        kind, rest = fields[0], fields[1:]
        if kind == "P" and rest:
            key, values = rest[0], rest[1:]
            if key in LIST_PARAMS:
                params[key] = values
            elif len(values) == 1:
                params[key] = _number(values[0])
            else:
                params[key] = " ".join(values) if values else True
        elif kind == "A" and rest:
            args.extend(rest)
        elif kind in ("F", "R") and len(rest) >= 3:
            entry: dict[str, Any] = {
                "kind": kind,
                "type": rest[0],
                "path": rest[1],
                "mode": rest[2],
            }
            if len(rest) >= 4:
                entry["unit"] = _number(rest[3])
            files.append(entry)
    return {"params": params, "args": args, "files": files}


def _calls_ast(source: bytes, known: set[str]) -> dict[str, list[int]] | None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    calls: dict[str, list[int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in known:
                calls.setdefault(node.func.id, []).append(node.lineno)
    return calls


def _calls_regex(source: bytes, known: set[str]) -> dict[str, list[int]]:
    calls: dict[str, list[int]] = {}
    text = source.decode("utf-8", errors="replace")
    for lineno, line in enumerate(text.splitlines(), start=1):
        code = line.split("#", 1)[0]
        for match in CALL.finditer(code):
            if match.group(1) in known:
                calls.setdefault(match.group(1), []).append(lineno)
    return calls


def scan_command_file(path: Path, known: set[str]) -> dict[str, Any]:
    """``{"parse": "ast" | "regex", "calls": {CMD: [line, ...]}}`` for one command file."""
    source = path.read_bytes()
    calls = _calls_ast(source, known)
    parse = "ast"
    if calls is None:
        calls, parse = _calls_regex(source, known), "regex"
    return {
        "parse": parse,
        "calls": {name: sorted(lines) for name, lines in sorted(calls.items())},
    }


def extract(upstream: Path, catalog_dir: Path) -> dict[str, Any]:
    """The whole index, without provenance."""
    astest = upstream / ASTEST_RELDIR
    if not astest.is_dir():
        raise FileNotFoundError(f"{astest} not found (run `git submodule update --init`)")
    commands = known_commands(upstream, catalog_dir)
    known = set(commands)
    scanned: dict[str, dict[str, Any]] = {}
    testcases: dict[str, dict[str, Any]] = {}
    for export in sorted(astest.glob("*.export")):
        meta = parse_export(export)
        command_files = []
        used: set[str] = set()
        for entry in meta["files"]:
            if entry["kind"] != "F" or entry["type"] != "comm":
                continue
            rel = entry["path"]
            target = astest / rel
            if not target.is_file():
                command_files.append({"path": rel, "missing": True})
                continue
            if rel not in scanned:
                scanned[rel] = scan_command_file(target, known)
            command_files.append({"path": rel, **scanned[rel]})
            used.update(scanned[rel]["calls"])
        testcases[export.stem] = {
            "export": (ASTEST_RELDIR / export.name).as_posix(),
            "commands": sorted(used),
            "command_files": command_files,
            "params": meta["params"],
            "parallel": "parallel" in meta["params"].get("testlist", []),
            **({"args": meta["args"]} if meta["args"] else {}),
            "files": meta["files"],
        }

    by_command: dict[str, list[str]] = {name: [] for name in commands}
    calls: Counter[str] = Counter()
    for name, case in testcases.items():
        for command in case["commands"]:
            by_command[command].append(name)
        for cfile in case["command_files"]:
            for command, lines in cfile.get("calls", {}).items():
                calls[command] += len(lines)
    index_commands = {
        name: {**info, "calls": calls[name], "testcases": by_command[name]}
        for name, info in commands.items()
    }
    parses = Counter(f["parse"] for f in scanned.values())
    summary = {
        "testcases": len(testcases),
        "command_files": len(scanned),
        "parse": dict(sorted(parses.items())),
        "known_commands": len(commands),
        "commands_used": sum(1 for v in by_command.values() if v),
        "parallel_testcases": sum(1 for c in testcases.values() if c["parallel"]),
    }
    return {"summary": summary, "commands": index_commands, "testcases": testcases}


def with_provenance(doc: dict, provenance: dict[str, str | None]) -> dict:
    header = {
        "_generated_from": {
            **provenance,
            "dir": ASTEST_RELDIR.as_posix(),
            "extractor": EXTRACTOR,
            "extractor_version": EXTRACTOR_VERSION,
        },
        "schema_version": SCHEMA_VERSION,
    }
    return {**header, **doc}


# Top-level maps written one entry per line, so that an upstream bump diffs per test case.
ONE_LINE_ENTRIES = ("commands", "testcases")


def render(doc: dict) -> str:
    """Indented JSON, except that each command and test case entry is on one line."""
    parts = []
    for key, value in doc.items():
        if key in ONE_LINE_ENTRIES:
            entries = [
                f"  {json.dumps(name)}: {json.dumps(entry, ensure_ascii=False)}"
                for name, entry in value.items()
            ]
            body = "{\n" + ",\n".join(entries) + "\n }" if entries else "{}"
        else:
            body = json.dumps(value, ensure_ascii=False, indent=1).replace("\n", "\n ")
        parts.append(f" {json.dumps(key)}: {body}")
    return "{\n" + ",\n".join(parts) + "\n}\n"


def write(repo: Path, out: Path, catalog_dir: Path | None = None) -> dict[str, Any]:
    """Build the index from ``repo/upstream`` and write it to ``out``; return the document."""
    doc = with_provenance(
        extract(repo / "upstream", catalog_dir or repo / "en" / "commands"),
        upstream_provenance(repo),
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(doc), encoding="utf-8")
    return doc
