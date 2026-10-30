---
command: AFFE_CHAR_THER
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/affe_char_ther.py:26
doc_fr: U4.44.02
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3e)
examples: [tpla01b, tpla06a, hpla100b, tplv102a]
---

# AFFE_CHAR_THER — assign thermal loads and BCs

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source, upstream test cases and runs of our own on a slab with
> hand-computed answers (`docs/reference-checks/README.md`). Every behavior claim cites its
> source. Not reviewed by an engineer.

`AFFE_CHAR_THER` defines the boundary conditions and loads of a thermal analysis, with constant
values: imposed temperatures (`TEMP_IMPO`), heat fluxes through faces (`FLUX_REP`), convection
to a surrounding fluid (`ECHANGE`), heat generated in the volume (`SOURCE`), and linear relations
between temperatures (`LIAISON_*`). It returns a `char_ther` load for `THER_LINEAIRE` (`EXCIT`).
It is the thermal counterpart of `AFFE_CHAR_MECA`: imposed temperatures are dualized with
Lagrange multipliers, and fluxes and convection act on the face elements of the model, so the
face groups must be in the thermal model. A value that varies in time is obtained with
`EXCIT/FONC_MULT` in `THER_LINEAIRE`, a value that varies in space or with temperature with
`AFFE_CHAR_THER_F`. A face with no condition is adiabatic (zero flux). The decisions it encodes
are which surfaces are held at a temperature, which exchange heat and how, and where heat is
generated.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Affectation de charges et conditions aux limites thermiques constantes» |
| Kind | `OPER` |
| Result | `char_ther` |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.44.02 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 2 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `TEMP_IMPO`, `FLUX_REP`, `ECHANGE`, `SOURCE` |

