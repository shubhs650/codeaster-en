"""``caen extract catalog``: command catalogs → ``en/commands/<CMD>.json``.

The catalogs in ``upstream/code_aster/Cata/Commands/`` are Python modules written with the
``Syntax`` DSL (``OPER``, ``MACRO``, ``PROC``, ``SIMP``, ``FACT``, ``BLOC``). They import
without the solver (numpy only, docs/INVENTORY.md §1), so this extractor imports them rather
than walking the AST. The DSL objects do not record where they were written, so before the
import we wrap ``PartOfSyntax.__init__`` to note the calling file and line.

The import runs in a child interpreter (``python -B -m codeaster_en.extract.catalog <dir>``):
the source lines can only be captured if the catalogs are imported *after* the wrapper is in
place, and a process that already imported ``code_aster.Cata`` (pytest, for example) cannot
re-import them. The child also never writes bytecode under ``upstream/``, and runs with a
fixed ``PYTHONHASHSEED`` so that values upstream builds from sets come out in a stable order.

Output layout is documented in ``docs/schemas/command.schema.json``.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

EXTRACTOR = "codeaster_en.extract.catalog"
# Bump when the output layout or content changes, so the diff tool can tell extractor
# changes from upstream changes.
EXTRACTOR_VERSION = "1"
SCHEMA_VERSION = 1

COMMANDS_RELDIR = Path("code_aster/Cata/Commands")

# Catalog names of the rule classes (code_aster/Cata/Language/Syntax.py).
RULE_NAMES = {
    "AtLeastOne": "AU_MOINS_UN",
    "ExactlyOne": "UN_PARMI",
    "AtMostOne": "EXCLUS",
    "IfFirstAllPresent": "PRESENT_PRESENT",
    "OnlyFirstPresent": "PRESENT_ABSENT",
    "AllTogether": "ENSEMBLE",
    "NotEmpty": "NON_VIDE",
}

# Catalog constructors per object class (code_aster/Cata/Language/Syntax.py).
COMMAND_KINDS = {"Operator": "OPER", "Macro": "MACRO", "Procedure": "PROC", "Formule": "FORM"}

# Definition arguments the extractor maps to output fields. Anything else found in a
# definition is copied verbatim to ``other`` so nothing is silently dropped.
_COMMAND_KEYS = {
    "nom",
    "op",
    "sd_prod",
    "fr",
    "reentrant",
    "regles",
    "translation",
    "compat_syntax",
    "docu",
    "repetable",
}
_SIMPLE_KEYS = {
    "statut",
    "typ",
    "into",
    "defaut",
    "min",
    "max",
    "val_min",
    "val_max",
    "val_min_included",
    "val_max_included",
    "validators",
    "fr",
    "inout",
    "enum",
}
_FACTOR_KEYS = {"statut", "min", "max", "regles", "fr"}
_BLOC_KEYS = {"condition", "regles", "fr"}


# --------------------------------------------------------------------------------------
# Child side: import the catalogs and serialise them.
# --------------------------------------------------------------------------------------


def _value(value: Any) -> Any:
    """Turn a catalog value into JSON."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else {"float": repr(value)}
    if isinstance(value, complex):
        return {"complex": [_value(value.real), _value(value.imag)]}
    if isinstance(value, (list, tuple)):
        return [_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _value(val) for key, val in value.items()}
    if isinstance(value, type):
        return value.__name__
    return repr(value)


def _types(typ: Any) -> list[str]:
    items = typ if isinstance(typ, (list, tuple)) else (typ,)
    return [item if isinstance(item, str) else _value(item) for item in items]


def _validators(value: Any) -> list[dict]:
    from code_aster.Cata.Language.Validators import Validator

    items = value if isinstance(value, (list, tuple)) else (value,)
    out = []
    for item in items:
        args = [
            _validators(arg)[0] if isinstance(arg, Validator) else _value(arg)
            for arg in getattr(item, "args", ())
        ]
        out.append({"name": type(item).__name__, "args": args})
    return out


def _rules(rules: Any) -> list[dict]:
    out = []
    for rule in rules:
        cls = type(rule).__name__
        entry: dict[str, Any] = {
            "rule": RULE_NAMES.get(cls, cls),
            "keywords": list(rule.ruleArgs),
        }
        defaults = getattr(rule, "ruleKwargs", None)
        if defaults:
            entry["defaults"] = {key: _value(val) for key, val in defaults.items()}
        out.append(entry)
    return out


