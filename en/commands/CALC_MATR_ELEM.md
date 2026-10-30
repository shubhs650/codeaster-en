---
command: CALC_MATR_ELEM
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/calc_matr_elem.py:68
doc_fr: U4.61.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 6.4)
examples: [sslx102c, func01e, zzzz289d]
---

# CALC_MATR_ELEM — compute element matrices

> **Assisted reference.** Written in session from the pinned catalog, the solver source it
> calls, the message catalog, upstream test cases and the committed fixture runs. Every behavior
> claim cites its source. Not reviewed by an engineer.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

Computes element matrices.

`CALC_MATR_ELEM` computes one kind of element matrix (stiffness, mass, damping, geometric
stiffness, ...) for every element of a model, without assembling it. It is the first of the
three steps of the explicit matrix path (`CALC_MATR_ELEM` → `NUME_DDL` → `ASSE_MATRICE`) that
gives the assembled matrices `CALC_MODES` needs; `ASSEMBLAGE` runs the three steps in one call.
`OPTION` picks the matrix; the model, material field and element properties give its terms; and
`CHARGE` adds the terms of dualized boundary conditions (Lagrange multipliers) to the stiffness
(`upstream/code_aster/MacroCommands/calc_matr_elem_ops.py:67`). In Tier 2 only `RIGI_MECA` and
`MASS_MECA` are used, as in the modal fixture (`tests/fixtures/modal/input/run.comm:33`).

