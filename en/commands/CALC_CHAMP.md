---
command: CALC_CHAMP
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/calc_champ.py:38
doc_fr: U4.81.04
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3d)
examples: [gcpc002c, ssll118a, ssll101a, erreu02a, hsns102b, hsnv100a]
---

# CALC_CHAMP — compute derived fields

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.

`CALC_CHAMP` adds fields to a result, computed from the fields the analysis stored: stresses at
element nodes and averaged at nodes, equivalent stresses (von Mises, Tresca, principal
stresses), strains, energies, nodal forces and support reactions. Each field is requested by
its option name (for example `'SIGM_NOEU'`) under a keyword that groups options by kind
(`CONTRAINTE`, `CRITERES`, `DEFORMATION`, `ENERGIE`, `FORCE`, …). The result is normally
updated in place with `reuse=`; without it a new result of the same type is created
(`upstream/code_aster/CodeCommands/calc_champ.py:41`). The command reads the model, material,
element properties and loads stored in the result by the analysis, so for the result of
`MECA_STATIQUE` it needs only `RESULTAT` and the options. The decision it encodes is which
quantities the engineer will look at, and where: at Gauss points (`_ELGA`), at the nodes of each
element (`_ELNO`, discontinuous between elements) or averaged at nodes (`_NOEU`, smooth).

| Fact | Value |
|---|---|
| Catalog description (fr) | «Completer ou creer un resultat en calculant des champs par elements ou aux noeuds» |
| Kind | `OPER` (Fortran operator 52, `upstream/bibfor/op/op0052.F90`) |
| Result | `resultat_sdaster` (same type as `RESULTAT`) |
| Can reuse its input (`reuse=`) | yes (the object given in `RESULTAT`); catalog `reentrant='f:RESULTAT'` |
| French reference | U4.81.04 — from en/doc-ids.yaml (status: proposed) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `CONTRAINTE`, `SIGM_ELNO`, `SIGM_NOEU`, `SIEF_ELNO`, `CRITERES`, `SIEQ_ELNO`, `SIEQ_NOEU`, `DEFORMATION`, `EPSI_ELNO`, `EPSI_NOEU`, `FORCE`, `REAC_NODA`, `FORC_NODA`, `ENERGIE` |

## Keywords

