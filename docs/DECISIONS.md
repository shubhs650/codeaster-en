# Decisions (ADR log)

Format: ID, date, status, decision, why, consequences. Append; never rewrite history — supersede with a new entry.

---

## ADR-001 — Overlay, not fork; no source translation
**Date:** 2026-10-22 · **Status:** accepted

**Decision.** code_aster source is consumed read-only as a pinned submodule. English material is a sidecar keyed by stable upstream identifiers (command names, keyword paths, message family+number, doc IDs). No identifier is ever renamed.

**Why.** ~1.5 M lines, continuous upstream change, French keywords are the public API that every test case, doc and forum answer depends on. A translated fork cannot merge upstream and loses the validation corpus — the reason to choose code_aster.

**Consequences.** Upstream bumps are a submodule pointer change plus a mechanical diff. Agents must never write under `upstream/`. LLM-friendliness comes from English *explanations* and a glossary, not English identifiers.

---

## ADR-002 — Two repos: `code_aster` (mirror) + `codeaster-en` (overlay)
**Date:** 2026-10-22 · **Status:** accepted

**Decision.** `github.com/<org>/code_aster` is a plain, action-synchronised mirror of `gitlab.com/codeaster/src` (never edited). `codeaster-en` references it as a submodule pinned to a stable tag.

**Why.** Keeps the overlay small and conflict-free; the Claude Code cloud sandbox can reach GitHub but not GitLab; fulfils "copy the GitLab repo to GitHub" as a reusable public artefact.

**Consequences.** Need the sync workflow and an initial import; blob-size check before first push; two repos to administer.

---

## ADR-003 — Scope is driven by `docs/COMMAND-SET.md` tiers
**Date:** 2026-10-22 · **Status:** accepted

**Decision.** Only commands/messages/docs in the active tier get English prose. Catalog and message *extraction* runs over everything (cheap, needed for diffs).

**Why.** Thousands of keywords and ~10k messages exist; most are irrelevant to a structural platform. Translating only what is used keeps review feasible and quality high.

**Consequences.** Users of exotic commands get French; the runtime renderer shows the ID and original text rather than hiding it.

---

## ADR-004 — Message strategy: gettext catalog vs runtime mapping
**Date:** 2026-10-23 · **Status:** accepted (owner, 2026-10-23: hybrid — generated `.mo` + runtime fallback)

**Options.** (a) Runtime only: parse `.mess`, map `FAMILY_N` → English. Works with any image, no solver change. (b) If upstream wraps messages in gettext and honours a locale, ship an English `.po/.mo`; solver prints English natively; runtime renderer remains for IDs/classification and as fallback.

**Evidence (upstream 17.4.26; counts in `docs/INVENTORY.md`).**
1. *gettext is wired in.* Every message is `_("""…""")` with `_` = `code_aster.Utilities.i18n.translate` → `gettext.translation("aster_messages", localedir, languages=[...], fallback=True)`. `localedir` = `$ASTER_LOCALEDIR` (exported by `data/profile.sh.tmpl`) or `$ASTER_ROOT/share/locale`. Fortran `utmess` → `utprin` (`bibc/supervis/aster_core_module.c`) → the same Python `MessageLog`, so one path covers all 6,890 messages.
2. *The switch is a `.comm` keyword, not the environment.* Only `DEBUT(LANG='EN')` calls `localization.translation()` (`code_aster/CodeCommands/debut.py:229`). `LANG` is an existing catalog keyword (`TXM`); using it renames nothing (CLAUDE.md rule 2). Our builder emits the `.comm` (ADR-008), so it can always add it.
3. *Translation happens at module import.* `_()` is evaluated when a family module is first imported (`Utmess.load_cata_msg` → `__import__`, cached). Families used before `LANG` is processed stay French: at least `SUPERVIS` (`SUPERVIS_12`/`_22` are emitted in `DEBUT` before line 229) and `Utmess.contacter_assistance`. The box footers ("Ceci est une alarme…") are translated at call time and do switch.
4. *Gaps gettext cannot close:* 15 messages are not wrapped in `_()`; `POST0_55`/`POST0_56` are f-strings (xgettext cannot extract them); messages printed before `DEBUT`.
5. *No `.mo` by default.* `i18n/wscript` compiles `.po` → `.mo` only when configured with `--enable-i18n` (default off). `astest/supv003a.comm` runs `DEBUT(LANG="EN")` and passes whether or not `$ASTER_LOCALEDIR/en-US/LC_MESSAGES/aster_messages.mo` exists. Verified in task 4.2 with the fixture image (ADR-011): the image ships **no** `.mo` (no `share/locale` at all), and `share/aster/profile.sh` sets `ASTER_LOCALEDIR=${RUNASTER_ROOT}/share/locale/aster` unconditionally, so a `docker run -e ASTER_LOCALEDIR=...` is overridden and has no effect. What works: mount the directory holding `en/LC_MESSAGES/aster_messages.mo` **at** `<install>/share/locale/aster` and run with `DEBUT(LANG='EN')`. A probe `.mo` with one entry for `MODELISA8_14` turned that Fortran-emitted alarm into English in `run.mess` (`shell_static` without `IGNORE_ALARM`); without the mount it stayed French, and the banner line "Langue des messages : en" stays French either way (not a catalog message). The upstream 2016 `.po` compiled as is has no entry for that message, so it changed nothing in the fixture logs. The `LANG='EN'` fixture variant is therefore deferred to task 3.4, when our own `.mo` exists.
6. *Upstream English exists but is weak.* `i18n/en-US/aster_messages.po`: 2016, v13, one Crowdin translator; 3,308 of 6,890 current messages (48 %) reusable verbatim, 1 with a placeholder mismatch; literal quality and glossary conflicts (*maille* → "mesh"). `catapy_en_US.ts`: 1,033 finished translations matching current `fr=` strings.
7. *Runtime mapping has a blind spot.* Plain informational messages (type `I` without `DECORATED`) are printed with no `<FAMILY_N>` ID (`Utmess.format_message`), so option (a) alone must reverse-match their text against French templates.

