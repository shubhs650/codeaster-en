# Plan — codeaster-en

Phases are sequential; tasks inside a phase can usually run in parallel across sessions unless marked `after:`. Every task has an acceptance criterion an agent can check. Task IDs are stable; reference them in PROGRESS and PRs.

**Autodrive (ADR-010, 2026-10-29).** Tasks run serially and the agent merges its own PRs. Where an acceptance criterion says "reviewed by owner", "owner sign-off" or `reviewed`, the agent meets it for progress purposes with a recorded self-review and an entry in `docs/OWNER-REVIEW-QUEUE.md`; the artefact keeps status `assisted` until the owner reviews it. Tasks owned by "Owner" (attaching files) are skipped and queued, not waited on. Phase gates are checked and passed by the agent.

Scope of translation is set by `docs/COMMAND-SET.md`: **Tier 1** (alpha: linear static, solids + shells) first, **Tier 2** (modal + extra loads) second, **Tier 3** (nonlinear, contact, thermal) only when ClearFEA pulls for it.

---

## Phase 0 — Bootstrap (owner + 1–2 agent sessions)

**Goal:** both repos exist, upstream is pinned, tooling skeleton runs, docs are in place.

| ID | Task | Owner | Acceptance |
|---|---|---|---|
| 0.1 | Create GitHub repo `code_aster` (public). Initial import from `https://gitlab.com/codeaster/src.git` via GitHub "Import repository" (or run `sync-upstream.yml` once with `workflow_dispatch`). | Owner | Repo has `main` and upstream tags; largest blob < 100 MB (or LFS/`main`-only decision recorded in DECISIONS). |
| 0.2 | Add `.github/workflows/sync-upstream.yml` (from `mirror-repo/`) to the mirror repo. Trigger it manually once. | Owner | Workflow run green; `main` matches GitLab HEAD. |
| 0.3 | Create GitHub repo `codeaster-en`; commit this doc set; add `upstream/` submodule pointing at the latest **stable** tag of the mirror; write `UPSTREAM_VERSION`. | Agent | `git submodule status` shows the tag; `UPSTREAM_VERSION` matches. |
| 0.4 | **Verify upstream anatomy.** Confirm the paths in `CLAUDE.md` §6 and `ARCHITECTURE.md` §3: command catalogs location and DSL, `Messages/` format, whether `code_aster.Cata` imports without a built solver, presence of gettext/localisation, `.mess` format (grab one from `astest` expected outputs if present). Correct both docs. Count commands, keywords, message families, messages, test cases. | Agent | Numbers and corrected paths recorded in PROGRESS; docs updated; findings in DECISIONS if they change the approach. |
| 0.5 | Tooling skeleton: `tools/pyproject.toml` (package `codeaster_en`, CLI `caen` via `typer`), `ruff`, `pytest`, `ci.yml`. `caen --help` lists stub subcommands `extract`, `translate`, `validate`, `mess`, `report`, `upstream`. | Agent | CI green on PR; `pip install -e tools[dev]` works in a clean venv. |
| 0.6 | Seed `en/glossary.yaml`: merge the committed seed with AsterStudy's `GLOBAL_DICT` (owner attaches the file) and all identifiers appearing in `docs/COMMAND-SET.md`. Mark everything `proposed`. | Agent | ≥ 150 entries; `caen validate glossary` passes (unique `fr`, non-empty `en`, valid `kind`). |

**Phase 0 done when:** a fresh clone with submodules, `pip install -e tools[dev]`, `pytest`, `caen validate` all succeed in the Claude Code cloud sandbox.

---

## Phase 1 — Extraction & inventory (agent, 3–5 sessions)

**Goal:** machine-readable, provenance-stamped English-ready data for everything in scope. No prose yet.

