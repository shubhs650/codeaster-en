# Claude Code cloud Project — setup and autonomous driving

How to run codeaster-en development as a **Claude Code Project** at claude.ai/code. A project is one coordinator conversation that starts parallel cloud *threads* (each a full cloud session on its own branch), and it shares instructions and memory across them.

Facts below are from the Claude Code docs as of Oct 2026 (Projects are a public beta on Pro/Max). Re-check the linked pages if a screen looks different.

---

## Part A — One-time GitHub setup (≈ 20 min)

1. **Create the mirror repo** `code_aster` (public), under your user or a new org (suggested: an `openengtools` org, so OET projects live together).
   - GitHub → **New → Import repository** → source `https://gitlab.com/codeaster/src.git`. Takes 10–30 min.
   - Or create it empty and run the sync workflow once (Part A.3).
2. **Create the overlay repo** `codeaster-en` (public). Unzip the kickoff bundle into it, then:
   - replace `<org>` in `README.md`, `.gitmodules.example`, `docs/*.md`;
   - commit and push to `main`.
   The submodule itself is added by the first agent thread (task 0.3), not by you.
3. **Mirror sync workflow**: in `code_aster`, create a branch `mirror-admin`, add `mirror-repo/.github/workflows/sync-upstream.yml` as `.github/workflows/sync-upstream.yml`, set `mirror-admin` as default branch, set **Settings → Actions → General → Workflow permissions → Read and write**, then **Actions → Sync upstream → Run workflow**.
4. **Install the Claude GitHub App** (https://github.com/apps/claude) on **both** repos. Projects need the App on every repo a thread clones, even if you've used `/web-setup` before.
5. **Branch protection on `codeaster-en/main`** (Settings → Rules → New ruleset): require a PR, require the `ci` status check, block force-push. This is the hard guard behind the "agent may self-merge" policy: nothing lands without green CI.
6. **Create the label** `needs-engineer-review` in `codeaster-en` (Issues → Labels).

Public repos get free GitHub Actions minutes, so CI cost is not an issue here (unlike your private repos on RunsOn).

---

## Part B — Cloud environment (≈ 10 min)

At claude.ai/code, on the new-session screen, open the **environment selector** (first control under the message box) → **New environment**.

| Field | Value |
|---|---|
| **Name** | `codeaster-en` |
| **Network access** | **Custom** · tick **Also include default list of common package managers** · **Allowed domains** (one per line): `code-aster.org`, `www.code-aster.org`, `salome-platform.org`, `www.salome-platform.org`, `discourse.salome-platform.org` |
| **Environment variables** | see block below |
| **Setup script** | paste `scripts/env-setup.sh` |

The default list already covers GitHub, **gitlab.com**, **Docker Hub**, PyPI and npm; the extra domains let threads fetch code_aster docs/PDFs and the AsterStudy dictionary directly instead of you attaching them. (If a host is still refused you'll see `403 host_not_allowed` in the thread — add it here.)

Environment variables (no secrets here — anyone using the environment can read them):

```text
BASH_DEFAULT_TIMEOUT_MS=600000
BASH_MAX_TIMEOUT_MS=1800000
CODEASTER_IMAGE=codeastersolver/codeaster-seq:latest
PYTHONDONTWRITEBYTECODE=1
```

- The timeouts let fixture solver runs and docker pulls finish without being backgrounded.
- If you later add a bulk-translation step that calls the Anthropic API with your own key, add it under **Network secrets** (header `x-api-key`, host `api.anthropic.com`), never as a variable. Not needed at first: threads translate in-session.

What the VM already has: Python 3 + pip/uv/pytest/ruff, Node 22, GCC/cmake, **Docker + compose**, git, gh, jq. Limits: ~4 vCPU, 16 GB RAM, 30 GB disk — fine for the small fixture models, too small to build code_aster from source (we never do).

Caching: the setup script result is snapshotted (if it finishes in ~5 min) and reused for ~7 days. The script caps the docker pull at 3 min; if the image isn't cached, `scripts/session-start.sh` pulls it in the background at session start.

---

## Part C — Repo-side Claude config (already in the bundle)

| File | Purpose |
|---|---|
| `CLAUDE.md` | Repo rules every thread reads |
| `.claude/settings.json` | SessionStart hook + permission rules: allows git/pytest/ruff/docker run; **denies edits under `upstream/` and force-push** |
| `scripts/session-start.sh` | Inits the `upstream/` submodule (shallow), `pip install -e tools[dev]`, starts Docker, pulls the solver image |
| `scripts/run-fixture.sh` | Runs a fixture case in the official container → `output/` |
| `scripts/env-setup.sh` | Copy of the environment setup script, for versioning |

These hooks and permission rules only apply in a project with **one** repository. That's why the project contains only `codeaster-en` and reaches the solver source through the submodule. Don't add the `code_aster` mirror as a second project repo.

---

## Part D — Create the Project (≈ 5 min)

1. claude.ai/code → **Projects** (left sidebar) → **New project**. (If it's missing, the beta hasn't reached your account; join the waitlist and use plain cloud sessions with the same prompts meanwhile.)
2. **Name**: `codeaster-en` · **Goal**: `English-first code_aster overlay ready for ClearFEA integration (PLAN.md "Definition of ready")` · **Context → Add**: the `codeaster-en` repo only.
3. **Create project.** If Claude posts **Setup recommendations**, switch off any extra repos and routines, then **Update setup**.
4. **Project settings → Environment** → cloud environment = `codeaster-en`.
5. **Project settings → Memory → Project instructions** → paste `docs/cloud/PROJECT-INSTRUCTIONS.md`.
6. **Project settings → General**:
   - **Coordinator model**: Opus, effort low (default — fine).
   - **Thread model**: Opus, effort high for Phases 0–2 and 4 (design and judgement work). Switch to Sonnet for bulk mechanical tasks (3.2 message translation, 5.2 doc translation) by saying so in the task. A project burns plan usage fast; on Pro expect to hit limits — Max is the realistic plan for this.
7. Desktop app only: project sidebar menu → **Notifications** → on, so you hear about blocked threads.

---

## Part E — Kick-off prompts (send in the project conversation)

### E1 — First message (calibration run, one thread)

```
Read docs/cloud/PROJECT-INSTRUCTIONS.md, CLAUDE.md, docs/PLAN.md and docs/SESSION-PROMPTS.md.

Start ONE thread now for prompt S0 (tasks 0.3 + 0.5) and wait for it to finish before anything else.
The mirror is at https://github.com/<org>/code_aster and already synced.
Also remember these as project memory:
- codeaster-en is an overlay; upstream/ is read-only forever.
- French command/keyword names are never renamed.
- Only the owner (Shubham) marks translations "reviewed".
When S0's PR is open, report: chosen upstream tag and why, CI result, anything surprising.
```

Open the thread when it finishes and check the branch, PR and how it reported. Fix anything it got wrong in project instructions, and tell Claude to remember the correction.

### E2 — Unlock autonomous mode (after S0 merged)

> Superseded on 2026-10-29 by full autodrive (ADR-010): one thread at a time, self-merge on green CI, no stops at ADRs or phase ends. See `docs/cloud/PROJECT-INSTRUCTIONS.md`.

```
S0 looks right. From now on run the plan autonomously:
- Follow the merge policy in the project instructions.
- Run at most 2 threads at a time; start the next ready task when one finishes without asking me.
- Order: S1 (0.4) → in parallel 0.6 glossary and 4.1 fixtures → S2 (1.2) and S3 (1.3+1.6) → 1.4, 1.5 →
  4.2 fixture outputs (run them with scripts/run-fixture.sh in-session and commit outputs) → Phase 2 batches.
- Stop and ask me at: any ADR decision (ADR-004 first), the end of each phase, or anything listed under
  "needs the owner's go-ahead".
- Post in this conversation only when a thread finishes, blocks, or needs review.
```

### E3 — Daily check-in (you, any time, from phone)

```
Status: for every open thread give task ID, state, PR link, what it's waiting on.
Then list PRs labelled needs-engineer-review with the 3 claims in each I should check first.
```

### E4 — Review hand-back (after you've reviewed a translation PR)

```
I reviewed PR #<n>. Accepted except: <notes>. Apply my notes in that thread, set status: reviewed with
reviewed_by: Shubham, reviewed_on: <date>, and merge when CI is green. Remember any rule I gave that
applies beyond this PR.
```

### E5 — Course correction

```
Pause new threads. For every open thread list what you asked it to do, what it assumed, and what it
couldn't reach. Don't fix anything yet.
```

---

## Part F — Routines that keep it running

Ask in the project conversation (Claude creates them as routines under the project's **Routines** tab):

```
Create two routines in this project:
1. "Nightly driver", daily at 01:07 IST: read PROGRESS.md and open PRs; if fewer than 2 threads are working
   and a task is ready under the project rules, start it; then post a 5-line status summary here.
2. "Upstream watch", weekly Monday 07:07 IST: check github.com/<org>/code_aster for a new stable tag
   newer than UPSTREAM_VERSION. If found and task 7.1 is implemented, run `caen upstream bump --dry-run`
   and post the diff summary; do not bump without my go-ahead.
```

Routine runs are fully autonomous (no permission prompts) and count against your plan, with a minimum interval of 1 hour. The off-the-hour times (:07) avoid start delays.

---

## Part G — Day-to-day operating rhythm

> Since ADR-010 (2026-10-29) the owner's part is optional: review `docs/OWNER-REVIEW-QUEUE.md` when time allows. Nothing waits on it.

| When | You | The project |
|---|---|---|
| Morning (5 min, phone) | E3 status; answer any **Waiting on you** threads | Overnight threads finished; driver routine posted a summary |
| Evening (30–60 min, laptop) | Review `needs-engineer-review` PRs — glossary terms and the Tier 1 command references are where your pressure-vessel judgement matters; send E4 | Applies notes, merges, starts the next tasks |
| End of phase | Check PLAN "done when"; reply "go to phase N" | Waits at the phase gate |

Your review effort goes mostly into Phase 2 (command meanings), 3.3 (messages that fire), and 5.3 (critical docs). Phases 0, 1, 4, 6 and 7 are mostly self-verifying through tests, fixtures and CI.

---

## Troubleshooting quick list

- **"Couldn't start the session — Claude doesn't have GitHub access"** → the Claude GitHub App isn't installed on that repo (Part A.4).
- **`403 host_not_allowed`** → add the domain under the environment's **Allowed domains**.
- **Setup script failed** → click **Edit setup script**; the script must exit 0.
- **Submodule empty in a thread** → check `/tmp/submodule.log`; usually means the mirror repo isn't reachable or public.
- **Thread hit the usage limit** → it waits and resumes on its own; **Pause** the project if you'd rather keep the next window.
- **Lost work after a sandbox reset** → that's why instructions require pushing every ~30 min.

Docs: Projects https://code.claude.com/docs/en/claude-projects · Cloud environments https://code.claude.com/docs/en/cloud-environments · Cloud sessions https://code.claude.com/docs/en/claude-code-on-the-web · Routines https://code.claude.com/docs/en/routines
