"""LLM context bundle checks (task 5.5, ADR-025): content, structure, size budget, CLI."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from codeaster_en import bundle
from codeaster_en.cli import app
from codeaster_en.validate import glossary as glossary_validator

REPO = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^```[a-z]*\n.*?^```$", re.S | re.M)


@pytest.fixture(scope="module")
def compact() -> bundle.Bundle:
    return bundle.build(REPO, "1", "compact")


@pytest.fixture(scope="module")
def full() -> bundle.Bundle:
    return bundle.build(REPO, "1", "full")


def _headings(text: str) -> list[tuple[int, str]]:
    """(line number, heading line) outside fenced code blocks."""
    out, fence = [], False
    for number, line in enumerate(text.split("\n"), start=1):
        if line.startswith("```"):
            fence = not fence
        elif not fence and re.match(r"#{1,6} ", line):
            out.append((number, line))
    return out


def test_tier_commands_follow_command_set() -> None:
    names, key = bundle.tier_commands(REPO, "1")
    assert names[:3] == ["DEBUT", "FIN", "POURSUITE"]
    assert "MECA_STATIQUE" in names and "CALC_MODES" not in names
    assert {"DDL_IMPO", "PRES_REP"} <= key["AFFE_CHAR_MECA"]
    names2, _ = bundle.tier_commands(REPO, "2")
    assert names2[: len(names)] == names and "CALC_MODES" in names2
    assert len(names2) == len(set(names2))
    with pytest.raises(bundle.BundleError):
        bundle.tier_commands(REPO, "4")


def test_compact_tier1_is_under_budget(compact: bundle.Bundle) -> None:
    """PLAN 5.5: < ~150k tokens. CHARS_PER_TOKEN is calibrated on Claude's tokenizer (ADR-025)."""
    assert compact.tokens < bundle.DEFAULT_MAX_TOKENS
    assert bundle.estimate_tokens("x" * 1950) == 1000


def test_build_is_deterministic(compact: bundle.Bundle) -> None:
    assert bundle.build(REPO, "1", "compact").text == compact.text


@pytest.mark.parametrize("detail", ["compact", "full"])
def test_every_tier1_reference_is_included(detail: str, compact, full) -> None:
    result = compact if detail == "compact" else full
    names, _ = bundle.tier_commands(REPO, "1")
    with_page = [n for n in names if (REPO / "en" / "commands" / f"{n}.md").is_file()]
    assert result.commands == with_page
    assert result.missing == ["POURSUITE"]
    for name in with_page:
        assert f"*Source: `en/commands/{name}.md` · status " in result.text


def test_guide_pages(compact: bundle.Bundle, full: bundle.Bundle) -> None:
    for page in (REPO / "en" / "guide").glob("*.md"):
        label = f"*Source: `en/guide/{page.name}` · "
        in_tier1 = page.name not in bundle.GUIDE_MIN_TIER
        assert (label in full.text) == in_tier1, page.name
        assert (label in compact.text) == (in_tier1 and page.name not in bundle.COMPACT_DROP_GUIDE)
    tier2 = bundle.build(REPO, "2", "full")
    assert "*Source: `en/guide/walkthrough-modal.md` · " in tier2.text
    assert "*Source: `en/commands/CALC_MODES.md` · " in tier2.text
    # The order of the guide's index: concepts, then the walkthroughs.
    assert full.text.index("en/guide/concepts.md` ·") < full.text.index(
        "en/guide/walkthrough-solid-static.md` ·"
    )


@pytest.mark.parametrize("detail", ["compact", "full"])
def test_structure(detail: str, compact, full) -> None:
    text = (compact if detail == "compact" else full).text
    headings = _headings(text)
    assert [h for _, h in headings if h.startswith("# ")] == [headings[0][1]]
    assert headings[0][0] == 1
    # Each contents entry gives the line its section starts on.
    lines = text.split("\n")
    entries = re.findall(r"^\s*- line (\d+): (.+)$", text, re.M)
    assert len(entries) > 20
    for number, label in entries:
        heading = lines[int(number) - 1]
        assert heading.startswith("## ") or heading.startswith("### "), (number, heading)
        assert heading.lstrip("# ") == label.split(" — `")[0]
    # Relative links were rewritten to repository paths.
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        assert target.startswith(("en/", "docs/", "tests/", "http", "#", "../")), target
        if target.startswith(("en/", "docs/", "tests/")):
            assert (REPO / target.split("#")[0]).exists(), target


def test_full_keeps_every_code_block(full: bundle.Bundle) -> None:
    """Pages are included whole in full detail: every fenced block is there, byte for byte,
    including `# ` comment lines that must not be read as headings."""
    for section in full.sections:
        if section.path.endswith(".md"):
            for block in FENCE.findall((REPO / section.path).read_text(encoding="utf-8")):
                assert block in full.text, (section.path, block[:60])
    assert "\n# Cylindrical shell with a radial nozzle under internal pressure.\n" in full.text


