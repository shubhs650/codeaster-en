"""Tests for ``caen translate messages`` (task 3.1).

The unit tests run against a small repository built in ``tmp_path`` (glossary, one family,
an upstream ``.po``) with scripted translators, so no network call is ever made. The last
tests check the family translated end-to-end in task 3.1 (``MODELISA8``) in the real repo.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from typer.testing import CliRunner

from codeaster_en import placeholders
from codeaster_en.cli import app
from codeaster_en.translate import messages as tm
from codeaster_en.translate import po
from codeaster_en.validate import glossary as glossary_validator
from codeaster_en.validate import messages as messages_validator

REPO = Path(__file__).resolve().parents[1]

GLOSSARY = """\
- {fr: maille, en: element, kind: term, note: "Never 'cell'.", aliases_en: [cell], status: machine}
- {fr: noeud, en: node, kind: term, note: "Mesh node.", aliases_en: [vertex], status: machine}
- {fr: GROUP_MA, en: element group, kind: keyword, note: "Named set of elements.", status: machine}
- {fr: PRES_REP, en: pressure, kind: keyword, note: "Distributed pressure.", status: machine}
"""

PO = r"""msgid ""
msgstr ""
"Language: en_US\n"

#, python-format
msgid ""
"\n"
" La maille %(k1)s est nulle.\n"
msgstr ""
"\n"
" The mesh %(k1)s is null.\n"

#, python-format
msgid "Le noeud %(k1)s n'existe pas"
msgstr "The node %(k2)s does not exist"

#, fuzzy, python-format
msgid "fuzzy %(i1)d"
msgstr "fuzzy %(i1)d"

msgid "vide"
msgstr ""

msgid "Erreur  dans   le groupe %(k1)s"
msgstr "Error in the group %(k1)s"

