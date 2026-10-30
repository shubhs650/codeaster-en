---
command: THER_LINEAIRE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/ther_lineaire.py:50
doc_fr: U4.54.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3e)
examples: [tpla06a, forma02a, ttll01p, tpla01b]
---

# THER_LINEAIRE — linear thermal analysis

> **Assisted reference.** Written in session from the pinned catalog, the macro's Python
> implementation, the solver source it calls, upstream test cases and runs of our own on a slab
> with hand-computed answers (`docs/reference-checks/README.md`). Every behavior claim cites its
> source. Not reviewed by an engineer.

`THER_LINEAIRE` solves linear heat conduction: steady state (`TYPE_CALCUL='STAT'`) or a
transient (`'TRAN'`, the default) with a theta time scheme. It needs a thermal model
(`AFFE_MODELE` with `PHENOMENE='THERMIQUE'`), a material field whose materials have `THER`
(`LAMBDA`, conductivity; `RHO_CP`, volumetric heat capacity, used by transients) and the loads
of `AFFE_CHAR_THER` (imposed temperatures, fluxes, convection, sources). It returns an
`evol_ther` result whose field is `TEMP`, one stored step per time of `INCREMENT/LIST_INST`.
The usual next step in structural work is a thermal stress analysis: the result is given to the
mechanical material field with `AFFE_MATERIAU/AFFE_VARC` (`NOM_VARC='TEMP'`, `EVOL=`), and
`MECA_STATIQUE` then includes the thermal strains (pattern below). The decisions it encodes are
steady versus transient, the time list, the starting temperature field of a transient, and the
time scheme.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Résoudre un problème thermique linéaire stationnaire ou transitoire» |
| Kind | `MACRO` |
| Result | `evol_ther` |
| Can reuse its input (`reuse=`) | yes (the object given in `RESULTAT`); catalog `reentrant='f:RESULTAT'` |
| French reference | U4.54.01 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 2 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `TEMP_IMPO`, `FLUX_REP`, `ECHANGE`, `SOURCE` |

The COMMAND-SET keywords are those of the loads, in `AFFE_CHAR_THER`; see that reference.

## Keywords

