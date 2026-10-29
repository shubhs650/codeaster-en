---
command: AFFE_MODELE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/affe_modele.py:26
doc_fr: U4.41.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3b)
examples: [cont200a, ssnd112a, hplv102a, ssls119c, hsnv140j]
---

# AFFE_MODELE — assign model

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.

`AFFE_MODELE` turns a mesh into a finite element model (`modele_sdaster`). For each `AFFE`
occurrence it takes a set of elements (`TOUT='OUI'` or `GROUP_MA`), a physics
(`PHENOMENE`) and a modeling type (`MODELISATION`), and assigns to every element whose
type the modeling supports the matching finite element: for example `'3D'` turns a `TETRA4`
into `MECA_TETRA4` and a boundary `TRIA3` into the face element `MECA_FACE3`
(`tests/fixtures/solid_static/output/run.mess`). Elements that receive no finite element
are simply not part of the model. The decision it encodes is the kinematic idealization of
each part: 3D solid, shell, plane stress, plane strain, axisymmetric, or discrete spring/mass.
Every later command that computes (`AFFE_CARA_ELEM`, `AFFE_CHAR_MECA`, `MECA_STATIQUE`,
`CALC_CHAMP`) works on this model. A model holds one physics only (`MODELE1_11`): a thermal
and a mechanical analysis of the same mesh need two `AFFE_MODELE` calls
(`upstream/astest/hplv102a.comm:31`, `:63`).

| Fact | Value |
|---|---|
| Catalog description (fr) | «Définir le phénomène physique modélisé et le type d'éléments finis sur le maillage» |
| Kind | `OPER` |
| Result | `modele_sdaster` |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.41.01 — from en/doc-ids.yaml (status: proposed) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `AFFE`, `TOUT`, `GROUP_MA`, `PHENOMENE`, `MECANIQUE`, `MODELISATION`, `DKT`, `DST`, `COQUE_3D`, `AXIS`, `C_PLAN`, `D_PLAN`, `DISCRET`, `DIS_T`, `DIS_TR`, `CARA`, `K_T_D_N`, `K_TR_D_N`, `VALE`, `REPERE` |

