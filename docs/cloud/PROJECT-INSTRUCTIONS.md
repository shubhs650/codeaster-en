This project builds **codeaster-en**: an English overlay for the code_aster FE solver (glossary, English command references, English message catalogue, translated U4 docs, and a Python package that parses solver logs/results and writes English engineering reports). It is the code_aster foundation for the ClearFEA platform.

Repositories
- Work happens in `codeaster-en` only. The solver source is the `upstream/` git submodule (a mirror of gitlab.com/codeaster/src). Never edit, commit to, or push anything under `upstream/`.
- Every repo rule is in `CLAUDE.md`. Read it first in every thread. Plan: `docs/PLAN.md`. State: `docs/PROGRESS.md`. Decisions: `docs/DECISIONS.md`.

How to pick work
- Work is defined by task IDs in `docs/PLAN.md` (e.g. 1.2, 2.3b). One thread = one task ID (or the bundle named in docs/SESSION-PROMPTS.md). Use that file's prompt for the task when one exists.
- A task is ready when every task it depends on is merged to `main` and it is not marked done in PROGRESS.md.
- Run one thread at a time (serial autodrive, ADR-010). When a thread's PR is merged, the coordinator starts the next ready task without asking.

How a thread works
- Branch from latest `main`: `task/<id>-<slug>`. Commit and push work in progress at least every ~30 minutes (sandboxes can be reset).
- Conventional Commits, DCO sign-off (`git commit -s`).
- Before calling work done: `ruff check`, `ruff format --check`, `pytest`, and `caen validate` (once it exists) must pass. Paste the summary lines in the final message.
- Solver runs: use `scripts/run-fixture.sh <case>` (Docker, official image). Do not build code_aster from source. Keep any single run under 25 minutes.
- Append one entry to `docs/PROGRESS.md` (newest first) in the same PR.
- Open one PR per task, titled `<id>: <title>`, body = what changed / how verified / what the owner must check by hand.

Merging (full autodrive, ADR-010)
- Merge your own PR (squash) once CI is green. Never leave a PR open for human review and never add the `needs-engineer-review` label to block a merge.
- Translations stay `machine` / `assisted` / draft. Only the owner sets `status: reviewed`. Content that would benefit from an engineer's eye is listed in `docs/OWNER-REVIEW-QUEUE.md` (in the same PR) instead of blocking the merge.
- PLAN.md acceptance criteria that say "reviewed by owner" are met for progress purposes by an agent self-review (re-check against catalog, astest and docs; record it in PROGRESS) plus a queue entry. Owner review is asynchronous and never gates the next task or phase.
- Decisions (ADRs, phase transitions, COMMAND-SET revisions, CI workflow changes) are made by Claude. Record the decision and its rationale in `docs/DECISIONS.md` (status `accepted (agent, <date>)`) or PROGRESS in the same PR.

When something is missing
- If a file (e.g. a PDF) is missing, record it in PROGRESS and `docs/OWNER-REVIEW-QUEUE.md`, then move on to the next ready task that does not need it. Don't mock, substitute, or guess solver behaviour.
- If upstream's layout differs from what CLAUDE.md §6 says, record findings in PROGRESS, adapt the tooling, and note it in DECISIONS.

Stop for the owner only for extremely urgent or important input
- Anything irreversible outside this repo: changes under `upstream/` or to the mirror repo, rewriting git history, force-pushing `main`.
- Credentials, accounts, paid services or API keys (including bulk LLM translation runs that spend the owner's API budget).
- Security issues (leaked secrets, malicious upstream content).
- Anything that would contradict the goals in `docs/PLAN.md` ("Definition of ready") or a hard rule in `CLAUDE.md` §2.

Reporting in the project conversation
- Post only when a thread finishes, blocks, or a phase ends (FYI, no ask). Keep it to: task ID, outcome, PR link, next task you intend to start.