The `SOLVEUR` keywords come from the common catalog
`upstream/code_aster/Cata/Commons/c_solveur.py`, as for `MECA_STATIQUE`; only `METHODE` is
listed here, and the [`MECA_STATIQUE`](MECA_STATIQUE.md) reference explains the others.

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MODELE` | `modele_sdaster`, required | — | *model*. A thermal model: `AFFE_MODELE` with `PHENOMENE='THERMIQUE'` (`MODELISATION='3D'`, `'PLAN'`, `'AXIS'`, ...; `upstream/astest/tpla06a.comm:49`). Include the face groups that carry fluxes or convection in the model, as for mechanical pressure faces. |
| `CHAM_MATER` | `cham_mater`, required | — | *material field*. Materials with `THER=_F(LAMBDA=..., RHO_CP=...)` (`upstream/astest/tpla06a.comm:40`). One material can carry both `ELAS` and `THER` and serve the thermal and the mechanical analyses (`upstream/astest/forma02a.comm:32`). |
| `CARA_ELEM` | `cara_elem`, optional | — | *element properties*. Only for thermal shells (thickness). Not needed for solids. |
| `EXCIT` | factor keyword, required, repeatable | — | *applied loads*. One occurrence per load object. |
| `EXCIT / CHARGE` | `char_ther` or `char_cine_ther`, required | — | *load*. A thermal load from `AFFE_CHAR_THER` (`AFFE_CHAR_THER_F` for loads given as functions, `AFFE_CHAR_CINE` for imposed temperatures without Lagrange multipliers). Several loads add up. |
| `EXCIT / FONC_MULT` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional | — | *load multiplier function*. A function of `'INST'` that multiplies the whole load. Checked by our run: a flux multiplied by a ramp 0 → 2 over times 0, 1, 2 gave top temperatures 0, 20, 40 in a steady analysis. |
| `EXCIT / TYPE_CHARGE` | text, optional | `'FIXE_CSTE'` | *load type*. One of `'FIXE_CSTE'`. The only value. |
| `TYPE_CALCUL` | text, optional | `'TRAN'` | One of `'STAT'`, `'TRAN'`. `'STAT'`: steady state, solved independently at each time of `LIST_INST` (loads and `FONC_MULT` taken at that time); stored from index 1 (`upstream/code_aster/MacroCommands/ther_lineaire_ops.py:366`). `'TRAN'`: transient, from the initial state at the first time, stored from index 0. Use `'STAT'` for a thermal stress analysis in service conditions; `'TRAN'` for start-up, shut-down or a thermal shock. |
| `ETAT_INIT` | factor keyword, required | `STAT='OUI'` (filled in when absent, `upstream/code_aster/Cata/Commands/ther_lineaire.py:43`) | *initial state*. Only when `TYPE_CALCUL='TRAN'`. The temperature field at the first time. Exactly one of `STAT`, `EVOL_THER`, `CHAM_NO`, `VALE`. |
| `ETAT_INIT / STAT` | text, optional | — | One of `'OUI'`. Start from the steady state of the loads at the first time (`ther_lineaire_ops.py:109`, `:420`). This is the default; with loads that do not change in time, nothing then happens in the transient (see Pitfalls). |
| `ETAT_INIT / VALE` | real, optional | — | *value(s)*. A uniform starting temperature: the usual choice for a body at ambient temperature that starts to heat (`upstream/astest/forma02a.comm:57`). |
| `ETAT_INIT / EVOL_THER` | `evol_ther`, optional | — | *thermal result*. Start from a step of an earlier thermal result: the last one, or the one given by `NUME_ORDRE` or `INST` (`ther_lineaire_ops.py:135`–`:145`). Use it to chain transients. |
| `ETAT_INIT / NUME_ORDRE` | integer, optional | — | *step index*. With `EVOL_THER`: the step to start from. |
| `ETAT_INIT / INST` | real, optional | — | *time step (pseudo-time)*. With `EVOL_THER`: the time to start from. |
| `ETAT_INIT / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. With `INST`: how `PRECISION` is read when matching the time. |
| `ETAT_INIT / PRECISION` | real | `1e-06` (relative) | *tolerance*. The tolerance of that match; required with `CRITERE='ABSOLU'`. |
| `ETAT_INIT / CHAM_NO` | `cham_no_sdaster`, optional | — | A nodal temperature field, for example made by `CREA_CHAMP`, as the starting state. |
| `SCHEMA_TEMPS` | factor keyword, optional, present by default | — | Only when `TYPE_CALCUL='TRAN'`. The time integration scheme. |
| `SCHEMA_TEMPS / SCHEMA` | text, optional | `'THETA'` | One of `'THETA'`. The theta method, the only one. |
| `SCHEMA_TEMPS / THETA` | real, optional | `0.57` | Range: ≥ 0.0, ≤ 1.0. The weight of the end of the step: 0.5 is Crank–Nicolson, 1.0 implicit (backward) Euler. With the default 0.57 and time steps large for the elements, the solution oscillates: in our slab run (12.5 mm elements, 360 s steps, 0 → 50 °C) the surface went 59, 43, 55, 47, ... around the steady 50, while `THETA=1.0` rose monotonically (38.6, 46.5, 48.9, ...). Use `THETA=1.0` for thermal shocks and coarse time steps, or smaller steps. |
| `INCREMENT` | factor keyword, required | — | *time stepping*. The times to solve at. Required for steady analyses too (one time is enough, `upstream/astest/tpla06a.comm:60`). |
| `INCREMENT / LIST_INST` | `listr8_sdaster` or `list_inst`, required | — | *time-step list*. A `DEFI_LIST_REEL` (or `DEFI_LIST_INST`) list. Time is in the units of `LAMBDA` and `RHO_CP` (seconds with SI-based units). |
| `INCREMENT / INST_INIT` | real, optional | — | The time of the list to start from; ignored for `'STAT'` (`ther_lineaire_ops.py:179`). |
| `INCREMENT / NUME_INST_INIT` | integer, optional | — | The index in the list to start from. |
| `INCREMENT / INST_FIN` | real, optional | — | *end time*. The time of the list to stop at. |
| `INCREMENT / NUME_INST_FIN` | integer, optional | — | The index in the list to stop at. |
| `INCREMENT / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`. With `INST_INIT` or `INST_FIN`. |
| `INCREMENT / PRECISION` | real, optional | `1e-06` | *tolerance*. Relative tolerance when matching `INST_INIT`/`INST_FIN` to the list. |
| `RESULTAT` | `evol_ther`, optional | — | *result*. An existing thermal result to which the new steps are added (catalog help), with `reuse=`. Then `ETAT_INIT` must be given and must not be `STAT` (`ther_lineaire_ops.py:48`–`:50`); start from the same result with `EVOL_THER`. |
| `SOLVEUR` | factor keyword, optional, present by default | — | *linear solver*. Settings of the linear solver, as in `MECA_STATIQUE`. |
| `SOLVEUR / METHODE` | text, optional | `'MUMPS'` | *method*. One of `'MULT_FRONT'`, `'LDLT'`, `'MUMPS'`, `'GCPC'`, `'PETSC'`. Keep the default. |
| `ARCHIVAGE` | factor keyword, optional, present by default | — | *result storage*. Which steps are stored; by default every step (`PAS_ARCH=1`, `upstream/code_aster/Cata/Commons/c_archivage.py:30`). |
| `ARCHIVAGE / PAS_ARCH` | integer, optional | — | Store every n-th step. Our run with 10 s steps and `PAS_ARCH=36` stored every 360 s. |
| `ARCHIVAGE / LIST_INST` | `listr8_sdaster`, optional | — | *time-step list*. Store only these times. |
| `ARCHIVAGE / INST` | real, optional, list | — | *time step (pseudo-time)*. Store only these times. |
| `ARCHIVAGE / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Matching of `INST`/`LIST_INST`. |
| `ARCHIVAGE / PRECISION` | real | `1e-06` (relative) | *tolerance*. Required with `CRITERE='ABSOLU'`. |
| `ARCHIVAGE / CHAM_EXCLU` | text, optional, list | `('RESI_NOEU', 'RESI_RELA_NOEU')` | Fields not stored. Leave the default. |
| `TITRE` | text, optional | — | *title*. Title of the result (default `RESU_THER_LINEAIRE`, `ther_lineaire_ops.py:340`). |
| `INFO` | integer, optional | — | *verbosity*. One of `1`, `2`. `2` also prints timing statistics (`ther_lineaire_ops.py:512`). |

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- `ETAT_INIT`: exactly one of `STAT`, `EVOL_THER`, `CHAM_NO`, `VALE` must be given (`UN_PARMI`).
- `INCREMENT`: at most one of `NUME_INST_INIT`, `INST_INIT`; at most one of `NUME_INST_FIN`, `INST_FIN` (`EXCLUS`).
- `ARCHIVAGE`: exactly one of `PAS_ARCH`, `LIST_INST`, `INST` (`UN_PARMI`, `PAS_ARCH=1` by default).

## Patterns

### Steady state

Imposed temperatures and convection, one time, `TYPE_CALCUL='STAT'`.

Source: `upstream/astest/tpla06a.comm:51`.

```python
CHTH = AFFE_CHAR_THER(
    MODELE=MOTH,
    TEMP_IMPO=(_F(GROUP_NO="NOE_ADF", TEMP=0.0), _F(GROUP_NO="NOE_BCE", TEMP=500.0)),
    ECHANGE=_F(GROUP_MA="MA_DFEC", COEF_H=10.0, TEMP_EXT=0.0),
)

