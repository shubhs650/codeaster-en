---
command: CREA_CHAMP
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/crea_champ.py:41
doc_fr: U4.72.04
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3d)
examples: [erreu02a, comp009a, cont008a, ahlv100a, cont006c, forma02d, ssls101m]
---

# CREA_CHAMP — create field

> **Assisted reference.** Written in session from the pinned catalog, the solver source it
> calls, the message catalog and upstream test cases. Every behavior claim cites its source. Not
> reviewed by an engineer.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

`CREA_CHAMP` builds one field object outside any analysis: a nodal field (`cham_no`), a
constant-per-element map (`carte`) or an element field (`cham_elem`), as set by `TYPE_CHAM`.
`OPERATION` says how: assign values (`AFFE`), extract from a result or a mesh (`EXTR`), assemble
from other fields (`ASSE`), combine (`COMB`), evaluate functions (`EVAL`), change location
(`DISC`), and a few more. In Tier 1 it is used for three things: a temperature field given to
`AFFE_MATERIAU` (`AFFE_VARC`, `NOM_VARC='TEMP'`) for thermal strains, an initial or reference
field, and pulling one step of a result out as a field for checks or further work. The type
asked for is checked against the field actually built (`CALCULEL4_70`, `CALCULEL4_71`).

| Fact | Value |
|---|---|
| Catalog description (fr) | «Création d'un champ» |
| Kind | `OPER` (Fortran operator 195, `upstream/bibfor/op/op0195.F90`) |
| Result | `cham_no_sdaster` (`NOEU_*`), `carte_sdaster` (`CART_*`), `cham_elem` (`ELEM_*`, `ELNO_*`, `ELGA_*`), from `TYPE_CHAM` |
| Can reuse its input (`reuse=`) | yes, only for `ASSE` and `COMB` (the object given in `CHAM_GD`); catalog `reentrant='f:CHAM_GD'` |
| French reference | U4.72.04 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `OPERATION`, `EXTR`, `AFFE`, `ASSE`, `TYPE_CHAM`, `AFFE_VARC`, `NOM_VARC`, `TEMP`, `VALE_REF`, `CHAM_GD` (`AFFE_VARC`, `NOM_VARC`, `VALE_REF` are `AFFE_MATERIAU` keywords; they come from the temperature-load row of COMMAND-SET) |

## Keywords

