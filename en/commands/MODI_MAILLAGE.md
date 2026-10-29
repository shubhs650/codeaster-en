---
command: MODI_MAILLAGE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/modi_maillage.py:51
doc_fr: U4.23.04
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3a)
examples: [cont202a, cont203a, cont204a, sdlv127b, ssnv128e, sslx300a, zzzz164c, hsnv121f, zzzz360a, sdls505a, sdls114a, mfron07a]
---

# MODI_MAILLAGE — modify mesh

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.

`MODI_MAILLAGE` changes an existing mesh in place and returns it. It does two kinds of work.
The first, and the one a structural model nearly always needs, is **orientation**: making the
normals of boundary (skin) elements point out of the solid (`ORIE_PEAU`), making shell normals
consistent (`ORIE_NORM_COQUE`), or making line elements run in one direction (`ORIE_LIGNE`).
Loads such as `PRES_REP` act along these normals, so the orientation decides the sign of the
load. The second is **geometric transformation** of the node coordinates: translation,
rotation, mirror, scaling, change of basis, adding a displacement field, or small random
perturbation. It needs a mesh (`MAILLAGE`) and, for the orientation options, the element groups
to orient. The command is re-entrant: write `MA = MODI_MAILLAGE(reuse=MA, MAILLAGE=MA, ...)`.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Effectuer des modifications sur un maillage existant: réorienter des mailles servant, à l'application d'une pression, à la modélisation du contact,...» |
| Kind | `OPER` |
| Result | `maillage_sdaster` |
| Can reuse its input (`reuse=`) | yes (the object given in `MAILLAGE`); catalog `reentrant='o:MAILLAGE'` |
| French reference | U4.23.04 — from en/doc-ids.yaml (status: proposed) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `ORIE_PEAU`, `ORIE_NORM_COQUE` |

## Keywords

