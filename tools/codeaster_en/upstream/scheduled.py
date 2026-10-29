"""Helpers for the monthly scheduled bump (``.github/workflows/upstream-bump.yml``, task 7.2).

The workflow runs, in order (ADR-024):

1. ``caen upstream check --to stable``: is the mirror's ``stable`` newer than the pin? Prints
   ``key=value`` lines for ``$GITHUB_OUTPUT``. Only ``status=newer`` goes on; ``current``
   (nothing to do) and ``older`` (the pin is ahead of ``stable``, e.g. after a manual bump to
   a stable-update) end the run.
2. ``caen upstream bump --to <target>`` (task 7.1), then ``caen validate`` (its failure is
   expected after a bump that changed placeholders, and is reported, not fatal).
3. ``caen upstream pr-body``: the PR description, from the diff report and
   :func:`stale_items` (every message whose English needs redoing, with whether
   ``caen validate`` rejects it).

Nothing here talks to GitHub; the workflow commits, pushes and opens the PR.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from codeaster_en import placeholders
from codeaster_en.extract import messages as messages_extractor
from codeaster_en.upstream import bump as bump_module

# GitHub rejects PR bodies over 65,536 characters; leave room for the header and stale list.
BODY_LIMIT = 65_000
TESTS_LIMIT = 80  # failing tests shown in the PR body
TABLE_LIMIT = 300  # stale rows shown in the PR body; `caen upstream stale` lists them all


@dataclass
class Check:
    current: str | None
    current_commit: str | None
    target: str
    target_commit: str
    status: str  # "newer" | "current" | "older"

    def lines(self) -> list[str]:
        return [
            f"status={self.status}",
            f"current={self.current or ''}",
            f"current_commit={self.current_commit or ''}",
            f"target={self.target}",
            f"target_commit={self.target_commit}",
        ]


def check(repo: Path, to: str = "stable", remote: str = "origin") -> Check:
    """Compare the pin with ``to`` resolved against the mirror (only ``git ls-remote``)."""
    upstream = repo / "upstream"
    if not (upstream / ".git").exists():
        raise bump_module.BumpError(f"{upstream}: submodule not checked out")
    old = bump_module.pinned(repo)
    tag, commit = bump_module.resolve(bump_module.remote_tags(upstream, remote), to)
    current = old["upstream"]
    if commit == old["upstream_commit"] or tag == current:
        status = "current"
    elif (
        current
        and bump_module.VERSION_TAG.fullmatch(current)
        and bump_module._version_key(tag) < bump_module._version_key(current)
    ):
        status = "older"
    else:
        status = "newer"
    return Check(current, old["upstream_commit"], tag, commit, status)


@dataclass
class StaleMessage:
    id: str
    method: str | None
    placeholders_ok: bool


@dataclass
class StaleItems:
    stale: list[StaleMessage] = field(default_factory=list)
    untranslated: list[str] = field(default_factory=list)

    @property
    def failing(self) -> list[StaleMessage]:
        return [m for m in self.stale if not m.placeholders_ok]


def stale_items(repo: Path) -> StaleItems:
    """Messages to re-translate: ``stale`` English, and messages with no English at all."""
    items = StaleItems()
    directory = repo / bump_module.MESSAGES_RELDIR
    for path in sorted(directory.glob(f"*{messages_extractor.SUFFIX}")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for msg in doc.get("messages", {}).values():
            if msg.get("en") is None:
                items.untranslated.append(msg["id"])
            elif msg.get("stale"):
                ok = not placeholders.compare(msg["fr"], msg["en"])
                items.stale.append(StaleMessage(msg["id"], msg.get("method"), ok))
    return items


def _ids(ids: list[str]) -> str:
    return ", ".join(f"`{i}`" for i in ids) if ids else "none"


def render_stale(items: StaleItems, limit: int | None = TABLE_LIMIT) -> str:
    """Markdown list of the messages to re-translate (``caen translate messages`` input)."""
    out = [
        "## Stale items to re-translate",
        "",
        f"Messages with `stale` English: **{len(items.stale)}**, of which "
        f"**{len(items.failing)}** have placeholders that no longer match the French "
        "(`caen validate` fails on those until the English is redone).",
        "",
    ]
    if items.stale:
        out += ["| ID | Method of the old English | Placeholders match |", "|---|---|---|"]
        out += [
            f"| `{m.id}` | {m.method or 'unknown'} | {'yes' if m.placeholders_ok else '**no**'} |"
            for m in items.stale[:limit]
        ]
        if limit is not None and len(items.stale) > limit:
            out.append(f"\n*({len(items.stale) - limit} more: `caen upstream stale`.)*")
        out.append("")
    out += [
        f"Messages with no English yet ({len(items.untranslated)}): {_ids(items.untranslated)}.",
        "",
        "Command references to revisit are listed in the diff report below "
        "(*English artefacts to revisit*).",
        "",
    ]
    return "\n".join(out)


def _tests_section(ok: bool, log: str) -> str:
    """``pytest`` outcome on the bumped tree: the summary line and each failing test."""
    lines = log.strip().splitlines()
    failing = [ln for ln in lines if ln.startswith(("FAILED ", "ERROR "))]
    summary = lines[-1] if lines else "no output"
    if ok:
        return f"`pytest` passes on the bumped tree ({summary.strip('= ')})."
    out = [f"`pytest` on the bumped tree: {summary.strip('= ')}.", "", "```text"]
    out += failing[:TESTS_LIMIT]
    if len(failing) > TESTS_LIMIT:
        out.append(f"... {len(failing) - TESTS_LIMIT} more")
    out.append("```")
    return "\n".join(out)


def pr_body(
    result: Check,
    report_md: str,
    items: StaleItems,
    *,
    validate_ok: bool,
    validate_log: str = "",
    report_path: str = "",
    run_url: str = "",
    dry_run: bool = False,
    tests_ok: bool | None = None,
    tests_log: str = "",
) -> str:
    """Description of the scheduled bump PR: what to do next, stale items, then the report.

    With ``dry_run`` (the workflow's run summary) ``en/`` was not rewritten, so the stale list
    is replaced by a pointer to the report's own list.
    """
    ran = f" by [this run]({run_url})" if run_url else ""
    if dry_run:
        ran += " — **dry run**, nothing was pushed"
    validate = (
        "`caen validate` passes on the bumped tree."
        if validate_ok
        else "`caen validate` **fails** on the bumped tree (expected when placeholders changed):"
    )
    out = [
        f"Scheduled upstream bump {result.current} → **{result.target}** "
        f"(commit `{result.target_commit[:9]}`), opened{ran} (task 7.2, ADR-024). "
        "The tree is exactly what `caen upstream bump` left; nothing was re-translated.",
        "",
        "## Before merging",
        "",
        "- [ ] Merge the `fixtures: regenerate solver outputs` PR(s) that the solver-fixtures "
        "run on this branch opens (`tests/test_fixture_outputs.py` checks `upstream_version`). "
        "Choose a newer `CONTAINER_IMAGE` first if one exists for the new tag (ADR-011).",
        "- [ ] Re-translate the stale messages below (`caen translate messages`), then "
        "`caen translate gettext`.",
        "- [ ] Revisit the command references listed in the report.",
        "- [ ] Fix the tests that pin upstream counts or versions (listed below): regenerate "
        "the goldens and drafts they name, update the counts from the report.",
        "- [ ] `ruff check`, `ruff format --check`, `pytest`, `caen validate` green; PROGRESS "
        "entry added.",
        "",
        validate,
        "",
    ]
    if not validate_ok and validate_log.strip():
        tail = "\n".join(validate_log.strip().splitlines()[-40:])
        out += ["```text", tail, "```", ""]
    if tests_ok is not None:
        out += [_tests_section(tests_ok, tests_log), ""]
    if dry_run:
        out += [
            "## Stale items to re-translate",
            "",
            "Dry run: `en/` was not rewritten, so the stale messages are the ones the report "
            "lists under *Messages whose French changed*.",
            "",
        ]
    else:
        out.append(render_stale(items))
    head = "\n".join(out)
    room = BODY_LIMIT - len(head) - 200
    if len(report_md) > room:
        where = f" Full report: `{report_path}` on this branch." if report_path else ""
        report_md = report_md[:room].rsplit("\n", 1)[0] + f"\n\n*(Report truncated.{where})*\n"
    return f"{head}\n---\n\n{report_md}"