Keywords that appear in several operations (`CHAM_GD`, `MODELE`, `NOM_CHAM`, `NUME_ORDRE`, …)
are listed once per operation group, in catalog order.

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `CHAM_GD` | `cham_gd_sdaster`, optional | — | *field (physical quantity)*. Only when `is_in("OPERATION", ("ASSE", "COMB"))`. With `reuse=`: the field being completed by `ASSE` or `COMB`. `reuse` is refused for the other operations (`UTILITAI3_43`, `upstream/bibfor/op/op0195.F90:125`). |
| `TYPE_CHAM` | text, required | — | *field type*. One of `'ELEM_ABSC_R'`, `'ELNO_ABSC_R'`, `'ELGA_ABSC_R'`, `'CART_ABSC_R'`, `'NOEU_ABSC_R'`, `'ELEM_CACOQU_R'`, `'ELNO_CACOQU_R'`, `'ELGA_CACOQU_R'`, `'CART_CACOQU_R'`, `'NOEU_CACOQU_R'`, `'ELEM_CADISK_R'`, `'ELNO_CADISK_R'`, … (518 values; see the .json). The field to create, as `<location>_<quantity>_<scalar>` (comment at `upstream/code_aster/Cata/Commands/crea_champ.py:53`): location `NOEU` (nodal field, `cham_no`), `CART` (constant per element, `carte`), `ELEM`, `ELNO`, `ELGA` (element fields, `cham_elem`); quantity from the quantity catalog (`DEPL`, `TEMP`, `SIEF`, `GEOM`, `NEUT`, …); scalar `R`, `C`, `F` (function) or `I`. The result type follows from it (`crea_champ_prod`, `crea_champ.py:25`). The field actually built must match, or `CALCULEL4_70` (location) and `CALCULEL4_71` (quantity) stop the run (`upstream/bibfor/op/op0195.F90:431`–`:442`). |
| `NUME_DDL` | `nume_ddl_sdaster`, optional | — | *DOF numbering*. For a nodal field: give it the DOF numbering of this `NUME_DDL`, so it can be combined with assembled vectors of the same system (`upstream/bibfor/op/op0195.F90:313`). Rule: not with `CHAM_NO`. |
| `CHAM_NO` | `cham_no_sdaster`, optional | — | For a nodal field: give it the same numbering as this existing nodal field. Rule: not with `NUME_DDL`. Sharing the numbering of input fields loses the information on Lagrange DOFs of dualized boundary conditions (warning `CREACHAMP1_14`). |
| `PROL_ZERO` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Only when `exists("NUME_DDL") or exists("CHAM_NO") or (exists("TYPE_CHAM") and TYPE_CHAM[0:2] == 'EL')`. What happens to components or elements the operation did not assign. `'OUI'`: they are set to zero. `'NON'` (default) for real element fields: they are set to NaN and the field is then checked, so any unassigned value stops the run (`upstream/bibfor/op/op0195.F90:137`, `:409`). Set `'OUI'` when only part of the model gets a value. |
| `OPTION` | text, optional | — | *option*. For an element field: the elementary option whose layout is used to allocate it; by default `TOU_INI_ELNO`, `TOU_INI_ELGA` or `TOU_INI_ELEM` (`upstream/bibfor/op/op0195.F90:158`). Rarely needed. |
| `AFFE_SP` | factor keyword, optional | — | For an element field with sub-points (layers of shells, fibers of beams): copy the value to every sub-point (catalog comment, `upstream/code_aster/Cata/Commands/crea_champ.py:74`; `upstream/bibfor/op/op0195.F90:388`). Not used in Tier 1. |
| `AFFE_SP / CARA_ELEM` | `cara_elem`, required | — | *element properties*. The element properties that define the sub-points. |
| `OPERATION` | text, required | — | *operation*. One of `'AFFE'`, `'ASSE'`, `'ASSE_DEPL'`, `'EVAL'`, `'EXTR'`, `'DISC'`, `'NORMALE'`, `'R2C'`, `'C2R'`, `'COMB'`. What the command does. `'AFFE'`: assign values or functions on groups (initial fields, temperature fields for `AFFE_MATERIAU`/`AFFE_VARC`). `'EXTR'`: take a field out of a result, a mesh, element properties, a load, a crack or a table. `'ASSE'`: assemble a field from pieces of other fields, by group and component. `'COMB'`: linear combination of nodal fields. `'EVAL'`: evaluate a field of functions. `'DISC'`: move a field to another location (for example nodes to Gauss points). `'NORMALE'`: unit normals on a group of faces or edges. `'R2C'`/`'C2R'`: real to complex and back. `'ASSE_DEPL'`: XFEM displacement assembly (`upstream/bibfor/op/op0195.F90:213`–`:306`). |
| `MODELE` | `modele_sdaster`, required | — | *model*. Only when `equal_to("OPERATION", 'NORMALE')`; or `equal_to("OPERATION", 'ASSE_DEPL')`. The model. `'NORMALE'`: the normals are computed on its elements (`upstream/astest/ssls101m.comm:93`); only nodal geometry fields `NOEU_GEOM_R` are allowed (`UTILITAI3_25`, `UTILITAI3_26`, `upstream/bibfor/op/op0195.F90:215`). `'ASSE_DEPL'`: the XFEM model. |
| `GROUP_MA` | element group, required, list | — | *element group*. Only when `equal_to("OPERATION", 'NORMALE')`. The faces (3D) or edges (2D) on which to compute normals. |
| `MAILLAGE` | `maillage_sdaster`, optional | — | *mesh*. Only when `equal_to("OPERATION", 'AFFE')`; or `equal_to("OPERATION", 'ASSE')`; or `equal_to("OPERATION", 'EXTR')`. The mesh, for nodal fields and constant maps. Rule for `AFFE` and `ASSE`: exactly one of `MAILLAGE`, `MODELE`. For `EXTR`: the mesh from which to take `NOM_CHAM='GEOMETRIE'` or `'ABSC_CURV'`. |
| `MODELE` | `modele_sdaster`, optional | — | *model*. Only when `equal_to("OPERATION", 'AFFE')`; or `equal_to("OPERATION", 'ASSE')`; or `equal_to("OPERATION", 'DISC')`; or `equal_to("OPERATION", 'EXTR') and exists("TABLE")`. The model. Required to build element fields (`ELEM`, `ELNO`, `ELGA`) with `AFFE`, `ASSE` and `DISC` (`upstream/bibfor/op/op0195.F90:148`). If both `MAILLAGE` and `MODELE` are given they must agree (`UTILITAI3_21`). |
| `AFFE` | factor keyword, required, repeatable | — | Only when `equal_to("OPERATION", 'AFFE')`. One assignment: values or functions for some components on some elements or nodes. Repeat it for different regions; a later occurrence overwrites an earlier one where they overlap. Where an entity is assigned twice, the last occurrence wins (U4.72.04 §3.3.1). |
| `AFFE / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole mesh or model. |
| `AFFE / GROUP_MA` | element group, optional, list | — | *element group*. The nodes or elements of these element groups. |
| `AFFE / GROUP_NO` | node group, optional, list | — | *node group*. These nodes (nodal fields). |
| `AFFE / NOM_CMP` | text, required, list | — | *component name*. The components to assign, for example `'TEMP'` for a temperature field (`upstream/astest/erreu02a.comm:85`) or `('DX', 'DY', 'DZ')`. Must belong to the quantity of `TYPE_CHAM`. |
| `AFFE / VALE` | real, optional, list | — | *value(s)*. Real values, one per component in `NOM_CMP`. |
| `AFFE / VALE_I` | integer, optional, list | — | Integer values, for integer quantities. |
| `AFFE / VALE_C` | complex, optional, list | — | *complex values*. Complex values, for complex quantities (`_C`). |
| `AFFE / VALE_F` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional, list | — | Functions or formulas, for function quantities (`_F`), for example a temperature that depends on the coordinates (`upstream/astest/comp005b.comm:66`). Evaluate them later with `'EVAL'`. |
| `ASSE` | factor keyword, required, repeatable | — | Only when `equal_to("OPERATION", 'ASSE')`. One piece of the assembled field: take components of `CHAM_GD` on a region and put them in the new field. Repeat it to assemble several pieces. |
| `ASSE / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole mesh. |
| `ASSE / GROUP_MA` | element group, optional, list | — | *element group*. On these element groups. |
| `ASSE / GROUP_NO` | node group, optional, list | — | *node group*. On these node groups. |
| `ASSE / CHAM_GD` | `cham_gd_sdaster`, required | — | *field (physical quantity)*. The source field of this piece. |
| `ASSE / NOM_CMP` | text, optional, list | — | *component name*. The components to take; all of them by default. |
| `ASSE / NOM_CMP_RESU` | text, optional, list | — | The names they get in the new field, one per `NOM_CMP` (rule: with `NOM_CMP`). Use it to rename components, for example to copy `DX` into a `NEUT` component. |
| `ASSE / CUMUL` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. `'OUI'`: add this piece to what earlier pieces put at the same place; `'NON'`: overwrite it. |
| `ASSE / COEF_R` | real, optional | `1.0` | Real factor applied to the piece. |
| `ASSE / COEF_C` | complex, optional | — | Complex factor applied to the piece (`upstream/astest/ahlv100a.comm:170`). |
| `COMB` | factor keyword, required, repeatable | — | Only when `equal_to("OPERATION", 'COMB')`. One term of the linear combination: `COEF_R` × `CHAM_GD` (catalog help: linear combination of nodal fields with the same layout, `upstream/code_aster/Cata/Commands/crea_champ.py:142`). Repeat it for each term. |
| `COMB / CHAM_GD` | `cham_no_sdaster`, required | — | *field (physical quantity)*. A nodal field. All terms should share the same numbering. |
| `COMB / COEF_R` | real, required | — | Its coefficient, for example `-1.0` to change the sign (`upstream/astest/cont008a.comm:185`). |
| `CHAM_F` | `cham_gd_sdaster`, required | — | Only when `equal_to("OPERATION", 'EVAL')`. A field of functions or formulas (`_F`, usually `NEUT_F`) to evaluate (`upstream/astest/comp009a.comm:196`). |
| `CHAM_PARA` | `cham_gd_sdaster`, required, list | — | Only when `equal_to("OPERATION", 'EVAL')`. The fields that give the values of the function parameters (for example the geometry, or other `NEUT_R` fields). The parameters are matched by component name: the fields must together hold every parameter of the functions, no component may appear in two of them, and all must have the discretization of `CHAM_F` (so two `NEUT` element fields cannot be given) (U4.72.04 §3.6.2, French only). |
| `CHAM_GD` | `cham_gd_sdaster`, required | — | *field (physical quantity)*. Only when `equal_to("OPERATION", 'ASSE_DEPL')`; or `equal_to("OPERATION", 'R2C')`; or `equal_to("OPERATION", 'C2R')`; or `equal_to("OPERATION", 'DISC')`. The input field: the field to convert (`R2C`, `C2R`), to move to another location (`DISC`, same quantity, else `UTILITAI3_27`, `upstream/bibfor/op/op0195.F90:293`), or the XFEM displacement (`ASSE_DEPL`). |
| `CHAM_MATER` | `cham_mater`, optional | — | *material field*. Only when `equal_to("OPERATION", 'ASSE_DEPL')`. The material field, for `ASSE_DEPL`. Not used in Tier 1. |
| `PARTIE` | text, required | — | One of `'REEL'`, `'IMAG'`, `'MODULE'`, `'PHASE'`. Only when `equal_to("OPERATION", 'C2R')`. Which real quantity to take from a complex field: real part, imaginary part, modulus or phase. |
| `FISSURE` | `fiss_xfem`, optional | — | Only when `equal_to("OPERATION", 'EXTR')`. An XFEM crack, to extract its level sets or local basis (`NOM_CHAM`). Not used in Tier 1. |
| `RESULTAT` | `resultat_sdaster`, optional | — | *result*. Only when `equal_to("OPERATION", 'EXTR')`. The result from which to extract a field (`upstream/astest/comp009a.comm:231`). Choose the field with `NOM_CHAM` and the step with `NUME_ORDRE`, `INST`, …, or reduce all steps with `TYPE_MAXI`. |
| `TABLE` | `table_sdaster`, optional | — | *table*. Only when `equal_to("OPERATION", 'EXTR')`. A table of field values (one row per node or point, as written by `POST_RELEVE_T`) to turn back into a field. One column per component, named as in the physical quantity (`DX`, `DY`, …), plus `NOEUD` for a nodal field, `MAILLE` for `ELEM`, `MAILLE` and `NOEUD` for `ELNO`, `MAILLE` and `POINT` for `ELGA`, and `SOUS_POINT` for fields with sub-points. No other column is allowed (remove `NUME_ORDRE`, `INST`, … with `CALC_TABLE`) (U4.72.04 §3.9.2). |
| `CARA_ELEM` | `cara_elem`, optional | — | *element properties*. Only when `equal_to("OPERATION", 'EXTR')`. Element properties, to extract one of their internal maps (`NOM_CHAM`, for example shell thickness `.CARCOQUE`). Not used in Tier 1. |
| `CHARGE` | `char_meca`, optional | — | *load*. Only when `equal_to("OPERATION", 'EXTR')`. A mechanical load, to extract one of its internal maps (`NOM_CHAM`, for example `.CHME.PRESS`). Not used in Tier 1. |
| `NOM_CHAM` | text, required | — | *field name*. One of `'GEOMETRIE'`, `'ABSC_CURV'`. Only when `equal_to("OPERATION", 'EXTR') and exists("MAILLAGE") and not exists("TABLE")`. From a mesh: `'GEOMETRIE'` (node coordinates, `upstream/astest/sdls115a.comm:86`) or `'ABSC_CURV'` (curvilinear abscissa). |
| `NOM_CHAM` | text, required | — | *field name*. One of `'.CARGENBA'`, `'.CARMASSI'`, `'.CARCABLE'`, `'.CARCOQUE'`, `'.CARGEOBA'`, `'.CARDISCK'`, `'.CARARCPO'`, `'.CARGENPO'`, `'.CARDISCM'`, `'.CARORIEN'`, `'.CARDISCA'`, `'.CVENTCXF'`, … (17 values; see the .json). Only when `equal_to("OPERATION", 'EXTR') and exists("CARA_ELEM")`. The internal map of `CARA_ELEM` to extract. |
| `NOM_CHAM` | text, required | — | *field name*. One of `'.CHME.EPSIN'`, `'.CHME.F1D1D'`, `'.CHME.F1D2D'`, `'.CHME.F1D3D'`, `'.CHME.F2D2D'`, `'.CHME.F2D3D'`, `'.CHME.F3D3D'`, `'.CHME.FCO2D'`, `'.CHME.FCO3D'`, `'.CHME.FELEC'`, `'.CHME.FL101'`, `'.CHME.FL102'`, … (24 values; see the .json). Only when `equal_to("OPERATION", 'EXTR') and exists("CHARGE")`. The internal map of `CHARGE` to extract. |
| `NOM_CHAM` | text, required | — | *field name*. One of `'LTNO'`, `'LNNO'`, `'GRLTNO'`, `'GRLNNO'`, `'STNO'`, `'BASLOC'`, `'GRI.LNNO'`, `'GRI.LTNO'`, `'GRI.GRLNNO'`, `'GRI.GRLTNO'`. Only when `equal_to("OPERATION", 'EXTR') and exists("FISSURE")`. The XFEM field of `FISSURE` to extract (level sets, gradients, local basis). |
| `NOM_CHAM` | text, required | — | *field name*. One of `'ACCE'`, `'ACCE_ABSOLU'`, `'COEF_H'`, `'COMPORTEMENT'`, `'COMPORTHER'`, `'CONT_ELEM'`, `'CONT_NOEU'`, `'DEGE_ELGA'`, `'DEGE_ELNO'`, `'DEGE_NOEU'`, `'DEPL'`, `'DEPL_ABSOLU'`, … (233 values; see the .json). Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT")`. The field of `RESULTAT` to extract, for example `'DEPL'`, `'SIEF_ELGA'`, `'TEMP'`. `TYPE_CHAM` must match its location and quantity (`'DEPL'` → `'NOEU_DEPL_R'`). |
| `TYPE_MAXI` | text, optional | — | One of `'MAXI'`, `'MINI'`, `'MAXI_ABS'`, `'MINI_ABS'`, `'NORM_TRAN'`. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT")`. Instead of one step, build a field of the extreme value over the selected steps, point by point: `'MAXI'`, `'MINI'`, `'MAXI_ABS'`, `'MINI_ABS'` (by absolute value) (`upstream/astest/forma02d.comm:192`). `'NORM_TRAN'`, for displacement fields only: at each point, all components at the step where the norm of the translation is largest (U4.72.04 §3.9.6). |
| `TYPE_RESU` | text, optional | `'VALE'` | *result type*. One of `'VALE'`, `'INST'`, `'VALE_ABS'`, `'NUME_ORDRE'`. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and equal_to("TYPE_MAXI", 'MAXI_ABS') or equal_to("TYPE_MAXI", 'MINI_ABS')`. With `TYPE_MAXI='MAXI_ABS'` or `'MINI_ABS'`: `'VALE'` the signed extreme value, `'VALE_ABS'` its absolute value, `'INST'` the time at which it occurs, `'NUME_ORDRE'` its step index. |
| `TYPE_RESU` | text, optional | `'VALE'` | *result type*. One of `'VALE'`, `'INST'`, `'NUME_ORDRE'`. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and equal_to("TYPE_MAXI", 'MAXI') or equal_to("TYPE_MAXI", 'MINI') or equal_to("TYPE_MAXI", 'NORM_TRAN')`. With `TYPE_MAXI='MAXI'`, `'MINI'` or `'NORM_TRAN'`: `'VALE'` the extreme value, `'INST'` the time at which it occurs (`upstream/astest/forma02d.comm:192`), `'NUME_ORDRE'` its step index. |
| `TOUT_ORDRE` | text, optional | — | One of `'OUI'`. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and exists("TYPE_MAXI")`. With `TYPE_MAXI`: every step. |
| `LIST_INST` | `listr8_sdaster`, optional | — | *time-step list*. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and exists("TYPE_MAXI")`. With `TYPE_MAXI`: these times, from a list. |
| `LIST_FREQ` | `listr8_sdaster`, optional | — | Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and exists("TYPE_MAXI")`. With `TYPE_MAXI`: these frequencies, from a list. |
| `NUME_ORDRE` | integer, optional, list | — | *step index*. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and exists("TYPE_MAXI")`. With `TYPE_MAXI`: these steps. |
| `INST` | real, optional, list | — | *time step (pseudo-time)*. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and exists("TYPE_MAXI")`. With `TYPE_MAXI`: these times. |
| `FREQ` | real, optional, list | — | *frequency*. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and exists("TYPE_MAXI")`. With `TYPE_MAXI`: these frequencies. |
| `NUME_MODE` | integer, optional, list | — | Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and exists("TYPE_MAXI")`. With `TYPE_MAXI`: these modes. |
| `NOEUD_CMP` | text, optional, list | — | Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and exists("TYPE_MAXI")`. With `TYPE_MAXI`: these static modes. Not used in Tier 1. |
| `NOM_CAS` | text, optional, list | — | Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and exists("TYPE_MAXI")`. With `TYPE_MAXI`: these load cases. Not used in Tier 1. |
| `ANGLE` | real, optional, list | — | Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and exists("TYPE_MAXI")`. With `TYPE_MAXI`: these Fourier angles. Not used in Tier 1. |
| `NUME_ORDRE` | integer, optional | — | *step index*. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and not exists("TYPE_MAXI")`. The step to extract. The usual choice: `NUME_ORDRE=1` for a static result with one step (`upstream/astest/comp009a.comm:231`). |
| `INST` | real, optional | — | *time step (pseudo-time)*. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and not exists("TYPE_MAXI")`. The time to extract. With `INTERPOL='LIN'` it may fall between two stored times. |
| `FREQ` | real, optional | — | *frequency*. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and not exists("TYPE_MAXI")`. The frequency to extract (modal or harmonic result). |
| `NUME_MODE` | integer, optional | — | Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and not exists("TYPE_MAXI")`. The mode number to extract (modal result). |
| `NOEUD_CMP` | text, optional, list of up to 2 | — | Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and not exists("TYPE_MAXI")`. The static mode to extract. Not used in Tier 1. |
| `NOM_CAS` | text, optional | — | Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and not exists("TYPE_MAXI")`. The load case to extract. Not used in Tier 1. |
| `ANGLE` | real, optional | — | Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and not exists("TYPE_MAXI")`. The Fourier angle to extract. Not used in Tier 1. |
| `INTERPOL` | text, optional | `'NON'` | *interpolation*. One of `'NON'`, `'LIN'`. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and not exists("TYPE_MAXI") and exists("INST")`. `'LIN'`: interpolate linearly between the two stored times around `INST`; `'NON'`: the time must be stored (within `PRECISION`). |
| `CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT")`. How `INST`/`FREQ` are matched to stored values. |
| `PRECISION` | real, optional | `1e-06` | *tolerance*. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and equal_to("CRITERE", 'RELATIF')`. Matching tolerance. |
| `PRECISION` | real, required | — | *tolerance*. Only when `equal_to("OPERATION", 'EXTR') and exists("RESULTAT") and equal_to("CRITERE", 'ABSOLU')`. Matching tolerance, required with `'ABSOLU'`. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `2` prints the created field (`upstream/bibfor/op/op0195.F90:403`). |
| `TITRE` | text, optional | — | *title*. Title of the field. |

2 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at most one of `NUME_DDL`, `CHAM_NO` may be given (`EXCLUS`).
- when `equal_to("OPERATION", 'AFFE')`: exactly one of `MAILLAGE`, `MODELE` must be given (`UN_PARMI`).
- `AFFE`: at least one of `TOUT`, `GROUP_MA`, `GROUP_NO`, `NOEUD` must be given (`AU_MOINS_UN`).
- `AFFE`: exactly one of `VALE`, `VALE_I`, `VALE_C`, `VALE_F` must be given (`UN_PARMI`).
- when `equal_to("OPERATION", 'ASSE')`: exactly one of `MAILLAGE`, `MODELE` must be given (`UN_PARMI`).
- `ASSE`: at least one of `TOUT`, `GROUP_MA`, `GROUP_NO` must be given (`AU_MOINS_UN`).
- `ASSE`: if `NOM_CMP_RESU` is given, `NOM_CMP` must all be given (`PRESENT_PRESENT`).
- when `equal_to("OPERATION", 'EXTR')`: at least one of `MAILLAGE`, `FISSURE`, `RESULTAT`, `TABLE`, `CARA_ELEM`, `CHARGE` must be given (`AU_MOINS_UN`).
- when `equal_to("OPERATION", 'EXTR')`: if `MAILLAGE` is given, none of `FISSURE`, `RESULTAT`, `CARA_ELEM`, `CHARGE` may be given (`PRESENT_ABSENT`).
- when `equal_to("OPERATION", 'EXTR')`: if `FISSURE` is given, none of `MAILLAGE`, `RESULTAT`, `TABLE`, `CARA_ELEM`, `CHARGE` may be given (`PRESENT_ABSENT`).
- when `equal_to("OPERATION", 'EXTR')`: if `RESULTAT` is given, none of `FISSURE`, `MAILLAGE`, `TABLE`, `CARA_ELEM`, `CHARGE` may be given (`PRESENT_ABSENT`).
- when `equal_to("OPERATION", 'EXTR')`: if `TABLE` is given, none of `RESULTAT`, `FISSURE`, `CARA_ELEM`, `CHARGE` may be given (`PRESENT_ABSENT`).
- when `equal_to("OPERATION", 'EXTR')`: if `CARA_ELEM` is given, none of `MAILLAGE`, `TABLE`, `RESULTAT`, `FISSURE`, `CHARGE` may be given (`PRESENT_ABSENT`).
- when `equal_to("OPERATION", 'EXTR')`: if `CHARGE` is given, none of `MAILLAGE`, `TABLE`, `RESULTAT`, `FISSURE`, `CARA_ELEM` may be given (`PRESENT_ABSENT`).
- when `exists("TYPE_MAXI")`: at most one of `TOUT_ORDRE`, `LIST_INST`, `LIST_FREQ`, `NUME_ORDRE`, `INST`, `FREQ`, `NUME_MODE`, `NOEUD_CMP`, `NOM_CAS`, `ANGLE` may be given (`EXCLUS`).
- when `not exists("TYPE_MAXI")`: exactly one of `NUME_ORDRE`, `INST`, `FREQ`, `NUME_MODE`, `NOEUD_CMP`, `NOM_CAS`, `ANGLE` must be given (`UN_PARMI`).

## What the solver does

- One branch per `OPERATION` (`upstream/bibfor/op/op0195.F90:213`–`:306`): `NORMALE` → `cnonor`,
  `AFFE` → `cnoaff` (nodal) or `caraff` (map, then converted to an element field with `chpchd`),
  `ASSE` → `chpass`, `COMB` → `x195cb`, `EVAL` → `chpeva`, `DISC` → `chpchd`, `EXTR` →
  `chprec` (or `u195tb` from a table).
- Element fields need a model to know the elements and their points (`:148`); nodal fields and
  maps only need the mesh.
- After the branch: optional imposed numbering (`NUME_DDL`/`CHAM_NO`, `:313`), sub-point
  duplication (`AFFE_SP`, `:388`), NaN check of unassigned values when `PROL_ZERO='NON'`
  (`:409`), and the mesh and type checks (`:420`–`:442`).

## Patterns

### Uniform temperature field for thermal strains

A nodal temperature field, given later to `AFFE_MATERIAU` with `AFFE_VARC=_F(NOM_VARC="TEMP",
CHAM_GD=..., VALE_REF=...)`.

Source: `upstream/astest/erreu02a.comm:85`.

```python
TEMPI = CREA_CHAMP(
    TYPE_CHAM="NOEU_TEMP_R",
    OPERATION="AFFE",
    MAILLAGE=M,
    AFFE=_F(TOUT="OUI", NOM_CMP="TEMP", VALE=20.0),
)
```

### Displacement field of one step of a result

Inside a loop in the source (indentation kept).

Source: `upstream/astest/comp009a.comm:231`.

```python
    EM = CREA_CHAMP(
        TYPE_CHAM="NOEU_DEPL_R", OPERATION="EXTR", RESULTAT=RESU[i], NOM_CHAM="DEPL", NUME_ORDRE=1
    )