**Decision.** Both, with one source of truth:
- `en/messages/<FAMILY>.en.json` stays the only place English message text is edited. Seed it from the upstream `.po` where the French matches exactly, as `method: machine` with provenance `upstream:i18n/en-US/aster_messages.po`; never `reviewed` until the owner says so.
- Generate `aster_messages.po` → `.mo` from it as a build artefact (task 3.4), install it at `<localedir>/en/LC_MESSAGES/` in the run image or via `ASTER_LOCALEDIR`, and have the `.comm` builder emit `DEBUT(LANG='EN')`. The solver then prints English for everything gettext reaches.
- Keep the runtime `.mess` renderer (tasks 4.3–4.4) for IDs, classification, and the French that leaks through (point 3, 4, and runs made without our `.mo`). It must handle both French and already-English bodies.
- Gate on task 4.2: one fixture run with `LANG='EN'` + our `.mo` must show English diagnostics before we rely on (b).
- Offer upstream (via `docs/DECISIONS.md`, not by editing `upstream/`): wrap the 15 bare strings, replace the two f-strings, and apply `LANG` before the first `UTMESS` in `DEBUT`.

**Consequences.** Task 1.3 adds a `.po` import step and records `source: upstream-po`; task 1.6 validates generated `.po` placeholders; task 3.4 emits the `.po` and checks it with `msgfmt`; task 4.2 adds a `LANG='EN'` fixture variant. If rejected (runtime only), the `.po` is still worth importing as a machine seed.

---

## ADR-005 — Report is generated from artefacts, never from physics
**Date:** 2026-10-22 · **Status:** accepted

**Decision.** `codeaster_en.report` extracts, labels, sums and formats; it never computes stresses, linearises, or judges compliance. Anything not in the run outputs is absent from the report, with a note saying what to request in the `.comm`.

**Why.** Traceability for an engineering document; ClearFEA's "analysis tool, not a verdict" positioning; keeps the module testable with golden files.

---

## ADR-006 — Translation provenance and status are mandatory fields
**Date:** 2026-10-22 · **Status:** accepted

**Decision.** Every English artefact carries upstream tag, source location, `method` (`machine` / `assisted` / `reviewed`), reviewer, date; stale-on-upstream-change is tracked by the bump tool.

**Why.** Machine translations will be wrong sometimes; users and agents must be able to tell what has been checked by an engineer.

---

## ADR-007 — Licence: GPL-3.0-or-later for the overlay
**Date:** 2026-10-22 · **Status:** accepted (owner to confirm after reading upstream licence headers)

**Decision.** Tools, translations and own docs under GPL-3.0-or-later; translated official docs carry EDF attribution and the original doc ID and are treated as derivative works of EDF's documentation.

**Why.** Message translations are derivative of GPL source; GPL-3.0-or-later is compatible with ClearFEA's AGPL-3.0. See `docs/LICENSING.md`.

---

## ADR-008 — Builder emits `.comm` files, not in-process Python API calls
**Date:** 2026-10-22 · **Status:** accepted for Phase 6, revisit later

**Decision.** `codeaster_en.comm` produces a textual `.comm` run by `run_aster`, even though modern code_aster can be driven in-process from Python.

