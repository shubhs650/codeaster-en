"""Tests for the ``.mess`` parser (task 4.3) on every committed fixture log.

The three reference runs end normally; the four ``broken_*`` runs fail on purpose (missing
group, singular matrix, bad keyword, invalid Python). All logs come from the solver
(``scripts/run-fixture.sh``), so no solver is run here.
"""

from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path

import pytest
from typer.testing import CliRunner

from codeaster_en.cli import app
from codeaster_en.mess import (
    Diagnostic,
    FailureClass,
    Stage,
    StageEnd,
    Text,
    classify,
    parse,
    parse_lines,
    stream,
)
from codeaster_en.mess.commlines import changed_text, line_mapper

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"
GOOD = ("solid_static", "shell_static", "modal")
BROKEN = (
    "broken_missing_group",
    "broken_singular_matrix",
    "broken_bad_keyword",
    "broken_python_syntax",
)
CASES = GOOD + BROKEN

# case -> (first error ID, failed command, text of the faulty .comm line)
EXPECTED_FAILURES = {
    "broken_missing_group": ("MODELISA7_77", "AFFE_CHAR_MECA", 'GROUP_MA="EDGE"'),
    "broken_singular_matrix": ("FACTOR_11", "MECA_STATIQUE", "RESU = MECA_STATIQUE("),
    "broken_bad_keyword": ("SUPERVIS_4", "AFFE_CHAR_MECA", "PRESSION=Q"),
}


def _mess(case: str) -> Path:
    return FIXTURES / case / "output" / "run.mess"


def _lines(case: str) -> list[str]:
    return _mess(case).read_text(encoding="utf-8").splitlines()


def _comm(case: str) -> list[str]:
    return (FIXTURES / case / "input" / "run.comm").read_text(encoding="utf-8").splitlines()


@pytest.fixture(scope="module")
def logs():
    return {case: parse(_mess(case)) for case in CASES}


# -- every line is classified, none is lost --------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_events_cover_every_line_in_order(case, logs):
    log = logs[case]
    expected = 1
    for ev in log.events:
        assert ev.start == expected, (case, ev.kind, ev.start)
        assert ev.lines, (case, ev.kind, ev.start)
        expected = ev.end + 1
    assert [line for ev in log.events for line in ev.lines] == _lines(case)
    assert log.lines == len(_lines(case))


@pytest.mark.parametrize("case", CASES)
def test_structural_lines_land_in_their_event(case, logs):
    owner = {}
    for ev in logs[case].events:
        for n in range(ev.start, ev.end + 1):
            owner[n] = ev
    for n, line in enumerate(_lines(case), start=1):
        if line.startswith(" ╔") or re.match(r"^ ║ <[A-Za-z_]+> <[A-Z0-9_]+>", line):
            assert isinstance(owner[n], Diagnostic), (case, n, line)
        if line.startswith("# Commande #"):
            assert isinstance(owner[n], Stage), (case, n, line)
        if line.startswith(("# Fin commande #", "# Résultat commande #")):
            assert isinstance(owner[n], StageEnd), (case, n, line)
        if line.startswith("Traceback (most recent call last)"):
            assert owner[n].kind == "traceback", (case, n, line)
        if line.startswith("--- DIAGNOSTIC JOB"):
            assert owner[n].kind == "summary", (case, n, line)
        if re.match(r"^ (OK|NOOK) ", line):
            assert owner[n].kind == "table", (case, n, line)


@pytest.mark.parametrize("case", CASES)
def test_diagnostic_ids_join_the_english_catalogue(case, logs):
    """Every message ID the parser extracts names a message in en/messages (task 4.4 join)."""
    for d in logs[case].of("diagnostic"):
        assert d.message_id and d.family and d.number is not None, (case, d.start)
        data = json.loads((REPO / "en" / "messages" / f"{d.family}.en.json").read_text())
        assert str(d.number) in data["messages"], d.message_id
        assert d.body and not d.body.startswith(("<", "\n")), d.message_id


# -- reference runs --------------------------------------------------------------------------


@pytest.mark.parametrize("case", GOOD)
def test_reference_runs_summary(case, logs):
    log = logs[case]
    s = log.summary()
    assert s["diagnostic_job"] == "OK"
    assert s["exit_code"] == 0
    assert s["closed_normally"] is True
    assert s["errors"] == []
    assert s["version"] == "17.4.22"
    assert s["failed_stage"] is None and s["exception"] is None
    printed = sum(1 for line in _lines(case) if re.match(r"^ OK ", line))
    assert s["test_resu"] == {"OK": printed} and printed > 0
    assert s["total_elapsed_s"] > 0
    assert classify(log).failure_class is None