def _other(definition: dict, known: set[str]) -> dict:
    from code_aster.Cata.Language.SyntaxObjects import PartOfSyntax

    return {
        key: _value(val)
        for key, val in definition.items()
        if key not in known and not isinstance(val, PartOfSyntax)
    }


def _entities(obj: Any, prefix: str, sources: dict[int, tuple[str, int]]) -> list[dict]:
    from code_aster.Cata.Language.SyntaxObjects import Bloc, FactorKeyword, SimpleKeyword

    out = []
    for name, ent in obj.definition.items():
        if not isinstance(ent, (SimpleKeyword, FactorKeyword, Bloc)):
            continue
        definition = ent.definition
        node: dict[str, Any] = {"name": name}
        if isinstance(ent, SimpleKeyword):
            node["kind"] = "simple"
            node["path"] = f"{prefix}{name}"
            node["status"] = definition.get("statut", "f")
            node["type"] = _types(definition.get("typ"))
            for key in ("min", "max", "val_min", "val_max", "val_min_included", "val_max_included"):
                if key in definition:
                    node[key] = _value(definition[key])
            if "defaut" in definition:
                node["default"] = _value(definition["defaut"])
            if "into" in definition:
                node["into"] = _value(definition["into"])
            if "enum" in definition:
                node["enum"] = _value(definition["enum"])
            if "inout" in definition:
                node["inout"] = definition["inout"]
            if "validators" in definition:
                node["validators"] = _validators(definition["validators"])
            known = _SIMPLE_KEYS
        elif isinstance(ent, FactorKeyword):
            node["kind"] = "factor"
            node["path"] = f"{prefix}{name}"
            node["status"] = definition.get("statut", "f")
            for key in ("min", "max"):
                if key in definition:
                    node[key] = _value(definition[key])
            known = _FACTOR_KEYS
        else:
            node["kind"] = "bloc"
            node["path"] = f"{prefix}[{name}]"
            node["condition"] = definition.get("condition")
            known = _BLOC_KEYS
        node["fr"] = definition.get("fr") or None
        if ent.rules:
            node["rules"] = _rules(ent.rules)
        other = _other(definition, known)
        if other:
            node["other"] = other
        node["source"] = _source(ent, sources)
        if not isinstance(ent, SimpleKeyword):
            # Keywords inside a bloc are written at the bloc's parent level by the user,
            # so a bloc does not add a path segment; a factor keyword does.
            child_prefix = prefix if isinstance(ent, Bloc) else f"{prefix}{name}/"
            node["keywords"] = _entities(ent, child_prefix, sources)
        out.append(node)
    return out


def _source(obj: Any, sources: dict[int, tuple[str, int]]) -> dict | None:
    found = sources.get(id(obj))
    if found is None:
        return None
    return {"file": found[0], "line": found[1]}


def _result_types(cmd: Any) -> tuple[list[str] | None, bool]:
    """(possible result types, whether the type depends on the keywords given)."""
    import types

    sd_prod = cmd.definition.get("sd_prod")
    if sd_prod is None:
        return [], False
    if not isinstance(sd_prod, types.FunctionType):
        return [_value(sd_prod)], False
    try:
        found = cmd.get_all_types()
    except Exception:  # noqa: BLE001 - some sd_prod functions need real arguments
        return None, True
    names: list[str] = []

    def add(item: Any) -> None:
        if isinstance(item, (list, tuple)):
            for sub in item:
                add(sub)
        elif item is not None:
            name = _value(item)
            if name not in names:
                names.append(name)

    add(found)
    return names, True


def _command(cmd: Any, sources: dict[int, tuple[str, int]]) -> dict:
    definition = cmd.definition
    result, computed = _result_types(cmd)
    doc: dict[str, Any] = {
        "command": cmd.name,
        "kind": COMMAND_KINDS.get(type(cmd).__name__, type(cmd).__name__),
        "fr": definition.get("fr") or None,
        "translation_upstream": _value(definition.get("translation")),
        "op": _value(definition.get("op")),
        "reentrant": definition.get("reentrant"),
        "result_types": result,
        "result_type_depends_on_keywords": computed,
        "has_compat_syntax": "compat_syntax" in definition,
    }
    for key in ("docu", "repetable"):
        if key in definition:
            doc[key] = _value(definition[key])
    doc["rules"] = _rules(cmd.rules)
    other = _other(definition, _COMMAND_KEYS)
    if other:
        doc["other"] = other
    doc["source"] = _source(cmd, sources)
    doc["keywords"] = _entities(cmd, "", sources)
    return doc


