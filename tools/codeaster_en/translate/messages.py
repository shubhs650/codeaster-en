"""``caen translate messages``: glossary-locked batch translation of ``en/messages/*.en.json``.

Task 3.1 (TRANSLATION-GUIDE.md §3 and §6, ADR-004, ADR-014). One run handles one or more
message families:

1. **Seed** (``seed_po=True``): a message whose French text is a ``msgid`` of upstream's 2016
   ``i18n/en-US/aster_messages.po`` *verbatim* takes its ``msgstr`` as ``method: machine``,
   ``translation_source: upstream:i18n/en-US/aster_messages.po``, if it passes the same checks
   as a model answer (placeholders, forbidden synonyms). No model is called.
2. **Translate** the remaining messages (``en`` null, or ``stale``) in batches. Each request
   carries the rules, the glossary (all ``term``/``abbrev`` entries in the cached system
   prompt, plus the ``command``/``keyword``/``value``/``concept`` entries whose French appears
   in the batch), the items as JSON (``id``, ``fr``, ``placeholders`` and, when the ``.po``
   has the message after whitespace normalisation, its dated English as ``upstream_en``), and
   a JSON output schema. Every answer is checked: the placeholder set must equal the French
   one exactly (:func:`codeaster_en.placeholders.compare`) and no forbidden synonym
   (``aliases_en``) of a glossary entry whose French occurs in the message may appear. Failed
   items are asked again, alone, with the problems listed, up to ``retries`` times; what still
   fails stays null and is reported.
3. **Write** after every batch (atomic rename), so an interrupted run resumes where it stopped:
   translated messages are skipped on the next run.

Severity hints are not asked from the model; they are inferred from the French wording by
:func:`severity_hint` (TRANSLATION-GUIDE.md §3.5) and are hints only: the real severity is the
``<A>``/``<E>``/``<F>`` tag in the ``.mess`` log.

Translators (backends) implement :class:`Translator`:

- :class:`AnthropicTranslator` calls the Claude API (``pip install 'codeaster_en[llm]'``,
  credentials from the environment). It spends the owner's API budget: CLAUDE.md §3 and
  ADR-010 make bulk runs an owner decision.
- :class:`ReplayTranslator` reads answers from a JSON Lines file. It is how tests run, and how
  an in-session agent translates without an API key: export the requests
  (:func:`export_requests`), answer them, then import the answers.

Glossary additions proposed by the model are never applied to other items; they are appended to
``en/glossary.yaml`` as ``status: proposed`` entries when their French is not there yet.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import yaml

from codeaster_en import placeholders
from codeaster_en.extract.messages import SUFFIX, render
from codeaster_en.translate import po
from codeaster_en.validate import glossary as glossary_validator
from codeaster_en.validate import synonyms

MESSAGES_RELDIR = Path("en/messages")
GLOSSARY_RELPATH = Path("en/glossary.yaml")
METHODS = ("machine", "assisted")  # "reviewed" is set by the owner only (CLAUDE.md §3)

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "medium"
DEFAULT_BATCH_SIZE = 20
DEFAULT_RETRIES = 2
MAX_TOKENS = 16000

# USD per million tokens (input, output), Anthropic first-party list prices cached 2026-10-06.
# Used for the dry-run estimate only; check the price page before a bulk run.
PRICES: dict[str, tuple[float, float]] = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}
CACHE_WRITE_FACTOR = 1.25
CACHE_READ_FACTOR = 0.10
CHARS_PER_TOKEN = 3.0  # conservative for French text and JSON; no tokenizer offline
OUTPUT_OVERHEAD_TOKENS = 15  # per item: {"id": ..., "en": ...} framing
ANSWER_CHARS_FACTOR = 1.0  # English text is about as long as the French

GLOSSARY_IN_SYSTEM = frozenset({"term", "abbrev"})
ADDITION_KINDS = sorted(glossary_validator.KINDS)

SYSTEM_RULES = """\
You translate code_aster solver messages from French to English for structural engineers.
code_aster is EDF's finite element solver. Each message is a Python %-format string that the
solver fills with a mapping and prints inside a box in the .mess log.

Rules:
1. Placeholders are sacred. Every specifier in the French (%(k1)s, %(i1)d, %(r1)f, %(r1)12.5E,
   %(k1)-8s, and the literal %%) must appear in your English with exactly the same characters.
   You may reorder them for English word order. Never rename, drop or add one, and never add
   a bare % sign (write "percent" or %% if the French has %%).