The COMMAND-SET row also lists `DISCRET`, `CARA`, `K_T_D_N`, `K_TR_D_N`, `VALE` and `REPERE`:
those are `AFFE_CARA_ELEM` keywords that go with the `DIS_T` / `DIS_TR` modelings, and they are
documented in [AFFE_CARA_ELEM](AFFE_CARA_ELEM.md).

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MAILLAGE` | `maillage_sdaster`, required | — | *mesh*. The mesh to build the model on, from `LIRE_MAILLAGE` (or `CREA_MAILLAGE`, `MODI_MAILLAGE`). Group names given in `GROUP_MA` must exist in it. A parallel mesh forces `DISTRIBUTION/METHODE='CENTRALISE'` (`upstream/code_aster/CodeCommands/affe_modele.py:39`). |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `1` prints the assignment summary (message `MODELE1_4`, then a table of modeling, element type, finite element and count). `2` also lists each element of an `AFFE` occurrence that could not be assigned (`MODELE1_2`, `upstream/bibfor/op/op0018.F90:285`). Use `2` to find which elements a modeling rejected. |
| `GRANDEUR_CARA` | factor keyword, optional | — | *characteristic quantities*. Characteristic quantities used to make the HM error indicators dimensionless. Only for coupled hydro-mechanical (THM) models with error indicators; not used in Tier 1. |
| `GRANDEUR_CARA / LONGUEUR` | real, optional | — | *length*. Characteristic length. Range: ≥ 0. |
| `GRANDEUR_CARA / PRESSION` | real, optional | — | *pressure*. Characteristic pressure. Range: ≥ 0. |
| `GRANDEUR_CARA / TEMPERATURE` | real, optional | — | *temperature*. Characteristic temperature. Range: ≥ 0. |
| `AFFE_SOUS_STRUC` | factor keyword, optional | — | Substructure assignment (catalog translation: "Substructures assignement"). Places super-elements (`SUPER_MAILLE`) in the model instead of, or as well as, finite elements. Out of Tier 1 scope. TODO(verify) the super-element workflow (`MACR_ELEM_STAT`, `DEFI_MAILLAGE`) against U4.41.01. |
| `AFFE_SOUS_STRUC / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Every super-element of the mesh. |
| `AFFE_SOUS_STRUC / SUPER_MAILLE` | element, optional, list | — | Names of the super-elements to place. |
| `AFFE_SOUS_STRUC / PHENOMENE` | text, optional | `'MECANIQUE'` | *physics*. One of `'MECANIQUE'`. Fixed: substructuring is mechanical only. |
| `AFFE` | factor keyword, optional, repeatable | — | One assignment: a set of elements, a physics and one modeling type (catalog translation: "Finite element assignement"). Repeat it to give different parts different modelings, for example a 3D solid plus `DIS_T` springs (`upstream/astest/ssnd112a.comm:54`). When two occurrences cover the same element, the later one wins wherever its modeling supports that element type (`upstream/bibfor/op/op0018.F90:247`). |
| `AFFE / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Assign to every element of the mesh; those whose type the modeling does not support are skipped. With `'3D'` this also turns the boundary faces into face elements, which pressure loads need (`tests/fixtures/solid_static/input/run.comm:22`). |
| `AFFE / GROUP_MA` | element group, optional, list | — | *element group*. Assign only to these groups. Use it when the mesh mixes parts with different modelings, or holds elements (point groups, construction lines) that must stay out of the model. |
| `AFFE / PHENOMENE` | text, required | — | *physics*. One of `'MECANIQUE'`, `'THERMIQUE'`, `'ACOUSTIQUE'`. All occurrences must give the same value (`MODELE1_11`, `upstream/bibfor/op/op0018.F90:207`). Tier 1 uses `'MECANIQUE'`. |
| `AFFE / MODELISATION` | text, required | — | *modeling type*. Only when `equal_to("PHENOMENE", 'MECANIQUE')`. One of 184 values (see the .json); the Tier 1 ones are in [Mechanical modeling types](#mechanical-modeling-types) below. One value per occurrence (catalog `max=1`). |
| `AFFE / FORMULATION` | text, optional | `'LINEAIRE'` | One of `'LINEAIRE'`, `'QUADRATIQUE'`, `'CUBIQUE'`, `'QUARTIQUE'`. Only when `equal_to("PHENOMENE", 'MECANIQUE') and equal_to('MODELISATION', ('3D_HHO', 'D_PLAN_HHO' ))`. Polynomial order of the HHO (hybrid high-order) modelings, as the value names say (linear to quartic). Out of Tier 1 scope. |
| `AFFE / FORMULATION` | text, optional | `'LINEAIRE'` | One of `'LINEAIRE'`, `'QUADRATIQUE'`. Only when `equal_to("PHENOMENE", 'MECANIQUE') and equal_to('MODELISATION', ("D_PLAN_GRAD_HHO", "3D_GRAD_HHO" ))`. Polynomial order of the gradient HHO modelings. Out of Tier 1 scope. |
| `AFFE / FORMULATION` | text, optional | `'U_P_PHI'` | One of `'U_P_PHI'`, `'U_P'`, `'U_PSI'`. Only when `equal_to("PHENOMENE", 'MECANIQUE') and equal_to('MODELISATION', ('2D_FLUIDE', '2D_FLUI_ABSO', '2D_FLUI_PESA', '2D_FLUI_STRU','3D_FLUIDE','3D_FLUI_ABSO', 'AXIS_FLUIDE', 'AXIS_FLUI_STRU', 'AXIS_FLUI_ABSO', 'FLUI_STRU'))`. Choice of unknowns for the fluid and fluid-structure modelings; the catalog maps each to a separate finite element family (`upstream/catalo/cataelem/Commons/phenomenons_modelisations.py`, `2D_FLUIDE#1` / `#2`). All fluid occurrences of one model must use the same formulation (`VERI_FORMULATION_IFS`). Out of Tier 1 scope. TODO(verify) the physical meaning of each set against U4.41.01. |
| `AFFE / FORMULATION` | text, optional | `'DIL'` | One of `'DIL'`, `'DIL_INCO'`. Only when `equal_to("PHENOMENE", 'MECANIQUE') and equal_to('MODELISATION', ('D_PLAN_DIL', '3D_DIL', ))`. Variant of the dilatation modelings. Out of Tier 1 scope. |
| `AFFE / MODELISATION` | text, required | — | *modeling type*. One of `'3D'`, `'3D_DIAG'`, `'AXIS'`, `'AXIS_DIAG'`, `'AXIS_FOURIER'`, `'COQUE'`, `'COQUE_AXIS'`, `'COQUE_PLAN'`, `'PLAN'`, `'PLAN_DIAG'`, `'3D_HHO'`, `'PLAN_HHO'`, … (17 values; see the .json). Only when `equal_to("PHENOMENE", 'THERMIQUE')`. Thermal modelings, for a heat-transfer model whose temperature then feeds a mechanical model through `AFFE_MATERIAU/AFFE_VARC` (`upstream/astest/hplv102a.comm:31`). Tier 2 and later. |
| `AFFE / FORMULATION` | text, optional | `'LINEAIRE'` | One of `'CONSTANTE'`, `'LINEAIRE'`, `'QUADRATIQUE'`, `'CUBIQUE'`, `'QUARTIQUE'`. Only when `equal_to("PHENOMENE", 'THERMIQUE') and equal_to('MODELISATION', ('3D_HHO', 'PLAN_HHO', 'AXIS_HHO'))`. Polynomial order of the thermal HHO modelings. Out of Tier 1 scope. |
| `AFFE / MODELISATION` | text, required | — | *modeling type*. One of `'3D'`, `'PLAN'`, `'3D_ABSO'`, `'PLAN_ABSO'`. Only when `equal_to("PHENOMENE", 'ACOUSTIQUE')`. Acoustic modelings. Out of Tier 1 scope. |
| `DISTRIBUTION` | factor keyword, optional, present by default | — | How the elements are shared out between MPI processes in a parallel run (catalog translation: "MPI distribution"). Present by default with `METHODE='SOUS_DOMAINE'`, `PARTITIONNEUR='METIS'`, as every fixture log shows. In a sequential run the solver ignores it and uses `'CENTRALISE'` (`upstream/bibfor/op/op0018.F90:414`). Leave it out. |
| `DISTRIBUTION / METHODE` | text, optional | `'SOUS_DOMAINE'` | *method*. One of `'MAIL_CONTIGU'`, `'MAIL_DISPERSE'`, `'CENTRALISE'`, `'GROUP_ELEM'`, `'SOUS_DOMAINE'`. `'CENTRALISE'`: no distribution. `'SOUS_DOMAINE'`: elements are split into sub-domains by a graph partitioner (`upstream/bibfor/op/op0018.F90:432`). On a parallel mesh only `'CENTRALISE'` is accepted (`MODELE1_99`); the command sets it for you (`upstream/code_aster/CodeCommands/affe_modele.py:40`). `'MAIL_CONTIGU'` and `'MAIL_DISPERSE'` are refused for modelings that need neighbor elements, such as joint elements (`MODELE1_13`). TODO(verify) the difference between `'MAIL_CONTIGU'`, `'MAIL_DISPERSE'` and `'GROUP_ELEM'` against U4.41.01. |
| `DISTRIBUTION / CHARGE_PROC0_MA` | integer, optional | `100` | Range: ≥ 0, ≤ 100. Only when `is_in("METHODE", ('MAIL_DISPERSE','MAIL_CONTIGU'))`. A percentage for process 0, which the name suggests is its share of the element load. TODO(verify) against U4.41.01. |
| `DISTRIBUTION / NB_SOUS_DOMAINE` | integer, optional | — | Only when `equal_to("METHODE",'SOUS_DOMAINE' )`. Number of sub-domains. Default: the number of MPI processes (`upstream/bibfor/op/op0018.F90:428`; catalog comment). |
| `DISTRIBUTION / PARTITIONNEUR` | text, optional | `'METIS'` | One of `'METIS'`, `'SCOTCH'`. Only when `equal_to("METHODE",'SOUS_DOMAINE' )`. The graph partitioner that builds the sub-domains (`upstream/bibfor/op/op0018.F90:426`). |
| `VERI_JACOBIEN` | text, optional | `'OUI'` | *Jacobian check*. Checks the shape of the elements (all Jacobians of the same sign). One of `'OUI'`, `'NON'`. `'OUI'` evaluates the Jacobian of the geometric mapping of every element and warns (`MAILLAGE1_1`) for each element where its sign changes between integration points, that is a distorted or inverted element (`upstream/bibfor/modelisa/modelCheck.F90:123`, `upstream/bibfor/te/te0328.F90:74`). Keep `'OUI'`. |
| `VERI_NORM_IFS` | text, optional | `'OUI'` | Checks the orientation of the normals for FSI (IFS). One of `'OUI'`, `'NON'`. Only acts on fluid-structure interface elements (`upstream/bibfor/modelisa/modelCheckFSINormals.F90`); a bad orientation stops the run (`FLUID1_4`). Keep `'OUI'`. |
| `VERI_FORMULATION_IFS` | text, optional | `'OUI'` | Checks the consistency of the formulation for FSI (IFS). One of `'OUI'`, `'NON'`. Checks that the fluid elements of the model share one `FORMULATION` (`upstream/bibfor/modelisa/modelCheckFluidFormulation.F90`). Keep `'OUI'`. |
| `VERI_PLAN` | text, optional | `'OUI'` | Checks the flatness of the elements. One of `'OUI'`, `'NON'`. For plate elements (`DKT`, `DST`) on `QUAD4`, warns with `PLATE1_81` when a quadrangle is not flat, which "can lead to wrong results" (`upstream/bibfor/modelisa/modelCheckPlaneity.F90:132`). Keep `'OUI'`; on a warning, remesh the warped region with triangles or finer quadrangles. |

