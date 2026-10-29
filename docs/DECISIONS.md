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

## ADR-012 — Command-reference drafts: generated in place, no paid LLM call, translation memory for `fr=` strings
**Date:** 2026-10-29 · **Status:** accepted (agent, 2026-10-29)

**Context.** PLAN.md task 2.2 asks for `caen translate command <CMD>`: a first-draft `en/commands/<CMD>.md` with the keyword table pre-filled, "English column from glossary + LLM", astest examples linked and the doc ID linked if known. Calling a paid LLM API needs the owner's key (stop rule, ADR-010). TRANSLATION-GUIDE §1 says catalog `fr=` strings go "into the `.json` as `en_help`", but the `.json` is generated and never hand-edited (CLAUDE.md §5). Tier 1 has 5,893 keyword rows (DEFI_MATERIAU alone 3,255), far beyond what a reference can list. There is no command → U4 document ID mapping in the repo; the catalog's `docu=` is set for 8 of 268 commands.

**Decision.**
1. Drafts are written in place as `en/commands/<CMD>.md` with `status: machine` and committed. Task 2.3 edits them and sets `status: assisted`; from then on the generator skips the file unless `--force`. Machine drafts are snapshots: `tests/test_translate_command.py` regenerates them and fails when stale.
2. The "LLM" part is an in-session agent translation stored in a translation memory, `en/catalog-help.yaml` (human-edited YAML, `{fr, en, method}`, matched on the exact French string). The generator itself makes no network call. A string with no entry is shown as `TODO(translate): «fr»`; `caen translate command --list-untranslated` lists them for the next translator (in-session, or the batch client of task 3.1 once it exists). The `.json` files are not touched.
3. Keyword-table scope: every top-level simple keyword; factor keywords with their sub-keywords when the command has ≤ 150 distinct keyword paths, or when the factor is a "key keyword" of the command in COMMAND-SET.md; the other factors are named in an "Other keywords" list. Hidden keywords (`statut='c'`) are left out. `--all-keywords` expands everything.
4. Doc IDs: the catalog's `docu=` first, else `en/doc-ids.yaml`. Its Tier 1 entries are agent recall with `status: proposed` (the PDFs are not reachable), queued for the owner; a draft shows where its ID came from.
5. Upstream's 2016 English labels (`translation_upstream`, catapy) are not used in drafts: they are short labels, and ADR-004 keeps upstream English as seed only.
6. The synonym scan ignores French text quoted in guillemets (`«…»`), because drafts quote `fr=` strings verbatim.

**Why.** Drafts in place give 2.3 a starting file and keep one source of truth per command; the status gate protects authored work. A translation memory keeps the `.json` generated, is reviewable line by line, and is reused across commands and by later tasks. Scoping by COMMAND-SET keeps the drafts readable and follows ADR-003.

