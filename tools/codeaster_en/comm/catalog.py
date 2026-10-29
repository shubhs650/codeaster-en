"""Check a command call against the pinned catalog in ``en/commands/<CMD>.json`` (task 6.1).

This is the builder's guard (ARCHITECTURE §4.8): it cannot emit a command or keyword the
pinned upstream does not know. It follows upstream's own checker
(``code_aster/Cata/Language/SyntaxChecker.py``) on the points a generated file can get wrong:

- unknown command, unknown keyword (``BLOC`` conditions evaluated as upstream does, with the
  keyword defaults filled in first; a condition that cannot be evaluated disables the block,
  as in ``SyntaxObjects.Bloc.isEnabled``);
- missing mandatory keyword (``statut='o'``);
- the catalog rules ``UN_PARMI``, ``AU_MOINS_UN``, ``EXCLUS``, ``PRESENT_PRESENT``,
  ``PRESENT_ABSENT``, ``ENSEMBLE``, ``NON_VIDE`` (``Rules.py``), on the keywords given plus
  defaults;
- number of values / occurrences (``max``, ``min``), value type, allowed values (``into``),
  bounds (``val_min``, ``val_max``);
- ``reuse`` only on reentrant commands; a result name only on commands that return one.

Concept types are checked when the builder knows the concept's type; the data-structure
hierarchy needed for that is :data:`DS_PARENTS` (from ``code_aster/Cata/Language/
DataStructure.py``, checked against it by the tests).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from codeaster_en.comm.syntax import Commented, Concept, Number, Param

DEFAULT_COMMANDS_DIR = Path(__file__).resolve().parents[3] / "en" / "commands"

# Parent class of each data structure the builder produces or consumes, as declared in
# upstream code_aster/Cata/Language/DataStructure.py (tests/test_comm.py checks every pair).
DS_PARENTS: dict[str, str] = {
    "evol_elas": "evol_sdaster",
    "evol_sdaster": "resultat_sdaster",
    "mode_meca": "dyna_phys",
    "dyna_phys": "resultat_sdaster",
    "table_container": "table_sdaster",
    "matr_asse_depl_r": "matr_asse_gd",
    "matr_asse_gd": "matr_asse",
    "matr_elem_depl_r": "matr_elem",
}

_SCALAR_TYPES = {"R", "I", "TXM", "C", "UnitDefault", "UnitMed", "grma", "grno", "ma", "no"}
_UNCHECKED = {"not_checked", "CO", "DataStructure"}


class CatalogError(ValueError):
    """The call does not match the pinned catalog. ``path`` locates the keyword."""

    def __init__(self, path: str, problem: str) -> None:
        super().__init__(f"{path}: {problem}")
        self.path = path
        self.problem = problem


@dataclass(frozen=True)
class CommandSpec:
    """The catalog entry of one command (``en/commands/<CMD>.json``)."""

    name: str
    kind: str
    reentrant: str | None
    result_types: tuple[str, ...]
    result_type_depends_on_keywords: bool
    keywords: tuple[dict[str, Any], ...]
    rules: tuple[dict[str, Any], ...]
    upstream: str

    @property
    def returns_result(self) -> bool:
        return bool(self.result_types)

    @property
    def result_type(self) -> str | None:
        """The result type when it does not depend on the keywords, else ``None``."""
        if len(self.result_types) == 1 and not self.result_type_depends_on_keywords:
            return self.result_types[0]
        return None


@cache
def load_command(name: str, commands_dir: Path = DEFAULT_COMMANDS_DIR) -> CommandSpec:
    path = commands_dir / f"{name}.json"
    if not path.is_file():
        raise CatalogError(name, f"unknown command (no {path.name} in the pinned catalog)")
    data = json.loads(path.read_text(encoding="utf-8"))
    return CommandSpec(
        name=data["command"],
        kind=data["kind"],
        reentrant=data.get("reentrant"),
        result_types=tuple(data.get("result_types") or ()),
        result_type_depends_on_keywords=bool(data.get("result_type_depends_on_keywords")),
        keywords=tuple(data["keywords"]),
        rules=tuple(data.get("rules") or ()),
        upstream=data["_generated_from"]["upstream"],
    )


def is_subtype(actual: str, allowed: str) -> bool:
    seen = actual
    while True:
        if seen == allowed:
            return True
        if seen not in DS_PARENTS:
            return False
        seen = DS_PARENTS[seen]


def check_call(
    spec: CommandSpec, keywords: Mapping[str, Any], *, result: bool, reuse: bool
) -> None:
    """Raise :class:`CatalogError` if ``spec.name(**keywords)`` breaks the catalog."""
    if result and not spec.returns_result:
        raise CatalogError(spec.name, "this command returns no result; do not name one")
    if not result and spec.returns_result:
        raise CatalogError(spec.name, "this command returns a result; give it a name")
    if reuse and (spec.reentrant or "n")[:1] not in ("o", "f"):
        raise CatalogError(spec.name, "reuse is not allowed (command is not reentrant)")
    if not reuse and (spec.reentrant or "")[:1] == "o":
        raise CatalogError(spec.name, "this command must reuse its input (reentrant 'o')")
    entries = [k for k in spec.keywords if k["name"] != "reuse"]
    _check_occurrence(spec.name, entries, list(spec.rules), dict(keywords), {})


def _values(value: Any) -> list[Any]:
    if isinstance(value, str | Mapping) or not isinstance(value, Sequence):
        return [value]
    return list(value)


def _plain(value: Any) -> Any:
    """The value as upstream's checker sees it in a block condition."""
    if isinstance(value, Param):
        return _plain(value.value)
    if isinstance(value, Number):
        return value.value
    if isinstance(value, Concept):
        return value
    if isinstance(value, str | Mapping) or not isinstance(value, Sequence):
        return value
    return tuple(_plain(v) for v in value)


