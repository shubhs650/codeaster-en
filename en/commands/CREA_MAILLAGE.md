---
command: CREA_MAILLAGE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/crea_maillage.py:38
doc_fr: U4.23.02
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3a)
examples: [mesh001h, zzzz383d, ssls147a, ssls04d, sslv130a, zzzz236a, sdld110a, sdls504a, ssnp142j, ssls111a, ssnp121q, forma43a]
---

# CREA_MAILLAGE — create derived mesh

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

`CREA_MAILLAGE` builds a **new** mesh from an existing one; the input mesh is left unchanged
(the result is a fresh object, `upstream/code_aster/CodeCommands/crea_maillage.py:39`). Each
call does exactly one transformation, chosen by one factor keyword: convert linear elements to
quadratic or back (`LINE_QUAD`, `QUAD_LINE`), add the extra nodes some element formulations
need (`MODI_MAILLE`, `HEXA20_27`, `PENTA15_18`, `COQUE_SOLIDE`, `MODI_HHO`), keep only part of
the mesh (`RESTREINT`), refine it uniformly (`RAFFINEMENT`), add point elements on nodes
(`CREA_POI1`), duplicate elements (`CREA_MAILLE`), extrude a surface into a solid layer
(`COQU_VOLU`), insert joint elements along a crack path (`CREA_FISS`), or prepare special meshes
(`DECOUPE_LAC`, `ECLA_PG`, `GEOM_FIBRE`, `REPERE`). The decision it encodes is usually "the mesh
from the mesher does not match the element formulation the model needs". Everything built on
the old mesh (model, fields) must be rebuilt on the new one.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Crée un maillage à partir d'un maillage existant» |
| Kind | `OPER` |
| Result | `maillage_sdaster`, `maillage_p` (depends on the keywords given) |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.23.02 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `QUAD_LINE`, `LINE_QUAD`, `COQU_VOLU` |

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MAILLAGE` | `maillage_sdaster` or `maillage_p`, optional | — | *mesh*. The source mesh. Required for every transformation except `GEOM_FIBRE` and `ECLA_PG` (`MESH1_15`; catalog comment). A parallel mesh (`maillage_p`) is refused by `CREA_FISS`, `MODI_MAILLE`, `COQU_VOLU` and `CREA_MAILLE` (`MESH1_22`). |
| `GEOM_FIBRE` | `gfibre_sdaster`, optional | — | A fiber-section geometry from `DEFI_GEOM_FIBRE`; the command returns the mesh of its fibers (`upstream/bibfor/op/op0167.F90:258`). Example: `upstream/astest/forma43a.comm:70`. The mesh holds all the fiber groups of the study (U4.23.02 §4.16). |
| `CREA_POI1` | factor keyword, optional, repeatable | — | Creates POI1 elements from nodes. Use it to carry point properties on nodes, for example discrete masses or springs (`DISCRET` in `AFFE_CARA_ELEM`), which need an element to be assigned to (`upstream/astest/sdld110a.comm:31`). |
| `CREA_POI1 / NOM_GROUP_MA` | element group, optional, list | — | Name of the element group that receives the new POI1 elements. Without it the elements are created but no group holds them (`upstream/bibfor/op/op0167.F90:758`), so later commands cannot address them: always give it. |
| `CREA_POI1 / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. A POI1 on every node of the mesh. |
| `CREA_POI1 / GROUP_MA` | element group, optional, list | — | *element group*. A POI1 on every node of these elements. |
| `CREA_POI1 / GROUP_NO` | node group, optional, list | — | *node group*. A POI1 on every node of these groups. The usual choice. |
| `CREA_MAILLE` | factor keyword, optional, repeatable | — | Duplicates elements: copies them, on the same nodes, into a new group. Use it to assign two element formulations to the same region, for example a second shell layer (`upstream/astest/ssls111a.comm:85`). The copies are double elements (same connectivity), which the mesh check flags (`MODELISA4_8`); that is intended here. |
| `CREA_MAILLE / NOM` | text, required | — | Name of the element group that receives the copies. |
| `CREA_MAILLE / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Duplicate every element (the default when neither `TOUT` nor `GROUP_MA` is given). |
| `CREA_MAILLE / GROUP_MA` | element group, optional, list | — | *element group*. Duplicate only these elements. |
| `RESTREINT` | factor keyword, optional | — | Restricts a mesh to element groups. Keeps the listed elements and the nodes they use (plus the nodes of `GROUP_NO`), then runs the mesh check (`upstream/bibfor/op/op0167.F90:556`–`557`). Use it to cut a sub-model or to post-process one part on its own mesh. |
| `RESTREINT / GROUP_MA` | element group, required, list | — | *element group*. The element groups to keep. |
| `RESTREINT / TOUT_GROUP_MA` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. `'NON'`: only the groups listed in `GROUP_MA` exist in the new mesh. `'OUI'`: every element group of the source mesh is kept, reduced to the kept elements (`upstream/bibfor/calculel/rdtmai.F90`). |
| `RESTREINT / GROUP_NO` | node group, optional, list | — | *node group*. Extra node groups whose nodes are kept even if no kept element uses them; with `TOUT_GROUP_NO='NON'` these are also the only node groups kept. |
| `RESTREINT / TOUT_GROUP_NO` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. `'NON'` (default): only the node groups listed in `GROUP_NO` are kept, so with no `GROUP_NO` the new mesh has no node groups at all. `'OUI'`: every node group is kept, reduced to the kept nodes. |
| `COQU_VOLU` | factor keyword, optional | — | *solid elements from shell surfaces*. Creates volume elements from surface elements: each surface element is extruded by `EPAIS` along its normal into one layer of solid elements (`upstream/bibfor/algeline/cmcovo.F90`). Use it to go from a shell model to a solid model of the same part. No upstream test case uses it in 17.4.26. |
| `COQU_VOLU / NOM` | text, required | — | Name of the element group made of the new solid elements (U4.23.02 §4.13.1). |
| `COQU_VOLU / GROUP_MA` | element group, required, list | — | *element group*. The surface elements to extrude. Orient their normals consistently first (`MODI_MAILLAGE/ORIE_NORM_COQUE`), since the extrusion follows them. |
| `COQU_VOLU / EPAIS` | real, required | — | *thickness*. Thickness of the solid layer. |
| `COQU_VOLU / PLAN` | text, required | — | One of `'SUP'`, `'MOY'`, `'INF'`. Where the given surface sits in the layer. `'SUP'`: it is the top face, the layer grows against the normal. `'INF'`: it is the bottom face, the layer grows along the normal. `'MOY'`: it is the mid-surface (see `TRANSLATION`) (`upstream/bibfor/algeline/cmcovo.F90`, `plan` branches). |
| `COQU_VOLU / TRANSLATION` | text, required | — | One of `'SUP'`, `'INF'`. Only when `equal_to("PLAN", 'MOY')`. With `PLAN='MOY'` the original nodes are moved by `EPAIS`/2 along the normal (`'SUP'`) or against it (`'INF'`), and the new nodes are placed `EPAIS` away on the other side, so that the given surface ends up mid-thickness. |
| `MODI_MAILLE` | factor keyword, optional, repeatable | — | Changes the element type. Use it when the chosen modeling type needs a different element: for example `COQUE_3D` shells need 7-node triangles, obtained with `'TRIA6_7'` (`upstream/astest/sdls504a.comm:24`, `:33`). |
| `MODI_MAILLE / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Convert every element of the relevant type. |
| `MODI_MAILLE / GROUP_MA` | element group, optional, list | — | *element group*. Convert only these elements. Converting part of a mesh gives warning `MESH1_4`, because it can make the mesh non-conforming. |
| `MODI_MAILLE / OPTION` | text, required | — | *option*. Choice of the transformation. One of `'TRIA6_7'`, `'QUAD8_9'`, `'SEG3_4'`, `'QUAD_TRIA3'`. `'TRIA6_7'`, `'QUAD8_9'`, `'SEG3_4'` add one node to each element (`upstream/bibfor/op/op0167.F90:563`). `'QUAD_TRIA3'` splits quadrangles into 3-node triangles: 2 per QUAD4, 6 per QUAD8 or QUAD9 (`upstream/bibfor/algeline/cmqutr.F90:162`); only one occurrence of it is allowed (`MESH1_9`). |
| `RAFFINEMENT` | factor keyword, optional | — | Uniform refinement of the mesh: each edge is split in two, `NIVEAU` times (`upstream/code_aster/ObjectsExt/mesh_ext.py`, `refine`). Use it for mesh-convergence studies. The whole mesh is refined; a partial selection is a fatal error (`MESH1_4`, `op0167.F90:474`). |
| `RAFFINEMENT / TOUT` | text, optional | `'OUI'` | *all (entire mesh)*. One of `'OUI'`. The only allowed value. |
| `RAFFINEMENT / NIVEAU` | integer, optional | `1` | Number of successive refinements. Each level multiplies the number of elements by about 2^d in dimension d. Example: `NIVEAU=2` (`upstream/astest/mesh001h.py:30`). |
| `CREA_FISS` | factor keyword, optional, repeatable | — | Creates a potential crack with joint elements or elements with a discontinuity, between two facing node lines. Use it to insert interface (joint) elements along a predefined crack path; the new group is then given a joint modeling type, for example `PLAN_JOINT` in `upstream/astest/ssnp142j.comm:80`, `:104`. The created elements have 4 nodes (`upstream/bibfor/mesh/cmcrea.F90` header), a 2D feature: the new elements are `QUAD4` along a line (U4.23.02 §4.14). |
| `CREA_FISS / NOM` | text, required | — | Name of the element group that receives the new joint elements. |
| `CREA_FISS / GROUP_NO_1` | node group, required | — | The nodes of one side of the crack path. |
| `CREA_FISS / GROUP_NO_2` | node group, required | — | The nodes of the other side, facing `GROUP_NO_1`. Both groups must have the same number of nodes and be ordered so that their numbering starts on the same side (for example with `DEFI_GROUP` `CREA_GROUP_NO` `OPTION='NOEUD_ORDO'`). `GROUP_NO_1` carries local nodes 1 and 2 and `GROUP_NO_2` nodes 3 and 4; choose them so that the element numbering runs counterclockwise (U4.23.02 §4.14.2). |
| `LINE_QUAD` | factor keyword, optional | — | *linear to quadratic*. Linear to quadratic conversion: adds a mid-side node on every edge (and center nodes where the element type needs them). Use it when the mesher produced linear elements but quadratic elements are wanted (bending of solids, stress accuracy). Example: `upstream/astest/ssls04d.comm:29`. |
| `LINE_QUAD / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Convert the whole mesh (the default when neither `TOUT` nor `GROUP_MA` is given). |
| `LINE_QUAD / GROUP_MA` | element group, optional, list | — | *element group*. Convert only these elements. Gives warning `MESH1_4` (risk of a non-conforming mesh). |
| `HEXA20_27` | factor keyword, optional | — | HEXA20 to HEXA27 conversion (adds face and volume center nodes). Use it when 27-node hexahedra are wanted; `upstream/astest/ssnp121q.comm:29` uses it to run a `3D` model on HEXA27. Warning `MESH1_11` if other elements with 8-node quadrangular faces (PENTA15, PYRAM13) stay unconverted, since the mesh may then be non-conforming. |
| `HEXA20_27 / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Convert all HEXA20 (default). |
| `HEXA20_27 / GROUP_MA` | element group, optional, list | — | *element group*. Convert only these elements (warning `MESH1_4`). |
| `PENTA15_18` | factor keyword, optional | — | PENTA15 to PENTA18 conversion (adds center nodes on the quadrangular faces). Same use and warnings as `HEXA20_27`. |
| `PENTA15_18 / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Convert all PENTA15 (default). |
| `PENTA15_18 / GROUP_MA` | element group, optional, list | — | *element group*. Convert only these elements (warning `MESH1_4`). |
| `MODI_HHO` | factor keyword, optional | — | Creates a mesh for HHO (hybrid high-order) modeling types, which need extra nodes. Use it only before an HHO model (`upstream/astest/ssnp123j.comm:27`). |
| `MODI_HHO / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. |
| `COQUE_SOLIDE` | factor keyword, optional, repeatable | — | Creates a mesh for the `COQUE_SOLIDE` (solid-shell) modeling type: HEXA8 become HEXA9 and PENTA6 become PENTA7 (`upstream/bibfor/op/op0167.F90:353`). Use it before assigning that modeling type. Example: `upstream/astest/zzzz416c.comm:23`. |
| `COQUE_SOLIDE / GROUP_MA` | element group, required, list | — | *element group*. The solid elements to convert. |
| `COQUE_SOLIDE / GROUP_MA_SURF` | element group, optional, list | — | The top or bottom surface of the shell, used to orient the converted hexahedra (`orieHexa9` is called per occurrence). Required when the mesh has `HEXA8`; not needed for `PENTA6`, whose `TRIA3` faces mark top and bottom (U4.23.02 §4.9). |
| `QUAD_LINE` | factor keyword, optional | — | *quadratic to linear*. Quadratic to linear conversion: removes mid-side and center nodes. Use it to obtain a linear mesh for a linear element formulation, or to locate mesh defects (advice of `MODELISA4_10`). Example: `upstream/astest/sslv130a.comm:1399`. |
| `QUAD_LINE / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Convert the whole mesh (default). |
| `QUAD_LINE / GROUP_MA` | element group, optional, list | — | *element group*. Convert only these elements (warning `MESH1_4`). |
| `REPERE` | factor keyword, optional | — | *coordinate system*. Change of coordinate system used to determine the properties of a beam section: moves a beam cross-section mesh to the origin and axes given by its section properties. Use it in beam-section workflows; no upstream test case calls it directly in 17.4.26. |
| `REPERE / TABLE` | `table_sdaster`, required | — | *table*. Name of the table of geometric properties of the section (center of gravity, torsion center, principal axes), made by `POST_ELEM` with `CARA_GEOM` or `CARA_POUTRE`. `MACR_CARA_POUTRE` uses this feature to compute the warping constant (U4.23.02 §4.12). |
| `REPERE / NOM_ORIG` | text, optional | — | Origin of the new coordinate system. One of `'CDG'`, `'TORSION'`. Center of gravity or torsion (shear) center of the section. |
| `REPERE / NOM_ROTA` | text, optional | — | Direction of the coordinate system. One of `'INERTIE'`. Align the axes with the principal axes of inertia. |
| `REPERE / GROUP_MA` | element group, optional | — | *element group*. Name of the element group whose center of gravity becomes the origin of the new coordinate system. Only when `equal_to("NOM_ORIG", 'CDG')`. |
| `DECOUPE_LAC` | factor keyword, optional | — | Creates LAC patches for contact: cuts the elements under the contact surface so that the LAC contact method can be used. Use it only for `DEFI_CONTACT` with the LAC method. After it, `MODI_MAILLAGE` may only move nodes (`MESH1_12`). Example: `upstream/astest/zzzz383d.comm:29`. |
| `DECOUPE_LAC / GROUP_MA_ESCL` | element group, required, list | — | *secondary element group*. The secondary contact surface to cut into patches. |
| `DECOUPE_LAC / DECOUPE_HEXA` | text, optional | `'PYRA'` | One of `'PYRA'`, `'HEXA'`. How the hexahedra under the surface are cut: into pyramids or into hexahedra (`upstream/astest/zzzz383c.comm:33`). `'PYRA'` adds the fewest nodes; `'HEXA'` helps when pyramids in the mesh are a problem (U4.23.02 §4.18). `DECOUPE_LAC` must be the last command acting on the mesh. |
| `ECLA_PG` | factor keyword, optional | — | Splits the elements into small elements that each contain a single Gauss point. Use it to visualize fields at Gauss points (`*_ELGA`): each value gets its own small element. `MAILLAGE` is not needed: the mesh comes from `MODELE`. No upstream test case calls it directly in 17.4.26. |
| `ECLA_PG / MODELE` | `modele_sdaster`, required | — | *model*. The model whose Gauss points are used. |
| `ECLA_PG / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Every element of the model. |
| `ECLA_PG / GROUP_MA` | element group, optional, list | — | *element group*. Only these elements. |
| `ECLA_PG / SHRINK` | real, optional | `0.9` | Reduction factor. Shrinks each sub-element so that the pieces are visibly separate. |
| `ECLA_PG / TAILLE_MIN` | real, optional | `0.0` | Minimum side length of the sub-elements. |
| `ECLA_PG / NOM_CHAM` | text, required, list | — | *field name*. One of `'DEGE_ELGA'`, `'DEPL_ELGA'`, `'DERA_ELGA'`, `'DIFF_ELGA'`, `'DISS_ELGA'`, `'EFGE_ELGA'`, `'ENDO_ELGA'`, `'ENEL_ELGA'`, `'EPEQ_ELGA'`, `'EPFD_ELGA'`, `'EPFP_ELGA'`, `'EPGQ_ELGA'`, … (50 values; see the .json). The Gauss-point fields to prepare the split mesh for. |
| `TITRE` | text, optional | — | *title*. Title stored with the new mesh. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `2` prints more detail about the new mesh. |

