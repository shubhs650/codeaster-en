---
command: DEFI_GROUP
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/defi_group.py:42
doc_fr: U4.22.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3a)
examples: [mesh001e, zzzz360a, zzzz238a, ssnp168a, ssnp110c, forma04a, ssnv183a, sslx300f, zzzz258a, zzzz510a, ssnp131a]
---

# DEFI_GROUP — define groups

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.

`DEFI_GROUP` adds element groups and node groups to an existing mesh, or deletes them. Every
later command addresses parts of the model through these groups (`GROUP_MA`, `GROUP_NO`), so
this is where the analyst decides which elements carry a material, which nodes are fixed, where
a load acts and where results are read. New groups are built from existing groups (copy,
union, intersection, difference, the nodes of an element group), from geometry (elements or
nodes inside a sphere, cylinder, band or plane, faces with a given normal), or as an ordered
node path along a line for result plots. The mesh is modified in place and returned: write
`MA = DEFI_GROUP(reuse=MA, MAILLAGE=MA, ...)`.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Définition de nouveaux groupes de noeuds et/ou de mailles dans un concept maillage» |
| Kind | `OPER` |
| Result | `maillage_sdaster`, `squelette`, `grille_sdaster`, `maillage_p` (depends on the keywords given) |
| Can reuse its input (`reuse=`) | yes (the object given in `MAILLAGE`, `GRILLE`); catalog `reentrant='o:MAILLAGE|GRILLE'` |
| French reference | U4.22.01 — from en/doc-ids.yaml (status: proposed) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `CREA_GROUP_MA`, `CREA_GROUP_NO`, `TOUT`, `UNION`, `INTERSEC`, `DIFFE`, `OPTION`, `NOEUD_ORDO`, `SPHERE`, `BANDE` |

## Order of operations