2. Keep line breaks and leading spaces where the French uses them for layout and lists. Keep
   leading and trailing newlines as they are.
3. Keep the register: short, direct, imperative where the French is. Do not soften errors and
   do not add explanations that are not in the French.
4. Translate the meaning, not the words. "Le concept %(k1)s n'existe pas" is
   "Result object %(k1)s does not exist", not "The concept ... does not exist".
5. Command names, keyword names and keyword values written in capitals (AFFE_MODELE,
   GROUP_MA, PRES_REP, 'OUI', 'NON') are the solver's API: copy them verbatim, including
   inside quotes. Never translate or rename them.
6. Use the glossary: when a French term has an entry, use its English, every time. Never use
   a word listed as forbidden for it. Plain American English, SI unit names.
7. If a French term you need has no entry and is a code_aster concept a reader would look up,
   propose it in glossary_additions (fr, en, kind, note). Do not invent solver behavior in a
   note; say what the word means in the message.
8. upstream_en, when given, is a dated 2016 community translation of the same text. Use it
   only as a hint; it is often too literal and it ignores the glossary (it says "mesh" for
   "maille", which is "element").
9. Answer with JSON only, matching the schema: one translation for every input id.
"""

OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "translations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "en": {"type": "string"}},
                "required": ["id", "en"],
                "additionalProperties": False,
            },
        },
        "glossary_additions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "fr": {"type": "string"},
                    "en": {"type": "string"},
                    "kind": {"type": "string", "enum": ADDITION_KINDS},
                    "note": {"type": "string"},
                },
                "required": ["fr", "en", "kind", "note"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["translations", "glossary_additions"],
    "additionalProperties": False,
}


class TranslateError(RuntimeError):
    """A run cannot start or a backend failed in a way that is not one item's fault."""


# ---------------------------------------------------------------- severity hint


