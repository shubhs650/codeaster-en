# Session prompts

Copy-paste starters for Claude Code (cloud) sessions. Each assumes the agent will read `CLAUDE.md`, `docs/PLAN.md` and `docs/PROGRESS.md` first — the prompt says so anyway because a fresh session has no memory.

General pattern:

```
Read CLAUDE.md, docs/PLAN.md and the last three entries of docs/PROGRESS.md.
Your task is <ID> — <title> from PLAN.md. Work on branch task/<id>-<slug>.
<task-specific context>
When done: run ruff, pytest and `caen validate`; append a PROGRESS entry; open a PR
titled "<id>: <title>" describing changes, verification, and anything I must review by hand.
Do not start another task.
```

---

## S0 — Bootstrap the overlay repo (task 0.3 + 0.5)

```
This is a brand-new repo containing only CLAUDE.md, README.md, docs/, en/glossary.yaml and mirror-repo/.
Read CLAUDE.md and docs/PLAN.md.

Do tasks 0.3 and 0.5:
1. Add the solver mirror as a submodule at upstream/ from https://github.com/<org>/code_aster,
   pinned to the latest tag that looks like a stable release (x.y.z with even minor, or the tag
   the mirror's README/CHANGELOG calls stable — check and tell me which you picked and why).
   Write that tag into UPSTREAM_VERSION.
2. Create tools/pyproject.toml for package codeaster_en with CLI `caen` (typer), dev extras
   ruff + pytest + pyyaml + jsonschema. Stub subcommands: extract, translate, validate, mess,
   report, upstream, bundle. `caen validate glossary` must actually work: unique fr, non-empty
   en, kind in the allowed set, no duplicate en within kind=command.
3. Add .github/workflows/ci.yml running ruff check/format and pytest with submodules fetched
   (shallow is fine).
4. Add tests/test_glossary.py exercising the validator on en/glossary.yaml.
Open a PR. Do NOT edit anything under upstream/.
```

## S1 — Verify upstream anatomy (task 0.4)

