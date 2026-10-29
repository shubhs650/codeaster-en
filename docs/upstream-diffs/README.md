# Upstream diff reports

One report per upstream bump, `<old>-<new>.md`, written by `caen upstream bump --to <tag>` (task 7.1, ADR-023). Each lists the commands, keywords and messages that changed between the extraction committed in `en/` and the new tag, the translated messages marked `stale`, and the English artefacts to revisit.

The two reports committed with task 7.1 come from exercising the tool on real mirror tags; the pin stayed at 17.4.26 (`stable`):

| Report | How it was made |
|---|---|
| [17.4.22-17.4.26.md](17.4.22-17.4.26.md) | Applied bump 17.4.26 → 17.4.22, then applied `--to stable` back to 17.4.26. It is also the catalog and message gap between the fixture image (17.4.22, ADR-011) and the pin. The return trip restored every file except the English of the two messages 17.4.22 lacks, which was restored from git. |
| [17.4.26-17.5.8.md](17.4.26-17.5.8.md) | `--dry-run` to 17.5.8, the latest `stable-updates` tag on 2026-10-29. Not applied: 17.5.8 is not a frozen `stable` state. |

From task 7.2 (ADR-024) new reports normally arrive through `.github/workflows/upstream-bump.yml`: once a month it bumps to `stable` when the mirror's `stable` is newer than the pin and opens a PR from `upstream/bump-<tag>` whose description holds the report and the stale messages (`caen upstream stale`).