2 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: exactly one of `COQU_VOLU`, `CREA_FISS`, `CREA_MAILLE`, `CREA_POI1`, `ECLA_PG`, `HEXA20_27`, `LINE_QUAD`, `MODI_MAILLE`, `QUAD_LINE`, `REPERE`, `RESTREINT`, `PENTA15_18`, `GEOM_FIBRE`, `DECOUPE_LAC`, `MODI_HHO`, `COQUE_SOLIDE`, `RAFFINEMENT` must be given (`UN_PARMI`).
- `CREA_POI1`: at least one of `TOUT`, `GROUP_MA`, `GROUP_NO`, `NOEUD` must be given (`AU_MOINS_UN`).
- `CREA_MAILLE`: exactly one of `TOUT`, `GROUP_MA` must be given; if none is given, `TOUT='OUI'` is assumed (`UN_PARMI`).
- `MODI_MAILLE`: at least one of `TOUT`, `MAILLE`, `GROUP_MA` must be given (`AU_MOINS_UN`).
- `LINE_QUAD`: exactly one of `TOUT`, `GROUP_MA` must be given; if none is given, `TOUT='OUI'` is assumed (`UN_PARMI`).
- `HEXA20_27`: exactly one of `TOUT`, `GROUP_MA` must be given; if none is given, `TOUT='OUI'` is assumed (`UN_PARMI`).
- `PENTA15_18`: exactly one of `TOUT`, `GROUP_MA` must be given; if none is given, `TOUT='OUI'` is assumed (`UN_PARMI`).
- `QUAD_LINE`: exactly one of `TOUT`, `GROUP_MA` must be given; if none is given, `TOUT='OUI'` is assumed (`UN_PARMI`).
- `DECOUPE_LAC`: at least one of `GROUP_MA_ESCL` must be given (`AU_MOINS_UN`).