| Fact | Value |
|---|---|
| Catalog description (fr) | «Calcul des matrices élémentaires» |
| Kind | `MACRO` |
| Result | `matr_elem_depl_r`, `matr_elem_depl_c`, `matr_elem_temp_r`, `matr_elem_pres_c` (depends on the keywords given) |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.61.01 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 2 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `MATR_ASSE`, `RIGI_MECA`, `MASS_MECA`, `CHARGE` |

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `OPTION` | text, required | — | *option*. One of `'RIGI_MECA'`, `'MASS_MECA'`, `'RIGI_GEOM'`, `'MASS_THER'`, `'AMOR_MECA'`, `'RIGI_THER'`, `'IMPE_MECA'`, `'ONDE_FLUI'`, `'MASS_FLUI_STRU'`, `'RIGI_FLUI_STRU'`, `'RIGI_ROTA'`, `'MECA_GYRO'`, … (18 values; see the .json). The matrix to compute (`upstream/code_aster/MacroCommands/calc_matr_elem_ops.py:67`–`:155`). Tier 2: `'RIGI_MECA'` elastic stiffness (with the Lagrange terms of `CHARGE`) and `'MASS_MECA'` consistent mass from `RHO` (`tests/fixtures/modal/input/run.comm:33`, `:35`). Also: `'MASS_MECA_DIAG'` lumped mass (`upstream/astest/sdlv100a.comm:72`); `'AMOR_MECA'` Rayleigh and discrete damping; `'RIGI_GEOM'` geometric stiffness from a prestress (buckling); `'RIGI_MECA_HYST'` hysteretic (complex) stiffness; `'RIGI_ROTA'`, `'MECA_GYRO'`, `'RIGI_GYRO'` rotating-machinery terms; thermal (`RIGI_THER`, `MASS_THER`), acoustic (`*_ACOU`) and fluid-structure (`*_FLUI_STRU`, `IMPE_MECA`, `ONDE_FLUI`) options. The result type follows the option (`matr_elem_depl_r` for the mechanical ones, `matr_elem_depl_c` for `RIGI_MECA_HYST`). |
| `MODELE` | `modele_sdaster`, required | — | *model*. The model whose elements are computed. |
| `INST` | real, optional | `0.0` | *time step (pseudo-time)*. Time at which time-dependent material data (external state variables such as temperature) are evaluated (`calc_matr_elem_ops.py:63`). Leave the default for a linear elastic material. |
| `GROUP_MA` | element group, optional, list | — | *element group*. Only when `equal_to("OPTION", 'RIGI_MECA')`; or `(equal_to("OPTION", 'MASS_MECA')) or (equal_to("OPTION", 'MASS_MECA_DIAG'))`; or `equal_to("OPTION", 'RIGI_GEOM')`; or `equal_to("OPTION", 'MECA_GYRO')`; or `equal_to("OPTION", 'RIGI_GYRO')`; or `equal_to("OPTION", 'AMOR_MECA')`; or `equal_to("OPTION", 'RIGI_MECA_HYST')`; or `equal_to("OPTION", 'MASS_FLUI_STRU')`; or `(equal_to("OPTION", 'IMPE_MECA')) or (equal_to("OPTION", 'ONDE_FLUI'))`. Compute the matrix on these element groups only; by default, every element of the model (`calc_matr_elem_ops.py:56`). Used to build a matrix of one part. |
| `CHAM_MATER` | `cham_mater`, optional | — | *material field*. Only when `equal_to("OPTION", 'RIGI_MECA')`; or `(equal_to("OPTION", 'MASS_MECA')) or (equal_to("OPTION", 'MASS_MECA_DIAG'))`; or `equal_to("OPTION", 'RIGI_GEOM')`; or `equal_to("OPTION", 'AMOR_MECA')`; or `equal_to("OPTION", 'RIGI_MECA_HYST')`. The material field: `E`, `NU` for the stiffness, `RHO` for the mass (`upstream/astest/sdlv100a.comm:68`). Missing material data stops the elementary computation (`CALCUL_20`, see [AFFE_MATERIAU](AFFE_MATERIAU.md)). |
| `CARA_ELEM` | `cara_elem`, optional | — | *element properties*. Only when `equal_to("OPTION", 'RIGI_MECA')`; or `(equal_to("OPTION", 'MASS_MECA')) or (equal_to("OPTION", 'MASS_MECA_DIAG'))`; or `equal_to("OPTION", 'RIGI_GEOM')`; or `equal_to("OPTION", 'RIGI_ROTA')`; or `equal_to("OPTION", 'MECA_GYRO')`; or `equal_to("OPTION", 'RIGI_GYRO')`; or `equal_to("OPTION", 'AMOR_MECA')`; or `equal_to("OPTION", 'RIGI_MECA_HYST')`; or `equal_to("OPTION", 'RIGI_THER')`; or `equal_to("OPTION", 'MASS_THER')`. Element properties: shell thickness, beam sections, discrete stiffness and mass values. Required when the model has structural elements (`upstream/astest/sdll02b.comm:56`). |
| `MODE_FOURIER` | integer, optional | `0` | Only when `equal_to("OPTION", 'RIGI_MECA')`; or `equal_to("OPTION", 'RIGI_GEOM')`; or `equal_to("OPTION", 'RIGI_THER')`. Fourier harmonic number for axisymmetric Fourier models (`AXIS_FOURIER`). Not used in Tier 2. |
| `CHARGE` | `char_meca`, optional, list | — | *load*. Only when `equal_to("OPTION", 'RIGI_MECA')`; or `(equal_to("OPTION", 'MASS_MECA')) or (equal_to("OPTION", 'MASS_MECA_DIAG'))`; or `equal_to("OPTION", 'MECA_GYRO')`; or `equal_to("OPTION", 'RIGI_GYRO')`; or `equal_to("OPTION", 'AMOR_MECA')`; or `equal_to("OPTION", 'RIGI_MECA_HYST')`; or `(equal_to("OPTION", 'IMPE_MECA')) or (equal_to("OPTION", 'ONDE_FLUI'))`. The mechanical loads whose boundary conditions are dualized (`DDL_IMPO`, `LIAISON_*`, `LIAISON_RBE3`): their Lagrange terms are added to the `RIGI_MECA` matrix, so `NUME_DDL` numbers the multipliers too (fixture `.mess`: "222 sont les couples de paramètres de Lagrange associés aux 111 relations linéaires dualisées", `tests/fixtures/modal/output/run.mess:286`). Give the same loads to the `MASS_MECA` call, as upstream does (`upstream/astest/sdlv100a.comm:70`); the mass itself does not use them (`calc_matr_elem_ops.py:97`). Applied forces in these loads are ignored here: a matrix has no right-hand side. Kinematic conditions (`AFFE_CHAR_CINE`) are not given here but to `ASSE_MATRICE` (`CHAR_CINE`). |
| `CALC_ELEM_MODELE` | text, optional | `'OUI'` | Stiffness matrix computed outside the model. One of `'OUI'`, `'NON'`. Only when `equal_to("OPTION", 'RIGI_MECA')`. `'NON'`: only the Lagrange (dual) terms of `CHARGE`, without the element stiffness of the model (`calc_matr_elem_ops.py:75`). Used to assemble the boundary conditions on their own. Keep `'OUI'`. |
| `SIEF_ELGA` | `cham_elem`, required | — | *stress at Gauss points*. Only when `equal_to("OPTION", 'RIGI_GEOM')`. The prestress (stresses at Gauss points, `SIEF_ELGA` from a static result) that the geometric stiffness is built from. Buckling (Tier 3). |
| `STRX_ELGA` | `cham_elem`, optional | — | Only when `equal_to("OPTION", 'RIGI_GEOM')`. Generalized stresses of beam elements for the geometric stiffness. Buckling (Tier 3). |
| `DEPL` | `cham_no_sdaster`, optional | — | *displacement*. Only when `equal_to("OPTION", 'RIGI_GEOM')`. A displacement field used for the geometric stiffness of some structural elements. Not described in U4.61.01 (v16), which documents only `SIEF_ELGA` for `RIGI_GEOM` (§3.7). Of all element catalogs, only the cable elements (`CABLE` modeling type) declare the displacement as an input of `RIGI_GEOM` (`upstream/catalo/cataelem/Elements/meca_cable.py:291`, routine `te0086`); other elements ignore it. Buckling (Tier 3). |
| `CHAM_MATER` | `cham_mater`, required | — | *material field*. Only when `equal_to("OPTION", 'RIGI_ROTA')`; or `equal_to("OPTION", 'MECA_GYRO')`; or `equal_to("OPTION", 'RIGI_GYRO')`; or `equal_to("OPTION", 'RIGI_THER')`; or `equal_to("OPTION", 'MASS_THER')`; or `equal_to("OPTION", 'RIGI_ACOU')`; or `(equal_to("OPTION", 'MASS_ACOU')) or (equal_to("OPTION", 'AMOR_ACOU'))`; or `equal_to("OPTION", 'RIGI_FLUI_STRU')`; or `equal_to("OPTION", 'MASS_FLUI_STRU')`; or `(equal_to("OPTION", 'IMPE_MECA')) or (equal_to("OPTION", 'ONDE_FLUI'))`. The material field, required for these options. |
| `CHARGE` | `char_meca`, required, list | — | *load*. Only when `equal_to("OPTION", 'RIGI_ROTA')`; or `equal_to("OPTION", 'RIGI_FLUI_STRU')`; or `equal_to("OPTION", 'MASS_FLUI_STRU')`. The loads that define the rotating or fluid-structure terms, required for these options. |
| `RIGI_MECA` | `matr_elem_depl_r`, optional | — | *mechanical stiffness matrix*. Only when `equal_to("OPTION", 'AMOR_MECA')`. Element stiffness matrix used for the stiffness-proportional part of Rayleigh damping (`AMOR_ALPHA` × K); together with `CHAM_MATER` (catalog rule `ENSEMBLE`). |
| `MASS_MECA` | `matr_elem_depl_r`, optional | — | *mechanical mass matrix*. Only when `equal_to("OPTION", 'AMOR_MECA')`. Element mass matrix used for the mass-proportional part of Rayleigh damping (`AMOR_BETA` × M). |
| `AMOR_FLUI` | text, optional | `'OUI'` | One of `'OUI'`, `'NON'`. Only when `equal_to("OPTION", 'AMOR_MECA')`. Include (`'OUI'`) or not the damping of fluid elements. Fluid-structure; out of scope. |
| `VNOR` | real, optional | `1.0` | One of `1.0`, `-1.0`. Only when `equal_to("OPTION", 'AMOR_MECA')`; or `(equal_to("OPTION", 'MASS_ACOU')) or (equal_to("OPTION", 'AMOR_ACOU')) and equal_to("OPTION", 'AMOR_ACOU')`; or `(equal_to("OPTION", 'IMPE_MECA')) or (equal_to("OPTION", 'ONDE_FLUI')) and equal_to("OPTION", 'IMPE_MECA')`. Sign (+1 or −1) of the normal velocity of the impedance or absorbing boundary. Fluid-structure and acoustics; out of scope. |
| `TYPE_AMOR` | text, optional | `'TOUT'` | One of `'TOUT'`, `'ABSO'`. Only when `equal_to("OPTION", 'AMOR_MECA')`. `'TOUT'`: full damping matrix (Rayleigh terms and discrete dampers); `'ABSO'`: absorbing-boundary terms only, which need just the material field; `'TOUT'` needs the stiffness and mass matrices (Rayleigh) or the discrete element properties (U4.61.01 §3.10). |
| `RIGI_MECA` | `matr_elem_depl_r`, required | — | *mechanical stiffness matrix*. Only when `equal_to("OPTION", 'RIGI_MECA_HYST')`. The element stiffness matrix that the hysteretic stiffness is built from (with the `AMOR_HYST` coefficient of `DEFI_MATERIAU/ELAS`, `upstream/code_aster/Cata/Commands/defi_materiau.py:420`). |
| `CHARGE` | `char_ther`, optional, list | — | *load*. Only when `equal_to("OPTION", 'RIGI_THER')`. The loads that define the rotating or fluid-structure terms, required for these options. |
| `CHARGE` | `char_acou`, optional, list | — | *load*. Only when `equal_to("OPTION", 'RIGI_ACOU')`; or `(equal_to("OPTION", 'MASS_ACOU')) or (equal_to("OPTION", 'AMOR_ACOU'))`. The loads that define the rotating or fluid-structure terms, required for these options. |
| `CARA_ELEM` | `cara_elem`, required | — | *element properties*. Only when `equal_to("OPTION", 'RIGI_FLUI_STRU')`; or `equal_to("OPTION", 'MASS_FLUI_STRU')`. Element properties, required for the fluid-structure options. |

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- when `equal_to("TYPE_AMOR", ('TOUT'))`: at least one of `CARA_ELEM`, `RIGI_MECA` must be given (`AU_MOINS_UN`).
- when `equal_to("TYPE_AMOR", ('TOUT'))`: `RIGI_MECA`, `CHAM_MATER` are given all together or not at all (`ENSEMBLE`).
- when `equal_to("TYPE_AMOR", 'ABSO')`: at least one of `CHAM_MATER` must be given (`AU_MOINS_UN`).

