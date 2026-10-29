"""English gettext catalog (task 3.4, ADR-004): ``en/messages/codeaster_en.po`` and the ``.mo``.

The catalog tests need no solver. The English runs under ``tests/fixtures/<case>/output_en/``
come from ``FIXTURE_LANG=EN scripts/run-fixture.sh`` (in a session or in the ``english`` job of
``.github/workflows/solver-fixtures.yml``): the same input with ``DEBUT(LANG="EN")`` and our
``.mo`` mounted where the image's ``profile.sh`` points ``ASTER_LOCALEDIR``.
"""

from __future__ import annotations

import gettext
import hashlib
import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from codeaster_en.cli import app
from codeaster_en.mess import parse
from codeaster_en.mess.catalog import MessageCatalog
from codeaster_en.mess.parser import UTMESS_FOOTERS
from codeaster_en.mess.render import FOOTERS_EN, translate
from codeaster_en.translate import gettext_po

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"
PO = REPO / gettext_po.PO_RELPATH
EN_CASES = ("solid_static", "shell_static", "modal", "broken_missing_group")
TEST_LINE = re.compile(r"^ (OK|NOOK) +(\S+) +(\S+) +(\S+) +(\S+)")


@pytest.fixture(scope="module")
def catalog() -> tuple[list[gettext_po.Entry], dict[str, str]]:
    return gettext_po.load(REPO)


@pytest.fixture(scope="module")
def mo_dir(tmp_path_factory: pytest.TempPathFactory, catalog) -> Path:
    entries, provenance = catalog
    localedir = tmp_path_factory.mktemp("locale")
    path = gettext_po.mo_path(localedir)
    path.parent.mkdir(parents=True)
    path.write_bytes(gettext_po.render_mo(entries, provenance))
    return localedir


# --- the catalog ---------------------------------------------------------------------------


def test_committed_po_is_current() -> None:
    assert gettext_po.check(REPO) == []


def test_catalog_covers_every_message_gettext_can_see(catalog) -> None:
    entries, _ = catalog
    ids = {i for e in entries for i in e.ids}
    expected, bare = set(), set()
    for path in sorted((REPO / "en" / "messages").glob("*.en.json")):
        for msg in json.loads(path.read_text(encoding="utf-8"))["messages"].values():
            if gettext_po.in_catalog(msg):
                expected.add(msg["id"])
            elif msg.get("gettext") is False:
                bare.add(msg["id"])
    assert expected <= ids
    assert not bare & ids  # never passed to _() upstream
    assert len(bare) == 15
    assert {"POST0_55", "POST0_56"} <= ids  # _(f"...") looks up the evaluated text
    footers = {i for i in ids if i.startswith("Utmess footer")}
    assert footers == {f"Utmess footer {k}" for k in "AEFS"}


def test_footers_are_the_upstream_msgids(catalog) -> None:
    entries, _ = catalog
    ws = re.compile(r"\s+")
    by_id = {e.ids[0]: e for e in entries if e.ids[0].startswith("Utmess footer")}
    printed = {ws.sub(" ", f).strip() for f in UTMESS_FOOTERS}
    for key, english in FOOTERS_EN.items():
        entry = by_id[f"Utmess footer {key}"]
        assert entry.msgstr == english
        assert ws.sub(" ", entry.msgid).strip() in printed


def test_mo_loads_the_way_debut_lang_en_asks_for_it(catalog, mo_dir: Path) -> None:
    """code_aster/Utilities/i18n.py: languages ['EN', 'en', variants], domain aster_messages."""
    entries, _ = catalog
    tr = gettext.translation(gettext_po.DOMAIN, str(mo_dir), languages=["EN", "en"])
    assert tr.info()["content-type"] == "text/plain; charset=UTF-8"
    assert [e.ids for e in entries if tr.gettext(e.msgid) != e.msgstr] == []
    assert tr.gettext("not a message") == "not a message"


def test_msgfmt_accepts_the_po_and_checks_formats(tmp_path: Path, catalog) -> None:
    """``msgfmt --check`` includes ``--check-format``: python-format entries keep directives."""
    stats = gettext_po.msgfmt_check(PO, tmp_path / "x.mo")
    if stats is None:
        pytest.skip("msgfmt is not installed")
    entries, _ = catalog
    assert f"{len(entries)} translated messages" in stats
    tr = gettext.GNUTranslations((tmp_path / "x.mo").open("rb"))
    assert all(tr.gettext(e.msgid) == e.msgstr for e in entries)


def test_po_entry_layout() -> None:
    text = PO.read_text(encoding="utf-8")
    assert "#. MODELISA8_14 [" in text
    assert "#: code_aster/Messages/modelisa8.py:" in text
    block = text[text.index("#. MODELISA7_77 ") :].split("\n\n")[0]
    assert "#, python-format" in block
    assert "GROUP_MA" in block