class _Context(dict):
    """Block evaluation namespace: unknown names (data-structure classes) are their name."""

    def __missing__(self, key: str) -> str:
        return key


def _block_helpers(ctx: Mapping[str, Any]) -> dict[str, Any]:
    # Same helpers as upstream SyntaxUtils.block_utils.
    def exists(name: str) -> bool:
        return ctx.get(name) is not None

    def is_in(name: Any, values: Any) -> bool:
        names = [name] if isinstance(name, str) else list(name)
        wanted = {values} if isinstance(values, str | int | float) else set(values)
        found: list[Any] = []
        for n in names:
            if not exists(n):
                return False
            v = ctx[n]
            found.extend(v if isinstance(v, tuple | list) else [v])
        return not wanted.isdisjoint(found)

    def value(name: str, default: Any = "") -> Any:
        return ctx.get(name, default)

    def is_type(name: str) -> Any:
        v = value(name)
        return v.type if isinstance(v, Concept) else type(v).__name__

    def size(name: str) -> int:
        return len(ctx.get(name))

    def less_than(name: str, test: Any) -> bool:
        return value(name) < test

    def greater_than(name: str, test: Any) -> bool:
        return value(name) > test

    return {
        "abs": abs,
        "len": len,
        "type": type,
        "isinstance": isinstance,
        "str": str,
        "int": int,
        "float": float,
        "tuple": tuple,
        "list": list,
        "AsType": lambda v: v.type if isinstance(v, Concept) else type(v).__name__,
        "exists": exists,
        "is_in": is_in,
        "equal_to": is_in,
        "value": value,
        "is_type": is_type,
        "size": size,
        "less_than": less_than,
        "greater_than": greater_than,
    }


def _enabled(condition: str, ctx: Mapping[str, Any]) -> bool:
    namespace = _Context({k: v for k, v in ctx.items()})
    namespace.update(_block_helpers(ctx))
    try:
        return bool(eval(condition, {"__builtins__": {}}, namespace))  # noqa: S307
    except Exception:  # noqa: BLE001 -- upstream disables a block it cannot evaluate
        return False


