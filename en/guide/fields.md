---
guide: result fields
title: Result fields, locations and components
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
sources:
  - upstream/code_aster/Cata/Commons/c_nom_cham_into.py
  - upstream/catalo/cataelem/Commons/physical_quantities.py
  - upstream/catalo/cataelem/Commons/located_components.py
  - upstream/catalo/cataelem/Elements/
  - upstream/code_aster/Cata/Language/DataStructure.py
  - upstream/code_aster/Cata/Commands/meca_statique.py
  - upstream/code_aster/Cata/Commands/calc_modes.py
  - upstream/bibfor/algorith/fgequi.F90
  - upstream/bibfor/calculel/
  - upstream/bibfor/resu_util/utpar1.F90
  - tests/fixtures/
  - en/commands/CALC_CHAMP.md
  - en/guide/modelisations.md  # <!-- caen-allow: modelisation --> (file name)
doc_fr: none (our own guide, not a translation)
status: assisted
method: assisted
reviewed_by:
reviewed_on:
written_by: agent, in session (task 2.5)
---

# Result fields, locations and components

> **Assisted guide.** Our own English note, written in session from the pinned command and
> element catalogs, the solver source, and our committed fixture runs. It is not a translation
> of an official document. Claims about what the solver does cite their source. Advice on what
> to report is engineering judgement and is marked as such. Where a point should be checked
> against the official documentation, it says `TODO(verify)`. Not reviewed by an engineer.

This guide explains what code_aster stores in a result and how to read the names. It is the
label source for the English engineering report (`docs/REPORT-SPEC.md` §4) and for the Phase 4
results readers. The French names (`DEPL`, `SIEQ_NOEU`, `VMIS`) are the solver's API and are
never renamed. The English labels come from `en/glossary.yaml`, and the tables below repeat
them so that a report or an LLM can look them up in one place.

## How a result is organized

A result is built in four levels:

| Level | Example | What it is | How you select it |
|---|---|---|---|
| result object | `RESU` of type `EVOL_ELAS` | The concept a solver command returns (`MECA_STATIQUE`, `CALC_MODES`). | Its name in the command file, `RESULTAT=RESU`. |
| step | step 1 at `INST` = 0.0 | One stored state: a load step, a time, or a mode. | `NUME_ORDRE` (step index), or the access parameter: `INST` for static results, `FREQ` or `NUME_MODE` for modal results. |
| field | `SIEQ_NOEU` | One quantity at one location, over the whole model or part of it. | `NOM_CHAM` (field name). |
| component | `VMIS` | One scalar of the field. | `NOM_CMP` (component name). |

A field name has two parts, `<QUANTITY>_<LOCATION>`: `SIGM_ELNO` is the stress (`SIGM`) at the
nodes of each element (`ELNO`). The catalog that lists every field name the post-processing
commands accept, with a one-line French description, is
`upstream/code_aster/Cata/Commons/c_nom_cham_into.py`. Line numbers in this guide that are given
without a file refer to it. Three nodal fields carry no location suffix: `DEPL`, `VITE` and
`ACCE` (displacement, velocity, acceleration, `:438`, `:442`, `:436`). Two end in `_NODA`
(`FORC_NODA`, `REAC_NODA`, `:382`, `:383`): they are vectors assembled on the degrees of freedom
(DOF), not fields averaged from elements.

### Quantity prefixes