### Mechanical modeling types

The Tier 1 values of `AFFE / MODELISATION` with `PHENOMENE='MECANIQUE'`. "Elements"
lists the element types the modeling turns into finite elements; any other type in the
assigned set is skipped (`upstream/catalo/cataelem/Commons/phenomenons_modelisations.py`, line
of each entry given).

| Value | Meaning | Elements | Use for |
|---|---|---|---|
| `3D` | 3D solid | `HEXA8/20/27`, `PENTA6/15/18`, `PYRAM5/13`, `TETRA4/10`; boundary `QUAD4/8/9`, `TRIA3/6`; edges `SEG2/3` (line 287) | Any solid part. The boundary faces become face elements that carry surface loads; give them by `TOUT='OUI'` or by their group. Our `solid_static` and `modal` fixtures. |
| `3D_SI` | 3D solid (reduced integration) | `HEXA8`, `HEXA20`, `TETRA10`; faces `QUAD4/8`, `TRIA6` (line 1447) | Same use as `3D` with reduced integration: the `HEXA20` stiffness uses 8 integration points instead of 27 (`upstream/catalo/cataelem/Elements/meca_3d_si_quad.py:51`, "Sub-integrated"); reduced integration is meant to limit locking. TODO(verify) when U4.41.01 recommends it over `3D`. |
| `DKT` | thin shell (DKT) | `TRIA3`, `QUAD4`; edges `SEG2` (line 3946) | Thin plates and shells on a linear mesh; no transverse shear (Kirchhoff). Our `shell_static` fixture (span/thickness = 100) matches the classical Navier plate solution with it (`tests/fixtures/shell_static/input/run.comm:5`). Needs `AFFE_CARA_ELEM/COQUE`. |
| `DST` | thick shell (DST) | `TRIA3`, `QUAD4`; edges `SEG2` (line 3979) | Moderately thick plates and shells on a linear mesh: includes transverse shear deformation (`upstream/bibfor/elements/dstb.F90:128`). Needs `AFFE_CARA_ELEM/COQUE`. |
| `COQUE_3D` | 3D shell (quadratic) | `QUAD9`, `TRIA7`; edges `SEG3` (line 3692) | Curved shells on a quadratic mesh. Mesh generators write `QUAD8` / `TRIA6`, so convert first with `CREA_MAILLAGE(MODI_MAILLE=_F(OPTION='QUAD8_9' or 'TRIA6_7'))` (`upstream/astest/ssls119c.comm:30`). Needs `AFFE_CARA_ELEM/COQUE`. |
| `C_PLAN` | plane stress | `TRIA3/6`, `QUAD4/8/9`; edges `SEG2/3` (line 3718) | 2D thin plates loaded in their plane. The mesh must lie in the plane z = 0 (`MODELE1_3`). |
| `D_PLAN` | plane strain | `TRIA3/6`, `QUAD4/8/9`; edges `SEG2/3` (line 3995) | 2D slices of long bodies (no strain along z), as in `upstream/astest/cont200a.comm:41`. Mesh in z = 0. |
| `AXIS` | axisymmetric | `TRIA3/6`, `QUAD4/8/9`; edges `SEG2/3` (line 1823) | Bodies of revolution under axisymmetric loads. The mesh is the cross-section in the plane z = 0, with x as the radius: every node needs x ≥ 0 (`MAILLAGE1_2`, `MAILLAGE1_3`). `upstream/astest/hplv102a.comm:63`. |
| `DIS_T` | translational discrete element (spring/mass) | `POI1`, `SEG2` (line 3926) | 3D springs, masses or dampers with translation degrees of freedom: on a `POI1` (node to ground) or a `SEG2` (between two nodes). Values come from `AFFE_CARA_ELEM/DISCRET`. |
| `DIS_TR` | translational+rotational discrete element | `POI1`, `SEG2` (line 3936) | As `DIS_T`, with rotation degrees of freedom as well; use it where the spring attaches to shell or beam nodes. |

