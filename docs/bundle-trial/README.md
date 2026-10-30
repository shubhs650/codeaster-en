# Bundle trial (task 5.5)

PLAN 5.5's acceptance asks for the LLM context bundle to be "used in a trial Claude Code session to write a new `.comm` that runs green". This directory is that trial, run on 2026-10-30.

## How it was run

- A fresh agent session, with no project context, was given only the Tier 1 compact bundle (`caen bundle --tier 1`, 296,722 characters at the time; the merged compact level keeps two patterns per reference instead of three and shortens long keyword lists in rules, 285,168 characters) and Gmsh 4.15.2. It was told not to read the repository, `upstream/` or the web, and not to run the solver.
- The problem was new, not one of the guide's walkthroughs: a quarter model of a steel plate with a central hole (200 × 100 × 10 mm, hole radius 10 mm) under a 50 MPa traction, with symmetry supports as kinematic conditions (`AFFE_CHAR_CINE`), a surface traction (`FORCE_FACE`), reactions printed to a table and a `TEST_RESU` equilibrium check against a hand value it had to work out.
- It wrote `input/mesh.geo`, `input/run.comm` and `input/run.export` (committed here unchanged) and a `mesh.med` (not committed: `gmsh -3 mesh.geo -format med -o mesh.med` in `input/` regenerates it; 12,712 nodes, 7,596 `TETRA10`).
- The study was then run once, unchanged, with the pinned image and the Docker command of the solid walkthrough (`CONTAINER_IMAGE`, the same image `solver-fixtures.yml` uses).

## Result

First run, no edits: `--- DIAGNOSTIC JOB : OK`, exit code 0, no warning in `output/run.mess`. The reaction resultant on the symmetry face is −25,000 N in X (`output/tables/reactions.csv`), the agent's hand value (50 MPa × 50 mm × 10 mm, sign from the bundle's reaction convention). Both `TEST_RESU` lines are `OK`:

```text
 OK   NON_REGRESSION   REAC_DX_SUM      -25000.0              -24999.999999999854    5.820766E-13%   9.999999999999999E-05%
 OK   ANALYTIQUE       REAC_DX_SUM      -25000.0              -24999.999999999854    5.820766E-13%   0.01%
```

`tests/test_bundle.py` checks the committed `run.comm` against the pinned catalog and the committed outputs. The study is not a solver fixture: it has no `run.json` or builder source, so `solver-fixtures.yml` does not rerun it.

## What the agent found missing or unclear

These are its words, condensed; they are inputs for later guide and reference work, not changes made here.

- **`TEST_RESU` on a first run.** The catalog requires a `VALE_CALC`, and a new study has no computed value yet. The agent set it to the hand value and said so in a comment, which works only because an equilibrium sum is exact. The bundle gives no advice for this case.
- **`FORCE_FACE`.** Only in the keyword table: no pattern says the traction is per unit area in global axes, or that face elements must be in the model (it inferred `TOUT="OUI"` from `PRES_REP`).
- **`DEFI_GROUP` `ENV_SPHERE`.** `RAYON` and `PRECISION` are listed without meaning (compact tables drop the authored meanings); it used `INTERSEC` instead.
- **`AFFE_CHAR_CINE` on face groups of a 3D model** is only implied by a pattern.
- **Rigid-body restraint of a solid** is shown only for the shell walkthrough; it used judgement (one node held in Z).
- **`DEBUT` for a clean study run** is spread over several pages (plain `DEBUT()` versus the fixtures' `ALARME="EXCEPTION"`).
- The `MECA_STATIQUE` table repeats `EXCIT` and `SOLVEUR / RENUM` (one row per catalog bloc), which reads as duplication.

It read about 2,700 of the bundle's 5,100 lines: the preamble, concepts, the solid walkthrough, the FAQ and eleven command references.