@pytest.mark.parametrize("case", GOOD)
def test_stages_have_start_end_and_comm_line(case, logs):
    comm = _comm(case)
    stages = logs[case].stages()
    numbered = [s for s in stages if "start" in s]
    assert len(numbered) >= 10
    for s in numbered:
        assert s["completed"], s
        assert s["command"] and re.fullmatch(r"[A-Z][A-Z0-9_]*", s["command"])
        if s["command"] == "FIN":  # run from the installed fin.py, not from run.comm
            assert s["comm_line"] is None
            continue
        line = comm[s["comm_line"] - 1]
        assert s["command"] in line, (s, line)
        if s["concept"]:
            assert line.startswith(s["concept"]), (s, line)


def test_shell_static_test_resu_rows(logs):
    table = next(t for t in logs["shell_static"].of("table") if t.name == "test_resu")
    analytic = {r["LEGENDE"]: r for r in table.rows if r["REFERENCE"] == "ANALYTIQUE"}
    assert set(analytic) == {"W_CENTER", "MXX_CENTER", "REAC_DZ_SUM"}
    assert analytic["W_CENTER"]["VALE_REFE"] == -2.11242
    assert analytic["W_CENTER"]["VALE_CALC"] == pytest.approx(-2.1122638)
    assert analytic["W_CENTER"]["context"]["GROUP_NO"] == "CENTER"
    assert analytic["REAC_DZ_SUM"]["context"]["TYPE_TEST"] == "SOMM"


def test_shell_static_ignored_alarm_is_reported(logs):
    s = logs["shell_static"].summary()
    assert s["alarms"] == {"MODELISA8_14": 3}
    assert s["ignored_alarms"] == ["MODELISA8_14"]


def test_modal_frequency_table(logs):
    table = next(t for t in logs["modal"].of("table") if t.name == "modes")
    freqs = [r["frequency_hz"] for r in table.rows]
    assert [r["mode"] for r in table.rows] == [1, 2, 3, 4, 5, 6]
    assert freqs == sorted(freqs)
    assert freqs[0] == pytest.approx(52.3396)
    assert freqs[-1] == pytest.approx(1497.03)
    assert table.lines[-1].startswith("Norme d'erreur moyenne")


def test_header_fields(logs):
    header = logs["solid_static"].of("header")[0]
    assert header.version == "17.4.22"
    assert header.message_language == "en (UTF-8)"
    assert header.fields["Nombre de processeurs MPI utilisés"] == "1"


def test_wrapped_command_header_and_result_type(logs):
    stages = {s["number"]: s for s in logs["modal"].stages()}
    fin = next(s for s in stages.values() if s.get("command") == "FIN")
    assert fin["source_line"] == 76
    fin_stage = next(e for e in logs["modal"].of("stage") if e.command == "FIN")
    # The path was wrapped at 100 columns; the "." dropped at the break is restored.
    assert "/code-aster-17.4.22-" in fin_stage.source_file
    assert fin_stage.source_file.endswith("/CodeCommands/fin.py")
    wrapped = [
        s for s in stages.values() if s.get("result_type") == "AssemblyMatrixDisplacementReal"
    ]
    assert len(wrapped) == 2


# -- broken runs -----------------------------------------------------------------------------


@pytest.mark.parametrize("case", sorted(EXPECTED_FAILURES))
def test_broken_runs_point_at_the_fault(case, logs):
    message_id, command, fault = EXPECTED_FAILURES[case]
    log = logs[case]
    s = log.summary()
    assert s["diagnostic_job"] == "<S>_ERROR"
    assert s["exit_code"] == 1
    assert s["errors"] == [message_id]
    assert s["alarms"] == {"MODELISA8_14": 3}
    stage = s["failed_stage"]
    assert stage["command"] == command
    assert fault in "\n".join(_comm(case)[stage["comm_line"] - 1 : stage["comm_line"] + 8])
    assert s["exception"]["comm_line"] == stage["comm_line"]
    result = classify(log)
    assert result.failure_class is FailureClass.USER_MODEL
    assert result.message_id == message_id
    assert case in result.evidence


def test_broken_python_syntax(logs):
    log = logs["broken_python_syntax"]
    s = log.summary()
    assert s["diagnostic_job"] == "<F>_SYNTAX_ERROR"
    assert s["exception"]["type"] == "SyntaxError"
    assert "comma" in s["exception"]["message"]
    comm = _comm("broken_python_syntax")
    assert comm[s["exception"]["comm_line"] - 1].strip() == '_F(GROUP_MA="EDGES", DZ=0.0)'
    result = classify(log)
    assert result.failure_class is FailureClass.USER_MODEL
    assert result.diagnostic_job == "<F>_SYNTAX_ERROR"


