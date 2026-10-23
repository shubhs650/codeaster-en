# Solver fixtures

Three reference jobs that cover the alpha scope (`docs/ARCHITECTURE.md` §6). Each case directory follows the job layout of `docs/CLEARFEA-INTEGRATION.md` §3:

```text
<case>/
├── input/    mesh.geo  mesh.med  run.comm  run.export  run.json
└── output/   run.mess  run.resu  run.rmed  tables/*.csv  exit_code   (task 4.2)
```

`input/` is hand-written (task 4.1). `output/` is produced by `scripts/run-fixture.sh tests/fixtures/<case>` with the official `codeastersolver/codeaster-seq` image and committed (task 4.2). Unit tests never run the solver.

## Cases

| Case | Model | Mesh | Loads and supports | `TEST_RESU` checks (hand values) | Modelled on |
|---|---|---|---|---|---|
| `solid_static` | `3D`, linear static | 4,622 nodes, 14,439 TETRA4; cylinder Ri 100 / Ro 120 / H 300 mm with a radial nozzle ri 25 / ro 35 mm | base fixed (`DDL_IMPO`), 2 MPa internal pressure on shell wall and nozzle bore (`PRES_REP` after `ORIE_PEAU`) | reaction sum DX = applied pressure resultant (3891.64 N, exact on the faceted mesh) | `forma01a`, `zzzz341b` |
| `shell_static` | `DKT` (QUAD4, so DKQ), linear static | 441 nodes, 20 × 20 QUAD4; square plate a 1000 mm, t 10 mm | edges DZ = 0, two corners restrain in-plane motion, 0.01 MPa pressure | centre DZ = −2.11242 mm, centre MXX = 478.864 N·mm/mm (Navier), reaction sum DZ = 10,000 N | `ssls101n` |
| `modal` | `3D`, `CALC_MODES` 6 lowest | 4,197 nodes, 640 HEXA20; cantilever 400 × 20 × 10 mm | X = 0 face clamped | frequencies 52.22, 104.44, 327.26, 654.51, 916.33 Hz (Euler–Bernoulli bending) and 1485.22 Hz (Saint-Venant torsion) | `sdlv100a`, `sdll05a` |

Units are mm, N, MPa, tonne, s (`units.system = "SI_mm"` in `run.json`). Material is steel, E = 210,000 MPa, ν = 0.3, ρ = 7.85e-9 t/mm³.

## Hand values

`hand_values.py` computes every reference value (Navier series for the plate, beam and torsion formulas for the cantilever, and the pressure resultant integrated over the skin faces of `mesh.med`). `run.json` lists each value under `checks` with its formula and source; `tests/test_fixtures.py` checks that `run.comm`, `run.json` and `hand_values.py` agree.

Until task 4.2 has run the solver, each `TEST_RESU` occurrence sets `VALE_CALC` to the hand value and `TOLE_MACHINE` to the same tolerance as `PRECISION`, so the non-regression check is no stricter than the reference check. Task 4.2 replaces `VALE_CALC` with the solver's own value and removes `TOLE_MACHINE`.

Two checks compare magnitudes only (`VALE_ABS="OUI"`): the reaction sums, because the sign convention of `REAC_NODA` is not yet confirmed from a run, and the plate moment `MXX`, for the same reason with `EFGE_NOEU`. Task 4.2 should record the observed signs and decide whether to drop `VALE_ABS`.

## Regenerating a mesh

```bash
cd tests/fixtures/<case>/input
gmsh -3 mesh.geo -format med -o mesh.med    # -2 for shell_static
```

The committed meshes were written by Gmsh 4.15.2 (MED 4.1). Another Gmsh version can number or split elements differently. If you regenerate a mesh, rerun `python tests/fixtures/hand_values.py`, because the `solid_static` reference depends on the facets, and update `run.comm` and `run.json` to match.

## Checks without the solver

`tests/test_fixtures.py` validates `run.json` against `docs/schemas/run.schema.json`, checks the `run.export` file list and logical units, checks that every group named in `run.comm` exists in `mesh.med`, and runs each `run.comm` through the pinned catalog's own syntax checker (`code_aster.Cata`, imported from `upstream/` without the solver). These tests cannot catch runtime behaviour: element and mesh compatibility, solver convergence, or the actual `TEST_RESU` verdicts. Task 4.2 covers those.
