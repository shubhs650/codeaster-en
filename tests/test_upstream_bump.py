"""Tests for ``caen upstream bump`` (task 7.1).

The diff functions are checked on hand-made documents. The bump itself runs against a
throw-away git repository standing in for the mirror: tag ``1.0.0`` holds the pinned
``upstream/code_aster`` tree (so the committed ``en/`` extraction is its "from" side) and tag
``1.0.1`` edits one keyword, two messages and removes one family. No network is used.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from codeaster_en.upstream import bump, diff

REPO = Path(__file__).resolve().parents[1]
UPSTREAM = REPO / "upstream"


def _kw(path: str, **fields: object) -> dict:
    name = path.rsplit("/", 1)[-1]
    return {"name": name, "path": path, "kind": "simple", "source": {"line": 1}, **fields}


def _cmd(name: str, keywords: list[dict], **fields: object) -> dict:
    return {"command": name, "kind": "OPER", "source": {"line": 1}, "keywords": keywords, **fields}


# --------------------------------------------------------------------------------------
# diff
# --------------------------------------------------------------------------------------


def test_compare_catalog_added_removed_changed() -> None:
    old = {
        "A": _cmd("A", [_kw("INFO", default=1, into=[1, 2]), _kw("GONE")]),
        "B": _cmd("B", []),
        "C": _cmd("C", [_kw("X")]),
    }
    new = {
        "A": _cmd("A", [_kw("INFO", default=2, into=[1, 2, 3], source={"line": 9}), _kw("NEW")]),
        "C": _cmd("C", [_kw("X", source={"line": 42})], source={"line": 7}),
        "D": _cmd("D", []),
    }
    result = diff.compare_catalog(old, new)
    assert result.added == ["D"]
    assert result.removed == ["B"]
    assert result.unchanged == 1  # C: only source lines moved
    [change] = result.changed
    assert change.command == "A"
    assert change.added == ["NEW"]
    assert change.removed == ["GONE"]
    [kw] = change.changed
    assert kw.path == "INFO"
    assert kw.changes == ["default: 1 → 2", "into: +[3]"]


def test_repeated_definitions_are_merged() -> None:
    """A keyword declared in several blocs is one path with several definitions."""
    old = _cmd("A", [_kw("S/N", default=30)] * 3 + [_kw("S/M")])
    new = _cmd("A", [_kw("S/N")] * 3 + [_kw("S/M", status="o")])
    change = diff.compare_command("A", old, new)
    assert change is not None
    by_path = {kw.path: kw.changes for kw in change.changed}
    assert by_path == {
        "S/N": ["default: removed (was 30) (in 3 definitions)"],
        "S/M": ['status: added "o"'],
    }
    grown = _cmd("A", [_kw("S/N", default=30)] * 4 + [_kw("S/M")])
    [kw] = diff.compare_command("A", old, grown).changed
    assert kw.changes == ["definitions: 3 → 4"]


def _family(name: str, messages: dict[int, dict]) -> dict:
    out = {}
    for number, fields in messages.items():
        fr = fields["fr"]
        out[str(number)] = {
            "id": f"{name}_{number}",
            "placeholders": [p for p in ("%(i1)d", "%(k1)s") if p in fr],
            "en": None,
            **fields,
        }
    return {"family": name, "messages": out}


def test_compare_messages() -> None:
    old = {
        "F": _family(
            "F",
            {
                1: {"fr": "même", "en": "same", "method": "assisted"},
                2: {"fr": "avant %(i1)d", "en": "before %(i1)d", "method": "machine"},
                3: {"fr": "texte"},
                4: {"fr": "retiré", "en": "removed", "method": "assisted"},
            },
        ),
        "G": _family("G", {1: {"fr": "famille retirée"}}),
    }
    new = {
        "F": _family("F", {1: {"fr": "même"}, 2: {"fr": "après %(k1)s"}, 3: {"fr": "texte 2"}}),
        "H": _family("H", {1: {"fr": "nouvelle"}}),
    }
    result = diff.compare_messages(old, new)
    assert result.families_added == ["H"]
    assert result.families_removed == ["G"]
    assert result.added == ["H_1"]
    assert result.removed == [("F_4", "assisted"), ("G_1", None)]
    assert result.unchanged == 1
    assert [(c.id, c.method, c.placeholders_changed) for c in result.changed] == [
        ("F_2", "machine", True),
        ("F_3", None, False),
    ]
    assert [c.id for c in result.stale] == ["F_2"]


def test_changed_span() -> None:
    before = "Le début est long. " * 3 + "un mot " + "et la fin est longue aussi." * 3
    after = before.replace("un mot", "deux mots")
    old, new = diff.changed_span(before, after, context=5)
    assert old == "…ong. un mot et l…"
    assert new == "…ong. deux mots et l…"
    assert diff.changed_span("abc", "abc") == ("abc", "abc")


def test_resolve_tags() -> None:
    tags = {"17.4.26": "aaa", "17.5.0": "aaa", "17.5.8": "bbb", "stable": "aaa", "odd": "ccc"}
    assert bump.resolve(tags, "17.5.8") == ("17.5.8", "bbb")
    assert bump.resolve(tags, "stable") == ("17.4.26", "aaa")
    with pytest.raises(bump.BumpError, match="not found"):
        bump.resolve(tags, "18.0.0")
    with pytest.raises(bump.BumpError, match="no version tag"):
        bump.resolve(tags, "odd")


# --------------------------------------------------------------------------------------
# bump against a local stand-in for the mirror
# --------------------------------------------------------------------------------------


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, (path, old)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


@pytest.fixture
def overlay(tmp_path: Path) -> Path:
    """An overlay checkout whose ``upstream/`` is a local repo tagged 1.0.0 and 1.0.1."""
    if not (UPSTREAM / "code_aster" / "Cata").is_dir():
        pytest.skip("upstream/ submodule not checked out")
    repo = tmp_path / "overlay"
    up = repo / "upstream"
    shutil.copytree(UPSTREAM / "code_aster", up / "code_aster")
    _git(up, "init", "-q")
    _git(up, "config", "user.email", "test@example.invalid")
    _git(up, "config", "user.name", "test")
    _git(up, "add", "-A")
    _git(up, "commit", "-q", "-m", "1.0.0")
    _git(up, "tag", "1.0.0")
    first = _git(up, "rev-parse", "HEAD")
    _edit(
        up / "code_aster/Cata/Commands/affe_modele.py",
        'INFO=SIMP(statut="f", typ="I", defaut=1, into=(1, 2)),',
        'INFO=SIMP(statut="f", typ="I", defaut=2, into=(1, 2)),',
    )
    homo1 = up / "code_aster/Messages/homo1.py"
    _edit(homo1, "une influence négligeable sur", "une influence sur")
    _edit(homo1, "plusieurs (%(i1)d) domaines", "plusieurs (%(i2)d) domaines")
    (up / "code_aster/Messages/modal0.py").unlink()
    _git(up, "commit", "-q", "-am", "1.0.1")
    _git(up, "tag", "1.0.1")
    _git(up, "tag", "stable")
    _git(up, "remote", "add", "origin", str(up))
    _git(up, "checkout", "-q", "--detach", first)

    for rel in ("en/commands", "en/messages"):
        shutil.copytree(REPO / rel, repo / rel)
    for rel in ("en/glossary.yaml", "tools/codeaster_en/__init__.py", "CONTAINER_IMAGE"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, repo / rel)
    (repo / "UPSTREAM_VERSION").write_text("1.0.0\n", encoding="utf-8")
    return repo


def _tree(repo: Path) -> dict[str, bytes]:
    return {
        p.relative_to(repo).as_posix(): p.read_bytes()
        for p in sorted(repo.rglob("*"))
        if p.is_file() and "upstream" not in p.relative_to(repo).parts
    }


def test_bump_dry_run_then_apply(overlay: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    before = _tree(overlay)
    head = _git(overlay / "upstream", "rev-parse", "HEAD")

    dry = bump.bump(overlay, "stable", dry_run=True)
    assert dry.report_path is None and dry.written == []
    assert _tree(overlay) == before
    assert _git(overlay / "upstream", "rev-parse", "HEAD") == head

    assert dry.report.new["upstream"] == "1.0.1"
    cat, msg = dry.report.catalog, dry.report.messages
    # PRE_SEISME_NONL builds its AFFE_MODELE keyword from the AFFE_MODELE catalog.
    assert [c.command for c in cat.changed] == ["AFFE_MODELE", "PRE_SEISME_NONL"]
    change = cat.changed[0]
    assert change.command == "AFFE_MODELE"
    assert [(k.path, k.changes) for k in change.changed] == [("INFO", ["default: 1 → 2"])]
    assert msg.families_removed == ["MODAL0"]
    assert [(c.id, c.placeholders_changed) for c in msg.stale] == [("HOMO1_18", True)]
    assert dry.report.references == {"AFFE_MODELE": "assisted"}
    for heading in ("# Upstream diff 1.0.0 → 1.0.1", "## Summary", "#### AFFE_MODELE"):
        assert heading in dry.markdown
    assert "| `HOMO1_18` | stale (assisted) | **yes** |" in dry.markdown

    # The secondary generators need parts of the repo the fixture does not copy; their own
    # tests cover them. Record that the bump calls them.
    calls: list[str] = []
    monkeypatch.setattr(bump.astest_extractor, "write", lambda r, o: calls.append("astest"))
    monkeypatch.setattr(
        bump.inventory_extractor, "write", lambda r: calls.append("inventory") or r / "INV"
    )
    monkeypatch.setattr(
        bump.gettext_po, "build", lambda r: calls.append("gettext") or {"po": r / "PO"}
    )
    image = "simvia/code_aster:1.0.1@sha256:" + "0" * 64
    applied = bump.bump(overlay, "1.0.1", image=image)
    assert calls == ["astest", "inventory", "gettext"]
    assert applied.report_path == overlay / "docs/upstream-diffs/1.0.0-1.0.1.md"
    assert applied.report_path.read_text(encoding="utf-8") == applied.markdown
    assert "(applied)" in applied.markdown
    assert _git(overlay / "upstream", "rev-parse", "HEAD") == _git(
        overlay / "upstream", "rev-parse", "1.0.1"
    )
    assert (overlay / "UPSTREAM_VERSION").read_text() == "1.0.1\n"
    assert '__version__ = "1.0.1.1"' in (overlay / "tools/codeaster_en/__init__.py").read_text()
    assert (overlay / "CONTAINER_IMAGE").read_text().splitlines()[-1] == image
    assert not (overlay / "en/messages/MODAL0.en.json").exists()
    assert applied.deleted == [overlay / "en/messages/MODAL0.en.json"]

    homo1 = json.loads((overlay / "en/messages/HOMO1.en.json").read_text(encoding="utf-8"))
    assert homo1["_generated_from"]["upstream"] == "1.0.1"
    m18 = homo1["messages"]["18"]
    assert m18["stale"] is True and m18["method"] == "assisted"
    assert m18["placeholders"] == ["%(i2)d"]
    assert "stale" not in homo1["messages"]["17"]
    affe = json.loads((overlay / "en/commands/AFFE_MODELE.json").read_text(encoding="utf-8"))
    assert affe["_generated_from"]["upstream_commit"] == _git(
        overlay / "upstream", "rev-parse", "HEAD"
    )
    # Untouched commands come out byte-identical apart from the provenance header.
    old = json.loads((REPO / "en/commands/DEBUT.json").read_text(encoding="utf-8"))
    new = json.loads((overlay / "en/commands/DEBUT.json").read_text(encoding="utf-8"))
    old.pop("_generated_from"), new.pop("_generated_from")
    assert old == new

    with pytest.raises(bump.BumpError, match="already at"):
        bump.bump(overlay, "1.0.1", dry_run=True)


def test_bump_refuses(overlay: Path) -> None:
    with pytest.raises(bump.BumpError, match="digest"):
        bump.bump(overlay, "1.0.1", image="simvia/code_aster:1.0.1")
    (overlay / "upstream/code_aster/stray.txt").write_text("x", encoding="utf-8")
    with pytest.raises(bump.BumpError, match="local changes"):
        bump.bump(overlay, "1.0.1")