Within one call the solver first deletes groups (`DETR_GROUP_MA`, `DETR_GROUP_NO`), then
creates element groups (`CREA_GROUP_MA`), then node groups (`CREA_GROUP_NO`)
(`upstream/bibfor/op/op0104.F90:75`, `:141`, `:144`). Occurrences of a factor keyword are
processed in order. So a `CREA_GROUP_NO` occurrence can use an element group created by
`CREA_GROUP_MA` in the same call, or a node group created by an earlier `CREA_GROUP_NO`
occurrence (as in `upstream/astest/mesh001e.py:30`), and a deleted name can be reused at once.

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MAILLAGE` | `maillage_sdaster` or `squelette`, optional | — | *mesh*. The mesh to add groups to. It is modified in place and is also the result (`upstream/code_aster/CodeCommands/defi_group.py:39`). Give this or `GRILLE`. |
| `GRILLE` | `grille_sdaster`, optional | — | A grid object (`grille_sdaster`) instead of a mesh. TODO(verify): grids come from `DEFI_GRILLE` (XFEM auxiliary grid); not needed for standard structural models. |
| `DETR_GROUP_MA` | factor keyword, optional, repeatable | — | Deletes element groups. Use it to free a name before re-creating the group, since creating a group whose name exists is a fatal error (`ALGELINE3_7`). |
| `DETR_GROUP_MA / NOM` | text, required, list | — | Names of the element groups to delete. |
| `DETR_GROUP_NO` | factor keyword, optional, repeatable | — | Deletes node groups. Same use as `DETR_GROUP_MA` (the fatal error for an existing node group name is `SOUSTRUC_37`). |
| `DETR_GROUP_NO / NOM` | text, required, list | — | Names of the node groups to delete. |
| `CREA_GROUP_MA` | factor keyword, optional, repeatable | — | *create element groups*. One occurrence per new element group. Exactly one selector per occurrence: `TOUT`, `GROUP_MA`, `UNION`, `INTERSEC`, `DIFFE` or `OPTION` (catalog rule). |
| `CREA_GROUP_MA / NOM` | text, required | — | Name of the new element group (24 characters at most, the name length that the MED reader keeps; see `LIRE_MAILLAGE`). It must not exist yet (`ALGELINE3_7`). |
| `CREA_GROUP_MA / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. All elements of the mesh; combine with `TYPE_MAILLE` to keep one dimension or element type, for example all solid elements (`upstream/astest/sslx300f.comm:35`). |
| `CREA_GROUP_MA / GROUP_MA` | element group, optional | — | *element group*. One existing group to copy, filter (`TYPE_MAILLE`) or take part of (`NUME_INIT`, `POSITION`). |
| `CREA_GROUP_MA / INTERSEC` | element group, optional, list | — | *intersection of groups*. Elements present in every listed group. |
| `CREA_GROUP_MA / UNION` | element group, optional, list | — | *union of groups*. Elements present in at least one listed group. Use it to address several regions with one name. |
| `CREA_GROUP_MA / DIFFE` | element group, optional, list | — | *difference of groups*. Elements of the first listed group that are in none of the others (`upstream/bibfor/soustruc/sscgma.F90`, `DIFFE` branch). Order matters. |
| `CREA_GROUP_MA / TYPE_MAILLE` | text, optional | `'TOUT'` | One of `'TOUT'`, `'1D'`, `'2D'`, `'3D'`, `'POI1'`, `'SEG2'`, `'SEG3'`, `'SEG4'`, `'TRIA3'`, `'TRIA6'`, `'TRIA7'`, `'QUAD4'`, … (24 values; see the .json). Filter applied after the selection: keep only elements of this topological dimension (`'1D'`, `'2D'`, `'3D'`) or this element type. Use it to split a mixed group, for example the solid elements from their boundary faces. See Pitfalls for what happens when nothing matches. |
| `CREA_GROUP_MA / OPTION` | text, optional | — | *option*. One of `'FACE_NORMALE'`, `'SPHERE'`, `'CYLINDRE'`, `'BANDE'`, `'APPUI'`, `'FISS_XFEM'`. Geometric or topological selection, detailed in the rows below. |
| `CREA_GROUP_MA / NUME_INIT` | integer, optional | — | Range: ≥ 1. Only when `exists("GROUP_MA")`. Position in `GROUP_MA` of the first element to take (default 1). Use with `NUME_FIN` to take a contiguous slice of a group. |
| `CREA_GROUP_MA / POSITION` | text, optional | — | One of `'INIT'`, `'FIN'`, `'MILIEU'`. Only when `exists("GROUP_MA")`. Takes one element of `GROUP_MA`: the first, the last, or the middle one (position (n+1)/2) in the group's stored order (`upstream/bibfor/soustruc/sscgma.F90:243`). |
| `CREA_GROUP_MA / NUME_FIN` | integer, optional | — | Range: ≥ 1. Only when `exists("GROUP_MA") and exists("NUME_INIT")`. Position of the last element to take (default: the end of the group). Smaller than `NUME_INIT` (`SOUSTRUC_33`) or beyond the group size (`SOUSTRUC_34`) is a fatal error. |
| `CREA_GROUP_MA / ANGL_NAUT` | real, optional, list of up to 2 | — | Only when `equal_to("OPTION", 'FACE_NORMALE')`; or `equal_to("OPTION", 'CYLINDRE')`; or `equal_to("OPTION", 'BANDE')`. The reference direction as nautical angles in degrees (1 angle in 2D, 2 in 3D). Alternative to `VECT_NORMALE`. |
| `CREA_GROUP_MA / VECT_NORMALE` | real, optional, list of up to 3 | — | Only when `equal_to("OPTION", 'FACE_NORMALE')`; or `equal_to("OPTION", 'CYLINDRE')`; or `equal_to("OPTION", 'BANDE')`. The reference direction as a vector: the face normal sought (`FACE_NORMALE`), the cylinder axis (`CYLINDRE`), or the normal to the band's mid-plane (`BANDE`). |
| `CREA_GROUP_MA / ANGL_PREC` | real, optional | `0.5` | Only when `equal_to("OPTION", 'FACE_NORMALE')`. Angular tolerance in degrees: a face is kept when its normal is within this angle of the reference direction (`upstream/bibfor/modelisa/cgmafn.F90`). The face normal is computed from its first three nodes. Raise it for faceted curved faces. |
| `CREA_GROUP_MA / VERI_SIGNE` | text, optional | `'OUI'` | One of `'OUI'`, `'NON'`. Only when `equal_to("OPTION", 'FACE_NORMALE')`. `'OUI'`: the face normal must point the same way as the reference direction. `'NON'`: either sense is accepted, so faces facing both ways are taken. |
| `CREA_GROUP_MA / POINT` | real, optional, list of up to 3 | — | *reference point*. Only when `equal_to("OPTION", 'SPHERE')`; or `equal_to("OPTION", 'CYLINDRE')`; or `equal_to("OPTION", 'BANDE')`. Center of the sphere, a point on the cylinder axis, or a point on the band's mid-plane, given by coordinates. |
| `CREA_GROUP_MA / GROUP_NO_CENTRE` | node group, optional | — | Only when `equal_to("OPTION", 'SPHERE')`; or `equal_to("OPTION", 'CYLINDRE')`. Same as `POINT`, given as a node group instead of coordinates. |
| `CREA_GROUP_MA / RAYON` | real, required | — | Only when `equal_to("OPTION", 'SPHERE')`; or `equal_to("OPTION", 'CYLINDRE')`. Radius of the sphere or cylinder. |
| `CREA_GROUP_MA / CRIT_NOEUD` | text, optional | `'AU_MOINS_UN'` | One of `'TOUS'`, `'AU_MOINS_UN'`, `'MAJORITE'`. Only when `equal_to("OPTION", 'SPHERE')`; or `equal_to("OPTION", 'CYLINDRE')`; or `equal_to("OPTION", 'BANDE')`. How many nodes of an element must lie inside the region for the element to be taken: at least one (default), all (`'TOUS'`), or at least half (`'MAJORITE'`) (`upstream/bibfor/modelisa/cgmasp.F90:193`–`230`). Use `'TOUS'` to stay strictly inside the region. |
| `CREA_GROUP_MA / GROUP_NO_CENTRE` | node group, optional | — | Only when `equal_to("OPTION", 'BANDE')`. A point on the band's mid-plane, given as a node group. |
| `CREA_GROUP_MA / DIST` | real, required | — | Only when `equal_to("OPTION", 'BANDE')`. Half-thickness of the band: the distance from the mid-plane to each of the two bounding planes (`upstream/bibfor/modelisa/cgmaba.F90`). |
| `CREA_GROUP_MA / GROUP_NO` | node group, optional, list | — | *node group*. Only when `equal_to("OPTION", 'APPUI')`. The nodes on which the elements must rest. |
| `CREA_GROUP_MA / TYPE_APPUI` | text, required | — | One of `'AU_MOINS_UN'`, `'TOUT'`, `'SOMMET'`, `'MAJORITE'`. Only when `equal_to("OPTION", 'APPUI')`. An element is taken when at least one of its nodes, all its nodes, all its corner nodes, or more than half its nodes are in `GROUP_NO` (`upstream/bibfor/modelisa/cgmaap.F90`). `'SOMMET'` is the one to use on quadratic meshes to get the faces of a node set. |
| `CREA_GROUP_MA / TYPE_GROUP` | text, optional | `'XFEM'` | One of `'HEAVISIDE'`, `'CRACKTIP'`, `'MIXTE'`, `'FISSUREE'`, `'XFEM'`. Only when `equal_to("OPTION", 'FISS_XFEM')`. Which XFEM-enriched elements of the cracks to take, by enrichment type. XFEM only. |
| `CREA_GROUP_MA / FISSURE` | `fiss_xfem`, required, list | — | Only when `equal_to("OPTION", 'FISS_XFEM')`. The XFEM crack objects (`DEFI_FISS_XFEM`). |
| `CREA_GROUP_NO` | factor keyword, optional, repeatable | — | *create node groups*. One occurrence per new node group, except `GROUP_MA` / `TOUT_GROUP_MA`, which can create several at once. Without `OPTION`, exactly one of `TOUT_GROUP_MA`, `GROUP_MA`, `GROUP_NO`, `INTERSEC`, `UNION`, `DIFFE` (catalog rule). |
| `CREA_GROUP_NO / OPTION` | text, optional | — | *option*. One of `'ENV_SPHERE'`, `'ENV_CYLINDRE'`, `'PLAN'`, `'SEGM_DROI_ORDO'`, `'NOEUD_ORDO'`, `'TUNNEL'`, `'INCLUSION'`, `'FISS_XFEM'`, `'INTERVALLE_VALE'`, `'RELA_CINE_BP'`. Geometric or derived selection, detailed below. Without `OPTION`, the group is built from other groups. |
| `CREA_GROUP_NO / TOUT_GROUP_MA` | text, optional | — | One of `'OUI'`. Only when `not exists("OPTION")`. Creates, for every element group of the mesh, a node group with the same name holding its nodes. The quickest way to get node groups for boundary conditions from a mesh that only has element groups (`tests/fixtures/shell_static/input/run.comm:24`). |
| `CREA_GROUP_NO / GROUP_MA` | element group, optional, list | — | *element group*. Only when `not exists("OPTION")`; or `equal_to("OPTION", 'TUNNEL')`. Without `OPTION`: creates a node group of the nodes of each listed element group, named like the element group unless `NOM` is given (`tests/fixtures/solid_static/input/run.comm:18`). With `TUNNEL`: the elements whose nodes are candidates. |
| `CREA_GROUP_NO / GROUP_NO` | node group, optional, list | — | *node group*. Only when `not exists("OPTION")`; or `equal_to("OPTION", 'SEGM_DROI_ORDO')`. Without `OPTION`: one existing node group to copy or take part of (`NUME_INIT`, `POSITION`). With `SEGM_DROI_ORDO`: the nodes to sort along the segment. |
| `CREA_GROUP_NO / INTERSEC` | node group, optional, list | — | *intersection of groups*. Only when `not exists("OPTION")`. Nodes present in every listed node group, for example the nodes shared by two faces (an edge) as in `upstream/astest/mesh001e.py:30`. |
| `CREA_GROUP_NO / UNION` | node group, optional, list | — | *union of groups*. Only when `not exists("OPTION")`. Nodes present in at least one listed node group. |
| `CREA_GROUP_NO / DIFFE` | node group, optional, list | — | *difference of groups*. Only when `not exists("OPTION")`. Nodes of the first listed group that are in none of the others. Use it to avoid applying two boundary conditions to the same nodes. |
| `CREA_GROUP_NO / NOM` | text, optional, list | — | Only when `not exists("OPTION") and exists("GROUP_MA")`. Names for the node groups made from `GROUP_MA`: one name per element group, or a single name for one node group holding the nodes of all of them. Any other count is fatal (`MODELISA7_8`). Without `NOM`, each node group takes its element group's name. |
| `CREA_GROUP_NO / CRIT_NOEUD` | text, optional | `'TOUS'` | One of `'TOUS'`, `'SOMMET'`, `'MILIEU'`, `'CENTRE'`. Only when `not exists("OPTION") and exists("GROUP_MA")`. Which nodes of the elements to take: all of them (default), corner nodes only, mid-side nodes only, or face/volume center nodes only (`upstream/bibfor/modelisa/gmgnre.F90`). |
| `CREA_GROUP_NO / NUME_INIT` | integer, optional | — | Range: ≥ 1. Only when `not exists("OPTION") and exists("GROUP_NO")`. Position in `GROUP_NO` of the first node to take (default 1). |
| `CREA_GROUP_NO / POSITION` | text, optional | — | One of `'INIT'`, `'FIN'`, `'MILIEU'`. Only when `not exists("OPTION") and exists("GROUP_NO")`. Takes one node of `GROUP_NO`: the first, the last or the middle one in the group's stored order. Most useful on an ordered group (`NOEUD_ORDO`), where "first" and "last" are the ends of the path. |
| `CREA_GROUP_NO / NUME_FIN` | integer, optional | — | Range: ≥ 1. Only when `not exists("OPTION") and exists("GROUP_NO") and exists("NUME_INIT")`. Position of the last node to take (default: the end of the group). |
| `CREA_GROUP_NO / NOM` | text, required | — | Only when `not exists("OPTION") and not exists("GROUP_MA") and not exists("TOUT_GROUP_MA")`; or `equal_to("OPTION", 'ENV_SPHERE')`; or `equal_to("OPTION", 'ENV_CYLINDRE')`; or `equal_to("OPTION", 'PLAN')`; or `equal_to("OPTION", 'SEGM_DROI_ORDO')`; or `equal_to("OPTION", 'NOEUD_ORDO')`; or `equal_to("OPTION", 'TUNNEL')`; or `equal_to("OPTION", 'INCLUSION')`; or `equal_to("OPTION", 'FISS_XFEM')`; or `equal_to("OPTION", 'INTERVALLE_VALE')`. Name of the new node group. It must not exist yet (`SOUSTRUC_37`). |
| `CREA_GROUP_NO / POINT` | real, optional, list of up to 3 | — | *reference point*. Only when `equal_to("OPTION", 'ENV_SPHERE')`; or `equal_to("OPTION", 'ENV_CYLINDRE')`; or `equal_to("OPTION", 'PLAN')`. Center of the sphere, a point on the cylinder axis, or a point on the plane (a line in 2D). |
| `CREA_GROUP_NO / GROUP_NO_CENTRE` | node group, optional | — | Only when `equal_to("OPTION", 'ENV_SPHERE')`; or `equal_to("OPTION", 'ENV_CYLINDRE')`; or `equal_to("OPTION", 'PLAN')`. Same as `POINT`, given as a node group. |
| `CREA_GROUP_NO / RAYON` | real, required | — | Only when `equal_to("OPTION", 'ENV_SPHERE')`; or `equal_to("OPTION", 'ENV_CYLINDRE')`; or `equal_to("OPTION", 'TUNNEL')`. Radius of the sphere or cylinder surface, or of the tunnel. |
| `CREA_GROUP_NO / PRECISION` | real, required | — | *tolerance*. Only when `equal_to("OPTION", 'ENV_SPHERE')`; or `equal_to("OPTION", 'ENV_CYLINDRE')`; or `equal_to("OPTION", 'PLAN')`; or `equal_to("OPTION", 'SEGM_DROI_ORDO')`. Distance tolerance. For `ENV_SPHERE` a node is kept when its distance to the center differs from `RAYON` by at most `PRECISION` (`upstream/bibfor/modelisa/cgnoes.F90:167`); `ENV_CYLINDRE` and `PLAN` work the same way with the distance to the axis or to the plane. So `RAYON=0` with a small `PRECISION` selects the nodes at a point. For `ENV_SPHERE` it must be strictly positive (`MODELISA3_91`). |
| `CREA_GROUP_NO / ANGL_NAUT` | real, optional, list of up to 3 | — | Only when `equal_to("OPTION", 'ENV_CYLINDRE')`; or `equal_to("OPTION", 'PLAN')`. Cylinder axis, or normal to the plane, as nautical angles in degrees. Alternative to `VECT_NORMALE`. |
| `CREA_GROUP_NO / VECT_NORMALE` | real, optional, list of up to 3 | — | Only when `equal_to("OPTION", 'ENV_CYLINDRE')`; or `equal_to("OPTION", 'PLAN')`. Cylinder axis, or normal to the plane (to the line in 2D), as a vector. |
| `CREA_GROUP_NO / GROUP_NO_ORIG` | node group, required | — | Only when `equal_to("OPTION", 'SEGM_DROI_ORDO')`. Start node of the segment. |
| `CREA_GROUP_NO / GROUP_NO_EXTR` | node group, required | — | Only when `equal_to("OPTION", 'SEGM_DROI_ORDO')`. End node of the segment. |
| `CREA_GROUP_NO / CRITERE` | text, required | — | *tolerance type*. One of `'ABSOLU'`, `'RELATIF'`. Only when `equal_to("OPTION", 'SEGM_DROI_ORDO')`. Whether `PRECISION` is an absolute distance or relative to the segment length. TODO(verify) the relative reference length in `oreino.F90`. |
| `CREA_GROUP_NO / GROUP_MA` | element group, required, list | — | *element group*. Only when `equal_to("OPTION", 'NOEUD_ORDO')`; or `equal_to("OPTION", 'INCLUSION')`. For `NOEUD_ORDO`: line elements (SEG2/SEG3/SEG4, all of one type) that form one continuous line without branches (`upstream/bibfor/elements/cgnoor.F90`). For `INCLUSION`: the elements whose nodes are tested. |
| `CREA_GROUP_NO / GROUP_NO_ORIG` | node group, optional | — | Only when `equal_to("OPTION", 'NOEUD_ORDO')`; or `equal_to("OPTION", 'TUNNEL')`. `NOEUD_ORDO`: the start of the path, which fixes its direction; if omitted the code picks one of the two ends (catalog comment, `defi_group.py:309`). `TUNNEL`: the start of the axis. |
| `CREA_GROUP_NO / GROUP_NO_EXTR` | node group, optional | — | Only when `equal_to("OPTION", 'NOEUD_ORDO')`. The end of the path. For a closed line, give the same node as `GROUP_NO_ORIG`. |
| `CREA_GROUP_NO / VECT_ORIE` | real, optional, list of up to 3 | — | Only when `equal_to("OPTION", 'NOEUD_ORDO')`. For a closed line: a vector giving the direction of travel from the origin (catalog comment). |
| `CREA_GROUP_NO / ORIGINE` | text, optional | — | One of `'SANS'`. Only when `equal_to("OPTION", 'NOEUD_ORDO')`. For a closed line with no `GROUP_NO_ORIG`: lets the code choose any node as origin (catalog comment). |
| `CREA_GROUP_NO / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Only when `equal_to("OPTION", 'TUNNEL')`. Candidate nodes are those of the whole mesh. |
| `CREA_GROUP_NO / GROUP_MA_AXE` | element group, optional, list | — | Only when `equal_to("OPTION", 'TUNNEL')`. Line elements that form the tunnel axis. `TUNNEL` keeps the nodes within `RAYON` of this axis (`upstream/bibfor/modelisa/cgnofu.F90`); it was written for tunnels bored in a concrete mesh. |
| `CREA_GROUP_NO / LONGUEUR` | real, optional | — | *length*. Only when `equal_to("OPTION", 'TUNNEL')`. Length of axis to process, from `GROUP_NO_ORIG`. |
| `CREA_GROUP_NO / CAS_FIGURE` | text, required | — | One of `'2D'`, `'3D'`, `'2.5D'`. Only when `equal_to("OPTION", 'INCLUSION')`. Geometric case for the point-in-element search: 2D elements, 3D elements, or surface elements in 3D space (`'2.5D'`) (`upstream/bibfor/modelisa/cgnoin.F90:133`). |
| `CREA_GROUP_NO / DISTANCE_MAX` | real, optional | — | Only when `equal_to("OPTION", 'INCLUSION')`. Distance within which a node counts as inside an element of `GROUP_MA_INCL`. Default: 1 % of the shortest edge of that mesh, so that nodes on element boundaries are kept (`upstream/bibfor/modelisa/cgnoin.F90:118`). |
| `CREA_GROUP_NO / GROUP_MA_INCL` | element group, required, list | — | Only when `equal_to("OPTION", 'INCLUSION')`. Keeps the nodes of `GROUP_MA` that lie geometrically inside these elements (catalog help of the bloc). |
| `CREA_GROUP_NO / MAILLAGE_INCL` | `maillage_sdaster`, optional | — | Only when `equal_to("OPTION", 'INCLUSION')`. Another mesh that holds `GROUP_MA_INCL`, when it is not the mesh being modified. |
| `CREA_GROUP_NO / TYPE_GROUP` | text, required | — | One of `'HEAVISIDE'`, `'CRACKTIP'`, `'MIXTE'`, `'XFEM'`, `'ZONE_MAJ'`, `'TORE'`. Only when `equal_to("OPTION", 'FISS_XFEM')`. Which XFEM nodes of the cracks to take, by enrichment type. XFEM only. |
| `CREA_GROUP_NO / FISSURE` | `fiss_xfem`, required, list | — | Only when `equal_to("OPTION", 'FISS_XFEM')`. The XFEM crack objects. |
| `CREA_GROUP_NO / RAYON_TORE` | real, required | — | Range: ≥ 0.0. Only when `equal_to("OPTION", 'FISS_XFEM') and equal_to("TYPE_GROUP", 'TORE')`. Radius of the torus around the crack front within which nodes are taken. XFEM only. |
| `CREA_GROUP_NO / CHAM_GD` | `cham_no_sdaster`, required | — | *field (physical quantity)*. Only when `equal_to("OPTION", 'INTERVALLE_VALE')`. A nodal field; nodes are selected by the value of one of its components. |
| `CREA_GROUP_NO / NOM_CMP` | text, required | — | *component name*. Only when `equal_to("OPTION", 'INTERVALLE_VALE')`. The component tested, for example `'DX'` or `'TEMP'`. |
| `CREA_GROUP_NO / VALE` | real, required, list of up to 2, at least 2 | — | *value(s)*. Only when `equal_to("OPTION", 'INTERVALLE_VALE')`. The interval `(min, max)`: a node is kept when min ≤ value ≤ max (`upstream/bibfor/modelisa/cgnoiv.F90:111`). |
| `CREA_GROUP_NO / CABLE_BP` | `cabl_precont`, required | — | Only when `equal_to("OPTION", 'RELA_CINE_BP')`. A prestressing cable object from `DEFI_CABLE_BP`. Creates one node group per set of kinematic relations that the cable defines (`upstream/bibfor/modelisa/cgrcbp.F90`). |
| `CREA_GROUP_NO / PREF_GRNO` | text, optional | `'RCBP'` | Only when `equal_to("OPTION", 'RELA_CINE_BP')`. Prefix of the names of the node groups created by `RELA_CINE_BP`. |
| `ALARME` | text, optional | `'OUI'` | One of `'OUI'`, `'NON'`. `'NON'` silences the warnings for groups that come out empty (`SOUSTRUC_36`, `SOUSTRUC_38`) in the boolean and filter selections (`upstream/bibfor/soustruc/sscgma.F90:111`). Keep `'OUI'`: an empty group usually means a wrong name or tolerance. |
| `INFO` | integer, optional | — | *verbosity*. One of `1`, `2`. At level 1 the log lists each new group and its size (see the excerpt below); at level 2 it also lists the members of each group (`upstream/bibfor/soustruc/sscgno.F90`). |

7 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed. Among them
are `MAILLE` and `NOEUD`, which select by element or node name; they still work on ordinary
meshes (`upstream/astest/zzzz360a.comm:24` uses them) but are refused on parallel meshes
(`MODELISA7_86`). Generated command files should use groups only.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at least one of `CREA_GROUP_MA`, `CREA_GROUP_NO`, `DETR_GROUP_NO`, `DETR_GROUP_MA` must be given (`AU_MOINS_UN`).
- command: exactly one of `MAILLAGE`, `GRILLE` must be given (`UN_PARMI`).
- `CREA_GROUP_MA`: exactly one of `TOUT`, `GROUP_MA`, `MAILLE`, `INTERSEC`, `UNION`, `DIFFE`, `OPTION` must be given (`UN_PARMI`).
- when `exists("GROUP_MA")`: at most one of `POSITION`, `NUME_INIT` may be given (`EXCLUS`).
- when `equal_to("OPTION", 'FACE_NORMALE')`: exactly one of `ANGL_NAUT`, `VECT_NORMALE` must be given (`UN_PARMI`).
- when `equal_to("OPTION", 'SPHERE')`: exactly one of `POINT`, `NOEUD_CENTRE`, `GROUP_NO_CENTRE` must be given (`UN_PARMI`).
- when `equal_to("OPTION", 'CYLINDRE')`: exactly one of `POINT`, `NOEUD_CENTRE`, `GROUP_NO_CENTRE` must be given (`UN_PARMI`).
- when `equal_to("OPTION", 'CYLINDRE')`: exactly one of `ANGL_NAUT`, `VECT_NORMALE` must be given (`UN_PARMI`).
- when `equal_to("OPTION", 'BANDE')`: exactly one of `POINT`, `NOEUD_CENTRE`, `GROUP_NO_CENTRE` must be given (`UN_PARMI`).
- when `equal_to("OPTION", 'BANDE')`: exactly one of `ANGL_NAUT`, `VECT_NORMALE` must be given (`UN_PARMI`).
- when `equal_to("OPTION", 'APPUI')`: exactly one of `NOEUD`, `GROUP_NO` must be given (`UN_PARMI`).
- when `not exists("OPTION")`: exactly one of `TOUT_GROUP_MA`, `GROUP_MA`, `GROUP_NO`, `NOEUD`, `INTERSEC`, `UNION`, `DIFFE` must be given (`UN_PARMI`).
- when `exists("GROUP_NO")`: at most one of `POSITION`, `NUME_INIT` may be given (`EXCLUS`).
- when `equal_to("OPTION", 'ENV_SPHERE')`: exactly one of `POINT`, `NOEUD_CENTRE`, `GROUP_NO_CENTRE` must be given (`UN_PARMI`).
- when `equal_to("OPTION", 'ENV_CYLINDRE')`: exactly one of `POINT`, `NOEUD_CENTRE`, `GROUP_NO_CENTRE` must be given (`UN_PARMI`).
- when `equal_to("OPTION", 'ENV_CYLINDRE')`: exactly one of `ANGL_NAUT`, `VECT_NORMALE` must be given (`UN_PARMI`).
- when `equal_to("OPTION", 'PLAN')`: exactly one of `POINT`, `NOEUD_CENTRE`, `GROUP_NO_CENTRE` must be given (`UN_PARMI`).
- when `equal_to("OPTION", 'PLAN')`: exactly one of `ANGL_NAUT`, `VECT_NORMALE` must be given (`UN_PARMI`).
- when `equal_to("OPTION", 'TUNNEL')`: at least one of `TOUT`, `GROUP_MA`, `MAILLE` must be given (`AU_MOINS_UN`).

## Patterns

### Node groups from element groups

Meshers usually export element groups only, while boundary conditions and result extraction
often need node groups. Either convert the groups you need, or all of them at once.

Source: `tests/fixtures/solid_static/input/run.comm:18` and
`tests/fixtures/shell_static/input/run.comm:24`.

```python
MAIL = DEFI_GROUP(reuse=MAIL, MAILLAGE=MAIL, CREA_GROUP_NO=_F(GROUP_MA="BASE"))

