"""``caen translate command``: first-draft command references ``en/commands/<CMD>.md``.

Task 2.2. A draft is built only from data already in the repository, so it never describes
behavior that has no source (CLAUDE.md §2.6):

- ``en/commands/<CMD>.json`` (``caen extract catalog``): keyword tree, types, defaults,
  allowed values, bloc conditions, rules and French ``fr=`` help strings;
- ``en/glossary.yaml``: the English name of the command and of each keyword;
- ``en/catalog-help.yaml``: the translation memory for catalog ``fr=`` strings (fr → en).
  A string without an entry is shown as ``TODO(translate)`` with the French quoted;
- ``en/astest-index.json`` (``caen extract astest-index``): upstream test cases that call the
  command. The call itself is lifted from ``upstream/astest`` when the submodule is present;
- ``en/doc-ids.yaml``: the French U4 document ID per command, when the catalog has no
  ``docu=``.

Keyword-table scope. Every top-level simple keyword is listed. Factor keywords are expanded
(with their sub-keywords) when the command has at most ``SMALL_COMMAND`` distinct keyword
paths, when ``--all-keywords`` is given, or when the factor is one of the command's "key
keywords" in ``docs/COMMAND-SET.md``; the other factors are named under "Other keywords".
Hidden keywords (``statut='c'``) are never listed.

Catalog semantics used for the English (``upstream/code_aster/Cata/Language/``):
``statut`` ``o`` required, ``f`` optional, ``d`` factor present by default, ``c`` hidden
(``SyntaxObjects.py``); a result can be reused (``reuse=``) when ``reentrant`` starts with
``o`` or ``f`` (``Command.can_reuse``); rule meanings from the docstrings in ``Rules.py``.

A draft has ``status: machine``. Re-running the generator overwrites a draft only while its
status is still ``machine``; an ``assisted`` or ``reviewed`` reference is left alone unless
``force`` is set.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jinja2
import yaml

from codeaster_en.extract import inventory
from codeaster_en.extract.catalog import iter_keywords
from codeaster_en.validate import glossary as glossary_validator

COMMANDS_RELDIR = Path("en/commands")
GLOSSARY_RELPATH = Path("en/glossary.yaml")
HELP_RELPATH = Path("en/catalog-help.yaml")
DOC_IDS_RELPATH = Path("en/doc-ids.yaml")
ASTEST_INDEX_RELPATH = Path("en/astest-index.json")
COMMAND_SET_RELPATH = Path("docs/COMMAND-SET.md")
UPSTREAM_RELDIR = Path("upstream")
TEMPLATES = Path(__file__).parent / "templates"
TEMPLATE = "command.md.j2"
GENERATOR = "caen translate command"

SMALL_COMMAND = 150
MAX_EXAMPLES = 3
MAX_PATTERNS = 2
MAX_PATTERN_LINES = 30
MAX_INTO = 12
# Error-handling test cases (erreu01a, ...): their calls can be deliberately invalid.
EXCLUDED_CASE_PREFIXES = ("erreu",)

STATUS_WORDS = {"o": "required", "f": "optional", "d": "optional, present by default"}
BASIC_TYPES = {
    "R": "real",
    "I": "integer",
    "C": "complex",
    "TXM": "text",
    "grma": "element group",
    "grno": "node group",
    "ma": "element",
    "no": "node",
}
GLOSSARY_KINDS = frozenset({"command", "keyword", "value", "concept", "term"})

# Rules.py docstrings, as sentences over the keyword list.
RULE_TEXT = {
    "AU_MOINS_UN": "at least one of {kw} must be given",
    "UN_PARMI": "exactly one of {kw} must be given",
    "EXCLUS": "at most one of {kw} may be given",
    "PRESENT_PRESENT": "if {first} is given, {rest} must all be given",
    "PRESENT_ABSENT": "if {first} is given, none of {rest} may be given",
    "ENSEMBLE": "{kw} are given all together or not at all",
    "NON_VIDE": "at least one keyword must be given",
}

_STATUS_LINE = re.compile(r"^status:\s*(\S+)\s*$", re.MULTILINE)


class DraftError(Exception):
    """A draft cannot be generated (missing catalog, unknown command)."""


# --------------------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------------------


@dataclass
class Sources:
    """Everything a draft is built from, loaded once for a run."""

    repo: Path
    commands: dict[str, dict[str, Any]]
    glossary: dict[str, dict[str, Any]]
    help_en: dict[str, str]
    doc_ids: dict[str, dict[str, Any]]
    index: dict[str, Any]
    key_keywords: dict[str, list[str]]
    tiers: dict[str, list[str]]

    @property
    def upstream(self) -> Path:
        return self.repo / UPSTREAM_RELDIR


def _read_yaml_list(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    data = yaml.load(path.read_text(encoding="utf-8"), Loader=glossary_validator._Yaml12Loader)
    if data is None:
        return []
    if not isinstance(data, list):
        raise DraftError(f"{path}: expected a list of entries")
    return data


def load_help(path: Path) -> dict[str, str]:
    """Translation memory ``{fr: en}`` from ``en/catalog-help.yaml``."""
    out: dict[str, str] = {}
    for entry in _read_yaml_list(path):
        if entry.get("en"):
            out[str(entry["fr"])] = str(entry["en"])
    return out


def load_sources(repo: Path) -> Sources:
    commands = inventory.load_commands(repo / COMMANDS_RELDIR)
    glossary = {
        str(e["fr"]): e
        for e in glossary_validator.load(repo / GLOSSARY_RELPATH)
        if e.get("kind") in GLOSSARY_KINDS
    }
    doc_ids = {str(e["command"]): e for e in _read_yaml_list(repo / DOC_IDS_RELPATH)}
    index_path = repo / ASTEST_INDEX_RELPATH
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else {}
    command_set = inventory.parse_command_set(
        (repo / COMMAND_SET_RELPATH).read_text(encoding="utf-8"), set(commands) | {"POURSUITE"}
    )
    key_keywords: dict[str, list[str]] = {}
    tiers: dict[str, list[str]] = {}
    for row in command_set.rows:
        for name in row.commands:
            key_keywords.setdefault(name, [])
            key_keywords[name] += [k for k in row.key_keywords if k not in key_keywords[name]]
            tiers.setdefault(row.tier, [])
            if name not in tiers[row.tier]:
                tiers[row.tier].append(name)
    return Sources(
        repo=repo,
        commands=commands,
        glossary=glossary,
        help_en=load_help(repo / HELP_RELPATH),
        doc_ids=doc_ids,
        index=index,
        key_keywords=key_keywords,
        tiers=tiers,
    )


# --------------------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------------------


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


def _code(text: str) -> str:
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def _literal(value: Any) -> str:
    if isinstance(value, str):
        # Control characters (FIN_LIGNE defaults to "\n") would break the table row.
        escaped = value.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        return _code(f"'{escaped}'")
    if isinstance(value, list | tuple):
        return _code("(" + ", ".join(repr(v) for v in value) + ")")
    return _code(repr(value))


def _condition(text: str) -> str:
    cond = " ".join(text.split())
    while cond.startswith("(") and cond.endswith(")") and _balanced(cond[1:-1]):
        cond = cond[1:-1].strip()
    return cond


def _balanced(text: str) -> bool:
    depth = 0
    for char in text:
        depth += {"(": 1, ")": -1}.get(char, 0)
        if depth < 0:
            return False
    return depth == 0


def keyword_label(path: str) -> str:
    return " / ".join(path.split("/"))


def translate_help(fr: str | None, help_en: dict[str, str]) -> str | None:
    """English for a catalog ``fr=`` string, a TODO quoting it, or None if there is none."""
    if not fr:
        return None
    en = help_en.get(fr)
    return en if en else f"TODO(translate): «{' '.join(fr.split())}»"


def _type_text(kw: dict[str, Any]) -> str:
    if kw["kind"] == "factor":
        text = "factor keyword"
    else:
        names = [BASIC_TYPES.get(t, _code(t)) for t in kw.get("type", [])]
        text = " or ".join(names) or "—"
    words = [text, STATUS_WORDS.get(kw.get("status") or "f", kw.get("status") or "optional")]
    low, high = kw.get("min"), kw.get("max")
    if high == "**":
        words.append("repeatable" if kw["kind"] == "factor" else "list")
    elif isinstance(high, int) and high > 1:
        words.append(f"up to {high}" if kw["kind"] == "factor" else f"list of up to {high}")
    if isinstance(low, int) and low > 1:
        words.append(f"at least {low}")
    return ", ".join(words)


def _allowed(kw: dict[str, Any]) -> str | None:
    into = kw.get("into")
    if into:
        shown = ", ".join(_literal(v) for v in into[:MAX_INTO])
        more = f", … ({len(into)} values; see the .json)" if len(into) > MAX_INTO else ""
        return f"One of {shown}{more}."
    bounds = []
    if "val_min" in kw:
        bounds.append(f"≥ {kw['val_min']}")
    if "val_max" in kw:
        bounds.append(f"≤ {kw['val_max']}")
    return f"Range: {', '.join(bounds)}." if bounds else None


# --------------------------------------------------------------------------------------
# Keyword table
# --------------------------------------------------------------------------------------


@dataclass
class Row:
    path: str
    kind: str
    type_text: str
    default: str
    allowed: str | None
    name_en: str | None
    help_text: str | None
    conditions: list[str] = field(default_factory=list)
    unconditional: bool = False

    @property
    def keyword(self) -> str:
        return _code(keyword_label(self.path))

    @property
    def meaning(self) -> str:
        parts: list[str] = []
        if self.name_en:
            parts.append(f"*{self.name_en}*.")
        if self.help_text:
            parts.append(self.help_text if self.help_text.endswith(".") else self.help_text + ".")
        if self.allowed:
            parts.append(self.allowed)
        if self.conditions and not self.unconditional:
            parts.append("Only when " + "; or ".join(_code(c) for c in self.conditions) + ".")
        if not self.name_en and not self.help_text:
            parts.append("TODO(2.3): meaning.")
        parts.append("TODO(2.3): when to use.")
        return _cell(" ".join(parts))


@dataclass
class RuleLine:
    scope: str
    text: str


@dataclass
class Other:
    name: str
    name_en: str | None
    help_text: str | None


def _rule_text(rule: dict[str, Any]) -> str:
    names = [_code(k) for k in rule["keywords"]]
    template = RULE_TEXT.get(rule["rule"], rule["rule"] + " {kw}")
    text = template.format(
        kw=", ".join(names), first=names[0] if names else "", rest=", ".join(names[1:])
    )
    defaults = rule.get("defaults")
    if defaults:
        given = ", ".join(_code(f"{k}={v!r}") for k, v in defaults.items())
        text += f"; if none is given, {given} is assumed"
    return f"{text} (`{rule['rule']}`)"


@dataclass
class Table:
    rows: list[Row]
    rules: list[RuleLine]
    others: list[Other]
    hidden: int
    expanded_all: bool


def _signature(kw: dict[str, Any]) -> tuple:
    return (
        kw["kind"],
        tuple(kw.get("type", [])),
        repr(kw.get("default")),
        tuple(repr(v) for v in kw.get("into", [])),
        kw.get("status"),
        kw.get("min"),
        kw.get("max"),
        kw.get("val_min"),
        kw.get("val_max"),
        kw.get("fr"),
    )


def build_table(doc: dict[str, Any], src: Sources, all_keywords: bool = False) -> Table:
    name = doc["command"]
    paths = {k["path"] for k in iter_keywords(doc["keywords"]) if k["kind"] != "bloc"}
    expand_all = all_keywords or len(paths) <= SMALL_COMMAND
    key = set(src.key_keywords.get(name, []))

    rows: dict[tuple, Row] = {}
    rules: list[RuleLine] = [RuleLine("command", _rule_text(r)) for r in doc.get("rules", [])]
    others: dict[str, Other] = {}
    hidden: set[str] = set()

    def in_scope(kw: dict[str, Any], top: dict[str, Any] | None) -> bool:
        root = top or kw
        return expand_all or root["kind"] == "simple" or root["name"] in key

    def walk(entities: list[dict], conditions: list[str], top: dict[str, Any] | None) -> None:
        for kw in entities:
            if kw["kind"] == "bloc":
                cond = _condition(kw.get("condition", ""))
                for rule in kw.get("rules", []):
                    if top is None or in_scope(top, None):
                        rules.append(RuleLine(f"when {_code(cond)}", _rule_text(rule)))
                walk(kw.get("keywords", []), [*conditions, cond], top)
                continue
            if kw.get("status") == "c":
                hidden.add(kw["path"])
                continue
            root = top or kw
            if not in_scope(kw, top):
                if root is kw and kw["name"] not in others:
                    others[kw["name"]] = Other(
                        kw["name"],
                        _glossary_en(src, kw["name"]),
                        translate_help(kw.get("fr"), src.help_en),
                    )
                continue
            sig = (kw["path"], _signature(kw))
            row = rows.get(sig)
            if row is None:
                row = rows[sig] = Row(
                    path=kw["path"],
                    kind=kw["kind"],
                    type_text=_type_text(kw),
                    default=_literal(kw["default"]) if "default" in kw else "—",
                    allowed=_allowed(kw),
                    name_en=_glossary_en(src, kw["name"]),
                    help_text=translate_help(kw.get("fr"), src.help_en),
                )
            if conditions:
                cond = " and ".join(conditions)
                if cond not in row.conditions:
                    row.conditions.append(cond)
            else:
                row.unconditional = True
            if kw["kind"] == "factor":
                for rule in kw.get("rules", []):
                    rules.append(RuleLine(_code(keyword_label(kw["path"])), _rule_text(rule)))
                walk(kw.get("keywords", []), [], root)

    walk(doc["keywords"], [], None)
    unique_rules: list[RuleLine] = []
    for rule in rules:
        if all((rule.scope, rule.text) != (r.scope, r.text) for r in unique_rules):
            unique_rules.append(rule)
    return Table(
        rows=list(rows.values()),
        rules=unique_rules,
        others=sorted(others.values(), key=lambda o: o.name),
        hidden=len(hidden),
        expanded_all=expand_all,
    )


def _glossary_en(src: Sources, name: str) -> str | None:
    entry = src.glossary.get(name)
    return str(entry["en"]) if entry else None


# --------------------------------------------------------------------------------------
# Examples from astest
# --------------------------------------------------------------------------------------


@dataclass
class Example:
    case: str
    file: str
    lines: list[int]
    snippet: str | None = None
    snippet_line: int | None = None


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


def call_snippet(path: Path, command: str, line: int) -> str | None:
    """Source of the statement whose value is the ``command(...)`` call starting on ``line``."""
    try:
        text = path.read_bytes().decode("utf-8")
        tree = ast.parse(text)
    except (OSError, UnicodeDecodeError, SyntaxError, ValueError):
        return None
    for stmt in ast.walk(tree):
        if not isinstance(stmt, ast.Assign | ast.Expr) or stmt.lineno != line:
            continue
        if _call_name(stmt.value) == command:
            return ast.get_source_segment(text, stmt)
    return None


def pick_examples(src: Sources, command: str) -> list[Example]:
    """Sequential test cases that call ``command``, closest to a Tier 1 workflow first.

    Ranked by the number of commands used that are outside Tier 1 (fewest first), then by the
    number of commands used (fewest first: the call is easier to read in a short case), then by
    name.
    """
    entry = src.index.get("commands", {}).get(command)
    if not entry:
        return []
    tier1 = set(src.tiers.get("1", []))
    cases = src.index.get("testcases", {})
    ranked = []
    for case in entry.get("testcases", []):
        info = cases.get(case)
        if not info or info.get("parallel") or case.startswith(EXCLUDED_CASE_PREFIXES):
            continue
        used = info.get("commands", [])
        outside = len([c for c in used if c not in tier1])
        ranked.append((outside, len(used), case))
    upstream_ok = (src.upstream / "astest").is_dir()
    candidates: list[Example] = []
    patterns = 0
    families: set[str] = set()
    for _, _, case in sorted(ranked):
        # One case per family: ssll01a and ssll01b usually differ only in the modeling.
        if case.rstrip("abcdefghijklmnopqrstuvwxyz") in families:
            continue
        cfile = next(
            (f for f in cases[case].get("command_files", []) if f.get("calls", {}).get(command)),
            None,
        )
        if cfile is None:
            continue
        lines = list(cfile["calls"][command])
        example = Example(case, f"astest/{cfile['path']}", lines)
        if upstream_ok and patterns < MAX_PATTERNS:
            snippet = call_snippet(src.upstream / example.file, command, lines[0])
            if snippet and snippet.count("\n") < MAX_PATTERN_LINES:
                example.snippet, example.snippet_line = snippet, lines[0]
                patterns += 1
        candidates.append(example)
        families.add(case.rstrip("abcdefghijklmnopqrstuvwxyz"))
        if (patterns >= MAX_PATTERNS or not upstream_ok) and len(candidates) >= MAX_EXAMPLES:
            break
    # Cases with a pattern first, then the simplest others, kept in rank order.
    chosen = [e for e in candidates if e.snippet][:MAX_PATTERNS]
    chosen += [e for e in candidates if not e.snippet][: MAX_EXAMPLES - len(chosen)]
    return [e for e in candidates if e in chosen]


# --------------------------------------------------------------------------------------
# Draft
# --------------------------------------------------------------------------------------


def doc_id(doc: dict[str, Any], src: Sources) -> tuple[str | None, str | None]:
    """``(doc ID, where it comes from)``: the catalog ``docu=`` wins over en/doc-ids.yaml."""
    docu = doc.get("docu")
    if docu:
        where = f"catalog docu= ({doc['source']['file']})"
        return str(docu), where
    entry = src.doc_ids.get(doc["command"])
    if entry:
        return str(entry["doc_id"]), f"{DOC_IDS_RELPATH} (status: {entry.get('status')})"
    return None, None


def _reuse(doc: dict[str, Any]) -> str:
    value = doc.get("reentrant") or ""
    parts = value.split(":")
    if parts[0] not in ("o", "f"):
        return "no"
    via = parts[-1] if len(parts) > 1 else ""
    names = ", ".join(_code(n) for n in via.split("|") if n)
    how = f" (the object given in {names})" if names else ""
    return f"yes{how}; catalog `reentrant='{value}'`"


def context(command: str, src: Sources, all_keywords: bool = False) -> dict[str, Any]:
    doc = src.commands.get(command)
    if doc is None:
        raise DraftError(f"{command}: no {COMMANDS_RELDIR}/{command}.json")
    gen = doc["_generated_from"]
    docid, docid_from = doc_id(doc, src)
    tier = next((t for t, names in sorted(src.tiers.items()) if command in names), None)
    results = doc.get("result_types")
    return {
        "command": command,
        "generator": GENERATOR,
        "upstream": gen.get("upstream"),
        "upstream_commit": gen.get("upstream_commit"),
        "source": f"{doc['source']['file']}:{doc['source']['line']}",
        "doc_fr": docid,
        "doc_fr_from": docid_from,
        "tier": tier,
        "title_en": _glossary_en(src, command),
        "fr": " ".join(doc["fr"].split()) if doc.get("fr") else None,
        "help_en": translate_help(doc.get("fr"), src.help_en),
        "kind": doc["kind"],
        "results": [_code(r) for r in results or []],
        "results_vary": doc.get("result_type_depends_on_keywords", False),
        "reuse": _reuse(doc),
        "key_keywords": [_code(k) for k in src.key_keywords.get(command, [])],
        "table": build_table(doc, src, all_keywords),
        "examples": pick_examples(src, command),
    }


def _environment() -> jinja2.Environment:
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATES),
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )


def render(command: str, src: Sources, all_keywords: bool = False) -> str:
    text = _environment().get_template(TEMPLATE).render(**context(command, src, all_keywords))
    return re.sub(r"\n{3,}", "\n\n", text)


def draft_status(path: Path) -> str | None:
    """``status:`` from the front matter of an existing reference, if any."""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    match = _STATUS_LINE.search(text.split("\n---", 1)[0])
    return match.group(1) if match else None


@dataclass
class Outcome:
    command: str
    path: Path | None
    action: str  # written | unchanged | skipped
    reason: str = ""


def resolve(src: Sources, commands: list[str] | None, tier: str | None) -> list[str]:
    """Explicit commands, else the commands of ``tier`` in COMMAND-SET order."""
    if commands:
        return list(commands)
    if tier is None:
        raise DraftError("name at least one command or pass --tier")
    if tier not in src.tiers:
        raise DraftError(f"tier {tier!r} has no commands in {COMMAND_SET_RELPATH}")
    return list(src.tiers[tier])


def write(
    src: Sources,
    commands: list[str],
    outdir: Path,
    force: bool = False,
    all_keywords: bool = False,
) -> list[Outcome]:
    outdir.mkdir(parents=True, exist_ok=True)
    outcomes: list[Outcome] = []
    for command in commands:
        if command not in src.commands:
            outcomes.append(Outcome(command, None, "skipped", f"no {command}.json in the catalog"))
            continue
        path = outdir / f"{command}.md"
        status = draft_status(path)
        if path.exists() and status != "machine" and not force:
            reason = f"status is {status!r}, not 'machine' (use --force to overwrite)"
            outcomes.append(Outcome(command, path, "skipped", reason))
            continue
        text = render(command, src, all_keywords)
        if path.is_file() and path.read_text(encoding="utf-8") == text:
            outcomes.append(Outcome(command, path, "unchanged"))
            continue
        path.write_text(text, encoding="utf-8")
        outcomes.append(Outcome(command, path, "written"))
    return outcomes


def untranslated(src: Sources, commands: list[str], all_keywords: bool = False) -> list[str]:
    """Catalog ``fr=`` strings a draft of ``commands`` would show as ``TODO(translate)``."""
    found: list[str] = []

    def add(fr: str | None) -> None:
        if fr and fr not in src.help_en and fr not in found:
            found.append(fr)

    for command in commands:
        doc = src.commands.get(command)
        if doc is None:
            continue
        add(doc.get("fr"))
        table = build_table(doc, src, all_keywords)
        scoped = {r.path for r in table.rows}
        for kw in iter_keywords(doc["keywords"]):
            if kw["kind"] != "bloc" and kw["path"] in scoped:
                add(kw.get("fr"))
        names = {o.name for o in table.others}
        for kw in iter_keywords(doc["keywords"]):
            if kw["kind"] != "bloc" and "/" not in kw["path"] and kw["name"] in names:
                add(kw.get("fr"))
    return found
