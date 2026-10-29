# Solver fixtures

Three reference jobs that cover the alpha scope (`docs/ARCHITECTURE.md` §6), plus four broken runs for the log parser (below). Each case directory follows the job layout of `docs/CLEARFEA-INTEGRATION.md` §3:

```text
<case>/
├── input/    mesh.geo  mesh.med  run.comm  run.export  run.json
└── output/   run.mess  run.resu  run.rmed  tables/*.csv  exit_code  run_aster.stdout  provenance.json   (task 4.2)
```

`input/` is hand-written (task 4.1). `output/` is produced by `scripts/run-fixture.sh tests/fixtures/<case>` with the image pinned in `/CONTAINER_IMAGE` and committed (task 4.2). There is no image for upstream 17.4.26, so the outputs come from code_aster **17.4.22** (`simvia/code_aster`, ADR-011); `output/provenance.json` records the image digest and versions. `run.resu` is empty (no job writes to unit 8). Unit tests never run the solver: `tests/test_fixture_outputs.py` reads the committed outputs, and `.github/workflows/solver-fixtures.yml` regenerates them and reruns that test.

## Cases

| Case | Model | Mesh | Loads and supports | `TEST_RESU` checks (hand values) | Modelled on |
|---|---|---|---|---|---|
| `solid_static` | `3D`, linear static | 4,622 nodes, 14,439 TETRA4; cylinder Ri 100 / Ro 120 / H 300 mm with a radial nozzle ri 25 / ro 35 mm | base fixed (`DDL_IMPO`), 2 MPa internal pressure on shell wall and nozzle bore (`PRES_REP` after `ORIE_PEAU`) | reaction sum DX = applied pressure resultant (3891.64 N, exact on the faceted mesh) | `forma01a`, `zzzz341b` |
| `shell_static` | `DKT` (QUAD4, so DKQ), linear static | 441 nodes, 20 × 20 QUAD4; square plate a 1000 mm, t 10 mm | edges DZ = 0, two corners restrain in-plane motion, 0.01 MPa pressure | centre DZ = −2.11242 mm, centre MXX = −478.864 N·mm/mm (Navier), reaction sum DZ = 10,000 N | `ssls101n` |
| `modal` | `3D`, `CALC_MODES` 6 lowest | 4,197 nodes, 640 HEXA20; cantilever 400 × 20 × 10 mm | X = 0 face clamped | frequencies 52.22, 104.44, 327.26, 654.51, 916.33 Hz (Euler–Bernoulli bending) and 1485.22 Hz (Saint-Venant torsion) | `sdlv100a`, `sdll05a` |

Units are mm, N, MPa, tonne, s (`units.system = "SI_mm"` in `run.json`). Material is steel, E = 210,000 MPa, ν = 0.3, ρ = 7.85e-9 t/mm³.

## Broken runs (task 4.3)

Four more jobs fail on purpose, so the `.mess` parser and the failure classifier (`codeaster_en.mess`, `docs/CLEARFEA-INTEGRATION.md` §5) are tested on real solver output. Each is `shell_static` cut after `MECA_STATIQUE` with one fault (marked `# fault:` in `run.comm`) and a plain `DEBUT()`, as a user's study would run, so the `MODELISA8_14` alarms are printed. They have no `run.json` and are not checked by `tests/test_fixture_outputs.py`; `tests/test_mess.py` checks them.

| Case | Fault | What the solver prints | `run_aster` diagnostic | Class |
|---|---|---|---|---|
| `broken_missing_group` | `DDL_IMPO` on `GROUP_MA="EDGE"` (the mesh has `EDGES`) | `<EXCEPTION> <MODELISA7_77>` in `AFFE_CHAR_MECA` | `<S>_ERROR`, exit 1 | `user-model` |
| `broken_singular_matrix` | `EXCIT` without the supports | `<EXCEPTION> <FACTOR_11>` in `MECA_STATIQUE` (MUMPS, zero pivot) | `<S>_ERROR`, exit 1 | `user-model` |
| `broken_bad_keyword` | `PRES_REP=_F(..., PRESSION=Q)` instead of `PRES` | `<EXCEPTION> <SUPERVIS_4>` from the catalog check of `AFFE_CHAR_MECA` | `<S>_ERROR`, exit 1 | `user-model` |
| `broken_python_syntax` | a missing comma | Python `SyntaxError` before the solver starts (no banner, no stage) | `<F>_SYNTAX_ERROR`, exit 1 | `user-model` |

