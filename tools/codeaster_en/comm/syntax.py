"""Values of a command file and their layout as Python source (task 6.1).

A ``.comm`` file is Python. The builder writes it the way ``ruff format`` (and Black) would lay
it out, so a builder file and a hand-written fixture compare byte for byte and ``ruff format``
leaves builder output unchanged. Only the subset a command file needs is covered: calls with
keyword arguments, ``_F(...)`` factor keywords, tuples, strings, numbers and names.

The layout rule is Black's right-hand split, restricted to that subset:

1. A statement that fits in :data:`LINE_LENGTH` columns stays on one line.
2. Otherwise its last bracket is split: the opening line, the contents indented four columns,
   the closing bracket on its own line.
3. The contents stay on one line if they fit, except a tuple of two or more items, which
   always puts one item per line once it is split.
4. Otherwise one item per line, each followed by a comma. A call with a single keyword is
   split again at that keyword's own bracket instead, with no trailing comma.
5. A comment inside a bracket forces every enclosing bracket to split.
"""

from __future__ import annotations

import keyword
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

LINE_LENGTH = 100
INDENT = "    "

_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")


class CommSyntaxError(ValueError):
    """A value that cannot be written to a command file."""


@dataclass(frozen=True)
class Concept:
    """A result object (concept) produced by a command: written as its Python name.

    ``type`` is the catalog data-structure name (``maillage_sdaster``, ``evol_elas``...) when
    the builder knows it, else ``None``.
    """

    name: str
    type: str | None = None


@dataclass(frozen=True)
class Param:
    """A named constant bound at the top of the file (``P = 2.0``) and used by name."""

    name: str
    value: Any


@dataclass(frozen=True)
class Number:
    """A number written with the given literal text (``1.0e-3``, ``104.440``)."""

    value: float
    text: str

    def __post_init__(self) -> None:
        try:
            parsed = float(self.text)
        except ValueError as exc:
            raise CommSyntaxError(f"not a number literal: {self.text!r}") from exc
        if parsed != float(self.value):
            raise CommSyntaxError(f"literal {self.text!r} is not {self.value!r}")
        if self.text != self.text.lower() or self.text.startswith("+"):
            raise CommSyntaxError(f"write {self.text!r} lower-case and without '+'")


@dataclass(frozen=True)
class Commented:
    """A tuple item with comment lines written just above it."""

    value: Any
    comment: str


@dataclass
class _Atom:
    text: str


@dataclass
class _Item:
    prefix: str  # "NAME=" for a keyword argument, "" for a tuple item
    node: _Node
    comments: list[str] = field(default_factory=list)


@dataclass
class _Bracket:
    opener: str  # "NAME(" for a call, "(" for a tuple
    items: list[_Item]
    is_tuple: bool


_Node = _Atom | _Bracket


def check_name(name: str) -> str:
    """Return ``name`` if it can name a concept or constant in a command file, else raise."""
    if not _NAME.match(name) or keyword.iskeyword(name) or name in {"_F", "reuse"}:
        raise CommSyntaxError(f"invalid name: {name!r}")
    return name


def string_literal(text: str) -> str:
    """Python string literal as ``ruff format`` writes it (double quotes preferred)."""
    if '"' in text and "'" not in text:
        quote = "'"
    else:
        quote = '"'
    body = text.replace("\\", "\\\\").replace("\n", "\\n").replace(quote, "\\" + quote)
    return quote + body + quote


def number_literal(value: int | float) -> str:
    if isinstance(value, bool):
        raise CommSyntaxError("booleans are not command values; code_aster uses 'OUI'/'NON'")
    if isinstance(value, int):
        return str(value)
    if not math.isfinite(value):
        raise CommSyntaxError(f"not a finite number: {value!r}")
    return repr(float(value))