def test_same_french_with_different_english_is_refused() -> None:
    def doc(n: int, en: str) -> dict:
        msg = {"id": f"X_{n}", "fr": "même", "en": en, "method": "assisted"}
        msg.update(placeholders=[], source={"line": n})
        return {"source": {"file": "x.py"}, "messages": {str(n): msg}}

    same = gettext_po.collect([doc(1, "same"), doc(2, "same")], {})
    assert [e.ids for e in same] == [["X_1", "X_2"]]
    with pytest.raises(gettext_po.CatalogError, match="X_2: same French as X_1"):
        gettext_po.collect([doc(1, "same"), doc(2, "other")], {})


def test_cli_writes_po_and_mo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(REPO)
    po = tmp_path / "out.po"
    result = CliRunner().invoke(
        app, ["translate", "gettext", "--po", str(po), "--mo", str(tmp_path / "locale")]
    )
    assert result.exit_code == 0, result.output
    assert po.read_text(encoding="utf-8") == PO.read_text(encoding="utf-8")
    assert gettext_po.mo_path(tmp_path / "locale").is_file()
    assert not (tmp_path / "locale" / "msgfmt-check.mo").exists()
    check = CliRunner().invoke(app, ["translate", "gettext", "--check"])
    assert check.exit_code == 0, check.output


# --- English runs of the fixtures ----------------------------------------------------------


def _out(case: str, lang: str = "en") -> Path:
    return FIXTURES / case / ("output_en" if lang == "en" else "output")


def _test_lines(path: Path) -> list[tuple[str, ...]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [m.groups() for m in map(TEST_LINE.match, lines) if m]


def _current(case: str) -> bool:
    """Whether output_en was produced with the committed .po (else it predates an edit)."""
    prov = json.loads((_out(case) / "provenance.json").read_text())
    return prov["po_sha256"] == hashlib.sha256(PO.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def messages() -> MessageCatalog:
    return MessageCatalog(REPO / "en" / "messages")


@pytest.mark.parametrize("case", EN_CASES)
def test_english_run_matches_the_french_run(case: str) -> None:
    prov = json.loads((_out(case) / "provenance.json").read_text())
    assert prov["lang"] == "EN" and len(prov["po_sha256"]) == 64
    assert (_out(case) / "exit_code").read_text() == (_out(case, "fr") / "exit_code").read_text()
    english = _test_lines(_out(case) / "run.mess")
    assert english == _test_lines(_out(case, "fr") / "run.mess")
    assert all(verdict == "OK" for verdict, *_ in english)


@pytest.mark.parametrize("case", EN_CASES)
def test_english_run_prints_english_diagnostics(case: str) -> None:
    text = (_out(case) / "run.mess").read_text(encoding="utf-8")
    log = parse(_out(case) / "run.mess")
    assert [line for ev in log.events for line in ev.lines] == text.splitlines()
    for marker in ("Ceci est une alarme", "Cette erreur", "Liste des alarmes émises"):
        assert marker not in text
    assert "List of the warnings issued during the analysis." in text
    assert "Checking the mesh." in text
    for d in log.of("diagnostic"):
        if d.severity == "A":
            assert d.footer and d.footer.strip().startswith("This is a warning.")


@pytest.mark.parametrize("case", EN_CASES)
def test_renderer_recognizes_the_solver_english(case: str, messages: MessageCatalog) -> None:
    if not _current(case):
        pytest.skip(f"{case}/output_en predates the committed .po; rerun the english job")
    english = translate(parse(_out(case) / "run.mess"), messages)
    assert english.coverage()["diagnostics_not_english"] == []
    for d in english.diagnostics:
        assert d.status == "english", d.message_id
        # SUPERVIS is imported before DEBUT applies LANG, so it stays French (ADR-004 point 3).
        assert d.already_english is (not d.message_id.startswith("SUPERVIS_")), d.message_id


def test_english_modal_run_keeps_its_mode_table() -> None:
    def modes(lang: str) -> list[dict]:
        log = parse(_out("modal", lang) / "run.mess")
        return next(t for t in log.of("table") if t.name == "modes").rows

    text = (_out("modal") / "run.mess").read_text(encoding="utf-8")
    assert "number    frequency (HZ)     error norm" in text
    assert modes("en") == modes("fr") and len(modes("en")) == 6


def test_log_structure_lines_stay_french(catalog) -> None:
    """KEEP_FRENCH: run_aster's normal-end check and the stage lines are not in the catalog."""
    entries, _ = catalog
    ids = {i for e in entries for i in e.ids}
    assert not ids & set(gettext_po.KEEP_FRENCH)
    for case in EN_CASES:
        text = (_out(case) / "run.mess").read_text(encoding="utf-8")
        assert '<I> <FIN> ARRET NORMAL DANS "FIN"' in text
        assert "# Commande #0002 de " in text and "# Fin commande #0002" in text


def test_english_broken_run_gives_the_same_problem(messages: MessageCatalog) -> None:
    def problem(lang: str) -> dict:
        log = parse(_out("broken_missing_group", lang) / "run.mess")
        (p,) = translate(log, messages).problems()
        return p

    en, fr = problem("en"), problem("fr")
    for key in ("message_id", "command", "comm_line", "headline"):
        assert en[key] == fr[key]
    assert "GROUP_MA  EDGE  is not part of mesh:  00000001" in en["message"]
