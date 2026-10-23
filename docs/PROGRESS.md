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