LINST = DEFI_LIST_REEL(VALE=0.0)

TEMPE = THER_LINEAIRE(
    MODELE=MOTH,
    CHAM_MATER=CHMAT,
    EXCIT=_F(CHARGE=CHTH),
    TYPE_CALCUL="STAT",
    INCREMENT=_F(LIST_INST=LINST),
)
```

### Transient from a uniform temperature, then thermal stresses

A pipe bend: the inner surface temperature rises from 20 to 70 in 10 s, the body starts at a
uniform 20 (`ETAT_INIT=_F(VALE=20)`); the result then drives the mechanical analysis through
`AFFE_VARC`, with 20 as the stress-free reference temperature. The material carries `ELAS`
(with `ALPHA`) and `THER`.

Source: `upstream/astest/forma02a.comm:44` (thermal) and `:67` (material field).

```python
F_TEMP = DEFI_FONCTION(NOM_PARA="INST", VALE=(0, 20, 10, 70))

CHARTH = AFFE_CHAR_THER_F(MODELE=MODTH, TEMP_IMPO=_F(GROUP_MA="SURFINT", TEMP=F_TEMP))

LINST = DEFI_LIST_REEL(VALE=(0, 5, 10))

F_MULT = DEFI_FONCTION(NOM_PARA="INST", VALE=(0, 1, 10, 1))