One transformation per call: chain calls for several (for example `LINE_QUAD`, then
`CREA_POI1`).

## Patterns

### Linear mesh to quadratic

Source: `upstream/astest/ssls04d.comm:29`.

```python
MA = CREA_MAILLAGE(MAILLAGE=M, LINE_QUAD=_F(TOUT="OUI"))
```

### Point elements for discrete masses or springs

`P` is a node group; the new POI1 elements go into element group `P`, which then receives a
discrete modeling type and a `DISCRET_2D` mass (`upstream/astest/sdld110a.comm:39`, `:48`).

Source: `upstream/astest/sdld110a.comm:31`.

```python
MA = CREA_MAILLAGE(MAILLAGE=MA, CREA_POI1=(_F(NOM_GROUP_MA="P", GROUP_NO="P"),))
```

### Seven-node triangles for `COQUE_3D`

Source: `upstream/astest/sdls504a.comm:33`.

```python
MAIL = CREA_MAILLAGE(MAILLAGE=MA, MODI_MAILLE=_F(TOUT="OUI", OPTION="TRIA6_7"))
```

### Keep one part of the mesh

`TOUT_GROUP_MA='OUI'` keeps the other element groups, restricted to `VOLAA`.

Source: `upstream/astest/zzzz236a.comm:57`.