The 2D variants `2D_DIS_T` / `2D_DIS_TR` (line 69) are the discrete elements for 2D models; a
model cannot mix 2D and 3D discrete elements (`MODELE1_54`).

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at least one of `AFFE`, `AFFE_SOUS_STRUC` must be given (`AU_MOINS_UN`).
- `AFFE_SOUS_STRUC`: exactly one of `TOUT`, `SUPER_MAILLE` must be given (`UN_PARMI`).
- `AFFE`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).

Checked by the solver (`upstream/bibfor/op/op0018.F90`, `upstream/bibfor/modelisa/modelCheck.F90`):

- every `AFFE` occurrence uses the same `PHENOMENE` (`MODELE1_11`, fatal);
- at least one element must receive a finite element (`MODELE1_6`, fatal);
- 2D and 3D discrete elements cannot be mixed (`MODELE1_54`, fatal);
- `AXIS` modelings need x ≥ 0 on every node (`MAILLAGE1_3`, fatal).

## Patterns

### Whole mesh, one modeling

`TOUT='OUI'` with `'3D'` assigns the volume elements and also the boundary faces, so that a
pressure applied on a face group finds its elements.

Source: `tests/fixtures/solid_static/input/run.comm:23`.

```python
MODE = AFFE_MODELE(MAILLAGE=MAIL, AFFE=_F(TOUT="OUI", PHENOMENE="MECANIQUE", MODELISATION="3D"))
```