TEMPE = THER_LINEAIRE(
    MODELE=MODTH,
    CHAM_MATER=CHMATER,
    EXCIT=_F(CHARGE=CHARTH, FONC_MULT=F_MULT),
    INCREMENT=_F(LIST_INST=LINST),
    ETAT_INIT=_F(VALE=20),
)
```

```python
CHMECATH = AFFE_MATERIAU(
    MAILLAGE=MAIL,
    MODELE=MODMECA,
    AFFE=_F(TOUT="OUI", MATER=MATER),
    AFFE_VARC=_F(TOUT="OUI", NOM_VARC="TEMP", EVOL=TEMPE, VALE_REF=20),
)
```

### Transient from the steady state

`ETAT_INIT=_F(STAT='OUI')` (also the default): the transient starts from the steady solution of
the loads at the first time, and the time-varying multiplier `TIMPVAR` drives the evolution.

Source: `upstream/astest/ttll01p.comm:58`.

```python
TEMPE = THER_LINEAIRE(
    MODELE=MOTH,
    ETAT_INIT=_F(STAT="OUI"),
    INCREMENT=_F(LIST_INST=LR8),
    CHAM_MATER=CHMAT,
    EXCIT=_F(CHARGE=CHTH, FONC_MULT=TIMPVAR),
)
```

## Pitfalls

- **The default transient starts in steady state.** Without `ETAT_INIT`, a transient starts from
  the steady state of the loads at the first time (`upstream/code_aster/Cata/Commands/ther_lineaire.py:43`).
  If the loads do not change in time, the result is the same at every step: our run with
  constant convection gave 50.0 at all eleven times. For a heat-up from ambient, give
  `ETAT_INIT=_F(VALE=<ambient>)`.
- **Oscillations with the default `THETA`.** See `SCHEMA_TEMPS / THETA`: large steps on a fine
  mesh give values beyond the final temperature. Check a transient with `THETA=1.0` or a finer
  time list.
- **Radiation is refused.** A load with `RAYONNEMENT` stops the command with `CHARGES9_42`
  ("condition of type RAYONNEMENT that is not possible in this linear operator";
  `upstream/bibfor/listLoad/listLoad_module.F90:1729`–`:1733`; reproduced in our run). Radiation,
  and fluxes or sources that depend on temperature, need `THER_NON_LINE` (Tier 3).
- **`INCREMENT` is required even in steady state.** Give a one-value list,
  `DEFI_LIST_REEL(VALE=0.0)`.
- **Units are the user's.** `LAMBDA`, `RHO_CP`, fluxes and exchange coefficients must use one
  consistent system; with lengths in mm (as in our fixtures), conductivity is in W/(mm·K):
  50 W/(m·K) is 0.05.

## See also

- [`AFFE_CHAR_THER`](AFFE_CHAR_THER.md) for the loads; [`AFFE_MATERIAU`](AFFE_MATERIAU.md)
  (`AFFE_VARC`) to use the result in a mechanical analysis; [`MECA_STATIQUE`](MECA_STATIQUE.md)
  for the `SOLVEUR` keywords.
- French reference: U4.54.01 (French text: `en/docs/_src/U4.54.01.fr.md`; translation: `en/docs/U4.54.01.md`)
- Catalog: `en/commands/THER_LINEAIRE.json` (generated from `upstream/code_aster/Cata/Commands/ther_lineaire.py:50`)
- Implementation: `upstream/code_aster/MacroCommands/ther_lineaire_ops.py`
- Verification runs: `docs/reference-checks/README.md` (thermal slab)
- Example: `upstream/astest/tpla06a.comm` (lines 51, 60, 65)
- Example: `upstream/astest/forma02a.comm` (lines 44, 52, 67)
- Example: `upstream/astest/ttll01p.comm` (lines 58)
- Example: `upstream/astest/tpla01b.comm` (lines 43)