The option keywords exist in one bloc per kind of result: linear mechanics (`evol_elas`,
`mode_meca`, `mult_elas`, …), dynamics (`dyna_harmo`, `dyna_trans`), nonlinear mechanics
(`evol_noli`), thermal (`evol_ther`), drying (`evol_sech`) and acoustics. A keyword therefore
appears once per bloc, with the option list that fits that result type
(`upstream/code_aster/Cata/Commands/calc_champ.py:95`). The Tier 1 options are described in the
next table.

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MODELE` | `modele_sdaster`, optional | — | *model*. Overrides the model stored in the result; a model different from the stored one gives `RESULT1_37` and the given one is used (`upstream/bibfor/resu_util/rslesd.F90:78`). Leave it out. |
| `CHAM_MATER` | `cham_mater`, optional | — | *material field*. Overrides the stored material field (`RESULT1_39`). Leave it out unless the result has none, for example a result read from a file. |
| `CARA_ELEM` | `cara_elem`, optional | — | *element properties*. Overrides the stored element properties (`RESULT1_38`). Same advice. |
| `RESULTAT` | `resultat_sdaster`, required | — | *result*. The result to complete (catalog: result of a global command). |
| `TOUT_ORDRE` | text, optional | — | *all steps*. One of `'OUI'`. Compute at every step of the result. This is also what happens when no step is selected (TODO(verify) the default in `upstream/bibfor/calculel/cclord.F90`). |
| `NUME_ORDRE` | integer, optional, list | — | *step index*. Compute only at these steps (1-based storage indices). |
| `NUME_MODE` | integer, optional, list | — | Compute only for these mode numbers of a modal result. |
| `NOEUD_CMP` | text, optional, list | — | Selects static modes of a `MODE_STATIQUE` result by node and component name. Not used in Tier 1. |
| `NOM_CAS` | text, optional | — | Selects a load case of a `mult_elas` result (`MACRO_ELAS_MULT`) by name. Not used in Tier 1. |
| `INST` | real, optional, list | — | *time step (pseudo-time)*. Compute only at these times, matched with `CRITERE`/`PRECISION`. |
| `FREQ` | real, optional, list | — | *frequency*. Compute only at these frequencies (modal or harmonic results). |
| `LIST_INST` | `listr8_sdaster`, optional | — | *time-step list*. Same as `INST`, from a `DEFI_LIST_REEL` list. |
| `LIST_FREQ` | `listr8_sdaster`, optional | — | Same as `FREQ`, from a list. |
| `CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. How `PRECISION` is applied when `INST`/`FREQ` values are matched with the stored ones. |
| `PRECISION` | real, optional | `1e-06` | *tolerance*. Only when `equal_to("CRITERE", 'RELATIF')`. Relative matching tolerance. |
| `PRECISION` | real, required | — | *tolerance*. Only when `equal_to("CRITERE", 'ABSOLU')`. Absolute matching tolerance, in the unit of the time or frequency. |
| `LIST_ORDRE` | `listis_sdaster`, optional | — | Same as `NUME_ORDRE`, from a list of integers (`DEFI_LIST_ENTI`). |
| `TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Compute on all elements (catalog help). The default when `GROUP_MA` is not given. |
| `GROUP_MA` | element group, optional, list | — | *element group*. Compute only on the elements of these groups (catalog help): to save time and disk on large models (`upstream/astest/hsns102b.comm:139`). See the pitfall on nodal averages. |
| `CONTRAINTE` | text, optional, list | — | *stress fields*. Linear and dynamic results. Stress and generalized-force options (16 values; see the .json and the options table): `SIGM_ELNO`, `SIGM_NOEU` for solids, `EFGE_ELNO`, `EFGE_NOEU` for shells and beams. |
| `DEFORMATION` | text, optional, list | — | *strain fields*. Linear and dynamic results. Strain options (18 values; see the .json): `EPSI_ELNO`, `EPSI_NOEU` for solids, `DEGE_*` for shells and beams, `EPME_*` for the mechanical part of the strain (total minus thermal). |
| `ENERGIE` | text, optional, list | — | *energy fields*. Linear and dynamic results. Energy options (15 values; see the .json): `EPOT_ELEM` (strain energy per element), `ENEL_*` (elastic energy density). Use it to find the parts of a structure that carry the load. |
| `CRITERES` | text, optional, list | — | *equivalent-stress fields*. Linear and dynamic results. One of `'EPEQ_ELGA'`, `'EPEQ_ELNO'`, `'EPEQ_NOEU'`, `'EPGQ_ELGA'`, `'EPGQ_ELNO'`, `'EPGQ_NOEU'`, `'EPMQ_ELGA'`, `'EPMQ_ELNO'`, `'EPMQ_NOEU'`, `'SIEQ_ELGA'`, `'SIEQ_ELNO'`, `'SIEQ_NOEU'`. `SIEQ_*` holds the equivalent stresses (components listed below the options table); `EP*Q_*` the equivalent strains. |
| `VARI_INTERNE` | text, optional, list | — | Linear and dynamic results. One of `'VARC_ELGA'`, `'VARC_ELNO'`, `'VARC_NOEU'`: the external state variables (for example the temperature given by `AFFE_VARC`) at Gauss points or nodes («Variables de commande», `upstream/code_aster/Cata/Commons/c_nom_cham_into.py:330`). To check the temperature a thermo-elastic analysis used. |
| `PROPRIETES` | text, optional, list | — | Linear, dynamic and nonlinear results. One of `'MATE_ELEM'`, `'MATE_ELGA'`: the elastic material parameters per element or at Gauss points (`c_nom_cham_into.py:452`). To check what material each element received. |
| `FORCE` | text, optional, list | — | *force fields*. Linear, dynamic and nonlinear results. One of `'FORC_NODA'`, `'REAC_NODA'`. `FORC_NODA`: the element internal forces assembled at nodes. `REAC_NODA`: `FORC_NODA` minus the applied loads, which leaves the support reactions (`upstream/bibfor/calculel/ccfnrn.F90:715`). Use `REAC_NODA` for reaction sums (`tests/fixtures/solid_static/input/run.comm:45`). |
| `EXCIT` | factor keyword, optional, repeatable | — | *applied loads*. Linear and dynamic results. Loads to use instead of those stored in the result (catalog help: loads with temperatures, distributed loads on beams, …). When given and different from the stored ones, `CHARGES9_53` warns and the given ones are used (`upstream/bibfor/resu_util/rsGetMainPara.F90:114`). Needed for results that store no loads, such as dynamic ones (`CALCCHAMP_54`). Leave it out after `MECA_STATIQUE`. |
| `EXCIT / CHARGE` | `char_meca` or `char_cine_meca`, required | — | *load*. One load. |
| `EXCIT / FONC_MULT` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional | — | *load multiplier function*. Multiplier of the load as a function of time, as in the analysis. |
| `EXCIT / COEF_MULT` | real, optional | — | *multiplying coefficients*. A constant multiplier of the load. Rule: not with `FONC_MULT`. |
| `EXCIT / TYPE_CHARGE` | text, optional | `'FIXE_CSTE'` | *load type*. One of `'FIXE_CSTE'`. Fixed load: the only type for linear results. |
| `CHAM_UTIL` | factor keyword, optional, repeatable | — | *user-defined field*. Linear, dynamic, nonlinear, thermal and drying results. Builds a new field `UTnn_<location>` from an existing field, with a formula, a predefined criterion or a norm. To get a quantity code_aster does not provide, for example a resultant moment of a beam (`upstream/astest/ssll101a.comm:164`). |
| `CHAM_UTIL / NOM_CHAM` | text, required | — | *field name*. The input field (catalog help), for example `'EFGE_ELNO'`; it must already exist or be computed in the same call (`upstream/astest/ssll101a.comm:165`). |
| `CHAM_UTIL / FORMULE` | `formule`, optional, list | — | One or more `FORMULE` objects whose parameters are components of the input field (catalog help: formula that gives the criterion); each gives one component of the output (`upstream/astest/ssll101a.comm:114`). |
| `CHAM_UTIL / CRITERE` | text, optional | — | *tolerance type*. One of `'TRACE'`, `'VMIS'`, `'INVA_2'`: a predefined criterion of the input tensor (catalog help). No upstream test case uses it; TODO(verify) against U4.81.04. |
| `CHAM_UTIL / NORME` | text, optional | — | *norm*. One of `'L2'`, `'FROBENIUS'`: a predefined norm of the input field (catalog help). No upstream test case; TODO(verify). |
| `CHAM_UTIL / NUME_CHAM_RESU` | integer, required | — | Number of the output field: `1` gives `UT01_ELNO` for an `ELNO` input (catalog help; `upstream/astest/ssll101a.comm:173`). Range: ≥ 1, ≤ 20. |
| `ACOUSTIQUE` | text, optional, list | — | *acoustic*. Dynamic and acoustic results. Acoustic intensity and pressure options. Out of scope. |
| `EXCIT / PHAS_DEG` | real, optional | `0.0` | Harmonic results. Phase of the load, in degrees. Out of scope. |
| `EXCIT / PUIS_PULS` | integer, optional | `0` | Harmonic results. Power of the angular frequency that multiplies the load. TODO(verify) against U4.81.04. Out of scope. |
| `EXCIT / FONC_MULT_C` | `fonction_c` or `formule_c`, optional | — | Harmonic results. Complex multiplier function. Out of scope. |
| `EXCIT / COEF_MULT_C` | complex, optional | — | Harmonic results. Complex constant multiplier. Out of scope. |
| `SOUS_POINT` | text, optional, list | — | Nonlinear results. One of `'DEPL_ELGA'`, `'TEMP_ELGA'`: fields at the sub-points of multilayer shells or multifiber beams (catalog help). Out of scope. |
| `CONTRAINTE` | text, optional, list | — | *stress fields*. Nonlinear results. Same use as for linear results (`SIEF_ELGA` is already stored by the analysis). |
| `DEFORMATION` | text, optional, list | — | *strain fields*. Nonlinear results. Adds plastic and creep strains (`EPFD_*`, `EPFP_*`, …) to the linear list. |
| `ENERGIE` | text, optional, list | — | *energy fields*. Nonlinear results. Adds dissipated and total energies. |
| `CRITERES` | text, optional, list | — | *equivalent-stress fields*. Nonlinear results. Adds damage and fracture indicators (`DERA_*`, `ENDO_*`) to the linear list. |
| `VARI_INTERNE` | text, optional, list | — | Nonlinear results. Adds `VARI_ELNO`, `VARI_NOEU`: the internal variables of the constitutive law at nodes. |
| `HYDRAULIQUE` | text, optional, list | — | Nonlinear results. One of `'FLHN_ELGA'`: hydraulic flux of coupled models (catalog help). Out of scope. |
| `EXCIT / TYPE_CHARGE` | text, optional | `'FIXE_CSTE'` | *load type*. Nonlinear results. One of `'FIXE_CSTE'`, `'FIXE_PILO'`, `'SUIV'`, `'DIDI'`: fixed, driven (`PILOTAGE`), follower, or differential imposed displacement, as in the nonlinear analysis. |
| `THERMIQUE` | text, optional, list | — | *thermal*. Thermal results. Heat flux (`FLUX_*`), temperature gradient (`GRAT_*`) and related options (13 values; see the .json). Tier 2 (steady thermal). |
| `EXCIT / CHARGE` | `char_ther` or `char_cine_ther`, required | — | *load*. Thermal results. A thermal load. |
| `SECHAGE` | text, optional, list | — | Drying results. Drying flux, gradient and humidity options. Out of scope. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`, `3`. Higher values print more detail. |
| `PARALLELISME_TEMPS` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. `'OUI'` distributes the steps between MPI processes in a parallel run (`upstream/bibfor/calculel/ccfnrn.F90:136`). Serial runs: leave `'NON'`. |
| `TITRE` | text, optional | — | *title*. Title of the result. |