Our slab run (`docs/reference-checks/thermal/`) checks the four COMMAND-SET keywords against
hand values: a block 100 mm thick, held at 0 on one face, with conductivity 0.05 W/(mm·K).
`FLUX_REP` 0.01 W/mm² on the other face gave 20.0 there (q·L/λ); `ECHANGE` with h = 5e-4 W/(mm²·K)
and 100 outside gave 50.0 (h·T_ext/(h + λ/L)); `SOURCE` 1e-4 W/mm³ with the other face
adiabatic gave 10.0 (s·L²/(2λ)).

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MODELE` | `modele_sdaster`, required | — | *model*. The thermal model (`PHENOMENE='THERMIQUE'`), with the face groups that carry `FLUX_REP`, `ECHANGE` or `RAYONNEMENT`. |
| `TEMP_IMPO` | factor keyword, optional, repeatable | — | *imposed temperature*. Holds nodes at a temperature (a Dirichlet condition): a surface in contact with a fluid at a known temperature when the film resistance is negligible, or a reference point. One occurrence per group and value. |
| `TEMP_IMPO / GROUP_MA` | element group, optional, list | — | *element group*. The nodes of these elements (faces, usually). |
| `TEMP_IMPO / GROUP_NO` | node group, optional, list | — | *node group*. These nodes (`upstream/astest/tpla06a.comm:53`). |
| `TEMP_IMPO / TOUT` | text, optional | `'OUI'` when no group is given | *all (entire mesh)*. One of `'OUI'`. Every node of the model. The catalog rule fills in `TOUT='OUI'` when neither `GROUP_MA` nor `GROUP_NO` is given (`upstream/code_aster/Cata/Commands/affe_char_ther.py:63`, `upstream/code_aster/Cata/Language/Rules.py:97`), so a forgotten group imposes the temperature everywhere. |
| `TEMP_IMPO / SANS_GROUP_MA` | element group, optional, list | — | *excluded element groups*. Removes the nodes of these elements from the selection. |
| `TEMP_IMPO / SANS_GROUP_NO` | node group, optional, list | — | *excluded node groups*. Removes these nodes from the selection. |
| `TEMP_IMPO / TEMP` | real, optional | — | *temperature*. The imposed value, in the user's temperature unit. At least one of `TEMP`, `TEMP_MIL`, `TEMP_INF`, `TEMP_SUP` (rule). |
| `TEMP_IMPO / TEMP_MIL` | real, optional | — | For thermal shell models: the temperature of the mid surface (degree of freedom `TEMP_MIL`). |
| `TEMP_IMPO / TEMP_INF` | real, optional | — | For thermal shell models: the temperature of the lower face (`upstream/astest/hpla100b.comm:84`, `COQUE_AXIS`). |
| `TEMP_IMPO / TEMP_SUP` | real, optional | — | For thermal shell models: the temperature of the upper face. |
| `FLUX_REP` | factor keyword, optional, repeatable | — | *distributed heat flux*. A heat flux per unit area through faces (edges in 2D): a heater, solar load, or a known heat loss. A positive `FLUN` enters the body (our slab run: +0.01 W/mm² raised the face to +20). |
| `FLUX_REP / GROUP_MA` | element group, optional, list | — | *element group*. The faces. Exactly one of `TOUT`, `GROUP_MA` (`TOUT='OUI'` filled in when absent, catalog rule). |
| `FLUX_REP / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. All face elements of the model. |
| `FLUX_REP / FLUN` | real, optional | — | The normal flux, power per unit area (W/mm² with lengths in mm), positive into the body. |
| `FLUX_REP / FLUN_INF` | real, optional | — | For thermal shells: the normal flux on the lower face. |
| `FLUX_REP / FLUN_SUP` | real, optional | — | For thermal shells: the normal flux on the upper face. |
| `FLUX_REP / CARA_TORSION` | `table_sdaster`, optional | — | A table used when beam section properties are computed by a thermal analogy (torsion constant). Not a heat load; outside Tier 2. TODO(verify) against U4.44.02. |
| `ECHANGE` | factor keyword, optional, repeatable | — | *convective heat exchange*. Heat exchange with a fluid at `TEMP_EXT` through a film coefficient `COEF_H`: the flux into the body is h·(T_ext − T) (our slab run: 50.0 against the hand value). The usual condition for a surface cooled or heated by air or water. |
| `ECHANGE / GROUP_MA` | element group, optional, list | — | *element group*. The faces in contact with the fluid. Exactly one of `TOUT`, `GROUP_MA`. |
| `ECHANGE / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. All face elements. |
| `ECHANGE / COEF_H` | real, optional | — | The film (heat transfer) coefficient h, power per unit area and degree (W/(mm²·K) with lengths in mm: 500 W/(m²·K) is 5e-4). Given with `TEMP_EXT` (rule `ENSEMBLE`). |
| `ECHANGE / TEMP_EXT` | real, optional | — | The fluid (bulk) temperature. |
| `ECHANGE / COEF_H_INF` | real, optional | — | For thermal shells: h on the lower face, with `TEMP_EXT_INF`. |
| `ECHANGE / TEMP_EXT_INF` | real, optional | — | For thermal shells: the fluid temperature on the lower face. |
| `ECHANGE / COEF_H_SUP` | real, optional | — | For thermal shells: h on the upper face, with `TEMP_EXT_SUP`. |
| `ECHANGE / TEMP_EXT_SUP` | real, optional | — | For thermal shells: the fluid temperature on the upper face. |
| `SOURCE` | factor keyword, optional, repeatable | — | *heat source*. Heat generated in the volume, power per unit volume: Joule heating, nuclear heating, a curing reaction. |
| `SOURCE / GROUP_MA` | element group, optional, list | — | *element group*. The elements that generate heat (`TOUT` and `GROUP_MA` exclude each other). |
| `SOURCE / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. |
| `SOURCE / SOUR` | real, optional | — | The power per unit volume (W/mm³ with lengths in mm). Exactly one of `SOUR`, `SOUR_CALCULEE`. |
| `SOURCE / SOUR_CALCULEE` | `cham_elem` or `cham_no_sdaster`, optional | — | A source field computed elsewhere (for example by an electrical analysis), applied where it is defined (`TOUT`/`GROUP_MA` not allowed with it). |
| `RAYONNEMENT` | factor keyword, optional, repeatable | — | Radiation to surroundings at `TEMP_EXT`, with the Stefan–Boltzmann constant `SIGMA` and emissivity `EPSILON` (catalog help: give temperatures in Celsius when there is radiation). Nonlinear in temperature: `THER_LINEAIRE` refuses it (`CHARGES9_42`, see Pitfalls); use it with `THER_NON_LINE` (Tier 3). |
| `RAYONNEMENT / GROUP_MA` | element group, optional, list | — | *element group*. The radiating faces. |
| `RAYONNEMENT / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. |
| `RAYONNEMENT / SIGMA` | real, required | — | The Stefan–Boltzmann constant in the user's units (5.67e-8 W/(m²·K⁴), 5.67e-14 W/(mm²·K⁴)). |
| `RAYONNEMENT / EPSILON` | real, required | — | The surface emissivity, 0 to 1. |
| `RAYONNEMENT / TEMP_EXT` | real, required | — | The temperature of the surroundings. |
| `LIAISON_DDL` | factor keyword, optional, repeatable | — | *linear DOF relation*. A linear relation between temperatures of nodes: Σ `COEF_MULT`·T = `COEF_IMPO`, as in `AFFE_CHAR_MECA`. |
| `LIAISON_DDL / GROUP_NO` | node group, optional, list | — | *node group*. The nodes, one per term (a group may be repeated). |
| `LIAISON_DDL / DDL` | text, optional, list | — | One of `'TEMP'`, `'TEMP_MIL'`, `'TEMP_INF'`, `'TEMP_SUP'`, `'H1'`. The degree of freedom of each term; `'TEMP'` for solids. |
| `LIAISON_DDL / COEF_MULT` | real, required, list | — | *multiplying coefficients*. One per term. |
| `LIAISON_DDL / COEF_IMPO` | real, required | — | *imposed value*. The right-hand side. |
| `LIAISON_GROUP` | factor keyword, optional, repeatable | — | The same relation applied node by node between two groups (pairs found by geometry, with an optional transformation `TRAN`, `ANGL_NAUT`, `CENTRE`): for example equal temperatures on two opposite faces of a periodic model. |
| `LIAISON_GROUP / GROUP_MA_1` | element group, optional, list | — | The first side (elements). Exactly one of `GROUP_MA_1`, `GROUP_NO_1`. |
| `LIAISON_GROUP / GROUP_NO_1` | node group, optional, list | — | The first side (nodes). |
| `LIAISON_GROUP / GROUP_MA_2` | element group, optional, list | — | The second side (elements). Exactly one of `GROUP_MA_2`, `GROUP_NO_2`. |
| `LIAISON_GROUP / GROUP_NO_2` | node group, optional, list | — | The second side (nodes). |
| `LIAISON_GROUP / SANS_GROUP_NO` | node group, optional, list | — | *excluded node groups*. Nodes left out of the pairing. |
| `LIAISON_GROUP / DDL_1` | text, optional, list | `'TEMP'` | The degree of freedom on side 1. |
| `LIAISON_GROUP / COEF_MULT_1` | real, required, list | — | The coefficient of side 1. |
| `LIAISON_GROUP / DDL_2` | text, optional, list | `'TEMP'` | The degree of freedom on side 2. |
| `LIAISON_GROUP / COEF_MULT_2` | real, required, list | — | The coefficient of side 2. |
| `LIAISON_GROUP / COEF_IMPO` | real, required | — | *imposed value*. The right-hand side of each relation. |
| `LIAISON_GROUP / TRAN` | real, list of 3 | — | A translation that maps side 1 onto side 2 for the pairing. |
| `LIAISON_GROUP / ANGL_NAUT` | real, list of 3 | — | Rotation angles (degrees) of that mapping. |
| `LIAISON_GROUP / CENTRE` | real, list of 3 | — | The center of that rotation. (The glossary label for the value `CENTRE`, about frequencies, does not apply here.) |
| `LIAISON_MAIL` | factor keyword, optional, repeatable | — | *mesh tie (bonded)*. Ties the temperatures of non-matching meshes: each secondary node takes the temperature interpolated in the main elements, as `LIAISON_MAIL` in `AFFE_CHAR_MECA` does for displacements (perfect thermal contact). |
| `LIAISON_MAIL / GROUP_MA_MAIT` | element group, optional, list | — | *main element group*. The elements interpolated from. |
| `LIAISON_MAIL / GROUP_MA_ESCL` | element group, optional, list | — | *secondary element group*. The elements whose nodes are tied. |
| `LIAISON_MAIL / GROUP_NO_ESCL` | node group, optional, list | — | *secondary node group*. Or the nodes directly. |
| `LIAISON_MAIL / TRAN` | real, optional, list | — | A translation applied to the secondary side before pairing. |
| `LIAISON_MAIL / ANGL_NAUT` | real, optional, list | — | Rotation angles of that transformation. |
| `LIAISON_MAIL / CENTRE` | real, optional, list | — | The center of that rotation. |
| `LIAISON_MAIL / ELIM_MULT` | text, optional | `'OUI'` | *skip already tied nodes*. One of `'OUI'`, `'NON'`. As in `AFFE_CHAR_MECA`. |
| `LIAISON_MAIL / DISTANCE_MAX` | real, optional | — | *maximum distance*. Secondary nodes farther than this from the main side are not tied. |
| `LIAISON_MAIL / DISTANCE_ALARME` | real, optional | — | A warning distance for the pairing. |
| `LIAISON_UNIF` | factor keyword, optional, repeatable | — | *uniform DOF coupling*. Gives all nodes of a group the same (unknown) temperature: a highly conductive part, or a well-mixed fluid volume modeled by its boundary. |
| `LIAISON_UNIF / GROUP_NO` | node group, optional, list | — | *node group*. Exactly one of `GROUP_NO`, `GROUP_MA`. |
| `LIAISON_UNIF / GROUP_MA` | element group, optional, list | — | *element group*. |
| `LIAISON_UNIF / DDL` | text, optional, list | `'TEMP'` | The degree of freedom made uniform. |
| `ECHANGE_PAROI` | factor keyword, optional, repeatable | — | Heat exchange between two facing walls of the mesh with a coefficient `COEF_H`: a gap or contact conductance between two parts. |
| `ECHANGE_PAROI / GROUP_MA_1` | element group, optional, list | — | The faces of the first wall. |
| `ECHANGE_PAROI / GROUP_MA_2` | element group, optional, list | — | The faces of the second wall. |
| `ECHANGE_PAROI / COEF_H` | real, required (meshed walls) | — | The exchange coefficient between the walls. With `FISSURE` (XFEM crack, outside scope) it is optional, as an alternative to `TEMP_CONTINUE`. |
| `ECHANGE_PAROI / TRAN` | real, list of 2 or 3 | — | A translation that maps wall 1 onto wall 2 for the pairing. |
| `ECHANGE_PAROI / FISSURE` | `fiss_xfem`, optional, list of up to 100 | — | An XFEM crack instead of meshed walls. Outside scope. |
| `ECHANGE_PAROI / TEMP_CONTINUE` | text, optional | — | One of `'OUI'`. With `FISSURE`: temperature continuous across the crack. Outside scope. |
| `PRE_GRAD_TEMP` | factor keyword, optional, repeatable | — | An imposed temperature gradient field (`FLUX_X`, `FLUX_Y`, `FLUX_Z`), used in homogenization studies. Outside Tier 2. TODO(verify) its meaning against U4.44.02. |
| `PRE_GRAD_TEMP / GROUP_MA` | element group, optional, list | — | *element group*. |
| `PRE_GRAD_TEMP / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. |
| `PRE_GRAD_TEMP / FLUX_X` | real, optional | — | X component. |
| `PRE_GRAD_TEMP / FLUX_Y` | real, optional | — | Y component. |
| `PRE_GRAD_TEMP / FLUX_Z` | real, optional | — | Z component. |
| `LIAISON_CHAMNO` | factor keyword, optional | — | A linear relation whose coefficients are the values of a nodal field. Outside Tier 2. |
| `LIAISON_CHAMNO / CHAM_NO` | `cham_no_sdaster`, required | — | The field of coefficients. |
| `LIAISON_CHAMNO / COEF_IMPO` | real, required | — | *imposed value*. The right-hand side. |
| `CONVECTION` | factor keyword, optional | — | Heat transported by a moving material at the velocity field `VITESSE`; used with `THER_NON_LINE_MO` (`upstream/astest/tplv102a.comm:63`, `:73`). Outside Tier 2. |
| `CONVECTION / VITESSE` | `cham_no_sdaster`, required | — | The velocity field. |
| `EVOL_CHAR` | `evol_char`, optional | — | Heat exchange or flux fields from another calculation (catalog help), for example a fluid analysis, stored as an `evol_char` result. Outside Tier 2. |
| `DOUBLE_LAGRANGE` | text, optional | `'OUI'` | *double Lagrange multipliers*. One of `'OUI'`, `'NON'`. How imposed temperatures and relations are dualized, as in `AFFE_CHAR_MECA`. Leave the default. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. |

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at least one of `EVOL_CHAR`, `TEMP_IMPO`, `SOURCE`, `FLUX_REP`, `ECHANGE`, `ECHANGE_PAROI`, `PRE_GRAD_TEMP`, `LIAISON_DDL`, `LIAISON_GROUP`, `LIAISON_UNIF`, `LIAISON_CHAMNO`, `RAYONNEMENT`, `LIAISON_MAIL`, `CONVECTION` must be given (`AU_MOINS_UN`).
- `TEMP_IMPO`: at least one of `TOUT`, `GROUP_MA`, `GROUP_NO` (`TOUT='OUI'` filled in when none is given); at least one of `TEMP`, `TEMP_MIL`, `TEMP_SUP`, `TEMP_INF`.
- `FLUX_REP`, `RAYONNEMENT`, `ECHANGE`, `PRE_GRAD_TEMP`: exactly one of `TOUT`, `GROUP_MA` (`TOUT='OUI'` filled in when none is given).
- `FLUX_REP`: at least one of `FLUN`, `FLUN_INF`, `FLUN_SUP`, `CARA_TORSION`; `CARA_TORSION` needs `GROUP_MA`.
- `ECHANGE`: at least one of `COEF_H`, `COEF_H_INF`, `COEF_H_SUP`; each `COEF_H*` together with its `TEMP_EXT*` (`ENSEMBLE`).
- `SOURCE`: exactly one of `SOUR`, `SOUR_CALCULEE`; `TOUT` and `GROUP_MA` exclude each other; `SOUR_CALCULEE` excludes both.
- `LIAISON_GROUP`: exactly one of `GROUP_MA_1`, `GROUP_NO_1`, and of `GROUP_MA_2`, `GROUP_NO_2`; `GROUP_MA_1` excludes `GROUP_NO_2`, `GROUP_NO_1` excludes `GROUP_MA_2`.
- `LIAISON_MAIL`: at least one of `GROUP_MA_ESCL`, `GROUP_NO_ESCL`.
- `ECHANGE_PAROI`: exactly one of `GROUP_MA_1`, `FISSURE`, and of `GROUP_MA_2`, `FISSURE`.
- `LIAISON_UNIF`: exactly one of `GROUP_NO`, `GROUP_MA`.

