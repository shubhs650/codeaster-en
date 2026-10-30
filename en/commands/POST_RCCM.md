---
command: POST_RCCM
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/post_rccm.py:26
doc_fr: U4.83.11
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3e)
examples: [sslv100c, sslv04h, rccm01a]
---

# POST_RCCM — stress linearization (RCC-M)

> **Assisted reference.** Written in session from the pinned catalog, the Fortran operator it
> calls, the message catalog, upstream test cases and a run of our own (see Patterns). Every
> behavior claim cites its source. Not reviewed by an engineer. Tier 1 covers
> `TYPE_RESU_MECA='EVOLUTION'` with `OPTION='PM_PB'` (stress linearization); the other modes are
> named but not described.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

`POST_RCCM` checks stresses against the RCC-M design code (French nuclear pressure equipment).
In Tier 1 it does **stress linearization through a wall**: from a `MACR_LIGN_COUPE` table along
a line across the wall, it splits each stress component into membrane (mean) and bending
(linear part) by integration over the points (`upstream/bibfor/postrele/rc32my.F90`), and
reports Tresca values of membrane (`PM`), bending (`PB`), membrane plus bending at each end
(`PMB`) and the remaining peak at each end (`F`), each the maximum over the times
(`upstream/bibfor/postrele/rcevom.F90:280`–`:356`). It gives no verdict: `SM` and `3SM` are
printed for the engineer to compare. The decisions it encodes are the section, the times, and
whether thermal (secondary) stresses are separated out (`TABL_SIGM_THER`).

| Fact | Value |
|---|---|
| Catalog description (fr) | «Vérification des critères de niveau 0 et certains critères de niveau A du RCC-M» |
| Kind | `OPER` |
| Result | `table_sdaster` |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.83.11 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `TYPE_RESU_MECA`, `OPTION`, `PM_PB` |

COMMAND-SET asked to verify the command's name in the pinned version: `POST_RCCM` exists
(`upstream/code_aster/Cata/Commands/post_rccm.py:26`, operator 165) and `OPTION='PM_PB'` is the
linearization.

## Keywords