def _fold(text: str) -> str:
    """Lower case without accents, for wording rules."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


_SEVERITY_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("fatal", re.compile(r"\bfatales?\b|\barret du code\b")),
    ("error", re.compile(r"\berreurs?\b|\bimpossibles?\b|\barrets?\b")),
    ("warning", re.compile(r"\balarmes?\b|\battention\b|\bon continue\b")),
)


def severity_hint(fr: str) -> str:
    """``fatal`` | ``error`` | ``warning`` | ``info`` from the French wording (most severe wins).

    TRANSLATION-GUIDE.md §3.5: *fatale*, *arrêt du code* → fatal; *erreur*, *impossible*,
    *arrêt* → error; *alarme*, *attention*, *on continue* → warning; otherwise info.
    """
    folded = _fold(fr)
    for level, pattern in _SEVERITY_RULES:
        if pattern.search(folded):
            return level
    return "info"


# ---------------------------------------------------------------- glossary


@dataclass(frozen=True)
class Term:
    fr: str
    en: str
    kind: str
    note: str
    pattern: re.Pattern[str]
    forbidden: tuple[synonyms.Alias, ...]


def _fr_pattern(fr: str) -> re.Pattern[str]:
    """Where a glossary ``fr`` occurs in a message: identifiers exactly, words loosely."""
    if fr.upper() == fr and re.search(r"[A-Z]", fr):
        return re.compile(rf"(?<![\w]){re.escape(fr)}(?![\w])")
    words = r"\s+".join(re.escape(w) for w in fr.split())
    return re.compile(rf"(?<!\w){words}(?:e?s|x)?(?!\w)", re.IGNORECASE)


def load_terms(glossary_path: Path) -> list[Term]:
    entries = glossary_validator.load(glossary_path)
    alias_by_fr: dict[str, list[synonyms.Alias]] = {}
    for alias in synonyms.aliases(entries):
        alias_by_fr.setdefault(alias.fr, []).append(alias)
    terms = []
    for entry in entries:
        fr = str(entry["fr"])
        terms.append(
            Term(
                fr=fr,
                en=str(entry["en"]),
                kind=str(entry["kind"]),
                note=str(entry.get("note") or ""),
                pattern=_fr_pattern(fr),
                forbidden=tuple(alias_by_fr.get(fr, ())),
            )
        )
    return terms


def _term_line(term: Term) -> str:
    line = f"- {term.fr} = {term.en} ({term.kind})"
    if term.forbidden:
        line += "; never: " + ", ".join(a.alias for a in term.forbidden)
    if term.note:
        line += f". {term.note}"
    return line


def relevant_terms(terms: Iterable[Term], texts: Iterable[str]) -> list[Term]:
    """Terms whose French occurs in any of ``texts``."""
    joined = "\n".join(texts)
    return [t for t in terms if t.pattern.search(joined)]


def glossary_problems(fr: str, en: str, terms: Iterable[Term]) -> list[str]:
    """Forbidden synonyms in ``en`` of glossary terms that occur in ``fr``."""
    problems = []
    for term in relevant_terms((t for t in terms if t.forbidden), [fr]):
        for alias in term.forbidden:
            for match in alias.pattern.finditer(en):
                if not match.group(0).isupper():
                    problems.append(
                        f"uses {match.group(0)!r}; the glossary says {term.fr!r} is "
                        f"{term.en!r}, never {alias.alias!r}"
                    )
                    break
    return problems


# ---------------------------------------------------------------- requests


@dataclass(frozen=True)
class Item:
    id: str
    fr: str
    placeholders: tuple[str, ...]
    upstream_en: str | None = None
    problems: tuple[str, ...] = ()

    def as_prompt(self) -> dict[str, Any]:
        data: dict[str, Any] = {"id": self.id, "fr": self.fr, "placeholders": self.placeholders}
        if self.upstream_en:
            data["upstream_en"] = self.upstream_en
        if self.problems:
            data["previous_answer_problems"] = list(self.problems)
        return data


@dataclass(frozen=True)
class Request:
    family: str
    batch: int
    attempt: int
    system: str
    user: str
    items: tuple[Item, ...]

    def as_json(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "batch": self.batch,
            "attempt": self.attempt,
            "ids": [i.id for i in self.items],
            "system": self.system,
            "user": self.user,
            "schema": OUTPUT_SCHEMA,
        }


def system_prompt(terms: Iterable[Term]) -> str:
    """Rules plus every ``term``/``abbrev`` entry: the same for every batch (cacheable)."""
    lines = [_term_line(t) for t in terms if t.kind in GLOSSARY_IN_SYSTEM]
    return (
        SYSTEM_RULES + "\nGlossary (general terms and abbreviations):\n" + "\n".join(lines) + "\n"
    )


def user_prompt(family: str, items: Iterable[Item], terms: Iterable[Term]) -> str:
    items = list(items)
    specific = [
        t for t in relevant_terms(terms, [i.fr for i in items]) if t.kind not in GLOSSARY_IN_SYSTEM
    ]
    parts = [f"Message family {family}."]
    if specific:
        parts.append(
            "Glossary entries for names in these messages:\n"
            + "\n".join(_term_line(t) for t in specific)
        )
    if any(i.problems for i in items):
        parts.append(
            "These messages were translated before and the answer was rejected; "
            "previous_answer_problems says why. Fix exactly that."
        )
    parts.append(
        "Translate these messages:\n"
        + json.dumps([i.as_prompt() for i in items], ensure_ascii=False, indent=1)
    )
    return "\n\n".join(parts) + "\n"


# ---------------------------------------------------------------- translators


@dataclass
class Answer:
    translations: dict[str, str]
    glossary_additions: list[dict[str, Any]] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None  # the whole request failed (refusal, truncated, unparsable)


class Translator(Protocol):
    label: str  # recorded as translation_source

    def translate(self, request: Request) -> Answer: ...


def parse_answer(text: str) -> Answer:
    """An :class:`Answer` from the JSON text of a model reply (schema :data:`OUTPUT_SCHEMA`)."""
    try:
        data = json.loads(text)
    except ValueError as exc:
        return Answer({}, error=f"reply is not JSON: {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("translations"), list):
        return Answer({}, error="reply has no 'translations' list")
    found: dict[str, str] = {}
    for row in data["translations"]:
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            if isinstance(row.get("en"), str):
                found[row["id"]] = row["en"]
    additions = [a for a in data.get("glossary_additions") or [] if isinstance(a, dict)]
    return Answer(found, additions)


class AnthropicTranslator:
    """Claude API backend. Needs the ``anthropic`` package and credentials in the environment."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        effort: str = DEFAULT_EFFORT,
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
            output_config={
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
            },
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        usage = getattr(response, "usage", None)
        tokens = {
            "input_tokens": getattr(usage, "input_tokens", 0) or 0,
            "output_tokens": getattr(usage, "output_tokens", 0) or 0,
        }
        if response.stop_reason == "refusal":
            return Answer({}, error="the model declined the request (refusal)", **tokens)
        if response.stop_reason == "max_tokens":
            return Answer({}, error="reply cut off at max_tokens; use a smaller batch", **tokens)
        text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
        answer = parse_answer(text)
        answer.input_tokens, answer.output_tokens = tokens["input_tokens"], tokens["output_tokens"]
        return answer