1 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

### Tier 1 options

Meanings from the catalog strings of `upstream/code_aster/Cata/Commons/c_nom_cham_into.py`
(line given) and the glossary. `_ELGA` = at Gauss points, `_ELNO` = at the nodes of each
element, `_NOEU` = averaged at nodes, `_ELEM` = one value per element.

| Option | Keyword | Meaning | Use |
|---|---|---|---|
| `SIEF_ELGA` | `CONTRAINTE` | Stresses and forces at Gauss points (`:86`). | Stored by `MECA_STATIQUE`; the starting point of the other stress options. |
| `SIGM_ELNO` | `CONTRAINTE` | Stresses at element nodes (`:97`), components `SIXX` … `SIYZ`. | Peak stresses without smoothing; jumps between elements show mesh quality. |
| `SIGM_NOEU` | `CONTRAINTE` | Stresses at nodes (`:98`): `SIGM_ELNO` averaged at each node. | Contour plots, values at a node. |
| `SIEF_ELNO`, `SIEF_NOEU` | `CONTRAINTE` | Stresses and forces at element nodes / at nodes (`:87`, `:95`). | For beams and discrete elements, where `SIEF` holds forces. |
| `EFGE_ELNO` | `CONTRAINTE` | Generalized forces at element nodes, in the local axes (`:77`): shell `NXX`, `NYY`, `NXY`, `MXX`, `MYY`, `MXY`, `QX`, `QY`; beam forces and moments. | Shell and beam design forces per unit length. |
| `EFGE_NOEU` | `CONTRAINTE` | Generalized forces at nodes (`:85`). | Shell results at a node (`tests/fixtures/shell_static/input/run.comm:64`). |
| `SIEQ_ELNO`, `SIEQ_NOEU` | `CRITERES` | Equivalent stresses at element nodes / at nodes (`:323`, `:327`). | Von Mises and principal stress plots. |
| `EPSI_ELNO`, `EPSI_NOEU` | `DEFORMATION` | Strains at element nodes / at nodes (`:185`, `:186`). | Compare with strain gauges. |
| `EPOT_ELEM` | `ENERGIE` | Elastic strain energy per element (`:244`). | Where the structure stores energy. |
| `FORC_NODA` | `FORCE` | Nodal forces (`:382`). | Internal force balance on a cut. |
| `REAC_NODA` | `FORCE` | Nodal reactions (`:383`). | Support reactions; their sum balances the applied load. |

