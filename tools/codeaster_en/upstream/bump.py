"""``caen upstream bump --to <tag>``: move the ``upstream/`` pin, re-extract, write the diff.

Steps (ARCHITECTURE.md §7, PLAN 7.1, ADR-023):

1. Resolve ``<tag>`` against the mirror with ``git ls-remote``. A version tag (``17.5.8``) is
   used as is; a moving tag (``stable``, ``testing``) is replaced by the lowest version tag on
   the same commit, so ``stable`` → ``17.4.26`` (not ``17.5.0``, the same commit) as in task
   0.3.
2. Fetch that one tag into the shallow submodule (``--depth 1``) and export its
   ``code_aster/`` tree to a temporary directory with ``git archive``. Both extractors read
   the export, so a dry run never touches the ``upstream/`` checkout.
3. Extract commands and messages from the export. Messages keep the translation fields of
   the committed files (``merge_translations``), which marks every translated message whose
   French changed ``stale``.
4. Diff the committed ``en/`` extraction against the new one (:mod:`.diff`).
5. Unless ``dry_run``: check out the new commit in ``upstream/``, write ``UPSTREAM_VERSION``,
   the command and message JSON (files of removed commands and families are deleted), the
   astest index, the inventory block, the gettext ``.po``, the package version
   (``<tag>.1``, ADR-020) and, if given, ``CONTAINER_IMAGE`` (ADR-011). Then write
   ``docs/upstream-diffs/<old>-<new>.md``.

Nothing is committed: the caller (an agent, or task 7.2's scheduled job) reviews the tree and
opens the PR. Rerunning the solver fixtures is listed as follow-up in the report.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import re
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path

from codeaster_en.extract import astest as astest_extractor
from codeaster_en.extract import catalog as catalog_extractor
from codeaster_en.extract import inventory as inventory_extractor
from codeaster_en.extract import messages as messages_extractor
from codeaster_en.translate import gettext_po
from codeaster_en.upstream import diff as diff_module
from codeaster_en.validate import glossary as glossary_validator

COMMANDS_RELDIR = Path("en/commands")
MESSAGES_RELDIR = Path("en/messages")
DIFFS_RELDIR = Path("docs/upstream-diffs")
VERSION_FILE = "UPSTREAM_VERSION"
IMAGE_FILE = "CONTAINER_IMAGE"
INIT_RELPATH = Path("tools/codeaster_en/__init__.py")
GLOSSARY_RELPATH = Path("en/glossary.yaml")
VERSION_TAG = re.compile(r"\d+(\.\d+)+")
_VERSION_LINE = re.compile(r'^__version__ = "[^"]*"$', re.MULTILINE)


class BumpError(RuntimeError):
    """The bump cannot go ahead (unknown tag, dirty checkout, nothing to do, ...)."""


@dataclass
class Result:
    report: diff_module.Report
    markdown: str
    report_path: Path | None
    written: list[Path]
    deleted: list[Path]


def _git(upstream: Path, *args: str, binary: bool = False) -> str | bytes:
    proc = subprocess.run(
        ["git", "-C", str(upstream), *args], capture_output=True, text=not binary, check=False
    )
    if proc.returncode != 0:
        stderr = proc.stderr if isinstance(proc.stderr, str) else proc.stderr.decode()
        raise BumpError(f"git {' '.join(args)}: {stderr.strip()}")
    return proc.stdout


def remote_tags(upstream: Path, remote: str = "origin") -> dict[str, str]:
    """``{tag: commit}`` of the mirror; annotated tags are peeled to their commit."""
    tags: dict[str, str] = {}
    peeled: dict[str, str] = {}
    for line in str(_git(upstream, "ls-remote", "--tags", remote)).splitlines():
        sha, _, ref = line.partition("\t")
        name = ref.removeprefix("refs/tags/")
        if name.endswith("^{}"):
            peeled[name[:-3]] = sha
        else:
            tags[name] = sha
    return {name: peeled.get(name, sha) for name, sha in tags.items()}


def _version_key(tag: str) -> tuple[int, ...]:
    return tuple(int(part) for part in tag.split("."))


def resolve(tags: dict[str, str], wanted: str) -> tuple[str, str]:
    """``(version tag, commit)`` for ``wanted``, a version tag or a moving tag like ``stable``."""
    if wanted not in tags:
        raise BumpError(f"tag {wanted!r} not found in the upstream mirror")
    commit = tags[wanted]
    if VERSION_TAG.fullmatch(wanted):
        return wanted, commit
    same = [t for t, c in tags.items() if c == commit and VERSION_TAG.fullmatch(t)]
    if not same:
        raise BumpError(f"tag {wanted!r} ({commit[:9]}) has no version tag on the same commit")
    return min(same, key=_version_key), commit


def fetch(upstream: Path, tag: str, commit: str, remote: str = "origin") -> None:
    """Make ``commit`` available in the (shallow) submodule."""
    probe = subprocess.run(
        ["git", "-C", str(upstream), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True,
        check=False,
    )
    if probe.returncode == 0:
        return
    _git(
        upstream, "fetch", "--depth", "1", "--no-tags", remote, f"+refs/tags/{tag}:refs/tags/{tag}"
    )


def export(upstream: Path, commit: str, dest: Path) -> Path:
    """Write ``commit``'s ``code_aster/`` tree under ``dest``; return ``dest``."""
    data = _git(upstream, "archive", "--format=tar", commit, "code_aster", binary=True)
    with tarfile.open(fileobj=io.BytesIO(bytes(data))) as tar:
        tar.extractall(dest, filter="data")
    return dest