With `OPTION='AMOR_MECA'`, `TYPE_AMOR='TOUT'` (default) needs `CARA_ELEM` or `RIGI_MECA`, and
`RIGI_MECA` goes with `CHAM_MATER`.

## Patterns

### Stiffness and mass of a solid model with a clamp

The modal fixture, written by the English builder (`Builder.modal`). Source:
`tests/fixtures/modal/input/run.comm:33`.

```python
RIGI_EL = CALC_MATR_ELEM(MODELE=MODE, CHAM_MATER=MATE, CHARGE=ENCAS, OPTION="RIGI_MECA")

MASS_EL = CALC_MATR_ELEM(MODELE=MODE, CHAM_MATER=MATE, CHARGE=ENCAS, OPTION="MASS_MECA")
```

### Consistent and lumped mass

Source: `upstream/astest/sdlv100a.comm:68`.

```python
MELR1 = CALC_MATR_ELEM(MODELE=MO, CHARGE=CH, CHAM_MATER=CHMAT, OPTION="RIGI_MECA")

MELM1 = CALC_MATR_ELEM(MODELE=MO, CHARGE=CH, CHAM_MATER=CHMAT, OPTION="MASS_MECA")

MELM2 = CALC_MATR_ELEM(MODELE=MO, CHARGE=CH, CHAM_MATER=CHMAT, OPTION="MASS_MECA_DIAG")
```

