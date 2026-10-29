"""Message templates for the English renderer (task 4.4): ``en/messages`` as matchers.

The solver prints a message as ``fr % args`` (``Messages/Utmess.py``), then wraps lines longer
than 100 columns at a separator (``Utilities/strfunc.py`` ``cut_long_lines``), centers it
(``CENTER`` flag) or draws a box around it (``textbox``). To put the English text in its place
we need the arguments back, so each French text is compiled into a regular expression:

- literal text is matched exactly, except that any run of whitespace matches any run of
  whitespace (wrapping turns a space into a line break, centering and boxes add padding);
- each placeholder becomes a capture group: digits for ``d``/``i``, a number for ``e``/``f``/
  ``g``, and the shortest text that lets the rest match for ``s`` (and the other conversions);
- a placeholder used twice must print the same text both times (back-reference).

Two compiled forms exist: ``box`` matches the whole body of a ``<TYPE> <ID>`` box (``s``
arguments may span lines), ``line`` matches at the start of a line of free text and must end
at a line end (``s`` arguments stay on one line). Recovered arguments are the text exactly as
printed (``0002`` for ``%(i1)04d``), so the English is filled in with the same formatting.

Known limit: when ``cut_long_lines`` breaks a line at ``,``, ``;``, ``.`` or ``:`` it drops
that character, so a template whose literal text was broken there does not match; the
renderer then keeps the French and says why.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from codeaster_en import data
from codeaster_en.placeholders import parse as parse_placeholders

DEFAULT_MESSAGES_DIR = data.messages_dir()

_WS_RUN = re.compile(r"\s+")
_INT = r"[ \t]*[-+]?\d+"
_REAL = r"[ \t]*[-+]?(?:\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?|nan|inf|NaN|Inf|NAN|INF)"
_CAPTURE = {"d": _INT, "i": _INT, "u": _INT, "e": _REAL, "E": _REAL, "f": _REAL, "F": _REAL}
_CAPTURE.update(g=_REAL, G=_REAL)

# A template is tried on free text only if it has at least this many literal characters (not
# counting whitespace): shorter ones ("%(k1)s : %(k2)s") would match almost any line.
MIN_LITERAL_FOR_TEXT = 10
_KEY_LEN = 4


def _literal_pattern(text: str) -> str:
    """Escape ``text`` with every whitespace run made flexible."""
    parts = _WS_RUN.split(text)
    return r"\s+".join(re.escape(p) for p in parts)


def _reformat(spec: str, value: str) -> str:
    """Print a numeric ``value`` again with ``spec``: its padding can end up in the whitespace
    run next to it when the French is matched, so the width is applied afresh. Strings are
    left as captured: two padded strings side by side (``%(k1)3s %(k2)-20s``) cannot be told
    apart once one is empty, so re-padding could misalign them."""
    fmt = re.sub(r"^%\([^)]*\)", "%", spec)
    conv = spec[-1]
    try:
        if conv in "diu":
            return fmt % int(value.strip())
        if conv in "eEfFgG":
            return fmt % float(value.strip())
    except (ValueError, TypeError):
        pass
    return value


_Pieces = list[tuple[str, str | None, str | None]]


def _split(text: str) -> _Pieces:
    """``(literal, spec, key)`` triples covering ``text`` stripped (spec ``None`` for the tail)."""
    text = text.strip()
    pieces: _Pieces = []
    pos = 0
    for ph in parse_placeholders(text).placeholders:
        literal = text[pos : ph.offset]
        if ph.conversion == "%":
            pieces.append((literal + "%", None, None))
        else:
            pieces.append((literal, ph.text, ph.key))
        pos = ph.offset + len(ph.text)
    pieces.append((text[pos:], None, None))
    return pieces


@dataclass
class Template:
    """One message of ``en/messages``: its French and English texts and their matchers."""

    id: str
    fr: str
    en: str | None = None
    method: str | None = None
    flags: str | None = None
    stale: bool = False
    _box: re.Pattern[str] | None = field(default=None, init=False, repr=False)
    _line: re.Pattern[str] | None = field(default=None, init=False, repr=False)

    @cached_property
    def _pieces(self) -> list[tuple[str, str | None, str | None]]:
        """``(literal, spec, key)`` triples covering ``fr`` (spec ``None`` for the tail)."""
        return _split(self.fr)

    @cached_property
    def _en_pieces(self) -> list[tuple[str, str | None, str | None]]:
        """The same for ``en``: a solver run with our gettext catalog prints the English."""
        return _split(self.en or "")

    @cached_property
    def literal_chars(self) -> int:
        return sum(len(_WS_RUN.sub("", lit)) for lit, _, _ in self._pieces)

    @cached_property
    def key(self) -> str | None:
        """First characters of the template when it starts with literal text, else ``None``."""
        words = self._pieces[0][0].split()
        return words[0][:_KEY_LEN] if words else None

    def _compile(
        self, multiline: bool, anchored: bool = True, pieces: _Pieces | None = None
    ) -> re.Pattern[str]:
        seen: dict[str, str] = {}
        out: list[str] = []
        for n, (literal, spec, _key) in enumerate(self._pieces if pieces is None else pieces):
            out.append(_literal_pattern(literal))
            if spec is None:
                continue
            if spec in seen:
                out.append(f"(?P={seen[spec]})")
                continue
            group = f"g{n}"
            seen[spec] = group
            conv = spec[-1]
            if conv in _CAPTURE:
                pat = _CAPTURE[conv]
            else:
                pat = r"(?s:.*?)" if multiline else r"[^\n]*?"
            out.append(f"(?P<{group}>{pat})")
        body = "".join(out)
        if not anchored:
            return re.compile(body)
        if multiline:
            return re.compile(rf"\s*{body}\s*\Z")
        return re.compile(rf"[ \t]*{body}[ \t]*(?=\n|\Z)")

    @property
    def box(self) -> re.Pattern[str]:
        if self._box is None:
            self._box = self._compile(multiline=True)
        return self._box

    @property
    def line(self) -> re.Pattern[str]:
        if self._line is None:
            self._line = self._compile(multiline=False)
        return self._line

    @cached_property
    def inline(self) -> re.Pattern[str]:
        """Unanchored, single-line form: finds this message inside another message's argument."""
        return self._compile(multiline=False, anchored=False)

    def replace_inside(self, text: str) -> str:
        """``text`` with every occurrence of this message replaced by its English."""
        if not self.en:
            return text
        return self.inline.sub(lambda m: (self.fill(self._args(m)) or m.group(0)).strip(), text)

    @cached_property
    def en_box(self) -> re.Pattern[str] | None:
        """``box`` for the English text (ADR-004: the solver may print it with our ``.mo``)."""
        return self._compile(multiline=True, pieces=self._en_pieces) if self.en else None

    def _args(self, match: re.Match[str], pieces: _Pieces | None = None) -> dict[str, str]:
        args: dict[str, str] = {}
        for n, (_, spec, _key) in enumerate(self._pieces if pieces is None else pieces):
            if spec is not None and spec not in args and match.group(f"g{n}") is not None:
                args[spec] = match.group(f"g{n}")
        return args

    def recover(self, body: str) -> dict[str, str] | None:
        """Arguments (by specifier, e.g. ``%(k1)s``) of a box body, or ``None`` if it is not
        this message."""
        m = self.box.match(body)
        return self._args(m) if m else None

    def recover_en(self, body: str) -> dict[str, str] | None:
        """:meth:`recover` for a body the solver already printed in English."""
        m = self.en_box.match(body) if self.en_box is not None else None
        return self._args(m, self._en_pieces) if m else None

    def match_at(self, text: str, pos: int) -> tuple[int, dict[str, str]] | None:
        """Match free text at ``pos`` (a line start); return the end offset and arguments."""
        m = self.line.match(text, pos)
        if not m or m.end() == pos:
            return None
        return m.end(), self._args(m)

    @cached_property
    def en_line(self) -> re.Pattern[str] | None:
        return self._compile(multiline=False, pieces=self._en_pieces) if self.en else None

    def match_at_en(self, text: str, pos: int) -> tuple[int, dict[str, str]] | None:
        """:meth:`match_at` for text the solver already printed in English."""
        m = self.en_line.match(text, pos) if self.en_line is not None else None
        if not m or m.end() == pos:
            return None
        return m.end(), self._args(m, self._en_pieces)

    def fill(self, args: dict[str, str]) -> str | None:
        """The English text with the recovered arguments, ``None`` if there is no English."""
        if not self.en:
            return None
        out: list[str] = []
        text = self.en
        pos = 0
        for ph in parse_placeholders(text).placeholders:
            out.append(text[pos : ph.offset])
            if ph.conversion == "%":
                out.append("%")
            else:
                out.append(_reformat(ph.text, args[ph.text]) if ph.text in args else ph.text)
            pos = ph.offset + len(ph.text)
        out.append(text[pos:])
        return "".join(out).strip("\n")