```
Read CLAUDE.md §6 and docs/ARCHITECTURE.md §3. They describe what we EXPECT to find in
upstream/. Verify every claim against the actual checkout:
- where command catalogs live and what DSL they use; whether `import code_aster.Cata`
  (or the equivalent) works in a plain Python venv without a built solver;
- the Messages/ format, placeholder styles present (collect the set of distinct %(…) formats);
- any gettext/localisation machinery (search for `gettext`, `_(`, `localization`, `.po`, `LANG`);
- whether astest contains any expected-output .mess files we could use as parser samples;
- the licence text and headers.
Count commands, keywords (total), message families, messages, test cases.
Correct CLAUDE.md §6 and ARCHITECTURE.md §3 in place. Write docs/INVENTORY.md with the counts.
Draft ADR-004 in docs/DECISIONS.md with your evidence (keep status: proposed; I decide).
Append a PROGRESS entry. Open a PR. No other changes.
```

## S2 — Catalog extractor (task 1.2)

```
Task 1.2. Implement `caen extract catalog` in tools/codeaster_en/extract/catalog.py.
Input: upstream/code_aster/Cata/Commands/ (path confirmed in docs/INVENTORY.md).
Output: en/commands/<CMD>.json for ALL commands, schema in docs/schemas/command.schema.json.
Capture per keyword: path (PARENT/CHILD), kind (simple/factor/bloc), type(s), cardinality
(min/max), default, allowed values (into), fr help string, source file and line.
Add _generated_from {upstream tag, file, extractor version}.
Snapshot tests for AFFE_MODELE, DEFI_MATERIAU, MECA_STATIQUE under tests/.
If the catalog DSL can only be evaluated by importing it, do that; if it needs the built
solver, fall back to a Python AST walk and say so in PROGRESS.
```

## S3 — Messages extractor + validator (tasks 1.3, 1.6)

```
Tasks 1.3 and 1.6. Implement `caen extract messages` → en/messages/<FAMILY>.en.json with
en: null, and the placeholder parser (regex covering every format listed in INVENTORY.md,
plus %%). Then `caen validate` with rules: glossary; placeholder equality fr↔en when en set;
forbidden-synonym scan over en/**/*.md; command .md keyword tables ⊆ .json keywords.
Wire validate into ci.yml. Tests for every rule, including a deliberately broken fixture.
```

## S4 — Command reference batch (task 2.3, repeat per batch)

```
Task 2.3 batch (b): AFFE_MODELE, DEFI_MATERIAU, AFFE_MATERIAU, AFFE_CARA_ELEM.
Read docs/TRANSLATION-GUIDE.md §2 and §4 and docs/COMMAND-SET.md.
For each command: start from `caen translate command <CMD>` draft (if 2.2 is done) or the
.json; write en/commands/<CMD>.md following the template; every keyword in the table must
exist in the .json; "when to use" is mandatory; patterns must be lifted from astest cases
found via en/astest-index.json and cited; pitfalls only from evidence you can cite.
Add glossary entries (status: proposed) for any term you needed.
Mark status: assisted. Run `caen validate`. List in the PR the three claims per command you
are least sure about so I can review them first.
```

## S5 — Fixture cases (task 4.1)

```
Task 4.1. Create tests/fixtures/{solid_static,shell_static,modal}/input/ each with:
a Gmsh .geo script producing a mesh.med with named physical groups, the mesh.med itself,
run.comm, run.export (sequential, 1 cpu, modest time/memory), and run.json per
docs/schemas/run.schema.json (write the schema if missing).
solid_static: a short cylinder with a radial nozzle (or a plate with a hole if too long),
fixed base, internal pressure; include MODI_MAILLAGE/ORIE_PEAU, MECA_STATIQUE, CALC_CHAMP
(SIEQ_NOEU, SIGM_NOEU, REAC_NODA), POST_RELEVE_T reactions, IMPR_RESU MED, IMPR_TABLE,
TEST_RESU on reaction sum = applied pressure resultant.
shell_static: simply supported square plate, DKT, uniform pressure, TEST_RESU vs Timoshenko.
modal: cantilever beam (3D), CALC_MODES first 6, POST_ELEM MASS_INER, TEST_RESU vs Euler-Bernoulli f1.
Use only Tier 1/2 keywords. Cite the astest cases you modelled on. Run each case with
scripts/run-fixture.sh, iterate until every TEST_RESU is OK, and commit output/ alongside input/.
Keep meshes small (each run < 10 min on 4 vCPU).
```

## S6 — Solver fixtures Action (task 4.2)

```
Task 4.2. Write .github/workflows/solver-fixtures.yml: on workflow_dispatch and on changes to
UPSTREAM_VERSION or tests/fixtures/**/input/**, pull codeastersolver/codeaster-seq with the
tag matching UPSTREAM_VERSION (read CONTAINER_TAG; create it), run each fixture with run_aster
inside the container, copy .mess/.rmed/tables/exit code to tests/fixtures/<case>/output/,
fail if any TEST_RESU is not OK, and commit the outputs on a branch + open a PR.
Document the image/version mapping in docs/ARCHITECTURE.md §6.
```

## S7 — `.mess` parser and renderer (tasks 4.3, 4.4)

```
Tasks 4.3 and 4.4. Using tests/fixtures/*/output/run.mess (and the broken-run fixtures),
implement codeaster_en.mess: parse(path) → Events; render(lang="en") joining to
en/messages/; argument recovery by matching the French template against the printed text;
untranslated flag; stream(path) for live tailing; CLI `caen mess translate run.mess`.
Every line must be classified or captured verbatim in an Unknown event — never dropped.
Tests on all fixture logs. Add classify.py with the four failure classes from
docs/CLEARFEA-INTEGRATION.md §5, keyed by family/number seen in the broken fixtures.
```

## S8 — Report generator (task 4.6)

```
Task 4.6. Implement codeaster_en.report per docs/REPORT-SPEC.md: collect.py → RunModel
(dataclass, JSON), render.py → report.md via Jinja2, then HTML (+CSS, print-ready) and PDF
(WeasyPrint). Golden-file tests on report.md and run_model.json for all three fixtures.
Add the French-word tripwire test (top-200 list in tests/data/french_tripwire.txt).
CLI: `caen report <job_dir> --out report --sections all --no-images`.
```

## S9 — Upstream bump tool (task 7.1)

```
Task 7.1. Implement `caen upstream bump --to <tag>`: update the submodule, UPSTREAM_VERSION,
CONTAINER_TAG; re-run extract catalog + messages; diff against the previous JSON and write
docs/upstream-diffs/<old>-<new>.md (commands/keywords added/removed/changed; messages
added/removed/text-changed → mark those en entries status: stale). Dry-run flag. Test by
bumping between two real tags in the mirror and back.
```