| Prefix | English (glossary) | Holds | Main components |
|---|---|---|---|
| `DEPL` | displacement | Nodal DOF values. | `DX`, `DY`, `DZ`, `DRX`, `DRY`, `DRZ` |
| `SIEF` | stress (integration-point field) | Stresses for continuum elements, forces for beams and discrete elements. | as `SIGM` or as `EFGE` |
| `SIGM` | stress | Stress tensor. | `SIXX`, `SIYY`, `SIZZ`, `SIXY`, `SIXZ`, `SIYZ` |
| `SIEQ` | equivalent stress | Von Mises, Tresca, principal stresses. | `VMIS`, `TRESCA`, `PRIN_1`..`PRIN_3`, ... |
| `EPSI` | strain | Strain tensor. | `EPXX`, `EPYY`, `EPZZ`, `EPXY`, `EPXZ`, `EPYZ` |
| `EPEQ` | equivalent strain | Equivalent and principal strains. | `INVA_2`, `PRIN_1`..`PRIN_3`, `INVA_2SG`, ... |
| `EFGE` | generalized forces | Shell and beam stress resultants. | shell `NXX`..`QY`; beam `N`..`MFZ` |
| `DEGE` | generalized strains | Shell and beam strains and curvatures. | shell `EXX`..`GAY`; beam `EPXX`..`KZ` |
| `SIPO` | beam section stresses | Stresses in a beam section from each force. | `SN`, `SVY`, `SVZ`, `SMT`, `SMFY`, `SMFZ` |
| `FORC` | force | Element forces assembled at the nodes. | DOF names `DX`..`DRZ` |
| `REAC` | reaction | Support reactions. | DOF names `DX`..`DRZ` |

### Location suffixes

| Suffix | English (glossary) | Where the values are | Continuous between elements? |
|---|---|---|---|
| `ELGA` | at Gauss points | At the integration points of each element (family `RIGI` for the stiffness, `upstream/catalo/cataelem/Commons/located_components.py:1204`). | No. |
| `ELNO` | at element nodes | At the nodes of each element, extrapolated from the Gauss points. A node shared by four elements has four values. | No: jumps between elements show where the mesh is too coarse. |
| `NOEU` | at nodes (averaged) | One value per node: the arithmetic mean of the `ELNO` values of the elements around it. | Yes, by construction. |
| `ELEM` | per element | One value per element. | No. |

