"""``caen translate doc``: chunked, glossary-locked translation of the official French documents.

Task 5.2 (TRANSLATION-GUIDE.md §5, ADR-027). Input: the documents ingested by task 5.1,
``en/docs/_src/<DOC-ID>.fr.json`` (blocks and translation chunks of at most 6,000 characters).
Output: ``en/docs/<DOC-ID>.md``, a GFDL modified version (ADR-026) with a provenance header.

Which documents and which chunks are translated is set by ``en/docs/scope.yaml`` (human-edited):
a chunk outside the scope keeps its French headings, marked "not translated", so section
numbers and cross-references still resolve (CLAUDE.md §2 rule 7).

One request per chunk. The request carries the rules, the glossary entries whose French occurs
in the chunk, the keywords of the command(s) the document describes (``en/doc-ids.yaml``), and
the chunk's French Markdown in which every code block (syntax trees, listings, ``.comm``
examples) is replaced by a ``[[CODE n]]`` marker: code is the solver's API and stays verbatim
(CLAUDE.md §2 rule 2), so the tool puts it back itself. The answer is English Markdown and
must pass :func:`check_chunk`: same code markers, page markers, heading numbers and levels,
list items, table rows and cells, equation and figure markers; every solver identifier of the
French still present; no forbidden glossary synonym; no French words left outside code.

Backends implement :class:`DocTranslator`:

- :class:`AnthropicDocTranslator` calls the Claude API (``pip install 'codeaster_en[llm]'``).
  It spends the owner's API budget: CLAUDE.md §3 and ADR-010 make that an owner decision.
- :class:`ReplayDocTranslator` reads answers from ``<DIR>/<DOC-ID>/<chunk>.md``. It is how tests
  run, and how an in-session agent translates without an API key: ``--export-requests DIR``
  writes ``<DIR>/<DOC-ID>/<chunk>.request.md``, the agent writes the answers next to them, and
  ``--responses DIR`` imports them through the same checks.

Re-assembly reads the existing ``en/docs/<DOC-ID>.md`` back by its chunk markers
(``<!-- chunk N fr=<sha> method=… -->``), so translated chunks, and chunks the owner edited or
marked ``reviewed``, are kept; a chunk whose French changed is flagged ``stale`` and offered
for translation again.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import yaml

from codeaster_en.docs import ingest
from codeaster_en.report import tripwire
from codeaster_en.translate import messages as msg
from codeaster_en.validate import glossary as glossary_validator
from codeaster_en.validate import synonyms

DOCS_RELDIR = Path("en/docs")
SRC_RELDIR = ingest.SOURCE_RELDIR
SCOPE_RELPATH = Path("en/docs/scope.yaml")
DOC_IDS_RELPATH = Path("en/doc-ids.yaml")
COMMANDS_RELDIR = Path("en/commands")
METHODS = ("machine", "assisted")  # "reviewed" is set by the owner only (CLAUDE.md §3)
LICENCE = "GFDL-1.3"
TOOL = "codeaster_en.translate.doc"
TOOL_VERSION = "1"
MAX_TOKENS = 32000

CODE_MARKER = re.compile(r"^\[\[CODE (\d+)\]\]$", re.M)
PAGE_MARKER = re.compile(r"^<!-- page (\d+) -->$", re.M)
HEADING_LINE = re.compile(r"^(#{1,6}) (?:(\d+(?:\.\d+)*) )?")
LIST_LINE = re.compile(r"^( *)- ", re.M)
FIGURE = re.compile(r"\*\[Figure, page (\d+): not extracted\]\*")
EQUATION = "<!-- equation -->"
IDENT = re.compile(r"(?<![\w])[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*(?![\w])")
# Capitalised French words that are also keyword values but read as prose ("par DEFAUT").
PROSE_CAPS = frozenset({"DEFAUT", "ATTENTION", "REMARQUE", "NOTA", "NB"})
CHUNK_MARKER = re.compile(r"^<!-- chunk (\d+)((?: [a-z_]+=[^ ]+)*) -->$", re.M)
_FENCED = re.compile(r"^```text\n.*?^```$", re.M | re.S)
_FRENCH_QUOTED = re.compile(r"«[^»]*»")
_CONCEPT_TYPE = re.compile(r"\[[a-z][a-z0-9_]*\]")  # [maillage], [table_sdaster]: API
_QUOTED_VALUE = re.compile(r"(?<!\w)'[^'\n]*'(?!\w)")  # 'OUI', 'mesh.med': values

SYSTEM_RULES = """\
You translate official code_aster documentation (EDF R&D user manuals, U4 command reference)
from French to English for structural engineers. code_aster is EDF's finite element solver.
You get one chunk of a document as Markdown and answer with the same chunk in English Markdown,
nothing else (no preamble, no code fence around the answer).

