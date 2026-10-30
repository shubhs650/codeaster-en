"""``caen docs ingest``: a French code_aster PDF → structured blocks and chunks (task 5.1).

The official documents on code-aster.org are LibreOffice exports with a fixed page frame:

- a running header (``Code_Aster Version`` / version label / ``Titre : … Date : … Page : n/N``
  / ``Responsable : … Clé : U4.41.01 Révision :`` / revision hash) and a running footer
  (``Manuel d'utilisation Fascicule u4.41: …`` / ``Document diffusé sous licence GNU FDL …``).
  Both are cut from every page; page 1's copy fills :func:`metadata`.
- Numbered headings in bold Arial (``1 But``, ``3.2.1 Opérande …``); the number of parts in
  the number is the level.
- Body text in Arial; command syntax, keyword values and listings in Courier New.
- Ruled tables (found with ``pdfplumber``'s line strategy) and a few unruled two-column
  listings, always in Courier, whose columns survive as spacing in a code block.
- Formulas typeset with OpenSymbol/Times (often with 7 pt subscripts on their own line) and
  figures as images. Neither can be recovered as text: a formula's characters are kept as
  extracted and its block is flagged ``equation``; a figure becomes a ``figure`` block.

Blocks, in reading order: ``title``, ``heading`` (``level``, ``number``), ``paragraph``,
``list_item`` (``depth``), ``code`` (``lines``), ``table`` (``rows``), ``figure``. Every block
records the PDF ``page`` it starts on. A paragraph cut by a page break is joined back.

Chunks (:func:`chunk`) group whole blocks for translation (task 5.2): a chunk starts at a
heading where it can and never exceeds :data:`CHUNK_CHARS` unless one block does.

Output layout: ``docs/schemas/doc-source.schema.json``; :func:`to_markdown` is the readable
rendering committed next to the JSON for review. Re-running on the same PDF gives the same
bytes (no dates, sorted keys).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

EXTRACTOR = "codeaster_en.docs.ingest"
# Bump when the output layout or content changes.
EXTRACTOR_VERSION = "1"
SCHEMA_VERSION = 1

SOURCE_RELDIR = Path("en/docs/_src")
SITE = "https://code-aster.org"
# The site redirects /doc/default/ to the current documentation version (v16 in 2026-10).
URL_TEMPLATE = SITE + "/doc/default/fr/man_{manual}/{fascicle}/{doc}.pdf"
DOC_ID = re.compile(r"^[URVD]\d\.\d\d\.\d\d$")

CHUNK_CHARS = 6000
BULLETS = frozenset("•◦▪▫–-‐−·●○■□➢➔►")
HEADING = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(\S.*)$")
TOC_LEADER = re.compile(r"(?:\.\s?){4,}\s*\d+\s*$")
MATH_FONTS = ("Symbol", "TimesNewRoman", "Times-", "Cambria", "StarMath", "Math")
SUBSCRIPT_MAX_SIZE = 8.0
PARAGRAPH_GAP = 5.0  # extra vertical space (pt) above a line that starts a new paragraph
GAP_COLUMN = 15.0  # horizontal gap (pt) that separates two cells of an unruled row


# Documents ingested besides the per-command ones of en/doc-ids.yaml: command-file syntax
# (PLAN 5.1) and IMPR_RESU's MED format, which U4.91.01 does not cover.
EXTRA_DOCS = ("U1.03.01", "U7.05.21")


class IngestError(ValueError):
    """The PDF is not a code_aster document in the expected layout."""


def pdf_url(doc_id: str) -> str:
    """Download URL of a French document (``U4.41.01`` → ``…/man_u/u4/u4.41.01.pdf``)."""
    if not DOC_ID.match(doc_id):
        raise IngestError(f"not a document ID: {doc_id!r} (expected e.g. U4.41.01)")
    doc = doc_id.lower()
    return URL_TEMPLATE.format(manual=doc[0], fascicle=doc[:2], doc=doc)


def _font(char: dict[str, Any]) -> str:
    return str(char["fontname"]).split("+", 1)[-1]


def _is_courier(font: str) -> bool:
    return "Courier" in font or "NimbusMon" in font or "Mono" in font


def _is_math(font: str) -> bool:
    return any(name in font for name in MATH_FONTS) or font == "OpenSymbol"


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def _line_text(chars: list[dict[str, Any]]) -> str:
    """Text of a run of characters, with a space wherever the PDF left a gap."""
    out: list[str] = []
    prev = None
    for ch in chars:
        if prev is not None and ch["x0"] - prev["x1"] > 0.2 * float(ch["size"]):
            if out and out[-1] != " " and ch["text"] != " ":
                out.append(" ")
        out.append(ch["text"])
        prev = ch
    return _clean("".join(out))


def _cells(chars: list[dict[str, Any]]) -> list[tuple[float, str]]:
    """``(x0, text)`` of the cells of a line, split at gaps wider than :data:`GAP_COLUMN`."""
    groups: list[list[dict[str, Any]]] = [[]]
    prev = None
    for ch in chars:
        if prev is not None and ch["x0"] - prev["x1"] > GAP_COLUMN and ch["text"].strip():
            groups.append([])
        groups[-1].append(ch)
        prev = ch
    cells = []
    for group in groups:
        text = _line_text(group)
        if text:
            cells.append((float(next(c for c in group if c["text"].strip())["x0"]), text))
    return cells


def _courier_text(chars: list[dict[str, Any]], left: float) -> str:
    """A Courier line with its columns kept: each character goes to its fixed-pitch column."""
    out: list[str] = []
    for ch in chars:
        if not ch["text"].strip():
            continue
        pitch = 0.6 * float(ch["size"])
        column = max(0, round((ch["x0"] - left) / pitch))
        # Proportional characters (Arial in a Courier line) can drift left: never overwrite.
        if column > len(out):
            out.extend(" " * (column - len(out)))
        out.append(ch["text"])
    return "".join(out).rstrip()


class _Line:
    """One text line of a page body with the features the classifier needs."""

    def __init__(self, raw: dict[str, Any], page: int, left: float, width: float = 595.0) -> None:
        self.chars: list[dict[str, Any]] = []
        for c in raw["chars"]:
            prev = self.chars[-1] if self.chars else None
            # Ligature glyphs ("ff") come twice at the same place.
            if c["text"] == "\x00" or (
                prev is not None and prev["text"] == c["text"] and abs(prev["x0"] - c["x0"]) < 0.5
            ):
                continue
            self.chars.append(c)
        self.page = page
        self.top = float(raw["top"])
        self.bottom = float(raw["bottom"])
        self.x0 = float(raw["x0"]) - left
        # Share of the text width this line fills: a wrapped line of prose fills most of it.
        self.fill = (float(raw["x1"]) - left) / max(1.0, width - 2 * left)
        self.left = left
        visible = [c for c in self.chars if c["text"].strip()]
        fonts = Counter(_font(c) for c in visible)
        self.font = fonts.most_common(1)[0][0] if fonts else ""
        self.first_font = _font(visible[0]) if visible else ""
        self.size = max((float(c["size"]) for c in visible), default=0.0)
        self.text = _clean(str(raw["text"]))
        self.cells = _cells(self.chars)
        n = max(1, len(visible))
        self.courier = sum(1 for c in visible if _is_courier(_font(c))) / n > 0.6
        self.math = sum(1 for c in visible if _is_math(_font(c))) / n > 0.3 or any(
            "\ue000" <= c["text"] <= "\uf8ff" for c in visible
        )
        self.subscript = bool(visible) and all(
            float(c["size"]) < SUBSCRIPT_MAX_SIZE for c in visible
        )
        self.bold = "Bold" in self.first_font and not _is_courier(self.first_font)


def _page_frame(lines: list[dict[str, Any]], height: float) -> tuple[float, float]:
    """``(header_bottom, footer_top)`` of the running header and footer."""
    header_bottom = 0.0
    for raw in lines:
        if raw["top"] < 120 and raw["text"].lstrip().startswith("Responsable"):
            header_bottom = float(raw["bottom"])
    # The revision hash sits just under the "Responsable" line when it does not fit on it.
    for raw in lines:
        if header_bottom and 0 < raw["top"] - header_bottom < 6 and len(raw["text"].split()) == 1:
            header_bottom = float(raw["bottom"])
    footer_top = height
    for raw in lines:
        if raw["top"] > height - 100 and raw["text"].lstrip().startswith("Manuel d"):
            footer_top = min(footer_top, float(raw["top"]))
    return header_bottom, footer_top


def _header_fields(lines: list[dict[str, Any]], header_bottom: float) -> dict[str, str]:
    """Fields of page 1's running header and footer (French labels → our keys)."""
    head = [_clean(raw["text"]) for raw in lines if raw["top"] <= header_bottom + 0.5]
    fields: dict[str, str] = {}
    text = " | ".join(head)
    patterns = {
        "title": r"Titre\s*:\s*(.*?)\s+Date\s*:",
        "date": r"Date\s*:\s*(\d\d/\d\d/\d{4})",
        "pages": r"Page\s*:\s*\d+\s*/\s*(\d+)",
        "responsible": r"Responsable\s*:\s*(.*?)\s+Clé\s*:",
        "key": r"Clé\s*:\s*(\S+)",
        "revision": r"Révision\s*:\s*\|?\s*([0-9a-f]{6,})",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            fields[key] = match.group(1).strip()
    for i, line in enumerate(head):
        if line.startswith("Code_Aster Version") and i + 1 < len(head):
            label = line.removeprefix("Code_Aster Version").strip() or head[i + 1]
            fields["version_label"] = label
    return fields


def _footer_fields(lines: list[dict[str, Any]], footer_top: float) -> dict[str, str]:
    foot = [_clean(raw["text"]) for raw in lines if raw["top"] >= footer_top - 0.5]
    fields: dict[str, str] = {}
    for line in foot:
        if line.startswith("Manuel d"):
            fields["fascicle"] = line
        elif "licence" in line.lower() or "license" in line.lower():
            fields["licence_notice"] = line
    return fields


def _table_rows(table: Any) -> list[list[str]]:
    rows = []
    for row in table.extract():
        cells = [_clean(cell or "") for cell in row]
        if any(cells):
            rows.append(cells)
    return rows


def _inside(line: _Line, bbox: tuple[float, float, float, float]) -> bool:
    x0, top, x1, bottom = bbox
    mid = (line.top + line.bottom) / 2
    return top - 1 <= mid <= bottom + 1 and x0 - 1 <= line.x0 + line.left <= x1


def _page_items(page: Any, number: int) -> tuple[list[tuple[float, Any]], dict[str, str]]:
    """Body items of one page, sorted by position: ``_Line``, table rows or a figure marker."""
    page = page.dedupe_chars()  # LibreOffice writes ligatures twice ("affffectations")
    raw_lines = page.extract_text_lines(return_chars=True, strip=False)
    header_bottom, footer_top = _page_frame(raw_lines, float(page.height))
    if not header_bottom:
        raise IngestError(f"page {number}: no running header ('Responsable : … Clé : …')")
    fields: dict[str, str] = {}
    if number == 1:
        fields = _header_fields(raw_lines, header_bottom) | _footer_fields(raw_lines, footer_top)
    heads = [r for r in raw_lines if r["top"] < 60 and r["text"].lstrip().startswith("Code_")]
    left = float(heads[0]["x0"]) if heads else 0.0

    body = page.crop((0, header_bottom + 0.5, page.width, footer_top - 0.5))
    tables = []
    for table in body.find_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines"}):
        rows = _table_rows(table)
        if len(rows) >= 2 and max(len(r) for r in rows) >= 2:
            tables.append((table.bbox, rows))

    items: list[tuple[float, Any]] = []
    for bbox, rows in tables:
        items.append((float(bbox[1]), {"type": "table", "rows": rows, "page": number}))
    lines = []
    for raw in raw_lines:
        if not (header_bottom < raw["top"] and raw["bottom"] < footer_top):
            continue
        line = _Line(raw, number, left, float(page.width))
        if line.text and not any(_inside(line, bbox) for bbox, _ in tables):
            lines.append(line)
    for start, end in _unruled_tables(lines):
        rows = _unruled_rows(lines[start:end])
        items.append((lines[start].top, {"type": "table", "rows": rows, "page": number}))
        lines[start:end] = [None] * (end - start)  # type: ignore[list-item]
    items += [(line.top, line) for line in lines if line is not None]
    for image in page.images:
        top = float(image["top"])
        if header_bottom < top < footer_top and image["width"] > 40 and image["height"] > 20:
            items.append((top, {"type": "figure", "page": number}))
    items.sort(key=lambda item: item[0])
    return items, fields


def _row_candidate(line: _Line) -> bool:
    return (
        2 <= len(line.cells) <= 5
        and not line.courier
        and not line.subscript
        and _bullet(line) is None
        and _heading(line) is None
        and not TOC_LEADER.search(line.text)
    )


def _unruled_tables(lines: list[_Line]) -> list[tuple[int, int]]:
    """``[start, end)`` index ranges of unruled tables: runs of multi-cell lines in which at
    least two rows start their second cell at the same x (justified prose never does)."""
    found = []
    i = 0
    while i < len(lines):
        if not _row_candidate(lines[i]):
            i += 1
            continue
        j = i + 1
        columns = {round(x) for x, _ in lines[i].cells}
        while j < len(lines) and lines[j].top - lines[j - 1].bottom < 3 * PARAGRAPH_GAP:
            line = lines[j]
            if _row_candidate(line):
                columns |= {round(x) for x, _ in line.cells}
            elif not (
                len(line.cells) == 1
                and not line.courier
                and any(abs(line.cells[0][0] - c) < 4 for c in columns)
                and line.cells[0][0] > min(columns) + 4
            ):
                break
            j += 1
        seconds = [round(ln.cells[1][0]) for ln in lines[i:j] if _row_candidate(ln)]
        if len(seconds) >= 2 and any(
            sum(1 for s in seconds if abs(s - x) < 4) >= 2 for x in seconds
        ):
            found.append((i, j))
            i = j
        else:
            i += 1
    return found


def _unruled_rows(lines: list[_Line]) -> list[list[str]]:
    """Rows of an unruled table; a one-cell line continues the cell it is aligned with."""
    rows: list[list[tuple[float, str]]] = []
    for line in lines:
        if len(line.cells) >= 2 or not rows:
            rows.append(list(line.cells))
            continue
        x, text = line.cells[0]
        last = rows[-1]
        k = min(range(len(last)), key=lambda n: abs(last[n][0] - x))
        last[k] = (last[k][0], _join(last[k][1], text))
    width = max(len(r) for r in rows)
    return [[t for _, t in r] + [""] * (width - len(r)) for r in rows]


def _heading(line: _Line) -> tuple[str, str] | None:
    if not line.bold or line.size < 9.5:
        return None
    match = HEADING.match(line.text)
    if not match or TOC_LEADER.search(line.text):
        return None
    return match.group(1), match.group(2)


def _bullet(line: _Line) -> str | None:
    """Text after the bullet when the line is a list item."""
    visible = [c for c in line.chars if c["text"].strip()]
    if len(visible) < 2:
        return None
    first, second = visible[0], visible[1]
    if first["text"] in BULLETS or "\ue000" <= first["text"] <= "\uf8ff":
        if second["x0"] - first["x1"] > 3 or first["text"] in "•▪◦●➢":
            return _line_text([c for c in line.chars if c is not first])
    return None


class _Builder:
    """Turns the classified lines of all pages into blocks."""

    def __init__(self) -> None:
        self.blocks: list[dict[str, Any]] = []
        self.prev: _Line | None = None
        self.prev_kind = ""
        self.code_left = 0.0
        self.list_x = 0.0

    def _new(self, block: dict[str, Any]) -> None:
        self.blocks.append(block)

    def _gap(self, line: _Line) -> float:
        if self.prev is None or self.prev.page != line.page:
            return 0.0
        return line.top - self.prev.bottom

    def add_line(self, line: _Line) -> None:
        last = self.blocks[-1] if self.blocks else None
        gap = self._gap(line)
        same_page = self.prev is not None and self.prev.page == line.page

        if TOC_LEADER.search(line.text) or (self.prev_kind == "toc" and gap < PARAGRAPH_GAP):
            self.prev, self.prev_kind = line, "toc"
            return
        if line.subscript and last is not None and same_page and gap < 4:
            # Subscripts and indices printed on their own line under a formula.
            if "text" in last:
                last["text"] += " " + line.text
            last["equation"] = True
            self.prev = line
            return

        heading = _heading(line)
        if heading is not None:
            number, title = heading
            self._new(
                {
                    "type": "heading",
                    "level": number.count(".") + 1,
                    "number": number,
                    "text": title,
                    "page": line.page,
                }
            )
            self.prev, self.prev_kind = line, "heading"
            return
        if (
            self.prev_kind == "heading"
            and last is not None
            and last["type"] == "heading"
            and line.bold
            and not line.courier
            and same_page
            and gap < 4
        ):
            last["text"] += " " + line.text  # heading wrapped onto a second line
            self.prev = line
            return
        big_bold = "Bold" in line.first_font and line.size >= 18
        if big_bold and self.prev_kind == "title" and last is not None:
            last["text"] += " " + line.text  # title on several lines
            self.prev = line
            return
        if big_bold and not any(b["type"] == "title" for b in self.blocks):
            self._new({"type": "title", "text": line.text, "page": line.page})
            self.prev, self.prev_kind = line, "title"
            return

        inline = (
            last is not None
            and last["type"] in ("paragraph", "list_item")
            and self.prev_kind in ("paragraph", "list_item")
            and same_page
            and gap < 3
            and self.prev is not None
            and self.prev.fill > 0.8
            and not last["text"].rstrip().endswith(":")
        )
        if line.courier and not inline:
            text = _courier_text(line.chars, line.left)
            if last is not None and last["type"] == "code" and (gap < 14 or not same_page):
                last["lines"].append(text)
            else:
                self._new({"type": "code", "lines": [text], "page": line.page})
            self.prev, self.prev_kind = line, "code"
            return

        item = _bullet(line)
        if item is not None:
            self.list_x = line.x0
            depth = 1 if line.x0 > 75 else 0
            self._new({"type": "list_item", "depth": depth, "text": item, "page": line.page})
            self.prev, self.prev_kind = line, "list_item"
            return

        math = line.math
        continues = (
            last is not None
            and last["type"] in ("paragraph", "list_item")
            and (
                (same_page and gap < PARAGRAPH_GAP)
                or (not same_page and last["type"] == "paragraph" and not _ends(last["text"]))
            )
        )
        if continues and last is not None:
            if last["type"] == "list_item" and line.x0 <= self.list_x + 1 and gap >= 2:
                continues = False
        if continues and last is not None:
            last["text"] = _join(last["text"], line.text)
            if math:
                last["equation"] = True
        else:
            block: dict[str, Any] = {"type": "paragraph", "text": line.text, "page": line.page}
            if math:
                block["equation"] = True
            self._new(block)
        self.prev, self.prev_kind = line, self.blocks[-1]["type"]

    def add_other(self, block: dict[str, Any]) -> None:
        self._new(block)
        self.prev_kind = block["type"]


def _ends(text: str) -> bool:
    return text.rstrip().endswith((".", ":", ";", "!", "?", ")", "»"))


def _join(left: str, right: str) -> str:
    if left.endswith("-") and right[:1].islower() and not left.endswith(" -"):
        return left[:-1] + right
    return f"{left} {right}"


def _finish_code(block: dict[str, Any]) -> None:
    lines = block["lines"]
    while lines and not lines[-1].strip():
        lines.pop()
    indents = [len(ln) - len(ln.lstrip()) for ln in lines if ln.strip()]
    cut = min(indents, default=0)
    block["lines"] = [ln[cut:] for ln in lines]


def blocks_from_pdf(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """``(blocks, metadata)`` of one French code_aster PDF."""
    import pdfplumber  # optional dependency: the `docs` extra

    builder = _Builder()
    meta: dict[str, Any] = {}
    with pdfplumber.open(path) as pdf:
        info = pdf.metadata or {}
        meta["page_count"] = len(pdf.pages)
        for key in ("Title", "Keywords"):
            if isinstance(info.get(key), str):
                meta[f"pdf_{key.lower()}"] = _clean(info[key])
        for number, page in enumerate(pdf.pages, start=1):
            items, fields = _page_items(page, number)
            meta.update(fields)
            for _, item in items:
                if isinstance(item, _Line):
                    builder.add_line(item)
                else:
                    builder.add_other(item)
    for block in builder.blocks:
        if block["type"] == "code":
            _finish_code(block)
    blocks = [
        b for b in builder.blocks if b["type"] != "code" or any(ln.strip() for ln in b["lines"])
    ]
    title = next((b["text"] for b in blocks if b["type"] == "title"), None)
    if title and str(meta.get("title", "")).endswith("[...]"):
        meta["title"] = title  # the running header cuts long titles
    if "key" not in meta:
        raise IngestError(f"{path}: no 'Clé : <doc ID>' in the page 1 header")
    return blocks, meta


def block_chars(block: dict[str, Any]) -> int:
    if block["type"] == "code":
        return sum(len(ln) + 1 for ln in block["lines"])
    if block["type"] == "table":
        return sum(len(c) + 3 for row in block["rows"] for c in row)
    return len(block.get("text", ""))


def chunk(blocks: list[dict[str, Any]], limit: int = CHUNK_CHARS) -> list[dict[str, Any]]:
    """Group consecutive blocks into translation chunks of at most ``limit`` characters.

    A chunk ends before a level 1 or 2 heading once it holds a third of the limit, and before
    any block that would push it over the limit. A single block larger than the limit is a
    chunk of its own.
    """
    chunks: list[dict[str, Any]] = []
    start, size = 0, 0
    for i, block in enumerate(blocks):
        n = block_chars(block)
        boundary = block["type"] == "heading" and block["level"] <= 2 and size >= limit // 3
        if i > start and (size + n > limit or boundary):
            chunks.append({"first": start, "last": i - 1, "chars": size})
            start, size = i, 0
        size += n
    if blocks:
        chunks.append({"first": start, "last": len(blocks) - 1, "chars": size})
    for number, item in enumerate(chunks, start=1):
        item["id"] = number
        heading = next(
            (b for b in reversed(blocks[: item["last"] + 1]) if b["type"] == "heading"), None
        )
        first = blocks[item["first"]]
        item["section"] = (
            f"{first['number']} {first['text']}"
            if first["type"] == "heading"
            else (f"{heading['number']} {heading['text']}" if heading else "")
        )
    return chunks


def ingest(path: Path, source_url: str | None = None) -> dict[str, Any]:
    """The ``en/docs/_src/<DOC-ID>.fr.json`` document for one PDF."""
    data = path.read_bytes()
    blocks, meta = blocks_from_pdf(path)
    doc_id = meta.pop("key")
    if not DOC_ID.match(doc_id):
        raise IngestError(f"{path}: header key {doc_id!r} is not a document ID")
    return {
        "_generated_from": {
            "extractor": EXTRACTOR,
            "extractor_version": EXTRACTOR_VERSION,
            "source_url": source_url,
            "source_sha256": hashlib.sha256(data).hexdigest(),
            "source_bytes": len(data),
        },
        "schema_version": SCHEMA_VERSION,
        "doc_id": doc_id,
        "language": "fr",
        "copyright": "EDF R&D",
        "licence": "GFDL (GNU Free Documentation License; see en/docs/_src/README.md)",
        "meta": dict(sorted(meta.items())),
        "blocks": blocks,
        "chunks": chunk(blocks),
    }


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ") or " "


def render_blocks(
    blocks: list[dict[str, Any]],
    first: int,
    last: int,
    page: int = 0,
    code: Callable[[dict[str, Any]], list[str]] | None = None,
) -> tuple[list[str], int]:
    """Markdown lines for ``blocks[first..last]`` and the page reached.

    A ``<!-- page N -->`` marker precedes the first block of each page after ``page``. ``code``
    renders a code block instead of the default fenced ``text`` block (task 5.2 replaces code
    blocks by markers).
    """
    out: list[str] = []
    for i in range(first, last + 1):
        block = blocks[i]
        if block["page"] != page:
            page = block["page"]
            out += [f"<!-- page {page} -->", ""]
        kind = block["type"]
        if kind == "title":
            out += [f"# {block['text']}", ""]
        elif kind == "heading":
            out += [f"{'#' * min(6, block['level'] + 1)} {block['number']} {block['text']}", ""]
        elif kind == "paragraph":
            suffix = " <!-- equation -->" if block.get("equation") else ""
            out += [block["text"] + suffix, ""]
        elif kind == "list_item":
            nxt = blocks[i + 1] if i + 1 < len(blocks) else None
            out.append(f"{'  ' * block['depth']}- {block['text']}")
            if nxt is None or nxt["type"] != "list_item":
                out.append("")
        elif kind == "code":
            out += code(block) if code else ["```text", *block["lines"], "```", ""]
        elif kind == "table":
            width = max(len(r) for r in block["rows"])
            rows = [r + [""] * (width - len(r)) for r in block["rows"]]
            out.append("| " + " | ".join(_md_cell(c) for c in rows[0]) + " |")
            out.append("|" + "---|" * width)
            out += ["| " + " | ".join(_md_cell(c) for c in r) + " |" for r in rows[1:]]
            out.append("")
        elif kind == "figure":
            out += [f"*[Figure, page {block['page']}: not extracted]*", ""]
    return out, page


def to_markdown(doc: dict[str, Any]) -> str:
    """Readable French rendering of an ingested document (for review and citation)."""
    meta = doc["meta"]
    gen = doc["_generated_from"]
    head = [
        "---",
        f"doc_id: {doc['doc_id']}",
        f"title_fr: {json.dumps(meta.get('title', ''), ensure_ascii=False)}",
        f"date: {meta.get('date', '')}",
        f"revision: {meta.get('revision', '')}",
        f"version_label: {meta.get('version_label', '')}",
        f"source: {gen['source_url'] or ''}",
        f"source_sha256: {gen['source_sha256']}",
        "copyright: EDF R&D",
        f"licence: {json.dumps(meta.get('licence_notice', ''), ensure_ascii=False)}",
        f"extractor: {gen['extractor']} v{gen['extractor_version']}",
        "---",
        "",
        "<!-- Generated by `caen docs ingest`; do not edit. French text as extracted from the PDF;",
        "     formulas (`equation`) and figures are not recoverable. -->",
        "",
    ]
    out = head
    page = 0
    for item in doc["chunks"]:
        out += [f"<!-- chunk {item['id']} -->", ""]
        lines, page = render_blocks(doc["blocks"], item["first"], item["last"], page)
        out += lines
    return "\n".join(out).rstrip() + "\n"


def write(doc: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    """Write ``<DOC-ID>.fr.json`` and ``<DOC-ID>.fr.md`` under ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{doc['doc_id']}.fr.json"
    md_path = out_dir / f"{doc['doc_id']}.fr.md"
    json_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md_path.write_text(to_markdown(doc), encoding="utf-8")
    return json_path, md_path


def write_index(out_dir: Path) -> Path:
    """Rewrite ``INDEX.md``: one row per ingested document in ``out_dir``."""
    rows = [
        "# Ingested French documents",
        "",
        "<!-- Generated by `caen docs ingest`/`caen docs fetch`; do not edit. -->",
        "",
        "| Doc ID | Title | Date | Revision | Pages | Chunks | Tables | Figures | Source |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for path in sorted(out_dir.glob("*.fr.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        meta = doc["meta"]
        kinds = Counter(b["type"] for b in doc["blocks"])
        url = doc["_generated_from"]["source_url"] or ""
        rows.append(
            f"| [{doc['doc_id']}]({doc['doc_id']}.fr.md) | {_md_cell(meta.get('title', ''))} "
            f"| {meta.get('date', '')} | {meta.get('revision', '')} | {meta['page_count']} "
            f"| {len(doc['chunks'])} | {kinds['table']} | {kinds['figure']} | {url} |"
        )
    path = out_dir / "INDEX.md"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def fetch(doc_id: str, cache: Path) -> tuple[Path, str]:
    """Download one document's PDF into ``cache`` (kept if already there); ``(path, url)``.

    ``url`` is where the site redirected to (``/doc/v16/…``), which names the documentation
    version; it is kept next to the PDF so a cached copy reports the same URL.
    """
    import urllib.request

    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{doc_id}.pdf"
    url_file = cache / f"{doc_id}.url"
    if path.is_file() and url_file.is_file():
        return path, url_file.read_text(encoding="utf-8").strip()
    url = pdf_url(doc_id)
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 (fixed https host)
        data = response.read()
        url = response.geturl()  # /doc/default/ redirects to the versioned path
    if not data.startswith(b"%PDF"):
        raise IngestError(f"{url}: not a PDF (the document may not exist)")
    path.write_bytes(data)
    url_file.write_text(url + "\n", encoding="utf-8")
    return path, url


def default_doc_ids(repo: Path) -> list[str]:
    """Every document of ``en/doc-ids.yaml`` plus :data:`EXTRA_DOCS`, sorted, no repeats."""
    import yaml

    entries = yaml.safe_load((repo / "en/doc-ids.yaml").read_text(encoding="utf-8")) or []
    return sorted({str(e["doc_id"]) for e in entries} | set(EXTRA_DOCS))
