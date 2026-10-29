---
guide: modeling types
title: Modeling types and when to pick each
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
sources:
  - upstream/catalo/cataelem/Commons/phenomenons_modelisations.py
  - upstream/catalo/cataelem/Elements/
  - upstream/code_aster/Cata/Commands/affe_modele.py
  - upstream/code_aster/Cata/Commands/affe_cara_elem.py
  - upstream/code_aster/Cata/Commands/affe_char_meca.py
  - upstream/bibfor/elements/
  - upstream/astest/
  - tests/fixtures/
  - en/commands/AFFE_MODELE.md
  - en/commands/AFFE_CARA_ELEM.md
doc_fr: none (our own guide, not a translation)
status: assisted
method: assisted
reviewed_by:
reviewed_on:
written_by: agent, in session (task 2.4)
---

# Modeling types and when to pick each

> **Assisted guide.** Our own English note, written in session from the pinned element
> catalog, the element and command source, upstream test cases and our committed fixture runs.
> It is not a translation of an official document. Claims about what the solver does cite their
> source. Advice on which modeling type to choose is engineering judgement and is marked as
> such; where it rests on a threshold that should come from the official documentation, it
> says `TODO(verify)`. Not reviewed by an engineer.

In code_aster the choice of finite element is made in one place: the `MODELISATION` value of
each `AFFE` occurrence of [`AFFE_MODELE`](../commands/AFFE_MODELE.md). The value names a
kinematic idealization (3D solid, shell, plane stress, beam, ...). The solver then turns every
element of the assigned groups whose type that idealization supports into a finite element,
for example `TETRA4` into `MECA_TETRA4` under `3D`, and skips the others. Element types the
modeling cannot use are skipped with warning `MODELE1_70`, and a model with no finite element
at all stops with `MODELE1_6` (see the `AFFE_MODELE` reference).

The modeling type decides, all at once:

- which element types of the mesh are accepted (linear or quadratic, 1D, 2D or 3D);
- which degrees of freedom (DOF) the nodes carry, so which `DDL_IMPO` components exist;
- which element properties `AFFE_CARA_ELEM` must supply (shell thickness, beam section);
- which loads apply (`PRES_REP` on faces, `FORCE_COQUE` on shells, `FORCE_POUTRE` on beams);
- which result fields are meaningful (stresses `SIGM_*` for solids, generalized forces
  `EFGE_*` for shells and beams).

This guide covers the nine values PLAN.md task 2.4 names: `3D`, `3D_SI`, `DKT`, `DST`,
`COQUE_3D`, `C_PLAN`, `D_PLAN`, `AXIS` and `POU_D_T`. It also names the nearest alternatives
(`POU_D_E`, `DIS_T`, `DIS_TR`) where the choice is between them. The French values are the
solver's API and are never renamed; the English labels come from `en/glossary.yaml`.

## Summary table

"Line" is the line of the entry in
`upstream/catalo/cataelem/Commons/phenomenons_modelisations.py`, which lists the element types
each modeling accepts. DOFs come from the `DDL_MECA` definition in the element catalog file
named in each section below.

