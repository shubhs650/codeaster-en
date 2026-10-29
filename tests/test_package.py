"""Packaging (task 6.2, ADR-020): version scheme, shipped data, the wheel's ``.mo``.

Building and installing the wheel is ``scripts/check-wheel.sh`` (CI job ``package``); these
tests cover what it relies on without a build.
"""

from __future__ import annotations

import ast
import gettext
import re
from pathlib import Path

import codeaster_en
from codeaster_en import data
from codeaster_en.comm import catalog as comm_catalog
from codeaster_en.mess import catalog as mess_catalog
from codeaster_en.results import labels
from codeaster_en.translate import gettext_po, mo

REPO = Path(__file__).resolve().parents[1]
SETUP = REPO / "tools" / "setup.py"


def _setup_constant(name: str):
    tree = ast.parse(SETUP.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise KeyError(name)


def test_version_is_upstream_tag_plus_overlay_serial() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+\.\d+", codeaster_en.__version__)
    assert codeaster_en.__version__.rsplit(".", 1)[0] == data.upstream_version()


def test_checkout_data_is_used_in_a_checkout() -> None:
    assert data.root() == REPO
    assert comm_catalog.DEFAULT_COMMANDS_DIR == REPO / "en" / "commands"
    assert mess_catalog.DEFAULT_MESSAGES_DIR == REPO / "en" / "messages"
    assert labels.DEFAULT_GLOSSARY == REPO / "en" / "glossary.yaml"


def test_shipped_data_covers_runtime_reads() -> None:
    shipped: set[Path] = set()
    for pattern in _setup_constant("DATA"):
        matches = set(REPO.glob(pattern))
        assert matches, f"setup.py DATA {pattern!r} matches nothing"
        shipped |= matches
    runtime = {data.glossary_path(), REPO / "UPSTREAM_VERSION", REPO / "LICENSE"}
    runtime |= set(data.commands_dir().glob("*.json"))
    runtime |= set(data.messages_dir().glob("*.en.json"))
    runtime.add(REPO / gettext_po.PO_RELPATH)
    assert runtime <= shipped, sorted(str(p) for p in runtime - shipped)


def test_mo_from_po_equals_mo_from_messages(tmp_path: Path) -> None:
    po = (REPO / gettext_po.PO_RELPATH).read_text(encoding="utf-8")
    entries, provenance = gettext_po.load(REPO)
    built = mo.write(mo.read_po(po))
    assert built == gettext_po.render_mo(entries, provenance)
    path = gettext_po.mo_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(built)
    catalog = gettext.translation(gettext_po.DOMAIN, str(tmp_path), languages=["en"])
    assert catalog.gettext(entries[0].msgid) == entries[0].msgstr