`SIEQ_*` components, as written to our solid fixture's MED file
(`tests/fixtures/solid_static/output/run.rmed`, field `RESU____SIEQ_NOEU`): `VMIS` (von Mises),
`TRESCA`, `PRIN_1`, `PRIN_2`, `PRIN_3` (principal stresses, in increasing order: `PRIN_1` ≤
`PRIN_2` ≤ `PRIN_3` at all 4,622 nodes of that run), `VMIS_SG` (von Mises signed by the trace of
the stress), `VECT_1_X` … `VECT_3_Z` (principal directions), `TRSIG` (trace) and `TRIAX`
(triaxiality).

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `INST`, `FREQ`, `NUME_MODE`, `NOEUD_CMP`, `LIST_INST`, `LIST_FREQ`, `LIST_ORDRE`, `NOM_CAS` may be given (`EXCLUS`).
- command: if `TOUT` is given, none of `GROUP_MA` may be given (`PRESENT_ABSENT`).
- when `is_type("RESULTAT") in (evol_elas,mode_meca,mode_meca_c,comb_fourier,mult_elas,fourier_elas,mode_flamb)`: at least one of `CONTRAINTE`, `DEFORMATION`, `ENERGIE`, `CRITERES`, `VARI_INTERNE`, `PROPRIETES`, `FORCE`, `CHAM_UTIL` must be given (`AU_MOINS_UN`).
- `EXCIT`: at most one of `FONC_MULT`, `COEF_MULT` may be given (`EXCLUS`).
- `CHAM_UTIL`: exactly one of `FORMULE`, `CRITERE`, `NORME` must be given (`UN_PARMI`).
- when `is_type("RESULTAT") in (dyna_harmo,dyna_trans)`: at least one of `CONTRAINTE`, `DEFORMATION`, `ENERGIE`, `CRITERES`, `VARI_INTERNE`, `PROPRIETES`, `ACOUSTIQUE`, `FORCE`, `CHAM_UTIL` must be given (`AU_MOINS_UN`).
- when `is_type("RESULTAT") in (evol_noli,)`: at least one of `SOUS_POINT`, `CONTRAINTE`, `DEFORMATION`, `ENERGIE`, `CRITERES`, `VARI_INTERNE`, `PROPRIETES`, `HYDRAULIQUE`, `FORCE`, `CHAM_UTIL` must be given (`AU_MOINS_UN`).
- when `is_type("RESULTAT") in (evol_ther,fourier_ther,)`: at least one of `THERMIQUE`, `CHAM_UTIL` must be given (`AU_MOINS_UN`).
- when `is_type("RESULTAT") in (evol_sech,)`: at least one of `SECHAGE`, `CHAM_UTIL` must be given (`AU_MOINS_UN`).
- when `is_type("RESULTAT") in (acou_harmo,mode_acou,tran_gene,harm_gene)`: at least one of `ACOUSTIQUE`, `CHAM_UTIL` must be given (`AU_MOINS_UN`).