def _load_dir(directory: Path, suffix: str) -> dict[str, dict]:
    docs = {}
    for path in sorted(directory.glob(f"*{suffix}")):
        if suffix == ".json" and path.name.endswith(messages_extractor.SUFFIX):
            continue
        docs[path.name[: -len(suffix)]] = json.loads(path.read_text(encoding="utf-8"))
    return docs


def committed_commands(repo: Path) -> dict[str, dict]:
    return _load_dir(repo / COMMANDS_RELDIR, ".json")


def committed_messages(repo: Path) -> dict[str, dict]:
    return _load_dir(repo / MESSAGES_RELDIR, messages_extractor.SUFFIX)


def pinned(repo: Path) -> dict[str, str | None]:
    return catalog_extractor.upstream_provenance(repo)


def _reference_status(path: Path) -> str:
    match = re.search(r"^status:\s*(\S+)", path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else "unknown"


def references(repo: Path, catalog: diff_module.CatalogDiff) -> dict[str, str]:
    """``{command: status}`` of the English references whose command changed or went away."""
    names = [c.command for c in catalog.changed] + catalog.removed
    out = {}
    for name in names:
        path = repo / COMMANDS_RELDIR / f"{name}.md"
        if path.is_file():
            out[name] = _reference_status(path)
    return out


def _keyword_names(docs: dict[str, dict]) -> set[str]:
    names: set[str] = set()
    for doc in docs.values():
        stack = list(doc.get("keywords", []))
        while stack:
            ent = stack.pop()
            if ent.get("kind") != "bloc":
                names.add(ent["name"])
            stack.extend(ent.get("keywords", []))
    return names


def glossary_orphans(
    repo: Path, old: dict[str, dict], new: dict[str, dict]
) -> list[tuple[str, str]]:
    """Glossary commands/keywords that existed before the bump and no longer do."""
    path = repo / GLOSSARY_RELPATH
    if not path.is_file():
        return []
    before = {"command": set(old), "keyword": _keyword_names(old)}
    after = {"command": set(new), "keyword": _keyword_names(new)}
    orphans = []
    for entry in glossary_validator.load(path):
        kind, fr = entry.get("kind"), str(entry.get("fr"))
        if kind in before and fr in before[kind] and fr not in after[kind]:
            orphans.append((fr, kind))
    return sorted(orphans)


def _extractor_notes(old_cmds: dict[str, dict], old_msgs: dict[str, dict]) -> list[str]:
    notes = []
    for label, docs, current in (
        ("catalog", old_cmds, catalog_extractor.EXTRACTOR_VERSION),
        ("messages", old_msgs, messages_extractor.EXTRACTOR_VERSION),
    ):
        versions = {d.get("_generated_from", {}).get("extractor_version") for d in docs.values()}
        if versions - {current}:
            notes.append(
                f"The committed {label} extraction was written by extractor version(s) "
                f"{sorted(map(str, versions))}, the new one by {current}: some differences may "
                "come from the extractor, not from upstream."
            )
    return notes


def _set_version(repo: Path, tag: str) -> Path:
    path = repo / INIT_RELPATH
    text = path.read_text(encoding="utf-8")
    new, count = _VERSION_LINE.subn(f'__version__ = "{tag}.1"', text)
    if count != 1:
        raise BumpError(f"{path}: no single __version__ line")
    path.write_text(new, encoding="utf-8")
    return path


def _set_image(repo: Path, image: str, tag: str) -> Path:
    path = repo / IMAGE_FILE
    path.write_text(
        "# code_aster container image used by scripts/run-fixture.sh and solver-fixtures.yml "
        "(ADR-011).\n"
        f"# Set by `caen upstream bump` for UPSTREAM_VERSION {tag}; pinned by digest.\n"
        f"{image}\n",
        encoding="utf-8",
    )
    return path


def bump(
    repo: Path,
    to: str,
    *,
    dry_run: bool = False,
    image: str | None = None,
    report_path: Path | None = None,
    remote: str = "origin",
    today: dt.date | None = None,
) -> Result:
    """Move the pin to ``to`` (or, with ``dry_run``, only compute the diff)."""
    upstream = repo / "upstream"
    if not (upstream / ".git").exists():
        raise BumpError(f"{upstream}: submodule not checked out (git submodule update --init)")
    if image is not None and "@sha256:" not in image:
        raise BumpError("--image must be pinned by digest (name:tag@sha256:…, ADR-011)")
    old = pinned(repo)
    tag, commit = resolve(remote_tags(upstream, remote), to)
    if commit == old["upstream_commit"] and tag == old["upstream"]:
        raise BumpError(f"upstream/ is already at {tag} ({commit[:9]})")
    if not dry_run and str(_git(upstream, "status", "--porcelain")).strip():
        raise BumpError(f"{upstream}: checkout has local changes")
    fetch(upstream, tag, commit, remote)
    new = {"upstream": tag, "upstream_commit": commit}

    with tempfile.TemporaryDirectory(prefix="caen-bump-") as tmp:
        tree = export(upstream, commit, Path(tmp))
        new_cmds = catalog_extractor.extract(tree)
        new_msgs = messages_extractor.extract(tree)

    old_cmds, old_msgs = committed_commands(repo), committed_messages(repo)
    for family, doc in new_msgs.items():
        messages_extractor.merge_translations(doc, old_msgs.get(family))

    catalog_diff = diff_module.compare_catalog(old_cmds, new_cmds)
    messages_diff = diff_module.compare_messages(old_msgs, new_msgs)
    old_ver = old["upstream"] or "unknown"
    follow_up = [
        f"Rerun `solver-fixtures.yml` and choose the image per ADR-011 (`CONTAINER_IMAGE` "
        f"{'set to `' + image + '`' if image else 'not changed by this bump'}); "
        "`tests/test_fixture_outputs.py` checks each fixture's `upstream_version`.",
        "Re-translate the stale messages (`caen translate messages`), then `caen translate "
        "gettext`.",
        "Revisit the command references listed above against the new catalog.",
        f"Package version restarts at `{tag}.1` (ADR-020).",
    ]
    report = diff_module.Report(
        old=old,
        new=new,
        catalog=catalog_diff,
        messages=messages_diff,
        applied=not dry_run,
        date=(today or dt.date.today()).isoformat(),
        references=references(repo, catalog_diff),
        glossary_orphans=glossary_orphans(repo, old_cmds, new_cmds),
        notes=_extractor_notes(old_cmds, old_msgs),
        follow_up=follow_up,
    )
    markdown = diff_module.render(report)
    written: list[Path] = []
    deleted: list[Path] = []
    if not dry_run:
        _git(upstream, "checkout", "--quiet", "--detach", commit)
        (repo / VERSION_FILE).write_text(f"{tag}\n", encoding="utf-8")
        written.append(repo / VERSION_FILE)
        written += _write_extracts(
            repo, new, new_cmds, new_msgs, catalog_diff, messages_diff, deleted
        )
        index = repo / astest_extractor.INDEX_RELPATH
        astest_extractor.write(repo, index)
        written.append(index)
        written.append(inventory_extractor.write(repo))
        written.append(Path(str(gettext_po.build(repo)["po"])))
        written.append(_set_version(repo, tag))
        if image is not None:
            written.append(_set_image(repo, image, tag))
        report_path = report_path or repo / DIFFS_RELDIR / f"{old_ver}-{tag}.md"
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(markdown, encoding="utf-8")
        written.append(report_path)
    return Result(report, markdown, report_path, written, deleted)


def _write_extracts(
    repo: Path,
    provenance: dict[str, str | None],
    commands: dict[str, dict],
    messages: dict[str, dict],
    catalog_diff: diff_module.CatalogDiff,
    messages_diff: diff_module.MessagesDiff,
    deleted: list[Path],
) -> list[Path]:
    written = []
    cmd_dir, msg_dir = repo / COMMANDS_RELDIR, repo / MESSAGES_RELDIR
    for name, doc in commands.items():
        path = cmd_dir / f"{name}.json"
        path.write_text(
            catalog_extractor.render(catalog_extractor.with_provenance(doc, provenance)),
            encoding="utf-8",
        )
        written.append(path)
    for family, doc in messages.items():
        path = msg_dir / f"{family}{messages_extractor.SUFFIX}"
        path.write_text(
            messages_extractor.render(messages_extractor.with_provenance(doc, provenance)),
            encoding="utf-8",
        )
        written.append(path)
    for path in [cmd_dir / f"{n}.json" for n in catalog_diff.removed] + [
        msg_dir / f"{f}{messages_extractor.SUFFIX}" for f in messages_diff.families_removed
    ]:
        path.unlink()
        deleted.append(path)
    return written