class ReplayTranslator:
    """Answers read from a JSON Lines file.

    Each line is either one translation ``{"id": ..., "en": ...}`` or a whole reply
    ``{"translations": [...], "glossary_additions": [...]}``. Lines starting with ``#`` and
    blank lines are ignored. The same id given twice keeps the last answer.
    """

    def __init__(self, path: Path, label: str | None = None) -> None:
        self.answers: dict[str, str] = {}
        self.additions: list[dict[str, Any]] = []
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                data = json.loads(line)
            except ValueError as exc:
                raise TranslateError(f"{path}:{number}: not JSON: {exc}") from exc
            if isinstance(data, dict) and "translations" in data:
                parsed = parse_answer(line)
                self.answers.update(parsed.translations)
                self.additions.extend(parsed.glossary_additions)
            elif isinstance(data, dict) and isinstance(data.get("id"), str):
                if not isinstance(data.get("en"), str):
                    raise TranslateError(f"{path}:{number}: 'en' must be a string")
                self.answers[data["id"]] = data["en"]
            else:
                raise TranslateError(f"{path}:{number}: expected an {{id, en}} object")
        self.label = label or f"replay:{path.name}"
        self._given_additions = False

    def translate(self, request: Request) -> Answer:
        found = {i.id: self.answers[i.id] for i in request.items if i.id in self.answers}
        additions: list[dict[str, Any]] = []
        if not self._given_additions:
            additions, self._given_additions = self.additions, True
        return Answer(found, additions)


# ---------------------------------------------------------------- run


@dataclass
class FamilyReport:
    family: str
    pending: int = 0
    seeded: int = 0
    translated: int = 0
    failed: dict[str, list[str]] = field(default_factory=dict)
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    glossary_added: list[str] = field(default_factory=list)


@dataclass
class Sources:
    root: Path
    terms: list[Term]
    upstream_po: dict[str, str]

    po_normalized: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.po_normalized:
            self.po_normalized = {_squash(k): v for k, v in self.upstream_po.items()}


def _squash(text: str) -> str:
    return " ".join(text.split())


def load_sources(root: Path) -> Sources:
    po_path = root / "upstream" / po.PO_RELPATH
    return Sources(
        root=root,
        terms=load_terms(root / GLOSSARY_RELPATH),
        upstream_po=po.load(po_path) if po_path.is_file() else {},
    )


def family_path(root: Path, family: str) -> Path:
    path = root / MESSAGES_RELDIR / f"{family.upper()}{SUFFIX}"
    if not path.is_file():
        raise TranslateError(f"no message family {family!r} ({path} not found)")
    return path


def all_families(root: Path) -> list[str]:
    return sorted(p.name[: -len(SUFFIX)] for p in (root / MESSAGES_RELDIR).glob(f"*{SUFFIX}"))