class MessageCatalog:
    """All message families of ``en/messages``, by ID and by the start of their text."""

    def __init__(self, messages_dir: str | Path | None = None) -> None:
        self.dir = Path(messages_dir) if messages_dir else DEFAULT_MESSAGES_DIR
        self.templates: dict[str, Template] = {}
        self.upstream: str | None = None
        self._by_key: dict[str, list[Template]] = {}
        for path in sorted(self.dir.glob("*.en.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.upstream = self.upstream or data.get("_generated_from", {}).get("upstream")
            messages = data.get("messages", {})
            for entry in messages.values() if isinstance(messages, dict) else messages:
                tpl = Template(
                    entry["id"],
                    entry["fr"],
                    entry.get("en"),
                    entry.get("method"),
                    entry.get("flags"),
                    bool(entry.get("stale")),
                )
                self.templates[tpl.id] = tpl
                if tpl.key and tpl.literal_chars >= MIN_LITERAL_FOR_TEXT:
                    self._by_key.setdefault(tpl.key, []).append(tpl)
        if not self.templates:
            raise FileNotFoundError(f"no message families (*.en.json) in {self.dir}")

    def get(self, message_id: str | None) -> Template | None:
        return self.templates.get(message_id) if message_id else None

    def candidates(self, line: str) -> list[Template]:
        """Templates whose text could start at this line."""
        word = line.lstrip()[:_KEY_LEN]
        out: list[Template] = []
        for k in range(1, len(word) + 1):
            out.extend(self._by_key.get(word[:k], ()))
        return out

    def match_text(self, text: str, pos: int) -> tuple[Template, int, dict[str, str]] | None:
        """Best template matching free text at ``pos``: the longest match, then the one with
        the most literal text."""
        eol = text.find("\n", pos)
        line = text[pos : eol if eol != -1 else len(text)]
        best: tuple[Template, int, dict[str, str]] | None = None
        for tpl in self.candidates(line):
            hit = tpl.match_at(text, pos)
            if hit is None:
                continue
            end, args = hit
            if best is None or (end, tpl.literal_chars) > (best[1], best[0].literal_chars):
                best = (tpl, end, args)
        return best