## Patterns

### Flux, convection and imposed temperature together

Three kinds of condition in one load: a zero flux and an incoming flux on two edges, convection
on a third, a temperature on a node group.

Source: `upstream/astest/tpla01b.comm:34`.

```python
CHTH = AFFE_CHAR_THER(
    MODELE=MOTH,
    FLUX_REP=(_F(GROUP_MA="GRMA13", FLUN=0.0), _F(GROUP_MA="GRMA14", FLUN=1729.9091)),
    ECHANGE=_F(GROUP_MA="GRMA12", COEF_H=500.0, TEMP_EXT=17.034444),
    TEMP_IMPO=_F(GROUP_NO="GRNM15", TEMP=100.0),
)
```

### One condition per load, combined in the analysis

Separate loads for the support and for each heat input, so that `THER_LINEAIRE` can combine
them, or multiply one of them by a function of time, in `EXCIT` (our slab run, values in mm, W
and K).

Source: `docs/reference-checks/thermal/run.comm:18`.

```python
BASE0 = AFFE_CHAR_THER(MODELE=MOTH, TEMP_IMPO=_F(GROUP_MA="BASE", TEMP=0.0))
# (a) flux 0.01 W/mm2 on TOP: T(TOP) = q L / lambda = 20 if FLUN > 0 enters the body
FLUX = AFFE_CHAR_THER(MODELE=MOTH, FLUX_REP=_F(GROUP_MA="TOP", FLUN=0.01))
# (b) convection h = 5e-4 W/(mm2.K), T_ext = 100: T(TOP) = h Text / (h + lambda/L) = 50
CONV = AFFE_CHAR_THER(MODELE=MOTH, ECHANGE=_F(GROUP_MA="TOP", COEF_H=5.0e-4, TEMP_EXT=100.0))
# (c) volume source 1e-4 W/mm3, TOP adiabatic: T(TOP) = s L^2 / (2 lambda) = 10
SOUR = AFFE_CHAR_THER(MODELE=MOTH, SOURCE=_F(GROUP_MA="BLOCK", SOUR=1.0e-4))
```

