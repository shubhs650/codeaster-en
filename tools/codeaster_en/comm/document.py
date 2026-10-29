"""A command file under construction: validated statements written in order (task 6.1).

:class:`CommandFile` is the low-level layer of the builder: it takes French command and keyword
names exactly as the catalog spells them, checks each call against ``en/commands/<CMD>.json``
(:mod:`codeaster_en.comm.catalog`) at the moment it is added, and writes the file in the layout
of :mod:`codeaster_en.comm.syntax`. The English API (:class:`codeaster_en.comm.Builder`) is
built on it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from codeaster_en.comm import catalog
from codeaster_en.comm.syntax import (
    CommSyntaxError,
    Concept,
    Param,
    check_name,
    comment_block,
    render_assignment,
    render_call,
)


@dataclass
class Statement:
    """One statement of the file: its source lines and the comment lines above it."""

    lines: list[str]
    comments: list[str] = field(default_factory=list)
    command: str | None = None  # None for a constant
    target: str | None = None
    keywords: dict[str, Any] = field(default_factory=dict)


class CommandFile:
    """Statements of a ``.comm`` file, each checked against the pinned catalog when added."""

    def __init__(self, commands_dir: Path = catalog.DEFAULT_COMMANDS_DIR) -> None:
        self.commands_dir = commands_dir
        self.header: list[str] = []
        self.statements: list[Statement] = []
        self._pending: list[str] = []
        self._names: dict[str, Concept | Param] = {}

    # -- comments ----------------------------------------------------------------------------

    def add_header(self, text: str) -> None:
        """Comment block at the top of the file, before the first statement."""
        if self.statements:
            raise CommSyntaxError("the header must come before the first statement")
        if self.header:
            self.header.append("")
        self.header.extend(comment_block(text))

    def add_comment(self, text: str) -> None:
        """Comment lines written just above the next statement."""
        self._pending.extend(comment_block(text))

    # -- statements --------------------------------------------------------------------------

    def _claim(self, name: str) -> str:
        check_name(name)
        if name in self._names:
            raise CommSyntaxError(f"name {name!r} is already used in this file")
        return name

    def _add(self, statement: Statement) -> None:
        statement.comments, self._pending = self._pending, []
        self.statements.append(statement)

    def param(self, name: str, value: Any, note: str | None = None) -> Param:
        """``NAME = value`` (a number, string or tuple), usable as a keyword value."""
        if isinstance(value, Concept | Param | Mapping):
            raise CommSyntaxError(f"{name}: a constant takes a number, a string or a tuple")
        p = Param(self._claim(name), value)
        self._add(Statement(render_assignment(name, value, note), target=name))
        self._names[name] = p
        return p

    def call(
        self,
        command: str,
        result: str | Concept | None = None,
        *,
        reuse: bool = False,
        result_type: str | None = None,
        **keywords: Any,
    ) -> Concept | None:
        """Add ``[result = ]COMMAND(**keywords)``; return the result concept, if any.

        ``result`` is a new name, or with ``reuse=True`` the concept the command updates in
        place (``reuse=`` is then written first, as upstream test cases do). ``result_type``
        names the result's data structure when the catalog's depends on the keywords.
        """
        spec = catalog.load_command(command, self.commands_dir)
        if reuse:
            if not isinstance(result, Concept) or self._names.get(result.name) != result:
                raise CommSyntaxError(f"{command}: reuse needs a concept defined in this file")
            target = result.name
        elif isinstance(result, Concept):
            raise CommSyntaxError(f"{command}: pass a new name, or reuse=True")
        else:
            target = result
        catalog.check_call(spec, keywords, result=target is not None, reuse=reuse)
        if reuse:
            concept = result
        elif target is not None:
            concept = Concept(self._claim(target), result_type or spec.result_type)
        else:
            concept = None
        self._add(
            Statement(
                render_call(command, keywords, target=target, reuse=reuse),
                command=command,
                target=target,
                keywords=dict(keywords),
            )
        )
        if concept is not None:
            self._names[concept.name] = concept
        return concept

    # -- output ------------------------------------------------------------------------------

    def text(self) -> str:
        """The file: header, then statements separated by a blank line.

        Consecutive constants are kept together without a blank line between them.
        """
        out: list[str] = list(self.header)
        previous: Statement | None = None
        for st in self.statements:
            grouped = (
                previous is not None
                and previous.command is None
                and st.command is None
                and not st.comments
            )
            if out and not grouped:
                out.append("")
            out.extend(st.comments)
            out.extend(st.lines)
            previous = st
        if self._pending:
            raise CommSyntaxError("a comment was added after the last statement")
        return "\n".join(out) + "\n"