msgid "un \"guillemet\"\tet tab"
msgstr "a \"quote\"\tand tab"
"""


def _message(family: str, number: int, fr: str, **extra: Any) -> dict[str, Any]:
    return {
        "id": f"{family}_{number}",
        "fr": fr,
        "placeholders": placeholders.parse(fr).tokens,
        "source": {"line": number},
        "en": None,
        **extra,
    }


def _family_doc() -> dict[str, Any]:
    texts = {
        1: "\n La maille %(k1)s est nulle.\n",
        2: "Le noeud %(k1)s n'existe pas",
        3: "Erreur dans le groupe %(k1)s",
        4: "Attention : le GROUP_MA %(k1)s est vide, on continue.",
        5: "Valeur %(r1)12.5E hors bornes, arrêt du code.",
    }
    return {
        "_generated_from": {"upstream": "test", "file": "code_aster/Messages/fam.py"},
        "schema_version": 1,
        "family": "FAM",
        "source": {"file": "code_aster/Messages/fam.py"},
        "messages": {str(n): _message("FAM", n, fr) for n, fr in texts.items()},
    }


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "en" / "messages").mkdir(parents=True)
    (tmp_path / "en" / "glossary.yaml").write_text(GLOSSARY, encoding="utf-8")
    (tmp_path / "en" / "messages" / "FAM.en.json").write_text(
        json.dumps(_family_doc(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    po_path = tmp_path / "upstream" / po.PO_RELPATH
    po_path.parent.mkdir(parents=True)
    po_path.write_text(PO, encoding="utf-8")
    return tmp_path


def _doc(repo: Path) -> dict[str, Any]:
    return json.loads((repo / "en/messages/FAM.en.json").read_text(encoding="utf-8"))


class Scripted:
    """Translator answering from a list of ``{id: en}`` dicts, one per call."""

    label = "test:scripted"

    def __init__(self, *answers: dict[str, str], additions: list | None = None) -> None:
        self.answers = list(answers)
        self.additions = additions or []
        self.requests: list[tm.Request] = []

    def translate(self, request: tm.Request) -> tm.Answer:
        self.requests.append(request)
        given = self.answers.pop(0) if self.answers else {}
        additions, self.additions = self.additions, []
        return tm.Answer(
            {i.id: given[i.id] for i in request.items if i.id in given},
            additions,
            input_tokens=10,
            output_tokens=5,
        )


GOOD = {
    "FAM_1": "\n Element %(k1)s has zero section.\n",
    "FAM_2": "Node %(k1)s does not exist",
    "FAM_3": "Error in group %(k1)s",
    "FAM_4": "Warning: element group %(k1)s is empty; continuing.",
    "FAM_5": "Value %(r1)12.5E out of range; the run stops.",
}


# --- .po reader -------------------------------------------------------------------------


def test_po_reader_keeps_translated_singular_entries() -> None:
    entries = po.parse(PO)
    assert entries["\n La maille %(k1)s est nulle.\n"] == "\n The mesh %(k1)s is null.\n"
    assert entries['un "guillemet"\tet tab'] == 'a "quote"\tand tab'
    assert "fuzzy %(i1)d" not in entries  # fuzzy
    assert "vide" not in entries  # empty msgstr
    assert "" not in entries  # header


def test_po_reader_handles_plural_and_rejects_garbage() -> None:
    plural = 'msgid "un"\nmsgid_plural "deux"\nmsgstr[0] "one"\nmsgstr[1] "two"\n'
    assert po.parse(plural) == {}
    with pytest.raises(po.PoError):
        po.parse("msgid unquoted\n")


def test_upstream_po_matches_inventory() -> None:
    path = REPO / "upstream" / po.PO_RELPATH
    if not path.is_file():
        pytest.skip("upstream/ submodule not checked out")
    # docs/INVENTORY.md: 5,349 active, translated, non-fuzzy entries.
    assert len(po.load(path)) == 5349


# --- severity and glossary ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("fr", "level"),
    [
        ("Erreur fatale : arrêt.", "fatal"),
        ("Arrêt du code.", "fatal"),
        ("Il est impossible de calculer", "error"),
        ("ERREUR dans la commande", "error"),
        ("Alarme : on continue", "warning"),
        ("Attention, la maille est plate", "warning"),
        ("Le calcul est terminé.", "info"),
        ("Les arrêts de rigidité", "error"),
    ],
)
def test_severity_hint(fr: str, level: str) -> None:
    assert tm.severity_hint(fr) == level


def test_glossary_problems_only_for_terms_in_the_french(repo: Path) -> None:
    terms = tm.load_terms(repo / "en/glossary.yaml")
    assert tm.glossary_problems("La maille M1", "Cell M1", terms)
    assert tm.glossary_problems("La maille M1", "Element M1", terms) == []
    # "cell" is only forbidden when the French talks about a maille.
    assert tm.glossary_problems("Le noeud N1", "Cell N1", terms) == []
    # Upper-case words are identifiers, never synonyms.
    assert tm.glossary_problems("La maille M1", "Element CELL", terms) == []


def test_prompts_carry_rules_and_glossary(repo: Path) -> None:
    src = tm.load_sources(repo)
    system = tm.system_prompt(src.terms)
    assert "Placeholders are sacred" in system
    assert "- maille = element (term); never: cell" in system
    assert "- GROUP_MA =" not in system  # keyword entries go in the batch prompt when relevant
    items = [tm.Item("FAM_4", "le GROUP_MA %(k1)s", ("%(k1)s",))]
    user = tm.user_prompt("FAM", items, src.terms)
    assert "- GROUP_MA = element group (keyword)" in user
    assert "PRES_REP" not in user
    assert json.loads(user[user.index("[") :])[0]["placeholders"] == ["%(k1)s"]


# --- seeding --------------------------------------------------------------------------


def test_seed_takes_verbatim_po_entries_with_matching_placeholders(repo: Path) -> None:
    src = tm.load_sources(repo)
    report = tm.translate_family(src, "FAM", None, seed_po=True)
    assert report.seeded == 1
    msgs = _doc(repo)["messages"]
    assert msgs["1"]["en"] == "\n The mesh %(k1)s is null.\n"
    assert msgs["1"]["method"] == "machine"
    assert msgs["1"]["translation_source"] == po.SOURCE_LABEL
    assert msgs["2"]["en"] is None  # .po has %(k2)s for %(k1)s
    assert msgs["3"]["en"] is None  # whitespace differs: hint only, never seeded


def test_whitespace_normalised_po_text_is_a_hint(repo: Path) -> None:
    src = tm.load_sources(repo)
    requests = tm.build_requests("FAM", tm._items(tm.pending_messages(_doc(repo)), src), src, 20)
    by_id = {i.id: i for i in requests[0].items}
    assert by_id["FAM_3"].upstream_en == "Error in the group %(k1)s"
    assert '"upstream_en": "Error in the group %(k1)s"' in requests[0].user


# --- translation run --------------------------------------------------------------------


def test_bad_answers_are_asked_again_with_the_problem(repo: Path) -> None:
    src = tm.load_sources(repo)
    first = dict(GOOD, FAM_2="Node %(k2)s does not exist", FAM_1="\n Cell %(k1)s is null.\n")
    del first["FAM_5"]
    translator = Scripted(first, GOOD)
    report = tm.translate_family(src, "FAM", translator, batch_size=10)
    assert report.translated == 5 and report.failed == {} and report.requests == 2
    retry = translator.requests[1]
    assert retry.attempt == 1
    assert sorted(i.id for i in retry.items) == ["FAM_1", "FAM_2", "FAM_5"]
    problems = {i.id: i.problems for i in retry.items}
    assert any("missing %(k1)s" in p for p in problems["FAM_2"])
    assert any("'cell'" in p for p in problems["FAM_1"])
    assert problems["FAM_5"] == ("no translation returned for this id",)
    assert "previous_answer_problems" in retry.user

    msgs = _doc(repo)["messages"]
    assert all(m["en"] == GOOD[m["id"]] for m in msgs.values())
    assert {m["method"] for m in msgs.values()} == {"machine"}
    assert {m["translation_source"] for m in msgs.values()} == {"test:scripted"}
    assert msgs["4"]["severity_hint"] == "warning"
    assert msgs["5"]["severity_hint"] == "fatal"
    assert msgs["3"]["severity_hint"] == "error"
    issues = messages_validator.check_family(_doc(repo), "FAM")
    assert issues == []


def test_failures_stay_null_and_the_run_resumes(repo: Path) -> None:
    src = tm.load_sources(repo)
    bad = dict(GOOD, FAM_5="Value %(r1)e out of range")
    report = tm.translate_family(src, "FAM", Scripted(bad, bad, bad), retries=2)
    assert list(report.failed) == ["FAM_5"]
    assert report.requests == 3
    assert _doc(repo)["messages"]["5"]["en"] is None

    again = Scripted(GOOD)
    report = tm.translate_family(src, "FAM", again)
    assert report.pending == 1 and report.translated == 1
    assert [i.id for i in again.requests[0].items] == ["FAM_5"]


def test_batches_are_written_one_by_one(repo: Path) -> None:
    src = tm.load_sources(repo)

    class Boom(Scripted):
        def translate(self, request: tm.Request) -> tm.Answer:
            if request.batch == 2:
                raise RuntimeError("network down")
            return super().translate(request)

    with pytest.raises(RuntimeError):
        tm.translate_family(src, "FAM", Boom(GOOD), batch_size=2)
    msgs = _doc(repo)["messages"]
    assert [m["en"] is not None for m in msgs.values()] == [True, True, False, False, False]


def test_stale_and_force_never_touch_reviewed(repo: Path) -> None:
    doc = _doc(repo)
    doc["messages"]["1"].update(en="old", method="machine", stale=True)
    doc["messages"]["2"].update(
        en="Node %(k1)s is missing", method="reviewed", reviewed_by="X", reviewed_on="2026-01-01"
    )
    doc["messages"]["3"].update(en="Error in group %(k1)s", method="assisted")
    (repo / "en/messages/FAM.en.json").write_text(json.dumps(doc), encoding="utf-8")
    src = tm.load_sources(repo)
    pending = {m["id"] for m in tm.pending_messages(_doc(repo))}
    assert pending == {"FAM_1", "FAM_4", "FAM_5"}
    forced = {m["id"] for m in tm.pending_messages(_doc(repo), force=True)}
    assert forced == {"FAM_1", "FAM_3", "FAM_4", "FAM_5"}
    tm.translate_family(src, "FAM", Scripted(GOOD), force=True, seed_po=True)
    msgs = _doc(repo)["messages"]
    assert msgs["2"]["en"] == "Node %(k1)s is missing" and msgs["2"]["method"] == "reviewed"
    assert "stale" not in msgs["1"]
    # force + seed: the .po seed never replaces an assisted translation, the model does.
    assert msgs["3"]["en"] == GOOD["FAM_3"]


def test_glossary_additions_are_appended_as_proposed(repo: Path) -> None:
    src = tm.load_sources(repo)
    additions = [
        {"fr": "section", "en": "cross-section", "kind": "term", "note": "Beam section."},
        {"fr": "maille", "en": "cell", "kind": "term", "note": "already there"},
        {"fr": "bad", "en": "x", "kind": "nonsense", "note": ""},
    ]
    report = tm.translate_family(src, "FAM", Scripted(GOOD, additions=additions))
    assert report.glossary_added == ["section"]
    path = repo / "en/glossary.yaml"
    assert glossary_validator.validate(path) == []
    entry = glossary_validator.load(path)[-1]
    assert entry["fr"] == "section" and entry["status"] == "proposed"


def test_method_reviewed_is_refused(repo: Path) -> None:
    with pytest.raises(tm.TranslateError):
        tm.translate_family(tm.load_sources(repo), "FAM", Scripted(), method="reviewed")


# --- backends -----------------------------------------------------------------------------


class FakeClient:
    def __init__(self, text: str, stop_reason: str = "end_turn") -> None:
        self.calls: list[dict[str, Any]] = []
        response = SimpleNamespace(
            stop_reason=stop_reason,
            content=[SimpleNamespace(type="text", text=text)],
            usage=SimpleNamespace(input_tokens=100, output_tokens=20),
        )

        def create(**kwargs: Any) -> Any:
            self.calls.append(kwargs)
            return response

        self.beta = SimpleNamespace(messages=SimpleNamespace(create=create))


def _request() -> tm.Request:
    item = tm.Item("FAM_2", "Le noeud %(k1)s n'existe pas", ("%(k1)s",))
    return tm.Request("FAM", 1, 0, "SYSTEM", "USER", (item,))


def test_anthropic_backend_request_shape() -> None:
    reply = {"translations": [{"id": "FAM_2", "en": "Node %(k1)s does not exist"}]}
    client = FakeClient(json.dumps({**reply, "glossary_additions": []}))
    answer = tm.AnthropicTranslator(client=client).translate(_request())
    assert answer.translations == {"FAM_2": "Node %(k1)s does not exist"}
    assert (answer.input_tokens, answer.output_tokens) == (100, 20)
    call = client.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["output_config"]["format"]["schema"] == tm.OUTPUT_SCHEMA
    assert call["output_config"]["effort"] == "medium"
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert call["fallbacks"] == "default"
    assert call["betas"] == ["server-side-fallback-2026-07-01"]
    assert "temperature" not in call


@pytest.mark.parametrize(
    ("stop", "text", "error"),
    [("refusal", "", "refusal"), ("max_tokens", "{", "max_tokens"), ("end_turn", "nope", "JSON")],
)
def test_anthropic_backend_failures_fail_the_batch(stop: str, text: str, error: str) -> None:
    answer = tm.AnthropicTranslator(client=FakeClient(text, stop)).translate(_request())
    assert answer.translations == {} and error in (answer.error or "")


def test_replay_backend_reads_both_line_forms(tmp_path: Path) -> None:
    path = tmp_path / "answers.jsonl"
    path.write_text(
        "# comment\n"
        '{"id": "FAM_2", "en": "first"}\n'
        '{"translations": [{"id": "FAM_2", "en": "Node %(k1)s does not exist"}],'
        ' "glossary_additions": [{"fr": "a", "en": "b", "kind": "term", "note": ""}]}\n',
        encoding="utf-8",
    )
    replay = tm.ReplayTranslator(path, "session:test")
    answer = replay.translate(_request())
    assert answer.translations == {"FAM_2": "Node %(k1)s does not exist"}
    assert len(answer.glossary_additions) == 1
    assert replay.translate(_request()).glossary_additions == []
    assert replay.label == "session:test"
    path.write_text('{"id": 3}\n', encoding="utf-8")
    with pytest.raises(tm.TranslateError):
        tm.ReplayTranslator(path)


# --- estimate, export, CLI ------------------------------------------------------------------


def test_dry_run_estimates_and_writes_nothing(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    before = (repo / "en/messages/FAM.en.json").read_bytes()
    monkeypatch.chdir(repo)
    result = CliRunner().invoke(app, ["translate", "messages", "-f", "FAM", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "FAM: 5 message(s), 1 request(s)" in result.output
    assert "$" in result.output
    assert (repo / "en/messages/FAM.en.json").read_bytes() == before
    est = tm.estimate(tm.load_sources(repo), "FAM", "claude-opus-5-5", 2, seed_po=True)
    assert est.items == 4 and est.requests == 2 and (est.cost_usd or 0) > 0
    assert tm.estimate(tm.load_sources(repo), "FAM", "other-model", 2).cost_usd is None


def test_cli_export_then_import(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(repo)
    runner = CliRunner()
    out = repo / "requests.jsonl"
    result = runner.invoke(
        app, ["translate", "messages", "-f", "FAM", "--seed-po", "--export-requests", str(out)]
    )
    assert result.exit_code == 0, result.output
    request = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert request["ids"] == ["FAM_2", "FAM_3", "FAM_4", "FAM_5"]
    assert request["schema"] == tm.OUTPUT_SCHEMA

    answers = repo / "answers.jsonl"
    answers.write_text(
        "".join(json.dumps({"id": k, "en": v}) + "\n" for k, v in GOOD.items() if k != "FAM_1"),
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        ["translate", "messages", "-f", "FAM", "--seed-po", "--responses", str(answers)]
        + ["--method", "assisted", "--source", "session:test"],
    )
    assert result.exit_code == 0, result.output
    assert "FAM: 1 seeded, 4/4 translated, 0 failed" in result.output
    msgs = _doc(repo)["messages"]
    assert msgs["1"]["method"] == "machine" and msgs["2"]["method"] == "assisted"
    assert msgs["2"]["translation_source"] == "session:test"


def test_cli_reports_failures_with_exit_code(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(repo)
    answers = repo / "answers.jsonl"
    answers.write_text('{"id": "FAM_2", "en": "Node %(k2)s"}\n', encoding="utf-8")
    result = CliRunner().invoke(
        app, ["translate", "messages", "-f", "FAM", "--responses", str(answers), "--retries", "0"]
    )
    assert result.exit_code == 1
    assert "FAM_2: not translated: en is missing %(k1)s" in result.output
    result = CliRunner().invoke(app, ["translate", "messages", "-f", "NOPE", "--dry-run"])
    assert result.exit_code == 1 and "no message family" in result.output


# --- the family translated in task 3.1 ------------------------------------------------------


def test_modelisa8_is_fully_translated_with_valid_placeholders() -> None:
    path = REPO / "en/messages/MODELISA8.en.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert messages_validator.check_family(doc, "MODELISA8") == []
    msgs = list(doc["messages"].values())
    assert msgs and all(isinstance(m["en"], str) for m in msgs)
    assert all(placeholders.compare(m["fr"], m["en"]) == [] for m in msgs)
    assert all(m["method"] in {"machine", "assisted"} for m in msgs)
    assert all(m["severity_hint"] == tm.severity_hint(m["fr"]) for m in msgs)
    terms = tm.load_terms(REPO / "en/glossary.yaml")
    assert [m["id"] for m in msgs if tm.glossary_problems(m["fr"], m["en"], terms)] == []
