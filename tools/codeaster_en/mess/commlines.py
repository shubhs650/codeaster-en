"""Map line numbers of the file the solver ran back to the user's ``.comm``.

``run_aster`` does not execute the ``.comm`` as written: ``RunAster.change_comm_file``
(upstream ``run_aster/run.py``) adds the ``code_aster`` imports in front of ``DEBUT`` or
``POURSUITE`` (``command_files.add_import_commands``), a ``__file__`` line when the text changed
(``file_changed``) and a coding line (``add_coding_line``), then runs ``<name>.changed.py``.
The ``.mess`` and Python tracebacks quote line numbers of that file. In the fixtures the shift
is 12 lines after ``DEBUT`` and 4 before it.

:func:`line_mapper` rebuilds the changed text with the same three steps (copied from
``run_aster/command_files.py`` at the pinned upstream) and aligns it with the original by
lines, so a line the user wrote maps to its own number and an inserted line maps to ``None``.
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Callable
from string import Template

_STARTER = Template(
    """
# temporarly added for compatibility with code_aster legacy
from math import *
${prolog}
import code_aster
${imports}

${starter}"""
)
_NOINIT_START = Template(
    _STARTER.safe_substitute(
        imports="from code_aster.Commands import *\nfrom code_aster import CA",
    )
)
_RE_DONE = re.compile(r"^from +code_aster(\.Commands| +import +CA)", re.M)
_RE_INIT = re.compile("^(?P<init>(DEBUT|POURSUITE))", re.M)
_RE_CODING = re.compile(r"^#( *(?:|\-\*\- *|en)coding.*)" + "\n", re.M)


def changed_text(comm_text: str, original: str = "run.comm") -> str:
    """Text of ``<name>.changed.py`` as ``run_aster`` writes it for a sequential study."""
    text = comm_text
    if not _RE_DONE.search(text) and _RE_INIT.search(text):
        text = _RE_INIT.sub(_NOINIT_START.substitute(prolog="", starter=r"\g<init>"), text)
    if text.strip() != comm_text.strip():
        text = f'# original filename\n__file__ = r"{original}"\n\n' + text
    text = _RE_CODING.sub("", text)
    return "# coding=utf-8\n" + text


def line_mapper(comm_text: str) -> Callable[[int], int | None]:
    """Return ``f(changed_line) -> comm_line`` (1-based), ``None`` for inserted lines."""
    old = comm_text.splitlines()
    new = changed_text(comm_text).splitlines()
    mapping: dict[int, int] = {}
    matcher = difflib.SequenceMatcher(a=new, b=old, autojunk=False)
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            mapping[block.a + k + 1] = block.b + k + 1
    return mapping.get
