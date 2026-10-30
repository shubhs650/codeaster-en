---
command: AFFE_CHAR_MECA
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/affe_char_meca.py:50
doc_fr: U4.44.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3c)
examples: [ssls147a, sslv114a, ssll106a, hsns102a, sdnv108a, ssnv147l, ssls111a, zzzz238a, ssnp154e, ssnv142d, zzzz144a, ssnv106a, sslv200a]
---

# AFFE_CHAR_MECA — assign mechanical loads and BCs

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

`AFFE_CHAR_MECA` builds a mechanical load (`char_meca`) on a model: forces (pressure, surface,
edge and nodal forces, gravity, rotation) and boundary conditions (imposed DOFs and linear
relations between DOFs: rigid links, ties between meshes, equal-DOF couplings). All values are
constants; `AFFE_CHAR_MECA_F` takes functions instead (see [DEFI_FONCTION](DEFI_FONCTION.md)).
It needs only the model. The analysis (`MECA_STATIQUE` and the others) takes one or more loads
in `EXCIT`, can scale each by a function of time (`FONC_MULT`), and sums them. A load can hold
both kinds; the Python layer splits its keywords into Neumann loads (forces) and Dirichlet
loads (conditions) (`upstream/code_aster/CodeCommands/affe_char_meca.py:33`). The conditions
are enforced with Lagrange multipliers: each imposed DOF or relation adds unknowns to the
system (`DOUBLE_LAGRANGE`); `AFFE_CHAR_CINE` imposes plain DOF values by elimination instead.
The decisions it encodes are the supports, the couplings and the loads of one load case, or a
part of it. Our three fixtures each use two calls, one for the supports and one for the load
(`tests/fixtures/solid_static/input/run.comm:29`), so that the analysis lists them separately
in `EXCIT`.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Affectation de charges et conditions aux limites mécaniques constantes» |
| Kind | `OPER` |
| Result | `char_meca` |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.44.01 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `DDL_IMPO`, `FACE_IMPO`, `PRES_REP`, `FORCE_FACE`, `FORCE_NODALE`, `FORCE_ARETE`, `PESANTEUR`, `ROTATION`, `LIAISON_DDL`, `LIAISON_UNIF`, `LIAISON_SOLIDE`, `LIAISON_MAIL`, `LIAISON_RBE3`, `GROUP_NO_MAIT`, `GROUP_NO_ESCL`, `DDL_MAIT`, `COEF_ESCL`, `GROUP_MA_MAIT`, `GROUP_MA_ESCL`, `TYPE_RACCORD`, `FONC_MULT` |

`LIAISON_MAIL` and `LIAISON_RBE3` are Tier 2 in COMMAND-SET (bonded assemblies, remote
loads). `FONC_MULT` is a keyword of the analysis (`MECA_STATIQUE/EXCIT`), not of this command.

## What the solver does with it

In order (`upstream/bibfor/load/charme.F90`): it reads the forces (`cbpres` for `PRES_REP` at
line 174, then gravity, rotation, nodal, face and edge forces), then the conditions (`caddli`
for `DDL_IMPO` at line 248, then `FACE_IMPO` and the `LIAISON_*` keywords). It then checks the
normals of the faces that carry `PRES_REP`, `FACE_IMPO` and `EFFE_FOND` (`chveno`, line 348;
switch: `VERI_NORM`) and checks that every assigned value means something to the element it is
on (`verif_affe`, line 352; switch: `VERI_AFFE`). The order of the keywords in the call does
not matter.

Signs and directions:

- **Forces** (`FORCE_NODALE`, `FORCE_FACE`, `FORCE_ARETE`) are given by global components;
  a positive `FZ` acts along +Z.
- **Pressure** (`PRES_REP/PRES`) acts along the normal: a positive pressure pushes against the
  element normal. On the boundary faces of a solid, whose normals point outward, it pushes
  into the solid. This is the convention of our `solid_static` fixture, where the hand value of
  the pressure resultant (`tests/fixtures/hand_values.py:97`) matches the solver's base
  reactions. On a shell it pushes against the shell normal (`tests/fixtures/shell_static/input/run.comm:52`,
  confirmed by the sagging moment of the run).
- **Imposed DOFs** (`DX`, ..., `DRZ`) are in the global axes, in the length unit of the mesh
  and radians.

## Keywords

The DOF names are the components of the displacement quantity `DEPL_R`; their meanings come
from the catalog comment of that quantity (`upstream/catalo/cataelem/Commons/physical_quantities.py:856`).
A component exists only on nodes whose elements carry it: solid (`3D`) nodes have `DX`, `DY`,
`DZ`; shell nodes (`DKT`, `COQUE_3D`) also have `DRX`, `DRY`, `DRZ`.