| ID | Task | Acceptance |
|---|---|---|
| 1.1 | **Decide message strategy.** Investigate gettext in upstream (`_()` wrappers, a `localization` module, existing `.po` files, locale handling in the supervisor). Write ADR: *runtime mapping only* vs *`.po` catalog + runtime fallback*. | `docs/DECISIONS.md` ADR-004 written with evidence (file paths, snippets). |
| 1.2 | `caen extract catalog`: walk `code_aster/Cata/Commands/`, emit `en/commands/<CMD>.json` for **all** commands (cheap, and the diff tool needs all). Schema documented in `docs/schemas/command.schema.json`. Include `fr=` strings, source file:line, upstream tag. | All commands extracted without error; JSON validates against schema; snapshot test on 3 commands. |
| 1.3 | `caen extract messages`: parse every `code_aster/Messages/<family>.py` into `en/messages/<FAMILY>.en.json` with `en: null`. Record placeholder sets per message. | All families extracted; count matches 0.4; placeholder extraction tested on tricky formats (`%(r1)12.5E`, `%%`, multiline). |
| 1.4 | `caen extract astest-index`: for every `astest/*.comm`, list commands used (via the catalog's own parser if importable, else a robust regex) → `en/astest-index.json` (command → [testcases], testcase → [commands], plus `.export` metadata: time/memory, parallel). | Index built; spot-check 5 known cases (e.g. `ssls` shells, `sdll` modal) by hand. |
| 1.5 | Inventory report `docs/INVENTORY.md`: counts, Tier 1/2 coverage (which commands/families exist, how many keywords, how many messages reference Tier-1 commands by family name heuristics), top-50 most-used commands across astest. | Doc committed; informs COMMAND-SET revision. |
| 1.6 | `caen validate`: glossary rules; placeholder equality `fr`↔`en` when `en` present; forbidden synonyms scan over `en/**/*.md`; command `.md` keywords ⊆ `.json` keywords. | Validator has tests; wired into CI. |

---

## Phase 2 — Glossary + Tier 1 command references (agent + engineer review, 6–10 sessions)

**Goal:** every Tier 1 command has a reviewed English reference an LLM can rely on.

| ID | Task | Acceptance |
|---|---|---|
| 2.1 | Glossary pass 1: translate/define every `proposed` entry from catalog `fr=` strings and context; add `note` where the French abbreviation is opaque (`MA`, `NO`, `CARA`, `SIEF`, `EFGE`, `ELGA`). | 100% entries have `en` + `note` where kind ≠ `value`; status `machine`. |
| 2.2 | `caen translate command <CMD>`: generates a first-draft `.md` from the `.json` (keyword table pre-filled, English column from glossary + LLM, examples auto-linked from astest-index, doc ID linked if known). Template in `tools/codeaster_en/translate/templates/command.md.j2`. | Drafts for all Tier 1 commands generated in one run; validator passes. |
| 2.3 | Author Tier 1 references, batched by theme: (a) `LIRE_MAILLAGE`, `MODI_MAILLAGE`, `DEFI_GROUP`, `CREA_MAILLAGE`; (b) `AFFE_MODELE`, `DEFI_MATERIAU`, `AFFE_MATERIAU`, `AFFE_CARA_ELEM`; (c) `AFFE_CHAR_MECA`, `AFFE_CHAR_CINE`, `DEFI_FONCTION`; (d) `MECA_STATIQUE`, `CALC_CHAMP`, `POST_RELEVE_T`, `POST_ELEM`, `CREA_CHAMP`, `IMPR_RESU`, `IMPR_TABLE`, `DEBUT`/`FIN`, `TEST_RESU`. Each batch = one session. For each command: purpose, keyword table with "when to use", 2 patterns, pitfalls, examples. | Every Tier 1 `.md` exists, status `assisted`, validator green, and the owner has reviewed `AFFE_MODELE`, `AFFE_CARA_ELEM`, `AFFE_CHAR_MECA`, `CALC_CHAMP` (the four with the most engineering judgement) → `reviewed`. |
| 2.4 | Modelisation & element note `en/guide/modelisations.md`: what `3D`, `3D_SI`, `DKT`, `DST`, `COQUE_3D`, `AXIS`, `C_PLAN`, `D_PLAN`, `POU_D_T` mean and when ClearFEA should pick each. | Reviewed by owner. |
| 2.5 | Field & component glossary `en/guide/fields.md`: result objects (`EVOL_ELAS`, `MODE_MECA`), field names (`DEPL`, `SIGM_*`, `SIEQ_*`, `EPSI_*`, `REAC_NODA`, `FORC_NODA`, `EFGE_*`), locations (`NOEU`, `ELNO`, `ELGA`), components. This drives report labels. | Reviewed by owner; glossary entries added. |

---

## Phase 3 — Messages (agent, 3–6 sessions + spot review)

| ID | Task | Acceptance |
|---|---|---|
| 3.1 | `caen translate messages --family <F>`: batched LLM translation, glossary injected into the prompt, placeholders validated, severity hint inferred from French wording (`ALARME`, `ERREUR`, `fatale`). Dry-run mode prints cost estimate (tokens). Resumable; writes `method: machine`. | Translates one family end-to-end with 100% placeholder validation. |
| 3.2 | Translate all families (bulk run, owner's API key via env var, or in-session for small families). | `en` non-null for every message; validator green; PROGRESS lists families and token cost. |
| 3.3 | Engineer review of the families that actually fire in the fixture runs (see 4.x) plus `MODELISA`, `CALCULEL`, `MECASTATIQUE`/`MECANONLINE`, `ALGELINE`, `FACTOR`, `POSTRELE`, `UTILITAI` — whichever exist. Fix wording; mark `reviewed`. | Those families `reviewed`; reviewer + date set. |
| 3.4 | If ADR-004 chose gettext: emit `en/messages/codeaster_en.po`, compile check with `msgfmt`, document how to install the `.mo` into a container and set the locale. | `.po` compiles; `solver-fixtures.yml` has an optional job that runs one fixture with the English locale and commits the English `.mess`. |

---

## Phase 4 — Runtime layer: log, results, report (agent, 6–10 sessions)

**Goal:** given a run directory, produce an English engineering report. This is the first thing ClearFEA imports.

| ID | Task | Acceptance |
|---|---|---|
| 4.1 | Fixture cases: write `solid_static`, `shell_static`, `modal` `.comm`/`.export`/mesh (mesh via Gmsh script committed alongside; `.med` committed). Include `TEST_RESU` against hand values. | Files committed under `tests/fixtures/<case>/input/`. |
| 4.2 | Run each fixture in-session with `scripts/run-fixture.sh` and commit `output/`. Then add `solver-fixtures.yml` so CI can regenerate them: GitHub Action pulls the image pinned in `CONTAINER_IMAGE` (ADR-011; no image matches 17.4.26), runs each fixture with `run_aster`, commits `output/` (`.mess`, `.rmed`, tables, exit code). Manual + on `UPSTREAM_VERSION` change. | Action green; outputs committed; `TEST_RESU` all OK. |
| 4.3 | `mess` parser: events model (`Stage`, `Diagnostic`, `Table`, `Summary`), parser tested on all fixture logs plus 3 deliberately broken runs (missing group, singular matrix, bad keyword) added to fixtures. | 100% of lines classified; unknown-line fallback never loses text. |
| 4.4 | `mess` English renderer: joins to `en/messages/`; argument recovery; `untranslated` flag; `caen mess translate run.mess` CLI → `.en.mess` and `.json`. | All diagnostics in fixtures render in English; broken runs give English, actionable errors. |
| 4.5 | `results` readers: native `h5py` MED reader (ADR-015; was `medcoupling` first, `meshio` fallback); list results/fields; per-group min/max with node/element ID and coordinates; reaction sums; modal table (frequency, mass participation if `POST_ELEM MASS_INER`/`CALC_MODES` outputs allow). | Tested on all three fixtures. |
| 4.6 | `report` generator per `docs/REPORT-SPEC.md`: Markdown → HTML (Jinja2) → PDF (WeasyPrint). Sections switchable; title block + logo slot; English only; every number traceable to a field or table. | `caen report tests/fixtures/solid_static` produces `.md`, `.html`, `.pdf`; golden-file test on `.md`. |
| 4.7 | Optional images: pyvista off-screen screenshots of deformed shape + von Mises for the report (feature-flagged; CI may lack GL). | Works locally; CI skips gracefully. |

---

## Phase 5 — Documentation (agent + owner for PDFs, 4–8 sessions)

| ID | Task | Acceptance |
|---|---|---|
| 5.1 | Owner attaches the French U4 PDFs for Tier 1 commands (and U1.03.01 command-file syntax, U4.81.01 `IMPR_RESU` MED notes). *(2026-10-30, ADR-026: code-aster.org became reachable, so `caen docs fetch` downloads them; U4.81.01 does not exist, the MED notes are U7.05.21.)* `caen docs ingest <pdf>` → text with structure preserved (`pdfplumber`/`pymupdf`), chunked, cached under `en/docs/_src/` (git-ignored if licence requires). | Text extraction reviewed for one doc; tables survive. |
| 5.2 | `caen translate doc <DOC-ID>`: chunked LLM translation with glossary + the command's `.json` as context; re-assembly; header with provenance. | Tier 1 U4 docs translated, status `machine`. |
| 5.3 | Engineer skim-review of the four critical docs (same four as 2.3). | `reviewed`. |
| 5.4 | `en/guide/` — "code_aster for structural engineers": concepts, three walkthroughs (built from the fixture cases), reading logs, reading results, FAQ of alarms seen in fixtures. | Owner can hand it to a colleague who completes `solid_static` unaided. |
| 5.5 | LLM context bundle: `caen bundle --tier 1` → one Markdown file (glossary + Tier 1 references + guide) sized for a coding-agent context window; published as a release asset. | Bundle < ~150k tokens; used in a trial Claude Code session to write a new `.comm` that runs green in the fixtures Action. |

---

## Phase 6 — ClearFEA readiness (agent, 4–6 sessions)

| ID | Task | Acceptance |
|---|---|---|
| 6.1 | `comm` builder: typed English API emitting French `.comm`, validated against catalog JSON; covers Tier 1 (+ Tier 2 modal). Round-trip tests; emitted `.comm` for the three fixtures is byte-identical (modulo comments) to the hand-written ones. | Tests green; fixtures regenerate from the builder. |
| 6.2 | Package: `codeaster-en` on PyPI (or GitHub release wheel), `en/` shipped as package data, lazy-loaded. Version = `<overlay>.<upstream tag>` scheme decided in DECISIONS. | `pip install codeaster-en` in a clean venv; `from codeaster_en import report`. |
| 6.3 | Adapter spec `docs/CLEARFEA-INTEGRATION.md` finalised with concrete function signatures, container image contract, job directory layout, error taxonomy mapping (user fault vs platform fault for billing), and a worked example of ClearFEA's `solver=code_aster` path. | Owner sign-off. |
| 6.4 | Tier 2 sweep: modal (`CALC_MODES`, `NORM_MODE`, `ASSEMBLAGE`, `POST_ELEM MASS_INER`) + extra loads (remote force/moment via `LIAISON_RBE3`/`LIAISON_SOLIDE`, hydrostatic via `DEFI_FONCTION`+`PRES_REP`, centrifugal `ROTATION`, springs `DISCRET`) through Phases 2–5 steps. | Tier 2 commands `assisted`+, fixtures extended, report covers modal. |

---

## Phase 7 — Maintenance loop (recurring)

| ID | Task | Acceptance |
|---|---|---|
| 7.1 | `caen upstream bump --to <tag>`: submodule bump, re-extract, diff report (`docs/upstream-diffs/<old>-<new>.md`): new/removed/changed commands, keywords, messages; mark changed messages `stale`. | Runs unattended; report readable. |
| 7.2 | Scheduled task (monthly): run 7.1 against latest stable, open PR with the diff and a list of stale items to re-translate. | PR opened automatically. |

---

## Sequencing summary

```
P0 bootstrap ─▶ P1 extract ─▶ P2 commands ─┬▶ P3 messages ─┐
                                           │               ├▶ P4 runtime/report ─▶ P6 ClearFEA
                                           └▶ P5 docs ─────┘        ▲
                                                                     └── fixtures (4.1/4.2) can start right after P0
```

Start fixtures (4.1, 4.2) early: they are the only way to see real `.mess` output and they de-risk the docker/Action path before anything depends on it.

## Definition of "semi-translated repo ready for ClearFEA"

- Tier 1 + Tier 2 commands: `.json` generated, `.md` at least `assisted`, the critical four `reviewed`.
- All messages `machine`, fixture-firing families `reviewed`.
- Three fixtures with committed outputs, Action green against pinned upstream.
- `caen report` produces an English PDF from any of them with zero French strings (CI greps the output for the top-200 French words as a tripwire).
- `pip install codeaster-en` works; the integration doc has signatures ClearFEA can code against.
- `caen upstream bump` has been exercised once on a real newer tag.