### Shell faces

Temperatures of the lower and upper faces of an axisymmetric thermal shell (`COQUE_AXIS`); the
through-thickness gradient then bends the shell in the mechanical analysis.

Source: `upstream/astest/hpla100b.comm:84`.

```python
CH_FIN1 = AFFE_CHAR_THER(MODELE=MOTHER, TEMP_IMPO=_F(TOUT="OUI", TEMP_INF=-0.5, TEMP_SUP=+0.5))
```

## Pitfalls

- **A missing group means the whole model.** `TEMP_IMPO`, `FLUX_REP`, `ECHANGE`,
  `RAYONNEMENT` and `PRE_GRAD_TEMP` without `GROUP_MA`/`GROUP_NO` act on everything: the
  catalog rules fill in `TOUT='OUI'` (`upstream/code_aster/Cata/Language/Rules.py:97`). A
  `TEMP_IMPO` without a group fixes every node, and the analysis returns that temperature
  everywhere.
- **Sign of `FLUN`.** Positive enters the body (checked by our run). A heat loss is a negative
  `FLUN`, or better an `ECHANGE` to the ambient.
- **Radiation needs the nonlinear solver.** `THER_LINEAIRE` stops with `CHARGES9_42` on a load
  with `RAYONNEMENT` (`upstream/bibfor/listLoad/listLoad_module.F90:1729`–`:1733`; reproduced in
  our run).