The `NOEU` average is a plain arithmetic mean over the elements that share the node, with no
weighting by element size (`upstream/bibfor/calculel/cescns.F90:70`). Every `_NOEU` option is
computed from the `_ELNO` option of the same name (`en/commands/CALC_CHAMP.md`, "What the
solver does"). Three consequences for reports:

- **Averages hide peaks.** At a stress concentration the averaged `SIGM_NOEU` is lower than the
  largest `SIGM_ELNO` value at that node. Report the `ELNO` maximum next to the `NOEU` maximum
  when the peak matters (judgement; `docs/REPORT-SPEC.md` §3 item 9 asks for the averaging
  method to be stated).
- **Equivalent stresses are averaged after they are computed.** `SIEQ_NOEU` is the average of
  `SIEQ_ELNO`, not the von Mises stress of `SIGM_NOEU`. In our solid fixture the two differ by
  up to 1.7 MPa where the peak is 34.7 MPa (`en/commands/CALC_CHAMP.md`, pitfalls).
- **The average depends on the element selection.** With `CALC_CHAMP / GROUP_MA`, nodes on the
  border of the group get a one-sided value (`upstream/bibfor/calculel/ccchno.F90:138`).

Shell and beam fields with sub-points (one value per layer of a shell, `COQUE_NCOU`) cannot be
averaged at nodes. `CALC_CHAMP` warns with `UTILITAI_3` and leaves those elements out
(`upstream/bibfor/calculel/cescns.F90:133`). If no element is left, the nodal field cannot be
created and the command stops with `CALCULEL4_16` (`upstream/bibfor/calculel/ccchno.F90:190`),
which advises extracting one layer first with `POST_CHAMP` (out of our scope,
`docs/COMMAND-SET.md`). Averaging shell or beam fields that are in local axes also checks that
the axes of neighboring elements agree. If they differ, `CALC_CHAMP` warns with `UTILITAI_4`
and gives the largest angle (`upstream/bibfor/calculel/ccvrrl.F90:306`).

## Result objects

| Type | English (glossary) | Produced by | Steps | Access parameter |
|---|---|---|---|---|
| `EVOL_ELAS` | linear static result | `MECA_STATIQUE` (`upstream/code_aster/Cata/Commands/meca_statique.py:36`) | One per time of `LIST_INST`, or one at `INST` = 0. | `INST` (`upstream/bibfor/resu_util/utpar1.F90:180`) |
| `MODE_MECA` | modal result | `CALC_MODES` | One per mode (in increasing frequency in our modal fixture, `tests/fixtures/modal/output/run.mess:403`). | `FREQ`, `NUME_MODE` (`utpar1.F90:373`, `:395`) |

The Python names `ElasticResult` and `ModeResult` are what the log prints for these types:
`de type <ElasticResult>` (`tests/fixtures/solid_static/output/run.mess:305`) and
`de type <ModeResult>` (`tests/fixtures/modal/output/run.mess:430`). The catalog classes are
`evol_elas` and `mode_meca` (`upstream/code_aster/Cata/Language/DataStructure.py:594`, `:650`).
`EVOL_NOLI` (nonlinear) and `EVOL_THER` (thermal) are Tier 2 and have glossary entries; this
guide does not cover their extra fields.

### `EVOL_ELAS`: what is stored, and when

`MECA_STATIQUE` stores `DEPL` and, by default, `SIEF_ELGA` (`OPTION`, default `'SIEF_ELGA'`,
`upstream/code_aster/Cata/Commands/meca_statique.py:89`). The log records the displacement
field: `Champ stocké <DEPL> ... pour le numéro d'ordre 1`
(`tests/fixtures/solid_static/output/run.mess:303`). Every other field (`SIGM_*`, `SIEQ_*`,
`EFGE_*`, `REAC_NODA`, ...) exists only if `CALC_CHAMP` computed it, and a field computed only
as an intermediate step is not stored (`en/commands/CALC_CHAMP.md`, pitfalls). The results
reader must therefore list the fields actually present and never assume one.

### `MODE_MECA`: mode parameters

Each mode is a step whose `DEPL` field is the mode shape. `CALC_MODES` also stores these
parameters per mode (`upstream/bibfor/algeline/vpstor.F90:82`):

| Parameter | English (glossary) | Meaning |
|---|---|---|
| `NUME_MODE` | mode number | Rank of the mode. |
| `FREQ` | frequency | Natural frequency, in Hz when the model units are consistent (cycles per unit time). |
| `OMEGA2` | squared angular frequency | (2π f)². |
| `MASS_GENE`, `RIGI_GENE` | generalized mass, generalized stiffness | φᵀ M φ and φᵀ K φ for the stored, normalized mode shape φ. |
| `FACT_PARTICI_DX`, `_DY`, `_DZ` | participation factor | Participation of the mode in a rigid-body motion along X, Y or Z. |
| `MASS_EFFE_DX`, `_DY`, `_DZ` | effective modal mass | Mass that the mode moves along X, Y or Z. |
| `MASS_EFFE_UN_DX`, `_DY`, `_DZ` | effective mass fraction | `MASS_EFFE_D*` divided by the total mass in that direction. |

The mode shapes are normalized, so their amplitude has no physical meaning: in our modal
fixture the largest absolute component of every stored mode shape is exactly 1.0
(`tests/fixtures/modal/output/run.rmed`, field `MODES___DEPL`). The `CALC_MODES` catalog default
for `NORM_MODE / NORME` is `'TRAN_ROTA'`
(`upstream/code_aster/Cata/Commands/calc_modes.py:118`). TODO(verify) against U4.52.02 that
this is the normalization applied when `NORM_MODE` is not given, and how `MASS_GENE` depends on
it. A report must label mode shapes "normalized" and never print their values in length units.
TODO(verify) whether `CALC_MODES` fills the `MASS_EFFE_*` and `FACT_PARTICI_*` values without a
separate request; the modal fixture computes the total mass with `POST_ELEM / MASS_INER`
instead (`tests/fixtures/modal/output/tables/mass_inertia.csv`).

### Field names in MED files

`IMPR_RESU(FORMAT='MED')` names each field `<result name padded to 8 with _><field name>`:
`RESU____DEPL`, `RESU____SIEQ_NOEU`, `MODES___DEPL`
(`tests/fixtures/solid_static/output/run.mess:385`, `tests/fixtures/modal/output/run.mess:445`).
The component names are stored with the field. The unit attribute is blank in all three
fixture files (`tests/fixtures/solid_static/output/run.rmed` and the other two). code_aster
has no unit system of its own, so units come from the job definition (`docs/REPORT-SPEC.md` §4; `run.json` in the fixtures,
`tests/fixtures/README.md`).

## Field summary

The Tier 1 fields. "Label" is the glossary English; "Line" is the field's entry in
`upstream/code_aster/Cata/Commons/c_nom_cham_into.py`. "Option" is the `CALC_CHAMP` keyword that
computes it ("stored" means the analysis stores it itself). "Units" assume a consistent unit
system: L = length, F = force (judgement, from dimensional analysis).

| Field | Label | Option | Applies to | Units | Line |
|---|---|---|---|---|---|
| `DEPL` | displacement | stored | all | L; rad for `DR*` | 438 |
| `SIEF_ELGA` | stress at Gauss points | stored (`MECA_STATIQUE`) | all | F/L² (solids); forces (beams) | 86 |
| `SIEF_ELNO` | stress at element nodes (from SIEF) | `CONTRAINTE` | all | as `SIEF_ELGA` | 87 |
| `SIEF_NOEU` | stress (nodal average, from SIEF) | `CONTRAINTE` | all | as `SIEF_ELGA` | 95 |
| `SIGM_ELGA` | stress at Gauss points (from SIGM) | `CONTRAINTE` | solids, 2D, shells by layer | F/L² | 96 |
| `SIGM_ELNO` | stress at element nodes | `CONTRAINTE` | solids, 2D, shells by layer | F/L² | 97 |
| `SIGM_NOEU` | stress (nodal average) | `CONTRAINTE` | solids, 2D | F/L² | 98 |
| `SIEQ_ELGA` | equivalent stress at Gauss points | `CRITERES` | solids, 2D, shells by layer | F/L² | 319 |
| `SIEQ_ELNO` | equivalent stress at element nodes | `CRITERES` | solids, 2D, shells by layer | F/L² | 323 |
| `SIEQ_NOEU` | equivalent stress (nodal average) | `CRITERES` | solids, 2D | F/L² | 327 |
| `EPSI_ELGA` | strain at Gauss points | `DEFORMATION` | solids, 2D, shells by layer | dimensionless | 184 |
| `EPSI_ELNO` | strain at element nodes | `DEFORMATION` | solids, 2D, shells by layer | dimensionless | 185 |
| `EPSI_NOEU` | strain (nodal average) | `DEFORMATION` | solids, 2D | dimensionless | 186 |
| `EPEQ_ELNO` | equivalent strain at element nodes | `CRITERES` | solids, 2D, shells | dimensionless | 288 |
| `EPEQ_NOEU` | equivalent strain (nodal average) | `CRITERES` | solids, 2D | dimensionless | 292 |
| `EFGE_ELGA` | shell/beam resultants at Gauss points | `CONTRAINTE` | shells, beams | see below | 76 |
| `EFGE_ELNO` | shell/beam resultants at element nodes | `CONTRAINTE` | shells, beams | see below | 77 |
| `EFGE_NOEU` | shell/beam resultants (nodal average) | `CONTRAINTE` | shells, beams | see below | 85 |
| `DEGE_ELNO` | shell/beam generalized strains at element nodes | `DEFORMATION` | shells, beams | 1 or 1/L | 122 |
| `SIPO_ELNO` | beam section stresses at element nodes | `CONTRAINTE` | beams | F/L² | 103 |
| `EPOT_ELEM` | strain energy per element | `ENERGIE` | all | F·L | 244 |
| `FORC_NODA` | nodal forces | `FORCE` | all | F; F·L for `DR*` | 382 |
| `REAC_NODA` | nodal reactions | `FORCE` | all | F; F·L for `DR*` | 383 |

Which family applies to which modeling type is decided by the element catalog: an option the
elements of the model cannot compute ends with `CALCCHAMP_89`, whose text gives `EFGE_ELNO` on
`3D` elements as its example (`en/commands/CALC_CHAMP.md`, pitfalls). See
[Modeling types](modelisations.md) for the main stress output of each modeling type.

## Displacement: `DEPL`

**Components.** `DX`, `DY`, `DZ` are translations along the global X, Y and Z axes, and `DRX`,
`DRY`, `DRZ` rotations about them, in the global axes ("repere global",
`upstream/catalo/cataelem/Commons/physical_quantities.py:857`). A node carries only the DOFs of
its elements: solid nodes have `DX`, `DY`, `DZ` (`tests/fixtures/solid_static/output/run.rmed`),
shell nodes all six (`tests/fixtures/shell_static/output/run.rmed`), and 2D nodes `DX`, `DY`
([Modeling types](modelisations.md)). Rotations are in radians.

**Report labels** (`docs/REPORT-SPEC.md` §4): "Displacement, X" for `DEPL/DX`, "Rotation about
X" for `DEPL/DRX`. The magnitude sqrt(DX² + DY² + DZ²) is not a solver component; a report may
compute it (REPORT-SPEC §1 allows extrema and simple arithmetic) and must label it
"Displacement magnitude".

**Pitfall.** In `AXIS`, `DX` is the radial and `DY` the axial displacement
([Modeling types](modelisations.md#axis--axisymmetric)). In a `MODE_MECA`, `DEPL` is a
normalized mode shape (see above).

## Stress: `SIEF_*` and `SIGM_*`

**`SIEF_ELGA` is the raw output.** It is the field the analysis itself stores, and the other
stress options are computed from it (`en/commands/CALC_CHAMP.md`, "What the solver does"). Its
content depends on the element: the stress tensor for solids and 2D elements
(`upstream/catalo/cataelem/Elements/meca_3d.py:1322`), the stress per layer for shells
(`upstream/catalo/cataelem/Elements/meca_dkt.py:935`), and the forces `N`, `VY`, `VZ`, `MT`,
`MFY`, `MFZ` for beams (`upstream/catalo/cataelem/Elements/meca_pou_d_t.py:196`). That is why
its label says "stress" but beam values are forces: label each component, not only the field.

**`SIGM_*` holds stresses only.** Components:

| Component | Label (glossary) | Meaning |
|---|---|---|
| `SIXX` | normal stress XX | σxx |
| `SIYY` | normal stress YY | σyy |
| `SIZZ` | normal stress ZZ | σzz |
| `SIXY` | shear stress XY | σxy |
| `SIXZ` | shear stress XZ | σxz (3D only) |
| `SIYZ` | shear stress YZ | σyz (3D only) |

Source: `upstream/catalo/cataelem/Commons/physical_quantities.py:3492`
("sigma_xx contraintes dans un milieu continu"); solids carry six components
(`upstream/catalo/cataelem/Commons/located_components.py:882`), 2D elements four, `SIXX`,
`SIYY`, `SIZZ`, `SIXY` (`located_components.py:892`). The axes are the global axes for solids
and 2D elements. TODO(verify) against U4.81.04 that `SIGM_*` on shell elements is given in the
local axes of the element, as `EFGE_ELNO` is.

**Shells.** `SIGM_ELNO` and `SIEQ_ELNO` on `DKT`, `DST` and `COQUE_3D` elements have one value
per layer level: `POST_CHAMP / EXTR_COQUE` selects a layer and a level `'INF'`, `'MOY'` or
`'SUP'` (lower, middle, upper face; `upstream/code_aster/Cata/Commands/post_champ.py:125`).
The element normal decides which face is the upper one
([Modeling types](modelisations.md#shells-dkt-dst-coque_3d)). Their `_NOEU` versions cannot be
built (see [Location suffixes](#location-suffixes)). Until `POST_CHAMP` is in scope, ClearFEA
should report shell results from `EFGE_*` (judgement).

**Beams** have no `SIGM_*` field (catalog attribute `SIGM` = `NON`,
[Modeling types](modelisations.md#beams-pou_d_t-and-pou_d_e)). Their stresses are in `SIPO_ELNO`.

## Equivalent stress: `SIEQ_*`

Computed by `CALC_CHAMP / CRITERES` from the stress tensor at each point, by
`upstream/bibfor/algorith/fgequi.F90`. The 17 components are the same for every element that
has them (`upstream/catalo/cataelem/Commons/located_components.py:914`):

| Component | Label (glossary) | Definition (fgequi.F90 line) |
|---|---|---|
| `VMIS` | von Mises | sqrt(3/2 s:s), s = deviatoric stress (`:161`, `upstream/bibfor/utilifor/lciv2s.F90`) |
| `TRESCA` | Tresca | largest difference between two principal stresses (`:175`) |
| `PRIN_1`, `PRIN_2`, `PRIN_3` | 1st principal, 2nd principal, 3rd principal | principal stresses, signed, in increasing order: `PRIN_1` ≤ `PRIN_2` ≤ `PRIN_3` (`:170`; sort order at `upstream/bibfor/algeline/vpordo.F90:24`) |
| `VMIS_SG` | signed von Mises | `VMIS` with the sign of the trace: negative when the mean stress is compressive (`:180`) |
| `VECT_1_X` .. `VECT_3_Z` | (principal directions) | X, Y, Z components of the unit vector of each principal stress, `VECT_1_*` for `PRIN_1` (`physical_quantities.py:3545`) |
| `TRSIG` | stress trace | σxx + σyy + σzz (`:194`) |
| `TRIAX` | stress triaxiality | mean stress over von Mises, (trace / 3) / `VMIS`; 0 where `VMIS` is near zero (`:199`) |

`PRIN_3` is the largest principal stress, so the maximum tensile stress is `PRIN_3` and the
maximum compressive stress is `PRIN_1`. Our solid fixture's `SIEQ_NOEU` satisfies this order at
all 4,622 nodes (`en/commands/CALC_CHAMP.md`).

**Report labels** (`docs/REPORT-SPEC.md` §4): "von Mises stress (nodal average)" for
`SIEQ_NOEU/VMIS`; "von Mises stress at element nodes" for `SIEQ_ELNO/VMIS`; "Maximum principal
stress" for `PRIN_3` and "Minimum principal stress" for `PRIN_1`, stating which field they come
from.

## Strain: `EPSI_*` and `EPEQ_*`

**`EPSI_*` components** (`upstream/catalo/cataelem/Commons/physical_quantities.py:1279`):

| Component | Label (glossary) | Meaning |
|---|---|---|
| `EPXX`, `EPYY`, `EPZZ` | normal strain XX, YY, ZZ | εxx, εyy, εzz |
| `EPXY`, `EPXZ`, `EPYZ` | shear strain XY, XZ, YZ (tensor) | εxy, εxz, εyz: **tensor** components, half the engineering shear strain γ |

The shear components are halved after the strain is computed from the displacements
(`upstream/bibfor/elements/eps1mc.F90:96`). For `3D` elements the chain is option `EPSI_ELGA`
(`upstream/catalo/cataelem/Elements/meca_3d.py:697`) → `upstream/bibfor/te/te0025.F90:88` →
`upstream/bibfor/elements/epsvmc.F90:105`; the same routine serves the other isoparametric
elements (TODO(verify) element by element). A strain
gauge rosette or a textbook that uses γxy will read twice `EPXY`. TODO(verify) the convention for
shell layer strains.

**`EPEQ_*` components** (`upstream/catalo/cataelem/Commons/located_components.py:957`):
`INVA_2` (equivalent strain, sqrt(2/3 e:e) with e the deviatoric strain,
`upstream/bibfor/utilifor/lciv2e.F90`), `PRIN_1`..`PRIN_3` (principal strains, increasing),
`INVA_2SG` (`INVA_2` with the sign of the volume change) and `VECT_*` (principal directions)
(`upstream/bibfor/algorith/fgequi.F90:128`). `PRIN_1` is the same identifier in `SIEQ_*` and
`EPEQ_*`; its glossary label "1st principal" fits both, and the field name says which.

## Shell and beam resultants: `EFGE_*`, `DEGE_*`, `SIPO_*`

**Shells** (`DKT`, `DST`, `COQUE_3D`; `upstream/catalo/cataelem/Elements/meca_dkt.py:164`):

| Component | Label (glossary) | Meaning | Units |
|---|---|---|---|
| `NXX`, `NYY` | membrane force XX, YY | normal membrane force per unit length | F/L |
| `NXY` | membrane shear force XY | in-plane shear force per unit length | F/L |
| `MXX`, `MYY` | bending moment XX, YY | bending moment per unit length | F·L/L |
| `MXY` | twisting moment XY | twisting moment per unit length | F·L/L |
| `QX`, `QY` | transverse shear force X, Y | out-of-plane shear force per unit length | F/L |

The values are per unit length of the shell mid-surface: our shell fixture's center moment
`MXX` = −479.645 N·mm/mm matches the Navier plate value −478.864 N·mm/mm
(`tests/fixtures/README.md`). They are in the local axes of each element
(«dans le repère local», `upstream/code_aster/Cata/Commons/c_nom_cham_into.py:79`); the local x
axis comes from `AFFE_CARA_ELEM / COQUE / ANGL_REP` or `VECTEUR`
([Modeling types](modelisations.md#shells-dkt-dst-coque_3d)). `EGRU_ELNO` gives the same forces
in a user-defined coordinate system (`:81`). Signs: under the fixture's pressure, which acts downward
(`tests/fixtures/shell_static/input/run.comm:52`), the plate's sagging moment `MXX` is negative
(`tests/fixtures/README.md`); the sign depends on the shell normal. TODO(verify) the general sign convention for `MXX` against
U4.81.04 before ClearFEA prints "tension on the upper face" or similar.

**Beams** (`POU_D_T`, `POU_D_E`; `upstream/catalo/cataelem/Elements/meca_pou_d_t.py:201`):

| Component | Label (glossary) | Meaning (`physical_quantities.py` line) | Units |
|---|---|---|---|
| `N` | axial force | «effort normal» (`:3498`) | F |
| `VY`, `VZ` | shear force Y, Z | shear force along local y, z (`:3499`) | F |
| `MT` | torsional moment | moment about the beam axis (`:3501`) | F·L |
| `MFY`, `MFZ` | bending moment Y, Z | bending moment about local y, z (`:3502`) | F·L |

Beam forces are in the local axes of the element: x along the beam, y and z from
`AFFE_CARA_ELEM / ORIENTATION` ([Modeling types](modelisations.md#beams-pou_d_t-and-pou_d_e)).
TODO(verify) the sign convention (force exerted on the element by the part after or before the
section) against U4.81.04.

**Generalized strains `DEGE_*`.** Shells: membrane strains `EXX`, `EYY`, `EXY`, curvatures
`KXX`, `KYY`, `KXY`, shear strains `GAX`, `GAY` (`meca_dkt.py:112`). Beams: `EPXX` (axial
strain), `GAXY`, `GAXZ` (shear strains), `GAT` (twist), `KY`, `KZ` (curvatures)
(`meca_pou_d_t.py:144`). Curvatures are in 1/L.

**Beam section stresses `SIPO_ELNO`.** `SN`, `SVY`, `SVZ`, `SMT`, `SMFY`, `SMFZ`: the stress in
the section due to each of `N`, `VY`, `VZ`, `MT`, `MFY`, `MFZ`
(`upstream/catalo/cataelem/Commons/located_components.py:1056`; meanings at
`physical_quantities.py:3530`). They are not combined: the largest fiber stress is not one of
them. TODO(verify) against U4.81.04 at which point of the section each is evaluated.

## Nodal forces and reactions: `FORC_NODA`, `REAC_NODA`

**Components** are the DOF names: `DX`, `DY`, `DZ` hold forces along X, Y, Z and `DRX`, `DRY`,
`DRZ` moments about them, in the global axes. The fixtures show the same names as `DEPL`:
`DX`, `DY`, `DZ` in `solid_static`, `DX` to `DRZ` in `shell_static`
(`tests/fixtures/solid_static/output/run.rmed`, `tests/fixtures/shell_static/output/run.rmed`, field `RESU____REAC_NODA`). A report must label them as
forces ("Reaction force, X", "Reaction moment about X"), never as displacements.

**Definitions.** `FORC_NODA` is the element internal forces assembled at the nodes.
`REAC_NODA` is `FORC_NODA` minus the applied loads, computed node by node
(`upstream/bibfor/calculel/ccfnrn.F90:715`). It is non-zero only where a DOF is imposed.
For a `MODE_MECA` result the inertia term is also involved (`upstream/bibfor/calculel/ccfnrn.F90:748`, with `OMEGA2`).

**Sign.** `REAC_NODA` is the force the support exerts on the structure. The sum of the
reactions balances the applied load and so has the opposite sign: +X in `solid_static`, where
the net pressure load points along −X, and +Z in `shell_static` (`tests/fixtures/README.md`).
The sum is checked with `TEST_RESU / TYPE_TEST='SOMM'`
(`tests/fixtures/solid_static/input/run.comm:78`).

**Pitfall.** In `AXIS`, nodal forces are per radian of circumference; multiply a reaction sum
by 2π for the full ring ([Modeling types](modelisations.md#axis--axisymmetric)).

## Energy: `EPOT_ELEM`

The elastic strain energy of each element, one value per element (`:244`). The component is
`TOTALE` (total) for solid elements (`upstream/catalo/cataelem/Commons/located_components.py:181`).
Shell elements add the split into `MEMBRANE`, `FLEXION`, `CISAILLE` and `COUPL_MF` (membrane,
bending, shear, membrane-bending coupling; `upstream/catalo/cataelem/Elements/meca_dkt.py:53`)
and beams into `TRAC_COM`, `TORSION`, `FLEX_Y`, `FLEX_Z`
(`upstream/catalo/cataelem/Elements/meca_pou_d_t.py:129`). Units F·L.

## What ClearFEA should report by default

Engineering judgement for task 4.6, following `docs/REPORT-SPEC.md` §3; the solver does not
choose this.

| Analysis | Fields to request in `CALC_CHAMP` | What the report shows |
|---|---|---|
| solid or 2D static | `SIGM_ELNO`, `SIGM_NOEU`, `SIEQ_ELNO`, `SIEQ_NOEU`, `REAC_NODA` | max displacement magnitude; max `VMIS` from `SIEQ_NOEU` and from `SIEQ_ELNO`; `PRIN_3` max and `PRIN_1` min; reaction sums per support group |
| shell static | `EFGE_ELNO`, `EFGE_NOEU`, `REAC_NODA` | max \|`DZ`\| (or magnitude); extreme `NXX`, `NYY`, `MXX`, `MYY`, `QX`, `QY` from `EFGE_NOEU`, stated "per unit length, element local axes"; reaction sums |
| beam static | `EFGE_ELNO`, `REAC_NODA` | extreme `N`, `VY`, `VZ`, `MT`, `MFY`, `MFZ` per member, local axes; reaction sums |
| modal | none required | table of `NUME_MODE`, `FREQ`, and the effective mass fractions when present; mode shapes labeled "normalized" |

The solid line is what our `solid_static` fixture computes
(`tests/fixtures/solid_static/input/run.comm:40`), and the shell line what `shell_static`
computes (`tests/fixtures/shell_static/input/run.comm:63`).

## See also

- [CALC_CHAMP](../commands/CALC_CHAMP.md): the options, their dependencies and pitfalls.
- [Modeling types](modelisations.md): which modeling type gives which field family.
- [POST_RELEVE_T](../commands/POST_RELEVE_T.md) and [IMPR_RESU](../commands/IMPR_RESU.md):
  extracting and writing fields.
- `docs/REPORT-SPEC.md`: how the report uses these labels.
- Field catalog: `upstream/code_aster/Cata/Commons/c_nom_cham_into.py`; component catalog:
  `upstream/catalo/cataelem/Commons/physical_quantities.py`.