MAIL = DEFI_GROUP(reuse=MAIL, MAILLAGE=MAIL, CREA_GROUP_NO=_F(TOUT_GROUP_MA="OUI"))
```

The log lists what was created (`tests/fixtures/shell_static/output/run.mess`; "number of node
groups created", then name and node count per group):

```text
NOMBRE  DE GROUPES DE NOEUDS CREES :      5
               !  CORNER_A                     !         1          !
               !  CORNER_B                     !         1          !
               !  CENTER                       !         1          !
               !  EDGES                        !        80          !
               !  PLATE                        !       441          !
```

### Combine groups

`LINEAIRE` is the union of two regions; `NON_LIN` is everything in `DEDANS` except them. The
second occurrence uses the group created by the first.

Source: `upstream/astest/ssnp168a.comm:35`.

```python
MAIL = DEFI_GROUP(
    reuse=MAIL,
    INFO=1,
    MAILLAGE=MAIL,
    CREA_GROUP_MA=(
        _F(NOM="LINEAIRE", UNION=("SINGU_H", "SINGU_B")),
        _F(NOM="NON_LIN", DIFFE=("DEDANS", "LINEAIRE")),
    ),
)
```

### Nodes on an edge shared by two faces

The first occurrence makes node groups `TOP` and `BOTTOM` from the element groups of the same
names; the second keeps their common nodes.

Source: `upstream/astest/mesh001e.py:30`.

```python
mesh = DEFI_GROUP(
    reuse=mesh,
    MAILLAGE=mesh,
    CREA_GROUP_NO=(_F(GROUP_MA=("TOP", "BOTTOM")), _F(NOM="TEST", INTERSEC=("TOP", "BOTTOM"))),
)
```

### The node at a given point

A sphere of radius 0 with a small tolerance selects the node at `(-a, 0)`, for example to
apply a point load or read a result there.

Source: `upstream/astest/ssnp110c.comm:217`.

```python
MA_XFEM = DEFI_GROUP(
    reuse=MA_XFEM,
    MAILLAGE=MA_XFEM,
    CREA_GROUP_NO=_F(
        OPTION="ENV_SPHERE", NOM="NTEST", POINT=(-a, 0.0), RAYON=0.0001, PRECISION=0.0001
    ),
)
```

### Ordered path for a result plot along a line

`NOEUD_ORDO` orders the nodes of the line `CONT1` from `C1`; `POST_RELEVE_T` then extracts a
stress component along it, and the table gets a curvilinear abscissa column (`ABSC_CURV`).

Source: `upstream/astest/forma04a.comm:83` and `:92`.

```python
MA = DEFI_GROUP(
    reuse=MA,
    MAILLAGE=MA,
    CREA_GROUP_NO=_F(OPTION="NOEUD_ORDO", NOM="CONT_ord", GROUP_MA="CONT1", GROUP_NO_ORIG="C1"),
)
```

### Faces with a given outward normal

Source: `upstream/astest/ssnv183a.comm:70`.

```python
EPROU = DEFI_GROUP(
    reuse=EPROU,
    MAILLAGE=EPROU,
    CREA_GROUP_MA=_F(NOM="FACE", OPTION="FACE_NORMALE", VECT_NORMALE=(0.0, 0.0, 1.0)),
)
```

### Nodes on a line (2D) or plane (3D)

Source: `upstream/astest/ssnp131a.comm:27`.

```python
MA = DEFI_GROUP(
    reuse=MA,
    MAILLAGE=MA,
    CREA_GROUP_NO=_F(
        NOM="LIGBE2", OPTION="PLAN", POINT=(0, 0), VECT_NORMALE=(0, 1), PRECISION=0.000010
    ),
)
```

## Pitfalls

- **Existing names are fatal.** Creating an element group or node group whose name already
  exists stops the run (`ALGELINE3_7`, `SOUSTRUC_37`; `upstream/bibfor/soustruc/sscgma.F90:120`,
  `sscgno.F90:165`). This includes `TOUT_GROUP_MA='OUI'` or `GROUP_MA` without `NOM` on a mesh
  whose file already holds a node group with the same name as an element group
  (`upstream/bibfor/utilitai/addGrpNo.F90:85`). Delete the old group with `DETR_GROUP_NO` /
  `DETR_GROUP_MA` in the same call, or choose another name.
- **Empty groups are not created.** When a selection finds nothing, the group is skipped with
  warning `SOUSTRUC_36` (elements) or `SOUSTRUC_38` (nodes), and the run continues. The first
  command that names the group then fails. Check tolerances (`PRECISION`, `RAYON`, `DIST`) and
  read the group table in the log.
- **`TYPE_MAILLE` that matches nothing keeps everything.** If no element of the selection has
  the requested type, the warning `SOUSTRUC_36` says the group is empty and not created, but the
  code then creates it with the unfiltered selection (`upstream/bibfor/modelisa/cgmftm.F90`
  returns the original list; `upstream/bibfor/soustruc/sscgma.F90:505`–`520`). With
  `ALARME='NON'` this happens silently. Check the element count in the log.
- **The mesh is modified in place even without `reuse=`.** The result object is the input mesh
  (`upstream/code_aster/CodeCommands/defi_group.py:39`); `upstream/astest/zzzz510a.py:39` writes
  `M = DEFI_GROUP(MAILLAGE=M, ...)` without `reuse`. A different result name does not make a
  copy.
- **`DIFFE` is order-dependent.** It removes the second and later groups from the first, so
  `DIFFE=("A", "B")` and `DIFFE=("B", "A")` differ.

## See also

- French reference: U4.22.01 (translation: `en/docs/U4.22.01.md` once task 5.x lands)
- Catalog: `en/commands/DEFI_GROUP.json` (generated from `upstream/code_aster/Cata/Commands/defi_group.py:42`)
- Implementation: `upstream/bibfor/op/op0104.F90`, `upstream/bibfor/soustruc/sscgma.F90`,
  `upstream/bibfor/soustruc/sscgno.F90`
- Related: `LIRE_MAILLAGE`, `MODI_MAILLAGE`, `CREA_MAILLAGE` (`RESTREINT`), `POST_RELEVE_T`
- Example: `upstream/astest/mesh001e.py` (lines 30)
- Example: `upstream/astest/zzzz360a.comm` (lines 24)
- Example: `upstream/astest/zzzz238a.comm` (lines 27)
