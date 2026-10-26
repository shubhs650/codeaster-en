"""Tests for the message placeholder parser (task 1.3) and fr/en comparison (task 1.6)."""

from __future__ import annotations

import pytest

from codeaster_en.placeholders import compare, parse

# Every format in docs/INVENTORY.md §2 (N replaced by 1), plus `ktout` (Utmess.py:229).
INVENTORY_FORMATS = """
%(k1)s %(i1)d %(r1)f %(r1)12.5E %(r1)19.12e %(r1)g %(r1).2f %(i1)i %(r1)12.5e %(i1)4d
%(r1)e %(r1)13.6G %(r1)E %(r1)10.3E %(r1).15E %(r1).4f %(r1)8.2f %(i1)10d %(k1)-8s
%(i1)12d %(i1)5d %(i1)8d %(k1)8s %(r1)12.4E %(r1).2e %(r1).3f %(r1)16.9g %(k1)-16s
%(i1)3d %(r1)12.2f %(r1)10.2E %(r1).0f %(i1)-17d %(k1)24s %(r1)1.1f %(r1)4.3G
%(r1)19.8e %(i1)04d %(r1)9.2E %(r1)+.2f %(r1)G %(r1)17.10e %(r1)10.3e %(i1)2d %(k1)3s
%(k1)-20s %(r1).6f %(r1)6.3f %(k1)-12s %(r1).3e %(ktout)s
""".split()


def test_inventory_has_51_formats_plus_ktout() -> None:
    assert len(INVENTORY_FORMATS) == 51  # 50 named in the table, %% tested separately, + ktout
    assert len(set(INVENTORY_FORMATS)) == len(INVENTORY_FORMATS)


@pytest.mark.parametrize("spec", INVENTORY_FORMATS)
def test_every_inventory_format_is_one_token(spec: str) -> None:
    parsed = parse(f"avant {spec} après")
    assert parsed.errors == []
    assert parsed.tokens == [spec]
    assert parsed.placeholders[0].key == spec[2 : spec.index(")")]


def test_literal_percent() -> None:
    parsed = parse("taux %(r1).2f %% atteint")
    assert parsed.tokens == ["%(r1).2f", "%%"]
    assert parsed.placeholders[1].key is None
    assert parsed.errors == []


def test_double_percent_is_consumed_before_a_key() -> None:
    # Python reads "%%(k1)s" as a literal "%" followed by the text "(k1)s".
    parsed = parse("%%(k1)s")
    assert parsed.tokens == ["%%"]


def test_multiline_message_order_and_repeats() -> None:
    text = """
 Le champ %(k1)s du résultat %(k2)s
   - valeur min : %(r1)12.5E
   - valeur max : %(r2)12.5E
 Le champ %(k1)s est ignoré (%(i1)-17d occurrences).
"""
    parsed = parse(text)
    assert parsed.errors == []
    assert parsed.tokens == ["%(k1)s", "%(k2)s", "%(r1)12.5E", "%(r2)12.5E", "%(i1)-17d"]
    assert parsed.counts()["%(k1)s"] == 2


def test_stray_percent_is_an_error() -> None:
    parsed = parse("50 % des noeuds")
    # Python would read "% d" as a positional integer conversion.
    assert parsed.tokens == ["% d"]
    assert "has no name" in parsed.errors[0]
    assert "line 1 col 4" in parsed.errors[0]


def test_percent_at_end_and_unterminated_key_are_errors() -> None:
    assert parse("100 %").errors
    assert parse("%(k1 manque").errors
    assert parse("%(k1)").errors  # no conversion


def test_positional_and_star_are_errors() -> None:
    assert "has no name" in parse("valeur %s").errors[0]
    assert "'*'" in parse("%(r1)*.2f").errors[0]


def test_error_reports_line_of_multiline_text() -> None:
    errors = parse("ligne 1\nligne 2 : 10 %\n").errors
    assert errors and errors[0].startswith("line 2 col 14")


# --- compare (fr ↔ en) ----------------------------------------------------------------


def test_compare_accepts_reordering() -> None:
    fr = "Le champ %(k1)s du résultat %(k2)s vaut %(r1)12.5E."
    en = "Result %(k2)s, field %(k1)s: %(r1)12.5E."
    assert compare(fr, en) == []


def test_compare_accepts_different_repeat_count() -> None:
    assert compare("%(k1)s puis %(k1)s", "%(k1)s twice") == []


def test_compare_missing_extra_and_changed_format() -> None:
    fr = "Valeur %(r1)12.5E pour %(k1)s : %(i1)d %%"
    problems = compare(fr, "Value %(r1)e for %(k1)s: %(i2)d %%")
    assert "en is missing %(r1)12.5E, %(i1)d" in problems
    assert "en has %(r1)e, %(i2)d, which the French does not" in problems


def test_compare_literal_percent_must_be_kept() -> None:
    assert compare("écart %(r1).2f %%", "deviation %(r1).2f percent") == ["en is missing %%"]


def test_compare_reports_invalid_english() -> None:
    problems = compare("écart %(r1).2f %%", "deviation %(r1).2f %")
    assert any(p.startswith("en: ") for p in problems)