## What the solver does

- **Dependencies are computed for you.** The list of requested options is completed with the
  options they depend on (`upstream/bibfor/calculel/calcop.F90:175`): `SIGM_NOEU` needs
  `SIGM_ELNO`, which needs `SIEF_ELGA` (comment at `calcop.F90:240`). Every `_NOEU` option is
  computed from the `_ELNO` option of the same name (`upstream/bibfor/calculel/ccliop.F90:121`).
  Options computed only as a dependency are kept on the temporary base and not stored in the
  result, unless they were also requested (`calcop.F90:283`–`:296`).
- **Fields already present are not recomputed.** If a requested field already exists at every
  selected step, `CALCCHAMP_1` warns and nothing is done for it (`calcop.F90:302`).
- **Reactions.** `REAC_NODA` = `FORC_NODA` − (fixed applied loads) − (follower loads), and also
  − (driven loads) for nonlinear results (`ccfnrn.F90:706`–`:729`). It is non-zero only where DOFs
  are imposed. Velocity-dependent damping is not included for dynamic results (`CALCCHAMP_4`).
- **Loads, model and material come from the result**, step by step; the keywords of the same
  name override them with a warning (`rslesd.F90`, `rsGetMainPara.F90`).

## Patterns

### Stresses, von Mises and reactions after a solid analysis

