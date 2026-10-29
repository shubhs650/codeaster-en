"""Glossary coverage: Tier 1/2 identifiers of docs/COMMAND-SET.md have entries (task 0.6);
every entry except values has a note (task 2.1)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from codeaster_en.validate import glossary

REPO = Path(__file__).resolve().parents[1]
GLOSSARY = REPO / "en" / "glossary.yaml"
COMMAND_SET = REPO / "docs" / "COMMAND-SET.md"
UPSTREAM = REPO / "upstream"

# Tokens in the Tier 1/2 tables that are not solver identifiers.
NOT_IDENTIFIERS = {"GAUCHE"}  # from "PROL_DROITE/GAUCHE"


def _tier12_identifiers() -> set[str]:
    text = COMMAND_SET.read_text(encoding="utf-8").split("## Tier 3")[0]
    rows = [line for line in text.splitlines() if line.startswith("|")]
    found: set[str] = set()
    for code in re.findall(r"`([^`]+)`", "\n".join(rows)):
        found.update(re.findall(r"\b(?:3D\w*|[A-Z][A-Z0-9_]*[A-Z0-9]|[A-Z])\b", code))
    return found - NOT_IDENTIFIERS


def test_tier12_identifiers_have_glossary_entries() -> None:
    have = {e["fr"] for e in glossary.load(GLOSSARY)}
    missing = sorted(_tier12_identifiers() - have)
    assert missing == []


def test_source_fields_point_into_upstream() -> None:
    if not (UPSTREAM / "code_aster").is_dir():
        pytest.skip("upstream/ submodule not checked out")
    bad = []
    for entry in glossary.load(GLOSSARY):
        if "source" not in entry:
            continue
        rel, _, line = entry["source"].rpartition(":")
        path = UPSTREAM / rel
        if not path.is_file() or not 1 <= int(line) <= len(path.read_text().splitlines()):
            bad.append(entry["fr"])
            continue
        if entry["fr"] not in path.read_text(encoding="utf-8").splitlines()[int(line) - 1]:
            bad.append(entry["fr"])
    assert bad == []


def test_entries_have_notes_except_values() -> None:
    # PLAN.md task 2.1: opaque abbreviations and identifiers are explained once, in `note`.
    missing = [
        e["fr"] for e in glossary.load(GLOSSARY) if e["kind"] != "value" and not e.get("note")
    ]
    assert missing == []