Top-level simple keywords and the key factor keywords from docs/COMMAND-SET.md are expanded
below; the other factor keywords are listed under [Other keywords](#other-keywords).

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `VERI_AFFE` | text, optional | `'OUI'` | *assignment check*. One of `'OUI'`, `'NON'`. Check that the values assigned to elements mean something for those elements; for example a pressure given on a group of volume elements, which do not carry pressure. With `'OUI'` such an assignment gives warning `CALCULEL_40`, which lists the first elements concerned and their groups (`upstream/bibfor/calculel/verif_affe_carte.F90:318`). Keep the default; the warning usually points at a wrong group name. |
| `VERI_NORM` | text, optional | `'OUI'` | *normal check*. One of `'OUI'`, `'NON'`. Check the normals of the faces under `PRES_REP`, `FACE_IMPO` (when it uses `PRES`, `DNOR` or `DTAN`) and `EFFE_FOND` (`upstream/bibfor/modelisa/chveno.F90:83`). On the boundary faces of a solid, every face normal must point outward: each badly oriented group gives `MODELISA8_56` (with the number of faces) and the command then stops with `MODELISA4_24`. On shells, all elements of a group must be oriented like the first one. Keep `'OUI'`: it is what makes a reversed pressure a stop instead of a wrong result. Set `'NON'` only when a group is legitimately not connected and the check stops on `MESH3_99`, as that message advises. |
| `MODELE` | `modele_sdaster`, required | — | *model*. The model the load is built on. Every group used below must be in its mesh; faces that carry `PRES_REP` or `FORCE_FACE` must have elements in the model (our `solid_static` fixture assigns the model with `TOUT='OUI'` for this reason, `tests/fixtures/solid_static/input/run.comm:22`). |
| `CARA_ELEM` | `cara_elem`, optional | — | *element properties*. Read only for `FORCE_COQUE_FO`, to get the shell thickness (`upstream/bibfor/load/char_eval_fonc.F90:158`); not needed in Tier 1. |
| `CHAM_MATER` | `cham_mater`, optional | — | *material field*. Read only for `FORCE_COQUE_FO`, to get the density (`upstream/bibfor/load/char_eval_fonc.F90:176`); not needed in Tier 1. Gravity and rotation take the density from the analysis's `CHAM_MATER`, not from here. |
| `EVOL_CHAR` | `evol_char`, optional | — | A pressure field from another calculation (catalog translation): a result of type `evol_char`, typically read from a file. Out of Tier 1 scope. |
| `DOUBLE_LAGRANGE` | text, optional | `'OUI'` | *double Lagrange multipliers*. One of `'OUI'`, `'NON'`. How many Lagrange multipliers each condition gets: two (the default) or one (`'NON'` marks the load `LAG1`, `upstream/bibfor/load/charme.F90:340`). Two multipliers let solvers that do not pivot factorize the matrix; one multiplier makes the problem smaller but works only with `MUMPS` and `PETSC` (U4.44.01 §4.2; `upstream/astest/petsc05a.comm:61`). Keep the default. |
| `PESANTEUR` | factor keyword, optional | — | *gravity*. Gravity field (catalog translation). A body force RHO × `GRAVITE` × unit(`DIRECTION`) on every element (`upstream/bibfor/te/te0015.F90:81`); the material must give `RHO` (`DEFI_MATERIAU/ELAS`). One occurrence only. |
| `PESANTEUR / GROUP_MA` | element group, optional, list | — | *element group*. Restrict gravity to these elements; without it, the whole model. |
| `PESANTEUR / GRAVITE` | real, required | — | *gravitational acceleration*. The magnitude g, in the units of the model: 9.81 with m and s (`upstream/astest/hsns102a.comm:163`), 9810 with mm and s. |
| `PESANTEUR / DIRECTION` | real, required, list of up to 3, at least 3 | — | *direction*. The direction of g in global axes; it is normalized, so (0, 0, −1) and (0, 0, −9.81) are the same (`upstream/bibfor/load/capesa.F90:84`). A zero vector stops the command (`CHARGES2_53`). |
| `ROTATION` | factor keyword, optional | — | *rotation (centrifugal load)*. Defines a rotation load (catalog translation): the centrifugal body force of a steady rotation, RHO × ω² × (distance from the axis), directed away from the axis (`upstream/bibfor/te/te0014.F90:102`). The material must give `RHO`. One occurrence only. |
| `ROTATION / GROUP_MA` | element group, optional, list | — | *element group*. Restrict the load to these elements; without it, the whole model. |
| `ROTATION / SANS_GROUP_MA` | element group, optional, list | — | *excluded element groups*. Elements to leave out. |
| `ROTATION / VITESSE` | real, required | — | *rotational speed*. The angular speed ω in radians per unit of time: the element routine squares it directly (`upstream/bibfor/te/te0014.F90:102`). Convert from rpm with ω = rpm × π / 30 (`upstream/astest/sdnv108a.comm:43`). |
| `ROTATION / AXE` | real, required, list of up to 3, at least 2 | — | The direction of the rotation axis in global axes; normalized by the command, must not be zero (`CHARGES2_53`, `upstream/bibfor/load/carota.F90:100`). |
| `ROTATION / CENTRE` | real, optional, list of up to 3, at least 2 | — | A point on the rotation axis. Default: the origin (`upstream/bibfor/load/char_read_vect.F90:52`). |
| `DDL_IMPO` | factor keyword, optional, repeatable | — | *imposed DOF*. Imposes one or more values of displacement (or of some associated quantities) on nodes (catalog translation). The usual supports: each given component of each selected node is set to the value, by a Lagrange multiplier. Repeat it for each support. A node and DOF given twice in one load keeps one relation, the last (`upstream/bibfor/modelisa/ordlrl.F90:59`; listed under `CHARGES2_34` with `INFO=2`). The comparison looks at the nodes, DOFs and coefficients, not at the imposed value, so the last value wins (`ordlrl.F90:381`–`:413`; the overloading rule of U4.44.01 §3.8). |
| `DDL_IMPO / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Every node of the mesh. |
| `DDL_IMPO / GROUP_NO` | node group, optional, list | — | *node group*. These nodes: points and node sets (`tests/fixtures/shell_static/input/run.comm:47`). |
| `DDL_IMPO / GROUP_MA` | element group, optional, list | — | *element group*. The nodes of these elements: the usual way to fix a face or an edge (`tests/fixtures/solid_static/input/run.comm:29`). |
| `DDL_IMPO / SANS_GROUP_MA` | element group, optional, list | — | *excluded element groups*. Leave out the nodes of these elements. |
| `DDL_IMPO / SANS_GROUP_NO` | node group, optional, list | — | *excluded node groups*. Leave out these nodes, for example a corner already held by another occurrence. |
| `DDL_IMPO / BLOCAGE` | text, optional, list of up to 3 | — | *DOF family lock*. One of `'DEPLACEMENT'`, `'ROTATION'`, `'TUYAU_FOURIER'`. Set a family of DOFs to zero on every node that carries it: `'DEPLACEMENT'` = `DX`, `DY`, `DZ`; `'ROTATION'` = `DRX`, `DRY`, `DRZ`; `'TUYAU_FOURIER'` = the pipe-element DOFs (`upstream/bibfor/load/caddli.F90:198`; value 0, `upstream/bibfor/load/char_impo_bloc.F90:82`). Unlike explicit components, a DOF missing on a node is just skipped, so `BLOCAGE=('DEPLACEMENT', 'ROTATION')` clamps a mixed solid and shell support in one occurrence. It replaces the removed `LIAISON='ENCASTRE'` (`upstream/code_aster/Cata/Commands/affe_char_meca.py:28`). |
| `DDL_IMPO / DX` | real, optional | — | Displacement along global X imposed on every selected node, in the length unit of the mesh. `DX=0.0` fixes the node in X. |
| `DDL_IMPO / DY` | real, optional | — | Displacement along global Y. |
| `DDL_IMPO / DZ` | real, optional | — | Displacement along global Z. |
| `DDL_IMPO / DRX` | real, optional | — | Rotation about global X, in radians. Exists only on nodes with rotational DOFs (shells, beams, discrete `DIS_TR`). |
| `DDL_IMPO / DRY` | real, optional | — | Rotation about global Y, in radians. |
| `DDL_IMPO / DRZ` | real, optional | — | Rotation about global Z, in radians. |
| `DDL_IMPO / GRX` | real, optional | — | Warping of the `POU_D_TG` beam (U4.44.01 §5.1). Not used in Tier 1. |
| `DDL_IMPO / DRGX` | real, optional | — | Rotation of the grids of the fuel-assembly beam element, about X (catalog comment). Out of scope. |
| `DDL_IMPO / DRGY` | real, optional | — | Same, about Y. Out of scope. |
| `DDL_IMPO / DRGZ` | real, optional | — | Same, about Z. Out of scope. |
| `DDL_IMPO / PRES` | real, optional | — | A pressure DOF: acoustic pressure of `3D_FLUIDE` (u–p–φ and u–p formulations), pore pressure of `3D_JOINT_CT`, or the Lagrange multiplier of the second-gradient mixed formulation (U4.44.01 §5.1). Not used in Tier 1. Not the `PRES_REP` load. |
| `DDL_IMPO / PSI` | real, optional | — | Fluid velocity potential (catalog comment). Out of scope. |
| `DDL_IMPO / PHI` | real, optional | — | Depending on the modeling, a fluid displacement potential, a crack angle or a shear angle of the `PLAQ_MITC` plate (catalog comment). Out of scope. |
| `DDL_IMPO / TEMP` | real, optional | — | *temperature*. A temperature DOF of the mechanical quantity (catalog comment «DDL de temperature»), carried by coupled modelings such as THM. Not a thermal load: a temperature field acting on the structure goes in `AFFE_MATERIAU/AFFE_VARC`. |
| `DDL_IMPO / PRE1` | real, optional | — | First pressure DOF of coupled hydro-mechanical (THM) modelings (catalog comment: «DDL de pression»). Out of scope. |
| `DDL_IMPO / PRE2` | real, optional | — | Second pressure DOF of THM modelings. Out of scope. |
| `DDL_IMPO / GONF` | real, optional | — | Swelling DOF of the incompressible (`_INCO_UPG`) and second-gradient formulations (U4.44.01 §5.1). Out of scope. |
| `DDL_IMPO / GLIS` | real, optional | — | Relative tangential displacement (slip), in a local basis (catalog comment). Out of scope. |
| `DDL_IMPO / LH1` | real, optional | — | Lagrange multiplier of the pressure across a crack in HM-XFEM (catalog comment). Out of scope. |
| `DDL_IMPO / LAG_GV` | real, optional | — | A Lagrange multiplier of some formulations (catalog comment: «méthode plaq_mitc»). Out of scope. |
| `DDL_IMPO / UI2`, `DDL_IMPO / UI3`, `DDL_IMPO / UI4`, `DDL_IMPO / UI5`, `DDL_IMPO / UI6`, `DDL_IMPO / UO2`, `DDL_IMPO / UO3`, `DDL_IMPO / UO4`, `DDL_IMPO / UO5`, `DDL_IMPO / UO6`, `DDL_IMPO / VI2`, `DDL_IMPO / VI3`, `DDL_IMPO / VI4`, `DDL_IMPO / VI5`, `DDL_IMPO / VI6`, `DDL_IMPO / VO2`, `DDL_IMPO / VO3`, `DDL_IMPO / VO4`, `DDL_IMPO / VO5`, `DDL_IMPO / VO6`, `DDL_IMPO / WI2`, `DDL_IMPO / WI3`, `DDL_IMPO / WI4`, `DDL_IMPO / WI5`, `DDL_IMPO / WI6`, `DDL_IMPO / WO2`, `DDL_IMPO / WO3`, `DDL_IMPO / WO4`, `DDL_IMPO / WO5`, `DDL_IMPO / WO6`, `DDL_IMPO / WO`, `DDL_IMPO / WI1`, `DDL_IMPO / WO1` | real, optional | — | DOFs of the pipe elements (`TUYAU_*` modelings, catalog comment «DDL des elements de tube»): the Fourier terms of the cross-section deformation. `BLOCAGE='TUYAU_FOURIER'` sets them all to zero. Out of scope. |
| `DDL_IMPO / H1X`, `DDL_IMPO / H1Y`, `DDL_IMPO / H1Z`, `DDL_IMPO / H1PRE1`, `DDL_IMPO / H2X`, `DDL_IMPO / H2Y`, `DDL_IMPO / H2Z`, `DDL_IMPO / H2PRE1`, `DDL_IMPO / H3X`, `DDL_IMPO / H3Y`, `DDL_IMPO / H3Z`, `DDL_IMPO / H3PRE1`, `DDL_IMPO / H4X`, `DDL_IMPO / H4Y`, `DDL_IMPO / H4Z`, `DDL_IMPO / K1`, `DDL_IMPO / K2`, `DDL_IMPO / K3`, `DDL_IMPO / PRE_FLU`, `DDL_IMPO / LAG_FLI`, `DDL_IMPO / LAG_FLS`, `DDL_IMPO / PR2_FLU`, `DDL_IMPO / LA2_FLI`, `DDL_IMPO / LA2_FLS`, `DDL_IMPO / PR3_FLU`, `DDL_IMPO / LA3_FLI`, `DDL_IMPO / LA3_FLS`, `DDL_IMPO / LAGS_C`, `DDL_IMPO / LAGS_F1`, `DDL_IMPO / LAGS_F2`, `DDL_IMPO / LAG2_C`, `DDL_IMPO / LAG2_F1`, `DDL_IMPO / LAG2_F2`, `DDL_IMPO / LAG3_C`, `DDL_IMPO / LAG3_F1`, `DDL_IMPO / LAG3_F2`, `DDL_IMPO / LAG4_C`, `DDL_IMPO / LAG4_F1`, `DDL_IMPO / LAG4_F2` | real, optional | — | XFEM DOFs (catalog comment): Heaviside enrichment (`H*`), crack-tip enrichment (`K*`), fluid pressure and flux in the crack for HM-XFEM (`PR*_FLU`, `LA*_FL*`), and contact multipliers (`LAG*_C`, `LAG*_F*`). Out of scope (XFEM). |
| `DDL_IMPO / V11`, `DDL_IMPO / V12`, `DDL_IMPO / V13`, `DDL_IMPO / V21`, `DDL_IMPO / V22`, `DDL_IMPO / V23`, `DDL_IMPO / V31`, `DDL_IMPO / V32`, `DDL_IMPO / V33`, `DDL_IMPO / PRES11`, `DDL_IMPO / PRES12`, `DDL_IMPO / PRES13`, `DDL_IMPO / PRES21`, `DDL_IMPO / PRES22`, `DDL_IMPO / PRES23`, `DDL_IMPO / PRES31`, `DDL_IMPO / PRES32`, `DDL_IMPO / PRES33` | real, optional | — | DOFs of the mixed second-gradient modeling: `Vij` = ∂ui/∂xj, `PRESij` the multiplier that enforces it (catalog comment). Out of scope. |
| `FACE_IMPO` | factor keyword, optional, repeatable | — | *imposed DOF on faces*. Imposes one or more values of displacement (or of some associated quantities) on all the nodes of a face (catalog translation). With `DX` ... `DRZ` it acts like `DDL_IMPO` on the nodes of the face elements. Its own use is the normal and tangential components (`DNOR`, `DTAN`, `DRNOR`), computed from the face normals at each node (`upstream/bibfor/load/cafaci.F90:221`): a symmetry plane or a sliding support on a face that is not parallel to a global plane. |
| `FACE_IMPO / GROUP_MA` | element group, optional, list | — | *element group*. The face (3D) or edge (2D) elements. |
| `FACE_IMPO / SANS_GROUP_MA` | element group, optional, list | — | *excluded element groups*. Leave out the nodes of these elements. |
| `FACE_IMPO / SANS_GROUP_NO` | node group, optional, list | — | *excluded node groups*. Leave out these nodes. |
| `FACE_IMPO / DX` | real, optional | — | Displacement along global X on every node of the faces. |
| `FACE_IMPO / DY` | real, optional | — | Displacement along global Y. |
| `FACE_IMPO / DZ` | real, optional | — | Displacement along global Z. |
| `FACE_IMPO / DRX` | real, optional | — | Rotation about global X, in radians. |
| `FACE_IMPO / DRY` | real, optional | — | Rotation about global Y. |
| `FACE_IMPO / DRZ` | real, optional | — | Rotation about global Z. |
| `FACE_IMPO / DNOR` | real, optional | — | Displacement along the normal to the face at each node: the relation n · u = `DNOR`. `DNOR=0.0` is a symmetry or frictionless-support condition on any plane (`upstream/astest/sslv130f.comm:494`). A non-zero value imposes a normal displacement, in the direction of the face normal, which must point outward (checked when the value is not zero, `upstream/bibfor/modelisa/chveno.F90:119`). |
| `FACE_IMPO / DRNOR` | real, optional | — | Rotation about the normal to the face, in radians; 3D models only (`CHARGES2_68`). |
| `FACE_IMPO / DTAN` | real, optional | — | Displacement along the tangent of an edge, for 2D models only; refused in 3D (`CHARGES2_63`, `upstream/bibfor/load/cafaci.F90:206`). |
| `FACE_IMPO / GRX` | real, optional | — | Beam DOF; see `DDL_IMPO / GRX`. |
| `FACE_IMPO / PRES` | real, optional | — | Pressure DOF; see `DDL_IMPO / PRES`. |
| `FACE_IMPO / PHI` | real, optional | — | See `DDL_IMPO / PHI`. Out of scope. |
| `FACE_IMPO / TEMP` | real, optional | — | *temperature*. See `DDL_IMPO / TEMP`. |
| `FACE_IMPO / PRE1` | real, optional | — | See `DDL_IMPO / PRE1`. Out of scope. |
| `FACE_IMPO / PRE2` | real, optional | — | See `DDL_IMPO / PRE2`. Out of scope. |
| `LIAISON_DDL` | factor keyword, optional, repeatable | — | *linear DOF relation*. Defines a linear relation between DOFs of two or more nodes (catalog translation): Σ `COEF_MULT`ᵢ × (DOF `DDL`ᵢ of node i) = `COEF_IMPO`. The building block for conditions no other keyword covers, such as two nodes moving together in one direction (`upstream/astest/ssnp154e.comm:58`). One relation per occurrence. |
| `LIAISON_DDL / GROUP_NO` | node group, optional, list | — | *node group*. The nodes of the relation, in order: node i takes `DDL`ᵢ and `COEF_MULT`ᵢ. Use one-node groups so the order is certain. The number of DOFs must equal the number of nodes (`MODELISA8_47`). |
| `LIAISON_DDL / DDL` | text, required, list | — | One of `'DX'`, `'DY'`, `'DZ'`, `'DRX'`, `'DRY'`, `'DRZ'`, `'PRES'`, `'PHI'`, `'GONF'`, `'TEMP'`, `'PRE1'`, `'PRE2'`, … (77 values; see the .json). The DOF of each node in the relation. |
| `LIAISON_DDL / COEF_MULT` | real, required, list | — | *multiplying coefficients*. The coefficient of each term, one per DOF (`MODELISA8_46` otherwise). |
| `LIAISON_DDL / COEF_IMPO` | real, required | — | *imposed value*. The right-hand side of the relation; 0 for a homogeneous relation. |
| `LIAISON_MAIL` | factor keyword, optional, repeatable | — | *mesh tie (bonded)*. Defines linear relations that join two boundaries of a structure (catalog translation). Each secondary node is projected onto the main elements, and its DOFs are tied to the interpolated DOFs of the element it falls in, so the two parts move together without sharing nodes (`upstream/bibfor/load/LoadKinematic_module.F90:84`). Use it to bond parts meshed separately (`upstream/astest/ssnv106a.comm:119`) or a shell to a solid. Tier 2. |
| `LIAISON_MAIL / GROUP_MA_MAIT` | element group, optional, list | — | *main element group*. The elements the secondary nodes are projected onto. For `TYPE_RACCORD='MASSIF'`, the elements of the main part (the projection is element to element in the model dimension, `upstream/bibfor/load/LoadKinematic_module.F90:542`); Give the solid elements next to the interface, not its faces: in 3D volume elements, in 2D surface elements (U4.44.01 §5.3.2). Giving too many candidates is harmless. |
| `LIAISON_MAIL / GROUP_MA_ESCL` | element group, optional, list | — | *secondary element group*. The nodes of these elements are the tied nodes. Usually the contact face of the secondary part. |
| `LIAISON_MAIL / GROUP_NO_ESCL` | node group, optional, list | — | *secondary node group*. The tied nodes, given directly. |
| `LIAISON_MAIL / DISTANCE_MAX` | real, optional | — | *maximum distance*. Nodes farther than this from every main element are not tied. Without it, every secondary node is tied, however far (message `CALCULEL5_48`). Set it to a small multiple of the gap between the meshes so that nodes that are not on the interface are not tied by mistake (`upstream/astest/sslv200a.comm:440`). |
| `LIAISON_MAIL / DISTANCE_ALARME` | real, optional | — | Distance above which a tied node is reported (warning `CALCULEL5_48`, which also writes a MED file of the distant nodes). Default: one tenth of the size of the nearest element (message text). |
| `LIAISON_MAIL / TYPE_RACCORD` | text, optional | `'MASSIF'` | *tie type*. One of `'MASSIF'`, `'COQUE'`, `'COQUE_MASSIF'`, `'MASSIF_COQUE'`. The kinds of elements on each side: `'MASSIF'` solid to solid (or 2D to 2D); `'COQUE'` shell to shell; `'COQUE_MASSIF'` the edge of a shell (secondary) onto a solid (main); `'MASSIF_COQUE'` a solid face (secondary) onto a shell (main) (projection routines chosen at `upstream/bibfor/load/LoadKinematic_module.F90:204`; `upstream/astest/ssls101m.comm:231`). |
| `LIAISON_MAIL / TRANSF_GEOM_MAIT` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional, list of up to 3, at least 3 | — | Three functions fx, fy, fz that define the geometric transformation applied to the nodes of the main (MAITRE) elements before the connection (catalog translation). Only when `equal_to("TYPE_RACCORD", 'COQUE')`. For shells whose mid-surfaces do not meet. |
| `LIAISON_MAIL / TRANSF_GEOM_ESCL` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional, list of up to 3, at least 3 | — | Three functions fx, fy, fz that define the geometric transformation applied to the nodes of the secondary (ESCLAVE) elements before the connection (catalog translation). Only when `equal_to("TYPE_RACCORD", 'COQUE')`. |
| `LIAISON_MAIL / DDL` | text, optional, list of up to 6 | — | The DOFs included in the connection (default: all the shell DOFs) (catalog translation). One of `'DX'`, `'DY'`, `'DZ'`, `'DRX'`, `'DRY'`, `'DRZ'`. Only when `equal_to("TYPE_RACCORD", 'COQUE')`. |
| `LIAISON_MAIL / TRAN` | real, optional, list of up to 3 | — | Only when `equal_to("TYPE_RACCORD", 'MASSIF')`. With `ANGL_NAUT` and `CENTRE`, a rigid transformation that maps the secondary nodes onto the main side before projection (the read is `kineLoadReadTransf`, `upstream/bibfor/load/LoadKinematic_module.F90:184`). Here `TRAN` is the translation. For periodic or repeated parts. The rotation is applied first, then the translation, and the transformation goes from the secondary side to the main side (U4.44.01 §5.13.3). |
| `LIAISON_MAIL / ANGL_NAUT` | real, optional, list of up to 3 | — | Only when `equal_to("TYPE_RACCORD", 'MASSIF')`. The rotation of that transformation, as nautical angles in degrees. |
| `LIAISON_MAIL / CENTRE` | real, optional, list of up to 3 | — | Only when `equal_to("TYPE_RACCORD", 'MASSIF')`. The center of that rotation. |
| `LIAISON_MAIL / DDL` | text, optional, list | — | One of `'DX'`, `'DY'`, `'DZ'`, `'DRX'`, `'DRY'`, `'DRZ'`, `'PRES'`, `'PHI'`, `'GONF'`, `'TEMP'`, `'PRE1'`, `'PRE2'`, … (78 values; see the .json). Only when `equal_to("TYPE_RACCORD", 'MASSIF')`. The DOFs to tie (default: all DOFs of the secondary nodes). `'DNOR'` ties only the normal displacement and must be the only one (`CHARGES7_2`). |
| `LIAISON_MAIL / EPAIS` | real, required | — | *thickness*. Only when `equal_to("TYPE_RACCORD", 'COQUE_MASSIF')`. The shell thickness, over which the shell edge is spread onto the solid. |
| `LIAISON_MAIL / CHAM_NORMALE` | `cham_no_sdaster`, required | — | Only when `equal_to("TYPE_RACCORD", 'COQUE_MASSIF')`. A nodal field of the shell normals at the secondary nodes (`upstream/astest/ssls101m.comm:97`). |
| `LIAISON_MAIL / ELIM_MULT` | text, optional | `'OUI'` | *skip already tied nodes*. One of `'OUI'`, `'NON'`. With `'OUI'`, a node already tied by an earlier occurrence is not tied again (`kineLoadElimMult`, `upstream/bibfor/load/LoadKinematic_module.F90:180`), which avoids redundant relations where two interfaces meet. With `'NON'` each occurrence is processed on its own, so a node shared by two secondary groups is tied twice and the factorization will probably stop on a zero pivot (U4.44.01 §5.13.3). |
| `LIAISON_SOLIDE` | factor keyword, optional, repeatable | — | *rigid-body coupling*. Models a rigid part of a structure (catalog translation): the selected nodes keep their relative distances, as if joined by a rigid body. Use it for a stiff insert or a loading plate. The catalog help also mentions a `TRAN` keyword for imposing the rigid part's displacement, but there is none in 17.4.26 (`upstream/code_aster/Cata/Commands/affe_char_meca.py:673`). |
| `LIAISON_SOLIDE / GROUP_NO` | node group, optional, list | — | *node group*. The nodes of the rigid part. |
| `LIAISON_SOLIDE / GROUP_MA` | element group, optional, list | — | *element group*. The nodes of these elements. |
| `LIAISON_SOLIDE / SANS_GROUP_MA` | element group, optional, list | — | *excluded element groups*. |
| `LIAISON_SOLIDE / SANS_GROUP_NO` | node group, optional, list | — | *excluded node groups*. |
| `LIAISON_SOLIDE / DIST_MIN` | real, optional | — | *minimum distance*. Distance below which two nodes are taken as coincident when the command decides whether the node cloud is a point, a line, a plane or a volume. Default: 1/1000 of the shortest element edge of the mesh (`upstream/bibfor/load/caliso.F90:163`). Raise it when warning `CALCULEL5_55` or `CALCULEL5_56` says the cloud is nearly flat or nearly straight; the message gives the value to exceed. |
| `LIAISON_UNIF` | factor keyword, optional, repeatable | — | *uniform DOF coupling*. Imposes the same (unknown) value on DOFs of a set of nodes (catalog translation). The DOF stays free, but all nodes share it: a face that stays plane and moves as one in that direction, for example the loaded end of a tensile specimen (`upstream/astest/ssnv142d.comm:99`). |
| `LIAISON_UNIF / GROUP_NO` | node group, optional, list | — | *node group*. The nodes that share the DOFs. |
| `LIAISON_UNIF / GROUP_MA` | element group, optional, list | — | *element group*. The nodes of these elements. |
| `LIAISON_UNIF / SANS_GROUP_MA` | element group, optional, list | — | *excluded element groups*. |
| `LIAISON_UNIF / SANS_GROUP_NO` | node group, optional, list | — | *excluded node groups*. |
| `LIAISON_UNIF / DDL` | text, required, list | — | One of `'DX'`, `'DY'`, `'DZ'`, `'DRX'`, `'DRY'`, `'DRZ'`, `'PRES'`, `'PHI'`, `'GONF'`, `'TEMP'`, `'PRE1'`, `'PRE2'`, … (77 values; see the .json). The DOFs made equal. |
| `LIAISON_RBE3` | factor keyword, optional, repeatable | — | *RBE3 distributed coupling*. Models RBE3-type linear relations between the degrees of freedom of a main node and secondary nodes (catalog translation): the main node's motion is the weighted average of the secondary nodes' motion, and a force or moment on the main node is spread over them without stiffening them. Use it to apply a remote load (force or moment at a point) to a face. The main node needs rotational DOFs for a moment: give it a discrete element (`DIS_TR` in `AFFE_MODELE`, zero stiffness in `AFFE_CARA_ELEM`), as in `upstream/astest/zzzz144a.comm:36`. Tier 2. |
| `LIAISON_RBE3 / GROUP_NO_MAIT` | node group, optional | — | *main node group*. A group of exactly one node, the point where the load acts (`MODELISA10_9` otherwise). |
| `LIAISON_RBE3 / DDL_MAIT` | text, required, list of up to 6 | — | *main-node DOFs*. One of `'DX'`, `'DY'`, `'DZ'`, `'DRX'`, `'DRY'`, `'DRZ'`. The DOFs of the main node that are coupled; all six to transmit forces and moments. |
| `LIAISON_RBE3 / GROUP_NO_ESCL` | node group, optional, list | — | *secondary node group*. The nodes over which the load is spread. |
| `LIAISON_RBE3 / DDL_ESCL` | text, required, list | — | The DOFs of the secondary nodes that take part, written as one string joined by hyphens, such as `'DX-DY-DZ'` for solid nodes (`upstream/bibfor/modelisa/carbe3.F90:313`). Give one string for all secondary nodes or one per node (`MODELISA10_10` otherwise). |
| `LIAISON_RBE3 / COEF_ESCL` | real, optional, list | `1.0` | *secondary-node weights*. The weight of each secondary node in the average: one value for all or one per DOF string (`MODELISA10_12`). Keep 1.0 for a uniform spread. |
| `VECT_ASSE` | `cham_no_sdaster`, optional | — | An assembled nodal force vector, applied as given. For loads computed by another command; out of Tier 1 scope. |
| `FORCE_NODALE` | factor keyword, optional, repeatable | — | *nodal force*. Applies nodal forces to nodes (catalog translation). Each selected node receives the full value given, not a share of it (`upstream/bibfor/load/cafono.F90:271`): on a group of n nodes the total force is n times the value. Use it on single-node groups or with a value divided by hand; for a force spread over a face prefer `FORCE_FACE`, or `LIAISON_RBE3` plus a nodal force on the main node. |
| `FORCE_NODALE / GROUP_NO` | node group, optional, list | — | *node group*. The loaded nodes. |
| `FORCE_NODALE / FX` | real, optional | — | Force along global X, in the force unit of the model (N with mm or m). |
| `FORCE_NODALE / FY` | real, optional | — | Force along global Y. |
| `FORCE_NODALE / FZ` | real, optional | — | Force along global Z. |
| `FORCE_NODALE / MX` | real, optional | — | Moment about global X. Only on nodes with rotational DOFs: on solid nodes alone the command stops (`CHARGES2_46`, `upstream/bibfor/load/cafono.F90:284`). |
| `FORCE_NODALE / MY` | real, optional | — | Moment about global Y. |
| `FORCE_NODALE / MZ` | real, optional | — | Moment about global Z (`upstream/astest/zzzz144a.comm:70`). |
| `FORCE_NODALE / ANGL_NAUT` | real, optional, list of up to 3 | — | Nautical angles, in degrees, of a local basis in which `FX` ... `MZ` are given instead of the global axes (`upstream/astest/sslv200a.comm:445`). More than three values: only the first three are kept (`MODELISA2_66`). |
| `FORCE_FACE` | factor keyword, optional, repeatable | — | *force per unit area on faces*. Applies surface forces on a face of a solid element (catalog translation): a traction vector in global components, constant over the face, on the face elements of a 3D model. Use it for a uniform traction or shear in a fixed direction; for a load normal to a curved face use `PRES_REP`. |
| `FORCE_FACE / GROUP_MA` | element group, optional, list | — | *element group*. The face elements; they must belong to the model. |
| `FORCE_FACE / FX` | real, optional | — | Force per unit area along global X (MPa with N and mm). |
| `FORCE_FACE / FY` | real, optional | — | Force per unit area along global Y. |
| `FORCE_FACE / FZ` | real, optional | — | Force per unit area along global Z (`upstream/astest/ssnv147l.comm:68`). |
| `FORCE_ARETE` | factor keyword, optional, repeatable | — | *force per unit length on edges*. Applies line forces on an edge of a solid or shell element (catalog translation): a force (and, on shells, moment) per unit length along line elements of the model, in global components (`upstream/astest/ssls111a.comm:122`). Use it for a line load on a shell edge. |
| `FORCE_ARETE / GROUP_MA` | element group, optional, list | — | *element group*. The line elements of the edge; they must belong to the model. |
| `FORCE_ARETE / FX` | real, optional | — | Force per unit length along global X (N/mm with N and mm). |
| `FORCE_ARETE / FY` | real, optional | — | Force per unit length along global Y. |
| `FORCE_ARETE / FZ` | real, optional | — | Force per unit length along global Z. |
| `FORCE_ARETE / MX` | real, optional | — | Moment per unit length about global X; shell edges only. `FORCE_ARETE` applies to `DKT`, `DST`, `Q4G`, `COQUE_3D` and `3D`; only the shells have rotations to carry the moments (U4.44.01 §7.2). |
| `FORCE_ARETE / MY` | real, optional | — | Moment per unit length about global Y. |
| `FORCE_ARETE / MZ` | real, optional | — | Moment per unit length about global Z. |
| `PRES_REP` | factor keyword, optional, repeatable | — | *distributed pressure*. Applies a pressure to a 2D or 3D continuum domain, or to a domain of shells and pipes (catalog translation). A pressure normal to the surface: on the boundary faces of a solid (`tests/fixtures/solid_static/input/run.comm:31`) or directly on shell elements (`tests/fixtures/shell_static/input/run.comm:53`). A positive value pushes against the normal (see [Signs and directions](#what-the-solver-does-with-it)). The normals are checked (`VERI_NORM`). |
| `PRES_REP / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Every element of the model that can carry a pressure. |
| `PRES_REP / GROUP_MA` | element group, optional, list | — | *element group*. The face elements of a solid (oriented with `MODI_MAILLAGE/ORIE_PEAU`), or the shell elements. |
| `PRES_REP / FISSURE` | `fiss_xfem`, optional, list of up to 100 | — | A pressure on the lips of XFEM cracks. Out of scope (XFEM). |
| `PRES_REP / PRES` | real, optional | — | The pressure, in the stress unit of the model (MPa with N and mm). Positive pushes against the face normal. |
| `PRES_REP / CISA_2D` | real, optional | — | *in-plane shear*. A shear stress along the edge, for 2D models (`upstream/astest/sslp01a.comm:52`, with a function). Positive along the tangent of the edge, which runs from its first node to its second; for `AXIS`, `D_PLAN`, `C_PLAN` and `AXIS_FOURIER` (U4.44.01 §7.6, §3.9.1). |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `2` prints more detail, for example the redundant relations that were removed (`CHARGES2_34`, `upstream/bibfor/modelisa/aflrch.F90:468`). |

4 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at least one of `EVOL_CHAR`, `PESANTEUR`, `ROTATION`, `DDL_IMPO`, `DDL_POUTRE`, `FACE_IMPO`, `CHAMNO_IMPO`, `ARETE_IMPO`, `LIAISON_DDL`, `LIAISON_OBLIQUE`, `LIAISON_GROUP`, `LIAISON_MAIL`, `LIAISON_CYCL`, `LIAISON_SOLIDE`, `LIAISON_ELEM`, `LIAISON_UNIF`, `LIAISON_CHAMNO`, `LIAISON_RBE3`, `LIAISON_INTERF`, `LIAISON_PROJ`, `VECT_ASSE`, `FORCE_NODALE`, `FORCE_FACE`, `FORCE_ARETE`, `FORCE_CONTOUR`, `FORCE_INTERNE`, `PRE_SIGM`, `PRES_REP`, `EFFE_FOND`, `PRE_EPSI`, `FORCE_POUTRE`, `FORCE_TUYAU`, `FORCE_COQUE`, `FORCE_COQUE_FO`, `LIAISON_COQUE`, `RELA_CINE_BP`, `FORCE_ELEC`, `VITE_FACE`, `ONDE_FLUI`, `FLUX_THM_REP`, `FORCE_SOL`, `ECHANGE_THM`, `ECHANGE_THM_HR` must be given (`AU_MOINS_UN`).
- command: if `EFFE_FOND` is given, `PRES_REP` must all be given (`PRESENT_PRESENT`).
- command: at most one of `FORCE_COQUE`, `FORCE_COQUE_FO` may be given (`EXCLUS`).
- `DDL_IMPO`: at least one of `TOUT`, `GROUP_MA`, `GROUP_NO`, `NOEUD` must be given (`AU_MOINS_UN`).
- `DDL_IMPO`: at least one of `DX`, `DY`, `DZ`, `DRX`, `DRY`, `DRZ`, `GRX`, `PRES`, `PSI`, `PHI`, `DRGX`, `DRGY`, `DRGZ`, `TEMP`, `PRE1`, `PRE2`, `UI2`, `UI3`, `VI2`, `VI3`, `WI2`, `WI3`, `UO2`, `UO3`, `VO2`, `VO3`, `WO2`, `WO3`, `UI4`, `UI5`, `VI4`, `VI5`, `WI4`, `WI5`, `UO4`, `UO5`, `VO4`, `VO5`, `WO4`, `WO5`, `UI6`, `UO6`, `VI6`, `VO6`, `WI6`, `WO6`, `WO`, `WI1`, `WO1`, `GONF`, `BLOCAGE`, `H1X`, `H1Y`, `H1Z`, `H1PRE1`, `H2X`, `H2Y`, `H2Z`, `H2PRE1`, `H3X`, `H3Y`, `H3Z`, `H3PRE1`, `H4X`, `H4Y`, `H4Z`, `K1`, `K2`, `K3`, `PRE_FLU`, `LAG_FLI`, `LAG_FLS`, `LAGS_C`, `LAGS_F1`, `LAGS_F2`, `PR2_FLU`, `LA2_FLI`, `LA2_FLS`, `LAG2_C`, `LAG2_F1`, `LAG2_F2`, `PR3_FLU`, `LA3_FLI`, `LA3_FLS`, `LAG3_C`, `LAG3_F1`, `LAG3_F2`, `LAG4_C`, `LAG4_F1`, `LAG4_F2`, `V11`, `V12`, `V13`, `V21`, `V22`, `V23`, `V31`, `V32`, `V33`, `PRES11`, `PRES12`, `PRES13`, `PRES21`, `PRES22`, `PRES23`, `PRES31`, `PRES32`, `PRES33`, `LH1`, `GLIS`, `LAG_GV` must be given (`AU_MOINS_UN`).
- `FACE_IMPO`: at least one of `DX`, `DY`, `DZ`, `DRX`, `DRY`, `DRZ`, `GRX`, `PRES`, `PHI`, `TEMP`, `PRE1`, `PRE2`, `DNOR`, `DRNOR`, `DTAN` must be given (`AU_MOINS_UN`).
- `FACE_IMPO`: at most one of `DNOR`, `DX` may be given (`EXCLUS`).
- `FACE_IMPO`: at most one of `DNOR`, `DY` may be given (`EXCLUS`).
- `FACE_IMPO`: at most one of `DNOR`, `DZ` may be given (`EXCLUS`).
- `FACE_IMPO`: at most one of `DNOR`, `DRX` may be given (`EXCLUS`).
- `FACE_IMPO`: at most one of `DNOR`, `DRY` may be given (`EXCLUS`).
- `FACE_IMPO`: at most one of `DNOR`, `DRZ` may be given (`EXCLUS`).
- `FACE_IMPO`: at most one of `DTAN`, `DX` may be given (`EXCLUS`).
- `FACE_IMPO`: at most one of `DTAN`, `DY` may be given (`EXCLUS`).
- `FACE_IMPO`: at most one of `DTAN`, `DZ` may be given (`EXCLUS`).
- `FACE_IMPO`: at most one of `DTAN`, `DRX` may be given (`EXCLUS`).
- `FACE_IMPO`: at most one of `DTAN`, `DRY` may be given (`EXCLUS`).
- `FACE_IMPO`: at most one of `DTAN`, `DRZ` may be given (`EXCLUS`).
- `LIAISON_DDL`: exactly one of `GROUP_NO`, `NOEUD` must be given (`UN_PARMI`).
- `LIAISON_MAIL`: at least one of `GROUP_MA_ESCL`, `GROUP_NO_ESCL` must be given (`AU_MOINS_UN`).
- when `equal_to("TYPE_RACCORD", 'MASSIF')`: if `DDL_MAIT` is given, `DDL_ESCL` must all be given (`PRESENT_PRESENT`). (This rule names keywords that the `MASSIF` block does not define, `upstream/code_aster/Cata/Commands/affe_char_meca.py:611`, so it never applies.)
- `LIAISON_SOLIDE`: exactly one of `GROUP_NO`, `GROUP_MA` must be given (`UN_PARMI`).
- `LIAISON_UNIF`: exactly one of `GROUP_NO`, `GROUP_MA` must be given (`UN_PARMI`).
- `FORCE_NODALE`: exactly one of `GROUP_NO`, `NOEUD` must be given (`UN_PARMI`).
- `FORCE_NODALE`: at least one of `FX`, `FY`, `FZ`, `MX`, `MY`, `MZ` must be given (`AU_MOINS_UN`).
- `FORCE_FACE`: at least one of `FX`, `FY`, `FZ` must be given (`AU_MOINS_UN`).
- `FORCE_ARETE`: at least one of `FX`, `FY`, `FZ`, `MX`, `MY`, `MZ` must be given (`AU_MOINS_UN`).
- `PRES_REP`: at least one of `TOUT`, `GROUP_MA`, `FISSURE` must be given (`AU_MOINS_UN`).
- `PRES_REP`: if `TOUT` is given, none of `GROUP_MA`, `FISSURE` may be given (`PRESENT_ABSENT`).
- `PRES_REP`: at least one of `PRES`, `CISA_2D` must be given (`AU_MOINS_UN`).

## Other keywords

Factor keywords outside this reference's scope (sub-keywords are in `en/commands/AFFE_CHAR_MECA.json`):

- `ARETE_IMPO`: Imposes one or more values of displacement on all the nodes of an edge of 3D elements.
- `CHAMNO_IMPO`: Imposes DOFs to the values of a cham_no_sdaster result object.
- `DDL_POUTRE` — *imposed beam DOF*: Fixes DOFs in the local coordinate system of a beam.
- `ECHANGE_THM`: Applies an exchange condition (hydraulic flux) to a 2D or 3D continuum domain.
- `ECHANGE_THM_HR`: Applies an HR-type exchange condition (hydraulic flux) to a 2D or 3D continuum domain.
- `EFFE_FOND`: Computes the end-cap effect on a piping branch (3D modeling type) under pressure.
- `FLUX_THM_REP`: Applies a heat flux and/or a fluid mass input (hydraulic flux) to a 2D or 3D continuum domain.
- `FORCE_CONTOUR`: Applies line forces on the boundary of a 2D, AXIS or AXIS_FOURIER domain.
- `FORCE_COQUE`: Applies surface forces on shell elements.
- `FORCE_COQUE_FO`: Applies surface forces, defined by time-independent functions, on shell elements.
- `FORCE_ELEC`: Applies the Laplace force that acts on a main conductor because of a straight secondary conductor.
- `FORCE_INTERNE`: Applies volume forces (2D or 3D) to a solid domain.
- `FORCE_POUTRE`: Applies line forces on beam elements.
- `FORCE_SOL`: Defines time-domain soil impedances and forces.
- `FORCE_TUYAU`: Applies a pressure on TUYAU (pipe) elements.
- `LIAISON_CHAMNO`: Defines a linear relation between all the DOFs present in a CHAM_NO result object.
- `LIAISON_COQUE`: Models the connection between shell elements by linear relations.
- `LIAISON_CYCL`: Defines linear relations that join the boundaries of two cyclically symmetric parts.
- `LIAISON_ELEM`: Models the connection of a 3D solid part with a beam or a pipe, of a shell with a beam or a pipe, and of a plate with a beam.
- `LIAISON_GROUP`: Defines the same linear relation between some DOFs of pairs of nodes.
- `LIAISON_INTERF`: Defines a linear relation between interface DOFs from a MACRELEM.
- `LIAISON_OBLIQUE`: Applies the same displacement value to nodes, defined component by component in an arbitrary oblique coordinate system.
- `LIAISON_PROJ`: Defines linear relations, from PROJ_CHAMP, between DOFs of the same model.
- `ONDE_FLUI`: Applies the amplitude of a sinusoidal incident pressure wave arriving normal to a face.
- `PRE_EPSI`: Applies an initial-strain load to a 2D, 3D or structural element.
- `PRE_SIGM`: Applies volume stresses (2D or 3D) to a solid domain.
- `RELA_CINE_BP`: Sets kinematic relations that link the cable nodes to the concrete nodes, and specifies whether initial stresses in the cables are taken into account.
- `VITE_FACE`: Imposes normal velocities on a face (ACOUSTIQUE physics).

## Patterns

### Fixed base and internal pressure on a solid

Our `solid_static` fixture: the base face held in X, Y and Z, and an internal pressure on the
inner skin of the shell and the nozzle bore, after `MODI_MAILLAGE/ORIE_PEAU` (line 19). Two
loads, both in `EXCIT`.

Source: `tests/fixtures/solid_static/input/run.comm:29`.

```python
FIXE = AFFE_CHAR_MECA(MODELE=MODE, DDL_IMPO=_F(GROUP_MA="BASE", DX=0.0, DY=0.0, DZ=0.0))

PRESS = AFFE_CHAR_MECA(MODELE=MODE, PRES_REP=_F(GROUP_MA=("P_SHELL", "P_NOZZLE"), PRES=P))

RESU = MECA_STATIQUE(
    MODELE=MODE,
    CHAM_MATER=MATE,
    EXCIT=(_F(CHARGE=FIXE), _F(CHARGE=PRESS)),
    SOLVEUR=_F(METHODE="MUMPS"),
)
```

The run log shows the defaults the command filled in (`tests/fixtures/solid_static/output/run.mess:232`):

```text
FIXE = AFFE_CHAR_MECA(DDL_IMPO=_F(DX=0.0,
                                  DY=0.0,
                                  DZ=0.0,
                                  GROUP_MA='BASE'),
                      DOUBLE_LAGRANGE='OUI',
                      INFO=1,
                      MODELE=MODE,
                      SYNTAXE='NON',
                      VERI_AFFE='OUI',
                      VERI_NORM='OUI')
```

### Simply supported plate under pressure

Our `shell_static` fixture: edges held in Z, two corners hold the in-plane rigid-body motion,
and a pressure on the plate elements themselves. The plate normal is +Z
(`MODI_MAILLAGE/ORIE_NORM_COQUE`, line 30), so a positive `PRES` loads it downward.

Source: `tests/fixtures/shell_static/input/run.comm:43`.

```python
APPUI = AFFE_CHAR_MECA(
    MODELE=MODE,
    DDL_IMPO=(
        _F(GROUP_MA="EDGES", DZ=0.0),
        _F(GROUP_NO="CORNER_A", DX=0.0, DY=0.0),
        _F(GROUP_NO="CORNER_B", DY=0.0),
    ),
)

# Positive PRES acts against the element normal (+Z), i.e. downward (as in ssls101n).
PRESS = AFFE_CHAR_MECA(MODELE=MODE, PRES_REP=_F(GROUP_MA="PLATE", PRES=Q))
```

### Clamp with `BLOCAGE`

All translations and rotations of node `A` set to zero, whatever the node carries.

Source: `upstream/astest/ssll106a.comm:122`.

```python
CHAR0 = AFFE_CHAR_MECA(MODELE=MO, DDL_IMPO=_F(GROUP_NO="A", BLOCAGE=("DEPLACEMENT", "ROTATION")))
```

### Clamped face and a point force in one load

Source: `upstream/astest/ssls147a.comm:37`.

```python
load1 = AFFE_CHAR_MECA(
    DDL_IMPO=_F(BLOCAGE=("DEPLACEMENT",), GROUP_MA=("Sencastre",)),
    FORCE_NODALE=_F(FZ=-0.5, GROUP_NO=("N",)),
    MODELE=model,
)
```

### Gravity

Units m and s; the material defines `RHO`.

Source: `upstream/astest/hsns102a.comm:163`.

```python
PES = AFFE_CHAR_MECA(MODELE=LEMOD, PESANTEUR=_F(GRAVITE=9.81, DIRECTION=(0, 0, -1)))
```

### Centrifugal load

A unit speed about Z; the test scales it later. Speeds in rpm are converted with π/30 a few
lines above (line 43).

Source: `upstream/astest/sdnv108a.comm:48`.

```python
CL1 = AFFE_CHAR_MECA(MODELE=MOD, ROTATION=_F(VITESSE=1, AXE=(nx, ny, nz)))
```

### Surface traction and edge load

`FORCE_FACE` on the face elements `TRAC` of a 3D model; `FORCE_ARETE` on the edge `L12` of a
plate model.

Source: `upstream/astest/ssnv147l.comm:68` and `upstream/astest/ssls111a.comm:122`.

```python
TRACTION = AFFE_CHAR_MECA(MODELE=MO, FORCE_FACE=_F(GROUP_MA="TRAC", FZ=1))

CHME2A = AFFE_CHAR_MECA(MODELE=MO2, FORCE_ARETE=_F(GROUP_MA="L12", FZ=frep))
```

### Normal displacement of a face

Face `DROITE` moved by 0.15 along its normal, with another face fixed.

Source: `upstream/astest/zzzz238a.comm:46`.

```python
CHBLO = AFFE_CHAR_MECA(MODELE=MO, DDL_IMPO=_F(GROUP_NO="GAUCHE", DX=0.0, DY=0.0, DZ=0.0))

CHDNOR = AFFE_CHAR_MECA(MODELE=MO, FACE_IMPO=_F(GROUP_MA="DROITE", DNOR=0.15))
```

### Two nodes with the same displacement in one direction

DY(B) − DY(C) = 0.

Source: `upstream/astest/ssnp154e.comm:58`.

```python
BLOQ = AFFE_CHAR_MECA(
    MODELE=MO,
    LIAISON_DDL=_F(GROUP_NO=("B", "C"), DDL=("DY", "DY"), COEF_MULT=(1.0, -1.0), COEF_IMPO=0.0),
)
```

### Face that moves as one

All nodes of `S_ARR` share the same, unknown, `DY`.

Source: `upstream/astest/ssnv142d.comm:99`.

```python
CH21 = AFFE_CHAR_MECA(MODELE=MO, LIAISON_UNIF=_F(GROUP_NO="S_ARR", DDL="DY"))
```

### Rigid part

Nodes A, B, C, D form a rigid body; E1, E2, E3 are coincident nodes made to move together.

Source: `upstream/astest/sslv114a.comm:48`.

```python
CH1 = AFFE_CHAR_MECA(
    MODELE=MOD1,
    LIAISON_SOLIDE=(
        #         -- CAS GENERAL :
        _F(GROUP_NO=("A", "B", "C", "D")),
        #         -- CAS PARTICULIER : NOEUDS CONFONDUS
        _F(GROUP_NO=("E1", "E2", "E3")),
    ),
    DDL_IMPO=(_F(GROUP_NO=("A", "E1"), DX=2.0, DY=3.0), _F(GROUP_NO=("B",), DY=3.001)),
)
```

### Remote moment on a face (RBE3)

The main node `PO` is a point element with `DIS_TR` (lines 36–49); the moment is applied to it
and spread over the face nodes of `Moment`.

Source: `upstream/astest/zzzz144a.comm:59`.

```python
CH4 = AFFE_CHAR_MECA(
    MODELE=MODM,
    LIAISON_RBE3=_F(
        GROUP_NO_MAIT="PO",
        GROUP_NO_ESCL="Moment",
        DDL_MAIT=("DX", "DY", "DZ", "DRX", "DRY", "DRZ"),
        DDL_ESCL="DX-DY-DZ",
        COEF_ESCL=1.0,
    ),
)

CH5 = AFFE_CHAR_MECA(MODELE=MODM, FORCE_NODALE=_F(GROUP_NO="PO", MZ=1.0e5))
```

### Bonded assembly of separately meshed parts

Supports and four solid-to-solid ties in one load.

Source: `upstream/astest/ssnv106a.comm:119`.

```python
Blocages = AFFE_CHAR_MECA(
    MODELE=MecaMode,
    DDL_IMPO=(
        _F(DX=0.0, DY=0.0, DZ=0, GROUP_MA="RenfortBloquage"),
        _F(DX=0, GROUP_MA=("RenfortSymetrieX", "CloisonSymetrieX")),
        _F(DZ=0, GROUP_MA=("CloisonSymetrieZ")),
    ),
    LIAISON_MAIL=(
        _F(GROUP_MA_ESCL="DoubleElements_double", GROUP_MA_MAIT="renfort", TYPE_RACCORD="MASSIF"),
        _F(GROUP_MA_ESCL="VisAppuiTete", GROUP_MA_MAIT="cloison", TYPE_RACCORD="MASSIF"),
        _F(GROUP_MA_ESCL="ContactVis", GROUP_MA_MAIT="renfort", TYPE_RACCORD="MASSIF"),
        _F(GROUP_NO_ESCL="CloisonsContactRenfort2", GROUP_MA_MAIT="renfort", TYPE_RACCORD="MASSIF"),
    ),
)
```

## Pitfalls

- **Pressure faces with inward normals.** With the default `VERI_NORM='OUI'`, a solid face group
  under `PRES_REP` whose normals do not all point outward stops the command: `MODELISA8_56`
  names the group and the number of badly oriented faces, then `MODELISA4_24` ("stop on
  error(s), normal not outward") (`upstream/bibfor/modelisa/chveno.F90:287`, `:398`). Run
  `MODI_MAILLAGE/ORIE_PEAU` on the group first. The wrong-sign result is silent only with
  `VERI_NORM='NON'`.
- **Not-connected face groups.** The normal check stops with `MESH3_99` when a pressure group
  is in several separate pieces (`upstream/bibfor/modelisa/chveno.F90:228`). Split it into
  connected groups, or, as the message advises, set `VERI_NORM='NON'` after orienting each
  piece with `ORIE_PEAU`.
- **`FORCE_NODALE` on a group multiplies the force.** Every node gets the full value
  (`upstream/bibfor/load/cafono.F90:271`). `FORCE_NODALE=_F(GROUP_NO='FACE', FZ=-1000.0)` on
  a 50-node face applies −50 000 in total. Divide by hand, use `FORCE_FACE` (per unit area),
  or use `LIAISON_RBE3` and a single nodal force.
- **A component that the nodes do not carry.** An explicit component (`DRX=0.0`, `MX=...`)
  that no node of the occurrence carries stops the command (`CHARGES2_45` for `DDL_IMPO`,
  `upstream/bibfor/load/caddli.F90:329`; `CHARGES2_46` for `FORCE_NODALE`). If only some nodes
  carry it, it is applied on those and skipped on the others without a message. For a support
  that mixes solids and shells, `BLOCAGE` says what is meant.
- **Gravity or rotation without density.** Both loads are RHO × acceleration; the material
  needs `RHO` in `DEFI_MATERIAU/ELAS` (`upstream/bibfor/te/te0015.F90:81`), in the mass unit
  that matches the model's units (t/mm³ with N and mm).
- **Gravity in the wrong units.** `GRAVITE` is in length/time² of the model: 9810 for mm, not
  9.81.
- **A load on elements that cannot carry it.** For example `PRES_REP` on the volume group
  instead of the skin group. `VERI_AFFE` reports it with warning `CALCULEL_40` and the first
  elements concerned, and the load is lost on those elements
  (`upstream/bibfor/calculel/verif_affe_carte.F90:318`). With the fixtures' setting
  `DEBUT(ERREUR=_F(ALARME='EXCEPTION'))` the warning stops the run.
- **Over-constrained nodes.** The same DOF imposed by two loads, or by a `DDL_IMPO` and a
  `LIAISON_*` that cannot both hold, gives redundant Lagrange conditions; the factorization
  then reports a singular matrix (`FACTOR_10`, `FACTOR_42` advise checking for "blocage absent
  ou surabondant", missing or redundant supports). TODO(verify) the exact message for each
  case. Within one load, identical relations are merged (`upstream/bibfor/modelisa/ordlrl.F90:59`).
- **`LIAISON_MAIL` ties nodes far from the interface.** Without `DISTANCE_MAX`, every secondary
  node is tied to its nearest main element, however far; the run then only warns
  (`CALCULEL5_48`). Read that warning: it counts the distant nodes and writes them to a MED
  file.
- **`LIAISON_SOLIDE` on nearly aligned or flat nodes.** Warnings `CALCULEL5_55` and
  `CALCULEL5_56` mean the relations are close to redundant and may give a zero pivot; raise
  `DIST_MIN` above the value the message gives (`upstream/bibfor/calculel/getcara_lisno.F90:160` and `:194`).

## See also

- French reference: U4.44.01 (French text: `en/docs/_src/U4.44.01.fr.md`; translation: `en/docs/U4.44.01.md`)
- Catalog: `en/commands/AFFE_CHAR_MECA.json` (generated from `upstream/code_aster/Cata/Commands/affe_char_meca.py:50`)
- Implementation: `upstream/code_aster/CodeCommands/affe_char_meca.py`;
  `upstream/bibfor/op/op0007.F90` → `upstream/bibfor/load/charme.F90`
- Kinematic form for plain supports: [AFFE_CHAR_CINE](AFFE_CHAR_CINE.md)
- Values that vary in time or space: `AFFE_CHAR_MECA_F` with [DEFI_FONCTION](DEFI_FONCTION.md)
  functions (`upstream/astest/forma00a.comm:91`)
- Before: [MODI_MAILLAGE](MODI_MAILLAGE.md) (`ORIE_PEAU`, `ORIE_NORM_COQUE`),
  [DEFI_GROUP](DEFI_GROUP.md), [AFFE_MODELE](AFFE_MODELE.md)
- Next steps: `MECA_STATIQUE` (`EXCIT`, `FONC_MULT`), then `CALC_CHAMP(FORCE='REAC_NODA')` for
  reactions
- Example: `upstream/astest/sslv114a.comm` (lines 48, 125)
- Example: `upstream/astest/ssls147a.comm` (lines 37, 43)
- Example: `upstream/astest/sslx102f.comm` (lines 77, 124)
- Example: `tests/fixtures/solid_static/input/run.comm` (lines 29, 31)
- Example: `tests/fixtures/shell_static/input/run.comm` (lines 43, 53)
- Example: `tests/fixtures/modal/input/run.comm` (line 26)
