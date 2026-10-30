"""PDF ingestion of the French documents (task 5.1): structure, chunks, committed sources."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import jsonschema
import pytest
import yaml

from codeaster_en.docs import ingest

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / ingest.SOURCE_RELDIR
FIXTURE_PDF = REPO / "tests/fixtures/docs/U4.21.01.pdf"
SCHEMA = json.loads((REPO / "docs/schemas/doc-source.schema.json").read_text(encoding="utf-8"))
COMMITTED = sorted(SRC.glob("*.fr.json"))


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fixture_doc() -> dict:
    pytest.importorskip("pdfplumber")
    return ingest.ingest(
        FIXTURE_PDF, source_url=_load(SRC / "U4.21.01.fr.json")["_generated_from"]["source_url"]
    )


def test_pdf_url() -> None:
    assert (
        ingest.pdf_url("U4.41.01") == "https://code-aster.org/doc/default/fr/man_u/u4/u4.41.01.pdf"
    )
    assert ingest.pdf_url("U7.05.21").endswith("/man_u/u7/u7.05.21.pdf")
    with pytest.raises(ingest.IngestError):
        ingest.pdf_url("AFFE_MODELE")


def test_fixture_matches_committed_source(fixture_doc: dict) -> None:
    """The committed source of the fixture PDF is what the code produces today."""
    assert fixture_doc == _load(SRC / "U4.21.01.fr.json")


def test_fixture_structure(fixture_doc: dict) -> None:
    blocks = fixture_doc["blocks"]
    assert fixture_doc["doc_id"] == "U4.21.01"
    meta = fixture_doc["meta"]
    assert meta["title"] == "Opérateur LIRE_MAILLAGE"
    assert re.fullmatch(r"\d\d/\d\d/\d{4}", meta["date"])
    assert "GNU FDL" in meta["licence_notice"]
    assert blocks[0] == {"type": "title", "text": "Opérateur LIRE_MAILLAGE", "page": 1}
    headings = [(b["number"], b["level"]) for b in blocks if b["type"] == "heading"]
    assert headings[:2] == [("1", 1), ("2", 1)]
    assert all(n.count(".") + 1 == lvl for n, lvl in headings)
    syntax = next(b for b in blocks if b["type"] == "code")
    assert "LIRE_MAILLAGE" in syntax["lines"][0]
    # Courier columns survive as spacing: keyword and "=" are separated by spaces.
    assert any(
        re.search(r"UNITE\s+=", ln) for b in blocks if b["type"] == "code" for ln in b["lines"]
    )
    tables = [b for b in blocks if b["type"] == "table"]
    assert tables and all(len(row) == len(tables[0]["rows"][0]) for row in tables[0]["rows"])
    assert any(b["type"] == "list_item" for b in blocks)
    text = json.dumps(blocks, ensure_ascii=False)
    for frame in (
        "Responsable :",
        "Document diffusé",
        "Code_Aster Version",
        "Manuel d'utilisation",
    ):
        assert frame not in text, frame


def test_fixture_recovers_the_body_words(fixture_doc: dict) -> None:
    """Every word of the page bodies reaches a block (formulas and figures aside)."""
    import pdfplumber

    pdf_words: Counter[str] = Counter()
    with pdfplumber.open(FIXTURE_PDF) as pdf:
        for page in pdf.pages:
            page = page.dedupe_chars()
            lines = page.extract_text_lines()
            top, bottom = ingest._page_frame(lines, float(page.height))
            for line in lines:
                if (
                    top < line["top"]
                    and line["bottom"] < bottom
                    and not ingest.TOC_LEADER.search(line["text"])
                ):
                    pdf_words.update(re.findall(r"\w+", line["text"]))
    md_words = Counter(re.findall(r"\w+", ingest.to_markdown(fixture_doc)))
    missing = pdf_words - md_words
    assert sum(missing.values()) <= 0.01 * sum(pdf_words.values()), missing.most_common(20)


def test_chunks_cover_blocks_in_order() -> None:
    blocks = [{"type": "heading", "level": 1, "number": "1", "text": "a" * 10, "page": 1}]
    blocks += [{"type": "paragraph", "text": "x" * 900, "page": 1} for _ in range(10)]
    blocks += [{"type": "heading", "level": 2, "number": "1.1", "text": "b", "page": 2}]
    blocks += [{"type": "paragraph", "text": "y" * 5000, "page": 2}]
    chunks = ingest.chunk(blocks, limit=3000)
    assert [(c["first"], c["last"]) for c in chunks][0] == (0, 3)
    assert chunks[0]["section"] == "1 aaaaaaaaaa"
    flat = [i for c in chunks for i in range(c["first"], c["last"] + 1)]
    assert flat == list(range(len(blocks)))
    assert all(c["chars"] <= 3000 or c["first"] == c["last"] for c in chunks)
    assert chunks[-1]["first"] == chunks[-1]["last"] == len(blocks) - 1  # oversized block alone


@pytest.mark.parametrize("path", COMMITTED, ids=[p.name for p in COMMITTED])
def test_committed_source_is_consistent(path: Path) -> None:
    doc = _load(path)
    jsonschema.validate(doc, SCHEMA)
    assert path.name == f"{doc['doc_id']}.fr.json"
    flat = [i for c in doc["chunks"] for i in range(c["first"], c["last"] + 1)]
    assert flat == list(range(len(doc["blocks"])))
    assert path.with_suffix(".md").read_text(encoding="utf-8") == ingest.to_markdown(doc)
    assert (doc["_generated_from"]["source_url"] or "").startswith("https://code-aster.org/doc/")


def test_committed_sources_cover_doc_ids() -> None:
    assert len(COMMITTED) >= 30
    have = {p.name.removesuffix(".fr.json") for p in COMMITTED}
    assert set(ingest.default_doc_ids(REPO)) <= have


def test_index_is_current(tmp_path: Path) -> None:
    for path in COMMITTED:
        (tmp_path / path.name).write_bytes(path.read_bytes())
    ingest.write_index(tmp_path)
    assert (tmp_path / "INDEX.md").read_text() == (SRC / "INDEX.md").read_text()


def test_verified_doc_ids_name_their_command() -> None:
    """A `verified` entry of en/doc-ids.yaml is a document whose title names the command."""
    entries = yaml.safe_load((REPO / "en/doc-ids.yaml").read_text(encoding="utf-8"))
    verified = [e for e in entries if e["status"] == "verified"]
    assert verified
    for entry in verified:
        title = _load(SRC / f"{entry['doc_id']}.fr.json")["meta"]["title"]
        assert re.search(rf"\b{entry['command']}\b", title), (entry, title)