**Consequences.**
- PLAN 2.2's "English column from glossary + LLM" is met without spending the owner's API budget. Task 3.1's batch translator can fill `en/catalog-help.yaml` for Tier 2+ commands.
- TRANSLATION-GUIDE §1 now points `fr=` translations to `en/catalog-help.yaml` instead of an `en_help` field in the `.json`.
- `POURSUITE` gets no draft (no catalog; it reuses `DEBUT`'s); 2.3 covers it in `DEBUT.md`.

---

## ADR-013 — Default modeling types for ClearFEA body kinds
**Date:** 2026-10-29 · **Status:** accepted (agent, 2026-10-29)

**Context.** PLAN.md task 2.4 asks when ClearFEA should pick each `MODELISATION`. The Phase 6 builder (`codeaster_en.comm`, `docs/CLEARFEA-INTEGRATION.md` §2: `b.model(mesh, solids=[...], shells={...})`) needs one default per body kind, and the mesh order ClearFEA asks Gmsh for depends on it.

**Decision.** Defaults, documented in `en/guide/modelisations.md` ("How ClearFEA should choose"): solid → `3D` (second-order mesh preferred); thin shell → `DKT`; thick shell → `DST`; curved quadratic shell → `COQUE_3D` (with `CREA_MAILLAGE` `QUAD8_9` / `TRIA6_7`); beam → `POU_D_T` (not `POU_D_E`); plane stress → `C_PLAN`; plane strain → `D_PLAN`; axisymmetric → `AXIS`. `3D_SI` is never a default. One modeling family per model (plus discrete elements) until `LIAISON_ELEM` is in COMMAND-SET. Beams are offered only after COMMAND-SET adds `AFFE_CARA_ELEM` `POUTRE` / `ORIENTATION` and `AFFE_CHAR_MECA` `FORCE_POUTRE`.

**Why.** Each default accepts the element types an automatic mesher produces for that body kind (element catalog `phenomenons_modelisations.py`) and makes the weaker kinematic assumption where the cost is the same: `POU_D_T` reduces to `POU_D_E` for slender members (`ptka01.F90`), `DKT` is validated by our `shell_static` fixture against the Navier solution (0.007 %). `3D_SI` skips `TETRA4`/`PENTA`/`PYRAM`, so on an automatic mesh it silently drops elements (`MODELE1_70` is only a warning). A shell or beam node on a solid face shares translations only; without `LIAISON_ELEM` the joint is a hinge.

**Consequences.** The span/thickness thresholds (about 20 and 5) and the beam span/depth threshold (about 10) are textbook rules of thumb, marked `TODO(verify)` until the U3 modeling notes are available. The builder must refuse a mixed solid/shell/beam model rather than produce a hinge silently.

---

## ADR-014 — Message translation tool: seed, cached glossary prompt, strict checks, replay backend
**Date:** 2026-10-29 · **Status:** accepted (agent, 2026-10-29)

**Context.** PLAN.md task 3.1 asks for `caen translate messages --family <F>`: batched LLM translation with the glossary in the prompt, placeholder validation, a severity hint from the French wording, a dry-run cost estimate, resumable runs, `method: machine`. ADR-004 says to seed from upstream's 2016 `.po` where the French matches exactly. A run against the Claude API spends the owner's budget, which is a stop condition (ADR-010), and the session has no API key; the acceptance criterion still asks for one family translated end-to-end.

**Decision.**
1. One tool, `codeaster_en/translate/messages.py`, three steps per family: optional `.po` seed (verbatim `msgid` only, never the 87 whitespace-normalized matches; `method: machine`, `translation_source: upstream:i18n/en-US/aster_messages.po`), model translation of what is left (`en` null or `stale`), atomic write after every batch so a rerun resumes.
2. Prompt (TRANSLATION-GUIDE §6): rules plus every `term`/`abbrev` glossary entry in the system prompt, which is the same for every request and carries `cache_control`; the `command`/`keyword`/`value`/`concept` entries whose French occurs in the batch go in the user prompt with the items (`id`, `fr`, `placeholders`, and the `.po` English as a labelled `upstream_en` hint when the French matches after whitespace normalization). Output is forced by a JSON schema (`output_config.format`).
3. Every answer, model or `.po`, passes the same check: identical placeholder set (`placeholders.compare`) and no forbidden synonym (`aliases_en`) of a glossary entry whose French occurs in that message. Failures are asked again alone with the problem listed (default 2 re-asks), then left null and reported with a non-zero exit code.
4. Severity hint is rule-based from the French (TRANSLATION-GUIDE §3.5), not asked from the model: it is deterministic, free, and testable.
5. Claude backend: `claude-opus-5-5`, effort `medium`, server-side refusal fallback (`fallbacks: "default"`), no `temperature` (removed from the current API; the guide's "temperature 0" is replaced by the schema and the checks). `anthropic` is an optional extra (`tools[llm]`); CI never needs it.
6. Replay backend: answers from a JSON Lines file. `--export-requests` writes the exact requests; an agent in session (or a person) answers them, `--responses` imports them through the same checks. In-session work is recorded `method: assisted`, `translation_source: session:<task>`.
7. Glossary additions from a reply are appended to `en/glossary.yaml` as `status: proposed` (with `source` when the French occurs literally in the family's upstream file), never applied to other items in the same run.
8. `--force` never touches `reviewed` messages, and the `.po` seed never replaces an `assisted` translation.

**Why.** The seed is free and ADR-004 asks for it; checking it like a model answer stops the 2016 file's glossary conflicts from entering through the back door. Putting the stable part of the glossary in a cached system prompt keeps a bulk run cheap (dry run for all 277 families: about 506 requests, about $17 with Opus 5.5 before seeding, about $12 after, thinking tokens excluded). The replay path makes the tool usable without the owner's key, and the same validation path covers both.

**Consequences.**
- Task 3.1's end-to-end family is `MODELISA8` (43 messages; `MODELISA8_14` fires in the `shell_static` fixture), translated in session through `--export-requests`/`--responses`, `method: assisted`.
- Task 3.2 is: `caen translate messages --all --seed-only` (free), then the model run on the rest. The seed fills 3,130 messages: 3,221 match verbatim, 91 fail the placeholder or forbidden-synonym check (most use "cell" for *maille*). The model run needs the owner's API key and budget approval, or is done in session family by family through the replay path.
- TRANSLATION-GUIDE §6 describes the tool as built.

## ADR-015 — Results reader: native `h5py` MED reader; `medcoupling` as a test cross-check only
**Date:** 2026-10-29 · **Status:** accepted (agent, 2026-10-29, task 4.5)

**Context.** ARCHITECTURE §4.6 and PLAN 4.5 asked for `medcoupling` first with a `meshio` fallback. In session: the `medcoupling` 9.15 wheel is 18 MB, a compiled SWIG module with its own C++ MED stack; reading groups and element fields through it needs per-level and per-type bookkeeping (`getGroupArr(level, ...)`, Gauss localizations) that hides the file layout the report must cite. `meshio` 5.3 reads our three `.rmed` files but flattens steps into names like `MODES___DEPL[0] - 52.3396`, does not keep component names, and keeps groups only as family tags. The MED layout that `IMPR_RESU` writes is small and stable (HDF5: `ENS_MAA`, `FAS`, `CHA`, `PROFILS`; no-interlace datasets), and `h5py` is already used by our fixture tools.

**Decision.**
1. `codeaster_en.results.med` reads MED with `h5py` directly: coordinates, node and element numbers, families to groups, fields with components and steps, values on nodes (`NOE`), per element or Gauss point (`MAI.<type>`) and at element nodes (`NOE.<type>`), with profiles. `numpy` and `h5py` become runtime dependencies of the package.
2. `medcoupling` is a `dev` extra only: `tests/test_results.py` compares the native reader with it (coordinates, node groups, every nodal field value of the three fixtures) and uses it to write a synthetic element-node field. Tests skip those checks when it is not installed. `meshio` is not used.
3. The modal table takes effective masses from a printed `RECU_TABLE` of the `CALC_MODES` result (they are not in the `.rmed`); the `modal` fixture now prints one (`tables/modal_parameters.csv`). Frequencies come from the `.rmed` step values (full precision) when they match the table.

**Why.** One small reader we can test byte for byte against an independent library, with no compiled dependency for ClearFEA's worker, and with the file layout visible in the code that the report cites. The cross-check keeps the main risk (misreading the no-interlace layout) covered.

**Consequences.**
- ARCHITECTURE §4.6, REPORT-SPEC §6 and CLEARFEA-INTEGRATION §2 now describe the built API (`results.open`, `fields`, `extrema`, `reactions`, `modal`, `read_tables`).
- Structured (`MED_STRUCTURE`) meshes, polygons/polyhedra and fields on faces/edges (`FAC`, `ARE`) are not read; code_aster does not write them for our scope. A new MED major version must be checked with the cross-check test.
- `PLAN.md` 4.5 wording ("medcoupling first, meshio fallback") is superseded by this ADR.

---

## ADR-016 — Report generator: Markdown built in code, applied loads summed over the result mesh, tripwire scope
**Date:** 2026-10-29 · **Status:** accepted (agent, 2026-10-29, task 4.6)

**Context.** PLAN 4.6 asks for Markdown → HTML (Jinja2) → PDF (WeasyPrint) with a golden test on the `.md`; REPORT-SPEC §3 item 10 asks for an applied-load resultant and a balance check, which task 4.5 left open because it needs the loads of the `.comm`; REPORT-SPEC §1 allows the generator only sums, extrema, percentages and unit conversion. In session: WeasyPrint needs the Pango system library; the fixture logs print solution statistics in French (`Le système linéaire à résoudre a 14730 degrés de liberté`); reaction and load sums carry round-off of about 1e-15 of their largest term, whose last digits depend on the summation order.

**Decision.**
1. `codeaster_en.report`: `collect.py` builds one JSON-ready `RunModel` (golden `run_model.json` per fixture, compared with a 1e-9 float tolerance); `render.py` writes the Markdown in Python (tables need escaping and per-table "French name once" bookkeeping, which is clearer in code than in a template), converts it with Python-Markdown and places it in a Jinja2 page (`templates/report.html.j2`, print CSS) that WeasyPrint prints. `markdown` is a runtime dependency; WeasyPrint is the optional extra `report` (and in `dev`, so CI checks the PDF); without it `caen report` writes `.md`/`.html`/`.json` and warns.
2. The `.comm` is read by a restricted AST walk (`report/comm.py`): command calls, `_F`, literals, arithmetic, names bound to constants, references to result objects. Nothing is executed; unread statements are listed in the report. Solver settings with their defaults come from the command echo in the `.mess`, parsed by the same reader.
3. Solution statistics come from the arguments of catalog messages recovered by the 4.4 renderer (`FACTOR_1`, `ALGELINE7_17`, `ALGELINE6_41/42`), never from French regular expressions, so they survive an English `.mo` (ADR-004).
4. The applied-load resultant is a sum over the mesh the solver used (the `.rmed` mesh, written after `MODI_MAILLAGE`): `PRES_REP` (constant `PRES`): `-PRES × Σ vector area` of the face elements; `FORCE_FACE`: force × area; `FORCE_ARETE`: force × length; `FORCE_NODALE`: force × node count (full force at every node, `cafono.F90:271`). Kinematic keywords add no load. Anything else (gravity, functions, `FONC_MULT`, occurrences of one keyword that overlap) is listed as "not evaluated" and the balance is flagged partial. Balance error = |reactions + applied| / |applied| × 100 on the force components; reactions are the whole `REAC_NODA` sum (or the single printed resultant table when the field is not in the `.rmed`).
5. Display: values whose magnitude is below 1e-9 of the largest in a reaction/load table print as `0`; a balance error below 1e-6 % prints as "less than 0.000001 %". Numbers otherwise have 4 significant figures, engineering exponents.
6. English-only tripwire (`report/tripwire.py`): French function words, engineering terms and accented letters, checked outside fenced code, inline code spans and all-capital words (solver identifiers quoted in English message text). Log excerpts and the log appendix replace every line the renderer could not translate (printed outside the message catalog) with a bracketed count, so raw French never reaches the report; the command echo is kept (French keywords are the API).

**Why.** Every number in the report then has a cited source and survives being regenerated on another machine; the balance check is honest about what it could not sum instead of guessing physics.

**Consequences.**
- Both static fixtures balance to below 1e-6 % against the solver's own reaction sums (`TEST_RESU` `VALE_CALC`).
- Cut lines (REPORT-SPEC §3 item 12) and images (task 4.7) are not built; the report says the section is omitted. 2D models (`PRES_REP` on edges, per unit thickness or per radian) are not evaluated.
- Regenerating the fixtures (`solver-fixtures.yml`) changes timings in the logs: rerun `UPDATE_GOLDEN=1 pytest tests/test_report.py` in the same PR.

---

## ADR-017 — Report images: pyvista off-screen, opt-in, probed in a subprocess
**Date:** 2026-10-29 · **Status:** accepted (agent, 2026-10-29, task 4.7)

**Context.** PLAN 4.7 asks for optional deformed-shape and von Mises images in the report, feature-flagged because CI may lack OpenGL; REPORT-SPEC §3 item 11 adds mode-shape thumbnails. In session: pyvista 0.49.2 with the VTK 9.7.1 wheel renders off-screen once the OSMesa library is installed (`libosmesa6`); without it (no X display, no EGL, no OSMesa) the first render attempt ended the Python process instead of raising.

**Decision.**
1. `codeaster_en.report.images`, off by default: `Config(images=True)` / `caen report --images`. pyvista is the optional extra `images` (also in `dev`); CI installs `libosmesa6` so the rendering tests run there too.
2. `available()` renders one sphere in a child Python process (cached per process). Only when that succeeds does the report render in-process. Otherwise each planned figure keeps its number and caption and the report prints one placeholder line with the reason ("Figure 1 not generated (…): …"); nothing fails.
3. Figures: deformed shape colored by displacement magnitude over the undeformed feature edges, largest displacement drawn at 10 % of the bounding-box diagonal (scale rounded to 2 significant figures and stated in the caption); von Mises from `SIEQ_NOEU` `VMIS` on the undeformed shape (no image when the run wrote no nodal `SIEQ`, e.g. the DKT fixture); one thumbnail per mode (at most 12), same 10 % rule, captioned as arbitrary in sign and amplitude. Values come from the same `.rmed` fields as the report tables.
4. Geometry: the highest-dimension cells of the result mesh, drawn through their corner nodes (quadratic cells as linear ones, so no MED↔VTK node reordering is needed for mid-side nodes); lower-dimension skin and point cells are not drawn.
5. PNGs go to `<report dir>/images/`; the Markdown links them relatively. For the PDF those links are rewritten to absolute file URIs because WeasyPrint's base URL stays the job directory (logo paths). `run_model.json` gains `images` (`null` when not requested), so the goldens change by one key; images are not golden-tested, the tests check size, links, scale and captions.

**Why.** Images are a convenience, not a result: they must never make a report fail or depend on a GPU. The subprocess probe is the only way to survive a VTK build that aborts without a context. Drawing corner nodes keeps the converter to a table of cell types while staying faithful at report-thumbnail scale.

**Consequences.**
- On a machine without OSMesa/EGL, `--images` costs one probe (a second or two) and yields placeholder lines.
- Shell layers, element (ELNO/ELGA) fields and contour plots of other components are not drawn; add them when a fixture writes them.
- `run_model.json` schema stays at version 1 (one optional key added).

## ADR-018 — English gettext catalog: generated .po, own .mo writer, log-structure lines stay French
**Date:** 2026-10-29 · **Status:** accepted (agent, 2026-10-29)

**Context.** PLAN.md task 3.4 and ADR-004 (b): ship the English of `en/messages` as a gettext catalog the solver loads with `DEBUT(LANG='EN')`, check it with `msgfmt`, and run one fixture in English. Task 4.2 showed the `.mo` must be mounted at `<install>/share/locale/aster` (the image's `profile.sh` resets `ASTER_LOCALEDIR`).

**Decision.**
1. `caen translate gettext` (`codeaster_en/translate/gettext_po.py`) writes `en/messages/codeaster_en.po` (committed, generated, never hand-edited; `caen validate gettext` fails when it is stale) and, with `--mo DIR`, `DIR/en/LC_MESSAGES/aster_messages.mo` (never committed). Domain `aster_messages`, language directory `en` (what `i18n.py` asks for with `LANG='EN'`).
2. `msgid` = the extracted `fr`, exactly as passed to `_()`. Included: every non-stale translated message except the 15 bare strings (never passed to `_()`); the two f-strings are included (`_()` sees the evaluated text). Plus the four `Utmess` box footers, whose English stays `FOOTERS_EN` in `mess/render.py` (now defined in `mess/parser.py`), so solver and renderer print the same words.
3. Identical French must have identical English (one `msgid`); the generator refuses a conflict. Five pairs differed after 3.2 and were aligned in this task (`ALGELINE3_7`/`SOUSTRUC_88`, `ELEMENTS_45`/`SHELL1_3`, `ELEMENTS3_51`/`PLATE1_2`, `ELEMENTS3_52`/`PLATE1_3`, `VARC1_1`/`MATERIAL2_51`).
4. The `.mo` is written by our code (GNU format, no hash table); `msgfmt --check` (which includes `--check-format` for the `python-format` entries) runs in tests when installed. No system dependency for users.
5. `KEEP_FRENCH`: `SUPERVIS2_99` (`<I> <FIN> ARRET NORMAL`, which `run_aster/status.py` `RE_FIN` counts to recognize a normal end) and the stage lines `SUPERVIS2_71/72/73/74/75/80` (`# Commande #`, `# Résultat commande #`, `# Mémoire (Mo)`, `# Fin commande #`, `# Dépend de`) are left out of the catalog, so tools that read the log by these lines keep working. The renderer still shows them in English.
6. The `.mess` parser and renderer read both languages: English footers, English modal table head/tail (`ALGELINE6`), and English box bodies matched against the English template (`already_english: true`).
7. `FIXTURE_LANG=EN scripts/run-fixture.sh` runs a fixture with the catalog (copy of `run.comm` with `LANG="EN"` added to `DEBUT`, `.mo` mounted read-only) into `<case>/output_en/` (no `.rmed`; `provenance.json` records `po_sha256`). The optional `english` job of `solver-fixtures.yml` runs `solid_static`, `shell_static`, `modal`, `broken_missing_group` and commits on dispatch.

**Why.** One source of truth (ADR-004); a committed `.po` is reviewable and diffable, the binary is not. Writing the `.mo` ourselves keeps ClearFEA's image build to `pip install` plus one command. `run_aster`'s exit diagnosis must not depend on our translation. The gate of ADR-004 is met: the English runs show English diagnostics and identical `TEST_RESU` values.

**Consequences.**
- Gettext cannot reach `SUPERVIS` (and `SUPERVIS2` when `DEBUT` prints first, e.g. `CODE='OUI'`): imported before `LANG` is applied. The upstream proposal in ADR-004 (apply `LANG` before the first `UTMESS`) still stands.
- Editing an English text that fixtures print makes `output_en/` stale; `tests/test_gettext.py` then skips its renderer check (sha mismatch) until the `english` job is rerun.
- The `.comm` builder (Phase 6) emits `DEBUT(LANG='EN')`; the ClearFEA image installs the `.mo` (`docs/ENGLISH-LOCALE.md`, `docs/CLEARFEA-INTEGRATION.md` §4).

## ADR-019 — `.comm` builder: two layers, catalog-checked calls, ruff layout, fixtures as builder output
**Date:** 2026-10-29 · **Status:** accepted (agent, 2026-10-29, task 6.1)

**Context.** PLAN.md task 6.1 asks for a typed English API that emits French `.comm`, validated against the catalog JSON, covering Tier 1 (+ Tier 2 modal), with the three fixtures regenerated from it byte-identically (modulo comments). The committed solver outputs refer to `run.comm` line numbers, so a fixture whose text changes must be rerun. ARCHITECTURE §4.8 and CLEARFEA-INTEGRATION §2 sketched the API.

**Decision.**
1. Two layers in `codeaster_en/comm/`: `CommandFile` (`document.py`) takes French command and keyword names as the catalog spells them and checks every call when it is added (`catalog.py`); `Builder` (`builder.py`) is the English API on top (`read_mesh`, `model`, `material`, `assign_materials`, `shell_properties`, `fix`, `restrain`, `pressure`, `linear_static`, `compute_fields`, `resultant`, `modal`, `mass_properties`, `modal_parameters`, `print_table`, `write_med`, `test_results`). French solver names that are values (fields `SIEQ_NOEU`, components `DX`, groups) pass through unchanged.
2. The check follows upstream's `SyntaxChecker`: unknown command or keyword, `BLOC` conditions evaluated with defaults filled in (an unevaluable condition disables the block, as upstream does), mandatory keywords, the seven catalog rules (with their default values), `max`/`min`, type, `into`, bounds, `reuse` only on reentrant commands, a result name only where the command returns one. Concept types are checked when known, through a small parent map that a test checks against upstream `DataStructure.py`. It runs from `en/commands/*.json` only (no `upstream/` at run time); tests also pass builder output through upstream's own checker.
3. Layout is `ruff format`'s (Black's right-hand split, line length 100) re-implemented for the `.comm` subset in `syntax.py`, so no formatter is a runtime dependency; a test runs `ruff format` on builder output and expects no change. Comments are supported where fixtures use them (header blocks, a comment above a statement, a trailing note on a constant, a comment above a tuple item). `literal("1.0e-3")` keeps a number written as typed.
4. ADR-013 is enforced by the API: `model(mesh, kind)` takes one body kind and its default modeling; another modeling must be of the same family; shell properties are refused on a non-shell model; `fix` clamps rotations too on shells. Beams stay out (COMMAND-SET gap).
5. `start()` writes `DEBUT(LANG='EN')` by default (ADR-004, ADR-018); fixtures pass `language=None`, `testing=True` (`CODE='OUI'`). `alarms_as_errors` with `ignore_alarms` is refused (task 4.2 finding).
6. `tests/fixtures/comm_inputs.py` writes the three fixture files with the English API; `tests/test_comm.py` requires byte identity, comments included. `solid_static` and `shell_static` were already identical. `modal` had one statement (`CALC_MODES`) split by hand where `ruff format` keeps it on one 99-column line; the file was regenerated from the builder and the fixture rerun in session (French and English, image of ADR-011), with goldens updated.

**Why.** Keeping the French layer separate makes the English API thin and lets ClearFEA (or a later builder method) reach any catalog command with the same guarantee. Matching `ruff format` makes "byte-identical" a property any reviewer can reproduce, and builder files diff cleanly against hand-written ones. Rerunning one fixture costs seconds and keeps every `.mess` line reference true.

**Consequences.**
- A keyword the pinned catalog does not know cannot be written; an upstream bump that renames one fails the builder tests, not a solver run.
- Not checked without the solver: element/modeling compatibility, mesh groups present in the `.med` (ClearFEA's pre-run check), concept types of results whose type depends on keywords unless the builder names it.
- Not yet in the API (later tasks, Tier 2 sweep 6.4): `AFFE_CHAR_MECA_F`, remote loads (`LIAISON_RBE3`), gravity, springs, temperature loads, `MACR_LIGN_COUPE`, `NORM_MODE`; `CommandFile.call` covers them meanwhile.

---

## Template

## ADR-NNN — <title>
**Date:** YYYY-MM-DD · **Status:** proposed | accepted | superseded by ADR-MMM

**Decision.** …

**Why.** …

**Consequences.** …

## ADR-020 — Packaging: version `<upstream tag>.<serial>`, `en/` staged into the wheel, checkout first
**Date:** 2026-10-29 · **Status:** accepted (agent, 2026-10-29, task 6.2)

**Context.** PLAN.md task 6.2 asks for a pip-installable `codeaster-en` with `en/` as package data, lazily loaded, and a version scheme `<overlay>.<upstream tag>` decided here. The package lives in `tools/` while its data is the repository's `en/`, which setuptools package data cannot reach from `tools/`. The builder (6.1) reads `en/commands/*.json`, the renderer `en/messages/*.en.json`, labels `en/glossary.yaml`, and the solver needs the `.mo` that task 3.4 builds on demand (ADR-018). Publishing needs credentials and is outward-facing.

**Decision.**
1. **Version** = `<upstream tag>.<overlay serial>`, PEP 440 release segments only: `17.4.26.1` is overlay build 1 for code_aster 17.4.26. Upstream first (not `<overlay>.<tag>` as PLAN worded it) so `pip install "codeaster-en==17.4.*"` picks the overlay that matches a solver image, and an upstream bump sorts above every build of the previous tag. The serial restarts at 1 on each bump (task 7.1). Local versions (`+17.4.26`) are not used: PyPI refuses them. Single source: `codeaster_en.__version__` (setuptools `dynamic`); a test checks its prefix against `UPSTREAM_VERSION`. Distribution name `codeaster-en`, import name `codeaster_en`.
2. **Data**: `tools/setup.py` copies a fixed list (`DATA`) into `codeaster_en/_data/` of the build tree (`build_py`) or the sdist release tree (`sdist`), never the source tree; a wheel built from the sdist picks it up through the `_data/**/*` package-data glob. Shipped: `en/commands/*.json` and `*.md`, `en/messages/*.en.json` and `codeaster_en.po`, `en/glossary.yaml`, `catalog-help.yaml`, `doc-ids.yaml`, `UPSTREAM_VERSION`, `LICENSE`, `NOTICE.md`. Left out: `en/astest-index.json` (6 MB, only the draft generator reads it) and `en/guide/`. Wheel ≈ 3.1 MB.
3. **The `.mo` ships** at `_data/locale/en/LC_MESSAGES/aster_messages.mo`, built at packaging time from the committed `.po` by `codeaster_en/translate/mo.py` (standard library; also the writer behind `caen translate gettext`). A test checks that `.mo` is byte-identical to the one built from `en/messages`, so no `upstream/` is needed to build the wheel. `codeaster_en.data.localedir()` gives the directory to mount (docs/ENGLISH-LOCALE.md).
4. **Lookup**: `codeaster_en.data` resolves paths only: the checkout's `en/` when the package sits in one (editable install, tests, CI), else `_data/`. Each module reads its files when used, as before; nothing is read at import.
5. **No publishing** in a session: CI job `package` (`scripts/check-wheel.sh`) builds sdist and wheel, installs the wheel in a clean venv, runs it from outside the checkout (report of `solid_static` equals the golden) and keeps `dist/` as a run artifact. PyPI (or a GitHub release) is an owner step, listed in OWNER-REVIEW-QUEUE.

**Consequences.** A data edit in `en/` needs no packaging step in the repo; a wheel freezes it. `tools/setup.py` must be updated when the runtime starts reading another file (the test `test_shipped_data_covers_runtime_reads` guards the current set). `LICENSE` (GPL-3.0 text, copied from upstream's) and `NOTICE.md` now exist at the root, as LICENSING.md asked. The `License ::` classifier is not set: setuptools ≥ 77 refuses it next to the SPDX `license` expression, which is the newer equivalent.

## ADR-021 — ClearFEA adapter contract: `codeaster_en.job`, free pre-run check, event-level tailing, no MPI yet
**Date:** 2026-10-29 · **Status:** accepted (agent, 2026-10-29, task 6.3; owner sign-off pending per PLAN 6.3)

**Context.** PLAN 6.3 asks for `docs/CLEARFEA-INTEGRATION.md` with concrete signatures, the container contract, job layout, the failure → billing mapping and a worked example. The draft named modules that were never built (`codeaster_en.run`, `catalog.validate_comm`, `version`) and left three items open (§8). The `.export` logical units are a coupling between the builder's defaults and the job layout, and the spec's billing policy relies on "pre-run checks" that did not exist.

**Decision.**
1. **New module `codeaster_en.job`** (no new data): `export_text` / `write_export` write `run.export` for the §3 layout (units 1, 20, 6, 8, tables 30–79, 80; byte-identical to the fixtures'), `table_units` numbers table files, and `precheck(comm_text, mesh)` returns `Problem`s for a command file that is not Python and for literal `GROUP_MA*`/`GROUP_NO*` names absent from the `.med` and not created by `DEFI_GROUP`. It catches two of the four broken fixtures (`broken_python_syntax`, `broken_missing_group`) with no solver.
2. **Running stays with ClearFEA.** No `run` helper: the call is one `run_aster run.export` inside ClearFEA's container with ClearFEA's limits; a wrapper here would only hide the timeout/cancellation policy ClearFEA owns. `scripts/run-fixture.sh` is the reference.
3. **No `catalog.validate_comm` for arbitrary `.comm` files.** Builder output is checked call by call already; a full checker for bring-your-own files would need the upstream `code_aster.Cata` checker (not in the wheel) or a second implementation of it. Such files fail fast at run time with `SUPERVIS_4` (`user-model`).
4. **Open items closed:** live tail is per event (`mess.stream` + `render_event`); `.comm` + `run_aster` stays (ADR-008); MPI is out until a fixture runs with `mpi_nbcpu > 1`.
5. **Worked example is executable:** the fenced block between `worked-example` markers in §9 runs in `tests/test_clearfea_example.py`, so the spec cannot drift from the code.

**Why.** ClearFEA should code against functions that exist and are tested; the units and the free group check are the two pieces of adapter logic that touch French and solver conventions, so they belong here (§7).

**Consequences.** Signature changes to anything in §2 are API changes for ClearFEA (§6). The group check does not follow variables or statement order; those faults still reach the solver and are classified from its log. A priority tier with MPI needs a new fixture and an `export_text` parameter.

## ADR-022 — Builder Tier 2: discrete elements beside the body family, remote loads by RBE3, hydrostatic pressure by formula
**Date:** 2026-10-29 · **Status:** accepted (agent, 2026-10-29, task 6.4b)

**Context.** PLAN 6.4 adds springs, remote force and moment, hydrostatic pressure, gravity, rotation and mode normalization to the builder. ADR-013 says a model has one modeling family, but springs (`DIS_T`) and the master point of an RBE3 remote load (`DIS_TR`) are discrete elements that upstream test cases add to a solid or shell model (`astest/zzzz144a.comm:36` adds a `DIS_TR` point to a `3D` model). The builder does not read the mesh, so it cannot tell a two-node spring from a point.

**Decision.**
1. **Discrete elements are not a second family.** `model(..., springs=, remote_points=)` adds `DIS_T` / `DIS_TR` `AFFE` occurrences after the body family's; `Model.discrete` records them. Mixing two body families stays refused (ADR-013 unchanged).
2. **`element_properties` covers every discrete group or refuses** (the solver would stop with `AFFECARAELEM_32`/`_33`). Springs need a `Spring`; the caller says whether it is a two-node spring (`K_T_D_L`) or a point tied to ground (`to_ground=True`, `K_T_D_N`). Remote points get a zero `K_TR_D_N` without asking, as zzzz144a does. All in `REPERE='GLOBAL'`, so zero-length springs need no local frame. `shell_properties` is now a shortcut for it (same output).
3. **Remote loads are RBE3, not rigid.** `remote_load` writes `LIAISON_RBE3` (all six master DOFs, `DDL_ESCL='DX-DY-DZ'`, `COEF_ESCL=1.0`) and the `FORCE_NODALE` in one `AFFE_CHAR_MECA`, on solids and shells alike (`astest/ssls136a.comm:59` uses `DX-DY-DZ` on DKT). A rigid connection is a separate `rigid_link` (`LIAISON_SOLIDE`), because it stiffens the face and engineers pick between the two on purpose.
4. **Hydrostatic pressure is one `FORMULE` of one coordinate**, `max(rho*g*(h - Z), 0.0)` with the numbers written into the expression (no extra `FORMULE` keyword arguments, which our catalog check does not model), then `AFFE_CHAR_MECA_F PRES_REP`. The axis points up; the free surface is at `axis = h`.
5. **Modes:** `normalize_modes` is `NORM_MODE` in place (default `MASS_GENE`, because `CALC_MODES` scales to a unit largest component); `filter_modes` is `EXTR_MODE` by frequency band or by `MASS_EFFE_UN` threshold in any direction (`bibfor/op/op0168.F90:294`), with the cumulative print on.

**Why.** These are the forms upstream's own tests use; each choice is written once in the builder, so ClearFEA does not have to rediscover the discrete-element and `DDL_ESCL` details.

**Amendment (task 6.4c, first solver run of the `solid_loads` fixture).** `element_properties` also writes a zero mass for every discrete group (`M_T_D_L`/`M_T_D_N` for springs, `M_TR_D_N` for remote points, as in `astest/fdlv100a.comm:78` and `astest/sslx200a.comm:62`): without it, gravity and rotation loads stop on alarm `DISCRETS_26` (`bibfor/te/te0043.F90:79`) raised as an error. Two additive methods: `node_group_at` (`DEFI_GROUP ENV_SPHERE`, for a node that must not be a POI1 because of `MODELISA8_14`) and `resultant(moment_about=)`. The report lists body loads (`PESANTEUR`, `ROTATION`) as not summed, because their resultant needs the mass (REPORT-SPEC §1), and with any unsummed load it states that no equilibrium check was made instead of printing a misleading percentage.

**Consequences.** `CLEARFEA-INTEGRATION.md` §2.1 gains the new methods (additive; no signature changed). `fix()` on a shell model clamps rotations, which a `DIS_T`-only ground node does not have; use `restrain` with translations there. Beams, masses (`M_T_D_N`) and temperature loads are not wrapped yet.