def _active(
    entries: Sequence[dict[str, Any]], ctx: Mapping[str, Any]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Keywords and rules visible at this level, with enabled blocks expanded."""
    keywords: dict[str, dict[str, Any]] = {}
    rules: list[dict[str, Any]] = []
    for entry in entries:
        if entry["kind"] == "bloc":
            if _enabled(entry["condition"], ctx):
                sub_kw, sub_rules = _active(entry.get("keywords", []), ctx)
                keywords.update(sub_kw)
                rules.extend(entry.get("rules", []))
                rules.extend(sub_rules)
        else:
            keywords[entry["name"]] = entry
    return keywords, rules


def _with_defaults(
    entries: Sequence[dict[str, Any]], given: dict[str, Any], parent: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Given keywords plus defaults, the visible keywords and the block rules (fixed point)."""
    filled = dict(given)
    for _ in range(10):
        ctx = {**parent, **{k: _plain(v) for k, v in filled.items()}}
        visible, rules = _active(entries, ctx)
        added = False
        for name, entry in visible.items():
            if name in filled:
                continue
            if entry["kind"] == "simple" and entry.get("default") not in (None, ""):
                filled[name] = entry["default"]
                added = True
            elif entry["kind"] == "factor" and entry.get("status") in ("c", "d"):
                filled[name] = {}
                added = True
        if not added:
            return filled, visible, rules
    return filled, visible, rules


def _check_occurrence(
    path: str,
    entries: Sequence[dict[str, Any]],
    own_rules: list[dict[str, Any]],
    given: dict[str, Any],
    parent: Mapping[str, Any],
) -> None:
    filled, visible, block_rules = _with_defaults(entries, given, parent)
    ctx = {**parent, **{k: _plain(v) for k, v in filled.items()}}
    for name in given:
        if name not in visible:
            known = ", ".join(sorted(visible)) or "none"
            raise CatalogError(f"{path}/{name}", f"unknown keyword here (known: {known})")
    for name, entry in visible.items():
        if entry.get("status") == "o" and name not in filled:
            raise CatalogError(f"{path}/{name}", "mandatory keyword is missing")
    for rule in own_rules + block_rules:
        _check_rule(path, rule, filled)
    for name, value in given.items():
        entry = visible[name]
        if entry["kind"] == "factor":
            _check_factor(f"{path}/{name}", entry, value, ctx)
        else:
            _check_simple(f"{path}/{name}", entry, value)


def _present(occurrence: Mapping[str, Any], name: str) -> bool:
    return occurrence.get(name) is not None


def _check_rule(path: str, rule: Mapping[str, Any], occ: Mapping[str, Any]) -> None:
    names = rule["keywords"]
    count = sum(_present(occ, n) for n in names)
    if count == 0 and rule.get("defaults"):
        # UN_PARMI / AU_MOINS_UN with default values: upstream inserts them (Rules.py).
        count = len(rule["defaults"])
    kind = rule["rule"]
    listed = ", ".join(names)
    if kind == "UN_PARMI" and count != 1:
        raise CatalogError(path, f"exactly one of {listed} is required (rule UN_PARMI)")
    if kind == "AU_MOINS_UN" and count < 1:
        raise CatalogError(path, f"at least one of {listed} is required (rule AU_MOINS_UN)")
    if kind == "EXCLUS" and count > 1:
        raise CatalogError(path, f"at most one of {listed} may be given (rule EXCLUS)")
    first = _present(occ, names[0])
    if kind == "PRESENT_PRESENT" and first and count != len(names):
        raise CatalogError(path, f"{names[0]} needs {', '.join(names[1:])} (PRESENT_PRESENT)")
    if kind == "PRESENT_ABSENT" and first and count != 1:
        raise CatalogError(path, f"{names[0]} excludes {', '.join(names[1:])} (PRESENT_ABSENT)")
    if kind == "ENSEMBLE" and count not in (0, len(names)):
        raise CatalogError(path, f"{listed} go together: all or none (rule ENSEMBLE)")
    if kind == "NON_VIDE" and not occ:
        raise CatalogError(path, "at least one keyword is required (rule NON_VIDE)")


def _check_count(path: str, entry: Mapping[str, Any], count: int, what: str) -> None:
    nmax = entry.get("max", 1)
    if nmax != "**" and count > int(nmax):
        raise CatalogError(path, f"at most {nmax} {what} allowed, got {count}")
    nmin = entry.get("min", 0)
    if count < int(nmin):
        raise CatalogError(path, f"at least {nmin} {what} required, got {count}")


def _check_factor(path: str, entry: dict[str, Any], value: Any, parent: Mapping[str, Any]) -> None:
    occurrences = [value] if isinstance(value, Mapping) else list(value)
    occurrences = [o.value if isinstance(o, Commented) else o for o in occurrences]
    if not all(isinstance(o, Mapping) for o in occurrences):
        raise CatalogError(path, "a factor keyword takes _F(...) occurrence(s)")
    _check_count(path, entry, len(occurrences), "occurrence(s)")
    for i, occ in enumerate(occurrences):
        where = path if len(occurrences) == 1 else f"{path}[{i}]"
        _check_occurrence(
            where, entry.get("keywords", []), list(entry.get("rules", [])), dict(occ), parent
        )


def _check_simple(path: str, entry: Mapping[str, Any], value: Any) -> None:
    if isinstance(value, Param):
        value = value.value
    if isinstance(value, Mapping):
        raise CatalogError(path, "a simple keyword does not take _F(...)")
    items = _values(value)
    _check_count(path, entry, len(items), "value(s)")
    types = list(entry.get("type") or [])
    for item in items:
        if isinstance(item, Param):
            item = item.value
        _check_type(path, types, item)
        plain = _plain(item)
        into = entry.get("into")
        if into is not None and not isinstance(plain, Concept) and plain not in into:
            raise CatalogError(path, f"{plain!r} is not one of {into}")
        if isinstance(plain, int | float):
            low, high = entry.get("val_min"), entry.get("val_max")
            if isinstance(low, int | float) and plain < low:
                raise CatalogError(path, f"{plain!r} is below the minimum {low}")
            if isinstance(high, int | float) and plain > high:
                raise CatalogError(path, f"{plain!r} is above the maximum {high}")


def _check_type(path: str, types: list[str], item: Any) -> None:
    if not types or set(types) & _UNCHECKED:
        return
    if isinstance(item, Concept):
        concept_types = [t for t in types if t not in _SCALAR_TYPES]
        if not concept_types:
            raise CatalogError(path, f"expects {'/'.join(types)}, got concept {item.name}")
        if item.type is not None and not any(is_subtype(item.type, t) for t in concept_types):
            raise CatalogError(
                path, f"expects {'/'.join(concept_types)}, got {item.name} ({item.type})"
            )
        return
    plain = _plain(item)
    ok = (
        (isinstance(plain, str) and bool({"TXM", "grma", "grno", "ma", "no"} & set(types)))
        or (
            isinstance(plain, int)
            and not isinstance(plain, bool)
            and bool({"I", "R", "UnitDefault", "UnitMed"} & set(types))
        )
        or (isinstance(plain, float) and "R" in types)
        or ("C" in types and isinstance(plain, int | float | complex))
    )
    if not ok:
        raise CatalogError(path, f"expects {'/'.join(types)}, got {plain!r}")