def test_compact_reference_content(compact: bundle.Bundle) -> None:
    text = compact.text.split("\n## Part 2: ")[1].split("\n## Part 3: ")[0]
    assert "Out of scope" not in "\n".join(ln for ln in text.split("\n") if ln.startswith("| `"))
    assert "| Fact | Value |" not in text
    assert "#### See also" not in text and "#### What the solver does" not in text
    # Patterns come first in each reference and are capped; the fixture pattern stays.
    assert "##### Fixed base and internal pressure on a solid" in text
    assert "##### Remote moment on a face (RBE3)" not in text
    # Sibling rows that read the same are merged.
    assert "| `DDL_IMPO / DX`, `DY`, `DZ`" in text
    # Rules about keywords no longer in the table are dropped, the others kept.
    assert "- `DDL_IMPO`: at least one of `TOUT`, `GROUP_MA`, `GROUP_NO`, `NOEUD`" in text


def test_glossary(compact: bundle.Bundle, full: bundle.Bundle) -> None:
    entries = glossary_validator.load(REPO / "en" / "glossary.yaml")  # YAML 1.2: NO stays "NO"
    for entry in entries:
        row = f"| `{bundle._cell(entry['fr'])}` | {bundle._cell(entry['en'])} |"
        assert row in full.text, entry["fr"]
        if entry["kind"] in bundle.COMPACT_GLOSSARY_KINDS:
            assert row in compact.text, entry["fr"]


def test_first_sentence() -> None:
    assert bundle.first_sentence("One of `'A.B'`. More.") == "One of `'A.B'`."
    assert bundle.first_sentence("Use 0.5 e.g. here. Then.") == "Use 0.5 e.g. here."
    assert bundle.first_sentence("No end") == "No end"


def test_compact_meaning() -> None:
    cell = "*imposed DOF*. One of `'OUI'`. Only when `exists(\"X\")`. Authored text. More."
    assert bundle.compact_meaning(cell) == "*imposed DOF*. One of `'OUI'`."
    assert bundle.compact_meaning("Range: ≥ 0.0. Text.") == "Range: ≥ 0.0."
    assert bundle.compact_meaning("Text only.") == ""


def test_merge_rows() -> None:
    rows = [
        "| `A / X` | real, optional | — |  |",
        "| `A / Y` | real, optional | — |  |",
        "| `A / Z` | integer, optional | — |  |",
        "| `B / X` | integer, optional | — |  |",
        "| `C` | real, optional | — |  |",
    ]
    assert bundle.merge_rows(rows) == [
        "| `A / X`, `Y` | real, optional | — |  |",
        "| `A / Z` | integer, optional | — |  |",
        "| `B / X` | integer, optional | — |  |",
        "| `C` | real, optional | — |  |",
    ]


def test_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(REPO)
    out = tmp_path / "b.md"
    result = CliRunner().invoke(app, ["bundle", "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert out.read_text(encoding="utf-8").startswith("# code_aster in English: context bundle")
    assert "tokens" in result.output
    result = CliRunner().invoke(app, ["bundle", "--out", str(out), "--max-tokens", "1000"])
    assert result.exit_code == 1
    assert "over the budget" in result.output
    result = CliRunner().invoke(app, ["bundle", "--out", str(out), "--detail", "short"])
    assert result.exit_code == 1


def test_workflow_builds_the_budgeted_bundle() -> None:
    workflow = yaml.safe_load((REPO / ".github/workflows/llm-bundle.yml").read_text())
    steps = workflow["jobs"]["bundle"]["steps"]
    build = next(s["run"] for s in steps if s.get("name") == "Build the bundles")
    first = build.splitlines()[1]
    assert "--tier 1 " in first and "--max-tokens" not in first  # the default budget applies


def _catalog_namespace() -> dict:
    if not (REPO / "upstream" / "code_aster" / "Cata").is_dir():
        pytest.skip("upstream/ submodule not checked out")
    sys.dont_write_bytecode = True  # never write into upstream/
    sys.path.insert(0, str(REPO / "upstream"))
    try:
        from code_aster.Cata.Commands import commandStore
    finally:
        sys.path.remove(str(REPO / "upstream"))
    return dict(commandStore)


def test_trial_study() -> None:
    """The study an agent wrote from the bundle alone (docs/bundle-trial/README.md): it passes
    the pinned catalog check, and its committed run ended OK with every TEST_RESU OK."""
    trial = REPO / "docs" / "bundle-trial"
    path = trial / "input" / "run.comm"
    exec(compile(path.read_text(), str(path), "exec"), _catalog_namespace() | {"_F": dict})
    assert "--- DIAGNOSTIC JOB : OK" in (trial / "output" / "run_aster.stdout").read_text()
    mess = (trial / "output" / "run.mess").read_text(encoding="utf-8", errors="replace")
    assert "<A>" not in mess and " NOOK " not in mess
    assert len(re.findall(r"^ OK +\w+ +REAC_DX_SUM", mess, re.M)) == 2
    table = (trial / "output" / "tables" / "reactions.csv").read_text().splitlines()
    row = next(line for line in table if line.startswith("REAC_SYM_X"))
    assert float(row.split(",")[5]) == pytest.approx(-25000.0, rel=1e-9)
