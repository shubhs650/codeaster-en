"""Restricted reading of a code_aster command file (task 4.6, ``docs/REPORT-SPEC.md`` §6).

A ``.comm`` file is Python. The report needs its command calls with their keyword values, not
to run it, so this module walks the syntax tree and evaluates only what is safe and static:
numbers, strings, tuples and lists, ``_F(...)`` factor keywords, arithmetic on numbers, and
names bound earlier to such values (``P = 2.0`` then ``PRES=P``). A name bound to a command
result is a :class:`Ref` to that result object. Anything else (loops, function calls other
than commands, imported values) is kept as :class:`Unevaluated` with its source text, and the
statements that were skipped are listed, so the report can say what it could not read.

The same reader parses the command echo that ``ExecuteCommand`` prints in the ``.mess``: that
echo is valid Python too, with every default value filled in.
"""

from __future__ import annotations

import ast
import operator
from dataclasses import dataclass, field
from typing import Any

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


@dataclass(frozen=True)
class Ref:
    """A reference to a result object (concept) produced by an earlier command."""

    name: str


@dataclass(frozen=True)
class Unevaluated:
    """An expression this reader does not evaluate; ``source`` is its text."""

    source: str


@dataclass
class Call:
    """One command call: ``concept = COMMAND(**keywords)`` at ``line`` of the file."""

    command: str
    concept: str | None
    line: int
    keywords: dict[str, Any]

    def get(self, key: str, default: Any = None) -> Any:
        return self.keywords.get(key, default)

    def occurrences(self, key: str) -> list[dict[str, Any]]:
        """The occurrences of a factor keyword (one ``_F`` or a tuple of them) as dicts."""
        value = self.keywords.get(key)
        if isinstance(value, dict):
            return [value]
        if isinstance(value, list):
            return [v for v in value if isinstance(v, dict)]
        return []


@dataclass
class CommandFile:
    calls: list[Call] = field(default_factory=list)
    constants: dict[str, Any] = field(default_factory=dict)
    skipped: list[int] = field(default_factory=list)  # lines of statements not read
    syntax_error: str | None = None

    def find(self, command: str) -> list[Call]:
        return [c for c in self.calls if c.command == command]

    def producer(self, concept: str, before: int | None = None) -> Call | None:
        """The last call that (re)defined ``concept`` before the given line."""
        found = None
        for c in self.calls:
            if before is not None and c.line >= before:
                break
            if c.concept == concept:
                found = c
        return found


def is_command_name(name: str) -> bool:
    return name.isupper() and name[0].isalpha() and name != "_F"


class _Evaluator:
    def __init__(self, text: str, env: dict[str, Any]) -> None:
        self.text = text
        self.env = env

    def unevaluated(self, node: ast.AST) -> Unevaluated:
        return Unevaluated(ast.get_source_segment(self.text, node) or ast.dump(node))

    def value(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Tuple | ast.List):
            return [self.value(e) for e in node.elts]
        if isinstance(node, ast.Name):
            return self.env.get(node.id, Unevaluated(node.id))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
            v = self.value(node.operand)
            if isinstance(v, int | float) and not isinstance(v, bool):
                return -v if isinstance(node.op, ast.USub) else v
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            a, b = self.value(node.left), self.value(node.right)
            if all(isinstance(x, int | float) and not isinstance(x, bool) for x in (a, b)):
                try:
                    return _BINOPS[type(node.op)](a, b)
                except (ArithmeticError, ValueError):
                    pass
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_F"
            and not node.args
        ):
            return self.keywords(node)
        return self.unevaluated(node)

    def keywords(self, call: ast.Call) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for kw in call.keywords:
            if kw.arg is None:  # **kwargs
                out["**"] = self.unevaluated(kw.value)
            else:
                out[kw.arg] = self.value(kw.value)
        return out


def _command_call(node: ast.AST) -> ast.Call | None:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and is_command_name(node.func.id)
    ):
        return node
    return None


def parse(text: str) -> CommandFile:
    """Read the command calls of a ``.comm`` file (or of a ``.mess`` command echo)."""
    out = CommandFile()
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        out.syntax_error = f"line {exc.lineno}: {exc.msg}"
        return out
    env: dict[str, Any] = {}
    ev = _Evaluator(text, env)
    for stmt in tree.body:
        target: str | None = None
        value: ast.AST | None = None
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            if isinstance(stmt.targets[0], ast.Name):
                target, value = stmt.targets[0].id, stmt.value
        elif isinstance(stmt, ast.Expr):
            value = stmt.value
        elif isinstance(stmt, ast.Import | ast.ImportFrom):
            continue
        if value is None:
            out.skipped.append(stmt.lineno)
            continue
        call = _command_call(value)
        if call is not None and not call.args:
            assert isinstance(call.func, ast.Name)
            out.calls.append(Call(call.func.id, target, stmt.lineno, ev.keywords(call)))
            if target:
                env[target] = Ref(target)
            continue
        if target is not None:
            v = ev.value(value)
            if isinstance(v, Unevaluated):
                out.skipped.append(stmt.lineno)
            else:
                out.constants[target] = v
            env[target] = v
            continue
        out.skipped.append(stmt.lineno)
    return out


def as_list(value: Any) -> list[Any]:
    """A keyword value as a list (code_aster accepts a scalar where a list is allowed)."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def to_jsonable(value: Any) -> Any:
    """Plain JSON form: a :class:`Ref` becomes ``{"ref": name}``, unevaluated text
    ``{"expr": source}``."""
    if isinstance(value, Ref):
        return {"ref": value.name}
    if isinstance(value, Unevaluated):
        return {"expr": value.source}
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    return value
