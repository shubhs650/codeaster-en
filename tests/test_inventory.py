"""Tests for ``caen extract inventory`` (task 1.5).

The generated block of the committed ``docs/INVENTORY.md`` is the snapshot: rebuilding it from
the committed ``en/`` data and ``docs/COMMAND-SET.md`` must give the same text. No upstream
checkout is needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from codeaster_en.cli import app
from codeaster_en.extract import inventory

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / inventory.INVENTORY_RELPATH

COMMAND_SET = """\
# Command set

## Tier 1 — alpha

| Function | Command | Key keywords to cover first | Status |
|---|---|---|---|
| Session | `DEBUT`, `FIN`, `POURSUITE` | `CODE`, `ERREUR` | — |
| Model | `AFFE_MODELE` | `AFFE` × (`PHENOMENE='MECANIQUE'`, `MODELISATION` ∈ {`3D`, `DKT`}) | — |

### Tier 1 message families

Likely: `SUPERVIS`, `MODELISA`, `MECASTATIQUE`.

## Tier 2 — post-alpha

| Function | Command | Key keywords | Status |
|---|---|---|---|
| Springs | `AFFE_CARA_ELEM` / `DISCRET` | `CARA` (`K_T_D_N`), `SIGM_*` | — |

## Tier 3 — later

`STAT_NON_LINE`, `CALC_EUROPLEXUS` (no).

## Explicitly out of scope

`MISS3D`, `IFS`.
"""


def _block(text: str) -> str:
    start = text.index(inventory.BEGIN) + len(inventory.BEGIN) + 1
    return text[start : text.index(inventory.END)]


def test_committed_block_is_up_to_date() -> None:
    assert _block(DOC.read_text(encoding="utf-8")) == inventory.build(REPO), (
        "docs/INVENTORY.md is stale: run `caen extract inventory`"
    )


def test_parse_command_set() -> None:
    known = {"DEBUT", "FIN", "POURSUITE", "AFFE_MODELE", "AFFE_CARA_ELEM", "STAT_NON_LINE"}
    cset = inventory.parse_command_set(COMMAND_SET, known)
    assert [(r.tier, r.function, r.commands) for r in cset.rows] == [
        ("1", "Session", ["DEBUT", "FIN", "POURSUITE"]),
        ("1", "Model", ["AFFE_MODELE"]),
        ("2", "Springs", ["AFFE_CARA_ELEM"]),
        ("3", "Later", ["STAT_NON_LINE", "CALC_EUROPLEXUS"]),
    ]
    assert cset.rows[0].key_keywords == ["CODE", "ERREUR"]
    # Values inside quotes count; lower-case and digit-led tokens do not.
    assert cset.rows[1].key_keywords == ["AFFE", "PHENOMENE", "MECANIQUE", "MODELISATION", "DKT"]
    # Non-command names in the Command column are keywords; wildcards are skipped.
    assert cset.rows[2].key_keywords == ["DISCRET", "CARA", "K_T_D_N"]
    assert cset.message_families == ["SUPERVIS", "MODELISA", "MECASTATIQUE"]


@pytest.mark.parametrize(
    ("family", "base"),
    [("MECANONLINE10", "MECANONLINE"), ("POST0", "POST"), ("MED", "MED"), ("JEVEUX1", "JEVEUX")],
)
def test_family_base(family: str, base: str) -> None:
    assert inventory.family_base(family) == base


def test_splice_keeps_hand_written_text() -> None:
    doc = f"# T\n\nintro\n\n{inventory.BEGIN}\nold\n{inventory.END}\n\n## After\n"
    out = inventory.splice(doc, "new\n")
    assert out == f"# T\n\nintro\n\n{inventory.BEGIN}\nnew\n{inventory.END}\n\n## After\n"


def test_splice_needs_markers() -> None:
    with pytest.raises(ValueError, match="markers"):
        inventory.splice("# T\n", "new\n")


def test_cli_writes_only_the_block(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "INVENTORY.md"
    out.write_text(f"# Inv\n\n{inventory.BEGIN}\n{inventory.END}\nkept\n", encoding="utf-8")
    monkeypatch.chdir(REPO)
    result = CliRunner().invoke(app, ["extract", "inventory", "--out", str(out)])
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# Inv\n\n") and text.endswith(f"{inventory.END}\nkept\n")
    assert "### 7.6 Top 50 commands across astest" in text