`FIN` still runs after an error raised as an exception, so `<I> <FIN> ARRET NORMAL` appears in two of these logs; it does not mean the run succeeded. The error box is printed again inside each Python traceback (three times for `SUPERVIS_4`); the parser marks the copies `repeat`.

## Hand values

`hand_values.py` computes every reference value (Navier series for the plate, beam and torsion formulas for the cantilever, and the pressure resultant integrated over the skin faces of `mesh.med`). `run.json` lists each value under `checks` with its formula and source; `tests/test_fixtures.py` checks that `run.comm`, `run.json` and `hand_values.py` agree.

`TEST_RESU` checks each value twice: against the hand value (`REFERENCE="ANALYTIQUE"`, `VALE_REFE`, `PRECISION`) and against the solver's own value from the first run (`VALE_CALC`, default `TOLE_MACHINE` 1e-6), so any change in solver results shows up as `NOOK`. First-run results (17.4.22, all `OK`):

| Case | Check | Hand value | Solver | Error |
|---|---|---|---|---|
| `solid_static` | `REAC_DX_SUM` | 3891.64 N | 3891.643 N | 0.00007 % |
| `shell_static` | `W_CENTER` | −2.11242 mm | −2.11226 mm | 0.007 % |
| `shell_static` | `MXX_CENTER` | −478.864 N·mm/mm | −479.645 N·mm/mm | 0.16 % |
| `shell_static` | `REAC_DZ_SUM` | 10,000 N | 10,000.000 N | 0 % |
| `modal` | `F1`–`F6` | 52.22, 104.44, 327.26, 654.51, 916.33, 1485.22 Hz | 52.34, 104.43, 327.07, 646.99, 911.68, 1497.03 Hz | 0.01–1.15 % |

Printed tables (`output/tables/`, `IMPR_TABLE` units in `run.export`): `reactions.csv` (`POST_RELEVE_T` resultant of `REAC_NODA` on the supports) in both static cases; in `modal`, `mass_inertia.csv` (`POST_ELEM MASS_INER`) and, since task 4.5, `modal_parameters.csv` (`RECU_TABLE` of the `CALC_MODES` result: `FREQ`, `MASS_GENE`, `MASS_EFFE_D*`, `MASS_EFFE_UN_D*`). The modal case was rerun for that table with the same image; its frequencies did not change. Its effective mass fractions in the bending planes (61.2/18.8/6.5 % in Z, 61.3/18.9 % in Y) agree with the Euler–Bernoulli cantilever (61.3/18.8/6.5 %, `hand_values.py`) within 1 %; `tests/test_results.py` checks them.

Signs, confirmed by the first run: `REAC_NODA` is the support reaction, so the reaction sums carry the opposite sign of the applied load (+X for `solid_static`, +Z for `shell_static`); the sagging moment `MXX` of the plate is negative. No check uses `VALE_ABS` any more.

`shell_static` sets `DEBUT(IGNORE_ALARM=("MODELISA8_14",))` without `ERREUR=_F(ALARME="EXCEPTION")`: the Gmsh point groups are POI1 cells, which the mesh check reports, and code_aster raises the alarm as an error before it looks at `IGNORE_ALARM`. The other two cases keep `ALARME="EXCEPTION"`. `tests/test_fixture_outputs.py` rejects any printed alarm in every case.

## Regenerating a mesh

```bash
cd tests/fixtures/<case>/input
gmsh -3 mesh.geo -format med -o mesh.med    # -2 for shell_static
```

The committed meshes were written by Gmsh 4.15.2 (MED 4.1). Another Gmsh version can number or split elements differently. If you regenerate a mesh, rerun `python tests/fixtures/hand_values.py`, because the `solid_static` reference depends on the facets, and update `run.comm` and `run.json` to match.

## Checks without the solver

`tests/test_fixtures.py` validates `run.json` against `docs/schemas/run.schema.json`, checks the `run.export` file list and logical units, checks that every group named in `run.comm` exists in `mesh.med`, and runs each `run.comm` through the pinned catalog's own syntax checker (`code_aster.Cata`, imported from `upstream/` without the solver). These tests cannot catch runtime behaviour: element and mesh compatibility, solver convergence, or the actual `TEST_RESU` verdicts. `tests/test_fixture_outputs.py` covers those from the committed outputs.

The report generator (task 4.6) keeps golden files of every fixture's report under `tests/golden/report/`. A PR that regenerates `output/` must also run `UPDATE_GOLDEN=1 pytest tests/test_report.py` and commit the changed goldens (timings and memory in the logs change on every run).
