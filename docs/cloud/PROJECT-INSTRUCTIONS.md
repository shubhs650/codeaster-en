This project builds **codeaster-en**: an English overlay for the code_aster FE solver (glossary, English command references, English message catalogue, translated U4 docs, and a Python package that parses solver logs/results and writes English engineering reports). It is the code_aster foundation for the ClearFEA platform.

Repositories
- Work happens in `codeaster-en` only. The solver source is the `upstream/` git submodule (a mirror of gitlab.com/codeaster/src). Never edit, commit to, or push anything under `upstream/`.
- Every repo rule is in `CLAUDE.md`. Read it first in every thread. Plan: `docs/PLAN.md`. State: `docs/PROGRESS.md`. Decisions: `docs/DECISIONS.md`.

How to pick work
- Work is defined by task IDs in `docs/PLAN.md` (e.g. 1.2, 2.3b). One thread = one task ID (or the bundle named in docs/SESSION-PROMPTS.md). Use that file's prompt for the task when one exists.
- A task is ready when every task it depends on is merged to `main` and it is not marked done in PROGRESS.md.
- Run at most 2 threads at once. Never run two threads that edit the same files (e.g. two threads both touching `en/glossary.yaml` — serialise those).

How a thread works
- Branch from latest `main`: `task/<id>-<slug>`. Commit and push work in progress at least every ~30 minutes (sandboxes can be reset).
- Conventional Commits, DCO sign-off (`git commit -s`).
- Before calling work done: `ruff check`, `ruff format --check`, `pytest`, and `caen validate` (once it exists) must pass. Paste the summary lines in the final message.
- Solver runs: use `scripts/run-fixture.sh <case>` (Docker, official image). Do not build code_aster from source. Keep any single run under 25 minutes.
- Append one entry to `docs/PROGRESS.md` (newest first) in the same PR.
- Open one PR per task, titled `<id>: <title>`, body = what changed / how verified / what the owner must check by hand.

Merging (autonomy policy)
- You may merge your own PR (squash) when ALL hold: CI is green, the PR does not carry the `needs-engineer-review` label, it does not change `CLAUDE.md`, `docs/DECISIONS.md` status fields, licence files, or `.github/workflows/`, and it does not mark any translation `status: reviewed`.
- Otherwise add the `needs-engineer-review` label, leave the PR open, and post a 3-line summary in the project conversation.
- Translations of commands/docs and any change to the meaning of a glossary term always get `needs-engineer-review`. Only the owner sets `status: reviewed`.

When something is missing
- If you need a file (PDF, AsterStudy dictionary, a credential), a decision, or access you don't have: say exactly what is missing in your first message and stop. Don't mock, substitute, or guess solver behaviour.
- If upstream's layout differs from what CLAUDE.md §6 says, record findings in PROGRESS and ask before adapting.

Needs the owner's go-ahead first
- Any change under `upstream/`, to the submodule pin outside task 7.1, to CI workflows, to licences, or to ADR status.
- Starting a phase whose previous phase's "done when" is not met.
- Bulk LLM translation runs that call an external API (state token estimate first).

Reporting in the project conversation
- Post only when a thread finishes, is blocked, or opens a PR needing review. Keep it to: task ID, outcome, PR link, next task you intend to start.