Rules:
1. Keep the structure exactly: every line that is a heading stays a heading with the same
   number of # and the same section number; every list item stays a list item at the same
   indentation; every table keeps its rows and cells (translate the cell text); every
   paragraph stays a paragraph. Do not merge, split, drop or add any of them.
2. Lines [[CODE n]] stand for code blocks the tool keeps verbatim. Copy each marker on its own
   line, in the same place. Copy <!-- page N --> markers, <!-- equation --> markers and
   *[Figure, page N: not extracted]* lines exactly where they are.
3. Command names, keyword names and keyword values written in capitals (AFFE_MODELE,
   GROUP_MA, PRES_REP, 'OUI', 'NON', TOUT='OUI') are the solver's API: copy them verbatim,
   including inside quotes and inside formulas. Never translate or rename them. Concept type
   names in brackets ([maillage], [modele], [table_sdaster]) are API too: keep them.
4. Formula lines marked <!-- equation --> were extracted from typeset math and are often
   garbled: copy their symbols as they are; translate only real French words in them.
5. Use the glossary: when a French term has an entry, use its English, every time. Never use
   a word listed as forbidden for it ("element", never "cell"; "corner node", never
   "vertex"; "warning", never "alarm"). Plain American English, SI unit names, the
   register of a reference manual. Do not add explanations that are not in the French.
6. Document references stay as they are ([U4.41.01], [R3.01.01]). Titles of other documents
   quoted in guillemets may be translated, or kept in French inside « ».
7. Never invent solver behavior. If the French is ambiguous, translate it literally.
"""


class TranslateError(RuntimeError):
    """A run cannot start or a backend failed in a way that is not one chunk's fault."""


# ---------------------------------------------------------------- scope and sources


@dataclass(frozen=True)
class DocScope:
    doc_id: str
    tier: int
    chunks: frozenset[int] | None  # None = every chunk
    reason: str = ""

    def includes(self, chunk_id: int) -> bool:
        return self.chunks is None or chunk_id in self.chunks


def parse_ranges(text: str | int | list[Any]) -> frozenset[int]:
    """``"1-4, 107"`` (or a list of such items) → ``{1, 2, 3, 4, 107}``."""
    items = text if isinstance(text, list) else [text]
    found: set[int] = set()
    for item in items:
        for part in str(item).split(","):
            part = part.strip()
            if not part:
                continue
            lo, _, hi = part.partition("-")
            first, last = int(lo), int(hi or lo)
            if last < first:
                raise TranslateError(f"bad chunk range {part!r}")
            found.update(range(first, last + 1))
    return frozenset(found)


def load_scope(root: Path) -> dict[str, DocScope]:
    """``en/docs/scope.yaml``: the documents to translate and, per document, which chunks."""
    path = root / SCOPE_RELPATH
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    scopes = {}
    for doc_id, entry in (data.get("docs") or {}).items():
        entry = entry or {}
        chunks = entry.get("chunks")
        scopes[str(doc_id)] = DocScope(
            doc_id=str(doc_id),
            tier=int(entry.get("tier", 1)),
            chunks=None if chunks in (None, "all") else parse_ranges(chunks),
            reason=str(entry.get("reason") or ""),
        )
    return scopes


def doc_commands(root: Path) -> dict[str, list[str]]:
    """Doc ID → the commands it documents, from ``en/doc-ids.yaml``."""
    entries = yaml.safe_load((root / DOC_IDS_RELPATH).read_text(encoding="utf-8")) or []
    found: dict[str, list[str]] = {}
    for entry in entries:
        found.setdefault(str(entry["doc_id"]), []).append(str(entry["command"]))
    return found