**Why.** A `.comm` is a downloadable, inspectable, version-stable artefact (ClearFEA's "view/download the solver input" requirement), is what the test corpus is written in, and keeps the worker process isolated from the solver process.

---

## ADR-009 — Salome-Meca / AsterStudy are not vendored or translated
**Date:** 2026-10-22 · **Status:** accepted

**Decision.** Only AsterStudy's translation dictionary is used (as glossary seed, with attribution). Nothing else from Salome is a dependency.

**Why.** ClearFEA has its own UI and meshing; the Salome desktop stack is heavy and unnecessary in a cloud worker.

---

## ADR-010 — Full autodrive: serial tasks, agent self-merge, agent decisions
**Date:** 2026-10-29 · **Status:** accepted (owner, 2026-10-29)

**Decision.** From 2026-10-29 the project runs without the owner in the loop. Tasks from `docs/PLAN.md` run serially, one thread at a time. Each thread merges its own PR (squash) once CI is green; no PR is left open for human review. ADRs, phase transitions, COMMAND-SET revisions and CI changes are decided by the agent, with the rationale recorded here or in PROGRESS. The owner is asked only for extremely urgent or important input: irreversible changes outside the repo (`upstream/`, mirror, `main` history), credentials/accounts/paid API use, security, or anything contradicting PLAN.md goals or CLAUDE.md §2. Supersedes the merge, concurrency and "owner's go-ahead" rules in `docs/cloud/PROJECT-INSTRUCTIONS.md` and the E2 prompt in `docs/cloud/CLOUD-SETUP.md`.

**Why.** The owner (Shubham) is not available to merge PRs or answer gate questions ("I won't be available to manually merge GitHub PR that needs human review… autodrive all development phase by phase, task by task serially. Merge the PR yourself."). Serial execution removes merge conflicts between threads, and green CI plus branch protection stays the hard guard on `main`.

**Consequences.**
- Invariants unchanged: `upstream/` is read-only; French command and keyword names are never renamed; only the owner sets `status: reviewed`. Agent work stays `machine`/`assisted`.
- Owner-review acceptance criteria (2.3 critical four, 2.4, 2.5, 3.3, 5.3, 6.3) are met for progress by a recorded agent self-review plus an entry in `docs/OWNER-REVIEW-QUEUE.md`. The "Definition of ready" items that require `reviewed` remain open until the owner reviews; everything else proceeds.
- Owner-only inputs (e.g. U4 PDFs for 5.1, an API key for 3.2 bulk runs) are queued; the agent does the parts it can (in-session translation) and moves on.
- `needs-engineer-review` label is retired as a merge blocker; existing open PRs carrying it are merged once CI is green.

---

## ADR-011 — Fixture solver image: `simvia/code_aster:17.4.22`, pinned by digest
**Date:** 2026-10-29 · **Status:** accepted (agent, 2026-10-29)

**Context.** Task 4.2 must run the fixtures with a solver matching `UPSTREAM_VERSION` = 17.4.26. The image named in PLAN.md, `codeastersolver/codeaster-seq`, is abandoned: Docker Hub lists only `latest` and `14.4.0`, both from 2019. Building 17.4.26 in a session is ruled out by CLAUDE.md rule 8. Docker Hub `simvia/code_aster` (published by Simvia, not by EDF; Spack build with MPI, run as `source /opt/activate.sh && run_aster`) publishes 17.4.0, 17.4.22, 18.1.0 and others, but no 17.4.26. conda-forge `code-aster` stops at 17.3.17 on the v17 branch.

**Decision.** Run fixtures with `simvia/code_aster:17.4.22`, pinned by digest in the one-line file `CONTAINER_IMAGE` (`simvia/code_aster:17.4.22@sha256:ac8e68fe…`). `scripts/run-fixture.sh`, `scripts/session-start.sh` and `.github/workflows/solver-fixtures.yml` read it; `CONTAINER_TAG` (never created) is dropped. Each fixture's `output/provenance.json` records the image, digest, the solver's own version string and `UPSTREAM_VERSION`, so the 17.4.22 ↔ 17.4.26 gap is visible on every artefact.

**Why.** 17.4.22 is the newest published image on the same frozen maintenance line (`v17`) below the pin. `git diff --stat 17.4.22 17.4.26` in the mirror is 52 files (637+/396−), mostly `astest/`: non-linear solver line search (`code_aster/Solvers/`), `MACR_ELEM_STAT` numbering (`numddl`/`nueffe`), fracture `CALC_G` options, metallurgy, discrete shock elements, `POST_JMOD`, two message families (`MECANONLINE5`, `SOUSTRUC`), and copyright/maintainer header changes in `c_solveur.py`. None of it is on the fixtures' code paths (linear `MECA_STATIQUE`, DKT, `CALC_MODES`, `TEST_RESU`). The catalog and message extractors keep reading 17.4.26 from `upstream/`; only the runtime is 17.4.22. Building from source would cost hours per run and break rule 8; using 18.1.0 would cross a major version and invalidate the pin.

**Consequences.**
- `TEST_RESU` `VALE_CALC` values are 17.4.22 results; the non-regression check (default `TOLE_MACHINE` 1e-6) will flag any drift when the image changes.
- When `UPSTREAM_VERSION` is bumped (`caen upstream bump`), pick the image with the same tag if Simvia publishes it, else the closest lower one on the same line, update `CONTAINER_IMAGE` with the digest, record the diff here, and rerun `solver-fixtures.yml`.
- `docs/CLEARFEA-INTEGRATION.md` worker image base becomes `CONTAINER_IMAGE`. If an official EDF image for 17.4.x appears, switch to it.
- The image runs as uid 1000 by default; `run-fixture.sh` runs it as the caller's uid with `HOME=/tmp` so the mounted `output/` stays writable.

---

## Template

## ADR-NNN — <title>
**Date:** YYYY-MM-DD · **Status:** proposed | accepted | superseded by ADR-MMM

**Decision.** …

**Why.** …

**Consequences.** …
