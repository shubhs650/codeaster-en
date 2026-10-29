"""Tests for the English ``.mess`` renderer (task 4.4) on every committed fixture log.

Acceptance (docs/PLAN.md 4.4): every diagnostic in the fixtures renders in English, and the
broken runs give an English, actionable account of what stopped them.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from codeaster_en.cli import app
from codeaster_en.mess import parse, parse_lines
from codeaster_en.mess.catalog import MessageCatalog, Template
from codeaster_en.mess.render import FOOTERS_EN, match_lines, translate
from codeaster_en.placeholders import parse as parse_placeholders

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"
MESSAGES = REPO / "en" / "messages"
CASES = (
    "solid_static",
    "shell_static",
    "modal",
    "broken_missing_group",
    "broken_singular_matrix",
    "broken_bad_keyword",
    "broken_python_syntax",
)

# case -> (message ID, command, recovered arguments, words the English headline must contain)
EXPECTED_PROBLEMS = {
    "broken_missing_group": (
        "MODELISA7_77",
        "AFFE_CHAR_MECA",
        {"%(k1)s": "EDGE", "%(k2)s": "00000001"},
        ("GROUP_MA", "EDGE", "is not part of mesh"),
    ),
    "broken_singular_matrix": (
        "FACTOR_11",
        "MECA_STATIQUE",
        {"%(i1)d": "517"},
        ("matrix is singular", "row 517"),
    ),
    "broken_bad_keyword": (
        "SUPERVIS_4",
        "AFFE_CHAR_MECA",
        {
            "%(k1)s": "AFFE_CHAR_MECA",
            "%(k2)s": "At least one argument of ('PRES', 'CISA_2D') must be defined",
        },
        ("Syntax error in AFFE_CHAR_MECA",),
    ),
}

FRENCH_MARKERS = ("Ceci est une alarme", "Cette erreur", " ne fait pas partie", "Problème :")


@pytest.fixture(scope="module")
def catalog() -> MessageCatalog:
    return MessageCatalog(MESSAGES)


@pytest.fixture(scope="module")
def rendered(catalog: MessageCatalog):
    return {
        case: translate(parse(FIXTURES / case / "output" / "run.mess"), catalog) for case in CASES
    }


# --- templates ------------------------------------------------------------------------------


def _sample_args(fr: str) -> dict[str, object]:
    args: dict[str, object] = {}
    for ph in parse_placeholders(fr).placeholders:
        if ph.key is None:
            continue
        conv = ph.conversion
        if conv in "diuxXoc":
            args[ph.key] = 7
        elif conv in "eEfFgG":
            args[ph.key] = 1.5
        else:
            args[ph.key] = f"V{ph.key.upper()}"
    return args


def test_every_french_template_recovers_its_own_arguments(catalog: MessageCatalog) -> None:
    """Format each of the 6,890 French texts like Utmess does, then match it back."""
    ws = re.compile(r"\s+")
    failures = []
    for tpl in catalog.templates.values():
        printed = (tpl.fr % _sample_args(tpl.fr)).strip()
        args = tpl.recover(printed)
        if args is None:
            failures.append(tpl.id)
            continue
        rebuilt = tpl.fr.strip()
        for spec, value in args.items():
            rebuilt = rebuilt.replace(spec, value)
        rebuilt = rebuilt.replace("%%", "%")
        if ws.sub(" ", rebuilt).strip() != ws.sub(" ", printed).strip():
            failures.append(tpl.id)
    assert failures == []
    assert len(catalog.templates) == 6890


def test_whitespace_and_wrapping_are_flexible() -> None:
    tpl = Template("X_1", "\n le GROUP_MA  %(k1)s  ne fait pas partie du maillage :  %(k2)s\n")
    assert tpl.recover("le GROUP_MA EDGE ne fait pas\npartie du maillage : 00000001") == {
        "%(k1)s": "EDGE",
        "%(k2)s": "00000001",
    }
    assert tpl.recover("le GROUP_MA EDGE ne fait pas partie du modèle : 00000001") is None


def test_repeated_placeholder_must_print_the_same_text() -> None:
    tpl = Template("X_2", "%(k1)s et encore %(k1)s fin")
    assert tpl.recover("A et encore A fin") == {"%(k1)s": "A"}
    assert tpl.recover("A et encore B fin") is None


def test_fill_keeps_numeric_format_and_literal_percent() -> None:
    tpl = Template(
        "X_3",
        "# Fin commande #%(i1)04d taux %(r1)6.3f %%",
        en="# End of command #%(i1)04d ratio %(r1)6.3f %%",
    )
    args = tpl.recover("# Fin commande #0012 taux  1.913 %")
    # The padding went to the whitespace run; fill() applies the width again.
    assert args == {"%(i1)04d": "0012", "%(r1)6.3f": "1.913"}
    assert tpl.fill(args) == "# End of command #0012 ratio  1.913 %"
    assert Template("X_4", "a %(k1)s").fill({"%(k1)s": "b"}) is None  # no English yet


def test_free_text_matching_and_verbatim_lines(catalog: MessageCatalog) -> None:
    lines = [
        "# Commande #0002 de run.comm.changed.py, ligne 24",
        "une ligne que le catalogue ne connaît pas",
        "",
        "# Résultat commande #0002 (LIRE_MAILLAGE): MAIL ('<00000001>') de type <Mesh>",
    ]
    segs = match_lines(lines, catalog)
    assert [(s.message_id, s.status) for s in segs] == [
        ("SUPERVIS2_71", "english"),
        (None, "verbatim"),
        (None, "blank"),
        ("SUPERVIS2_72", "english"),
    ]
    assert segs[0].args == {"%(i1)04d": "0002", "%(k1)s": "run.comm.changed.py", "%(i2)d": "24"}
    assert segs[0].en == "# Command #0002 from run.comm.changed.py, line 24"
    # SUPERVIS2_76 (" de type <...>") is nested in SUPERVIS2_72's argument.
    assert segs[3].en == (
        "# Result of command #0002 (LIRE_MAILLAGE): MAIL ('<00000001>') of type <Mesh>"
    )


# --- fixtures -------------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_every_fixture_diagnostic_renders_in_english(case: str, rendered) -> None:
    english = rendered[case]
    for d in english.diagnostics:
        assert d.status == "english", (d.message_id, d.status)
        assert d.en
        if d.severity == "A":
            assert d.footer_en == FOOTERS_EN["A"]
    cov = english.coverage()
    assert cov["diagnostics_not_english"] == []
    assert cov["untranslated_messages"] == []


@pytest.mark.parametrize("case", CASES)
def test_rendered_log_keeps_layout_and_command_echo(case: str, rendered) -> None:
    english = rendered[case]
    text = english.to_text()
    original = (FIXTURES / case / "output" / "run.mess").read_text(encoding="utf-8")
    assert text.count(" ╔") == original.count(" ╔")
    for marker in FRENCH_MARKERS:
        assert marker not in text
    # The user's commands are echoed exactly as printed (French names are the solver's API).
    for ev in english.events:
        if ev.event.kind == "stage":
            echo = [line for line in ev.event.lines if not line.startswith(("#", ".."))]
            out = ev.lines()
            for line in echo:
                assert line in out
    # Box lines have the width Utilities/strfunc.py textbox gives them (99 columns).
    widths = {len(line) for line in original.splitlines() if line.startswith(" ║")}
    for line in text.splitlines():
        if line.startswith(" ║"):
            assert {len(line)} == widths, line


@pytest.mark.parametrize("case", sorted(EXPECTED_PROBLEMS))
def test_broken_runs_give_english_actionable_errors(case: str, rendered) -> None:
    message_id, command, args, words = EXPECTED_PROBLEMS[case]
    english = rendered[case]
    problems = english.problems()
    assert len(problems) == 1
    problem = problems[0]
    assert problem["message_id"] == message_id
    assert problem["command"] == command
    assert problem["english"] is True
    for word in words:
        assert word in problem["headline"]
    # The command file line points at the failing command in the user's .comm.
    comm = (FIXTURES / case / "input" / "run.comm").read_text(encoding="utf-8").splitlines()
    assert command in comm[problem["comm_line"] - 1]
    diag = next(d for d in english.diagnostics if d.message_id == message_id)
    assert diag.args == args
    assert english.classification.failure_class == "user-model"


def test_python_syntax_error_is_reported_with_its_line(rendered) -> None:
    english = rendered["broken_python_syntax"]
    (problem,) = english.problems()
    assert problem["kind"] == "exception"
    comm = (FIXTURES / "broken_python_syntax" / "input" / "run.comm").read_text(encoding="utf-8")
    faulty = comm.splitlines()[problem["comm_line"] - 1]
    assert '_F(GROUP_MA="EDGES", DZ=0.0)' in faulty
    assert problem["headline"].startswith("Python SyntaxError at line")


def test_good_runs_report_no_problem(rendered) -> None:
    for case in ("solid_static", "shell_static", "modal"):
        assert rendered[case].problems() == []
        assert not rendered[case].classification.failed


def test_warning_list_box_holds_several_messages(rendered) -> None:
    box = next(
        d for d in rendered["broken_missing_group"].diagnostics if d.message_id == "CATAMESS_89"
    )
    assert box.en.strip().startswith("List of the warnings issued")
    assert [e["message_id"] for e in box.extra] == ["CATAMESS_90"]
    assert "MODELISA8_14" in box.extra[0]["en"] and "issued" in box.extra[0]["en"]


# --- untranslated and unknown messages ------------------------------------------------------


def _catalog_without(tmp_path: Path, family: str, number: str) -> MessageCatalog:
    for path in MESSAGES.glob("*.en.json"):
        shutil.copy(path, tmp_path / path.name)
    path = tmp_path / f"{family}.en.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["messages"][number]["en"] = None
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return MessageCatalog(tmp_path)


def test_untranslated_message_keeps_french_and_says_so(tmp_path: Path) -> None:
    catalog = _catalog_without(tmp_path, "MODELISA7", "77")
    english = translate(parse(FIXTURES / "broken_missing_group" / "output" / "run.mess"), catalog)
    diag = next(d for d in english.diagnostics if d.message_id == "MODELISA7_77")
    assert diag.status == "untranslated"
    assert diag.args == {"%(k1)s": "EDGE", "%(k2)s": "00000001"}
    text = english.to_text()
    assert "le GROUP_MA  EDGE  ne fait pas partie" in text
    assert "no English translation yet" in text
    assert english.coverage()["diagnostics_not_english"] == ["MODELISA7_77"]
    (problem,) = english.problems()
    assert problem["english"] is False


def test_unknown_id_and_mismatched_body() -> None:
    box = [
        " ╔" + "=" * 96 + "╗",
        " ║ <A> <NOSUCH_1>" + " " * 79 + "║",
        " ║" + " " * 96 + "║",
        " ║ Texte inconnu." + " " * 80 + "║",
        " ╚" + "=" * 96 + "╝",
    ]
    english = translate(parse_lines(box))
    (diag,) = english.diagnostics
    assert diag.status == "unknown-id"
    box[1] = box[1].replace("NOSUCH_1", "MODELISA7_77")
    (diag,) = translate(parse_lines(box)).diagnostics
    assert diag.status == "no-args"


# --- CLI ------------------------------------------------------------------------------------


def test_cli_translate_writes_english_log_and_json(tmp_path: Path) -> None:
    mess = FIXTURES / "broken_missing_group" / "output" / "run.mess"
    result = CliRunner().invoke(
        app, ["mess", "translate", str(mess), "--out-dir", str(tmp_path), "--strict"]
    )
    assert result.exit_code == 0, result.output
    assert "diagnostics in English: 5/5" in result.output
    assert "AFFE_CHAR_MECA (command file line 33) failed" in result.output
    text = (tmp_path / "run.en.mess").read_text(encoding="utf-8")
    assert "GROUP_MA  EDGE  is not part of mesh:  00000001" in text
    data = json.loads((tmp_path / "run.en.json").read_text(encoding="utf-8"))
    assert data["language"] == "en"
    assert data["classification"]["failure_class"] == "user-model"
    assert data["problems"][0]["comm_line"] == 33
    assert (
        data["_generated_from"]["messages_upstream"]
        == (REPO / "UPSTREAM_VERSION").read_text(encoding="utf-8").strip()
    )


def test_cli_strict_fails_on_untranslated_diagnostic(tmp_path: Path) -> None:
    messages = tmp_path / "messages"
    messages.mkdir()
    _catalog_without(messages, "MODELISA7", "77")
    mess = FIXTURES / "broken_missing_group" / "output" / "run.mess"
    args = ["mess", "translate", str(mess), "--out-dir", str(tmp_path)]
    args += ["--messages", str(messages), "--strict"]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 1
    assert "not: MODELISA7_77" in result.output
    missing = CliRunner().invoke(app, ["mess", "translate", str(tmp_path / "nope.mess")])
    assert missing.exit_code == 1


def test_streamed_events_render_like_the_whole_log(catalog: MessageCatalog, rendered) -> None:
    from codeaster_en.mess import render_event, stream

    mess = FIXTURES / "broken_singular_matrix" / "output" / "run.mess"
    lines = []
    for ev in stream(mess, follow=False):
        lines.extend(render_event(ev, catalog).lines())
    whole = rendered["broken_singular_matrix"].to_text().splitlines()[2:]
    assert lines == whole
