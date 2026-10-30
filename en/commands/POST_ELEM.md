---
command: POST_ELEM
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/post_elem.py:39
doc_fr: U4.81.22
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3d)
examples: [adlv312a, forma20a, perfe03a, petsc02f, ssll111a, cont006c, ssll107b]
---

# POST_ELEM — element-based post-processing

> **Assisted reference.** Written in session from the pinned catalog, the solver source it
> calls, the message catalog, upstream test cases and the committed fixture runs. Every behavior
> claim cites its source. Not reviewed by an engineer.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

`POST_ELEM` computes one global quantity over all or part of the model and writes it to a
table (`table_sdaster`): mass and inertia, an energy, the integral or mean of a field, its
extrema, its norm, or the volume distribution of a component. Exactly one option is given per
call (catalog rule); several occurrences of that option give several rows (one per group). The
input is a model with its material field and element properties (`MASS_INER`, `CARA_GEOM`), a
result (energies, `INTEGRALE`, `MINMAX`), or a field object (`CHAM_GD`). In Tier 1 it answers
two questions: does the model weigh what it should (`MASS_INER`), and what are the extreme or
mean values of a field on a region (`MINMAX`, `INTEGRALE`). The table then goes to
`IMPR_TABLE`, `TEST_TABLE` or Python.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Calcul de quantités globales (masse, inerties, énergie, ...) sur tout ou partie du modèle» |
| Kind | `OPER` (Fortran operator 107, `upstream/bibfor/op/op0107.F90`) |
| Result | `table_sdaster` (the catalog also allows `table_container`) |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.81.22 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `MASS_INER`, `VOLUMOGRAMME`, `NORME`, `FILTRE_MODE`, `CRIT_EXTR`, `MASS_EFFE_UN`, `SEUIL` (all but the first two come from the modal row of COMMAND-SET; see Pitfalls) |

## Keywords