The operations run in a fixed order whatever the order in the call: `ORIE_FISSURE`,
`MODI_MAILLE`, `DEFORME`, `TRANSLATION`, `MODI_BASE`, `ROTATION`, `SYMETRIE`, `ECHELLE`, then
the orientations (`ORIE_PEAU`, `ORIE_NORM_COQUE`, `ORIE_LIGNE`), then `ABSC_CURV`
(`upstream/bibfor/op/op0154.F90:98`–`287`).

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MAILLAGE` | `maillage_sdaster`, required | — | *mesh*. The mesh to modify. It is modified in place and is also the result (`upstream/code_aster/CodeCommands/modi_maillage.py:38`), so pass the same name with `reuse=`. |
| `ORIE_FISSURE` | factor keyword, optional | — | Orients the elements of a single-layer band, such as a band of joint or crack elements, so that their transverse direction is consistent. The band must be one element thick and rest on elements of the same dimension; otherwise the command stops with `ALGORITH2_30`. Use it on the interface band of joint elements (example: `upstream/astest/mfron07a.comm:34`). TODO(verify): the list of joint modeling types that require it, against U4.23.04. |
| `ORIE_FISSURE / GROUP_MA` | element group, required, list | — | *element group*. The element groups that form the band. |
| `DEFORME` | factor keyword, optional | — | Moves the nodes: adds a displacement field to the coordinates, or perturbs them randomly. Use it to continue a study on a deformed geometry, or to shift a mesh (message `MAILLAGE1_3` suggests it to move an axisymmetric mesh into the half-plane X ≥ 0). |
| `DEFORME / OPTION` | text, required | — | *option*. One of `'TRAN'`. The only option: the nodes are translated. |
| `DEFORME / DEPL` | `cham_no_sdaster`, optional | — | *displacement*. A nodal displacement field (`DEPL_R`) on the same mesh; it is added to the coordinates (`upstream/bibfor/op/op0154.F90:133`). A field on another mesh stops the command (`MESH1_1`, which advises `PROJ_CHAMP` to move the field onto this mesh). Extract the field first, for example with `CREA_CHAMP` from a result. |
| `DEFORME / ALEA` | real, optional | — | Random perturbation. Each coordinate moves by a random amount up to ± `ALEA` times the mesh size in that direction (`upstream/bibfor/algorith/modi_alea.F90`). The source says the purpose is to break the symmetries of a mesh, for example to avoid multiple (repeated) eigenmodes. Use a tiny value, as in `ALEA=1.0e-8` (`upstream/astest/sdls505a.comm:31`). |
| `ORIE_PEAU` | factor keyword, optional, repeatable | — | *orient boundary elements outward*. Reorients boundary (skin) elements so that their normal points out of the solid they bound: faces (TRIA, QUAD) of a 3D solid, or edges (SEG) of a 2D domain. Use it on every group that carries a pressure (`PRES_REP`) or a normal displacement (`FACE_IMPO DNOR`) before `AFFE_CHAR_MECA`, which checks that these normals point outward (see Pitfalls). |
| `ORIE_PEAU / GROUP_MA_PEAU` | element group, required, list | — | The boundary element groups to orient. They may only contain skin elements: a volume element stops the command (`MODELISA5_94`), and SEG cannot be mixed with TRIA/QUAD (`MODELISA5_98`). |
| `ORIE_PEAU / GROUP_MA_INTERNE` | element group, optional, list | — | The solid (or, in 2D, surface) elements that define "inside". Needed only when a boundary group lies inside the mesh, between elements on both sides, for example an interface between two materials or a crack lip. Without it the command stops with `PREPOST4_97`, whose advice is to give `GROUP_MA_INTERNE` to choose the side. Example: `upstream/astest/sdlv127b.comm:26`. |
| `ORIE_NORM_COQUE` | factor keyword, optional, repeatable | — | *orient shell normals*. Makes the normals of shell (surface) elements consistent across each group. Loads defined relative to the normal, such as `FORCE_COQUE` `PRES`, depend on it. Use it on every shell group, and give `VECT_NORM` to fix which side is "positive". |
| `ORIE_NORM_COQUE / GROUP_MA` | element group, required, list | — | *element group*. The shell element groups to orient. Each group must be connected: a group in several disconnected pieces stops the command (`MESH3_6`, or `MODELISA6_2` with `VECT_NORM`). Split it into one occurrence per piece. |
| `ORIE_NORM_COQUE / VECT_NORM` | real, optional, list of up to 3 | — | Reference normal direction. The elements that touch the reference node (`GROUP_NO`) are oriented so that their normal agrees with this vector, and the orientation is then propagated to their neighbors (`upstream/bibfor/modelisa/orvlma.F90`). Without `VECT_NORM` all elements are oriented like the first element of the group, whatever its direction. |
| `ORIE_NORM_COQUE / GROUP_NO` | node group, optional | — | *node group*. Only when `exists("VECT_NORM")`. The node at which `VECT_NORM` applies; if the group holds several nodes the first is used. If omitted, the first node of the first element of the first group is used (`upstream/bibfor/mesh/mesh_modification_module.F90:140`–`148`). Give a node where the intended normal is unambiguous. No element touching that node stops the command (`MODELISA6_1`). |
| `ORIE_LIGNE` | factor keyword, optional, repeatable | — | Orients line elements (SEG) so that they all run in the same direction. Needed where element direction matters: `DEFI_CABLE_BP` cables (`MODELISA7_14`) and beams with a varying (homothetic) circular section (`MODELISA5_52`, `MODELISA5_53`) both ask for it. Example: `upstream/astest/sslx300a.comm:39`. |
| `ORIE_LIGNE / GROUP_MA` | element group, required, list | — | *element group*. The line element groups to orient. Only line elements are accepted (`MODELISA5_93`). |
| `ORIE_LIGNE / VECT_TANG` | real, optional, list of up to 3 | — | Reference tangent direction at the node `GROUP_NO`; the line is oriented so that it runs along this vector there. Without it, the elements are oriented like the first element of each group. |
| `ORIE_LIGNE / GROUP_NO` | node group, required | — | *node group*. Only when `exists("VECT_TANG")`. The node where `VECT_TANG` applies; a group with several nodes gives warning `SOUSTRUC_87` and its first node is used. |
| `MODI_MAILLE` | factor keyword, optional | — | Moves the mid-side nodes of quadratic elements next to a crack front to the quarter points, which gives Barsoum elements that represent the crack-tip stress singularity. Requires a quadratic mesh (`ALGORITH16_72`). Use it for linear-elastic fracture computations on a meshed crack. |
| `MODI_MAILLE / OPTION` | text, required | — | *option*. One of `'NOEUD_QUART'` (quarter-point nodes). |
| `MODI_MAILLE / GROUP_MA_FOND` | element group, optional | — | The crack front as an element group (line elements in 3D). Give this or `GROUP_NO_FOND`. |
| `MODI_MAILLE / GROUP_NO_FOND` | node group, optional | — | The crack front as a node group (in 3D, at least 2 nodes: `ALGORITH16_74`). Example: `upstream/astest/sdls114a.comm:44`. |
| `MODI_BASE` | factor keyword, optional | — | Re-expresses all node coordinates in a new orthonormal basis: the new coordinates are the components along `VECT_X`, `VECT_Y` and their cross product (`upstream/bibfor/algorith/chgref.F90`). The vectors are normalized. Use it to align a model with the global axes. |
| `MODI_BASE / VECT_X` | real, required, list of up to 3, at least 2 | — | First axis of the new basis. 2 values in 2D (the second axis is then perpendicular to it), 3 values in 3D. A zero vector stops the command (`ALGORITH_96`). |
| `MODI_BASE / VECT_Y` | real, optional, list of up to 3, at least 2 | — | Second axis of the new basis. Required in 3D, where it must be orthogonal to `VECT_X` (`ALGORITH_97`). Not used in 2D. |
| `ECHELLE` | real, optional | — | Scale factor: every coordinate is multiplied by it (`upstream/bibfor/algorith/echell.F90`). Use it to change length units, for example `ECHELLE=1000.0` from meters to millimeters (`upstream/astest/hsnv121f.comm:42`). All material data and loads must then use the same unit system. |
| `TRANSLATION` | real, optional, list of up to 3, at least 2 | — | Translation vector added to every node (2 values in 2D, 3 in 3D). Example: `upstream/astest/zzzz164c.comm:43`. |
| `ROTATION` | factor keyword, optional, repeatable | — | Rigid rotation of the mesh. Here `ROTATION` is a geometric transformation, not the centrifugal load of `AFFE_CHAR_MECA` (see the glossary note). Repeat the keyword for successive rotations; they are applied in order. |
| `ROTATION / POIN_1` | real, required, list of up to 3, at least 2 | — | A point on the rotation axis (in 2D, the center of rotation). |
| `ROTATION / ANGLE` | real, optional | `0.0` | Rotation angle in degrees (`upstream/bibfor/algorith/rotama.F90:64` converts it to radians). |
| `ROTATION / POIN_2` | real, optional, list of up to 3, at least 2 | — | 3D only: a second point on the axis; the axis runs from `POIN_1` to `POIN_2`. Give this or `DIR`. |
| `ROTATION / DIR` | real, optional, list of up to 3, at least 2 | — | 3D only: direction of the rotation axis through `POIN_1`. Give this or `POIN_2`. |
| `SYMETRIE` | factor keyword, optional | — | Mirrors the mesh about a plane in 3D or a line in 2D. Use it to build the other half of a symmetric part. TODO(verify): whether element orientation (normals) is restored after mirroring, against U4.23.04. |
| `SYMETRIE / POINT` | real, required, list of up to 3, at least 2 | — | *reference point*. Point on the line or on the plane. |
| `SYMETRIE / AXE_1` | real, required, list of up to 3, at least 2 | — | Direction vector of the line, or first vector in the plane. It must have as many components as `POINT` (`MESH1_62`). |
| `SYMETRIE / AXE_2` | real, optional, list of up to 3, at least 3 | — | Second vector in the plane. Required in 3D (`MESH1_64`); ignored with a warning in 2D (`MESH1_63`). |
| `ABSC_CURV` | factor keyword, optional | — | Computes and stores the curvilinear abscissa (distance along the line) of the nodes of a line of elements. Post-processing that reports results against the curvilinear abscissa needs it (`POSTRELE_4`, `POSTRELE_16`). The elements must form one open line (`INTEMAIL_36`, `INTEMAIL_37`) of POI1/SEG2/SEG3/SEG4 (`MODELISA_2`). |
| `ABSC_CURV / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Use the whole mesh as the line. |
| `ABSC_CURV / GROUP_MA` | element group, optional, list | — | *element group*. The line elements to use. |
| `ABSC_CURV / GROUP_NO_ORIG` | node group, optional | — | The node where the abscissa is zero: a group with exactly one node (`MODELISA_5`) at one end of the line (`INTEMAIL_38`). Example: `upstream/astest/zzzz360a.comm:41`. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `2` also writes one line per element to the log as it is oriented (`upstream/bibfor/modelisa/orvlma.F90`). |