### Beam model, kinematic supports given at assembly

No `CHARGE`: the supports are `AFFE_CHAR_CINE` loads, given to `ASSE_MATRICE`. Source:
`upstream/astest/sdll02b.comm:56`.

```python
MELR2 = CALC_MATR_ELEM(MODELE=MO, CARA_ELEM=CARELEM, CHAM_MATER=CHMAT, OPTION="RIGI_MECA")

MELM2 = CALC_MATR_ELEM(MODELE=MO, CARA_ELEM=CARELEM, CHAM_MATER=CHMAT, OPTION="MASS_MECA")
```

## Pitfalls

- **Supports go in twice or not at all.** A dualized support given to `CALC_MATR_ELEM`
  (`CHARGE`) adds Lagrange equations to the stiffness; the mass has none. That is expected:
  `CALC_MODES` handles the multipliers. A support given nowhere leaves rigid-body modes at
  0 Hz. Kinematic supports (`AFFE_CHAR_CINE`) go to `ASSE_MATRICE` instead.
- **No `RHO`, no mass.** `MASS_MECA` needs `RHO` in `DEFI_MATERIAU/ELAS`; without it the
  elementary computation fails (`CALCUL_20`).
- **Shells, beams and discrete elements need `CARA_ELEM`.** Without it their element terms are
  missing (`CALCUL_21`), as in a static analysis.
- **Same options as `ASSEMBLAGE`.** `ASSEMBLAGE` calls this command once per `MATR_ASSE`
  occurrence with the same keywords
  (`upstream/code_aster/MacroCommands/assemblage_ops.py:143`); use it when the element matrices
  are not needed separately.

## See also

- French reference: U4.61.01 (from en/doc-ids.yaml, status: verified; French text:
  `en/docs/_src/U4.61.01.fr.md`; translation: `en/docs/U4.61.01.md`)
- Catalog: `en/commands/CALC_MATR_ELEM.json` (generated from `upstream/code_aster/Cata/Commands/calc_matr_elem.py:68`)
- Implementation: `upstream/code_aster/MacroCommands/calc_matr_elem_ops.py`
- Before: [AFFE_MODELE](AFFE_MODELE.md), [AFFE_MATERIAU](AFFE_MATERIAU.md),
  [AFFE_CARA_ELEM](AFFE_CARA_ELEM.md), [AFFE_CHAR_MECA](AFFE_CHAR_MECA.md)
- Next steps: [NUME_DDL](NUME_DDL.md), [ASSE_MATRICE](ASSE_MATRICE.md); all three in one call:
  [ASSEMBLAGE](ASSEMBLAGE.md)
- Example: `tests/fixtures/modal/input/run.comm` (line 33)
- Example: `upstream/astest/sdlv100a.comm` (line 68)
- Example: `upstream/astest/sdll02b.comm` (line 56)