- **Face groups must be in the model.** As for mechanical pressure, `FLUX_REP` and `ECHANGE`
  act on face elements; include the face groups in `AFFE_MODELE` (our run assigns
  `GROUP_MA=("BLOCK", "BASE", "TOP")`, `docs/reference-checks/thermal/run.comm:11`).
- **Units.** Coefficients are per unit area in the length unit of the mesh: with mm,
  h = 500 W/(m²·K) is 5e-4 W/(mm²·K) and a flux of 10 kW/m² is 0.01 W/mm².

## See also

- [`THER_LINEAIRE`](THER_LINEAIRE.md), which solves with these loads;
  [`AFFE_CHAR_MECA`](AFFE_CHAR_MECA.md) for the same `LIAISON_*` keywords in mechanics.
- French reference: U4.44.02 (French text: `en/docs/_src/U4.44.02.fr.md`; translation: `en/docs/U4.44.02.md` once task 5.2 lands)
- Catalog: `en/commands/AFFE_CHAR_THER.json` (generated from `upstream/code_aster/Cata/Commands/affe_char_ther.py:26`)
- Implementation: `upstream/code_aster/CodeCommands/affe_char_ther.py` (operator 34)
- Verification run: `docs/reference-checks/README.md` (thermal slab)
- Example: `upstream/astest/tpla01b.comm` (lines 34)
- Example: `upstream/astest/tpla06a.comm` (lines 51)
- Example: `upstream/astest/hpla100b.comm` (lines 83, 84, 85)
- Example: `upstream/astest/tplv102a.comm` (lines 63)