def _walk(keywords: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for kw in keywords:
        yield kw
        yield from _walk(kw.get("keywords") or [])


def load_identifiers(root: Path) -> frozenset[str]:
    """Every command name, keyword name and capitalised keyword value of the catalog JSON."""
    found: set[str] = set()
    for path in (root / COMMANDS_RELDIR).glob("*.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        found.add(doc["command"])
        for kw in _walk(doc.get("keywords") or []):
            found.add(kw["name"])
            for value in kw.get("into") or []:
                if isinstance(value, str) and IDENT.fullmatch(value):
                    found.add(value)
    return frozenset(v for v in found if len(v) >= 2)


def command_keywords(root: Path, command: str) -> list[str]:
    path = root / COMMANDS_RELDIR / f"{command}.json"
    if not path.is_file():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    return sorted({kw["path"] for kw in _walk(doc.get("keywords") or [])})


@dataclass
class Sources:
    root: Path
    terms: list[msg.Term]
    forbidden: list[synonyms.Alias]
    identifiers: frozenset[str]
    scope: dict[str, DocScope]
    commands: dict[str, list[str]]
    upstream: str


def load_sources(root: Path) -> Sources:
    glossary = root / msg.GLOSSARY_RELPATH
    version = root / "UPSTREAM_VERSION"
    return Sources(
        root=root,
        terms=msg.load_terms(glossary),
        forbidden=synonyms.aliases(glossary_validator.load(glossary)),
        identifiers=load_identifiers(root),
        scope=load_scope(root),
        commands=doc_commands(root),
        upstream=version.read_text(encoding="utf-8").strip() if version.is_file() else "",
    )


def load_source(root: Path, doc_id: str) -> dict[str, Any]:
    path = root / SRC_RELDIR / f"{doc_id}.fr.json"
    if not path.is_file():
        raise TranslateError(f"no ingested document {doc_id!r} ({path} not found)")
    return json.loads(path.read_text(encoding="utf-8"))


def tier_docs(src: Sources, tier: int) -> list[str]:
    """Documents of ``scope.yaml`` at this tier or below."""
    return sorted(d for d, s in src.scope.items() if s.tier <= tier)


# ---------------------------------------------------------------- chunks


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    id: int
    section: str
    fr: str  # French Markdown with [[CODE n]] markers
    code: tuple[tuple[str, ...], ...]  # the code blocks' lines, in marker order
    headings: tuple[str, ...]  # French heading lines (for out-of-scope rendering)
    end_page: int
    sha: str  # of the chunk's blocks; changes when the French changes


def _sha(blocks: list[dict[str, Any]]) -> str:
    data = json.dumps(blocks, ensure_ascii=False, sort_keys=True).encode()
    return hashlib.sha256(data).hexdigest()[:12]


def chunks_of(doc: dict[str, Any]) -> list[Chunk]:
    """The document's chunks with code blocks replaced by ``[[CODE n]]`` markers.

    Page markers continue from one chunk to the next, as in ``<DOC-ID>.fr.md``.
    """
    found = []
    page = 0
    for item in doc["chunks"]:
        code: list[tuple[str, ...]] = []

        def marker(block: dict[str, Any], code: list[tuple[str, ...]] = code) -> list[str]:
            code.append(tuple(block["lines"]))
            return [f"[[CODE {len(code)}]]", ""]

        lines, page = ingest.render_blocks(doc["blocks"], item["first"], item["last"], page, marker)
        text = "\n".join(lines).strip() + "\n"
        blocks = doc["blocks"][item["first"] : item["last"] + 1]
        found.append(
            Chunk(
                doc_id=doc["doc_id"],
                id=item["id"],
                section=item["section"],
                fr=text,
                code=tuple(code),
                headings=tuple(ln for ln in lines if ln.startswith("#")),
                end_page=page,
                sha=_sha(blocks),
            )
        )
    return found


def expand_code(text: str, code: tuple[tuple[str, ...], ...]) -> str:
    """Put the verbatim code blocks back in place of their markers."""

    def block(match: re.Match[str]) -> str:
        return "\n".join(["```text", *code[int(match.group(1)) - 1], "```"])

    return CODE_MARKER.sub(block, text)


def collapse_code(text: str) -> tuple[str, list[tuple[str, ...]]]:
    """The inverse of :func:`expand_code`: fenced ``text`` blocks → markers, plus their lines."""
    code: list[tuple[str, ...]] = []

    def marker(match: re.Match[str]) -> str:
        code.append(tuple(match.group(0).split("\n")[1:-1]))
        return f"[[CODE {len(code)}]]"

    return _FENCED.sub(marker, text), code


# ---------------------------------------------------------------- checks


def _shape(text: str) -> dict[str, list[Any]]:
    lines = text.split("\n")
    headings = []
    for ln in lines:
        m = HEADING_LINE.match(ln)
        if m:
            headings.append((len(m.group(1)), m.group(2)))
    return {
        "code markers": CODE_MARKER.findall(text),
        "page markers": PAGE_MARKER.findall(text),
        "headings (level, number)": headings,
        "list items (indent)": [len(m.group(1)) for m in LIST_LINE.finditer(text)],
        "table rows (cells)": [ln.count(" | ") for ln in lines if ln.startswith("|")],
        "figure markers": FIGURE.findall(text),
        "equation markers": [ln.count(EQUATION) for ln in lines if EQUATION in ln],
    }


def _prose(text: str) -> str:
    """Text outside code markers, code spans and comments."""
    text = CODE_MARKER.sub("", text)
    text = re.sub(r"`[^`\n]*`", "", text)
    return re.sub(r"<!--.*?-->", "", text)


def identifiers_in(text: str, known: frozenset[str]) -> set[str]:
    return {t for t in IDENT.findall(_prose(text)) if t in known and t not in PROSE_CAPS}


def french_left(en: str) -> list[str]:
    """French words left in the English prose (outside code and « » quotes), proper names kept."""
    text = _QUOTED_VALUE.sub("", _CONCEPT_TYPE.sub("", _FRENCH_QUOTED.sub("", _prose(en))))
    return [w for w in tripwire.french_words(text) if not w[:1].isupper() or w.lower() == w]


def check_chunk(chunk: Chunk, en: str, src: Sources) -> list[str]:
    """Why ``en`` is not an acceptable translation of ``chunk`` (empty list = accepted)."""
    if not en.strip():
        return ["empty translation"]
    problems = []
    fr_shape, en_shape = _shape(chunk.fr), _shape(en)
    for name, fr_items in fr_shape.items():
        if en_shape[name] != fr_items:
            problems.append(f"{name} differ: French {fr_items}, English {en_shape[name]}")
    missing = identifiers_in(chunk.fr, src.identifiers) - set(IDENT.findall(en))
    if missing:
        problems.append("solver identifiers missing: " + ", ".join(sorted(missing)))
    problems += msg.glossary_problems(_prose(chunk.fr), en, src.terms)
    for number, alias, word in synonyms.scan_text(en, src.forbidden):
        problems.append(
            f"line {number}: forbidden synonym {word!r} (glossary {alias.fr!r} -> {alias.en!r})"
        )
    left = french_left(en)
    if left:
        problems.append("French words left: " + ", ".join(sorted(set(left))[:20]))
    return problems


# ---------------------------------------------------------------- requests and backends


@dataclass(frozen=True)
class Request:
    doc_id: str
    chunk: int
    attempt: int
    system: str
    user: str


def system_prompt(terms: Iterable[msg.Term]) -> str:
    lines = [msg._term_line(t) for t in terms if t.kind in msg.GLOSSARY_IN_SYSTEM]
    return (
        SYSTEM_RULES + "\nGlossary (general terms and abbreviations):\n" + "\n".join(lines) + "\n"
    )


def user_prompt(
    chunk: Chunk, title: str, src: Sources, problems: Iterable[str] = (), previous: str = ""
) -> str:
    specific = [
        t
        for t in msg.relevant_terms(src.terms, [_prose(chunk.fr)])
        if t.kind not in msg.GLOSSARY_IN_SYSTEM
    ]
    commands = src.commands.get(chunk.doc_id, [])
    parts = [
        f"Document {chunk.doc_id}, {title!r}, chunk {chunk.id} (section {chunk.section!r}).",
    ]
    for command in commands:
        keywords = command_keywords(src.root, command)
        if keywords:
            parts.append(f"Keywords of {command} (verbatim API): " + ", ".join(keywords))
    if specific:
        parts.append(
            "Glossary entries for names in this chunk:\n"
            + "\n".join(msg._term_line(t) for t in specific)
        )
    problems = list(problems)
    if problems:
        parts.append(
            "Your previous answer was rejected for these reasons; fix exactly that:\n"
            + "\n".join(f"- {p}" for p in problems)
        )
        if previous:
            parts.append("Previous answer:\n" + previous)
    parts.append("Translate this chunk:\n\n" + chunk.fr)
    return "\n\n".join(parts) + "\n"


@dataclass
class Answer:
    text: str | None
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None


class DocTranslator(Protocol):
    label: str  # recorded as the chunk's source

    def translate(self, request: Request) -> Answer: ...


class AnthropicDocTranslator:
    """Claude API backend. Needs the ``anthropic`` package and credentials in the environment."""

    def __init__(
        self,
        model: str = msg.DEFAULT_MODEL,
        effort: str = msg.DEFAULT_EFFORT,
        client: Any = None,
    ) -> None:
        if client is None:
            try:
                import anthropic
            except ImportError as exc:
                raise TranslateError(
                    "the Claude backend needs the anthropic package: pip install -e 'tools[llm]'"
                ) from exc
            client = anthropic.Anthropic()
        self.client = client
        self.model = model
        self.effort = effort
        self.label = f"llm:{model}"

    def translate(self, request: Request) -> Answer:
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=[
                {"type": "text", "text": request.system, "cache_control": {"type": "ephemeral"}}
            ],
            messages=[{"role": "user", "content": request.user}],
            output_config={"effort": self.effort},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        usage = getattr(response, "usage", None)
        tokens = {
            "input_tokens": getattr(usage, "input_tokens", 0) or 0,
            "output_tokens": getattr(usage, "output_tokens", 0) or 0,
        }
        if response.stop_reason == "refusal":
            return Answer(None, error="the model declined the request (refusal)", **tokens)
        if response.stop_reason == "max_tokens":
            return Answer(None, error="reply cut off at max_tokens", **tokens)
        text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
        return Answer(text, **tokens)


class ReplayDocTranslator:
    """Answers read from ``<directory>/<DOC-ID>/<chunk>.md``; a missing file is no answer."""

    def __init__(self, directory: Path, label: str | None = None) -> None:
        if not directory.is_dir():
            raise TranslateError(f"{directory}: not a directory")
        self.directory = directory
        self.label = label or f"replay:{directory.name}"

    def translate(self, request: Request) -> Answer:
        path = self.directory / request.doc_id / f"{request.chunk}.md"
        if not path.is_file():
            return Answer(None)
        return Answer(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- stored translation


@dataclass
class Stored:
    """One chunk as found in an existing ``en/docs/<DOC-ID>.md``."""

    attrs: dict[str, str]
    body: str


def doc_path(root: Path, doc_id: str) -> Path:
    return root / DOCS_RELDIR / f"{doc_id}.md"


def read_stored(path: Path) -> dict[int, Stored]:
    """Chunk number → marker attributes and body (code expanded), from a translated document."""
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    marks = list(CHUNK_MARKER.finditer(text))
    found = {}
    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        attrs = dict(a.split("=", 1) for a in mark.group(2).split())
        found[int(mark.group(1))] = Stored(attrs, text[mark.end() : end].strip("\n"))
    return found


def _translated(stored: Stored | None) -> bool:
    return stored is not None and "method" in stored.attrs


def pending(chunk: Chunk, stored: Stored | None, force: bool = False) -> bool:
    """In scope and not translated yet, translated from older French, or ``force``d."""
    if stored is not None and stored.attrs.get("method") == "reviewed":
        return False
    if not _translated(stored) or force:
        return True
    assert stored is not None
    return stored.attrs.get("fr") != chunk.sha


def _untranslated(chunk: Chunk, why: str) -> str:
    """A chunk left in French: its headings (so section numbers resolve) and a note."""
    lines = []
    for heading in chunk.headings:
        lines += [f"{heading} *(not translated)*", ""]
    lines.append(f"*[French chunk {chunk.id} (section {chunk.section!r}) not translated: {why}.]*")
    return "\n".join(lines)


def _yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def assemble(
    doc: dict[str, Any],
    scope: DocScope,
    chunks: list[Chunk],
    bodies: dict[int, Stored],
    src: Sources,
) -> str:
    """The English document: provenance header, notices, then every chunk in order."""
    meta = doc["meta"]
    gen = doc["_generated_from"]
    doc_id = doc["doc_id"]
    counts = {"total": len(chunks), "translated": 0, "stale": 0, "pending": 0, "out_of_scope": 0}
    body: list[str] = []
    methods: set[str] = set()
    sources: set[str] = set()
    dates: list[str] = []
    title_en = ""
    for chunk in chunks:
        stored = bodies.get(chunk.id)
        if _translated(stored):
            assert stored is not None
            attrs = dict(stored.attrs)
            counts["translated"] += 1
            if attrs.get("fr") != chunk.sha:
                attrs["stale"] = "1"
                counts["stale"] += 1
            methods.add(attrs["method"])
            sources.add(attrs.get("source", ""))
            dates.append(attrs.get("on", ""))
            text = stored.body
            if chunk.id == 1:
                title_en = next(
                    (ln[2:].strip() for ln in text.split("\n") if ln.startswith("# ")), ""
                )
            attr_text = " ".join(f"{k}={v}" for k, v in attrs.items())
        elif scope.includes(chunk.id):
            counts["pending"] += 1
            text = _untranslated(chunk, "translation pending")
            attr_text = f"fr={chunk.sha} status=pending"
        else:
            counts["out_of_scope"] += 1
            text = _untranslated(chunk, "outside the scope of docs/COMMAND-SET.md")
            attr_text = f"fr={chunk.sha} status=out-of-scope"
        body += [f"<!-- chunk {chunk.id} {attr_text} -->", "", text, ""]
    method = (
        "machine"
        if "machine" in methods
        else ("assisted" if "assisted" in methods else (min(methods) if methods else ""))
    )
    date, revision = meta.get("date", ""), meta.get("revision", "")
    title_fr = meta.get("title", "")
    last = max((d for d in dates if d), default="")
    commands = src.commands.get(doc_id, [])
    head = [
        "---",
        f"doc_id: {doc_id}",
        f"title_fr: {_yaml_str(title_fr)}",
        f"title_en: {_yaml_str(title_en)}",
        f"commands: [{', '.join(commands)}]",
        f"tier: {scope.tier}",
        f"doc_date: {date}",
        f"doc_revision: {revision}",
        f"doc_version_label: {meta.get('version_label', '')}",
        f"source: {gen.get('source_url') or ''}",
        f"source_sha256: {gen.get('source_sha256', '')}",
        f"french_text: _src/{doc_id}.fr.md",
        "copyright: EDF R&D",
        f"licence: {LICENCE}",
        f"licence_notice: {_yaml_str(meta.get('licence_notice', ''))}",
        f"checked_against_upstream: {src.upstream}",
        f"method: {method}",
        f"status: {'reviewed' if method == 'reviewed' else 'machine' if method else 'pending'}",
        f"translation_source: {', '.join(sorted(s for s in sources if s))}",
        f"translated_on: {last}",
        "chunks: {" + ", ".join(f"{k}: {v}" for k, v in counts.items()) + "}",
        f"scope: {_yaml_str(scope.reason or 'every chunk')}",
        "reviewed_by:",
        "reviewed_on:",
        "history:",
        f"  - {_yaml_str(f'{date}: French original, EDF R&D, revision {revision}.')}",
        "  - "
        + _yaml_str(
            f"{last or 'pending'}: unofficial English translation by codeaster-en "
            f"(caen translate doc, {method or 'not translated yet'})."
        ),
        f"generator: {TOOL} v{TOOL_VERSION}",
        "---",
        "",
        f"> **Unofficial English translation** of EDF R&D document {doc_id}, {_yaml_str(title_fr)}"
        f" ({date}, revision {revision}). The French original prevails. "
        f"Translation method: {method or 'none yet'}; not reviewed by an engineer unless "
        "`reviewed_by` is set above.",
        ">",
        "> Copyright EDF R&D; translation by the codeaster-en project. Permission is granted to "
        "copy, distribute and/or modify this document under the terms of the GNU Free "
        "Documentation License, Version 1.3 or any later version published by the Free "
        "Software Foundation; with no Invariant Sections, no Front-Cover Texts, and no "
        "Back-Cover Texts. A copy of the license is in "
        "[_src/LICENSE-GFDL-1.3.txt](_src/LICENSE-GFDL-1.3.txt). "
        f"Original notice: «{meta.get('licence_notice', '')}». Keyword names, values and "
        "syntax blocks are the solver's own and stay in French; where this document and the "
        f"catalog of code_aster {src.upstream} disagree, the catalog wins.",
        "",
    ]
    return "\n".join(head + body).rstrip() + "\n"


# ---------------------------------------------------------------- run


@dataclass
class DocReport:
    doc_id: str
    in_scope: int = 0
    pending: int = 0
    translated: int = 0
    failed: dict[int, list[str]] = field(default_factory=dict)
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    path: Path | None = None


def _title(doc: dict[str, Any]) -> str:
    return str(doc["meta"].get("title", ""))


def _store(chunk: Chunk, en: str, method: str, source: str, today: str) -> Stored:
    attrs = {"fr": chunk.sha, "method": method, "source": source.replace(" ", "_"), "on": today}
    return Stored(attrs, expand_code(en.strip(), chunk.code))


def translate_doc(
    src: Sources,
    doc_id: str,
    translator: DocTranslator | None,
    *,
    retries: int = 2,
    method: str = "machine",
    force: bool = False,
    only: frozenset[int] | None = None,
    today: str | None = None,
) -> DocReport:
    """Translate the pending in-scope chunks of one document and rewrite ``en/docs/<ID>.md``.

    With ``translator=None`` the document is only re-assembled (new header, pending and
    out-of-scope chunks rendered, stale chunks flagged).
    """
    if method not in METHODS:
        raise TranslateError(f"method must be one of {METHODS}, not {method!r}")
    if doc_id not in src.scope:
        raise TranslateError(f"{doc_id} is not in {SCOPE_RELPATH}")
    scope = src.scope[doc_id]
    doc = load_source(src.root, doc_id)
    chunks = chunks_of(doc)
    path = doc_path(src.root, doc_id)
    bodies = read_stored(path)
    today = today or dt.date.today().isoformat()
    report = DocReport(doc_id, path=path)
    system = system_prompt(src.terms)
    for chunk in chunks:
        if not scope.includes(chunk.id):
            continue
        report.in_scope += 1
        if not pending(chunk, bodies.get(chunk.id), force) or (only and chunk.id not in only):
            continue
        report.pending += 1
        if translator is None:
            continue
        problems: list[str] = []
        previous = ""
        for attempt in range(retries + 1):
            request = Request(
                doc_id,
                chunk.id,
                attempt,
                system,
                user_prompt(chunk, _title(doc), src, problems, previous),
            )
            answer = translator.translate(request)
            report.requests += 1
            report.input_tokens += answer.input_tokens
            report.output_tokens += answer.output_tokens
            if answer.error:
                problems = [answer.error]
                continue
            if answer.text is None:
                problems = ["no answer"]
                break
            problems = check_chunk(chunk, answer.text, src)
            if not problems:
                bodies[chunk.id] = _store(chunk, answer.text, method, translator.label, today)
                report.translated += 1
                break
            previous = answer.text
            if isinstance(translator, ReplayDocTranslator):
                break  # a file answers the same way every time
        if problems:
            report.failed[chunk.id] = problems
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(assemble(doc, scope, chunks, bodies, src), encoding="utf-8")
    return report


def export_requests(
    src: Sources, doc_id: str, out: Path, force: bool = False, only: frozenset[int] | None = None
) -> int:
    """Write ``<out>/<DOC-ID>/<chunk>.request.md`` for every pending in-scope chunk."""
    scope = src.scope.get(doc_id)
    if scope is None:
        raise TranslateError(f"{doc_id} is not in {SCOPE_RELPATH}")
    doc = load_source(src.root, doc_id)
    bodies = read_stored(doc_path(src.root, doc_id))
    target = out / doc_id
    count = 0
    for chunk in chunks_of(doc):
        if not scope.includes(chunk.id) or (only and chunk.id not in only):
            continue
        if not pending(chunk, bodies.get(chunk.id), force):
            continue
        target.mkdir(parents=True, exist_ok=True)
        (target / f"{chunk.id}.request.md").write_text(
            user_prompt(chunk, _title(doc), src), encoding="utf-8"
        )
        count += 1
    if count:
        (out / "SYSTEM.md").write_text(system_prompt(src.terms), encoding="utf-8")
    return count


@dataclass(frozen=True)
class Estimate:
    doc_id: str
    chunks: int
    french_chars: int
    input_tokens: int
    output_tokens: int
    cost_usd: float | None


def estimate(src: Sources, doc_id: str, model: str, force: bool = False) -> Estimate:
    """Token and cost estimate for the pending chunks (first attempt, no re-asks)."""
    scope = src.scope.get(doc_id)
    if scope is None:
        raise TranslateError(f"{doc_id} is not in {SCOPE_RELPATH}")
    doc = load_source(src.root, doc_id)
    bodies = read_stored(doc_path(src.root, doc_id))
    todo = [
        c for c in chunks_of(doc) if scope.includes(c.id) and pending(c, bodies.get(c.id), force)
    ]
    system_tokens = msg._tokens(system_prompt(src.terms)) if todo else 0
    user_tokens = sum(msg._tokens(user_prompt(c, _title(doc), src)) for c in todo)
    output_tokens = sum(msg._tokens(c.fr) for c in todo)
    cost = None
    if model in msg.PRICES and todo:
        price_in, price_out = msg.PRICES[model]
        system_cost = system_tokens * (
            msg.CACHE_WRITE_FACTOR + msg.CACHE_READ_FACTOR * (len(todo) - 1)
        )
        cost = ((system_cost + user_tokens) * price_in + output_tokens * price_out) / 1e6
    return Estimate(
        doc_id,
        len(todo),
        sum(len(c.fr) for c in todo),
        system_tokens * len(todo) + user_tokens,
        output_tokens,
        cost,
    )


# ---------------------------------------------------------------- validation


def validate_dir(root: Path) -> tuple[list[str], int, int]:
    """``(issues, documents, translated chunks)`` for every ``en/docs/<DOC-ID>.md``.

    Each translated chunk is checked against the current French: same chunk set, code blocks
    verbatim, and :func:`check_chunk` on the text. A chunk whose French changed (``stale``) is
    reported only when its marker does not say so.
    """
    src = load_sources(root)
    issues: list[str] = []
    files = sorted((root / DOCS_RELDIR).glob("*.md"))
    files = [p for p in files if ingest.DOC_ID.match(p.stem)]
    translated = 0
    for path in files:
        doc_id = path.stem
        rel = path.relative_to(root)
        if doc_id not in src.scope:
            issues.append(f"{rel}: {doc_id} is not in {SCOPE_RELPATH}")
            continue
        chunks = {c.id: c for c in chunks_of(load_source(root, doc_id))}
        stored = read_stored(path)
        if set(stored) != set(chunks):
            issues.append(f"{rel}: chunk markers {sorted(stored)} != French chunks")
            continue
        for number, item in stored.items():
            chunk = chunks[number]
            if not _translated(item):
                continue
            translated += 1
            if item.attrs.get("method") not in (*METHODS, "reviewed"):
                issues.append(f"{rel}: chunk {number}: bad method {item.attrs.get('method')!r}")
            if item.attrs.get("fr") != chunk.sha and item.attrs.get("stale") != "1":
                issues.append(f"{rel}: chunk {number}: French changed; not marked stale")
            if item.attrs.get("fr") != chunk.sha:
                continue
            text, code = collapse_code(item.body)
            if tuple(code) != chunk.code:
                issues.append(f"{rel}: chunk {number}: code blocks differ from the French")
            for problem in check_chunk(chunk, text, src):
                issues.append(f"{rel}: chunk {number}: {problem}")
    return issues, len(files), translated