def test_repeated_boxes_are_flagged(logs):
    boxes = logs["broken_bad_keyword"].of("diagnostic")
    supervis = [d for d in boxes if d.message_id == "SUPERVIS_4"]
    assert [d.repeat for d in supervis] == [False, True, True]
    assert [d.message_id for d in logs["broken_bad_keyword"].errors] == ["SUPERVIS_4"]
    assert supervis[0].body.splitlines()[0] == "Erreur de syntaxe dans AFFE_CHAR_MECA"
    assert supervis[0].severity == "EXCEPTION" and supervis[0].stage == 10


def test_alarm_footer_is_split_from_the_body(logs):
    alarm = next(d for d in logs["broken_missing_group"].diagnostics if d.severity == "A")
    assert alarm.message_id == "MODELISA8_14"
    assert alarm.body == "La maille POI1 1 est incluse dans une autre."
    assert alarm.footer.startswith("Ceci est une alarme.")
    singular = next(d for d in logs["broken_singular_matrix"].errors)
    assert singular.body.startswith("Problème : la matrice est singulière")
    assert singular.footer is None  # EXCEPTION boxes carry no Utmess comment


# -- robustness and streaming ----------------------------------------------------------------


def test_truncated_log_keeps_every_line():
    lines = _lines("broken_singular_matrix")
    cut = next(i for i, line in enumerate(lines) if "<EXCEPTION> <FACTOR_11>" in line) + 3
    log = parse_lines(lines[:cut])
    assert [line for ev in log.events for line in ev.lines] == lines[:cut]
    assert log.events[-1].kind == "diagnostic" and log.events[-1].message_id == "FACTOR_11"


def test_unknown_text_falls_back_verbatim():
    lines = ["something the parser has never seen", "", "  another one ║", "<X> odd"]
    log = parse_lines(lines)
    assert [ev.kind for ev in log.events] == ["text", "blank", "text"]
    assert all(isinstance(ev, Text) for ev in log.of("text"))
    assert [line for ev in log.events for line in ev.lines] == lines


def test_stream_without_follow_equals_parse(logs):
    events = list(stream(_mess("modal"), follow=False))
    assert [e.to_dict() for e in events] == [e.to_dict() for e in logs["modal"].events]


def test_stream_follows_a_growing_file(tmp_path, logs):
    src = _lines("broken_missing_group")
    target = tmp_path / "run.mess"

    def writer() -> None:
        with target.open("w", encoding="utf-8") as fobj:
            for k, line in enumerate(src):
                fobj.write(line + "\n")
                if k % 50 == 0:
                    fobj.flush()
                    time.sleep(0.01)

    thread = threading.Thread(target=writer)
    thread.start()
    events = list(stream(target, poll=0.01, idle_timeout=5))
    thread.join()
    assert [line for ev in events for line in ev.lines] == src
    assert [e.kind for e in events] == [e.kind for e in logs["broken_missing_group"].events]


def test_comm_line_mapper_matches_run_aster_shift():
    comm = "# a comment\n\nDEBUT()\n\nMAIL = LIRE_MAILLAGE(UNITE=20)\nFIN()\n"
    text = changed_text(comm).splitlines()
    assert text[0] == "# coding=utf-8"
    to_comm = line_mapper(comm)
    assert to_comm(text.index("DEBUT()") + 1) == 3
    assert to_comm(text.index("MAIL = LIRE_MAILLAGE(UNITE=20)") + 1) == 5
    assert to_comm(1) is None


def test_classify_without_log_and_resource_rule():
    assert classify(None).failure_class is FailureClass.PLATFORM
    lines = [
        "-" * 60,
        "--- DIAGNOSTIC JOB : <S>_CPU_LIMIT",
        "-" * 60,
        "EXECUTION_CODE_ASTER_EXIT_10=4",
    ]
    result = classify(parse_lines(lines))
    assert result.failure_class is FailureClass.USER_RESOURCES
    assert "TODO(verify)" in result.evidence
    unknown = classify(parse_lines(["-" * 60, "--- DIAGNOSTIC JOB : <S>_NO_CONVERGENCE"]), 1)
    assert unknown.failure_class is FailureClass.UNKNOWN


def test_cli_mess_parse(tmp_path):
    out = tmp_path / "run.json"
    result = CliRunner().invoke(
        app, ["mess", "parse", str(_mess("broken_missing_group")), "--out", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert "user-model in AFFE_CHAR_MECA (command #9)" in result.output
    data = json.loads(out.read_text())
    assert data["classification"]["failure_class"] == "user-model"
    assert data["summary"]["errors"] == ["MODELISA7_77"]
    assert data["events"][0]["lines"]
    missing = CliRunner().invoke(app, ["mess", "parse", str(tmp_path / "nope.mess")])
    assert missing.exit_code == 1