```

### Change the sign of a field

Source: `upstream/astest/cont008a.comm:185`.

```python
mdepl = CREA_CHAMP(TYPE_CHAM="NOEU_DEPL_R", OPERATION="COMB", COMB=_F(CHAM_GD=depl, COEF_R=-1.0))
```

### Node coordinates as a field

Source: `upstream/astest/sdls115a.comm:86`.

```python
CHGEOM = CREA_CHAMP(TYPE_CHAM="NOEU_GEOM_R", OPERATION="EXTR", MAILLAGE=MAIL, NOM_CHAM="GEOMETRIE")
```

### Field of the maximum over time, and when it occurs

Source: `upstream/astest/forma02d.comm:192`.

```python
EXTR_T = CREA_CHAMP(
    TYPE_CHAM="ELNO_SIEF_R",
    OPERATION="EXTR",
    RESULTAT=DYNATRA,
    NOM_CHAM="SIPO_ELNO",
    TYPE_MAXI="MAXI",
    TYPE_RESU="INST",
    LIST_INST=LISTER,
    PRECISION=1.0e-6,
)
```

### Move a nodal field to Gauss points

Inside a loop in the source (indentation kept).

Source: `upstream/astest/cont006c.comm:119`.

```python
    CHXG = CREA_CHAMP(
        OPERATION="DISC", TYPE_CHAM="ELGA_GEOM_R", PROL_ZERO="OUI", CHAM_GD=CHXN, MODELE=MODELE
    )