```python
MNA1 = CREA_MAILLAGE(MAILLAGE=MA0, RESTREINT=_F(GROUP_MA="VOLAA", TOUT_GROUP_MA="OUI"))
```

### Uniform refinement

Source: `upstream/astest/mesh001h.py:30`.

```python
mesh = CREA_MAILLAGE(MAILLAGE=mesh_init, RAFFINEMENT=_F(TOUT="OUI", NIVEAU=2), INFO=1)
```

## Pitfalls

- **New mid-side nodes lie on straight edges.** `LINE_QUAD` places each new node at the
  barycenter of its edge (`upstream/bibfor/prepost/crea_maillage_module.F90:2489`), so a curved
  boundary meshed with linear elements stays faceted after conversion. For curved geometry,
  generate the quadratic mesh in the mesher instead.
- **Partial conversions can break conformity.** Converting only some groups (`GROUP_MA` in
  `LINE_QUAD`, `QUAD_LINE`, `HEXA20_27`, `PENTA15_18`, `MODI_MAILLE`) gives warning `MESH1_4`:
  neighboring linear and quadratic elements then do not share their mid-side nodes. Convert the
  whole mesh unless the interface is handled otherwise.
- **`RESTREINT` drops node groups by default.** With the default `TOUT_GROUP_NO='NON'` and no
  `GROUP_NO`, the new mesh has no node groups (`upstream/bibfor/calculel/rdtmai.F90`), and
  boundary conditions given by `GROUP_NO` then fail. Set `TOUT_GROUP_NO='OUI'` (and
  `TOUT_GROUP_MA='OUI'`) to keep the groups, as the Python helper `Mesh.restrict` does
  (`upstream/code_aster/ObjectsExt/mesh_ext.py`).