The keywords outside the factor keywords (`MODELE`, `RESULTAT`, `INST`, …) belong to the option
given; their meaning depends on it, so `RESULTAT`, `NUME_ORDRE`, `INST` and a few others appear
once per option group, in catalog order.

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MASS_INER` | factor keyword, optional, repeatable | — | *mass and inertia properties*. Mass, center of gravity and inertia tensor of the selected elements, from the density `RHO` of the material field (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:82`). One table row per occurrence and group: columns `LIEU`, `ENTITE`, `MASSE`, `CDG_X`/`CDG_Y`/`CDG_Z`, the inertia tensor at the center of gravity (`IX_G` … `IYZ_G`), principal inertias (`IX_PRIN_G` …) and the three angles of the principal axes `ALPHA`, `BETA`, `GAMMA` (`upstream/bibfor/utilitai/pemain.F90:72`). The Tier 1 check that the model weighs what the drawing says (`tests/fixtures/modal/input/run.comm:29`). |
| `MASS_INER / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model: one row with `ENTITE='TOUT'`. |
| `MASS_INER / GROUP_MA` | element group, optional, list | — | *element group*. These groups: one row per group, with the group name in `LIEU` (`upstream/astest/adlv312a.comm:94`). |
| `MASS_INER / ORIG_INER` | real, optional, list of up to 3, at least 3 | — | A point (X, Y, Z). The table then also gives its coordinates (`X_P`, `Y_P`, `Z_P`) and the inertia tensor about that point (`IX_P` … `IYZ_P`) (`upstream/bibfor/utilitai/pemain.F90:72`, `:177`). Use it for the inertia about a support or a rotation axis. |
| `MODELE` | `modele_sdaster`, optional | — | *model*. Only when `exists("MASS_INER")`; or `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("ENER_DISS")`; or `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`; or `exists("ENER_TOTALE")`; or `exists("INTEGRALE")`; or `exists("VOLUMOGRAMME")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`; or `exists("INDIC_ENER")`; or `exists("INDIC_SEUIL")`; or `exists("CHAR_LIMITE")`; or `exists("CARA_GEOM")`; or `exists("CARA_POUTRE")`; or `exists("AIRE_INTERNE")`. The model. Required when no `RESULTAT` is given (`POSTELEM_20`, `upstream/bibfor/utilitai/medomp.F90:97`); with a `RESULTAT`, the model, material field and element properties stored in the result are used instead (`upstream/bibfor/utilitai/medomp.F90:156`). |
| `CHAM_MATER` | `cham_mater`, optional | — | *material field*. Only when `exists("MASS_INER")`; or `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("ENER_DISS")`; or `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`; or `exists("ENER_TOTALE")`; or `exists("INTEGRALE")`; or `exists("VOLUMOGRAMME")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`; or `exists("INDIC_ENER")`; or `exists("INDIC_SEUIL")`; or `exists("CHAR_LIMITE")`; or `exists("CARA_GEOM")`; or `exists("CARA_POUTRE")`. The material field. Give it with `MODELE` for mass and energy options: the mass comes from `RHO`. Missing when the model needs one: warning `CALCULEL3_40` (`upstream/bibfor/utilitai/medomp.F90:122`). |
| `CARA_ELEM` | `cara_elem`, optional | — | *element properties*. Only when `exists("MASS_INER")`; or `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("ENER_DISS")`; or `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`; or `exists("ENER_TOTALE")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`; or `exists("CHAR_LIMITE")`. The element properties. Required for shells, beams and discrete elements (thickness, section, point masses); missing on a model with structural elements gives warning `CALCULEL3_39` (`upstream/bibfor/utilitai/medomp.F90:113`). |
| `NUME_COUCHE` | integer, optional | `1` | Only when `exists("MASS_INER")`; or `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("ENER_DISS")`; or `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`; or `exists("ENER_TOTALE")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`. Layer number of a multilayer shell where the quantity is evaluated. Not used in Tier 1 (single-layer shells). |
| `NIVE_COUCHE` | text, optional | `'MOY'` | One of `'INF'`, `'SUP'`, `'MOY'`. Only when `exists("MASS_INER")`; or `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("ENER_DISS")`; or `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`; or `exists("ENER_TOTALE")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`. Position in the layer: lower face (`'INF'`), upper face (`'SUP'`) or mid-surface (`'MOY'`). Not used in Tier 1. |
| `MODE_FOURIER` | integer, optional | `0` | Only when `exists("MASS_INER")`; or `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("ENER_DISS")`; or `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`; or `exists("ENER_TOTALE")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`; or `exists("INDIC_ENER")`; or `exists("INDIC_SEUIL")`; or `exists("CHAR_LIMITE")`; or `exists("CARA_GEOM")`; or `exists("CARA_POUTRE")`. Fourier harmonic number for axisymmetric Fourier models. Not used in Tier 1. |
| `GEOMETRIE` | text, optional | `'INITIALE'` | One of `'INITIALE'`, `'DEFORMEE'`. Only when `exists("MASS_INER")`. `'INITIALE'`: mass and inertia on the undeformed mesh. `'DEFORMEE'`: on the mesh moved by the displacement `CHAM_GD`, or by the `DEPL` of `RESULTAT`; then exactly one step must be selected (`upstream/bibfor/op/op0107.F90:104`, `:117`, message `POSTELEM_10`). |
| `CHAM_GD` | `cham_no_sdaster` or `cham_elem`, optional | — | *field (physical quantity)*. Only when `exists("MASS_INER")`; or `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("INTEGRALE")`; or `exists("VOLUMOGRAMME")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`. A field object instead of a result: a displacement field for `GEOMETRIE='DEFORMEE'` or `ENER_POT`/`ENER_CIN`, or the field to integrate or bin (`INTEGRALE`, `VOLUMOGRAMME`) (`upstream/astest/sdll146a.comm:296`). |
| `RESULTAT` | `mode_meca` or `evol_elas` or `evol_noli` or `mult_elas` or `fourier_elas` or `dyna_trans` or `evol_sech`, optional | — | *result*. Only when `exists("MASS_INER")`. Only for `GEOMETRIE='DEFORMEE'`: the result whose `DEPL` moves the mesh. |
| `CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `exists("MASS_INER")`; or `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("ENER_DISS")`; or `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`; or `exists("ENER_TOTALE")`; or `exists("INTEGRALE")`; or `exists("VOLUMOGRAMME")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`; or `exists("INDIC_ENER")`; or `exists("INDIC_SEUIL")`; or `exists("CHAR_LIMITE")`; or `exists("TRAV_EXT")`. How `INST`/`FREQ` are matched to the stored values. |
| `PRECISION` | real, optional | `1e-06` | *tolerance*. Only when `exists("MASS_INER") and equal_to("CRITERE", 'RELATIF')`; or `exists("ENER_POT") and equal_to("CRITERE", 'RELATIF')`; or `exists("ENER_CIN") and equal_to("CRITERE", 'RELATIF')`; or `exists("ENER_DISS") and equal_to("CRITERE", 'RELATIF')`; or `exists("ENER_ELAS") and equal_to("CRITERE", 'RELATIF')`; or `exists("ENER_ELTR") and equal_to("CRITERE", 'RELATIF')`; or `exists("ENER_TOTALE") and equal_to("CRITERE", 'RELATIF')`; or `exists("INTEGRALE") and equal_to("CRITERE", 'RELATIF')`; or `exists("VOLUMOGRAMME") and equal_to("CRITERE", 'RELATIF')`; or `exists("WEIBULL") and equal_to("CRITERE", 'RELATIF')`; or `exists("RICE_TRACEY") and equal_to("CRITERE", 'RELATIF')`; or `exists("INDIC_ENER") and equal_to("CRITERE", 'RELATIF')`; or `exists("INDIC_SEUIL") and equal_to("CRITERE", 'RELATIF')`; or `exists("CHAR_LIMITE") and equal_to("CRITERE", 'RELATIF')`; or `exists("TRAV_EXT") and equal_to("CRITERE", 'RELATIF')`. Matching tolerance for `INST`/`FREQ`. |
| `PRECISION` | real, required | — | *tolerance*. Only when `exists("MASS_INER") and equal_to("CRITERE", 'ABSOLU')`; or `exists("ENER_POT") and equal_to("CRITERE", 'ABSOLU')`; or `exists("ENER_CIN") and equal_to("CRITERE", 'ABSOLU')`; or `exists("ENER_DISS") and equal_to("CRITERE", 'ABSOLU')`; or `exists("ENER_ELAS") and equal_to("CRITERE", 'ABSOLU')`; or `exists("ENER_ELTR") and equal_to("CRITERE", 'ABSOLU')`; or `exists("ENER_TOTALE") and equal_to("CRITERE", 'ABSOLU')`; or `exists("INTEGRALE") and equal_to("CRITERE", 'ABSOLU')`; or `exists("VOLUMOGRAMME") and equal_to("CRITERE", 'ABSOLU')`; or `exists("WEIBULL") and equal_to("CRITERE", 'ABSOLU')`; or `exists("RICE_TRACEY") and equal_to("CRITERE", 'ABSOLU')`; or `exists("INDIC_ENER") and equal_to("CRITERE", 'ABSOLU')`; or `exists("INDIC_SEUIL") and equal_to("CRITERE", 'ABSOLU')`; or `exists("CHAR_LIMITE") and equal_to("CRITERE", 'ABSOLU')`; or `exists("TRAV_EXT") and equal_to("CRITERE", 'ABSOLU')`. Matching tolerance for `INST`/`FREQ`, required with `'ABSOLU'`. |
| `TOUT_ORDRE` | text, optional | — | One of `'OUI'`. Only when `exists("MASS_INER")`; or `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("ENER_DISS")`; or `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`; or `exists("ENER_TOTALE")`; or `exists("INTEGRALE")`; or `exists("VOLUMOGRAMME")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`; or `exists("INDIC_ENER")`; or `exists("INDIC_SEUIL")`; or `exists("CHAR_LIMITE")`; or `exists("TRAV_EXT")`. Every step of the result: one set of rows per step. |
| `NUME_ORDRE` | integer, optional | — | *step index*. Only when `exists("MASS_INER")`. One step of the result (with `MASS_INER`, a single value). |
| `LIST_ORDRE` | `listis_sdaster`, optional | — | Only when `exists("MASS_INER")`; or `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("ENER_DISS")`; or `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`; or `exists("ENER_TOTALE")`; or `exists("INTEGRALE")`; or `exists("VOLUMOGRAMME")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`; or `exists("INDIC_ENER")`; or `exists("INDIC_SEUIL")`; or `exists("CHAR_LIMITE")`. Steps from a list of integers. |
| `INST` | real, optional | — | *time step (pseudo-time)*. Only when `exists("MASS_INER")`. One time of the result (with `MASS_INER`, a single value). |
| `LIST_INST` | `listr8_sdaster`, optional | — | *time-step list*. Only when `exists("MASS_INER")`; or `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("ENER_DISS")`; or `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`; or `exists("ENER_TOTALE")`; or `exists("INTEGRALE")`; or `exists("VOLUMOGRAMME")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`; or `exists("INDIC_ENER")`; or `exists("INDIC_SEUIL")`; or `exists("CHAR_LIMITE")`. Times from a list of reals. |
| `FREQ` | real, optional | — | *frequency*. Only when `exists("MASS_INER")`. One frequency of a modal or harmonic result. |
| `LIST_FREQ` | `listr8_sdaster`, optional | — | Only when `exists("MASS_INER")`; or `exists("ENER_POT")`; or `exists("ENER_CIN")`. Frequencies from a list of reals. |
| `NUME_MODE` | integer, optional | — | Only when `exists("MASS_INER")`. One mode number of a modal result. |
| `NOEUD_CMP` | text, optional, list of up to 2, at least 2 | — | Only when `exists("MASS_INER")`. A static mode of a `MODE_STATIQUE` result, by node and component. Not used in Tier 1. |
| `NOM_CAS` | text, optional | — | Only when `exists("MASS_INER")`. A load case of a `mult_elas` result, by name. Not used in Tier 1. |
| `ENER_POT` | factor keyword, optional, repeatable | — | Potential strain energy of the selected elements, from a displacement field (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:139`). Table columns `NUME_ORDRE`, `INST` (or `FREQ` for modes), `LIEU`, `ENTITE`, `TOTALE` (the energy) and `POUR_CENT` (share of the energy of the whole model) (`upstream/bibfor/utilitai/peepot.F90:108`). Use it to see where a structure stores its energy, or which part dominates a mode. |
| `ENER_POT / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `ENER_POT / GROUP_MA` | element group, optional, list | — | *element group*. These groups: one row per group, with its share in `POUR_CENT`. |
| `ANGLE` | integer, optional | `0` | Only when `exists("ENER_POT")`; or `exists("ENER_CIN")`. Harmonic angle, in degrees, for Fourier models. Not used in Tier 1. |
| `RESULTAT` | `mode_meca` or `evol_elas` or `evol_ther` or `evol_noli` or `dyna_trans` or `mult_elas` or `evol_sech`, optional | — | *result*. Only when `exists("ENER_POT")`. The result whose displacements give the energy (`upstream/astest/forma20a.comm:201`). |
| `NUME_ORDRE` | integer, optional, list | — | *step index*. Only when `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("ENER_DISS")`; or `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`; or `exists("ENER_TOTALE")`; or `exists("INTEGRALE")`; or `exists("VOLUMOGRAMME")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`; or `exists("INDIC_ENER")`; or `exists("INDIC_SEUIL")`; or `exists("CHAR_LIMITE")`. These steps only. |
| `INST` | real, optional, list | — | *time step (pseudo-time)*. Only when `exists("ENER_POT")`; or `exists("ENER_CIN")`; or `exists("ENER_DISS")`; or `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`; or `exists("ENER_TOTALE")`; or `exists("INTEGRALE")`; or `exists("VOLUMOGRAMME")`; or `exists("WEIBULL")`; or `exists("RICE_TRACEY")`; or `exists("INDIC_ENER")`; or `exists("INDIC_SEUIL")`; or `exists("CHAR_LIMITE")`. These times only. |
| `FREQ` | real, optional, list | — | *frequency*. Only when `exists("ENER_POT")`; or `exists("ENER_CIN")`. These frequencies only. |
| `NUME_MODE` | integer, optional, list | — | Only when `exists("ENER_POT")`; or `exists("ENER_CIN")`. These modes only. |
| `NOEUD_CMP` | text, optional, list | — | Only when `exists("ENER_POT")`; or `exists("ENER_CIN")`. These static modes. Not used in Tier 1. |
| `NOM_CAS` | text, optional, list | — | Only when `exists("ENER_POT")`; or `exists("ENER_CIN")`. These load cases. Not used in Tier 1. |
| `ENER_CIN` | factor keyword, optional, repeatable | — | Kinetic energy, from a velocity field or, for a modal result, from the mode shape and its frequency (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:202`). From a velocity V it is ½ VᵀMV; from a displacement or mode shape U with a frequency it is ½ ω² UᵀMU, ω the angular frequency. Columns `INST`, `LIEU`, `ENTITE`, `TOTALE`, `POUR_CENT` (U4.81.22 §3.10, French only). |
| `ENER_CIN / OPTION` | text, optional | `'MASS_MECA'` | *option*. One of `'MASS_MECA'`, `'MASS_MECA_DIAG'`. The mass matrix used: consistent (`'MASS_MECA'`) or lumped (`'MASS_MECA_DIAG'`). |
| `ENER_CIN / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `ENER_CIN / GROUP_MA` | element group, optional, list | — | *element group*. These groups. |
| `RESULTAT` | `mode_meca` or `evol_elas` or `evol_ther` or `evol_noli` or `dyna_trans` or `evol_sech`, optional | — | *result*. Only when `exists("ENER_CIN")`. The result that gives the velocity or the mode shapes. |
| `ENER_DISS` | factor keyword, optional, repeatable | — | Energy dissipated by the constitutive law (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:257`). Nonlinear results only (`evol_noli`). Not used in Tier 1. |
| `ENER_DISS / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `ENER_DISS / GROUP_MA` | element group, optional, list | — | *element group*. These groups. |
| `RESULTAT` | `evol_noli`, required | — | *result*. Only when `exists("ENER_DISS")`; or `exists("ENER_TOTALE")`; or `exists("INDIC_ENER")`; or `exists("INDIC_SEUIL")`; or `exists("CHAR_LIMITE")`. The nonlinear result (`evol_noli`) to post-process. |
| `ENER_ELAS` | factor keyword, optional, repeatable | — | Elastic strain energy (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:289`). For linear results it matches `ENER_POT`; for nonlinear results it is the elastic part only (½ ∫ σ : D⁻¹ : σ in small strains). Columns `TOTALE` and, on plates and shells, `MEMBRANE`, `FLEXION`, `CISAILLE`, `COUPL_MF`; several groups add a `UNION_GROUP_MA` row (U4.81.22 §3.11, French only). |
| `ENER_ELAS / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `ENER_ELAS / GROUP_MA` | element group, optional, list | — | *element group*. These groups. |
| `RESULTAT` | `evol_noli` or `evol_elas`, required | — | *result*. Only when `exists("ENER_ELAS")`; or `exists("ENER_ELTR")`. The result (`evol_elas` or `evol_noli`) to post-process. |
| `ENER_ELTR` | factor keyword, optional, repeatable | — | Modified elastic strain energy, tensile part only (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:321`). Not used in Tier 1. |
| `ENER_ELTR / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `ENER_ELTR / GROUP_MA` | element group, optional, list | — | *element group*. These groups. |
| `ENER_TOTALE` | factor keyword, optional, repeatable | — | Total strain energy (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:354`). Not used in Tier 1. |
| `ENER_TOTALE / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `ENER_TOTALE / GROUP_MA` | element group, optional, list | — | *element group*. These groups. |
| `INTEGRALE` | factor keyword, optional, repeatable | — | Integral and mean of field components over the selected elements (catalog help, "mean of a component", at `upstream/code_aster/Cata/Commands/post_elem.py:392`). The table gives the measure of the domain `VOL` (length, area or volume) and, per component, `INTE_<cmp>` (integral) and `MOYE_<cmp>` = integral / `VOL` (`upstream/bibfor/utilitai/peecal.F90:278`, `:280`). Use it for a mean stress over a section, a total heat flux, an average temperature. |
| `INTEGRALE / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `INTEGRALE / GROUP_MA` | element group, optional, list | — | *element group*. These groups: one row per group. |
| `INTEGRALE / NOM_CHAM` | text, optional | — | *field name*. One of `'ACCE'`, `'ACCE_ABSOLU'`, `'COEF_H'`, `'COMPORTEMENT'`, `'COMPORTHER'`, `'CONT_ELEM'`, `'CONT_NOEU'`, `'DEGE_ELGA'`, `'DEGE_ELNO'`, `'DEGE_NOEU'`, `'DEPL'`, `'DEPL_ABSOLU'`, … (233 values; see the .json). The field of `RESULTAT` to integrate; required with `RESULTAT` (`POSTELEM_4`). `FORC_NODA` and `REAC_NODA` are refused: nodal forces are not a distributed quantity (`POSTELEM_5`, `upstream/bibfor/utilitai/peeint.F90:297`). |
| `INTEGRALE / NOM_CMP` | text, optional, list | — | *component name*. The components to integrate, for example `'SIZZ'` (`upstream/astest/perfe03a.comm:260`). A component absent on the selected elements is fatal (`UTILITAI7_12`). |
| `INTEGRALE / NOM_VARI` | text, optional, list | — | Internal variables to integrate, by name instead of `V1`, `V2`, …. Only with `RESULTAT`, not with `CHAM_GD` (`POSTELEM_6`). |
| `INTEGRALE / DEJA_INTEGRE` | text, optional | — | One of `'OUI'`, `'NON'`. For element fields (`_ELEM`) only, and then required (`UTILITAI7_13`, `upstream/bibfor/utilitai/peecal.F90:157`): `'OUI'` if the element value is already an integral over the element (it is summed), `'NON'` if it is a density (it is weighted by the element measure) (`upstream/bibfor/utilitai/chpond.F90:221`). It tells truly constant fields from fields already integrated over the element, such as energies (U4.81.22 §3.23.3, French only). |
| `INTEGRALE / TYPE_MAILLE` | text, required | — | One of `'1D'`, `'2D'`, `'3D'`. Keep only the elements of this dimension among those selected: `'3D'` volumes, `'2D'` faces, `'1D'` edges (`upstream/bibfor/utilitai/peeint.F90:160`). The count removed is printed (`PREPOST2_7`); none left is fatal (`PREPOST2_8`). Required, so that skin elements do not dilute a volume mean. |
| `RESULTAT` | `evol_noli` or `evol_ther` or `evol_elas` or `evol_char` or `evol_sech`, optional | — | *result*. Only when `exists("INTEGRALE")`; or `exists("VOLUMOGRAMME")`. The result that holds the field to integrate or bin. |
| `VOLUMOGRAMME` | factor keyword, optional, repeatable | — | *volume distribution of a component*. Distribution of the volume of the selected elements over intervals of one component: how much of the structure is above a stress level (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:432`). Table columns `INTERVALLE`, `BORNE_INF`, `BORNE_SUP`, `DISTRIBUTION` per interval (`upstream/bibfor/utilitai/pevolu.F90:190`). |
| `VOLUMOGRAMME / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `VOLUMOGRAMME / GROUP_MA` | element group, optional | — | *element group*. One group (single value). |
| `VOLUMOGRAMME / CARA_ELEM` | `cara_elem`, optional | — | *element properties*. Element properties, for structural elements (beam sections) (`upstream/astest/ssll111a.comm:502`). |
| `VOLUMOGRAMME / TYPE_MAILLE` | text, optional | — | One of `'2D'`, `'3D'`. Keep only elements of this dimension, as for `INTEGRALE`. |
| `VOLUMOGRAMME / NOM_CHAM` | text, optional | — | *field name*. One of `'ACCE'`, `'ACCE_ABSOLU'`, `'COEF_H'`, `'COMPORTEMENT'`, `'COMPORTHER'`, `'CONT_ELEM'`, `'CONT_NOEU'`, `'DEGE_ELGA'`, `'DEGE_ELNO'`, `'DEGE_NOEU'`, `'DEPL'`, `'DEPL_ABSOLU'`, … (233 values; see the .json). The field of `RESULTAT` to bin. |
| `VOLUMOGRAMME / NOM_CMP` | text, required | — | *component name*. The one component to bin, for example `'SIXX'`. |
| `VOLUMOGRAMME / NB_INTERV` | integer, optional | — | Number of equal intervals between the bounds. |
| `VOLUMOGRAMME / SEUIL` | real, optional | — | *threshold*. A single threshold: two intervals, below and above it (`upstream/bibfor/utilitai/pevolu.F90:408`). |
| `VOLUMOGRAMME / BORNES` | real, optional, list of up to 2, at least 2 | — | Lower and upper bound of the intervals; by default the minimum and maximum of the component (`upstream/bibfor/utilitai/pevolu.F90:414`). |
| `VOLUMOGRAMME / NORME` | text, optional | `'RELATIF'` | *norm*. One of `'RELATIF'`, `'ABSOLU'`. `'RELATIF'`: the `DISTRIBUTION` column is a percentage (0 to 100) of the total volume; `'ABSOLU'`: the volume of each interval, in mesh units (U4.81.22 §3.26.3). |
| `NORME` | factor keyword, optional | — | *norm*. Computes the spatial extrema of one component of a field, for every requested time step. The catalog help ("spatial extrema of one component") is copied from `MINMAX` and is wrong here: the command writes a norm of the field over the selected elements, column `VALE_NORM`, with `TYPE_NORM` (`upstream/bibfor/utilitai/penorm.F90:225`). Used to measure the difference between two fields (`upstream/astest/cont006c.comm:302`). |
| `NORME / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `NORME / GROUP_MA` | element group, optional, list | — | *element group*. These groups. |
| `NORME / TYPE_MAILLE` | text, optional | — | One of `'2D'`, `'3D'`. Keep only elements of this dimension. |
| `NORME / TYPE_NORM` | text, optional | — | One of `'L2'`, `'FROBENIUS'`. `'L2'`: square root of the integral of the squared components; `'FROBENIUS'`: Frobenius norm of a tensor field; as in `CALC_CHAMP`, the two differ by the off-diagonal terms. Continuum elements only; the fields accepted are `DEPL`, `TEMP`, `NEUT_R`, `FLUX`, `SIEF` and `EPSI` (U4.81.22 §3.27). |
| `NORME / RESULTAT` | `evol_noli` or `evol_ther` or `evol_elas` or `evol_sech`, optional | — | *result*. The result that holds the field. |
| `NORME / NOM_CHAM` | text, optional | — | *field name*. One of `'DEPL'`, `'TEMP'`, `'SECH'`, `'NEUT_R'`, `'FLUX_ELGA'`, `'FLUX_ELNO'`, `'FLUX_NOEU'`, `'EPSI_ELGA'`, `'EPSI_ELNO'`, `'EPSI_NOEU'`, `'SIEF_ELGA'`, `'SIEF_ELNO'`, … (13 values; see the .json). The field of `RESULTAT`; required with `RESULTAT` (rule). |
| `NORME / CHAM_GD` | `cham_no_sdaster` or `cham_elem`, optional | — | *field (physical quantity)*. A field object instead of a result; then `MODELE` is required (rule). |
| `NORME / MODELE` | `modele_sdaster`, optional | — | *model*. The model, required with `CHAM_GD`. |
| `NORME / COEF_MULT` | real, optional, list of up to 30 | — | *multiplying coefficients*. Only when `exists("CHAM_GD")`. Weights of the components of a `NEUT_R` field, one per component; default 1, and a short list is padded with zeros (U4.81.22 §3.27.3). |
| `NORME / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `exists("RESULTAT")`. How `INST` is matched. |
| `NORME / PRECISION` | real, optional | `1e-06` | *tolerance*. Only when `exists("RESULTAT") and equal_to("CRITERE", 'RELATIF')`. Matching tolerance. |
| `NORME / PRECISION` | real, required | — | *tolerance*. Only when `exists("RESULTAT") and equal_to("CRITERE", 'ABSOLU')`. Matching tolerance, required with `'ABSOLU'`. |
| `NORME / TOUT_ORDRE` | text, optional | — | One of `'OUI'`. Only when `exists("RESULTAT")`. Every step. |
| `NORME / NUME_ORDRE` | integer, optional, list | — | *step index*. Only when `exists("RESULTAT")`. These steps. |
| `NORME / LIST_ORDRE` | `listis_sdaster`, optional | — | Only when `exists("RESULTAT")`. Steps from a list. |
| `NORME / INST` | real, optional, list | — | *time step (pseudo-time)*. Only when `exists("RESULTAT")`. These times. |
| `NORME / LIST_INST` | `listr8_sdaster`, optional | — | *time-step list*. Only when `exists("RESULTAT")`. Times from a list. |
| `MINMAX` | factor keyword, optional, repeatable | — | Computes the spatial extrema of one component of a field, for every requested time step. Minimum and maximum of components over the selected elements, with where they occur, for each step. Nodal fields give `MAX_<cmp>`, `NO_MAX_<cmp>` (node), `MIN_<cmp>`, `NO_MIN_<cmp>` (`upstream/bibfor/utilitai/pemaxn.F90:243`); element fields give `MAX_<cmp>`, `MA_MAX_<cmp>` (element), `PT_MAX_<cmp>` (point) and the same for the minimum (`upstream/bibfor/utilitai/pemaxe.F90:207`). Unlike `POST_RELEVE_T`, it accepts Gauss-point fields (`upstream/astest/petsc02f.comm:108`). |
| `MINMAX / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `MINMAX / GROUP_MA` | element group, optional, list | — | *element group*. These groups (`upstream/astest/petsc02f.comm:101`). |
| `MINMAX / RESULTAT` | `evol_noli` or `evol_ther` or `evol_elas` or `evol_sech`, optional | — | *result*. The result that holds the field. |
| `MINMAX / NOM_CHAM` | text, optional | — | *field name*. One of `'ACCE'`, `'ACCE_ABSOLU'`, `'COEF_H'`, `'COMPORTEMENT'`, `'COMPORTHER'`, `'CONT_ELEM'`, `'CONT_NOEU'`, `'DEGE_ELGA'`, `'DEGE_ELNO'`, `'DEGE_NOEU'`, `'DEPL'`, `'DEPL_ABSOLU'`, … (233 values; see the .json). The field of `RESULTAT`; required with `RESULTAT` (rule). |
| `MINMAX / CHAM_GD` | `cham_no_sdaster` or `cham_elem`, optional | — | *field (physical quantity)*. A field object instead of a result; then `MODELE` is required (rule). |
| `MINMAX / MODELE` | `modele_sdaster`, optional | — | *model*. The model, required with `CHAM_GD`. |
| `MINMAX / NOM_CMP` | text, required, list | — | *component name*. The components, for example `'DY'` or `'SIXX'`. |
| `MINMAX / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `exists("RESULTAT")`. How `INST` is matched. |
| `MINMAX / PRECISION` | real, optional | `1e-06` | *tolerance*. Only when `exists("RESULTAT") and equal_to("CRITERE", 'RELATIF')`. Matching tolerance. |
| `MINMAX / PRECISION` | real, required | — | *tolerance*. Only when `exists("RESULTAT") and equal_to("CRITERE", 'ABSOLU')`. Matching tolerance, required with `'ABSOLU'`. |
| `MINMAX / TOUT_ORDRE` | text, optional | — | One of `'OUI'`. Only when `exists("RESULTAT")`. Every step. |
| `MINMAX / NUME_ORDRE` | integer, optional, list | — | *step index*. Only when `exists("RESULTAT")`. These steps. |
| `MINMAX / LIST_ORDRE` | `listis_sdaster`, optional | — | Only when `exists("RESULTAT")`. Steps from a list. |
| `MINMAX / INST` | real, optional, list | — | *time step (pseudo-time)*. Only when `exists("RESULTAT")`. These times. |
| `MINMAX / LIST_INST` | `listr8_sdaster`, optional | — | *time-step list*. Only when `exists("RESULTAT")`. Times from a list. |
| `WEIBULL` | factor keyword, optional, repeatable | — | Weibull stress, to the power m, for brittle fracture probability (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:570`). Not used in Tier 1. |
| `WEIBULL / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `WEIBULL / GROUP_MA` | element group, optional, list | — | *element group*. These groups. |
| `WEIBULL / OPTION` | text, optional | `'SIGM_ELGA'` | *option*. One of `'SIGM_ELGA'`, `'SIGM_ELMOY'`. Stress at Gauss points (`'SIGM_ELGA'`) or averaged per element (`'SIGM_ELMOY'`). |
| `WEIBULL / CORR_PLAST` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. `'OUI'`: the Weibull stress accounts for the plastic strain (U4.81.22 §3.14.3.2). |
| `WEIBULL / COEF_MULT` | real, optional | `1.0` | *multiplying coefficients*. Symmetry and thickness coefficient: for `3D`, 2 with the defect plane on a symmetry plane, 4 with half the defect meshed, 1 without symmetry; 2D values involve the thickness (U4.81.22 §3.14.3.3). |
| `RESULTAT` | `evol_noli`, optional | — | *result*. Only when `exists("WEIBULL")`; or `exists("RICE_TRACEY")`. The nonlinear result to post-process. |
| `RICE_TRACEY` | factor keyword, optional, repeatable | — | Growth rate of a spherical cavity (Rice and Tracey ductile fracture model) over a domain (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:614`). Not used in Tier 1. |
| `RICE_TRACEY / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `RICE_TRACEY / GROUP_MA` | element group, optional, list | — | *element group*. These groups. |
| `RICE_TRACEY / OPTION` | text, optional | `'SIGM_ELGA'` | *option*. One of `'SIGM_ELGA'`, `'SIGM_ELMOY'`. Stress at Gauss points or averaged per element. |
| `RICE_TRACEY / LOCAL` | text, optional | `'OUI'` | *local axes*. One of `'OUI'`, `'NON'`. `'OUI'`: the law is integrated on each element and the largest result is kept; `'NON'`: on the volume-weighted means of triaxiality and plastic strain over the domain (U4.81.22 §3.15.3.2). |
| `INDIC_ENER` | factor keyword, optional, repeatable | — | Global indicator of loss of load proportionality, energy based (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:651`). Not used in Tier 1. |
| `INDIC_ENER / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `INDIC_ENER / GROUP_MA` | element group, optional, list | — | *element group*. These groups. |
| `INDIC_SEUIL` | factor keyword, optional, repeatable | — | Global indicator of loss of load proportionality, threshold based (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:681`). Not used in Tier 1. |
| `INDIC_SEUIL / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole model. |
| `INDIC_SEUIL / GROUP_MA` | element group, optional, list | — | *element group*. These groups. |
| `CHAR_LIMITE` | factor keyword, optional | — | Post-processing of a limit load analysis (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:706`). Not used in Tier 1. |
| `CHAR_LIMITE / CHAR_CSTE` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Whether the load is constant (`'OUI'`) or not (U4.81.22 §3.18.3). |
| `CARA_GEOM` | factor keyword, optional, repeatable | — | Geometric properties of a beam cross-section meshed in 2D (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:739`): area `A`, center of gravity, second moments `IY_G`, `IZ_G`, `IYZ_G`, principal axes, extreme fibers (`Y_MAX`, …, `R_MAX`) (`upstream/bibfor/utilitai/pecage.F90:73`). Feeds `CARA_POUTRE` and `AFFE_CARA_ELEM` for a beam model. Not in the Tier 1 workflow. |
| `CARA_GEOM / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole section. |
| `CARA_GEOM / GROUP_MA` | element group, optional, list | — | *element group*. These groups (`upstream/astest/ssll107b.comm:229`). |
| `CARA_GEOM / SYME_X` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. `'OUI'`: the mesh is half of a section symmetric about the X axis; properties are given for the full section; `SYME_X` and `SYME_Y` together mean a quarter (U4.81.22 §3.19.3.2; `upstream/astest/ssll107b.comm:40`). |
| `CARA_GEOM / SYME_Y` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Same, for symmetry about the Y axis. |
| `CARA_GEOM / ORIG_INER` | real, optional, list of up to 2, at least 2 | — | A point (Y, Z) about which second moments are also given (`Y_P`, `Z_P`, `IY_P`, …). |
| `CARA_POUTRE` | factor keyword, optional | — | Mechanical properties of a beam section: torsion constant, shear areas, warping (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:767`), from the `CARA_GEOM` table and thermal analogy solutions. Not in the Tier 1 workflow; the `MACR_CARA_POUTRE` macro wraps it. |
| `CARA_POUTRE / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole section. |
| `CARA_POUTRE / GROUP_MA` | element group, optional, list | — | *element group*. These groups. |
| `CARA_POUTRE / GROUP_MA_INTE` | element group, optional, list | — | Boundaries of internal holes of the section. `CARA_POUTRE` is reserved for `MACR_CARA_POUTRE` and its operands are not documented (U4.81.22 §3.20). |
| `CARA_POUTRE / CARA_GEOM` | `table_sdaster`, required | — | The table from a previous `POST_ELEM` `CARA_GEOM` call. |
| `CARA_POUTRE / RT` | real, optional | — | Torsion radius, used for the torsional stress; reserved for `MACR_CARA_POUTRE` (U4.81.22 §3.20). |
| `CARA_POUTRE / LAPL_PHI` | `evol_ther`, optional | — | Thermal-analogy solution for the torsion function. |
| `CARA_POUTRE / LAPL_PHI_Y` | `evol_ther`, optional | — | Thermal-analogy solution for shear along Y. |
| `CARA_POUTRE / LAPL_PHI_Z` | `evol_ther`, optional | — | Thermal-analogy solution for shear along Z. |
| `CARA_POUTRE / LIAISON` | text, optional | — | One of `'ROTULE'`, `'ENCASTREMENT'`. End condition, pinned (`'ROTULE'`) or clamped (`'ENCASTREMENT'`), for the warping option; with `LONGUEUR` and `MATERIAU` (rule). |
| `CARA_POUTRE / LONGUEUR` | real, optional | — | *length*. Beam length for the warping option. |
| `CARA_POUTRE / MATERIAU` | `mater_sdaster`, optional | — | Material for the warping option. |
| `CARA_POUTRE / OPTION` | text, optional | — | *option*. One of `'CARA_TORSION'`, `'CARA_CISAILLEMENT'`, `'CARA_GAUCHI'`. Which properties: torsion, shear or warping. |
| `AIRE_INTERNE` | factor keyword, optional, repeatable | — | Area of a hole in a 2D mesh (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:779`). Not used in Tier 1. |
| `AIRE_INTERNE / GROUP_MA_BORD` | element group, required, list | — | The edge elements bounding the hole. |
| `TRAV_EXT` | factor keyword, optional | — | Work of the external forces (catalog help at `upstream/code_aster/Cata/Commands/post_elem.py:785`). A time not stored in the result gives `POSTELEM_11`. Compare it with `ENER_POT` as an energy balance check. |
| `RESULTAT` | `evol_elas` or `evol_noli` or `dyna_trans`, required | — | *result*. Only when `exists("TRAV_EXT")`. The result whose external work is computed. |
| `TITRE` | text, optional | — | *title*. Title of the table. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. |

5 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: exactly one of `MASS_INER`, `ENER_POT`, `ENER_CIN`, `TRAV_EXT`, `MINMAX`, `WEIBULL`, `RICE_TRACEY`, `CARA_GEOM`, `CHAR_LIMITE`, `NORME`, `CARA_POUTRE`, `INDIC_ENER`, `INDIC_SEUIL`, `VOLUMOGRAMME`, `AIRE_INTERNE`, `ENER_ELAS`, `ENER_ELTR`, `ENER_TOTALE`, `ENER_DISS`, `INTEGRALE` must be given (`UN_PARMI`).
- `MASS_INER`: exactly one of `TOUT`, `GROUP_MA`, `MAILLE` must be given (`UN_PARMI`).
- when `exists("MASS_INER")`: at most one of `CHAM_GD`, `RESULTAT` may be given (`EXCLUS`).
- when `exists("MASS_INER")`: at most one of `CHAM_GD`, `TOUT_ORDRE`, `NUME_ORDRE`, `INST`, `FREQ`, `NUME_MODE`, `NOEUD_CMP`, `LIST_ORDRE`, `LIST_INST`, `LIST_FREQ`, `NOM_CAS` may be given (`EXCLUS`).
- `ENER_POT`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- when `exists("ENER_POT")`: exactly one of `CHAM_GD`, `RESULTAT` must be given (`UN_PARMI`).
- when `exists("ENER_POT")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `INST`, `FREQ`, `NUME_MODE`, `NOEUD_CMP`, `LIST_ORDRE`, `LIST_INST`, `LIST_FREQ`, `NOM_CAS` may be given (`EXCLUS`).
- `ENER_CIN`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- when `exists("ENER_CIN")`: exactly one of `CHAM_GD`, `RESULTAT` must be given (`UN_PARMI`).
- when `exists("ENER_CIN")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `INST`, `FREQ`, `NUME_MODE`, `NOEUD_CMP`, `LIST_ORDRE`, `LIST_INST`, `LIST_FREQ`, `NOM_CAS` may be given (`EXCLUS`).
- `ENER_DISS`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- when `exists("ENER_DISS")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `LIST_ORDRE`, `INST`, `LIST_INST` may be given (`EXCLUS`).
- `ENER_ELAS`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- when `exists("ENER_ELAS")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `LIST_ORDRE`, `INST`, `LIST_INST` may be given (`EXCLUS`).
- `ENER_ELTR`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- when `exists("ENER_ELTR")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `LIST_ORDRE`, `INST`, `LIST_INST` may be given (`EXCLUS`).
- `ENER_TOTALE`: exactly one of `TOUT`, `GROUP_MA`, `MAILLE` must be given (`UN_PARMI`).
- when `exists("ENER_TOTALE")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `LIST_ORDRE`, `INST`, `LIST_INST` may be given (`EXCLUS`).
- `INTEGRALE`: exactly one of `TOUT`, `GROUP_MA`, `MAILLE` must be given (`UN_PARMI`).
- `INTEGRALE`: exactly one of `NOM_CMP`, `NOM_VARI` must be given (`UN_PARMI`).
- when `exists("INTEGRALE")`: exactly one of `CHAM_GD`, `RESULTAT` must be given (`UN_PARMI`).
- when `exists("INTEGRALE")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `INST`, `LIST_ORDRE`, `LIST_INST` may be given (`EXCLUS`).
- `VOLUMOGRAMME`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- `VOLUMOGRAMME`: exactly one of `NB_INTERV`, `SEUIL` must be given (`UN_PARMI`).
- when `exists("VOLUMOGRAMME")`: exactly one of `CHAM_GD`, `RESULTAT` must be given (`UN_PARMI`).
- when `exists("VOLUMOGRAMME")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `INST`, `LIST_ORDRE`, `LIST_INST` may be given (`EXCLUS`).
- `NORME`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- `NORME`: exactly one of `CHAM_GD`, `RESULTAT` must be given (`UN_PARMI`).
- `NORME`: if `CHAM_GD` is given, `MODELE` must all be given (`PRESENT_PRESENT`).
- `NORME`: if `RESULTAT` is given, `NOM_CHAM` must all be given (`PRESENT_PRESENT`).
- when `exists("RESULTAT")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `LIST_ORDRE`, `INST`, `LIST_INST` may be given (`EXCLUS`).
- `MINMAX`: exactly one of `CHAM_GD`, `RESULTAT` must be given (`UN_PARMI`).
- `MINMAX`: if `CHAM_GD` is given, `MODELE` must all be given (`PRESENT_PRESENT`).
- `MINMAX`: if `RESULTAT` is given, `NOM_CHAM` must all be given (`PRESENT_PRESENT`).
- `MINMAX`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- `WEIBULL`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- when `exists("WEIBULL")`: exactly one of `CHAM_GD`, `RESULTAT` must be given (`UN_PARMI`).
- when `exists("WEIBULL")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `LIST_ORDRE`, `INST`, `LIST_INST` may be given (`EXCLUS`).
- `RICE_TRACEY`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- when `exists("RICE_TRACEY")`: exactly one of `CHAM_GD`, `RESULTAT` must be given (`UN_PARMI`).
- when `exists("RICE_TRACEY")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `LIST_ORDRE`, `INST`, `LIST_INST` may be given (`EXCLUS`).
- `INDIC_ENER`: exactly one of `TOUT`, `GROUP_MA`, `MAILLE` must be given (`UN_PARMI`).
- when `exists("INDIC_ENER")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `LIST_ORDRE`, `INST`, `LIST_INST` may be given (`EXCLUS`).
- `INDIC_SEUIL`: exactly one of `TOUT`, `GROUP_MA`, `MAILLE` must be given (`UN_PARMI`).
- when `exists("INDIC_SEUIL")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `LIST_ORDRE`, `INST`, `LIST_INST` may be given (`EXCLUS`).
- when `exists("CHAR_LIMITE")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `LIST_ORDRE`, `INST`, `LIST_INST` may be given (`EXCLUS`).
- `CARA_GEOM`: at least one of `TOUT`, `GROUP_MA` must be given (`AU_MOINS_UN`).
- `CARA_POUTRE`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- `CARA_POUTRE`: `LONGUEUR`, `LIAISON`, `MATERIAU` are given all together or not at all (`ENSEMBLE`).

## What the solver does

- `op0107.F90` runs the one option given. For every option except `NORME`, `MINMAX`,
  `INTEGRALE` and `TRAV_EXT`, a parallel (distributed) mesh is refused by an assertion
  (`upstream/bibfor/op/op0107.F90:102` for `MASS_INER`).
- The model, material field and element properties are read from the command when there is no
  `RESULTAT`, and from the result otherwise; with a result and no step given, the first stored
  step is used to find them (`upstream/bibfor/utilitai/medomp.F90:128`–`:156`).
- `MASS_INER` evaluates the elementary option `MASS_INER` on the selected elements and sums it
  (`upstream/bibfor/utilitai/pemain.F90:145`).

## Patterns

### Mass and inertia of the whole model

The Tier 1 check after the mesh and material are assigned: the mass in the table must match the
drawing. In mm/N/MPa units, density is in t/mm³ and the mass comes out in tonnes (fixture: 6.28E-04
t for a 400 × 20 × 10 mm steel bar).

Source: `tests/fixtures/modal/input/run.comm:29`.

```python
MASSE = POST_ELEM(MODELE=MODE, CHAM_MATER=MATE, MASS_INER=_F(TOUT="OUI"))
```

### Mass per group, with shells

`CARA_ELEM` carries the shell thickness; without it the shell mass is wrong.

Source: `upstream/astest/adlv312a.comm:94`.

```python
TABL_MAS = POST_ELEM(
    MODELE=MODELE,
    CHAM_MATER=CH_MATER,
    CARA_ELEM=CARA,
    MASS_INER=_F(GROUP_MA=("FLUIDE", "COQUE", "INTERF")),
)
```

### Extrema of a component on a group, every step

Source: `upstream/astest/petsc02f.comm:101`.

```python
MIN_DEPY = POST_ELEM(
    MINMAX=_F(GROUP_MA="Arete_superieure_x", NOM_CMP="DY", NOM_CHAM="DEPL", RESULTAT=MESTAT1)
)
```

### Mean stress over the volume

`TYPE_MAILLE="3D"` keeps the skin elements out of the mean.

Source: `upstream/astest/perfe03a.comm:260`.

```python
INT_SI = POST_ELEM(
    INTEGRALE=_F(TOUT="OUI", NOM_CHAM="SIEF_ELGA", NOM_CMP="SIZZ", TYPE_MAILLE="3D"),
    MODELE=MO,
    RESULTAT=SIG,
)
```

### Potential strain energy of a result

Inside a loop in the source (indentation kept).

Source: `upstream/astest/forma20a.comm:201`.

```python
    ENER[num_calc] = POST_ELEM(RESULTAT=DEPLA[num_calc], ENER_POT=_F(TOUT="OUI"))
```

### Volume above stress levels

Source: `upstream/astest/ssll111a.comm:502`.

```python
VOLUM2 = POST_ELEM(
    RESULTAT=DEP1G,
    MODELE=MOPOU,
    VOLUMOGRAMME=_F(
        NOM_CMP="SIXX",
        CARA_ELEM=POUCAG,
        TOUT="OUI",
        NOM_CHAM="SIEF_ELGA",
        NORME="RELATIF",
        NB_INTERV=5,
    ),
)
```

### L2 norm of a field difference

Inside a loop in the source (indentation kept).

Source: `upstream/astest/cont006c.comm:302`.

```python
    tabU = POST_ELEM(NORME=_F(TYPE_NORM="L2", GROUP_MA=GROUP_MA_VOL, CHAM_GD=DIFFUG, MODELE=MODELE))
```

### Beam section properties from a 2D section mesh

Source: `upstream/astest/ssll107b.comm:40`.

```python
TCARS = POST_ELEM(MODELE=MO, CHAM_MATER=CHMAT, CARA_GEOM=_F(TOUT="OUI", SYME_X="OUI", SYME_Y="OUI"))
```

## Pitfalls

- **No material field, no mass.** `MASS_INER` and the energies need `CHAM_MATER` (and
  `CARA_ELEM` for shells, beams, discrete elements). Without them the solver only warns
  (`CALCULEL3_40`, `CALCULEL3_39`, `upstream/bibfor/utilitai/medomp.F90:113`, `:122`) and the
  later elementary computation may fail or give a wrong mass.
- **`LIEU` is not the name you typed.** With `TOUT='OUI'` the `LIEU` column holds the internal
  name of the mesh (`upstream/bibfor/utilitai/pemain.F90:187`; fixture value `00000001`), and
  `ENTITE` is `TOUT`. Filter a table on `ENTITE` or on the group name, not on the mesh variable
  name.
- **Units follow the model.** The mass is `RHO` × volume in whatever units the mesh and material
  use. The mm/N/MPa system gives tonnes and t·mm² (fixture `IY_G` = 8.38 t·mm²).
- **`INTEGRALE` refuses nodal forces.** `FORC_NODA` and `REAC_NODA` are not distributed
  quantities (`POSTELEM_5`): use `POST_RELEVE_T` with `RESULTANTE` for reaction sums.
- **Element fields need `DEJA_INTEGRE`.** An `_ELEM` field in `INTEGRALE` without
  `DEJA_INTEGRE` is fatal (`UTILITAI7_13`).
- **`GEOMETRIE='DEFORMEE'` needs a single step.** With a result and no `CHAM_GD`, exactly one
  step must be selected, or `POSTELEM_10` stops the run (`upstream/bibfor/op/op0107.F90:117`).
  The message text says "more than one step", which contradicts the test in the code.
- **The `NORME` help text is a copy.** The catalog gives `NORME` the same French help as
  `MINMAX` ("spatial extrema"); the solver computes a norm (`VALE_NORM`,
  `upstream/bibfor/utilitai/penorm.F90:225`). Rely on the column, not the help.
- **COMMAND-SET key keywords.** `FILTRE_MODE`, `CRIT_EXTR` and `MASS_EFFE_UN` come from the
  modal post-processing row of docs/COMMAND-SET.md, which groups `NORM_MODE`, `EXTR_MODE` and
  `POST_ELEM MASS_INER`. They are not `POST_ELEM` keywords: `FILTRE_MODE` and `CRIT_EXTR` belong
  to `EXTR_MODE`, and `MASS_EFFE_UN` is a value of `CRIT_EXTR`. `NORME` and `SEUIL` there mean
  the `NORM_MODE` and `FILTRE_MODE` keywords, not this command's `NORME` option or
  `VOLUMOGRAMME / SEUIL`.

## See also

- French reference: U4.81.22 (French text: `en/docs/_src/U4.81.22.fr.md`; translation: `en/docs/U4.81.22.md`)
- Catalog: `en/commands/POST_ELEM.json` (generated from `upstream/code_aster/Cata/Commands/post_elem.py:39`)
- Implementation: `upstream/bibfor/op/op0107.F90`; options in `upstream/bibfor/utilitai/`
  (`pemain` mass, `peepot` potential energy, `peecin` kinetic energy, `peeint`/`peecal`
  integral, `pemima` extrema, `penorm` norm, `pevolu` volume distribution, `pecage` section)
- Before: [AFFE_MATERIAU](AFFE_MATERIAU.md), [AFFE_CARA_ELEM](AFFE_CARA_ELEM.md),
  [MECA_STATIQUE](MECA_STATIQUE.md), [CALC_CHAMP](CALC_CHAMP.md)
- Related: [POST_RELEVE_T](POST_RELEVE_T.md) (values at nodes, reaction sums)
- Next steps: [IMPR_TABLE](IMPR_TABLE.md), `TEST_TABLE`
- Example: `tests/fixtures/modal/input/run.comm` (line 29)
- Example: `upstream/astest/adlv312a.comm` (line 94)
- Example: `upstream/astest/petsc02f.comm` (line 101)
- Example: `upstream/astest/perfe03a.comm` (line 260)
