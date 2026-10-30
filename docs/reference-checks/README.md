# Reference checks (task 2.3e)

Small studies run in session to check claims in the command references written in task 2.3e
(`DEFI_CONSTANTE`, `MACR_LIGN_COUPE`, `POST_RCCM`, `THER_LINEAIRE`, `AFFE_CHAR_THER`). They are
not solver fixtures: there is no `run.json`, and `solver-fixtures.yml` does not rerun them. Each
directory holds the `.comm` and `.export` as run and the tables printed by `IMPR_TABLE`
(`output/t<unit>.csv`, comment lines removed). Run on 2026-10-30 with the pinned image
(`CONTAINER_IMAGE`, code_aster 17.4.22) and the Docker command of `scripts/run-fixture.sh`.

To rerun one, copy the mesh named in its header next to `run.comm`
(`tests/fixtures/solid_static/input/mesh.med` or `tests/fixtures/solid_loads/input/mesh.med`).

## `cut-lines/` — `MACR_LIGN_COUPE`, `POST_RCCM`, `DEFI_CONSTANTE` (solid_static)

The `solid_static` vessel (internal pressure 2 MPa, wall from radius 100 to 120 mm), a line
through the wall at z = 75 mm on the −Y side (radial direction −Y). Expected to stop at the last
command (see `LC`). Results:

| Table | What it shows |
|---|---|
| `t31.csv` (`LA`) | Two lines in one call, `REPERE='LOCAL'` first and `'INITIAL'` second: **both** come out in global axes (the local line has hoop stress in `SIXX`, 8.52 at the inner surface, identical to the global line). The rotation decision follows the last occurrence's `REPERE` (`macr_lign_coupe_ops.py:680`, `:893`). |
| `t32.csv` (`LB`) | The same `'LOCAL'` line alone: rotated (`SIXX` = −0.76 radial, `SIYY` = 8.52 hoop). |
| — (`LC`) | `'INITIAL'` first, `'LOCAL'` second: the run stops with `ValueError: SEGMENT using INITIAL not handled` (`run.mess`), from `crea_resu_local`. |
| `t33.csv` (`TW`) | `SIGM_ELNO` along the wall, 21 points: 20 rows; the outer point (radius 120) is outside the faceted mesh and dropped with `POST0_24`. |
| `t34.csv` | `POST_RCCM` `PM_PB`, `TYPE_RESU='VALE_MAX'` on `TW`: one row per quantity and end (`PM` 9.87, `PB` 2.92, `PMB` 12.58 / 9.00, `F`), `SM` 150 and `3SM` 450 from `RCCM=_F(SM=150.0)`. |
| `t35.csv` | The same with `TYPE_RESU='DETAILS'`: one row per end. |
| `t36.csv` | `AFFE_CHAR_MECA_F` with `DDL_IMPO` given by `DEFI_CONSTANTE(VALE=0.0)`: base reaction 3891.64 N in X, the `solid_static` fixture's value with `AFFE_CHAR_MECA`. |

## `cut-lines-distance/` — `DISTANCE_MAX` and `POSTRCCM_7`

The `TW` line again with `DISTANCE_MAX=0.5`: all 21 points kept (`t33.csv`, last abscissa 20.0),
and `POST_RCCM` gives `PM` 9.73 instead of 9.87 on the 19 mm line (`t35.csv`). A last
`POST_RCCM` with a material that has only `ELAS` stops with `POSTRCCM_7` ("il faut définir le
comportement RCCM dans DEFI_MATERIAU"), as expected.

## `thermal/` — `THER_LINEAIRE`, `AFFE_CHAR_THER` (solid_loads block)

The `solid_loads` block (100 mm in Z, `HEXA8`), conductivity 0.05 W/(mm·K), `RHO_CP` 3.6e-3
J/(mm³·K), `BASE` (z = 0) held at 0, other faces adiabatic unless loaded. Mean temperature of
the `TOP` nodes (z = 100):

| Table | Load on `TOP` (or volume) | Hand value | Result |
|---|---|---|---|
| `t31.csv` | `FLUX_REP` `FLUN=0.01` | q·L/λ = 20 | 20.0 |
| `t32.csv` | `ECHANGE` h = 5e-4, T_ext = 100 | h·T_ext/(h + λ/L) = 50 | 50.0 |
| `t33.csv` | `SOURCE` `SOUR=1e-4` (volume) | s·L²/(2λ) = 10 | 10.0 |
| `t34.csv` | transient, default `ETAT_INIT`, constant convection | — | 50.0 at all 11 times (starts in steady state) |
| `t35.csv` | transient, `ETAT_INIT=_F(VALE=0.0)`, default `THETA=0.57`, 360 s steps | rises to 50 | 0, 59.1, 43.0, 54.5, 47.0, ... (oscillates) |
| `t36.csv` | `TYPE_CALCUL='STAT'` at times 0, 1, 2, flux × ramp 0 → 2 | 0, 20, 40 | 0, 20, 40 (stored from index 1) |

A last steady analysis with `RAYONNEMENT` stops with `CHARGES9_42` (radiation not possible in a
linear operator), as expected.

## `thermal-theta/` — time scheme

The `t35` transient with `SCHEMA_TEMPS=_F(THETA=1.0)`: 0, 38.6, 46.5, 48.9, 49.6, ... rising
monotonically to 50 (`t35.csv`); with the default `THETA` and 10 s steps stored every 36th
(`ARCHIVAGE=_F(PAS_ARCH=36)`): 0, 45.8, 49.5, 49.9, ... (`t36.csv`). Ends with `DIAGNOSTIC JOB : OK`.
