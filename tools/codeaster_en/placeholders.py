"""Printf-style placeholders in code_aster message texts.

``Utmess`` formats every message body with ``fmt % dicarg`` (``Messages/Utmess.py``, through
``ufmt``), where ``dicarg`` maps ``k1``… to strings, ``i1``… to integers, ``r1``… to reals,
and ``ktout`` to all the strings joined by spaces (``Utmess.build_dict_args``). So a message
text is a Python ``%``-format string used with a mapping: every conversion must be named, and
a literal percent sign is written ``%%``.

:func:`parse` follows Python's printf grammar (mapping key, flags, width, precision, length
modifier, conversion), so it covers every format counted in docs/INVENTORY.md §2
(``%(k1)s``, ``%(r1)12.5E``, ``%(i1)-17d``, ``%(r1)+.2f``, ``%%`` …) and anything else Python
would accept. Text Python would reject, or a conversion without a mapping key, is reported in
:attr:`Parsed.errors` instead of being silently skipped.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

# Python printf grammar: %[(key)][flags][width][.precision][length]conversion
_SPEC = re.compile(
    r"""%
    (?:\((?P<key>[^)]*)\))?
    (?P<flags>[-+ \#0]*)
    (?P<width>\*|\d+)?
    (?:\.(?P<precision>\*|\d*))?
    (?P<length>[hlL])?
    (?P<conversion>[diouxXeEfFgGcrsa%])
    """,
    re.VERBOSE,
)

LITERAL_PERCENT = "%%"


@dataclass(frozen=True)
class Placeholder:
    """One conversion specifier as written, e.g. ``%(r1)12.5E`` (``key`` ``r1``)."""

    text: str
    key: str | None
    conversion: str
    offset: int


@dataclass
class Parsed:
    placeholders: list[Placeholder] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def tokens(self) -> list[str]:
        """Distinct specifiers (``%%`` included) in order of first appearance."""
        return list(dict.fromkeys(p.text for p in self.placeholders))

    def counts(self) -> Counter[str]:
        return Counter(p.text for p in self.placeholders)


def _line_col(text: str, offset: int) -> str:
    line = text.count("\n", 0, offset) + 1
    col = offset - (text.rfind("\n", 0, offset) + 1) + 1
    return f"line {line} col {col}"


def parse(text: str) -> Parsed:
    """Scan ``text`` left to right the way ``str.__mod__`` does."""
    result = Parsed()
    pos = text.find("%")
    while pos != -1:
        match = _SPEC.match(text, pos)
        if match is None:
            snippet = text[pos : pos + 12].split("\n")[0]
            result.errors.append(
                f"{_line_col(text, pos)}: '%' does not start a valid placeholder "
                f"(near {snippet!r}); write a literal percent sign as '%%'"
            )
            pos = text.find("%", pos + 1)
            continue
        spec = match.group(0)
        key = match.group("key")
        conversion = match.group("conversion")
        if conversion == "%" and spec != LITERAL_PERCENT:
            result.errors.append(f"{_line_col(text, pos)}: malformed literal percent {spec!r}")
        elif conversion != "%" and key is None:
            result.errors.append(
                f"{_line_col(text, pos)}: placeholder {spec!r} has no name; messages are "
                "formatted with a mapping, so write e.g. '%(k1)s' (or '%%' for a percent sign)"
            )
        elif "*" in spec:
            result.errors.append(f"{_line_col(text, pos)}: '*' width/precision in {spec!r}")
        result.placeholders.append(Placeholder(spec, key, conversion, pos))
        pos = text.find("%", match.end())
    return result


def compare(fr: str, en: str) -> list[str]:
    """Problems with ``en`` as a translation of ``fr`` (empty list = placeholders agree).

    The two texts must use the same set of specifiers, each character for character
    (``%(r1)12.5E`` is not ``%(r1)e``). Order may change for English word order, and a
    specifier may be repeated or not as the sentence needs (TRANSLATION-GUIDE.md §3).
    """
    parsed_en = parse(en)
    problems = [f"en: {err}" for err in parsed_en.errors]
    want = set(parse(fr).tokens)
    have = set(parsed_en.tokens)
    missing = [t for t in parse(fr).tokens if t not in have]
    extra = [t for t in parsed_en.tokens if t not in want]
    if missing:
        problems.append(f"en is missing {', '.join(missing)}")
    if extra:
        problems.append(f"en has {', '.join(extra)}, which the French does not")
    return problems