The log reports what was assigned (`tests/fixtures/solid_static/output/run.mess`, message
`MODELE1_4` and the summary table):

```text
Sur les 18778 mailles du maillage 00000001, on a demandé l'affectation de 18778, on a pu en affecter
18778.
Modélisation     Formulation      Type maille  Élément fini     Nombre
_                _                TRIA3        MECA_FACE3       4339
3D               _                TETRA4       MECA_TETRA4      14439
```

That is: of the 18,778 elements, 18,778 were requested and 18,778 assigned; the 4,339
boundary triangles became face elements.

### One group, shell modeling

Assign by group when the mesh holds elements that must stay out of the model. In our
`shell_static` fixture the point groups (`POI1`) and the edge lines are left out: 400 of the
483 elements are assigned, and each `QUAD4` becomes a `MEDKQU4` (DKT quadrangle)
(`tests/fixtures/shell_static/output/run.mess`).

Source: `tests/fixtures/shell_static/input/run.comm:33`.

```python
MODE = AFFE_MODELE(
    MAILLAGE=MAIL, AFFE=_F(GROUP_MA="PLATE", PHENOMENE="MECANIQUE", MODELISATION="DKT")
)
```

### Solid plus springs

One `AFFE` per modeling. The `DIS_T` elements sit on a `POI1` group; their stiffness comes
from `AFFE_CARA_ELEM/DISCRET` (`upstream/astest/ssnd112a.comm:177`).

Source: `upstream/astest/ssnd112a.comm:54` (French comment kept).

```python
TROISD = AFFE_MODELE(
    MAILLAGE=MAIL,
    AFFE=(
        _F(
            TOUT="OUI",
            PHENOMENE="MECANIQUE",
            #  MODELISATION='3D_SI',
            MODELISATION="3D",
        ),
        _F(GROUP_MA=("PX1",), PHENOMENE="MECANIQUE", MODELISATION="DIS_T"),
    ),
)
```

### Quadratic shell: convert the mesh first

`COQUE_3D` needs 9-node quadrangles or 7-node triangles.

Source: `upstream/astest/ssls119c.comm:30`.

```python
MAIL = CREA_MAILLAGE(MAILLAGE=MA, MODI_MAILLE=_F(OPTION="QUAD8_9", TOUT="OUI"))

MO = AFFE_MODELE(AFFE=_F(TOUT="OUI", PHENOMENE="MECANIQUE", MODELISATION="COQUE_3D"), MAILLAGE=MAIL)
```