- **No conversion of a mesh that carries curvilinear abscissas.** `LINE_QUAD`, `QUAD_LINE`,
  `COQUE_SOLIDE`, `MODI_HHO` and `RAFFINEMENT` stop with `MESH1_8` if
  `MODI_MAILLAGE/ABSC_CURV` was run on the mesh; they also refuse meshes with macro-elements
  (`MESH1_7`). Run `ABSC_CURV` on the derived mesh instead.
- **POI1 without a group is unreachable.** `CREA_POI1` without `NOM_GROUP_MA` creates the
  elements but puts them in no group.
- **The old mesh is not updated.** The result is a separate object; models and fields built on
  the source mesh do not apply to it. Rebinding the same Python name, as in
  `MA = CREA_MAILLAGE(MAILLAGE=MA, ...)` (`upstream/astest/sdld110a.comm:31`), is allowed and is
  the clearest way to avoid using the old mesh by mistake.

## See also

- French reference: U4.23.02 (French text: `en/docs/_src/U4.23.02.fr.md`; translation: `en/docs/U4.23.02.md`)
- Catalog: `en/commands/CREA_MAILLAGE.json` (generated from `upstream/code_aster/Cata/Commands/crea_maillage.py:38`)
- Implementation: `upstream/bibfor/op/op0167.F90`, `upstream/code_aster/CodeCommands/crea_maillage.py`
- Related: `LIRE_MAILLAGE`, `MODI_MAILLAGE`, `DEFI_GROUP`, `AFFE_MODELE` (modeling type decides
  the element types needed), `AFFE_CARA_ELEM` (`DISCRET` on POI1)
- Example: `upstream/astest/mesh001h.py` (lines 30)
- Example: `upstream/astest/zzzz383d.comm` (lines 29, 50, 69)
- Example: `upstream/astest/ssls147a.comm` (lines 27)