1 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at least one of `ORIE_FISSURE`, `DEFORME`, `ORIE_PEAU`, `ORIE_NORM_COQUE`, `MODI_MAILLE`, `TRANSLATION`, `ROTATION`, `MODI_BASE`, `ECHELLE`, `SYMETRIE`, `ORIE_LIGNE`, `ABSC_CURV` must be given (`AU_MOINS_UN`).
- command: if `ORIE_FISSURE` is given, none of `DEFORME`, `ORIE_PEAU`, `ORIE_NORM_COQUE`, `MODI_MAILLE`, `ORIE_LIGNE` may be given (`PRESENT_ABSENT`).
- command: if `DEFORME` is given, none of `ORIE_FISSURE`, `ORIE_PEAU`, `ORIE_NORM_COQUE`, `MODI_MAILLE`, `ORIE_LIGNE` may be given (`PRESENT_ABSENT`).
- command: if `ORIE_PEAU` is given, none of `ORIE_FISSURE`, `DEFORME`, `ORIE_NORM_COQUE`, `MODI_MAILLE`, `ORIE_LIGNE` may be given (`PRESENT_ABSENT`).
- command: if `ORIE_NORM_COQUE` is given, none of `ORIE_FISSURE`, `DEFORME`, `ORIE_PEAU`, `MODI_MAILLE`, `ORIE_LIGNE` may be given (`PRESENT_ABSENT`).
- command: if `MODI_MAILLE` is given, none of `ORIE_FISSURE`, `DEFORME`, `ORIE_PEAU`, `ORIE_NORM_COQUE`, `ORIE_LIGNE` may be given (`PRESENT_ABSENT`).
- command: at most one of `ROTATION`, `MODI_BASE` may be given (`EXCLUS`).
- command: at most one of `SYMETRIE`, `ROTATION` may be given (`EXCLUS`).
- command: at most one of `SYMETRIE`, `TRANSLATION` may be given (`EXCLUS`).
- command: at most one of `SYMETRIE`, `MODI_BASE` may be given (`EXCLUS`).
- command: at most one of `SYMETRIE`, `ECHELLE` may be given (`EXCLUS`).
- `DEFORME`: exactly one of `DEPL`, `ALEA` must be given (`UN_PARMI`).
- `MODI_MAILLE`: at least one of `GROUP_MA_FOND`, `GROUP_NO_FOND` must be given (`AU_MOINS_UN`).
- `ROTATION`: at most one of `DIR`, `POIN_2` may be given (`EXCLUS`).
- `ABSC_CURV`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).