def _dump(upstream: Path) -> dict[str, dict]:
    """Import the catalogs from ``upstream`` and return ``{command name: document}``.

    Must run in a fresh interpreter (see the module docstring).
    """
    upstream = upstream.resolve()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(upstream))
    if "code_aster.Cata.Commands" in sys.modules:
        raise RuntimeError("code_aster.Cata.Commands already imported; run in a fresh process")

    from code_aster.Cata.Language import SyntaxObjects

    cata_dir = upstream / "code_aster" / "Cata"
    lang_dir = cata_dir / "Language"
    sources: dict[int, tuple[str, int]] = {}
    original_init = SyntaxObjects.PartOfSyntax.__init__

    def recording_init(self: Any, curDict: dict) -> None:  # noqa: N803 - upstream's name
        original_init(self, curDict)
        frame = sys._getframe(1)
        while frame is not None:
            path = Path(frame.f_code.co_filename)
            if path.is_relative_to(cata_dir) and not path.is_relative_to(lang_dir):
                sources[id(self)] = (path.relative_to(upstream).as_posix(), frame.f_lineno)
                break
            frame = frame.f_back

    SyntaxObjects.PartOfSyntax.__init__ = recording_init
    try:
        from code_aster.Cata.Commands import commandStore
    finally:
        SyntaxObjects.PartOfSyntax.__init__ = original_init

    docs = {}
    for name in sorted(commandStore):
        cmd = commandStore[name]
        if not isinstance(cmd, SyntaxObjects.Command):
            continue  # VARIABLE (VariableSupport), not a command
        docs[name] = _command(cmd, sources)
    return docs


# --------------------------------------------------------------------------------------
# Parent side: run the child, add provenance, write files.
# --------------------------------------------------------------------------------------


def upstream_provenance(repo: Path) -> dict[str, str | None]:
    """Pinned tag (``UPSTREAM_VERSION``) and commit of ``repo/upstream``."""
    tag = None
    version_file = repo / "UPSTREAM_VERSION"
    if version_file.is_file():
        lines = [ln.strip() for ln in version_file.read_text().splitlines()]
        tag = next((ln for ln in lines if ln and not ln.startswith("#")), None)
    try:
        commit = subprocess.run(
            ["git", "-C", str(repo / "upstream"), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    return {"upstream": tag, "upstream_commit": commit}


def extract(upstream: Path) -> dict[str, dict]:
    """Run the catalog import in a child interpreter; return ``{command: document}``."""
    if not (upstream / COMMANDS_RELDIR).is_dir():
        raise FileNotFoundError(
            f"{upstream / COMMANDS_RELDIR} not found (run `git submodule update --init`)"
        )
    # Fixed hash seed: some into= tuples are built from a set (Commons/c_nom_cham_into.py,
    # `tuple(set(...))`), so their order would otherwise change from run to run.
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0")
    proc = subprocess.run(
        [sys.executable, "-B", "-m", EXTRACTOR, str(upstream)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(Path(__file__).resolve().parents[2]),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"catalog import failed:\n{proc.stderr}")
    return json.loads(proc.stdout)


def with_provenance(doc: dict, provenance: dict[str, str | None]) -> dict:
    source = doc.get("source") or {}
    header = {
        "_generated_from": {
            **provenance,
            "file": source.get("file"),
            "extractor": EXTRACTOR,
            "extractor_version": EXTRACTOR_VERSION,
        },
        "schema_version": SCHEMA_VERSION,
    }
    return {**header, **doc}


def render(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def write(repo: Path, outdir: Path, only: list[str] | None = None) -> list[Path]:
    """Extract every command (or ``only`` those) and write ``outdir/<CMD>.json``."""
    docs = extract(repo / "upstream")
    if only:
        missing = sorted(set(only) - set(docs))
        if missing:
            raise KeyError(f"not in the catalog: {', '.join(missing)}")
        docs = {name: docs[name] for name in only}
    provenance = upstream_provenance(repo)
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, doc in docs.items():
        path = outdir / f"{name}.json"
        path.write_text(render(with_provenance(doc, provenance)), encoding="utf-8")
        written.append(path)
    return written


def iter_keywords(entities: list[dict]) -> Iterator[dict]:
    """Depth-first walk over a command's ``keywords`` tree, blocs included."""
    for ent in entities:
        yield ent
        yield from iter_keywords(ent.get("keywords", []))


if __name__ == "__main__":
    json.dump(_dump(Path(sys.argv[1])), sys.stdout, ensure_ascii=False)
