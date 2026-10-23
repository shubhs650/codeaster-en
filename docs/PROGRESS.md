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
