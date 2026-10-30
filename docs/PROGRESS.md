# Progress log

Newest entry first. One entry per session. Keep entries short; detail belongs in the PR.

Template:

```
## YYYY-MM-DD — <task id> <title> — <agent|owner>
Done: …
Open: …
Decisions: (ADR refs or "none")
Needs owner: …
```

---

## 2026-10-30 — 5.1 ingest the French documents — agent
Done: code-aster.org answered from the sandbox for the first time (`/doc/default/fr/…` redirects to `/doc/v16/…`), so the PDFs were fetched by the agent instead of waiting for the owner (ADR-026). New package `codeaster_en.docs` and CLI `caen docs ingest <pdf…>` / `caen docs fetch [DOC-ID…]` (pdfplumber, new `docs` extra). The extractor cuts the running header and footer and parses page 1's (title, date, key, revision, licence), keeps numbered headings with their level, puts Courier lines on the fixed-pitch grid so syntax trees and two-column listings keep their columns, finds ruled tables (line strategy) and unruled ones (two rows sharing a column start), joins paragraphs across lines and pages, flags formula lines `equation`, marks figures, drops the table of contents, and cuts chunks of at most 6,000 characters at level 1–2 headings. Ingested and committed 35 documents in `en/docs/_src/` (`<ID>.fr.json` + `.fr.md`, `INDEX.md`, 4.3 MB): every ID of `en/doc-ids.yaml`, U1.03.01 and U7.05.21 (IMPR_RESU MED). Reviewed by hand: `U4.41.01.fr.md` against the PDF (syntax tree, both operand tables, the modelisation listing by family, the two distribution tables, the example). Measured over all 35: 99.4 % of the words of the page bodies reach the Markdown (212,417 words; the rest are mostly formula fragments and Courier words split by the grid).
Found: `U4.63.11` is `PROJ_BASE`; `NUME_DDL` is `U4.61.11` (fixed in `en/doc-ids.yaml` and `NUME_DDL.md`). `U4.81.01` does not exist; the MED format of `IMPR_RESU` is `U7.05.21` (IMPR_RESU.md's MED `TODO(verify)`s now point there). All 35 doc-ids entries are `verified` by title (tested). Documents are GFDL (no version; we use 1.3): LICENSING.md, NOTICE.md and `en/docs/_src/README.md` updated. Document dates run from 2012 (U1.03.01) to 2024.
Tests: `tests/test_docs_ingest.py` (+43): golden ingest of `tests/fixtures/docs/U4.21.01.pdf` against the committed JSON, structure and frame checks, ≥ 99 % body words, chunk coverage, schema, `.fr.md` and `INDEX.md` current, verified IDs name their command. The synonym validator skips `_src/` (French).
Open: 5.2 (`caen translate doc`, chunked translation into `en/docs/`, GFDL headers) is now unblocked; the references' `TODO(verify)` items can be settled against `en/docs/_src/` (candidate task). Formulas need hand work in 5.2.
Decisions: ADR-026.
Needs owner: nothing blocking; review-queue entry added (licence reading, edition, extraction quality).

## 2026-10-30 — 2.3e remaining Tier 1/2 command references — agent
Done: the five draft references left after 2.3a–d rewritten as `status: assisted`: Tier 1 `DEFI_CONSTANTE`, `MACR_LIGN_COUPE`, `POST_RCCM` (EVOLUTION + `PM_PB` in full, other options marked "Out of Tier 1 scope") and Tier 2 `THER_LINEAIRE`, `AFFE_CHAR_THER`. Each has a full keyword table, rules, output-table notes where relevant, patterns cited to `astest` lines and pitfalls. Claims that the catalog and test cases did not settle were checked by running small studies with the pinned image (`docs/reference-checks/`, four studies on the `solid_static` and `solid_loads` meshes): thermal slab against hand values (flux 20, convection 50, source 10), default transient starts in steady state, `THETA=0.57` oscillation vs `THETA=1.0`, `RAYONNEMENT` refused (`CHARGES9_42`), `FLUN` > 0 enters the body, `DISTANCE_MAX=0.0` drops points outside the mesh (`POST0_24`), `POST_RCCM` table shapes and `POSTRCCM_7`, `DEFI_CONSTANTE` in `AFFE_CHAR_MECA_F` gives the fixture reaction.
Found: `MACR_LIGN_COUPE` with several `LIGN_COUPE` occurrences decides the axis rotation from the last occurrence's `REPERE` (`macr_lign_coupe_ops.py:680`, `:893`): `LOCAL` then `INITIAL` leaves both lines unrotated; `INITIAL` then `LOCAL` stops with `ValueError`. Documented as a pitfall; candidate upstream report.
Bundle: the Tier 1 compact bundle must stay under 150k tokens (ADR-025); intros, pitfalls and patterns were trimmed and out-of-scope `POST_RCCM` rows marked so the compact rules drop them. `test_bundle` green.
Open: 8 `TODO(verify)` across the five pages. The reference checks are not solver fixtures (no `run.json`), same status as `docs/bundle-trial/`. 5.1–5.3 still wait for the U4 PDFs.
Decisions: none (no ADR).
Needs owner: nothing blocking; review-queue entries added.

## 2026-10-30 — 5.5 LLM context bundle — agent
Done: `caen bundle [--tier 1|2] [--detail compact|full] [--out] [--max-tokens]` (`codeaster_en.bundle`): guide, command references and glossary in one deterministic Markdown file with a preamble (rules for writing a `.comm`) and a contents list with line numbers. Measured with Claude's tokenizer, the whole Tier 1 set is ~350k tokens, so the default compact level cuts keyword tables, patterns, rules, guide pages and glossary by fixed rules (ADR-025): Tier 1 compact is 285,168 characters, 146,240 tokens estimated, 143,015 as read by Claude Code. `llm-bundle.yml` publishes all four bundles to the rolling `llm-bundle` pre-release (and to any published release). Trial: a fresh agent with only the bundle wrote a plate-with-hole study (`AFFE_CHAR_CINE`, `FORCE_FACE`, `TEST_RESU`) that ran `DIAGNOSTIC JOB : OK` with both checks `OK` on the first run with the pinned image (`docs/bundle-trial/`). `tests/test_bundle.py` (17 tests). The `caen` stub mechanism is gone (bundle was the last stub).
Open: the trial study is not a solver fixture (no `run.json`/builder source), so it was run in session with the fixtures' image and Docker command, not by `solver-fixtures.yml`. Trial gaps for the guide: first-run `VALE_CALC`, `FORCE_FACE` pattern, `ENV_SPHERE` meanings, rigid-body restraint of solids. 5.1–5.3 still wait for the U4 PDFs.
Decisions: ADR-025.
Needs owner: nothing blocking; review-queue entry added.

## 2026-10-29 — 5.4 engineers' guide — agent
Done: "code_aster for structural engineers" in `en/guide/`, 8 new pages (`status: assisted`): `README.md` (index, reading order, tools), `concepts.md` (workflow, the command sequence as result objects, supports are loads, `EXCIT`, syntax, groups, units, logical units, message levels, log line offsets), three walkthroughs built from the fixtures (`walkthrough-solid-static.md`, `walkthrough-shell-static.md`, `walkthrough-modal.md`), `reading-logs.md`, `reading-results.md` (`caen results`, tables, checks, `caen report`) and `faq.md` (every message ID our fixture runs printed: `SUPERVIS_22`, `CATAMESS_89`, `MODELISA8_14`, `DISCRETS_26`, `MODELISA7_77`, `FACTOR_11`, `SUPERVIS_4`, Python `SyntaxError`, plus four practical questions).
The solid walkthrough is a full study: `mesh.geo` and `run.export` are the fixture's, the `.comm` is the fixture's without `CODE` and `TEST_RESU`. Verified in session by doing it: Gmsh 4.15.2 mesh, the Docker command from the page with the pinned image, `DIAGNOSTIC JOB : OK`, `reactions.csv` identical to the fixture, `caen report` on the study directory. The "things to try" variants were run too: wrong group `MODELISA7_77`, support left out `FACTOR_11`, `PRESSION` `SUPERVIS_4`, `TETRA10` mesh (peak 46.7 vs 34.7 MPa, reaction 3926.97 N = the true-circle value). Without `docker run --user` the run fails with `PermissionError` (uid 1000 in the image); the page says so.
`tests/test_guide.py` (+6 tests): page structure, `<!-- example: path -->` blocks byte-identical to fixture files, the `example-study` block has the fixture's commands (AST) minus `DEBUT` keywords and `TEST_RESU` and passes the pinned catalog check, relative links and heading anchors resolve, FAQ IDs appear in a committed fixture log (or the fixture notes) and in `en/messages`. Citation check now skips placeholder paths such as `en/messages/<FAMILY>.en.json`.
Self-review: every `path:line` citation re-printed and read against its line; numbers recomputed (Navier, Euler–Bernoulli ratios, mean hoop stress P·Ri/t = 10.0 MPa vs 9.9 MPa in the run).
Open: PLAN 5.4's acceptance (a colleague completes `solid_static` unaided) is the owner's; queued. 5.1–5.3 still wait for the U4 PDFs. Next ready task: 5.5 (LLM context bundle), which includes this guide.
Decisions: none (no ADR). The wheel still does not ship `en/guide/` (ADR-020); 5.5's bundle is the way the guide reaches an agent.
Needs owner: nothing blocking; review-queue entry added.

## 2026-10-29 — 7.2 scheduled monthly upstream bump — agent
Done: `.github/workflows/upstream-bump.yml`, which runs at 05:17 UTC on the 3rd of each month or on dispatch (`to`, `dry_run`).
It runs the new `caen upstream check` (prints `status=newer|current|older` against the mirror) and goes on only for `newer`, and only when no `upstream/bump-<tag>` branch exists yet.
It then runs `caen upstream bump`, followed by `caen validate` and `pytest`. Failures are recorded, not fatal.
It commits exactly what the tool wrote, pushes `upstream/bump-<tag>` and opens a PR. If Actions may not open PRs, it opens an issue instead.
The PR body comes from the new `caen upstream pr-body`: a merge checklist, the validate and pytest results with each failing test, the stale list (`caen upstream stale`: stale messages with a placeholder-match flag, plus messages with no English), and the diff report, truncated under GitHub's limit.
GITHUB_TOKEN pushes start no workflows, so the job dispatches `ci.yml` (new `workflow_dispatch` trigger) and `solver-fixtures.yml` on the branch. solver-fixtures opens its regenerate PR into the bump branch.
4 new tests: check/bump/stale/body on the stand-in mirror, truncation and caps, the CLI flags the workflow uses, and the workflow structure. actionlint clean.
Checked against the real mirror: `check` gives `stable` → current (17.4.26), 17.5.8 → newer, 17.4.22 → older.
Rehearsal: I applied a real bump to 17.5.8 locally and ran the workflow's steps by hand, then reverted it. All changed paths fall inside the commit pathspec. The stale list showed `HOMO1_18` (placeholders match) and 4 messages with no English. validate passed, and pytest had 27 failed and 3 errors (classes in ADR-024 Consequences). ADR-023 only expected the fixtures and placeholders to fail.
Open: the PR path runs for real only once `stable` moves. After this merges, a dispatched dry run to 17.5.8 exercises the job on Actions (result below, if any). The follow-up for a bump PR is a coordinator task: re-translate, regenerate goldens, drafts and counts, and merge the fixture PR.
Decisions: ADR-024.
Needs owner: nothing blocking. Queue entry: allow Actions to create PRs (repo setting); an optional token would make CI run natively on bump PRs.

## 2026-10-29 — 7.1 upstream bump tool — agent
Done: `caen upstream bump --to <tag> [--dry-run] [--image …] [--report …]` (new package
`codeaster_en.upstream`: `bump.py`, `diff.py`). Resolves the tag with `ls-remote` (moving tags
such as `stable` → lowest version tag on the same commit), fetches it `--depth 1`, extracts
commands and messages from a `git archive` export, diffs against the committed `en/` JSON and
writes `docs/upstream-diffs/<old>-<new>.md` (commands/keywords added, removed, changed field by
field; messages added, removed, French changed with the differing span; stale count and
placeholder-changed flag; command references and glossary entries to revisit; follow-up). An
applied bump also moves the submodule and rewrites `UPSTREAM_VERSION`, the JSON (removed
commands/families deleted), astest index, inventory block, `.po`, `__version__` (`<tag>.1`) and,
with `--image`, `CONTAINER_IMAGE`; it commits nothing. Exercised on real tags: applied 17.4.26 →
17.4.22 and back with `--to stable` (every file restored except the English of the two messages
17.4.22 lacks, restored from git); dry run to 17.5.8 (1 command, 4 added, 1 removed, 1 stale
message). Both reports committed with a README. 7 new tests (diff units; a bump against a local
stand-in mirror with tags 1.0.0/1.0.1: dry run leaves the tree untouched, apply marks the stale
message, deletes the removed family, sets version and image).
Open: task 7.2 (scheduled monthly run + PR). The pin stays at 17.4.26: `stable` has not moved.
Decisions: ADR-023.
Needs owner: nothing blocking; review-queue entry added.

## 2026-10-29 — 6.4c Tier 2 fixture and report coverage — agent
Done: last of three PRs for PLAN 6.4 (with #35, #36). New fixture `solid_loads`: steel block
on a clamped base with gravity, rotation, water pressure (`FORMULE` + `AFFE_CHAR_MECA_F`), a
remote force and moment spread by RBE3, and a SEG2 spring to a ground node; run in the pinned
image (17.4.22), `DIAGNOSTIC JOB : OK`, no alarm. Reaction sums match the hand values to
1e-12 %; the support moment table (new `resultant(moment_about=)`) matches the hand moments
(MX exact; MY, MZ within 2e-5 and 9e-5, the couple of the 50 mm spring). `modal` now runs
`NORM_MODE` (mode 1 generalized mass 1, new check `M1_MASS_GENE`; frequencies unchanged), rerun
in both locales. Builder: zero masses on discrete groups (found by the first run: alarm
`DISCRETS_26` under gravity), `node_group_at` (`ENV_SPHERE`). Results reader: nodal fields
with a MED profile (the `SIEQ_NOEU` of a model with discrete-only nodes) failed to load; fixed.
Report: RBE3 targets, `FORMULE` expressions under the loads table, body loads marked "needs
the mass distribution", no balance percentage when loads are unsummed, a note on relation
reactions, `RESULT_X..Z` table columns. Goldens regenerated.
Open: PLAN 6.4 done. `EXTR_MODE` and `rigid_link` (`LIAISON_SOLIDE`) are checked by the
upstream syntax checker only, not by a solver run. Tier 2 rows outside PLAN 6.4's list stay
open: bonded contact (`LIAISON_MAIL`), temperature load (`AFFE_VARC`), steady thermal
(`THER_LINEAIRE`, `AFFE_CHAR_THER`, still `machine`).
Decisions: ADR-022 amended (zero masses, report treatment of body loads).
Needs owner: nothing blocking; review-queue entry added.

## 2026-10-29 — 6.4b AFFE_CHAR_MECA_F reference and Tier 2 builder methods — agent
Done: second of three PRs for PLAN 6.4. `en/commands/AFFE_CHAR_MECA_F.md` rewritten as a full
reference (`assisted`, 2 `TODO(verify)`). Builder (ADR-022): `model(springs=, remote_points=)`
adds `DIS_T`/`DIS_TR` occurrences; `element_properties` (`COQUE` + `DISCRET`, `Spring`, zero
`K_TR_D_N` on remote points, refuses uncovered discrete groups; `shell_properties` now calls it,
fixture output unchanged); `remote_load` (`LIAISON_RBE3` + `FORCE_NODALE`), `rigid_link`
(`LIAISON_SOLIDE`), `gravity` (`PESANTEUR`), `rotation` (`ROTATION`), `hydrostatic_pressure`
(`FORMULE` + `AFFE_CHAR_MECA_F PRES_REP`), `normalize_modes` (`NORM_MODE`), `filter_modes`
(`EXTR_MODE`). Every form taken from an upstream test case (zzzz144a, ssls136a, sdnv138c,
erreu01a, forma12a). Tests: pattern test, refusal test, and the upstream `code_aster.Cata`
checker accepts a file using every new method. `CLEARFEA-INTEGRATION.md` §2.1 lists the new
methods (additive).
Open: 6.4c (fixture with remote load, springs, gravity, rotation and hydrostatic pressure run
in the solver; modal fixture with `NORM_MODE`/`EXTR_MODE`; report coverage).
Decisions: ADR-022.
Needs owner: nothing blocking; review-queue entry added.

## 2026-10-29 — 6.4a Tier 2 modal command references — agent
Done: first of three PRs for PLAN 6.4. Machine drafts for the 10 new Tier 2 commands
(`caen translate command --tier 2`; 57 Tier 2 `fr=` strings added to `en/catalog-help.yaml`, 10
U4 IDs to `en/doc-ids.yaml`, `proposed`). Seven rewritten as full references, `status:
assisted`, 2.3 format: `CALC_MODES`, `NORM_MODE`, `EXTR_MODE`, `ASSEMBLAGE`, `CALC_MATR_ELEM`,
`NUME_DDL`, `ASSE_MATRICE`. Evidence: catalogs, `MacroCommands/Modal/calc_modes_*.py`,
`assemblage_ops.py`, `calc_matr_elem_ops.py`, `nume_ddl_ops.py`, `asse_matrice_ops.py`, Fortran
(`op0037`, `op0045`, `op0168`, `vpinis`, `vpfopr`, `vppara`, `vpnorm`, `vpcntl`, `vppost`,
`vpstor`), message texts and the modal fixture log. Self-review: every file:line re-printed; 11
`TODO(verify)` left. Glossary: 12 new `proposed` entries (`VERI_MODE`, `STOP_ERREUR`, `STURM`,
`SEUIL_FREQ`, `DIM_SOUS_ESPACE`, `STOP_BANDE_VIDE`, `AMELIORATION`, `MODE_SIGNE`, `AVEC_CMP`,
`SANS_CMP`, `MATR_ELEM`, `CHAR_CINE`), 500 entries.
Findings: default `CALC_MODES` shapes have a unit largest component, not unit generalized mass
(`vppara.F90:130`); `CALC_MODES` has no `MODELE` form (COMMAND-SET says it has); kinematic
supports work for modal analysis through `ASSE_MATRICE CHAR_CINE` (`sdll02b`), although the 6.1
builder doc says static only; `VERI_MODE` failure is `ALGELINE2_74` raised as a solver error.
Open: 6.4b (`AFFE_CHAR_MECA_F` reference + builder methods for remote force/moment, hydrostatic
pressure, centrifugal load, springs, `NORM_MODE`) and 6.4c (fixtures, report). `THER_LINEAIRE`
and `AFFE_CHAR_THER` (COMMAND-SET Tier 2 thermal row, outside PLAN 6.4's list) stay `machine`.
Decisions: none (no ADR).
Needs owner: nothing blocking; review-queue entry added.

## 2026-10-29 — 6.3 ClearFEA adapter spec — agent
Done: `docs/CLEARFEA-INTEGRATION.md` rewritten against the built code (signatures checked with
`inspect`): builder method table (6.1), `job`, `mess`, `results`, `report`, `data`, version
(ADR-020); job layout with the logical-unit table; container contract (image, wheel, `.mo`
placement, entry, exit codes); failure → billing in three steps with each rule's evidence; the
§8 open items decided; §9 worked example (build → precheck → run → classify → results →
report). New `codeaster_en.job` (ADR-021): `export_text`/`write_export` (byte-identical to the
four fixture exports), `table_units`, `precheck` (catches `broken_python_syntax` and
`broken_missing_group` without a solver). `tests/test_job.py` (18) and
`tests/test_clearfea_example.py` (4: the doc's block is executed; shell_static outputs stand in
for the solver; a misspelled group is rejected before the solver; a singular-matrix run is
`FACTOR_11`, charged).
Verified: `ruff check`, `ruff format --check` clean; `pytest` 538 passed / 4 skipped;
`caen validate` OK.
Open: owner sign-off (PLAN 6.3 acceptance; OWNER-REVIEW-QUEUE). `TODO(verify)`: exit codes for
time/memory limits and crashes, the worker image's Python, MPI. Next ready task: 6.4 (Tier 2
sweep).
Decisions: ADR-021 (no `run` helper, no `validate_comm` for bring-your-own files, per-event
tail, no MPI yet).
Needs owner: sign-off on the spec (not blocking further tasks).

## 2026-10-29 — 6.2 package codeaster-en — agent
Done: pip-installable `codeaster-en` (ADR-020). Version `17.4.26.1` = upstream tag + overlay
serial, single-sourced in `codeaster_en.__version__` (report goldens updated from `0.1.0`).
`tools/setup.py` stages `en/` (commands JSON + references, messages, `.po`, glossary, help,
doc IDs), `UPSTREAM_VERSION`, `LICENSE`, `NOTICE.md` and a `.mo` built from the committed `.po`
into `codeaster_en/_data/` of the wheel and sdist. New `codeaster_en.data` resolves paths
(checkout first, then wheel); `comm`, `mess`, `results`, `report` use it instead of
`parents[3]`. `codeaster_en.translate.mo` (stdlib `.po` reader and `.mo` writer) now backs
`caen translate gettext` too. `LICENSE` (GPL-3.0 text from upstream) and `NOTICE.md` added.
`scripts/check-wheel.sh` + CI job `package`: `python -m build`, clean venv, `from codeaster_en
import report`, `.mo` loads, `caen report` on `solid_static` from the wheel equals the golden;
`dist/` kept as a run artifact. `tests/test_package.py` (4 tests). Wheel 3.1 MB, 584 data files.
Open: publishing (PyPI or GitHub release) is an owner step, not done (OWNER-REVIEW-QUEUE).
Decisions: ADR-020.
Needs owner: PyPI account/trusted publisher if a public release is wanted.

## 2026-10-29 — 6.1 .comm builder — agent
Done: `codeaster_en.comm` (`tools/codeaster_en/comm/`): `CommandFile` (French names, every call
checked against `en/commands/*.json` when added: unknown command/keyword, `BLOC` conditions with
defaults, mandatory keywords, the 7 catalog rules, counts, types, `into`, bounds, `reuse`, result
names, known concept types) and `Builder`, the English API (`read_mesh`, `node_groups`,
`orient_skin`, `orient_shell_normals`, `model` with ADR-013 body kinds, `material`,
`assign_materials`, `shell_properties`, `fix`/`restrain` (`DDL_IMPO` or kinematic
`MECA_IMPO`), `pressure`, `linear_static`, `compute_fields`, `resultant`, `modal`
(`CALC_MATR_ELEM`/`NUME_DDL`/`ASSE_MATRICE`/`CALC_MODES`), `mass_properties`,
`modal_parameters`, `print_table`, `write_med`, `test_results`). Layout = `ruff format`'s, done
in code (`syntax.py`). `tests/fixtures/comm_inputs.py` writes the three fixture `run.comm` files
with the English API, comments included; `tests/test_comm.py` (26 tests): byte identity, `ruff
format` leaves builder output unchanged, round trip through the report's `.comm` reader, upstream
checker accepts builder output, catalog-check failures, `DS_PARENTS` vs upstream.
`solid_static` and `shell_static` were already byte-identical. `modal` had one hand-wrapped
statement (`CALC_MODES`, 99 columns, which `ruff format` keeps on one line): regenerated from the
builder and rerun in session (`run-fixture.sh`, French and `FIXTURE_LANG=EN`, image of ADR-011):
exit 0, same `TEST_RESU` values, only timestamps/timings changed; modal report goldens updated.
ARCHITECTURE §4.8 and CLEARFEA-INTEGRATION §2 now show the built API (snippets executed).
Verified: `ruff check` and `ruff format --check` clean, `pytest` 512 passed / 4 skipped (msgfmt,
off-screen OpenGL), `caen validate` OK.
Open: 6.2 (packaging) is next; `en/commands/*.json` are read from the repo path, so 6.2 must
ship them as package data and point `DEFAULT_COMMANDS_DIR` there. Remote loads, gravity, springs,
temperature, `AFFE_CHAR_MECA_F`, `MACR_LIGN_COUPE`, `NORM_MODE` are not English methods yet
(6.4); `Builder.file.call` reaches them with the same checks.
Decisions: ADR-019.
Needs owner: nothing blocking; review-queue entry added.
Branch is `claude/project-thread-uo0mbf` (session-assigned).

## 2026-10-29 — 3.4 English messages as gettext — agent
Done: `caen translate gettext` (`tools/codeaster_en/translate/gettext_po.py`) generates
`en/messages/codeaster_en.po` (6,813 entries, committed) and, with `--mo DIR`,
`DIR/en/LC_MESSAGES/aster_messages.mo` (own GNU `.mo` writer; `msgfmt --check` clean, including
format checks). `caen validate` gains `gettext` (the `.po` must match `en/messages`).
`FIXTURE_LANG=EN scripts/run-fixture.sh` runs a fixture with `DEBUT(LANG="EN")` and the `.mo`
mounted at the install's `share/locale/aster`; `solid_static`, `shell_static`, `modal`,
`broken_missing_group` ran in session (17.4.22 image), outputs in `tests/fixtures/*/output_en/`:
English diagnostics and footers, identical `TEST_RESU` values and exit codes.
`solver-fixtures.yml` has an optional `english` job (PR verify; commit on dispatch). The `.mess`
parser and renderer now read English footers, the English modal table and English box bodies
(`already_english`). Five same-French message pairs with different English were aligned (one
`msgid` each). `docs/ENGLISH-LOCALE.md` says how to install the `.mo` and switch a run.
Open: `SUPERVIS` (and `SUPERVIS2` when `DEBUT` prints first) stays French because it is imported
before `LANG` is applied (ADR-004 point 3, upstream proposal). 3.3 (owner review) still open;
after it, rerun the `english` job so `output_en/` matches the new `.po`.
Decisions: ADR-018 (generated `.po`, own `.mo` writer, `KEEP_FRENCH` for `SUPERVIS2_99` — the
`<I> <FIN> ARRET NORMAL` line `run_aster` counts — and the stage lines `SUPERVIS2_71–75/80`).
Needs owner: nothing blocking; review-queue entry added.
Branch is `claude/project-thread-1mj5vz` (session-assigned).

## 2026-10-29 — 3.2 bulk message translation — agent
Done: every one of the 6,890 messages in 277 families has English (`en` non-null); `caen validate`
green. Token cost: zero (no API calls; the owner's API key was never needed).
- 3.2a (PR #26): free upstream seed, 3,113 messages from upstream's 2016
  `i18n/en-US/aster_messages.po` (`method: machine`).
- 3.2b (PR #27): 992 messages translated in session (`method: assisted`,
  `translation_source: session:task-3.2`, same `check()` as 3.1): SUPERVIS*, UTILITAI*,
  MODELISA*, CALCULEL*, MECANONLINE*, ALGELINE*, FACTOR*, POSTRELE.
- 3.2c (PR #28): 634 for CHARGES*, ELEMENTS*, ELEMENT, MATERIAL*, MESH*, MED*, RESULT*, CHAMPS,
  COMPOR*.
- 3.2d (PR #29): 801 for CALCUL*, CALCCHAMP*, ASSEMBLA, CONTACT*, DISCRETS, POUTRE0, PLATE1,
  SHELL1, MEMBRANE, PIPE1, SOLIDSHELL1, DYNAMIQUE*, DYNALINE*, DYNAPOST, DYNAVISCO, MODAL, SEISME,
  MISS0, DAMPING*, DEFIBASEMODALE1, MODESTAT1, SPECTRAL0, XFEM*, RUPTURE*, THM*, POST0, POSTRCCM,
  POSTROCHE; earlier session entries now say "step index" (glossary: *numéro d'ordre*) and
  "mode shape" (glossary: *mode propre*).
- 3.2e (this PR): the last 1,251 (all other families: JEVEUX*, PREPOST*, ROM*, ALGORITH*,
  DISCRETISATION*, FONCT0, PETSC, ELIMLAGR, ETATINIT, FATIGUE1, HHO*, META1, MFRONT, OAR0,
  PARTITION*, PCOMB, PROJECTION4, SOUSTRUC*, SUBDIVISE, TABLE0, VARC1, VOLUFINI and the rest).
  `VIDE_1` has an empty French text, so its English is the empty string: the validator and
  `check()` now accept an empty `en` only when `fr` is empty (test added).
Totals: 3,113 `machine` (seed) + 3,777 `assisted` (session); none `reviewed`.
Open: 3.3 (owner/engineer review, owner-only `reviewed`); the seed English is literal 2016
Crowdin wording and is the first place to look when a message reads badly.
Decisions: none. Wording choices: "Ce message est un message d'erreur développeur. Contactez
le support technique." = "This is a developer error message. Contact technical support.";
*noeud sommet* / *sommet* = "corner node" (the glossary forbids "vertex"); *variable de
commande* = "external state variable" (as AFFE_VARC); *pilotage* = "continuation control";
*instant de calcul* = "time step"; grid *cellules* in PROJ_CHAMP = "grid boxes" (the glossary
forbids "cell"); *Conseil* = "Advice"; *nappe* = "two-variable function"; *carte* = "map";
*fond de fissure* / *lèvre* = "crack front" / "lip"; *choc* = "impact"; *appui* = "support";
ELU/ELS = "ULS (ELU)" / "SLS (ELS)".
Needs owner: nothing blocking; review queue entry added.

## 2026-10-29 — 4.7 report images — agent
Done: `codeaster_en.report.images` (pyvista off-screen): deformed shape colored by displacement
magnitude over the undeformed edges (largest displacement drawn at 10 % of the model diagonal,
scale in the caption), von Mises from `SIEQ_NOEU` `VMIS`, and one thumbnail per mode for modal
runs. Off by default; `caen report --images` / `Config(images=True)`. `available()` probes
rendering in a child process; without pyvista or an off-screen OpenGL context every figure
becomes a placeholder line with the reason. PNGs in `<report>/images/`, linked from the Markdown,
embedded in the PDF. `run_model.json` gains `images` (`null` unless requested; goldens
regenerated). Optional extra `images` (pyvista, also in `dev`); CI installs `libosmesa6`.
`tests/test_report_images.py` (12 tests): figure plan per fixture, mesh conversion, scale,
placeholders with rendering forced off, CLI flag, real renders of all three fixtures (PNG size,
links, PDF embedding; skipped without OpenGL). Checked the images by eye in session.
Open: shell layers, ELNO/ELGA fields and other components are not drawn; no fixture writes `SIEQ`
on shells, so the shell report has only the deformed shape.
Decisions: ADR-017 (opt-in, subprocess probe, corner-node geometry, 10 % scale, PDF links).
Needs owner: nothing blocking; review queue entry added (look of the figures).

## 2026-10-29 — 4.6 report generator — agent
Done: `codeaster_en.report`: `comm.py` (restricted AST reader of the `.comm` and of the `.mess`
command echo: calls, `_F`, constants, arithmetic, result-object references; nothing executed),
`loads.py` (applied-load resultant summed over the `.rmed` mesh: constant `PRES_REP`,
`FORCE_FACE`, `FORCE_ARETE`, `FORCE_NODALE`; others listed as not evaluated; balance check
with percentage error), `collect.py` (`RunModel`: title block, units, outcome and failure
class, model, materials, element properties, loads and BCs, solution statistics from message
arguments `FACTOR_1`/`ALGELINE7_17`, displacements, stresses or shell resultants per report
group, reactions, modal table, deduplicated English diagnostics, `TEST_RESU` verification,
appendices), `render.py` (Markdown, HTML via Python-Markdown + Jinja2 page with print CSS,
PDF via WeasyPrint), `tripwire.py` (French words outside code). CLI `caen report <job>
[--out] [--section ...] [--logo] [--log] [--no-pdf]` writes `report.md`, `report.html`,
`report.pdf`, `run_model.json`. Failed runs get sections 1-7 and 13 with the failing command,
`.comm` line, fatal message in English, class and the last 50 English log lines.
`tests/test_report.py` (63 tests): golden `report.md` and `run_model.json` for all 7 fixtures
(`tests/golden/report/`), tripwire on every report, balance against the solver's own reaction
sums (both static fixtures < 1e-6 %), load rules on synthetic `.comm` files, PDF when WeasyPrint
is installed, CLI. Glossary: 25 `proposed` entries (element types `TETRA4`..`HEXA27`,
`TEST_RESU` reference types, `SORENSEN`). CI installs Pango for WeasyPrint.
Open: cut lines (REPORT-SPEC item 12; no fixture prints such tables) and images (task 4.7).
2D-model loads, gravity and function loads are not summed (balance flagged partial). Shell
stresses per layer need a fixture that writes `SIEQ` on shells. Regenerating fixtures needs
`UPDATE_GOLDEN=1 pytest tests/test_report.py` (noted in `tests/fixtures/README.md`).
Decisions: ADR-016 (Markdown built in code, Jinja2 page, WeasyPrint optional extra `report`;
loads summed over the result mesh; display round-off threshold; tripwire scope).
Needs owner: nothing blocking; review queue entry added.

## 2026-10-29 — 4.5 results readers — agent
Done: `codeaster_en.results`: `med.py` (native MED reader over `h5py`: mesh, numbering,
families to groups, fields, steps, values on nodes, per element/Gauss point and at element
nodes, profiles), `tables.py` (`IMPR_TABLE` `TABLEAU` files, several tables per file, with or
without `SEPARATEUR`), `labels.py` (glossary labels; stem + axis composition such as
`MASS_EFFE_UN_DZ` -> "effective mass fraction (Z)"), `reader.py` (`results.open(rmed)` ->
`fields()`, `groups()`, `extrema(field, component or tuple for a norm, groups)` with node or
element ID and coordinates, `reactions(groups, tables)` from `REAC_NODA` and `POST_RELEVE_T`
tables, `modal(tables)`: frequency, period, generalized mass, effective mass and fraction per
direction, cumulative sums, total mass). JSON-ready dataclasses. CLI `caen results
fields|extrema|reactions|modal <rmed or output dir> [--json]`. The `modal` fixture now prints
`RECU_TABLE(CO=MODES, NOM_PARA=(FREQ, MASS_GENE, MASS_EFFE_D*, MASS_EFFE_UN_D*))` to
`tables/modal_parameters.csv` (rerun with the ADR-011 image; `DIAGNOSTIC JOB : OK`, frequencies
unchanged). Tested on all three fixtures (`tests/test_results.py`, 26 tests): reader values equal
`VALE_CALC` (centre `DZ`, `MXX`, reaction sums, frequencies to 1e-12); effective mass fractions
of the bending modes match the Euler-Bernoulli cantilever (61.3/18.8/6.5 %) within 1 %
(`hand_values.py`); every nodal value equals `medcoupling`'s; a synthetic element-node field
checks the element path. Fields guide `TODO(verify)` on `MASS_EFFE_*` resolved: `CALC_MODES`
fills them without a request.
Open: the applied-load resultant and the balance percentage (REPORT-SPEC §3 item 10) need the
loads from the `.comm`, so they belong to task 4.6. No fixture writes an element field
(`*_ELNO`/`*_ELGA`) to the `.rmed`; only the synthetic test covers them.
Decisions: ADR-015 (native `h5py` reader; `medcoupling` as a dev-only cross-check; `meshio`
not used). `numpy` and `h5py` are now runtime dependencies. 7 glossary entries `proposed`.
Needs owner: nothing blocking; review queue entry added.

## 2026-10-29 — 4.4 English `.mess` renderer — agent
Done: `codeaster_en.mess.catalog` compiles each French message of `en/messages` into a regular
expression (literal text exact, any whitespace run flexible for `cut_long_lines` wrapping,
centering and boxes; placeholders as captures; repeated placeholders as back-references) and
fills the English with the recovered arguments, numbers re-printed with their original format.
All 6,890 French texts recover their own arguments (round-trip test). `codeaster_en.mess.render`:
boxes joined by `<TYPE> <ID>`, with further messages inside the same box matched too
(`CATAMESS_89` + `CATAMESS_90`); ID-less informational output matched line by line against the
templates (longest match wins); `SUPERVIS2_76` translated where it is nested in another
message's argument; Utmess footers in English; command echo, tracebacks and the trailer kept as
printed. `caen mess translate run.mess [--out-dir] [--messages] [--strict]` writes
`run.en.mess` (same layout, boxes redrawn) and `run.en.json` (diagnostics with status and
arguments, `problems` = English account of what stopped the run with command and `.comm` line,
failure class, coverage). `render_event` renders streamed events. 56 messages that fire in the
fixtures translated in session (`method: assisted`, `translation_source: session:task-4.4`):
`SUPERVIS2` (header and command lines), `SUPERVIS`, `CATAMESS`, `JEVEUX`, `FACTOR`/`FACTOR2`,
`MODELISA7_77`, `MED`, `MESH3`, `MODELE1`, `ALGELINE6/7`, `ARCHIVAGE`. Result: every diagnostic
in all 7 fixture logs renders in English (24/24 boxes); broken runs give e.g. "AFFE_CHAR_MECA
(command file line 33) failed: GROUP_MA EDGE is not part of mesh: 00000001 [error
MODELISA7_77]". `tests/test_mess_render.py` (30 tests), also run by `solver-fixtures.yml`.
Severity label for `A` is now "warning" (glossary: *alarme*), also in the 4.3 events model.
Open: lines printed outside the message catalog (Fortran `WRITE`: mesh statistics, the
end-of-run JEVEUX memory report, `CALC_MODES` tables) stay French and are counted under
`coverage.text_lines.verbatim` (73 of ~265 lines in `broken_missing_group`); a later task could
add a small hand table for the common ones. Task 3.4 must keep `SUPERVIS2_99` out of the `.mo`:
`run_aster/status.py:237` greps its French text to recognize a normal end. Two padded string arguments side by side
(`%(k1)3s %(k2)-20s`) cannot be split exactly when one is empty; the English still reads right.
Decisions: no ADR. English output is `run.en.json` (not `run.json`) so it never overwrites the
4.3 parser's JSON. `tests/test_messages_extract.py` CLI test now starts from the committed
`CATAMESS` file, since that family has English now.
Needs owner: nothing blocking; review queue entry added.

## 2026-10-29 — 4.3 `.mess` log parser — agent
Done: `codeaster_en.mess` (`events.py`, `parser.py`, `log.py`, `commlines.py`, `classify.py`)
and `caen mess parse <run.mess> [--out run.json]`. One pass with a few lines of look-ahead turns
a log into events: `runner`, `header`, `stage` / `stage_end` (command number, command, concept,
line, result type, CPU/elapsed, memory), `diagnostic` (`<TYPE> <FAMILY_N>` boxes: severity, ID,
body, Utmess footer split off, `repeat` for copies re-printed in tracebacks), `notice`, `table`
(`TEST_RESU` rows, `CALC_MODES` frequencies, end-of-run timings), `traceback`, `summary`
(`DIAGNOSTIC JOB`), and `text` / `blank` as the verbatim fallback. Every line lands in exactly
one event (tested on all 7 logs). Stage and traceback lines are mapped back to the user's
`.comm` (`run_aster` runs `run.comm.changed.py`, 12 lines longer after `DEBUT`).
`stream(path)` follows a growing log and stops after the trailer. `classify(log)` gives the
CLEARFEA-INTEGRATION §5 class; rules keyed by message ID (`MODELISA7_77`, `FACTOR_11`,
`SUPERVIS_4`) then by `run_aster` diagnostic. Four broken-run fixtures run with the ADR-011
image (`broken_missing_group`, `broken_singular_matrix`, `broken_bad_keyword`, and
`broken_python_syntax` as a fourth), see `tests/fixtures/README.md`. `tests/test_mess.py`
(45 tests); `solver-fixtures.yml` now also runs it on regenerated logs.
Open: task 4.4 (English renderer, argument recovery, `caen mess translate`). Nonlinear
convergence tables are not parsed (no nonlinear fixture; they fall back to `text`). The
`user-resources` and `platform` rules come from `run_aster/status.py`, not from a run
(`TODO(verify)` in `classify.py`). Plain informational solver output has no ID, so it stays
`text`; 4.4 must match it against `I` message templates.
Decisions: no ADR. The fallback event is called `text` rather than `unknown`: in a normal log most
unclassified lines are the solver's own ID-less informational output, not unknown content.
`ARRET NORMAL` is reported as `closed_normally`, not success: `FIN` closes the base even after
an exception (seen in two broken runs). A box seen again with the same severity, ID and body is
flagged `repeat` and left out of `errors`.
Needs owner: nothing blocking; review queue entry added.

## 2026-10-29 — 3.1 message translation tool — agent
Done: `caen translate messages` (`tools/codeaster_en/translate/messages.py`, `po.py`): optional
seed from upstream's `i18n/en-US/aster_messages.po` (verbatim `msgid` only, same checks as a
model answer), batched requests with the rules and `term`/`abbrev` glossary in a cached system
prompt and the matching `command`/`keyword`/`value`/`concept` entries per batch, JSON-schema
output, placeholder and forbidden-synonym checks with re-asks of failed items only, severity
hint from the French wording, dry-run token/cost estimate, atomic write per batch (resumable),
`--force` that never touches `reviewed`. Backends: Claude API (`claude-opus-5-5`, effort
`medium`, server-side refusal fallback; optional extra `tools[llm]`) and a JSON Lines replay
(`--export-requests` / `--responses`) for in-session work and tests. End-to-end family:
`MODELISA8`, 43/43 messages translated in session through export/import, 0 placeholder or
glossary failures, `method: assisted`, `translation_source: session:task-3.1`; 2 proposed
glossary entries (`mot-clé facteur`, `fibre`). `tests/test_translate_messages.py` (30 tests,
no network) incl. a check that `MODELISA8` is complete and valid. TRANSLATION-GUIDE §6
rewritten to match. Dry run, all 277 families: 506 requests, ~2.5 M input / ~0.4 M output
tokens, ~$17 with Opus 5.5 (~$12 after the seed); thinking tokens not included.
Open: task 3.2 (bulk). The seed fills 3,130 messages for free (3,221 verbatim matches, 91
rejected by the checks, mostly "cell" for *maille*); the remaining ~3,700 need either the
owner's API key and budget approval, or in-session translation family by family via the
replay path. The Claude backend has not been called for real (no key in session); its
request shape is unit-tested against the installed `anthropic` 2.3.0 signature.
Decisions: ADR-014. The guide's "temperature 0" is dropped (sampling parameters are removed
from the current API); the schema and the checks give determinism where it matters.
`MODELISA8_53` French looks truncated ("n3 colinéaires"), noted in the file. A stray remote
branch `task/3-1-translate-messages` (same commit, pushed by mistake before switching to the
session branch) could not be deleted from the sandbox.
Needs owner: nothing blocking; review queue entry added. Bulk model run in 3.2 needs budget.

## 2026-10-29 — 2.5 fields and components guide — agent
Done: `en/guide/fields.md` (`status: assisted`): how a result is organized (result → step →
field → component), field-name grammar (quantity prefixes, location suffixes), how `NOEU` is
averaged (plain arithmetic mean of `ELNO`, `cescns.F90:70`; shells with layers excluded,
`UTILITAI_3` / `CALCULEL4_16`; local-axes check `UTILITAI_4`), `EVOL_ELAS` and `MODE_MECA`
(stored fields, access parameters, mode parameters from `vpstor.F90`, MED field naming), a field
summary table (label, option, applies to, units, catalog line), then displacement, stress,
equivalent stress (formulas from `fgequi.F90`: `PRIN_*` sorted increasing, `TRESCA`, `VMIS_SG`,
`TRSIG`, `TRIAX`), strain (tensor shear, `eps1mc.F90:96`), shell and beam resultants, nodal
forces and reactions (components are DOF names; sign from fixtures), energy, and a default
"what to report" table for task 4.6. Glossary: 59 new `proposed` entries (5 abbreviations, 13
fields, 35 components, 6 modal parameters); `PRIN_1`/`PRIN_2`/`PRIN_3` and `REAC_NODA` notes now
cite source and drop their `TODO(verify)`. Drafts regenerated: `MACR_LIGN_COUPE.md` gained the
`NUME_MODE` term. `tests/test_guide.py`: labels in `fields.md` tables equal the glossary `en`
(≥ 75 checked), field summary lines point at `c_nom_cham_into.py`. Synonym scan now skips
Markdown link targets (file names such as `modelisations.md`), with a test. Self-review:
citations re-printed and checked by the test; 9 `TODO(verify)`.
Open: owner review (PLAN acceptance, queued). Phase 2 is complete once this merges; next ready
task per PLAN.
Decisions: none (no ADR). Choices: one glossary term per component, field-specific meaning in
the note (`DX` is "X translation"; reports label `REAC_NODA/DX` "Reaction force, X" per
REPORT-SPEC §4); shell results reported from `EFGE_*` until `POST_CHAMP` is in scope.
Needs owner: nothing blocking; review queue entry added.

## 2026-10-29 — 2.4 modelisations guide — agent
Done: `en/guide/modelisations.md` (`status: assisted`), the first file in `en/guide/`. Covers
`3D`, `3D_SI`, `DKT`, `DST`, `COQUE_3D`, `C_PLAN`, `D_PLAN`, `AXIS`, `POU_D_T` (+ `POU_D_E`,
`DIS_T`/`DIS_TR` as alternatives): summary table (element types, DOFs, `AFFE_CARA_ELEM` data,
outputs, catalog line), a ClearFEA selection procedure and builder defaults, one section per
modeling with "pick it when" and pitfalls, and mixing modeling types (`LIAISON_ELEM`).
Evidence: `phenomenons_modelisations.py`, element catalogs (`DDL_MECA` of each), `porigi.F90` /
`ptka01.F90` (Timoshenko vs Euler: shear coefficients zeroed), `dmatmc.F90` (plane stress vs
plane strain Hooke matrix), `dstb.F90`, `aceaor.F90`, messages, astest, our three fixtures.
New `tests/test_guide.py`: every cited `path:line` exists, summary table values are real
`MODELISATION` values and its line numbers point at the catalog entries. Glossary: 5 new
`proposed` entries (`POUTRE`, `FORCE_POUTRE`, `FORCE_COQUE`, `FORCE_CONTOUR`, `LIAISON_ELEM`);
drafts regenerated, none changed. Self-review: citations re-printed; 9 `TODO(verify)`.
Open: owner review (PLAN acceptance); 2.5 fields guide is next.
Decisions: ADR-013 (default modeling type per ClearFEA body kind; beams and mixed models wait
for COMMAND-SET scope). Findings: beams (`AFFE_CARA_ELEM` `POUTRE`/`ORIENTATION`,
`FORCE_POUTRE`) and `LIAISON_ELEM` are not in COMMAND-SET Tier 1/2 although PLAN 2.4 names
`POU_D_T`; queued. `AXIS` reactions are per radian (`ssna111a.comm:94`).
Needs owner: nothing blocking; review queue entry added.

## 2026-10-29 — 2.3d solver and post-processing references (MECA_STATIQUE, CALC_CHAMP, POST_RELEVE_T, POST_ELEM, CREA_CHAMP, IMPR_RESU, IMPR_TABLE, DEBUT/FIN, TEST_RESU) — agent
Done: the ten 2.2 drafts rewritten as full references, `status: assisted`, batch (a)-(c)
format: purpose paragraph, every keyword row with meaning and "when to use", patterns from
astest and our fixtures cited file:line, what the solver does, pitfalls with message IDs.
Evidence: catalogs, `CodeCommands/` and `MacroCommands/` Python (`debut.py`, `fin.py`,
`calc_champ`, `impr_table_ops`, `TestResult`), Fortran (`op0107`, `op0195`, `irmfac`, `trresu`,
`penorm`, `pemain`, `rvmima`, ...), message texts. Self-review: every file:line citation
re-printed and checked; 54 `TODO(verify)` left. Generator fix: `_literal` now escapes control
characters (the `IMPR_TABLE` `FIN_LIGNE` default `"\n"` split its draft row), with a test; the
`IMPR_TABLE` draft regenerated. Glossary: 7 new `proposed` entries (`TOUT_ORDRE`, `CHAM_UTIL`,
`RENUM`, `NPREC`, `ELIM_LAGR`, `STOP_SINGULIER`, `PCENT_PIVOT`), 390 entries total. ruff,
pytest (251 passed), `caen validate` green (24 references).
Open: 2.3 is complete. Next ready: 2.4 modelisations guide (`en/guide/modelisations.md`).
Decisions: none (no ADR).
Needs owner: nothing blocking; review items in OWNER-REVIEW-QUEUE (PLAN 2.3 owner review of
`CALC_CHAMP`; catalog, message and COMMAND-SET issues; glossary `CRITERE` context).
Branch is `claude/project-thread-wfqlrx` (session-assigned).

## 2026-10-29 — 2.3c loads and functions references (AFFE_CHAR_MECA, AFFE_CHAR_CINE, DEFI_FONCTION) — agent
Done: the three 2.2 drafts rewritten as full references, `status: assisted`, batch (a)/(b)
format: purpose paragraph, every keyword row with meaning and "when to use" (the 100+ exotic
`DDL_IMPO` components grouped into multi-keyword rows using the `DEPL_R` catalog comment),
patterns from astest and our fixtures cited file:line (13 / 5 / 6), what the solver does with the
load (order in `charme.F90`, sign conventions), pitfalls with message IDs. Evidence: catalogs,
`CodeCommands/defi_fonction.py`, Fortran (`charme`, `caddli`, `cafaci`, `cafono`, `capesa`,
`carota`, `caliso`, `carbe3`, `chveno`, `LoadKinematic_module`, `charci`, `chcsur`, `op0003`,
`fointr`, `te0014`, `te0015`), message texts. Self-review: every file:line citation re-printed
and checked; 18 `TODO(verify)` left. Glossary: 14 new `proposed` entries (`VERI_AFFE`,
`VERI_NORM`, `DOUBLE_LAGRANGE`, `BLOCAGE`, `COEF_MULT`, `COEF_IMPO`, `DISTANCE_MAX`, `DIST_MIN`,
`ELIM_MULT`, `EVOL_IMPO`, `VALE_PARA`, `VALE_FONC`, `NOEUD_PARA`, `CISA_2D`), kept generic where
the keyword recurs in other commands (`DNOR`/`DTAN` left out: they mean a normal vector in
`MACR_LIGN_COUPE`); `VITESSE` units TODO resolved. Machine drafts regenerated (`CALC_CHAMP`,
`MACR_LIGN_COUPE`, `POST_ELEM` gain the new terms). ruff, pytest (250 passed), `caen validate` green.
Findings for later tasks: pressure is positive against the outward normal; `FORCE_NODALE` on a
group applies the full value at each node; `AFFE_CHAR_CINE` silently skips missing DOFs;
`UTILITAI2_67` text says triplets for pairs; spatially varying pressure needs `AFFE_CHAR_MECA_F`
(the COMMAND-SET "Hydrostatic" row also lists `FONC_MULT`; queued for the owner).
Open: 2.3 batch (d) `MECA_STATIQUE`, `CALC_CHAMP`, `POST_RELEVE_T`, `POST_ELEM`, `CREA_CHAMP`,
`IMPR_RESU`, `IMPR_TABLE`, `DEBUT`/`FIN`, `TEST_RESU`.
Decisions: none (no ADR).
Needs owner: nothing blocking; review items in OWNER-REVIEW-QUEUE (PLAN 2.3 owner review of
`AFFE_CHAR_MECA`; glossary `CENTRE` and COMMAND-SET corrections).
Branch is `claude/project-thread-geqwlq` (session-assigned).

## 2026-10-29 — 2.3b model and material references (AFFE_MODELE, DEFI_MATERIAU, AFFE_MATERIAU, AFFE_CARA_ELEM) — agent
Done: the four 2.2 drafts rewritten as full references, `status: assisted`, batch (a) format:
purpose paragraph, every keyword row with meaning and "when to use", 5–7 patterns each from
astest or our fixtures (cited file:line, incl. `.mess` excerpts of the assignment summary and
filled-in defaults), solver-side checks, pitfalls with message IDs. AFFE_MODELE gets a table of
the Tier 1 modelings (meaning, accepted element types, use); AFFE_CARA_ELEM a table of the
`DISCRET` `CARA` codes and `VALE` counts. Evidence: catalogs, `CodeCommands/affe_modele.py`,
`defi_materiau.py`, `affe_cara_elem.py`, `MacroCommands/affe_materiau_ops.py`, the Fortran
(`op0018`/`modelCheck*`, `op0006`/`rcmate`, `op0019`/`aceaco`/`aceadi`/`ace_verif_affe`, element
routines `te0121`, `coqrep`, `dxtloc`, `dxmate`, `alfint`, `verift`), message texts and the
fixture logs. Self-review: every claim re-checked against its source; 20 `TODO(verify)` left,
mostly options outside Tier 1 use. Glossary: 7 new `proposed` entries (`AMOR_ALPHA`, `AMOR_BETA`,
`TEMP_DEF_ALPHA`, `A_CIS`, `COEF_RIGI_DRZ`, `EXCENTREMENT`, `VERI_JACOBIEN`); `3D_SI` English
corrected to "reduced integration" (catalog: "Sub-integrated"). Machine drafts regenerated
(unchanged). ruff, pytest (250 passed), `caen validate` green.
Findings for later tasks: `AMOR_ALPHA` is the stiffness coefficient, `AMOR_BETA` the mass one
(reverse of C = αM + βK); default shell local x is the projection of global X, fatal
`PLATE1_40` on shells normal to X; `AFFE_CARA_ELEM` stops if the model has shells/discretes
and their keyword is missing (`AFFECARAELEM_32/33`); missing material or shell data is only
caught in the analysis (`CALCUL_20`, `CALCUL_21`) — useful for the 3.x message renderer and
for ClearFEA pre-checks.
Open: 2.3 batch (c) `AFFE_CHAR_MECA`, `AFFE_CHAR_CINE`, `DEFI_FONCTION`.
Decisions: none (no ADR).
Needs owner: nothing blocking; review items in OWNER-REVIEW-QUEUE (PLAN 2.3 owner review of
`AFFE_MODELE` and `AFFE_CARA_ELEM`).
Branch is `claude/project-thread-ji2j0p` (session-assigned).

## 2026-10-29 — 2.3a mesh command references (LIRE_MAILLAGE, MODI_MAILLAGE, DEFI_GROUP, CREA_MAILLAGE) — agent
Done: the four 2.2 drafts rewritten as full references, `status: assisted`: purpose paragraph,
every keyword row with meaning and "when to use", the order in which the solver applies the
keywords (DEFI_GROUP, MODI_MAILLAGE), 4–7 patterns each lifted from astest or our fixtures
(cited file:line, incl. `.mess` excerpts), and pitfalls. Evidence: catalogs, the
`CodeCommands/*.py` implementations, the Fortran they call (`op0001`/`chckma`, `op0104`/
`sscgma`/`sscgno`, `op0154`/`orilgm`/`mesh_modification_module`, `op0167`/`rdtmai`/`cmcovo`/
`crea_maillage_module`), message texts (`en/messages/*.en.json`, French) and the fixture logs.
Self-review (PLAN.md acceptance, ADR-010): every claim re-checked against its cited source;
claims with no source are `TODO(verify)` (11 in total, mostly joint, solid-shell and beam-section options
outside Tier 1 use). Glossary: 9 new entries (`proposed`: `DETR_GROUP_MA`, `DETR_GROUP_NO`,
`CREA_POI1`, `RESTREINT`, `APLAT`, `GROUP_MA_PEAU`, `GROUP_MA_INTERNE`, `NOEUD_QUART`,
`ABSC_CURV`); the `TODO(verify)` notes of `VERI_MAIL` (APLAT) and `DIFFE` resolved from source.
Machine drafts regenerated (unchanged). ruff, pytest (250 passed), `caen validate` green.
Findings for later tasks: `DEFI_GROUP` and `MODI_MAILLAGE` always return their input mesh
(in place, even without `reuse=`); `DEFI_GROUP CREA_GROUP_MA TYPE_MAILLE` that matches nothing
creates the group unfiltered while warning that it is empty (looks like an upstream bug, listed
in OWNER-REVIEW-QUEUE); `AFFE_CHAR_MECA` checks `PRES_REP`/`FACE_IMPO`/`EFFE_FOND` normals
(`chveno.F90`) — relevant to 2.3c; `CREA_MAILLAGE RESTREINT` drops node groups by default.
Open: 2.3 batch (b) `AFFE_MODELE`, `DEFI_MATERIAU`, `AFFE_MATERIAU`, `AFFE_CARA_ELEM`.
Decisions: none (no ADR). Fixture files are cited as pattern sources alongside astest.
Needs owner: nothing blocking; review items in OWNER-REVIEW-QUEUE.
Branch is `claude/project-thread-64a5ae` (session-assigned).

## 2026-10-29 — 2.2 command reference draft generator — agent
Done: `caen translate command [CMD...] [--tier N] [--all-keywords] [--force]
[--list-untranslated]` (`tools/codeaster_en/translate/command.py`, template
`translate/templates/command.md.j2`, new dependency `jinja2`). Drafts for all 24 Tier 1 commands
that have a catalog were generated in one run (`--tier 1`) and committed as
`en/commands/<CMD>.md`, `status: machine`: front matter with provenance (upstream tag, commit,
catalog file:line, doc ID, examples), a facts table (result type, `reuse=`, tier, key
keywords), a keyword table (1,401 rows: type/cardinality, default, allowed values, bloc
conditions, glossary English, translated `fr=` help, `TODO(2.3)` for meaning/when to use), the
catalog rules in English (semantics from `Cata/Language/Rules.py`), up to two calls lifted
verbatim from astest and three linked cases (simplest Tier-1-only sequential cases, one per
family, `erreu*` error tests excluded). New `en/catalog-help.yaml`: 220 `fr=` strings
translated in-session (`method: machine`), which covers every string the Tier 1 drafts show.
New `en/doc-ids.yaml`: Tier 1 U4 IDs (`proposed`; the catalog's `docu=` wins, e.g.
POST_RELEVE_T U4.81.21). The synonym scan now skips French quoted in `«…»`. New
`tests/test_translate_command.py` (18 tests: snapshot of the machine drafts, Tier 1 coverage, data
files, table scope, rules, overwrite guard, snippet extraction, example ranking, CLI).
Self-review: re-read the AFFE_MODELE, LIRE_MAILLAGE, MECA_STATIQUE and DEFI_MATERIAU drafts
against their `.json`; types, defaults, conditions and rules match the catalog.
Open: `POURSUITE` has no catalog, so no draft (2.3 covers it in `DEBUT.md`). 675 rows still say
`TODO(2.3): meaning` (keyword without glossary entry or `fr=` string); 2.3 writes them.
Decisions: ADR-012 (drafts in place with a status guard; in-session translation memory instead
of a paid LLM call; COMMAND-SET key keywords bound the table for commands with more than 150
keyword paths; doc IDs from `docu=` then `en/doc-ids.yaml`). Branch is
`claude/project-thread-pssseb` (session-assigned).
Needs owner: nothing blocking. Queue: confirm the U4 IDs (PLAN.md says U4.81.01 for IMPR_RESU,
`en/doc-ids.yaml` says U4.91.01) and spot-check the RCC-M help translations.

## 2026-10-29 — 2.1 glossary pass 1 — agent
Done: every non-value entry of `en/glossary.yaml` now has a `note` (164 added: 23 terms, 36
commands, 81 keywords, 24 concepts), drafted from the catalog `fr=` strings, allowed values and
defaults in `en/commands/*.json`, and, for result components, the comments in
`upstream/catalo/cataelem/Commons/physical_quantities.py` (VMIS_SG) and
`code_aster/MacroCommands/Modal/post_mode_ops.py` (MASS_EFFE_UN). All 353 entries moved from
`proposed` to `machine`. New test `test_entries_have_notes_except_values` keeps the note rule.
Self-review: each claim about a keyword's sub-keywords, values or defaults was re-checked against
the catalog JSON; no `en` value changed.
Open: 12 entries carry `TODO(verify)` that needs the U4 docs (not in the sandbox): DIFFE,
VALE_REF, RESI_RELA, VOLUMOGRAMME, PM_PB, VITESSE (from 0.6) and VERI_MAIL (APLAT), REAC_NODA
(exact definition), PRIN_1/PRIN_3 (ordering), LONG_CARA, COEF_AMOR (new). Listed in the owner
review queue.
Decisions: none (no ADR). Branch is `claude/project-thread-4lglpc` (session-assigned). Status `machine` is used for agent-drafted entries as PLAN.md 2.1
asks; entries added later still start as `proposed`.
Needs owner: nothing blocking.

## 2026-10-29 — 4.2 run fixtures, commit outputs, solver-fixtures Action — agent
Done: ran all three fixtures in-session with Docker and committed `tests/fixtures/*/output/`
(`run.mess`, `run.rmed`, `run.resu` (empty), `tables/*.csv`, `exit_code`, `run_aster.stdout`,
new `provenance.json`). All three jobs end `DIAGNOSTIC JOB : OK`, every `TEST_RESU` is `OK`
(errors vs hand values: 0.00007 % reaction, 0.007 % / 0.16 % plate, 0.01–1.15 % frequencies).
`VALE_CALC` = solver values, `TOLE_MACHINE` and `VALE_ABS` removed; signs confirmed (reaction
sums +X / +Z, plate MXX negative) and propagated to `run.json` and `hand_values.py`. New
`CONTAINER_IMAGE` (digest-pinned) read by `run-fixture.sh` (now runs as the caller's uid, wipes
`output/` first, writes provenance), `session-start.sh`, and new
`.github/workflows/solver-fixtures.yml` (verify on PRs touching inputs/image/pin; on dispatch,
commit regenerated outputs to a branch and open a PR). New `tests/test_fixture_outputs.py`
(clean exit, no printed alarm, all TEST_RESU OK, VALE_CALC = run.mess values, MED fields,
tables, provenance). Each run takes under 10 s.
Open: `LANG='EN'` fixture variant moves to task 3.4 (needs our `.mo`). The cloud environment still
sets `CODEASTER_IMAGE=codeastersolver/codeaster-seq:latest` and its setup script pulls that
dead image; nothing reads the variable now (owner queue).
Decisions: ADR-011 (fixture image `simvia/code_aster:17.4.22`: no 17.4.26 image exists,
`codeastersolver/codeaster-seq` stopped at 14.4.0, building is rule 8; 17.4.22 → 17.4.26 diff is
52 files, none on fixture code paths). ADR-004 point 5 resolved: the image ships no `.mo`;
`profile.sh` overrides `ASTER_LOCALEDIR`, so the `.mo` must be mounted at
`<install>/share/locale/aster`; with that plus `DEBUT(LANG='EN')` a probe `.mo` turned a
Fortran-emitted alarm English in `run.mess`. `shell_static`: Gmsh point groups are POI1 cells
and trip alarm `MODELISA8_14`; `IGNORE_ALARM` does not work together with
`ERREUR=_F(ALARME="EXCEPTION")` (Utmess raises the alarm to an error first), so that case uses
`IGNORE_ALARM` only; the test rejects any other printed alarm. `run_aster` resolves
`../output/` relative to the export (TODO from 4.1 closed).
Needs owner: nothing blocking (queue: image choice, environment variable cleanup).

## 2026-10-29 — 0.6 glossary seed — agent
Done: `en/glossary.yaml` 250 → 353 entries, all `proposed`. (1) Every Tier 1/2 identifier in
`docs/COMMAND-SET.md` that had no entry (70: 5 commands, 51 keywords, 13 values, 1 concept), each
with `source` (upstream catalog file:line at 17.4.26), English drafted from the catalog `fr=`
strings and allowed values; uncertain wording marked TODO(verify). (2) AsterStudy `GLOBAL_DICT`
(82 keys; Copyright 2016 EDF R&D, GPL-3; copy from github.com/simvia-tech/vs-code-aster, fetched
2026-10-26, sha256 in the glossary section header): 49 keys already had entries — our `en` kept,
AsterStudy's English recorded verbatim in a new `asterstudy` field; 33 new entries added, English
normalized to CLAUDE.md §5 style. `BANDE` broadened from "frequency band" to "band" (also a
DEFI_GROUP geometric option). Narrowed aliases_en that are everyday English words (reference,
frame, link, connection, filename, affect, loading, criteria, excitation, characteristics,
instant) so the forbidden-synonym scan does not flag correct prose. New
`tests/test_glossary_coverage.py` (Tier 1/2 coverage; `source` lines resolve). `source` and
`asterstudy` fields documented in ARCHITECTURE §4.1.
Open: none for 0.6.
Decisions: none. Not added: message-family names (task 1.3) and COMMAND-SET's out-of-scope items.
Findings: `SPHERE`/`BANDE` are values of `CREA_GROUP_MA/NO` `OPTION`; `MASS_EFFE_UN` is a
`CRIT_EXTR` value; GLOBAL_DICT's `SANS_MAILLE`/`SANS_NOEUD` are absent from 17.4.26; the owner's
upload was a corporate-proxy block page, so the file was fetched from the URL it named.
Needs owner: nothing blocking (ADR-010; merged on green CI). Review items queued in
`docs/OWNER-REVIEW-QUEUE.md`: AFFE_VARC/NOM_VARC ("external state variable" vs upstream's
"command variable"), the TODO(verify) entries, BANDE, and GLOBAL_DICT disagreements.
Phase 0 "done when" met: clone + submodule, `pip install -e tools[dev]`, pytest and
`caen validate` all pass in the cloud sandbox.

## 2026-10-29 — ops: switch to full autodrive — agent
Done: ADR-010 (owner's instruction, 2026-10-29). Updated `docs/cloud/PROJECT-INSTRUCTIONS.md`
(serial threads, self-merge on green CI, agent-made decisions, short stop list), `CLAUDE.md` §3
(session routine step 6, "When to stop and ask"), `docs/PLAN.md` (autodrive note on owner-review
criteria), `docs/SESSION-PROMPTS.md`, `docs/cloud/CLOUD-SETUP.md` (E2 and Part G superseded).
Added `docs/OWNER-REVIEW-QUEUE.md` for asynchronous, non-blocking owner review and owner-only inputs.
Open: PR #3 (0.6 glossary seed) is open with `needs-engineer-review`; under ADR-010 it is merged
once CI is green.
Decisions: ADR-010.
Needs owner: nothing blocking; see `docs/OWNER-REVIEW-QUEUE.md`.


## 2026-10-23 — 1.5 inventory report — agent
Done: `caen extract inventory` (`tools/codeaster_en/extract/inventory.py`) writes §7 of
`docs/INVENTORY.md` between marker comments from `en/commands/`, `en/messages/`,
`en/astest-index.json` and `docs/COMMAND-SET.md` (no upstream access): totals; every Tier
1/2/3 command with catalog kind, keyword/`fr=`/bloc counts, astest cases, calls and rank; each
"key keyword" in COMMAND-SET checked against the row's catalog (187 of 190 found); the Tier 1
"Likely" message families; messages that reference Tier 1/2 commands (family-name and
mention heuristics); top 50 commands across astest. §8 (hand-written) lists 8 proposals for the
COMMAND-SET revision. `tests/test_inventory.py` (9 tests) fails when §7 is stale.
Open: owner to decide the §8 proposals (COMMAND-SET.md not edited). Built on PR #2 (0.4),
which creates `docs/INVENTORY.md`. CI pin check fixed separately in PR #9 (`ls-remote`).
Decisions: none (no ADR). Choices: commands ranked by number of test cases, then calls.
COMMAND-SET rows are parsed by backtick spans; a key keyword is "found" if it is a keyword
name, an `into=` value, or a command of the row.
Needs owner: §8 — `CALC_MODES` has no `MODELE` form in 17.4.26; `FONC_MULT` belongs to
`MECA_STATIQUE/EXCIT`, not the hydrostatic load; `CALC_EUROPLEXUS` and family `MECASTATIQUE`
do not exist; candidates to add: `FORMULE`, `TEST_TABLE`, `DEFI_LIST_REEL` (Tier 1),
`CALC_TABLE`, `CREA_TABLE` (Tier 2). With 1.5, every Phase 1 task is done.

## 2026-10-23 — 1.4 astest index — agent
Done: `caen extract astest-index` (`tools/codeaster_en/extract/astest.py`) writes
`en/astest-index.json` (schema `docs/schemas/astest-index.schema.json`). A test case is one
`astest/<name>.export` (4,496); its `F comm` lines name 4,708 distinct command files (`.comm`,
`.com0`–`.com3`, 259 `.py` scripts, 2 `.2`). Every file parses with `ast` (a regex fallback,
marked `parse: "regex"`, exists but is unused in 17.4.26). Each `NAME(...)` call to a known command
is recorded with its line numbers, per file, so 2.x references can cite `ssls101a.comm:47`.
Index has both directions: `commands` (name → source, total calls, test cases; every known
command listed, used or not) and `testcases` (commands, command files, `P` params with
time/memory/ncpus/mpi_nbcpu/testlist, `parallel`, `A` args, every `F`/`R` file line). Known
commands = the 268 catalog commands + `POURSUITE` (exported by `CodeCommands/__init__.py`, runs
DEBUT's catalog) + 11 `UserMacro` definitions not in `Cata/Commands` (e.g. `DEFI_CONT`,
57 cases). 279 of 280 are used; only `MACRO_AC_PERMUTE` has no test case, so every catalog
command has at least one example. 320 cases are `parallel`. Spot-checked by hand with `grep`
against the upstream files: `ssls101a` (DKT shell), `sdll100a` (dynamics), `adlv101a`
(`.comm` + `.com1` with POURSUITE), `cont001b` (`.py` script, DEFI_CONT), `zzzz100g`
(calls inside a comment/string and a test-local `UserMacro` correctly not counted). All
five are pinned in `tests/test_astest_index.py`, plus a byte-for-byte snapshot and schema test.
Open: Python modules imported by a command file (`F nom`/`F libr`) are not followed, so
commands called only inside them are missed. `CO(...)` is not a command and is not counted.
Decisions: none (no ADR). Choices: the catalog offers no `.comm` parser that runs without the
solver, so `ast` is the primary method. Calls through an attribute (`table.EXTR_TABLE()`) are
methods and are skipped. `commands` and `testcases` entries are written one per line (6.2 MB
instead of 9.7 MB with full indentation), so an upstream bump diffs per test case. Re-run this
extractor after `caen extract catalog`, since known commands come from `en/commands/*.json`.
Needs owner: nothing.

## 2026-10-23 — 1.3 + 1.6 messages extractor and validator — agent
Done: `caen extract messages` (`tools/codeaster_en/extract/messages.py`) parses every
`upstream/code_aster/Messages/<family>.py` with `ast` and writes `en/messages/<FAMILY>.en.json`
(277 families, 6,890 messages, all `en: null`; schema `docs/schemas/messages.schema.json`).
Each message keeps `fr` verbatim, its distinct `placeholders`, source line, and when they
apply: `flags` (41 dict-form messages), `gettext: false` (15 unwrapped + the 2 f-strings
`POST0_55/56`, whose module constant is substituted and named in `fstring_names`) and
`reachable: false` (the 4 numbered ≥ 100). Re-extraction keeps translation fields
(`en`, `method`, `severity_hint`, `translation_source`, `reviewed_by`, `reviewed_on`, `note`)
and marks a translated message `stale: true` when its French changed. Placeholder parser
`codeaster_en/placeholders.py` follows Python's printf grammar, so it accepts all 51 INVENTORY
formats and `%%`, and reports stray `%`, unnamed conversions and `*`. `caen validate` now runs
four rules: glossary (unchanged), messages (ids, placeholder list matches `fr`, fr↔en
placeholder set equality, `method` set and reviewer/date when `reviewed`), synonyms
(`aliases_en` scan over `en/**/*.md`), commands (`.md` keyword-table rows ⊆ `.json` keyword
paths; `.json` sibling and front-matter `command:` checked). CI already ran `caen validate`, so
the rules are wired in with no `ci.yml` change. Tests: `test_placeholders.py`,
`test_messages_extract.py` (counts, hand checks, byte-for-byte snapshots, schema, merge),
`test_validate.py` with `tests/validate_fixtures/{good,broken}` (broken trips every rule).
Open: none for 1.3/1.6. ARCHITECTURE.md §4.3's example predates the schema; the schema wins
(not edited here to avoid conflicting with PR #2).
Decisions: none (no ADR). Choices: fr↔en equality is on the **set** of specifiers, each
character for character; order and repeat count may change (TRANSLATION-GUIDE §3.1 "reorder…
never rename, drop, or add"). The synonym scan skips code spans/fences and all-caps matches
(French identifiers), counts plurals, and honours a per-line `<!-- caen-allow: word -->`.
Bloc paths (`AFFE/[b_x]`) are not accepted as keywords. Count differences from INVENTORY §2 are
explained, not errors: its regex needed a digit in the key, so it missed 5 `%(ktout)s`
(`Utmess.py:229`, all strings joined), and it skipped the f-strings (3 more `%(kN)s`).
Needs owner: several glossary `aliases_en` are ordinary English words (`reference`, `link`,
`connection`, `frame`, `filename`, `instant`, `criteria`); scanned over the current `docs/` they
give 42 hits, mostly "reference(s)". Once `en/commands/*.md` exist they will fail the build
unless the aliases are narrowed (e.g. `reference frame`) or lines use `caen-allow`. Branch is
`claude/project-thread-noz4t1` (session-assigned); a stray `task/1-3-messages-extract` branch
could not be deleted from the sandbox.

## 2026-10-23 — 1.2 catalog extractor — agent
Done: `caen extract catalog` (`tools/codeaster_en/extract/catalog.py`) writes
`en/commands/<CMD>.json` for all 268 commands (135 OPER, 116 MACRO, 16 PROC, 1 FORM; `VARIABLE`
skipped). It **imports** the catalog (no solver needed, as 0.4 found); no AST fallback. Source
file and line come from wrapping `PartOfSyntax.__init__` before the import and reading the
caller's frame, so every command, keyword and bloc (21,764 objects) has a line, including the
ones built by `Cata/Commons/` factories (their source is the Commons file). The import runs in
a child interpreter with `-B` and `PYTHONHASHSEED=0`. Schema: `docs/schemas/command.schema.json`.
Counts match INVENTORY §1 (17,595 SIMP, 1,322 FACT, 2,847 BLOC, 258 commands with `fr=`).
`tests/test_catalog.py`: fresh extraction must equal every committed file, all files validate
against the schema, snapshot + hand checks against the source for AFFE_MODELE, DEFI_MATERIAU,
MECA_STATIQUE, nothing is written under `upstream/`. Output is identical on Python 3.11 and 3.13.
Open: none for 1.2. Task 1.6 (`caen validate`) can use `catalog.iter_keywords` and `path`.
Decisions: none (no ADR). Choices, all documented in the schema: a keyword `path` is what the
user writes (`AFFE/MODELISATION`); blocs add no segment and get their own path `AFFE/[b_name]`.
Optional fields are emitted only when the catalog sets them; the checker's defaults (`max`=1,
`statut`=`f`) are stated in the schema with their upstream source, not filled in. Arguments the
extractor does not interpret go to `other` verbatim. Upstream's own English labels
(`translation=` on 14 commands) are kept as `translation_upstream` (data only; glossary wins).
`PYTHONHASHSEED=0` because `Commons/c_nom_cham_into.py:594` builds `into=` with
`tuple(set(...))`, whose order otherwise changes per run.
Needs owner: possible upstream contribution (not filed): catalog typos the syntax checker
ignores — `default=` instead of `defaut=` (6 SIMP: `post_jmod.py:33`, `post_newmark.py`,
`rest_gene_phys.py:80`), `ft=` instead of `fr=` (`calc_stab_pente.py:110`), and `condition=` on
6 SIMP and 2 FACT (only BLOC reads it). TODO(verify) whether these defaults are applied
elsewhere (e.g. in the macro's Python); the extractor records them under `other`, not `default`.

## 2026-10-23 — 4.1 fixture cases — agent
Done: `tests/fixtures/{solid_static,shell_static,modal}/input/` with `mesh.geo` (Gmsh 4.15.2),
`mesh.med`, `run.comm`, `run.export` (1 cpu, 600 s, 2048 MB; outputs to `../output/`),
`run.json`. New `docs/schemas/run.schema.json` (title block, units, groups, sections, solver,
checks, provenance). `tests/fixtures/hand_values.py` computes every `TEST_RESU` reference:
Navier plate series, Euler-Bernoulli and Saint-Venant torsion frequencies, and the pressure
resultant integrated on the faceted `solid_static` mesh. `tests/test_fixtures.py` (24 tests)
checks schema, export file list, mesh groups, comm ↔ run.json ↔ hand values, and runs every
`run.comm` through the pinned catalog's syntax checker (`code_aster.Cata`, no solver).
`run-fixture.sh` now creates `output/tables/`. `numpy` and `h5py` are added to the `dev` extra.
Open: task 4.2. The fixtures were **not** run (no 17.4.26 image). `VALE_CALC` = hand value with
`TOLE_MACHINE` = `PRECISION` until 4.2 records the solver's values. TODO(verify) in 4.2:
`REAC_NODA` and `EFGE_NOEU` signs (checks use `VALE_ABS`), and that `run_aster` resolves
`../output/` paths relative to the export.
Decisions: none (no ADR). Choices: modal mode 6 is the first torsion mode (about 1485 Hz), not
bending, so it is checked against Saint-Venant torsion. The reaction sum uses `TEST_RESU`
`TYPE_TEST="SOMM"` over the whole `REAC_NODA` field, because `trresu.F90` ignores `GROUP_NO`
with `TYPE_TEST`. Matrices are built with `CALC_MATR_ELEM`/`NUME_DDL`/`ASSE_MATRICE`
(COMMAND-SET Tier 2 alternative to `ASSEMBLAGE`). Branch is `claude/project-thread-26k744`
(session-assigned).
Needs owner: nothing blocking.

## 2026-10-23 — 0.4 verify upstream anatomy (S1) — agent
Done: verified CLAUDE.md §6 and ARCHITECTURE.md §3 against 17.4.26 and corrected both in place;
`docs/INVENTORY.md` with counts. **268 commands** (135 OPER, 116 MACRO, 16 PROC, 1 FORM; + `VARIABLE`)
in 269 modules; **18,917 keyword occurrences** (17,595 simple, 1,322 factor; 2,847 blocs), 4,227
distinct names; `fr=` on only 13 % of keywords. **277 message families, 6,890 messages**, 51
placeholder formats (all named, + `%%`). **4,496 test cases** (`.export`), no expected `.mess` in
astest. `code_aster.Cata.Commands` imports in a plain venv (numpy only) → task 1.2 extracts by
import. `code_aster.Messages` does **not** import without the solver (`Utmess` → `aster_core`) →
task 1.3 must use `ast`. Upstream gettext: `_()` → domain `aster_messages`, switched on only by
`DEBUT(LANG=...)`, `.mo` built only with `--enable-i18n`. Upstream `en-US/aster_messages.po` covers
3,308/6,890 current messages (48 %) verbatim, literal 2016 quality.
Open: Task 4.2 must check whether the official
image ships an English `.mo` and whether `ASTER_LOCALEDIR` can be overridden.
Decisions: ADR-004 accepted by the owner (2026-10-23): `en/messages` is the source of truth, a
generated `.mo` is loaded via `DEBUT(LANG='EN')`, and the runtime renderer is the fallback. This
settles task 1.1.
Findings for later tasks: `POURSUITE` has no catalog (runs on `DEBUT`'s) — its Tier 1 reference
should say so; 4 messages numbered ≥ 100 are unreachable (`Utmess` asserts N < 100); `POST0_55/56`
are f-strings interpolating a module constant; 15 messages are not wrapped in `_()`; plain `I`
messages print without their ID in `.mess`. Licence headers GPL-3.0-or-later as ADR-007 assumes;
`.po`/`.ts` have no own licence header; the owner confirmed their reuse under GPL with attribution.
Needs owner: none.
Branch is `claude/project-thread-ux6ket` (session-assigned) rather than `task/0-4-…`.

## 2026-10-23 — 0.3 + 0.5 upstream pin and tooling skeleton — agent
Done: `upstream/` submodule → github.com/shubhs650/code_aster (shallow), pinned to **17.4.26**
(commit 5d2a06d, 2026-07-06; same commit as tags `17.5.0` and `stable`). `UPSTREAM_VERSION` =
17.4.26. `tools/` package `codeaster_en` + `caen` CLI (typer) with stubs extract, translate, mess,
report, upstream, bundle; `caen validate [glossary]` implemented (unique fr, non-empty en, kind
and status in allowed sets, aliases_en ≠ en, unique en within kind=command). `ci.yml`: checks the
submodule commit equals the UPSTREAM_VERSION tag, then ruff check/format, pytest, caen validate.
`tests/test_glossary.py` (36 tests). Root `ruff.toml` / `pytest.ini`; `.gitmodules.example`
replaced by the real `.gitmodules`.
Open: task 0.4 (S1). `CONTAINER_TAG` not created (Docker Hub `codeastersolver/codeaster-seq`
lists only `latest` and `14.4.0`; image ↔ 17.4.26 mapping is for task 4.2).
Decisions: tag rule — upstream README defines `stable` as "the latest frozen state of the stable
version in the maintenance branch"; it points at 17.4.26 = 17.5.0. 17.5.1–17.5.8 are
`stable-updates` (unfrozen maintenance head of `v17`); 18.0.x/18.1.x are `main`/`testing`
(18.0.25 = `testing`, so "even minor" alone would have picked a development tag). Glossary is
loaded with YAML 1.2 booleans so `fr: NO` stays the string "NO", not `False`. Ruff limited to
Python files (ruff ≥ 0.17 also reformats Markdown code blocks in docs/).
Needs owner: confirm 17.4.26 (vs. latest stable-update 17.5.8); upstream already ships English
localisation — `i18n/en-US/aster_messages.po` (Crowdin, 2016, ~6.7k msgids, v13 paths) and
`i18n/catapy_en_US.ts` (catalog strings, ~1.5k entries) — task 0.4/1.1 should assess reuse.
Branch is `claude/project-thread-mmwu8d` (session-assigned) rather than `task/0-3-…`.

## 2026-10-22 — kickoff — owner
Done: Doc set written (README, CLAUDE.md, ARCHITECTURE, PLAN, COMMAND-SET, TRANSLATION-GUIDE,
REPORT-SPEC, CLEARFEA-INTEGRATION, DECISIONS, LICENSING, SESSION-PROMPTS), seed glossary,
mirror sync workflow. No code.
Open: Tasks 0.1–0.2 (owner: create mirror repo, import, add sync workflow). Then S0 session.
Decisions: ADR-001…009 recorded.
Needs owner: choose GitHub org/user for both repos; attach AsterStudy translation dictionary
file for task 0.6; decide whether `code_aster` mirror keeps all tags or `main` only (after
blob-size check).