### Axisymmetric model

Source: `upstream/astest/hplv102a.comm:63`.

```python
MO = AFFE_MODELE(MAILLAGE=M, AFFE=_F(TOUT="OUI", PHENOMENE="MECANIQUE", MODELISATION="AXIS"))
```

## Pitfalls

- **Load faces left out of the model.** A pressure or surface force acts on boundary elements,
  and those exist only if `AFFE_MODELE` assigned the face elements. Assigning only the volume
  group leaves them out; use `TOUT='OUI'` or list the face groups too, as our `solid_static`
  fixture does (`tests/fixtures/solid_static/input/run.comm:22`).
- **A modeling that does not support the element type.** For each `AFFE` occurrence,
  elements of the modeling's own dimension that it cannot turn into finite elements trigger
  warning `MODELE1_70` with their count (`upstream/bibfor/op/op0018.F90:269`). Typical cases:
  `DKT` / `DST` on a quadratic (`TRIA6`, `QUAD8`) mesh, or `COQUE_3D` on `QUAD8` / `TRIA6`
  (see [Mechanical modeling types](#mechanical-modeling-types)). If no element at all is
  assigned the run stops with `MODELE1_6`; if none of the assigned elements can compute a
  stiffness, warning `MODELE1_64` gives the classic example of a `'3D'` modeling assigned to a
  mesh of surface facets only.
- **2D models need the mesh in the plane z = 0.** For `C_PLAN`, `D_PLAN` and `AXIS`, a mesh off
  that plane gives warning `MODELE1_3` (`upstream/bibfor/op/op0018.F90:236`); a truly 3D mesh
  gives `MODELE1_53`, whose text warns that results are wrong if the faces are not in a plane
  z = constant; a flat mesh at z ≠ 0 gives `MODELE1_58` (`upstream/bibfor/modelisa/modelCheck.F90:96`).
- **Axisymmetric meshes on the wrong side of the axis.** `AXIS` takes x as the radius: a node
  with x < 0 stops the run (`MAILLAGE1_2`, `MAILLAGE1_3`, `upstream/bibfor/soustruc/taxis.F90:89`);
  the message suggests `MODI_MAILLAGE/DEFORME` to move the mesh.
- **Distorted elements.** `VERI_JACOBIEN` reports elements whose Jacobian changes sign
  (`MAILLAGE1_1`, "too distorted"). With `DEBUT(ERREUR=_F(ALARME='EXCEPTION'))`, as in our
  fixtures, that warning stops the run. Fix the mesh rather than setting `VERI_JACOBIEN='NON'`.
- **Shell orientation is set elsewhere.** The local axes and normal of `DKT` / `DST` /
  `COQUE_3D` elements come from the mesh connectivity and from `AFFE_CARA_ELEM/COQUE`
  (`ANGL_REP` / `VECTEUR`); orient the normals with `MODI_MAILLAGE/ORIE_NORM_COQUE` before
  building the model (`tests/fixtures/shell_static/input/run.comm:27`).

## See also

- French reference: U4.41.01 (translation: `en/docs/U4.41.01.md` once task 5.x lands)
- Catalog: `en/commands/AFFE_MODELE.json` (generated from `upstream/code_aster/Cata/Commands/affe_modele.py:26`)
- Implementation: `upstream/code_aster/CodeCommands/affe_modele.py`; `upstream/bibfor/op/op0018.F90`;
  checks `upstream/bibfor/modelisa/modelCheck.F90`; modeling → element table
  `upstream/catalo/cataelem/Commons/phenomenons_modelisations.py`
- Before: `LIRE_MAILLAGE`, `MODI_MAILLAGE` (orient normals), `CREA_MAILLAGE` (convert element types)
- Next steps: `AFFE_CARA_ELEM` (shells, discrete elements), `AFFE_MATERIAU`, `AFFE_CHAR_MECA`
- Example: `upstream/astest/cont200a.comm` (line 41)
- Example: `upstream/astest/ssnd112a.comm` (line 54)
- Example: `upstream/astest/ssls119c.comm` (line 32)
- Example: `tests/fixtures/solid_static/input/run.comm` (line 23)
- Example: `tests/fixtures/shell_static/input/run.comm` (line 33)
