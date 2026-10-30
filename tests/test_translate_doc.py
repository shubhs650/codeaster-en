"""Tests for ``caen translate doc`` (task 5.2, ADR-027).

Unit tests run in a small repository built in ``tmp_path`` (glossary, one command JSON, two
ingested documents from the real ``en/docs/_src``) with scripted translators, so no network
call is made. The last tests check the committed ``en/docs`` translations and their scope.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml
from typer.testing import CliRunner

from codeaster_en.cli import app
from codeaster_en.docs import ingest
from codeaster_en.translate import doc as td

REPO = Path(__file__).resolve().parents[1]

GLOSSARY = """\
- {fr: maille, en: element, kind: term, note: "Never 'cell'.", aliases_en: [cell], status: machine}
- {fr: VALE, en: value(s), kind: keyword, note: "Values.", status: machine}
"""

GOOD = REPO / "en/docs/U4.31.01.md"


def _repo(tmp_path: Path, scope: str | None = None) -> Path:
    root = tmp_path / "repo"
    (root / "en/docs/_src").mkdir(parents=True)
    (root / "en/commands").mkdir()
    (root / "en/glossary.yaml").write_text(GLOSSARY, encoding="utf-8")
    shutil.copy(REPO / "en/commands/DEFI_CONSTANTE.json", root / "en/commands")
    for command in ("FIN", "CALC_FONCTION"):
        shutil.copy(REPO / f"en/commands/{command}.json", root / "en/commands")
    (root / "en/doc-ids.yaml").write_text(
        "- {command: DEFI_CONSTANTE, doc_id: U4.31.01, status: verified}\n"
        "- {command: FIN, doc_id: U4.11.02, status: verified}\n",
        encoding="utf-8",
    )
    for doc_id in ("U4.31.01", "U4.11.02"):
        shutil.copy(REPO / f"en/docs/_src/{doc_id}.fr.json", root / "en/docs/_src")
    (root / "en/docs/scope.yaml").write_text(
        scope or "docs:\n  U4.31.01: {tier: 1}\n  U4.11.02: {tier: 1, chunks: '1'}\n",
        encoding="utf-8",
    )
    (root / "UPSTREAM_VERSION").write_text("17.4.26\n", encoding="utf-8")
    return root


def _answer(root: Path) -> str:
    """The committed English of U4.31.01 chunk 1, with code collapsed back to markers."""
    body = td.read_stored(GOOD)[1].body
    return td.collapse_code(body)[0] + "\n"


def _replay(tmp_path: Path, doc_id: str, answers: dict[int, str]) -> td.ReplayDocTranslator:
    directory = tmp_path / "answers"
    for number, text in answers.items():
        (directory / doc_id).mkdir(parents=True, exist_ok=True)
        (directory / doc_id / f"{number}.md").write_text(text, encoding="utf-8")
    directory.mkdir(exist_ok=True)
    return td.ReplayDocTranslator(directory, "session:test")


# ---------------------------------------------------------------- units


def test_parse_ranges() -> None:
    assert td.parse_ranges("1-3, 7") == {1, 2, 3, 7}
    assert td.parse_ranges(["2", 5]) == {2, 5}
    with pytest.raises(td.TranslateError):
        td.parse_ranges("4-2")


def test_chunks_replace_code_and_round_trip() -> None:
    doc = td.load_source(REPO, "U4.41.01")
    chunks = td.chunks_of(doc)
    assert [c.id for c in chunks] == [c["id"] for c in doc["chunks"]]
    n_code = sum(1 for b in doc["blocks"] if b["type"] == "code")
    assert sum(len(c.code) for c in chunks) == n_code
    assert "```" not in "".join(c.fr for c in chunks)
    for chunk in chunks:
        expanded = td.expand_code(chunk.fr, chunk.code)
        text, code = td.collapse_code(expanded)
        assert text == chunk.fr and tuple(code) == chunk.code


def test_render_blocks_matches_french_markdown() -> None:
    """The refactored renderer still writes the committed ``.fr.md`` byte for byte."""
    doc = td.load_source(REPO, "U4.41.01")
    path = REPO / "en/docs/_src/U4.41.01.fr.md"
    assert ingest.to_markdown(doc) == path.read_text(encoding="utf-8")


def test_check_accepts_the_committed_translation(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    src = td.load_sources(root)
    chunk = td.chunks_of(td.load_source(root, "U4.31.01"))[0]
    assert td.check_chunk(chunk, _answer(root), src) == []


@pytest.mark.parametrize(
    ("old", "new", "problem"),
    [
        ("[[CODE 2]]\n", "", "code markers differ"),
        ("<!-- page 2 -->\n", "", "page markers differ"),
        ("### 3.2 Operand VALE", "### 3.3 Operand VALE", "headings (level, number) differ"),
        ("### 3.2 Operand VALE", "#### 3.2 Operand VALE", "headings (level, number) differ"),
        ("- Define the constant", "Define the constant", "list items (indent) differ"),
        ("( CALC_FONCTION , ", "( ", "solver identifiers missing: CALC_FONCTION"),
        ("real number", "real number per cell", "forbidden synonym 'cell'"),
        ("Value of the constant", "Valeur de la constante", "French words left"),
        ("Value of the constant", "", ""),
    ],
)
def test_check_rejects(tmp_path: Path, old: str, new: str, problem: str) -> None:
    root = _repo(tmp_path)
    src = td.load_sources(root)
    chunk = td.chunks_of(td.load_source(root, "U4.31.01"))[0]
    answer = _answer(root)
    assert old in answer
    problems = td.check_chunk(chunk, answer.replace(old, new, 1), src)
    if problem:
        assert any(problem in p for p in problems), problems
    assert td.check_chunk(chunk, "  \n", src) == ["empty translation"]


def test_french_left_ignores_quotes_values_and_names() -> None:
    text = "See «Opérateur AFFE_MODELE», the [maillage] object, value 'maillage.med', Lamé."
    assert td.french_left(text) == []
    assert td.french_left("the maillage") == ["maillage"]


def test_prompt_has_keywords_glossary_and_no_code(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    src = td.load_sources(root)
    chunk = td.chunks_of(td.load_source(root, "U4.31.01"))[0]
    user = td.user_prompt(chunk, "Opérateur DEFI_CONSTANTE", src)
    assert "Keywords of DEFI_CONSTANTE (verbatim API): NOM_RESU, TITRE, VALE" in user
    assert "- VALE = value(s) (keyword)" in user
    assert "[[CODE 1]]" in user and "```" not in user
    system = td.system_prompt(src.terms)
    assert "maille = element (term); never: cell" in system


# ---------------------------------------------------------------- runs


def test_assemble_pending_translated_and_out_of_scope(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    src = td.load_sources(root)
    rep = td.translate_doc(src, "U4.11.02", None)
    assert (rep.in_scope, rep.pending, rep.translated) == (1, 1, 0)
    text = td.doc_path(root, "U4.11.02").read_text(encoding="utf-8")
    assert "status=pending" in text and "status=out-of-scope" in text
    assert "## 2 Syntaxe *(not translated)*" in text or "*(not translated)*" in text
    assert "chunks: {total: 2, translated: 0, stale: 0, pending: 1, out_of_scope: 1}" in text

    rep = td.translate_doc(src, "U4.31.01", _replay(tmp_path, "U4.31.01", {1: _answer(root)}))
    assert (rep.translated, rep.failed) == (1, {})
    path = td.doc_path(root, "U4.31.01")
    text = path.read_text(encoding="utf-8")
    front = yaml.safe_load(text.split("---\n")[1])
    assert front["title_en"] == "DEFI_CONSTANTE operator"
    assert front["licence"] == "GFDL-1.3" and front["method"] == "machine"
    assert front["translation_source"] == "session:test"
    assert front["commands"] == ["DEFI_CONSTANTE"] and front["reviewed_by"] is None
    assert "Unofficial English translation" in text and "French original prevails" in text
    assert "DEFI_CONSTANTE\n" in text  # the syntax block is back, verbatim
    assert td.validate_dir(root) == ([], 2, 1)

    # A second run asks for nothing and leaves the file as it is.
    again = td.translate_doc(src, "U4.31.01", _replay(tmp_path, "U4.31.01", {}))
    assert (again.pending, again.requests) == (0, 0)
    assert path.read_text(encoding="utf-8") == text


def test_stale_chunk_is_flagged_and_offered_again(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    src = td.load_sources(root)
    td.translate_doc(src, "U4.31.01", _replay(tmp_path, "U4.31.01", {1: _answer(root)}))
    source = root / "en/docs/_src/U4.31.01.fr.json"
    doc = json.loads(source.read_text(encoding="utf-8"))
    doc["blocks"][2]["text"] += " Modifié."
    source.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    assert td.validate_dir(root)[0] == [
        "en/docs/U4.31.01.md: chunk 1: French changed; not marked stale"
    ]
    rep = td.translate_doc(src, "U4.31.01", None)
    assert rep.pending == 1
    text = td.doc_path(root, "U4.31.01").read_text(encoding="utf-8")
    assert "stale=1" in text and "stale: 1" in text
    assert td.validate_dir(root)[0] == []


def test_reviewed_chunk_is_never_redone(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    src = td.load_sources(root)
    td.translate_doc(src, "U4.31.01", _replay(tmp_path, "U4.31.01", {1: _answer(root)}))
    path = td.doc_path(root, "U4.31.01")
    path.write_text(
        path.read_text(encoding="utf-8").replace("method=machine", "method=reviewed"),
        encoding="utf-8",
    )
    rep = td.translate_doc(src, "U4.31.01", _replay(tmp_path, "U4.31.01", {}), force=True)
    assert rep.pending == 0
    assert "status: reviewed" in path.read_text(encoding="utf-8")


def test_replay_failure_is_reported_and_chunk_stays_pending(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    src = td.load_sources(root)
    bad = _answer(root).replace("[[CODE 3]]\n", "")
    rep = td.translate_doc(src, "U4.31.01", _replay(tmp_path, "U4.31.01", {1: bad}))
    assert rep.translated == 0 and "code markers differ" in rep.failed[1][0]
    assert "status=pending" in td.doc_path(root, "U4.31.01").read_text(encoding="utf-8")


class FakeClient:
    def __init__(self, replies: list[str]) -> None:
        self.calls: list[dict[str, Any]] = []
        self.replies = replies

        def create(**kwargs: Any) -> Any:
            self.calls.append(kwargs)
            text = self.replies.pop(0)
            return SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text=text)],
                usage=SimpleNamespace(input_tokens=100, output_tokens=50),
            )

        self.beta = SimpleNamespace(messages=SimpleNamespace(create=create))


def test_anthropic_backend_re_asks_with_problems(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    src = td.load_sources(root)
    good = _answer(root)
    client = FakeClient([good.replace("[[CODE 1]]\n", ""), good])
    translator = td.AnthropicDocTranslator(client=client)
    rep = td.translate_doc(src, "U4.31.01", translator)
    assert (rep.translated, rep.requests, rep.output_tokens) == (1, 2, 100)
    second = client.calls[1]["messages"][0]["content"]
    assert "previous answer was rejected" in second and "code markers differ" in second
    assert client.calls[0]["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "source=llm:claude-opus-5-5" in td.doc_path(root, "U4.31.01").read_text(encoding="utf-8")


def test_cli_export_dry_run_and_responses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _repo(tmp_path)
    (root / ".git").mkdir()
    monkeypatch.chdir(root)
    runner = CliRunner()
    out = tmp_path / "req"
    result = runner.invoke(app, ["translate", "doc", "--tier", "1", "--export-requests", str(out)])
    assert result.exit_code == 0, result.output
    assert (out / "U4.31.01/1.request.md").is_file() and (out / "SYSTEM.md").is_file()
    assert (out / "U4.11.02/1.request.md").is_file()
    assert not (out / "U4.11.02/2.request.md").exists()  # out of scope
    assert "2 document(s), 2 chunk(s)" in result.output
    answers = tmp_path / "answers"
    (answers / "U4.31.01").mkdir(parents=True)
    (answers / "U4.31.01/1.md").write_text(_answer(root), encoding="utf-8")
    result = runner.invoke(
        app,
        ["translate", "doc", "U4.31.01", "--responses", str(answers), "--source", "session:t"],
    )
    assert result.exit_code == 0, result.output
    assert "1/1 pending chunk(s) translated" in result.output
    result = runner.invoke(app, ["validate", "docs"])
    assert result.exit_code == 0, result.output


# ---------------------------------------------------------------- committed translations


def test_committed_translations_are_valid() -> None:
    issues, files, translated = td.validate_dir(REPO)
    assert issues == []
    assert files >= 1 and translated >= 1


def test_committed_translations_are_current() -> None:
    """Re-assembling a committed document changes nothing (header and markers generated)."""
    src = td.load_sources(REPO)
    for path in sorted((REPO / td.DOCS_RELDIR).glob("*.md")):
        if not ingest.DOC_ID.match(path.stem):
            continue
        doc = td.load_source(REPO, path.stem)
        text = td.assemble(doc, src.scope[path.stem], td.chunks_of(doc), td.read_stored(path), src)
        assert text == path.read_text(encoding="utf-8"), path.name


def test_scope_names_ingested_documents_and_real_chunks() -> None:
    src = td.load_sources(REPO)
    known = {e["doc_id"] for e in yaml.safe_load((REPO / "en/doc-ids.yaml").read_text())}
    known |= set(ingest.EXTRA_DOCS)
    for doc_id, scope in src.scope.items():
        assert doc_id in known, doc_id
        doc = td.load_source(REPO, doc_id)
        if scope.chunks is not None:
            assert scope.reason, doc_id
            assert scope.chunks <= {c["id"] for c in doc["chunks"]}, doc_id


def test_tier1_and_tier2_documents_are_fully_translated() -> None:
    """PLAN 5.2 acceptance, extended to Tier 2: every in-scope chunk of every Tier 1 and 2
    document is translated."""
    src = td.load_sources(REPO)
    assert {s.tier for s in src.scope.values()} == {1, 2}
    for doc_id in td.tier_docs(src, 2):
        path = td.doc_path(REPO, doc_id)
        assert path.is_file(), doc_id
        stored = td.read_stored(path)
        doc = td.load_source(REPO, doc_id)
        left = [
            c.id
            for c in td.chunks_of(doc)
            if src.scope[doc_id].includes(c.id) and td.pending(c, stored.get(c.id))
        ]
        assert left == [], (doc_id, left)