```

### Normals on a group of faces

Source: `upstream/astest/ssls101m.comm:93`.

```python
CHNOR = CREA_CHAMP(
    TYPE_CHAM="NOEU_GEOM_R", OPERATION="NORMALE", MODELE=MODEL, GROUP_MA="DBCE", INFO=1
)
```

## Pitfalls

- **`TYPE_CHAM` must match what is built.** Extracting `'DEPL'` needs `'NOEU_DEPL_R'`;
  `'SIEF_ELGA'` needs `'ELGA_SIEF_R'`. A mismatch in location gives `CALCULEL4_70`, in quantity
  `CALCULEL4_71` (`upstream/bibfor/op/op0195.F90:432`).
- **Partial assignment of element fields.** With the default `PROL_ZERO='NON'`, unassigned
  values of a real element field are NaN and the run stops (`upstream/bibfor/op/op0195.F90:409`).
  Use `PROL_ZERO='OUI'` when only some elements get a value.
- **Element fields need `MODELE`.** `AFFE`, `ASSE` and `DISC` to `ELEM`/`ELNO`/`ELGA` need the
  model (`upstream/bibfor/op/op0195.F90:148`); `MAILLAGE` alone only builds nodal fields and maps.
- **`reuse` only for `ASSE` and `COMB`.** Any other operation with `reuse=` stops with
  `UTILITAI3_43`.
- **`DISC` keeps the quantity.** It changes where values live, not what they are: the input and
  output quantities must match, except real/complex pairs and `VARI_R`/`VAR2_R`
  (`UTILITAI3_27`, `upstream/bibfor/op/op0195.F90:293`).
- **`COMB` and numbering.** `COMB` combines nodal fields; imposing their numbering on the output
  with `NUME_DDL`/`CHAM_NO` drops the Lagrange DOFs of dualized boundary conditions
  (`CREACHAMP1_14`).
- **A temperature field is not a thermal load by itself.** It acts only once given to
  `AFFE_MATERIAU` (`AFFE_VARC`, with `VALE_REF`) and the material has a thermal expansion
  coefficient; see [AFFE_MATERIAU](AFFE_MATERIAU.md).

## See also

- French reference: U4.72.04 (French text: `en/docs/_src/U4.72.04.fr.md`; translation: `en/docs/U4.72.04.md`)
- Catalog: `en/commands/CREA_CHAMP.json` (generated from `upstream/code_aster/Cata/Commands/crea_champ.py:41`)
- Implementation: `upstream/bibfor/op/op0195.F90`
- Uses of the field: [AFFE_MATERIAU](AFFE_MATERIAU.md) (`AFFE_VARC`), [POST_RELEVE_T](POST_RELEVE_T.md)
  (`CHAM_GD`), [POST_ELEM](POST_ELEM.md) (`CHAM_GD`), [IMPR_RESU](IMPR_RESU.md) (`CHAM_GD`),
  [TEST_RESU](TEST_RESU.md) (`CHAM_NO`, `CARTE`)
- Example: `upstream/astest/erreu02a.comm` (line 85)
- Example: `upstream/astest/comp009a.comm` (line 231)
- Example: `upstream/astest/forma02d.comm` (line 192)