def _write(path: Path, doc: dict[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(render(doc), encoding="utf-8")
    os.replace(tmp, path)


def pending_messages(doc: dict[str, Any], force: bool = False) -> list[dict[str, Any]]:
    """Messages to translate: no English yet, or English older than the French (``stale``).

    ``force`` adds every other message except ``reviewed`` ones, which only the owner changes.
    """
    return [
        m
        for m in doc["messages"].values()
        if m.get("en") is None or m.get("stale") or (force and m.get("method") != "reviewed")
    ]


def _store(msg: dict[str, Any], en: str, method: str, source: str) -> None:
    msg["en"] = en
    msg["method"] = method
    msg["severity_hint"] = severity_hint(msg["fr"])
    msg["translation_source"] = source
    msg.pop("stale", None)
    for key in ("reviewed_by", "reviewed_on"):
        msg.pop(key, None)


def check(msg: dict[str, Any], en: str, terms: list[Term]) -> list[str]:
    """Why ``en`` is not acceptable for ``msg`` (empty list = accepted)."""
    if not en.strip() and msg["fr"].strip():
        return ["empty translation"]
    return placeholders.compare(msg["fr"], en) + glossary_problems(msg["fr"], en, terms)


def _seedable(msg: dict[str, Any], src: Sources) -> str | None:
    """The ``.po`` English of ``msg``: its French is a verbatim msgid and :func:`check` passes."""
    en = src.upstream_po.get(msg["fr"])
    if en is None or check(msg, en, src.terms):
        return None
    return en


def seed_from_po(doc: dict[str, Any], src: Sources, force: bool = False) -> set[str]:
    """Fill pending messages whose French is a verbatim ``.po`` msgid. Returns their ids."""
    seeded = set()
    for msg in pending_messages(doc, force):
        en = _seedable(msg, src)
        if en is not None and msg.get("method") in (None, "machine"):
            _store(msg, en, "machine", po.SOURCE_LABEL)
            seeded.add(msg["id"])
    return seeded


def _todo(
    doc: dict[str, Any], src: Sources, force: bool, seed_po: bool, limit: int | None
) -> list[dict[str, Any]]:
    """Messages the model is asked for: pending ones, minus those the seed step fills."""
    todo = pending_messages(doc, force)
    if seed_po:
        todo = [
            m for m in todo if _seedable(m, src) is None or m.get("method") not in (None, "machine")
        ]
    return todo if limit is None else todo[:limit]


def _items(msgs: Iterable[dict[str, Any]], src: Sources) -> list[Item]:
    normalized = src.po_normalized
    return [
        Item(
            id=m["id"],
            fr=m["fr"],
            placeholders=tuple(m["placeholders"]),
            upstream_en=normalized.get(_squash(m["fr"])),
        )
        for m in msgs
    ]


def _chunks(items: list[Item], size: int) -> list[list[Item]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def build_requests(
    family: str, items: list[Item], src: Sources, batch_size: int, system: str | None = None
) -> list[Request]:
    system = system if system is not None else system_prompt(src.terms)
    return [
        Request(family, n, 0, system, user_prompt(family, chunk, src.terms), tuple(chunk))
        for n, chunk in enumerate(_chunks(items, batch_size), start=1)
    ]


def _upstream_line(src: Sources, rel: str | None, fr: str) -> str | None:
    """``<file>:<line>`` of the first line of upstream ``rel`` containing ``fr`` literally."""
    path = src.root / "upstream" / rel if rel else None
    if path is None or not path.is_file():
        return None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if fr in line:
            return f"{rel}:{number}"
    return None


def _append_glossary(
    src: Sources, additions: list[dict[str, Any]], source_file: str | None = None
) -> list[str]:
    """Append new ``status: proposed`` entries; returns the French of those written.

    ``source`` is set to the first line of the family's upstream file that contains the French
    literally (the convention ``tests/test_glossary_coverage.py`` checks), or left out.
    """
    path = src.root / GLOSSARY_RELPATH
    known = {t.fr for t in src.terms}
    lines = []
    added = []
    for raw in additions:
        fr, en = str(raw.get("fr") or "").strip(), str(raw.get("en") or "").strip()
        kind = raw.get("kind")
        if not fr or not en or fr in known or kind not in glossary_validator.KINDS:
            continue
        entry = {
            "fr": fr,
            "en": en,
            "kind": kind,
            "note": str(raw.get("note") or "").strip(),
        }
        where = _upstream_line(src, source_file, fr)
        if where:
            entry["source"] = where
        entry["status"] = "proposed"
        dumped = yaml.safe_dump(entry, allow_unicode=True, default_flow_style=True, sort_keys=False)
        lines.append("- " + " ".join(dumped.split()))
        known.add(fr)
        added.append(fr)
    if lines:
        text = path.read_text(encoding="utf-8")
        marker = "# proposed by caen translate messages (task 3.1); review before use"
        if marker not in text:
            text = text.rstrip("\n") + "\n" + marker + "\n"
        path.write_text(text.rstrip("\n") + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
        src.terms = load_terms(path)
    return added


def translate_family(
    src: Sources,
    family: str,
    translator: Translator | None,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    retries: int = DEFAULT_RETRIES,
    method: str = "machine",
    seed_po: bool = False,
    force: bool = False,
    limit: int | None = None,
) -> FamilyReport:
    """Seed and/or translate one family in place. ``translator=None`` only seeds."""
    if method not in METHODS:
        raise TranslateError(f"method must be one of {METHODS}, got {method!r}")
    path = family_path(src.root, family)
    doc = json.loads(path.read_text(encoding="utf-8"))
    family = doc["family"]
    report = FamilyReport(family)
    todo = _todo(doc, src, force, seed_po, limit)
    if seed_po:
        report.seeded = len(seed_from_po(doc, src, force))
        if report.seeded:
            _write(path, doc)
    if translator is None:
        return report
    by_id = {m["id"]: m for m in doc["messages"].values()}
    report.pending = len(todo)
    system = system_prompt(src.terms)
    for request in build_requests(family, _items(todo, src), src, batch_size, system):
        queue = list(request.items)
        problems: dict[str, list[str]] = {}
        for attempt in range(retries + 1):
            if not queue:
                break
            current = Request(
                family,
                request.batch,
                attempt,
                system,
                user_prompt(family, queue, src.terms),
                tuple(queue),
            )
            answer = translator.translate(current)
            report.requests += 1
            report.input_tokens += answer.input_tokens
            report.output_tokens += answer.output_tokens
            if answer.glossary_additions:
                report.glossary_added += _append_glossary(
                    src, answer.glossary_additions, doc["source"]["file"]
                )
            retry: list[Item] = []
            for item in queue:
                en = answer.translations.get(item.id)
                if en is None:
                    found = [answer.error or "no translation returned for this id"]
                else:
                    found = check(by_id[item.id], en, src.terms)
                if found:
                    problems[item.id] = found
                    retry.append(
                        Item(item.id, item.fr, item.placeholders, item.upstream_en, tuple(found))
                    )
                else:
                    problems.pop(item.id, None)
                    _store(by_id[item.id], en, method, translator.label)
                    report.translated += 1
            _write(path, doc)
            queue = retry
        report.failed.update(problems)
    return report


# ---------------------------------------------------------------- dry run / export


@dataclass
class Estimate:
    family: str
    items: int
    requests: int
    input_tokens: int
    output_tokens: int
    cost_usd: float | None


def _tokens(text: str) -> int:
    return int(len(text) / CHARS_PER_TOKEN) + 1


def estimate(
    src: Sources,
    family: str,
    model: str,
    batch_size: int,
    force: bool = False,
    seed_po: bool = False,
    limit: int | None = None,
) -> Estimate:
    """Token and cost estimate for translating one family (first attempt, no re-asks).

    Tokens are counted as characters / :data:`CHARS_PER_TOKEN` (no tokenizer offline). Thinking
    tokens are not included. The system prompt is billed as a cache write on the first request
    and a cache read on the others (``cache_control`` on the system block).
    """
    doc = json.loads(family_path(src.root, family).read_text(encoding="utf-8"))
    todo = _todo(doc, src, force, seed_po, limit)
    requests = build_requests(doc["family"], _items(todo, src), src, batch_size)
    system_tokens = _tokens(requests[0].system) if requests else 0
    user_tokens = sum(_tokens(r.user) for r in requests)
    output_tokens = sum(
        int(_tokens(i.fr) * ANSWER_CHARS_FACTOR) + OUTPUT_OVERHEAD_TOKENS
        for r in requests
        for i in r.items
    )
    input_tokens = system_tokens * len(requests) + user_tokens
    cost = None
    if model in PRICES and requests:
        price_in, price_out = PRICES[model]
        system_cost = system_tokens * (CACHE_WRITE_FACTOR + CACHE_READ_FACTOR * (len(requests) - 1))
        cost = ((system_cost + user_tokens) * price_in + output_tokens * price_out) / 1e6
    return Estimate(doc["family"], len(todo), len(requests), input_tokens, output_tokens, cost)


def export_requests(
    src: Sources,
    family: str,
    out: Path,
    batch_size: int,
    force: bool = False,
    seed_po: bool = False,
    limit: int | None = None,
) -> int:
    """Append the first-attempt requests of one family to ``out`` (JSON Lines). Returns count."""
    doc = json.loads(family_path(src.root, family).read_text(encoding="utf-8"))
    todo = _todo(doc, src, force, seed_po, limit)
    requests = build_requests(doc["family"], _items(todo, src), src, batch_size)
    with out.open("a", encoding="utf-8") as handle:
        for request in requests:
            handle.write(json.dumps(request.as_json(), ensure_ascii=False) + "\n")
    return len(requests)