The table covers the top-level keywords and `TRANSITOIRE` (the input of `EVOLUTION`). Factor
keywords of the other modes are listed under [Other keywords](#other-keywords).

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `TYPE_RESU_MECA` | text, required | — | *mechanical result type (RCC-M)*. One of `'EVOLUTION'`, `'ZE200a'`, `'ZE200b'`, `'B3200'`, `'B3600'`. `'EVOLUTION'`: the stresses come as tables along lines, for one or more transients; this is the mode for linearization. The other values are the RCC-M chapter B3200 and B3600 and appendix ZE200 methods, built from unit load cases and situations (`CHAR_MECA`, `RESU_MECA_UNIT`, `SITUATION`, `TUYAU`); `'B3200'` serves a 2D or 3D component under many situations (earthquake, transitions, environmental fatigue); `'B3600'` a piping line (fatigue or equivalent moment); `'ZE200a'`/`'ZE200b'` piping with thermal (and pressure) transients (U4.83.11 §3.4). Outside Tier 1, not described here. |
| `OPTION` | text, required, list (`EVOLUTION`); one value (other modes) | — | *option*. With `'EVOLUTION'`: one or more of `'PM_PB'`, `'SN'`, `'FATIGUE_ZH210'`, `'AMORCAGE'`. `'PM_PB'`: the linearization described above (level 0 criteria, primary stresses; "only the mechanical part", comment at `upstream/bibfor/postrele/rcevom.F90:247`). `'SN'`: the range of primary plus secondary stress between times (`rcevsn.F90`). `'FATIGUE_ZH210'`: a fatigue usage factor, which also computes `SN` (`upstream/bibfor/postrele/rcevol.F90:122`). `'AMORCAGE'`: crack initiation, which cannot be combined with the others (`POSTRCCM_3`). `SN`, `FATIGUE_ZH210` and `AMORCAGE` are outside Tier 1. With the other `TYPE_RESU_MECA` values, the options listed in the .json. |
| `MATER` | `mater_sdaster`, required | — | *material*. The material for the code data. It must have an `RCCM` block in `DEFI_MATERIAU`, even for `PM_PB`, or the run stops with `POSTRCCM_7` (`upstream/bibfor/op/op0165.F90:84`; checked by our run, see Patterns). `PM_PB` reads only `RCCM/SM` from it, to print `SM` and `3SM` (`upstream/bibfor/postrele/rcevo1.F90:44`). It need not be the material of the analysis. |
| `TYPE_RESU` | text, optional | `'VALE_MAX'` | *result type*. One of `'VALE_MAX'`, `'DETAILS'`, `'SYSTUS'`. `'VALE_MAX'`: the maximum over the times of each quantity, with the time it occurs (`INST_PM`, ...); one row per quantity and end of line (see Output table). `'DETAILS'`: one row per end of line and time, with `INST`, `PM`, `PB`, `PMB`, `F` side by side (`rcevod.F90`; checked by our run). Use `'DETAILS'` to see how the values evolve, or simply for a compact table when there is one time. `'SYSTUS'`: the values for each situation or combination of situations that contributes to the usage factor; only for `'B3200'`, `'ZE200a'` and `'ZE200b'` (U4.83.11 §3.1), so it disables the `EVOLUTION` keywords (catalog condition). Outside Tier 1. |
| `AXIS` | text, optional | `'NON'` | *axisymmetric*. One of `'NON'`, `'OUI'`. `'OUI'` for a line in an axisymmetric model: the linearization then follows the "PRSECT" method of ANSYS (comment at `upstream/bibfor/postrele/rc32axis.F90:19`), with a bending part that differs at the two ends, so `PB` gets two values (`rcevom.F90:385`). Only with `'EVOLUTION'` (`POSTRCCM_59`); the code does not check that the model is axisymmetric (`POSTRCCM_58`). |
| `RAYON_MOYEN` | real, optional | `-1.0` | With `AXIS='OUI'`: the curvature radius given to the line (catalog help: "curvature assigned to the cut line"). A value ≤ 0 (the default) means no curvature correction (`upstream/bibfor/postrele/rc32axis.F90:63`). Give the curvature of the mean line where it crosses the cut segment, in the XOY plane of the axisymmetric model, when that line is curved there (a head or an elbow); it must be strictly positive (U4.83.11 §9.1.2, French only). |
| `SY_MAX` | real, optional | — | Yield strength for the thermal ratcheting check (catalog help), done when `TRANSITOIRE/TABL_RESU_PRES` is given; without `SY_MAX` (or `RCCM/SY_02`) the check is skipped with `POSTRCCM_4` (`upstream/bibfor/postrele/rcevol.F90:184`). Not part of `PM_PB`. Out of Tier 1 scope. |
| `TYPE_KE` | text, optional | `'KE_MECA'` | One of `'KE_MECA'`, `'KE_MIXTE'`. The plasticity correction factor Ke for fatigue from the mechanical part only, or split into mechanical and thermal parts (catalog help). Fatigue only; not used by `PM_PB`. Out of Tier 1 scope. |
| `SOUS_CYCL` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Takes sub-cycles into account (catalog help). `ZE200*` and `B3200` only. Out of Tier 1 scope. |
| `METHODE` | text, optional | `'TRESCA'` | *method*. One of `'TRESCA'`, `'TOUT_INST'`. How the times are selected (catalog help). `ZE200*` and `B3200` only. Out of Tier 1 scope. |
| `CHAM_MATER` | `cham_mater`, required | — | *material field*. `B3600` with `OPTION='FATIGUE'` only. Out of Tier 1 scope. |
| `MODELE` | `modele_sdaster`, required | — | *model*. `B3600` with `OPTION='FATIGUE'` only. Out of Tier 1 scope. |
| `CARA_ELEM` | `cara_elem`, required | — | *element properties*. `B3600` with `OPTION='FATIGUE'` only. Out of Tier 1 scope. |
| `INFO` | integer, optional | — | *verbosity*. One of `1`, `2`. |
| `TITRE` | text, optional | — | *title*. A title for the table (`upstream/astest/rccm01a.comm:66`). |
| `TRANSITOIRE` | factor keyword, required, repeatable | — | *transient to post-process* (catalog help). With `'EVOLUTION'`: one occurrence per transient (load history). Each gives the stress table and the times to read. Rules: exactly one of `TOUT_ORDRE`, `INST`, `LIST_INST`, `TOUT_INST`; exactly one of `TABL_RESU_MECA`, `TABL_SIGM_THETA`. |
| `TRANSITOIRE / TABL_RESU_MECA` | `table_sdaster`, optional | — | The stresses along the lines (catalog help), a `MACR_LIGN_COUPE` table on `SIGM_ELNO` or `SIGM_NOEU`. It must have the columns `INTITULE`, `ABSC_CURV`, `COOR_X`, `COOR_Y`, `INST` and the stress components `SIXX`, `SIYY`, `SIZZ`, `SIXY` (and `SIXZ`, `SIYZ` in 3D); a missing one stops the run with `POSTRCCM_17` (`upstream/bibfor/postrele/rcevo2.F90:89`–`:97`, `:255`–`:261`). Each `INTITULE` is one section, processed on its own and reported under its name. |
| `TRANSITOIRE / TABL_SIGM_THER` | `table_sdaster`, optional | — | The stresses along the same lines under the thermal load alone (catalog help: "result under thermal loading only"). When given, its membrane and bending parts are subtracted before `PM` and `PB` are computed (`upstream/bibfor/postrele/rcevom.F90:297`), so they cover primary stresses only (`upstream/astest/rccm01a.comm:67` versus `:91`). Give it whenever the transient includes temperature. |
| `TRANSITOIRE / TABL_RESU_PRES` | `table_sdaster`, optional | — | The stresses along the lines under pressure alone (catalog help); used by the thermal ratcheting check (see `SY_MAX`). Not part of `PM_PB`. Out of Tier 1 scope. |
| `TRANSITOIRE / TABL_SIGM_THETA` | `table_sdaster`, optional | — | Stresses at a distance from a singularity, per angle THETA (catalog help); for `AMORCAGE`. Outside Tier 1. Out of Tier 1 scope. |
| `TRANSITOIRE / NB_OCCUR` | integer, optional | `1` | How many times the transient occurs (catalog help); for fatigue. Not used by `PM_PB`. Out of Tier 1 scope. |
| `TRANSITOIRE / TOUT_INST` | text, optional | — | One of `'OUI'`. All times of the table. The usual choice, and the only sensible one for a single static step (`upstream/astest/sslv100c.comm:87`). |
| `TRANSITOIRE / TOUT_ORDRE` | text, optional | — | One of `'OUI'`. All steps. |
| `TRANSITOIRE / INST` | real, optional, list | — | These times only. |
| `TRANSITOIRE / LIST_INST` | `listr8_sdaster`, optional | — | The times as a `DEFI_LIST_REEL` list. |
| `TRANSITOIRE / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. With `INST` or `LIST_INST`: whether `PRECISION` is relative or absolute when matching times. |
| `TRANSITOIRE / PRECISION` | real | `1e-06` (relative) | *tolerance*. The tolerance of that match; required with `CRITERE='ABSOLU'`. |

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- `TRANSITOIRE` (with `EVOLUTION`): exactly one of `TOUT_ORDRE`, `INST`, `LIST_INST`, `TOUT_INST` must be given (`UN_PARMI`).
- `TRANSITOIRE` (with `EVOLUTION`): exactly one of `TABL_RESU_MECA`, `TABL_SIGM_THETA` must be given (`UN_PARMI`).
- when `equal_to("TYPE_RESU_MECA", 'B3200')`: `CHAR_MECA`, `RESU_MECA_UNIT` are given all together or not at all (`ENSEMBLE`).

## Output table

With `TYPE_RESU='VALE_MAX'`: columns `INTITULE`, `LIEU` (`ORIG` or `EXTR`, the line's ends),
`SM`, `3SM`, `TABL_RESU`, then `INST_PM`, `PM`, `INST_PB`, `PB`, `INST_PMB`, `PMB`, `INST_F`,
`F` (`upstream/bibfor/postrele/rcevom.F90:78`–`:84`), one pair of rows per quantity with the
others left empty: filter on `INTITULE`, `LIEU` and the column (`upstream/astest/sslv100c.comm:91`).
`PM` (and `PB` unless `AXIS='OUI'`) is the same at both ends. Our `solid_static` run (wall
20 mm, 2 MPa, `docs/reference-checks/`): `PM` 9.73, `PB` 3.22, `PMB` 12.67 / 8.86 MPa, against
a thin-wall hoop stress of 10 MPa.

## Patterns

### Linearization through a wall (plane strain)

Two lines across a pressurized hollow cylinder, made by `MACR_LIGN_COUPE` on `SIGM_ELNO`, then
`PM`, `PB`, `PMB` for each line and end. The material has an `RCCM` block with `SM`.

Source: `upstream/astest/sslv100c.comm:83` (material at `:39`, lines at `:62`).

```python
MA = DEFI_MATERIAU(ELAS=_F(E=200000.0, NU=0.3, ALPHA=0.0), RCCM=_F(M_KE=1.7, N_KE=0.3, SM=200.0))
```

```python
T_PMPB = POST_RCCM(
    OPTION="PM_PB",
    TYPE_RESU_MECA="EVOLUTION",
    MATER=MA,
    TRANSITOIRE=_F(TABL_RESU_MECA=T_RESU, TOUT_INST="OUI"),
)
```

### Axisymmetric model

The same in an axisymmetric model: `AXIS='OUI'`, default `RAYON_MOYEN` (no curvature
correction).

Source: `upstream/astest/sslv04h.comm:330`.

```python
T1 = POST_RCCM(
    OPTION="PM_PB",
    TYPE_RESU_MECA="EVOLUTION",
    MATER=MA,
    AXIS="OUI",
    RAYON_MOYEN=-1.0,
    TRANSITOIRE=_F(TABL_RESU_MECA=T_RESU, TOUT_INST="OUI"),
)
```

### Thermal stresses separated out, details per time

Total stresses and thermal-only stresses of a transient, read from files here; `PM` and `PB`
then exclude the thermal part. `TYPE_RESU='DETAILS'` gives the values at each time.

Source: `upstream/astest/rccm01a.comm:61`.

```python
PMPB1 = POST_RCCM(
    TYPE_RESU_MECA="EVOLUTION",
    OPTION="PM_PB",
    TYPE_RESU="DETAILS",
    MATER=MAT,
    TITRE="CALCUL DE PM_PB (DETAILS), SITUATION 1, EVOLUTION",
    TRANSITOIRE=_F(TABL_RESU_MECA=T_TOT1, TABL_SIGM_THER=T_TH1, TOUT_INST="OUI"),
)
```

## Pitfalls

- **`MATER` needs `RCCM`.** A material with only `ELAS` stops with `POSTRCCM_7`, even for
  `PM_PB` (`upstream/bibfor/op/op0165.F90:84`; reproduced in our run). Add `RCCM=_F(SM=...)`.
- **The section is the table's line, as extracted.** `MACR_LIGN_COUPE` drops points outside
  the elements with only a warning (`POST0_24`): on the `solid_static` wall the outer point was
  lost, the section was 19 mm instead of 20 and `PM` 9.87 instead of 9.73 MPa, until
  `DISTANCE_MAX=0.5` kept it. Check that `ABSC_CURV` spans the full thickness.
- **Line placement is the engineer's.** Usual practice (outside the solver): a straight line
  normal to the wall, through the full thickness, away from discontinuities, with enough points
  (`sslv100c` uses 100, our run 21).
- **Thermal stresses count as primary unless separated** with `TABL_SIGM_THER`.
- **Axes do not matter.** Tresca values of line-averaged tensors do not depend on the axes the
  components are written in.
- **No verdict.** Allowables (for example Pm ≤ Sm, Pm + Pb ≤ 1.5 Sm in RCC-M and ASME design
  rules) come from the code applied, not from this command. TODO(verify) for the edition in use.

## Other keywords

Factor keywords of the other `TYPE_RESU_MECA` modes (sub-keywords are in
`en/commands/POST_RCCM.json`); outside Tier 1:

- `CHAR_MECA`: Mechanical loads.
- `ENVIRONNEMENT`: Data for the Fen calculation.
- `FACT_SIGM`: Stress intensity factors (weld).
- `INDI_SIGM`: Stress indices.
- `RESU_MECA`: Results due to external forces.
- `RESU_MECA_UNIT`: Unit mechanical results.
- `RESU_PRES`: Results due to pressure.
- `RESU_THER`: Thermal results.
- `SEISME`: Seismic situation.
- `SITUATION`: Situation.
- `TUYAU`: Geometric properties of the piping.
- `ZONE_ANALYSE`: List of the elements or nodes analyzed.

## See also

- [`MACR_LIGN_COUPE`](MACR_LIGN_COUPE.md), which makes the input table;
  [`DEFI_MATERIAU`](DEFI_MATERIAU.md) for the `RCCM` block.
- French reference: U4.83.11 (French text: `en/docs/_src/U4.83.11.fr.md`; translation: `en/docs/U4.83.11.md`)
- Catalog: `en/commands/POST_RCCM.json` (generated from `upstream/code_aster/Cata/Commands/post_rccm.py:26`)
- Implementation: `upstream/bibfor/op/op0165.F90`; `EVOLUTION` in `upstream/bibfor/postrele/rcevol.F90`
  (`rcevo2.F90` reads the tables, `rc32my.F90` and `rc32axis.F90` linearize, `rcevom.F90` and
  `rcevod.F90` write the table)
- Verification run: `docs/reference-checks/README.md` (`solid_static` wall line)
- Example: `upstream/astest/sslv100c.comm` (lines 39, 62, 83)
- Example: `upstream/astest/sslv04h.comm` (lines 316, 330)
- Example: `upstream/astest/rccm01a.comm` (lines 61, 73, 85)