def _node(value: Any) -> _Node:
    if isinstance(value, Concept | Param):
        return _Atom(value.name)
    if isinstance(value, Number):
        return _Atom(value.text)
    if isinstance(value, str):
        return _Atom(string_literal(value))
    if isinstance(value, int | float):
        return _Atom(number_literal(value))
    if isinstance(value, Mapping):
        return call_node("_F", value)
    if isinstance(value, Commented):
        raise CommSyntaxError("a comment can only be attached to a tuple item")
    if isinstance(value, Sequence):
        items = []
        for v in value:
            if isinstance(v, Commented):
                items.append(_Item("", _node(v.value), _comment_lines(v.comment)))
            else:
                items.append(_Item("", _node(v)))
        if not items:
            raise CommSyntaxError("empty sequence")
        return _Bracket("(", items, is_tuple=True)
    raise CommSyntaxError(f"unsupported value type: {type(value).__name__}")


def call_node(name: str, keywords: Mapping[str, Any]) -> _Bracket:
    return _Bracket(
        f"{name}(",
        [_Item(f"{key}=", _node(value)) for key, value in keywords.items()],
        is_tuple=False,
    )


def _comment_lines(text: str) -> list[str]:
    return [f"# {line}".rstrip() for line in text.splitlines()]


def comment_block(text: str) -> list[str]:
    """``# `` comment lines for ``text`` (one per line of text; blank lines give ``#``)."""
    return _comment_lines(text)


def _flat(node: _Node) -> str:
    if isinstance(node, _Atom):
        return node.text
    inner = ", ".join(item.prefix + _flat(item.node) for item in node.items)
    if node.is_tuple and len(node.items) == 1:
        inner += ","
    return node.opener + inner + ")"


def _has_comments(node: _Node) -> bool:
    if isinstance(node, _Atom):
        return False
    return any(item.comments or _has_comments(item.node) for item in node.items)


def _fits(indent: str, text: str) -> bool:
    return len(indent) + len(text) <= LINE_LENGTH


def _render(prefix: str, node: _Node, suffix: str, indent: str) -> list[str]:
    flat = prefix + _flat(node) + suffix
    if isinstance(node, _Atom) or not node.items:
        return [indent + flat]
    if not _has_comments(node) and _fits(indent, flat):
        return [indent + flat]
    return [indent + prefix + node.opener, *_body(node, indent + INDENT), indent + ")" + suffix]


def _body(node: _Bracket, indent: str) -> list[str]:
    items = node.items
    one_tuple = node.is_tuple and len(items) == 1
    if not _has_comments(node) and not (node.is_tuple and len(items) > 1):
        text = ", ".join(item.prefix + _flat(item.node) for item in items)
        text += "," if one_tuple else ""
        if _fits(indent, text):
            return [indent + text]
    if len(items) == 1 and not node.is_tuple:
        return _item(items[0], indent, "")
    lines: list[str] = []
    for item in items:
        lines.extend(_item(item, indent, ","))
    return lines


def _item(item: _Item, indent: str, suffix: str) -> list[str]:
    return [indent + c for c in item.comments] + _render(item.prefix, item.node, suffix, indent)


def render_call(
    command: str, keywords: Mapping[str, Any], *, target: str | None = None, reuse: bool = False
) -> list[str]:
    """Source lines of ``[target = ]COMMAND(...)``; ``reuse=target`` comes first if asked."""
    if reuse:
        if target is None:
            raise CommSyntaxError(f"{command}: reuse needs a result name")
        keywords = {"reuse": Concept(target), **keywords}
    prefix = f"{target} = " if target else ""
    return _render(prefix, call_node(command, keywords), "", "")


def render_assignment(name: str, value: Any, note: str | None = None) -> list[str]:
    """Source line(s) of ``NAME = value`` with an optional trailing ``  # note``."""
    lines = _render(f"{name} = ", _node(value), "", "")
    if note is not None:
        if len(lines) != 1 or "\n" in note:
            raise CommSyntaxError(f"{name}: a trailing note needs a one-line statement")
        lines[0] += f"  # {note}"
    return lines