| `MODELISATION` | English label | Element types | DOFs per node | Needs in `AFFE_CARA_ELEM` | Main stress output | Line |
|---|---|---|---|---|---|---|
| `3D` | 3D solid | `HEXA8/20/27`, `PENTA6/15/18`, `PYRAM5/13`, `TETRA4/10`; faces `QUAD4/8/9`, `TRIA3/6`; edges `SEG2/3` | `DX`, `DY`, `DZ` | nothing | `SIGM_*`, `SIEQ_*` | 288 |
| `3D_SI` | 3D solid (reduced integration) | `HEXA8`, `HEXA20`, `TETRA10`; faces `QUAD4/8`, `TRIA6` | `DX`, `DY`, `DZ` | nothing | `SIGM_*`, `SIEQ_*` | 1448 |
| `DKT` | thin shell (DKT) | `TRIA3`, `QUAD4`; edges `SEG2` | `DX`..`DZ`, `DRX`..`DRZ` | `COQUE` (thickness, local axes) | `EFGE_*`; stresses by layer | 3946 |
| `DST` | thick shell (DST) | `TRIA3`, `QUAD4`; edges `SEG2` | `DX`..`DZ`, `DRX`..`DRZ` | `COQUE` | `EFGE_*`; stresses by layer | 3979 |
| `COQUE_3D` | 3D shell (quadratic) | `QUAD9`, `TRIA7`; edges `SEG3` | `DX`..`DRZ` on corner and mid-side nodes; `DRX`..`DRZ` only on the center node | `COQUE` | `EFGE_*`; stresses by layer | 3692 |
| `C_PLAN` | plane stress | `TRIA3/6`, `QUAD4/8/9`; edges `SEG2/3` | `DX`, `DY` | nothing | `SIGM_*`, `SIEQ_*` | 3718 |
| `D_PLAN` | plane strain | `TRIA3/6`, `QUAD4/8/9`; edges `SEG2/3` | `DX`, `DY` | nothing | `SIGM_*`, `SIEQ_*` | 3995 |
| `AXIS` | axisymmetric | `TRIA3/6`, `QUAD4/8/9`; edges `SEG2/3` | `DX` (radial), `DY` (axial) | nothing | `SIGM_*`, `SIEQ_*` | 1824 |
| `POU_D_T` | Timoshenko beam | `SEG2` only | `DX`..`DZ`, `DRX`..`DRZ` | `POUTRE` (section), optionally `ORIENTATION` | `EFGE_*` | 5373 |

Sources for the DOF column: `upstream/catalo/cataelem/Elements/meca_3d.py:33`,
`meca_3d_si_quad.py:33`, `meca_dkt.py:35`, `meca_dst.py:35`, `meca_coque_3d.py:58` (node sets
`EN1` / `EN2` at `:980` and `:996`), `meca_c_plan.py:33`, `meca_d_plan.py:33`, `meca_axis.py:33`,
`meca_pou_d_t.py:113`, all under `upstream/catalo/cataelem/Elements/`.

## How ClearFEA should choose

The procedure below is our recommendation for ClearFEA's job model and for the Phase 6 builder
(`codeaster_en.comm`). It is engineering judgement, recorded as ADR-013 in `docs/DECISIONS.md`;
the solver does not make this choice for you.

1. **Is the part a body of revolution under loads that are also axisymmetric** (pressure
   vessel without nozzles, flange, shaft under axial load and internal pressure)? Use `AXIS`
   on the meridian cross-section. Any non-axisymmetric feature (a nozzle, a lateral load)
   rules it out: use 3D.
2. **Is the part prismatic and long, loaded the same way along its length, with the
   out-of-plane strain prevented** (dam, retaining wall, buried pipe section, long weld
   seam)? Use `D_PLAN` on the cross-section.
3. **Is the part a thin flat plate loaded only in its own plane** (gusset, flange web under
   in-plane force)? Use `C_PLAN` on the plate's outline.