In practice: one call does either one orientation task or geometric transformations. To orient
both skins and shells, call the command twice.

## Patterns

### Orient pressure faces of a solid outward

The step before applying `PRES_REP` on a 3D solid. Every face group that receives pressure is
listed.

Source: `tests/fixtures/solid_static/input/run.comm:20` (also `upstream/astest/cont202a.py:292`
for contact surfaces).

```python
MAIL = MODI_MAILLAGE(reuse=MAIL, MAILLAGE=MAIL, ORIE_PEAU=_F(GROUP_MA_PEAU=("P_SHELL", "P_NOZZLE")))
```

### Orient a boundary group that lies inside the mesh

`GROUP_MA_INTERNE` names the element group on the "inside" of the boundary group `LITOT`.
Use this form whenever the boundary group has elements on both sides.

Source: `upstream/astest/sdlv127b.comm:26`.

```python
mail = MODI_MAILLAGE(
    reuse=mail, MAILLAGE=mail, ORIE_PEAU=_F(GROUP_MA_PEAU="LITOT", GROUP_MA_INTERNE="SUF")
)
```

### Orient shell normals along a known direction

The plate normals are made to point along +Z, starting from the node group `CENTER`. The log
reports how many elements were flipped: here none, because the Gmsh normals already pointed
along +Z, and the call makes that explicit and checked.