The usual Tier 1 post-processing call: nodal stresses, equivalent stresses and reactions in
one call, updating the result in place.

Source: `tests/fixtures/solid_static/input/run.comm:40`.

```python
RESU = CALC_CHAMP(
    reuse=RESU,
    RESULTAT=RESU,
    CONTRAINTE=("SIGM_ELNO", "SIGM_NOEU"),
    CRITERES=("SIEQ_ELNO", "SIEQ_NOEU"),
    FORCE="REAC_NODA",
)
```

### Shell resultants and reactions

Source: `tests/fixtures/shell_static/input/run.comm:63`.

```python
RESU = CALC_CHAMP(
    reuse=RESU, RESULTAT=RESU, CONTRAINTE=("EFGE_ELNO", "EFGE_NOEU"), FORCE="REAC_NODA"
)
```

### Element-node stresses only

Source: `upstream/astest/gcpc002c.comm:52`.

```python
VECAS = CALC_CHAMP(reuse=VECAS, RESULTAT=VECAS, CONTRAINTE=("SIGM_ELNO"))
```

### Strains and stresses at nodes

`SIGM_NOEU` alone is enough: `SIGM_ELNO` is computed as a dependency (and not stored).

Source: `upstream/astest/erreu02a.comm:125`.

```python
U1 = CALC_CHAMP(reuse=U1, RESULTAT=U1, DEFORMATION="EPSI_NOEU", CONTRAINTE="SIGM_NOEU")
```

### Restricted to one element group, new result

Without `reuse=`, a new result is created; here only the elements of `GEOB` get stresses.

Source: `upstream/astest/hsns102b.comm:139`.

```python
DEPB = CALC_CHAMP(CONTRAINTE=("SIGM_ELNO"), RESULTAT=DEP, GROUP_MA="GEOB")
```

### Beam forces, then nodal forces

Source: `upstream/astest/ssll118a.comm:59` and `:62`.

```python
MEST1 = CALC_CHAMP(reuse=MEST1, RESULTAT=MEST1, CONTRAINTE=("EFGE_ELGA",))

MEST1 = CALC_CHAMP(reuse=MEST1, RESULTAT=MEST1, FORCE="FORC_NODA")
```

### A user-defined field from a formula

The resultant moment of a beam, sqrt(MT² + MFY² + MFZ²), computed from `EFGE_ELNO` into
`UT01_ELNO`.

Source: `upstream/astest/ssll101a.comm:161` (formula at `:114`).

```python
Meq = FORMULE(NOM_PARA=["MT", "MFY", "MFZ"], VALE="sqrt(MT*MT+MFY*MFY+MFZ*MFZ)")

STAT1 = CALC_CHAMP(
    reuse=STAT1,
    PARALLELISME_TEMPS="NON",
    CHAM_UTIL=_F(FORMULE=(Meq,), NOM_CHAM="EFGE_ELNO", NUME_CHAM_RESU=1),
    CONTRAINTE="EFGE_ELNO",
    INFO=2,
    NUME_ORDRE=1,
    RESULTAT=STAT1,
)
```

