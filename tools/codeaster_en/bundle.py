"""``caen bundle``: one Markdown file for a coding agent's context window (task 5.5, ADR-025).

The bundle concatenates, in reading order:

1. a short preamble: what the bundle is, the rules for writing a ``.comm`` with it, and a
   table of contents with the line number where each section starts (an agent reads a file
   this size in parts, by offset);
2. the engineers' guide ``en/guide/``, in the order of its index page;
3. the English command references ``en/commands/<CMD>.md`` of the requested tier(s), in
   ``docs/COMMAND-SET.md`` order (``--tier 2`` means Tiers 1 and 2);
4. the glossary ``en/glossary.yaml`` as compact tables, one per ``kind``.

Every source file is included whole, with three mechanical changes and nothing else
rewritten: its front matter becomes one provenance line (path, status, method, upstream,
French doc ID), its "Assisted reference / Machine draft / Assisted guide" banner is dropped
(the preamble states it once), and its headings move down two levels under the bundle's
part headings. Relative Markdown links are rewritten to repository paths
(``en/commands/MECA_STATIQUE.md``), which is also how each included file is labelled, so a
reader can follow a link by searching for the path.

Size is estimated, not measured: :data:`CHARS_PER_TOKEN` is a deliberately low
characters-per-token ratio for this text (French identifiers, tables and code tokenize worse
than prose; ADR-025 records the calibration). ``--max-tokens`` makes the build fail above the
budget (PLAN 5.5: < ~150k tokens).

The output is deterministic (no date): the same checkout gives the same bytes.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from codeaster_en import __version__
from codeaster_en.extract import inventory
from codeaster_en.validate import glossary as glossary_validator

GUIDE_RELDIR = Path("en/guide")
COMMANDS_RELDIR = Path("en/commands")
GLOSSARY_RELPATH = Path("en/glossary.yaml")
COMMAND_SET_RELPATH = Path("docs/COMMAND-SET.md")
UPSTREAM_RELPATH = Path("UPSTREAM_VERSION")

CHARS_PER_TOKEN = 1.95
DEFAULT_MAX_TOKENS = 150_000
DETAILS = ("compact", "full")

# Compact detail (the default): what a command reference keeps, and which guide pages go.
COMPACT_DROP_SECTIONS = ("See also", "Other keywords", "What the solver does")
COMPACT_DROP_GUIDE = ("README.md", "reading-logs.md", "reading-results.md", "fields.md")
COMPACT_MAX_PATTERNS = 2  # the authors list the fixtures' and the commonest patterns first
GUIDE_MIN_TIER = {"walkthrough-modal.md": "2"}  # pages about a higher tier's commands
COMPACT_GLOSSARY_KINDS = ("abbrev", "term")
RULE_LIST_MAX = 12  # longer keyword lists in a rule are cut to the keywords in the table
_OUT_OF_SCOPE = re.compile(r"\b[Oo]ut of (?:Tier 1 )?scope\b")
_RULE = re.compile(r"^- (?:command:|when `|`[A-Z][A-Z0-9_]*`:)")  # a generated catalog rule
_NOT_SENTENCE_END = ("e.g.", "i.e.", "cf.", "vs.", "etc.", "approx.", "resp.", "no.")
KIND_ORDER = ("abbrev", "term", "concept", "command", "keyword", "value")
KIND_TITLES = {
    "abbrev": "Abbreviations inside identifiers",
    "term": "Terms",
    "concept": "Concepts and component names",
    "command": "Commands",
    "keyword": "Keywords",
    "value": "Keyword values",
}

_FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)
_BANNER = re.compile(
    r"^> \*\*(?:Assisted reference|Machine draft|Assisted guide|Reviewed reference)\.\*\*"
)
_HEADING = re.compile(r"^(#{1,6}) ")
_FENCE = re.compile(r"^\s*(```|~~~)")
_LINK = re.compile(r"(\]\()([^)\s#]+\.md)(#[^)\s]*)?(\))")


class BundleError(ValueError):
    pass


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / CHARS_PER_TOKEN)


@dataclass
class Section:
    title: str
    path: str  # repo-relative, or "" for generated sections
    lines: list[str] = field(default_factory=list)
    level: int = 2  # heading level of the section's first line in the bundle


@dataclass
class Bundle:
    tier: str
    text: str
    sections: list[Section]
    commands: list[str]
    missing: list[str]  # tier commands with no en/commands/<CMD>.md (e.g. POURSUITE)

    @property
    def tokens(self) -> int:
        return estimate_tokens(self.text)


# --------------------------------------------------------------------------------------
# Sources


def tier_commands(repo: Path, tier: str) -> tuple[list[str], dict[str, set[str]]]:
    """Commands of Tiers 1..``tier`` in COMMAND-SET order, each once, and each command's
    "key keywords" (the COMMAND-SET column, over every row the command appears in)."""
    if tier not in ("1", "2", "3"):
        raise BundleError(f"tier must be 1, 2 or 3, not {tier!r}")
    known = {p.stem for p in (repo / COMMANDS_RELDIR).glob("*.json")} | {"POURSUITE"}
    command_set = inventory.parse_command_set(
        (repo / COMMAND_SET_RELPATH).read_text(encoding="utf-8"), known
    )
    names: list[str] = []
    key: dict[str, set[str]] = {}
    for wanted in [str(t) for t in range(1, int(tier) + 1)]:
        for row in command_set.rows:
            if row.tier == wanted:
                names += [n for n in row.commands if n not in names]
                for name in row.commands:
                    key.setdefault(name, set()).update(row.key_keywords)
    return names, key


def guide_pages(repo: Path) -> list[Path]:
    """``en/guide/*.md``: the index, then the pages in the order it links them, then the rest."""
    guide = repo / GUIDE_RELDIR
    index = guide / "README.md"
    if not index.is_file():
        raise BundleError(f"{index}: missing")
    order = [index]
    for target in _LINK.findall(index.read_text(encoding="utf-8")):
        page = (guide / target[1]).resolve()
        if page.parent == guide.resolve() and page.is_file() and page not in order:
            order.append(page)
    order += sorted(p for p in guide.glob("*.md") if p.resolve() not in order)
    return [p.resolve() for p in order]


def upstream_pin(repo: Path) -> str:
    path = repo / UPSTREAM_RELPATH
    if not path.is_file():
        return "unknown"
    lines = (ln.strip() for ln in path.read_text(encoding="utf-8").splitlines())
    return next((ln for ln in lines if ln and not ln.startswith("#")), "unknown")


# --------------------------------------------------------------------------------------
# One Markdown file → one section


def _front_matter(text: str) -> tuple[dict, str]:
    match = _FRONT.match(text)
    if not match:
        return {}, text
    data = yaml.safe_load(match.group(1)) or {}
    return (data if isinstance(data, dict) else {}), text[match.end() :]


def provenance_line(path: str, meta: dict, detail: str = "full") -> str:
    """The one line that replaces a page's front matter. ``compact`` leaves out the commit and
    the catalog path (the page itself has both)."""
    parts = [f"`{path}`"]
    status = meta.get("status")
    method = meta.get("method")
    if status:
        parts.append(f"status {status}" + (f" ({method})" if method and method != status else ""))
    if meta.get("reviewed_by"):
        parts.append(f"reviewed by {meta['reviewed_by']} on {meta.get('reviewed_on') or '?'}")
    if meta.get("upstream"):
        commit = str(meta.get("upstream_commit") or "")[:7] if detail == "full" else ""
        parts.append(f"upstream {meta['upstream']}" + (f" ({commit})" if commit else ""))
    if meta.get("source") and detail == "full":
        parts.append(f"catalog `{meta['source']}`")
    doc_fr = meta.get("doc_fr")
    if doc_fr and not str(doc_fr).startswith("none"):
        parts.append(f"French doc {doc_fr}")
    return "*Source: " + " · ".join(parts) + "*"


def _drop_banner(lines: list[str]) -> list[str]:
    """Remove the leading ``> **Assisted reference.** …`` blockquote (and one blank after)."""
    for i, line in enumerate(lines):
        if _BANNER.match(line):
            end = i
            while end < len(lines) and lines[end].startswith(">"):
                end += 1
            if end < len(lines) and not lines[end].strip():
                end += 1
            return lines[:i] + lines[end:]
    return lines


def _rewrite_link(match: re.Match[str], source_dir: Path, repo: Path) -> str:
    target = match.group(2)
    if "://" in target or target.startswith("/"):
        return match.group(0)
    resolved = (source_dir / target).resolve()
    try:
        rel = resolved.relative_to(repo.resolve()).as_posix()
    except ValueError:
        return match.group(0)
    return f"{match.group(1)}{rel}{match.group(3) or ''}{match.group(4)}"


def first_sentence(text: str) -> str:
    """``text`` up to its first sentence end outside code spans (``e.g.``, ``0.5`` don't end it)."""
    in_code = False
    for i, char in enumerate(text):
        if char == "`":
            in_code = not in_code
        elif char in ".!?" and not in_code and (i + 1 == len(text) or text[i + 1] == " "):
            word = text[: i + 1].rsplit(" ", 1)[-1].lower()
            if word.lstrip("(*") in _NOT_SENTENCE_END:
                continue
            return text[: i + 1]
    return text


def compact_meaning(text: str) -> str:
    """A keyword's meaning cut to the glossary term and the allowed values.

    The cell starts with what ``caen translate command`` generated (task 2.2): ``*term*.``,
    then ``One of …`` or ``Range: …``, and ``Only when …`` (the bloc condition, which the rules
    and patterns cover); the authored text follows. Only the term and the values are kept.
    """
    kept: list[str] = []
    rest = text.strip()
    while rest:
        sentence = first_sentence(rest)
        rest = rest[len(sentence) :].strip()
        if (sentence.startswith("*") and sentence.endswith("*.")) or sentence.startswith(
            ("One of ", "Range: ")
        ):
            kept.append(sentence)
    return " ".join(kept)


def _row_cells(line: str) -> list[str]:
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]


def _row_keywords(cell: str) -> list[str]:
    """``EXCIT / CHARGE`` → [EXCIT, CHARGE]; a cell may hold several code spans."""
    return re.findall(r"[A-Z][A-Z0-9_]*", " ".join(re.findall(r"`([^`]*)`", cell)))


def _compact_row(line: str, key: set[str]) -> str | None:
    """A keyword-table row with its meaning cut to the glossary term and the allowed values
    (:func:`compact_meaning`), or ``None`` when the row is left out: its author marked it out
    of scope, or it is a keyword nested under a factor keyword that is neither one of the
    command's COMMAND-SET key keywords nor required."""
    if _OUT_OF_SCOPE.search(line):
        return None
    cells = _row_cells(line)
    if len(cells) < 3:
        return line
    if " / " in cells[0] and not set(_row_keywords(cells[0])) & key and "required" not in cells[1]:
        return None
    return "| " + " | ".join([*cells[:-1], compact_meaning(cells[-1])]) + " |"


def _rule_keywords(line: str) -> set[str]:
    """Keywords a rule bullet constrains: the code spans after its scope (``command:`` or
    ``when …:``)."""
    body = line.split("`:", 1)[1] if line.startswith("- when ") and "`:" in line else line
    body = body.split(":", 1)[1] if body.startswith("- command:") else body
    return set(_row_keywords(body))


def merge_rows(rows: list[str]) -> list[str]:
    """Merge consecutive compact rows of sibling keywords that read the same: same parent
    factor keyword, type, default and (cut-down) meaning. ``DDL_IMPO / DX``, ``DY``, ``DZ`` …
    become one row listing the names, as the 2.3 authors already did for exotic components."""
    merged: list[list[str]] = []
    for row in rows:
        cells = _row_cells(row)
        last = merged[-1] if merged else None
        if (
            last is not None
            and " / " in cells[0]
            and " / " in last[0]
            and last[0].split(" / ")[0] == cells[0].split(" / ")[0]
            and last[1:] == cells[1:]
        ):
            last[0] += ", `" + cells[0].strip("`").split(" / ", 1)[1] + "`"
            continue
        merged.append(cells)
    return ["| " + " | ".join(cells) + " |" for cells in merged]


def shorten_rule(line: str, table: set[str]) -> str:
    """In a long list of keywords (``at least one of `A`, `B`, …``), keep the ones still in
    the keyword table and count the others: the DOF and material-law lists run to hundreds."""

    def shorten(match: re.Match[str]) -> str:
        names = re.findall(r"`([^`]+)`", match.group(0))
        if len(names) <= RULE_LIST_MAX:
            return match.group(0)
        kept = [n for n in names if n in table]
        others = len(names) - len(kept)
        return ", ".join(f"`{n}`" for n in kept) + f" (and {others} more not in the table)"

    return re.sub(r"`[^`]+`(?:, `[^`]+`)+", shorten, line)


def compact_reference(lines: list[str], key: set[str]) -> list[str]:
    """Compact detail for a command reference (ADR-025).

    Kept: the introduction, the keyword table (:func:`_compact_row`, then :func:`merge_rows`),
    the catalog rules that constrain at least one keyword still in the table, the first
    :data:`COMPACT_MAX_PATTERNS` patterns and the pitfalls. Dropped: the facts table, the prose
    around the keyword table, rows marked out of scope, and the sections in
    :data:`COMPACT_DROP_SECTIONS`.
    """
    out: list[str] = []
    section = ""
    fence = False
    in_facts = False
    table: set[str] = set()
    rows: list[str] = []
    patterns = 0
    for line in lines:
        if _FENCE.match(line):
            fence = not fence
        if not fence and line.startswith("## "):
            section = line[3:].strip()
        if section == "Patterns" and not fence and line.startswith("### "):
            patterns += 1
        if section == "Patterns" and patterns > COMPACT_MAX_PATTERNS:
            continue
        if rows and not (section == "Keywords" and line.startswith("| `")):
            out += merge_rows(rows)
            rows = []
        if any(section.startswith(name) for name in COMPACT_DROP_SECTIONS):
            continue
        if not section and not fence:
            if line.startswith("| Fact |"):
                in_facts = True
            if in_facts:
                in_facts = line.startswith("|")
                continue
        if section == "Keywords" and not fence and not line.startswith("## "):
            if line.startswith("| `"):
                row = _compact_row(line, key)
                if row is not None:
                    rows.append(row)
                    table.update(_row_keywords(_row_cells(line)[0]))
            elif line.startswith("|"):
                out.append(line)
            elif not line.strip() and out and out[-1].strip():
                out.append(line)
            continue
        if section == "Rules" and _RULE.match(line) and table:
            if not _rule_keywords(line) & table:
                continue
            line = shorten_rule(line, table)
        out.append(line)
    out += merge_rows(rows)
    collapsed: list[str] = []
    for line in out:
        if line.strip() or (collapsed and collapsed[-1].strip()):
            collapsed.append(line)
    return collapsed


def convert(
    path: Path, repo: Path, shift: int = 2, detail: str = "full", key: set[str] | None = None
) -> Section:
    """One source page as a bundle section: provenance line, headings shifted, links rewritten."""
    rel = path.resolve().relative_to(repo.resolve()).as_posix()
    meta, body = _front_matter(path.read_text(encoding="utf-8"))
    lines = _drop_banner(body.strip("\n").split("\n"))
    if detail == "compact" and rel.startswith(COMMANDS_RELDIR.as_posix()):
        lines = compact_reference(lines, key or set())
    out: list[str] = []
    title = ""
    fence: str | None = None
    for line in lines:
        marker = _FENCE.match(line)
        if fence:
            if marker and marker.group(1) == fence:
                fence = None
            out.append(line)
            continue
        if marker:
            fence = marker.group(1)
            out.append(line)
            continue
        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            if level + shift > 6:
                raise BundleError(f"{rel}: heading level {level} cannot move down {shift}")
            if level == 1 and not title:
                title = line[2:].strip()
                out.append("#" * (1 + shift) + " " + title)
                out.append("")
                out.append(provenance_line(rel, meta, detail))
                continue
            line = "#" * shift + line
        out.append(_LINK.sub(lambda m: _rewrite_link(m, path.parent, repo), line))
    if not title:
        raise BundleError(f"{rel}: no H1 heading")
    return Section(title=title, path=rel, lines=out, level=1 + shift)


# --------------------------------------------------------------------------------------
# Glossary


def _cell(value: object) -> str:
    text = " ".join(str(value).split())
    return text.replace("|", "\\|")


def glossary_section(repo: Path, detail: str = "full") -> Section:
    entries = glossary_validator.load(repo / GLOSSARY_RELPATH)
    rel = GLOSSARY_RELPATH.as_posix()
    statuses = sorted({str(e.get("status")) for e in entries})
    lines = [
        "## Glossary",
        "",
        f"*Source: `{rel}` · {len(entries)} entries · statuses: {', '.join(statuses)}*",
        "",
        "The controlled vocabulary. Use the English in the **en** column and no other; the",
        "**never** column lists synonyms the project's validator rejects. French identifiers",
        "(commands, keywords, values) stay French in a `.comm`: the English is for prose only.",
    ]
    kinds = [k for k in KIND_ORDER if any(e.get("kind") == k for e in entries)]
    kinds += sorted({str(e.get("kind")) for e in entries} - set(kinds))
    if detail == "compact":
        kinds = [k for k in kinds if k in COMPACT_GLOSSARY_KINDS]
    for kind in kinds:
        rows = [e for e in entries if e.get("kind") == kind]
        lines += ["", f"### {KIND_TITLES.get(kind, kind)} (`kind: {kind}`)", ""]
        with_note = any(e.get("note") for e in rows)
        header = "| fr | en | never |" + (" note |" if with_note else "")
        lines += [header, "|---|---|---|" + ("---|" if with_note else "")]
        for e in rows:
            never = ", ".join(str(a) for a in e.get("aliases_en") or [])
            row = f"| `{_cell(e['fr'])}` | {_cell(e['en'])} | {_cell(never)} |"
            if with_note:
                row += f" {_cell(e.get('note') or '')} |"
            lines.append(row)
    return Section(title="Glossary", path=rel, lines=lines, level=2)


# --------------------------------------------------------------------------------------
# Assembly

PREAMBLE = """\
This file is the English overlay for the code_aster finite element solver, packed for a coding
agent or an engineer: our guide, the English reference of every command in scope, and the
glossary. It is generated by `caen bundle` from the repository
https://github.com/shubhs650/codeaster-en (GPL-3.0-or-later); the solver and its French
documentation are by EDF R&D, also GPL. Do not edit it: change the source files and rebuild.

## How to use this file

- **It is long. Read it in parts.** Read this section and the contents, then the guide's
  "Concepts" and the walkthrough closest to your problem, then the reference of each command
  you write. The contents list the line where each section starts.
- **Command and keyword names are French and stay French.** `AFFE_MODELE`, `GROUP_MA`,
  `PRES_REP` are the solver's API; never translate, rename or alias them in a `.comm`. The
  English in this file explains them.
- **A `.comm` file is Python.** Commands are called like functions, factor keywords take
  `_F(...)`, and every command result is assigned to a name. The walkthroughs give complete,
  tested files to start from.
- **Use only keywords that appear in a reference or a walkthrough.** The solver checks every
  keyword against its catalog and stops on an unknown one (`SUPERVIS_4`, see the FAQ). Where
  a reference says `TODO(verify)`, the point is not confirmed: do not rely on it.
- **Groups in the `.comm` must exist in the mesh**, with the exact names (`MODELISA7_77`).
- **Units are whatever the mesh and material use**; the solver has none. The fixtures use mm,
  N, MPa, tonne, s.
- **Status.** `machine` = generated, unchecked; `assisted` = written by an agent from cited
  sources, not reviewed by an engineer; `reviewed` = checked by the owner. Each section's
  source line gives its status. Nothing here is a substitute for the official documentation.
- **Links** point to paths in the repository. Files included here are labelled with the same
  path in their source line, so search this file for the path; other files are in the
  repository.
"""


def build(repo: Path, tier: str = "1", detail: str = "compact") -> Bundle:
    if detail not in DETAILS:
        raise BundleError(f"detail must be one of {', '.join(DETAILS)}, not {detail!r}")
    repo = repo.resolve()
    commands, key = tier_commands(repo, tier)
    sections: list[Section] = []
    dropped: list[str] = []
    for page in guide_pages(repo):
        if (detail == "compact" and page.name in COMPACT_DROP_GUIDE) or GUIDE_MIN_TIER.get(
            page.name, "1"
        ) > tier:
            dropped.append(page.relative_to(repo).as_posix())
            continue
        sections.append(convert(page, repo, detail=detail))
    included: list[str] = []
    missing: list[str] = []
    for name in commands:
        path = repo / COMMANDS_RELDIR / f"{name}.md"
        if path.is_file():
            sections.append(convert(path, repo, detail=detail, key=key.get(name)))
            included.append(name)
        else:
            missing.append(name)
    sections.append(glossary_section(repo, detail))
    pin = upstream_pin(repo)
    tiers = "Tier 1" if tier == "1" else f"Tiers 1–{tier}"
    title = f"# code_aster in English: context bundle ({tiers}, {detail})"
    flags = f"--tier {tier}" + (" --detail full" if detail == "full" else "")
    header = [
        title,
        "",
        f"*codeaster-en {__version__} · code_aster {pin} · {len(included)} command references"
        f" · built by `caen bundle {flags}`*",
        "",
        *PREAMBLE.rstrip("\n").split("\n"),
    ]
    if detail == "compact":
        header += [
            "- **Compact detail.** To fit a context window, each command reference keeps its"
            " introduction, catalog rules, first patterns and pitfalls, and a keyword table"
            " cut to name, type, default, English term and allowed values: the authored"
            " meaning of each keyword, rows marked out of scope, and keywords nested under a"
            " factor keyword that is neither key (COMMAND-SET) nor required are in the source"
            " file only. A row may list several sibling keywords that read the same. The"
            ' facts table, "What the solver does", "Other keywords" and "See also" are'
            " left out, and the glossary lists abbreviations and terms only (keyword terms are"
            " in the tables). The `--detail full` bundle has everything.",
        ]
        if dropped:
            header[-1] += " Guide pages left out: " + ", ".join(f"`{d}`" for d in dropped) + "."
    if missing:
        header += [
            f"- **Not included:** {', '.join(f'`{m}`' for m in missing)} (no reference page:"
            " it has no catalog of its own and takes `DEBUT`'s keywords).",
        ]
    parts = [
        ("Part 1: Guide", [s for s in sections if s.path.startswith(GUIDE_RELDIR.as_posix())]),
        (
            f"Part 2: Command references ({tiers})",
            [s for s in sections if s.path.startswith(COMMANDS_RELDIR.as_posix())],
        ),
        ("Part 3: Glossary", [s for s in sections if s.path == GLOSSARY_RELPATH.as_posix()]),
    ]
    # Body first, so the contents can give line numbers; the contents' own length is fixed.
    body: list[str] = []
    starts: list[tuple[int, str, int]] = []  # (body line, label, depth)
    for part_title, part_sections in parts:
        if part_title.startswith("Part 3"):
            glossary = part_sections[0]
            starts.append((len(body) + 1, part_title, 0))
            body += ["", f"## {part_title}", *glossary.lines[1:]]
            continue
        starts.append((len(body) + 1, part_title, 0))
        body += ["", f"## {part_title}"]
        for section in part_sections:
            starts.append((len(body) + 1, f"{section.title} — `{section.path}`", 1))
            body += ["", *section.lines]
    toc_head = ["", "## Contents", ""]
    offset = len(header) + len(toc_head) + len(starts) + 1  # +1: line numbers count from 1
    toc = ["  " * depth + f"- line {start + offset}: {label}" for start, label, depth in starts]
    text = "\n".join([*header, *toc_head, *toc, *body]) + "\n"
    return Bundle(tier=tier, text=text, sections=sections, commands=included, missing=missing)