Source: `tests/fixtures/shell_static/input/run.comm:27` (also `upstream/astest/ssnv128e.comm:51`).

```python
MAIL = MODI_MAILLAGE(
    reuse=MAIL,
    MAILLAGE=MAIL,
    ORIE_NORM_COQUE=_F(GROUP_MA="PLATE", GROUP_NO="CENTER", VECT_NORM=(0.0, 0.0, 1.0)),
)
```

Log (`tests/fixtures/shell_static/output/run.mess`): `Traitement du GROUP_MA: PLATE de 400
mailles.` / `0 mailles ont été orientées.` (messages `MESH3_3`, `MESH3_4`: group PLATE, 400
elements processed, 0 elements reoriented).

### Change length units

Source: `upstream/astest/hsnv121f.comm:42`.

```python
MA = MODI_MAILLAGE(reuse=MA, MAILLAGE=MA, ECHELLE=1000.0)
```

### Rotate a mesh about an axis

45° about the global X axis through the origin.

Source: `upstream/astest/zzzz164c.comm:45`.

```python
MA[2] = MODI_MAILLAGE(MAILLAGE=MA[2], ROTATION=_F(POIN_1=(0.0, 0, 0), ANGLE=45, POIN_2=(1, 0, 0.0)))
```

## Pitfalls

- **Pressure faces must be oriented before the load is defined.** `AFFE_CHAR_MECA` checks that
  the normals of `PRES_REP`, `FACE_IMPO` and `EFFE_FOND` faces point outward and stops with
  error `MODELISA8_56` ("N badly oriented elements; use MODI_MAILLAGE") when they do not
  (`upstream/bibfor/modelisa/chveno.F90:83`, `:287`). For `FORCE_COQUE` it only checks that
  normals are consistent. Run `ORIE_PEAU` (solids) or `ORIE_NORM_COQUE` (shells) first.
  `VERI_NORM='NON'` switches the check off but does not correct the normals.
- **The command modifies its input even without `reuse=`.** The result object is the input
  mesh (`upstream/code_aster/CodeCommands/modi_maillage.py:38`), so
  `MA2 = MODI_MAILLAGE(MAILLAGE=MA, TRANSLATION=...)` also moves `MA`. To keep the original,
  read the mesh twice (as `upstream/astest/zzzz164c.comm` does with `MA[0]`…`MA[4]`) or copy it
  first.
- **Disconnected shell groups cannot be oriented in one pass.** Orientation spreads from
  element to element; a group made of separate pieces stops the command with `MESH3_6` or
  `MODELISA6_2`. Give one `ORIE_NORM_COQUE` occurrence per piece, each with its own
  `GROUP_NO` and `VECT_NORM`.
- **No topology change after `CREA_MAILLAGE/DECOUPE_LAC`.** On a mesh already cut into LAC
  contact patches, any `MODI_MAILLAGE` operation except `DEFORME` and `TRANSLATION` stops with
  `MESH1_12`. Do all orientation and transformation before `DECOUPE_LAC`
  (`upstream/bibfor/op/op0154.F90:298`).
- **`ECHELLE` changes the unit system.** Scaling the mesh does not rescale Young's modulus,
  pressures or densities; the whole data set must be in the new units.

## See also

- French reference: U4.23.04 (translation: `en/docs/U4.23.04.md` once task 5.x lands)
- Catalog: `en/commands/MODI_MAILLAGE.json` (generated from `upstream/code_aster/Cata/Commands/modi_maillage.py:51`)
- Implementation: `upstream/bibfor/op/op0154.F90`; orientation `upstream/bibfor/modelisa/orilgm.F90`,
  `upstream/bibfor/mesh/mesh_modification_module.F90`
- Related: `LIRE_MAILLAGE`, `DEFI_GROUP`, `AFFE_CHAR_MECA` (`PRES_REP`, `VERI_NORM`)
- Example: `upstream/astest/cont202a.py` (lines 292)
- Example: `upstream/astest/cont203a.py` (lines 69)
- Example: `upstream/astest/cont204a.py` (lines 93)
- Example: `tests/fixtures/solid_static/input/run.comm` (line 20), `tests/fixtures/shell_static/input/run.comm` (line 27)