## Pitfalls

- **`SIEQ_NOEU` is not computed from `SIGM_NOEU`.** It is the nodal average of `SIEQ_ELNO`
  (`ccliop.F90:121`), so its von Mises is not the von Mises of the averaged stress. In our solid
  fixture the two differ by up to 1.7 MPa where the peak is 34.7 MPa, while the trace `TRSIG`,
  which is linear, matches to round-off (computed from `tests/fixtures/solid_static/output/run.rmed`).
  For the same reason `VMIS_SG` at a node can be smaller in magnitude than `VMIS` where the sign
  changes between elements. Report which field a value comes from.
- **Nodal averages depend on `GROUP_MA`.** With `GROUP_MA`, `_NOEU` fields average only over the
  selected elements (the `ELNO` field is reduced to that list, `upstream/bibfor/calculel/ccchno.F90:138`).
  Nodes on the border of the group then get a one-sided value.
- **Asking again does nothing.** A field already in the result is not recomputed (`CALCCHAMP_1`),
  even after the loads or the material changed in the command file. Create a new result
  (without `reuse=`) to recompute.
- **Intermediate fields are not stored.** Requesting `SIGM_NOEU` alone does not leave `SIGM_ELNO`
  in the result (`calcop.F90:283`); `IMPR_RESU` or `POST_RELEVE_T` on `SIGM_ELNO` then fails. Ask
  for every field you will print or test.
- **Shell and beam fields are in local axes.** `EFGE_ELNO` is in the local axes of each element
  (`c_nom_cham_into.py:77`); `POST_RELEVE_T` warns (`POSTRELE_70`) when such a field is extracted
  without `REPERE='LOCAL'`. Element local axes are set by `AFFE_CARA_ELEM` (`ANGL_REP`).
- **Reactions from a dynamic result need the loads.** Dynamic results store no loads, so
  `REAC_NODA` without `EXCIT` gets `CALCCHAMP_54` and equals `FORC_NODA`
  (`ccfnrn.F90:733`).
- **An option the elements cannot compute.** `CALCCHAMP_89` means the field could not be
  computed, usually because the elementary calculation does not exist for that element type
  (for example a solid stress option on shell elements). Choose the option family that fits the
  modeling (`SIGM_*` for solids, `EFGE_*` for shells and beams).

## See also

- French reference: U4.81.04 (translation: `en/docs/U4.81.04.md` once task 5.x lands)
- Catalog: `en/commands/CALC_CHAMP.json` (generated from `upstream/code_aster/Cata/Commands/calc_champ.py:38`)
- Implementation: `upstream/code_aster/CodeCommands/calc_champ.py`; `upstream/bibfor/op/op0052.F90`,
  `upstream/bibfor/calculel/calcop.F90` (options and dependencies), `ccliop.F90`, `ccchno.F90`
  (nodal fields), `ccfnrn.F90` (`FORC_NODA`, `REAC_NODA`); option list
  `upstream/code_aster/Cata/Commons/c_nom_cham_into.py`
- Before: [MECA_STATIQUE](MECA_STATIQUE.md)
- Next steps: [POST_RELEVE_T](POST_RELEVE_T.md) (reaction sums, values on groups),
  [POST_ELEM](POST_ELEM.md), [IMPR_RESU](IMPR_RESU.md), [TEST_RESU](TEST_RESU.md)
- Example: `upstream/astest/gcpc002c.comm` (line 52)
- Example: `upstream/astest/ssll118a.comm` (lines 59, 62)
- Example: `upstream/astest/ssll101a.comm` (line 161)
- Example: `tests/fixtures/solid_static/input/run.comm` (line 40)
- Example: `tests/fixtures/shell_static/input/run.comm` (line 63)