4. **Is one dimension much smaller than the other two** (plates, shells, sheet metal,
   tanks)? Use a shell modeling on the mid-surface: `DKT` by default, `DST` when the shell is
   moderately thick, `COQUE_3D` when it is strongly curved and you can provide a quadratic
   mesh. See [Shells](#shells-dkt-dst-coque_3d) for the thresholds.
5. **Are two dimensions much smaller than the length** (frames, trusses with bending, shafts,
   pipes treated as beams)? Use `POU_D_T` on the center line.
6. **Otherwise**, mesh the solid and use `3D`. Prefer a quadratic mesh (`TETRA10`, `HEXA20`)
   for stresses. Use `3D_SI` only on a hexahedral-dominant quadratic mesh where locking is a
   concern.

Defaults for the builder (ADR-013):

| ClearFEA body kind | `MODELISATION` | Mesh to request from Gmsh | Required extra data |
|---|---|---|---|
| solid | `3D` | second order (`TETRA10`), or first order for quick checks | material |
| shell (thin) | `DKT` | first order, `TRIA3` / `QUAD4` on the mid-surface | thickness; reference vector for local axes |
| shell (thick) | `DST` | first order, `TRIA3` / `QUAD4` | thickness; reference vector |
| curved shell (quadratic) | `COQUE_3D` | second order, converted to `QUAD9` / `TRIA7` | thickness; reference vector |
| beam | `POU_D_T` | first order `SEG2` on the center line | section; orientation |
| plane stress | `C_PLAN` | 2D, in the plane z = 0 | material |
| plane strain | `D_PLAN` | 2D, in the plane z = 0 | material |
| axisymmetric | `AXIS` | 2D, in z = 0, x = radius ≥ 0, y = axis | material |

The rules of thumb used above (span to thickness ratio for shells, span to depth ratio for
beams) are textbook structural mechanics, not solver behavior. TODO(verify) them against the
code_aster usage notes for each modeling (the U3 documents, not available in the sandbox).

## Solids: `3D`, `3D_SI`

### `3D` — 3D solid

**What it is.** Isoparametric volume elements with three translations per node
(`upstream/catalo/cataelem/Elements/meca_3d.py:33`). Every volume type is accepted, linear and
quadratic, and the boundary faces and edges assigned with them become face and edge elements
that carry surface and line loads (`MECA_FACE3` for a `TRIA3`,
`tests/fixtures/solid_static/output/run.mess`).

**Pick it when** the part is chunky (no dimension much smaller than the others), when the
stress you need is a local 3D concentration (fillets, nozzles, bosses), or when you are unsure:
it makes no kinematic assumption. Our `solid_static` fixture (cylinder with nozzle, `TETRA4`)
and `modal` fixture (cantilever, `HEXA20`) both use it. The modal fixture's first five
frequencies match Euler-Bernoulli beam theory within 1.15 % on 640 `HEXA20` elements
(`tests/fixtures/README.md`).

**Watch out for:**

- **Load faces.** Assign the model with `TOUT='OUI'`, or list the face groups that carry
  pressure, or `PRES_REP` finds no element there (`en/commands/AFFE_MODELE.md`, pitfalls).
- **Linear tetrahedra.** Four-node tetrahedra (`TETRA4`) are known to be too stiff in bending,
  so displacements and stresses come out low unless the mesh is very fine. This is general
  finite element knowledge, not something our fixtures measure: `solid_static` checks only the
  reaction sum, which is an equilibrium check and does not depend on element stiffness. For
  stress results, ask Gmsh for second-order elements (`TETRA10`).
- **No rotations.** Solid nodes have no `DRX`..`DRZ`. A `DDL_IMPO` with `DRX` on a solid node
  has nothing to act on, and a shell or beam attached to a solid face is not tied in rotation
  unless you add a connection (see [Mixing modeling types](#mixing-modeling-types)).

### `3D_SI` — 3D solid (reduced integration)

**What it is.** The same kinematics as `3D`, with fewer integration points for the stiffness:
the catalog calls the elements "Sub-integrated"
(`upstream/catalo/cataelem/Elements/meca_3d_si_quad.py:51`); for a `HEXA20` the stiffness uses
8 integration points instead of 27 (glossary note on `3D_SI`). Only `HEXA8`, `HEXA20` and
`TETRA10` volumes are accepted, with `QUAD4`, `QUAD8` and `TRIA6` faces (line 1448).

**Pick it when** the mesh is hexahedral and quadratic and the full-integration elements lock
(nearly incompressible material, bending of thin solid parts). Upstream test cases use it
in that role, for example a viscoelastic layer in `upstream/astest/sdll151a.comm:34` and an
alternative to `3D` that `upstream/astest/ssnd112a.comm:60` keeps commented out.
TODO(verify) when the official documentation recommends `3D_SI` over `3D`.

**Do not pick it** for a tetrahedral mesh from an automatic mesher unless it is all `TETRA10`:
`TETRA4`, `PENTA*` and `PYRAM*` are not in the list, so they are skipped with warning
`MODELE1_70` and missing from the model. ClearFEA should not offer `3D_SI` as a default.

## Shells: `DKT`, `DST`, `COQUE_3D`

All three are meshed on the mid-surface and carry three translations and three rotations per
node. All three need `AFFE_CARA_ELEM / COQUE` with the thickness `EPAIS` for every shell
element; an element without it stops the analysis with `CALCUL_21`
(`en/commands/AFFE_CARA_ELEM.md`). All three report generalized forces `EFGE_ELNO` /
`EFGE_NOEU` (membrane `NXX`, `NYY`, `NXY`, bending `MXX`, `MYY`, `MXY`, shear `QX`, `QY`) in
the element local axes, which come from the `COQUE / ANGL_REP` or `VECTEUR` reference direction
(`en/commands/CALC_CHAMP.md`). Stresses are stored per layer through the thickness
(`COQUE_NCOU`, catalog attribute `SOUS_POINT`). The rotation about the shell normal (`DRZ`)
has no physical stiffness and is held by a small fictitious one (`COEF_RIGI_DRZ`,
`upstream/bibfor/elements/dxtloc.F90:125`).

Orient the shell normals before building the model
(`MODI_MAILLAGE / ORIE_NORM_COQUE`, `tests/fixtures/shell_static/input/run.comm:30`): the normal
decides the sign of the pressure and which face is "upper" for `NIVE_COUCHE='SUP'`.

### `DKT` — thin shell (DKT)

**What it is.** Plate elements of the "discrete Kirchhoff" family on `TRIA3` and `QUAD4`
(finite elements `MEDKTR3`, `MEDKQU4`, line 3946). Transverse shear deformation is neglected,
which is the thin-plate (Kirchhoff) assumption; the glossary note says the same.

**Pick it when** the shell is thin: as a rule of thumb, smallest span over thickness above
about 20. Our `shell_static` fixture (simply supported square plate, span 1000 mm, thickness
10 mm, 20 × 20 `QUAD4`) matches the Navier thin-plate solution within 0.007 % for the center
deflection and 0.16 % for the center moment `MXX` (`tests/fixtures/README.md`). This is the
ClearFEA default for shells.

**Watch out for:**

- **Linear mesh only.** `TRIA6` and `QUAD8` are skipped (`MODELE1_70`). Ask Gmsh for
  first-order elements.
- **Warped quadrangles.** A non-flat `QUAD4` gives warning `PLATE1_81` ("can lead to wrong
  results", `VERI_PLAN`, `en/commands/AFFE_MODELE.md`). On curved surfaces, prefer triangles
  or refine.
- **Thick plates.** Without shear deformation, a `DKT` plate is too stiff when the thickness is
  not small compared with the span, and transverse shear forces `QX`, `QY` come only from
  equilibrium. Switch to `DST`.

### `DST` — thick shell (DST)

**What it is.** The "discrete shear" counterpart on the same element types (`MEDSTR3`,
`MEDSQU4`, line 3979). It includes transverse shear deformation: the element builds a
transverse shear strain matrix from the shear forces
(`upstream/bibfor/elements/dstb.F90:128`), with a fixed 5/6 correction factor
(`upstream/bibfor/elements/dxmate.F90:196`, `kcis`).

**Pick it when** the shell is moderately thick (span over thickness between about 5 and 20),
or for sandwich and composite plates where transverse shear matters. Below a ratio of about 5
the plate is a solid: use `3D`. For thin shells `DST` and `DKT` should give close results,
since the shear term becomes small; TODO(verify) whether the official documentation prefers
one of them for thin shells. Upstream example: `upstream/astest/ssls04b.comm:29`.

### `COQUE_3D` — 3D shell (quadratic)

**What it is.** Curved quadratic shell elements on 9-node quadrangles and 7-node triangles
(`MEC3QU9H`, `MEC3TR7H`, line 3692). The center node carries rotations only; the other nodes
carry all six DOFs (`upstream/catalo/cataelem/Elements/meca_coque_3d.py:58`, `:980`, `:996`).
Transverse shear is included, with the correction factor `A_CIS` (default 5/6) read by these
elements only (`upstream/bibfor/elements/vdesga.F90:74`).

**Pick it when** the shell is strongly curved (small radius over thickness, nozzles, elbows,
torispherical heads) and a quadratic mesh is available, so that the geometry is represented
without faceting.

**Watch out for:**

- **Mesh conversion.** Gmsh writes `QUAD8` and `TRIA6`, which `COQUE_3D` does not accept.
  Convert before `AFFE_MODELE` with `CREA_MAILLAGE(MODI_MAILLE=_F(OPTION='QUAD8_9', ...))`
  and `'TRIA6_7'` (`upstream/astest/ssls119c.comm:30`).
- **Center node.** The center node has no translations, so a `DDL_IMPO` on `DX`..`DZ` of a
  group that includes it fails on that node. Give boundary conditions on edge node groups.

## 2D models: `C_PLAN`, `D_PLAN`, `AXIS`

All three use 2D elements with two translations per node, `DX` and `DY`
(`upstream/catalo/cataelem/Elements/meca_c_plan.py:33`, `meca_d_plan.py:33`, `meca_axis.py:33`),
linear or quadratic (`TRIA3/6`, `QUAD4/8/9`). Edges (`SEG2/3`) carry line loads
(`FORCE_CONTOUR`, `PRES_REP`). The mesh must lie in the plane z = 0: otherwise `MODELE1_3`,
`MODELE1_53` or `MODELE1_58` (`en/commands/AFFE_MODELE.md`, pitfalls). Stresses have four
components, `SIXX`, `SIYY`, `SIZZ`, `SIXY` (catalog attribute `NBSIGM` = 4;
`upstream/catalo/cataelem/Commons/located_components.py:1221`). A centrifugal
`ROTATION` load must turn about the z axis for `C_PLAN` and `D_PLAN` (`CHARGES2_67`) and about
the y axis, through the origin, for `AXIS` (`CHARGES2_65`, `CHARGES2_66`;
`upstream/code_aster/Messages/charges2.py:285`).

The difference between the three is the assumption on the third direction, which selects the
material law: `C_PLAN` uses the plane-stress Hooke matrix and `D_PLAN` and `AXIS` the
plane-strain one (`upstream/bibfor/comport_util/dmatmc.F90:91`, `:105`, `:114`).

### `C_PLAN` — plane stress

**What it is.** The stress normal to the plane is zero (σzz = 0); the strain εzz is free.

**Pick it when** a thin flat part is loaded only in its own plane: plates in membrane action,
gussets, thin brackets loaded in plane. If the part also bends out of its plane, it is a shell
(`DKT`). Upstream example: `upstream/astest/ssnp110a.comm:27`.

**Watch out for:** the plate thickness. `AFFE_CARA_ELEM` has no thickness for `C_PLAN` in our
Tier 1 scope, so results are per unit thickness. TODO(verify) against U4.44.01 how loads and
reactions are scaled; until then ClearFEA should divide applied line loads by the thickness
and multiply reactions back.

### `D_PLAN` — plane strain

**What it is.** The strain normal to the plane is zero (εzz = 0); the stress σzz is not zero
and is reported in `SIZZ`.

**Pick it when** a long prismatic body is loaded uniformly along its length and its ends are
restrained: dams, retaining walls, tunnels, buried pipes, long welds, contact of long rollers.
Results are per unit length along z. Upstream example:
`upstream/astest/cont200a.comm:41`.

### `AXIS` — axisymmetric

**What it is.** A body of revolution about the global y axis, modeled by its meridian
cross-section in the plane z = 0. `x` is the radius and must be ≥ 0 on every node
(`MAILLAGE1_2`, `MAILLAGE1_3`); `DX` is the radial and `DY` the axial displacement. The hoop
stress is `SIZZ` (TODO(verify) against U4.41.01).

**Pick it when** both the geometry and the loads are axisymmetric: pressure vessels and pipes
without nozzles, flanges, shafts, rotating disks (`ROTATION` about y). Upstream example:
`upstream/astest/hplv102a.comm:63`.

**Watch out for:**

- **Forces per radian.** Nodal forces and reactions are per radian of circumference, not for
  the full ring: an upstream test case notes "la force est en n/radian" (the force is in N per
  radian) next to its `REAC_NODA` (`upstream/astest/ssna111a.comm:94`). Multiply a reaction by
  2π for the total; divide a total ring force by 2π before applying it as `FORCE_NODALE`.
  TODO(verify) this for `FORCE_NODALE` against U4.44.01.
- **Points on the axis.** Nodes with x = 0 are on the axis of revolution; a pressure that
  follows the deformation cannot be applied there (`ALGORITH8_25`, for `PRES_REP` with `TYPE_CHAR='SUIV'`).
- **Non-axisymmetric loads.** A lateral load or a single bolt cannot be modeled; use 3D, or
  `AXIS_FOURIER` (out of scope).

## Beams: `POU_D_T` (and `POU_D_E`)

**What it is.** A straight two-node beam on `SEG2` (`MECA_POU_D_T`, line 5373) with six DOFs
per node (`upstream/catalo/cataelem/Elements/meca_pou_d_t.py:113`) and transverse shear
deformation (Timoshenko). In the stiffness matrix the shear terms enter through
φ = 12 E I α / (G A L²), where α is the section's shear coefficient (`AY`, `AZ`)
(`upstream/bibfor/elements/ptka01.F90:104`). `POU_D_E` (Euler-Bernoulli beam, line 5337) is
the same element with α set to zero (`upstream/bibfor/elements/porigi.F90:106`), that is
without shear deformation. Since φ falls as 1/L², the two converge for slender elements.

The beam has no stresses in the `SIGM_*` sense (catalog attribute `SIGM` = `NON`, line 5381):
it reports generalized forces `EFGE_ELNO` / `EFGE_NOEU` (`N`, `VY`, `VZ`, `MT`, `MFY`, `MFZ`)
in its local axes (`en/commands/CALC_CHAMP.md`).

**Pick it when** a member is long compared with its cross-section (frames, trusses with rigid
joints, piping as a line model, shafts). `POU_D_T` is our default rather than `POU_D_E`: it is
exact in the slender limit and also correct for short, deep members (span over depth below
about 10, where shear deformation adds noticeably to the deflection).

**Data it needs** (`upstream/code_aster/Cata/Commands/affe_cara_elem.py:511`):

- `POUTRE` with `SECTION='CERCLE'` (`CARA=('R', 'EP')`, radius and wall thickness),
  `'RECTANGLE'` (`'H'`, `'EP'` or `'HY'`, `'HZ'`, ...) or `'GENERALE'` (at least `'A'`, `'IY'`,
  `'IZ'`, `'JX'`, plus `'AY'`, `'AZ'` for the shear coefficients). `GENERALE` example with
  `AY = AZ = 1.2`: `upstream/astest/ssll105b.comm:35`. TODO(verify) how `AY`, `AZ` are set for
  `CERCLE` and `RECTANGLE` sections, against U4.42.01.
- `ORIENTATION` (`upstream/code_aster/Cata/Commands/affe_cara_elem.py:1170`) to fix the local
  y axis, for example `CARA='VECT_Y'` with a vector whose projection on the plane normal to the
  beam axis gives local y (catalog help). Without it, the solver computes the axis direction
  from the two nodes and leaves the twist angle at its initial zero
  (`upstream/bibfor/modelisa/aceaor.F90:162`). TODO(verify) which direction local y takes
  then. Always give `ORIENTATION` for non-circular sections, or `IY` and `IZ` may act about the
  wrong axes.

**Watch out for:**

- **Straight two-node elements only.** `SEG3` is skipped; ask Gmsh for first-order lines, and
  use several elements per member for curved members and for dynamic analysis.
- **Loads.** Distributed loads use `FORCE_POUTRE`
  (`upstream/code_aster/Cata/Commands/affe_char_meca.py:975`), not `FORCE_ARETE`.
- **Not in COMMAND-SET yet.** `AFFE_CARA_ELEM / POUTRE` and `ORIENTATION` are not listed in
  `docs/COMMAND-SET.md` Tier 1 or 2, and `en/commands/AFFE_CARA_ELEM.md` documents them only by
  name. Beams need that scope extension before the builder offers them (queued for the owner).

## Mixing modeling types

One `AFFE_MODELE` can mix modeling types, one `AFFE` occurrence per group, as long as all use
`PHENOMENE='MECANIQUE'` (`MODELE1_11`). Common mixes are a solid with springs
(`3D` + `DIS_T`, `upstream/astest/ssnd112a.comm:54`) and a shell with a solid
(`DKT` + `3D`, `upstream/astest/ssls101m.comm:48`).

Nodes shared by different modeling types carry the union of their DOFs, but the elements only
couple through the DOFs they have in common. A shell or beam node on a solid face is therefore
tied in translation only and acts as a hinge. To transmit moments, add a kinematic connection
with `AFFE_CHAR_MECA / LIAISON_ELEM` (`upstream/code_aster/Cata/Commands/affe_char_meca.py:682`):

| Connection | `OPTION` | Upstream example |
|---|---|---|
| shell edge on solid face | `'COQ_3D'` | `upstream/astest/ssls101m.comm:165` |
| beam end on solid face | `'3D_POU'` | `upstream/astest/sdlv122a.comm:100` |
| beam end on shell edge | `'COQ_POU'` | `upstream/astest/sdll135f.comm:84` |

`LIAISON_ELEM` is outside COMMAND-SET Tier 1 and 2. Until it is in scope, ClearFEA should keep
one modeling family per model, apart from discrete elements.

## Discrete elements: `DIS_T`, `DIS_TR`

Not one of the nine, but often the alternative to a beam or a solid: springs, point masses
and dampers on `POI1` (node to ground) or `SEG2` (between two nodes), with their values from
`AFFE_CARA_ELEM / DISCRET` (`en/commands/AFFE_CARA_ELEM.md`). Use `DIS_T` (translations) on
solid nodes and `DIS_TR` (translations and rotations) on shell or beam nodes. For a 2D model
use `2D_DIS_T` / `2D_DIS_TR`; a model cannot mix 2D and 3D discrete elements (`MODELE1_54`).

## See also

- [AFFE_MODELE](../commands/AFFE_MODELE.md): the command, its keywords and the full list of
  modeling values.
- [AFFE_CARA_ELEM](../commands/AFFE_CARA_ELEM.md): shell thickness and local axes, discrete
  values.
- [CALC_CHAMP](../commands/CALC_CHAMP.md): which result fields each modeling type produces.
- [CREA_MAILLAGE](../commands/CREA_MAILLAGE.md): element type conversion for `COQUE_3D`.
- Element catalog: `upstream/catalo/cataelem/Commons/phenomenons_modelisations.py`.
- Fixtures: `tests/fixtures/solid_static` (`3D`, `TETRA4`), `tests/fixtures/shell_static`
  (`DKT`, `QUAD4`), `tests/fixtures/modal` (`3D`, `HEXA20`).
