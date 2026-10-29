---
guide: walkthrough shell_static
title: "Walkthrough 2: a plate in bending"
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
sources:
  - tests/fixtures/shell_static/
  - en/commands/
  - en/guide/modelisations.md  # <!-- caen-allow: modelisation --> (file name)
doc_fr: none (our own guide, not a translation)
status: assisted
method: assisted
reviewed_by:
reviewed_on:
written_by: agent, in session (task 5.4)
---

# Walkthrough 2: a plate in bending

> **Assisted guide.** Built from our `shell_static` fixture and its committed run (code_aster
> 17.4.22). Hand checks are engineering judgement and are marked as such. Not reviewed by an
> engineer.

A square steel plate, simply supported on all four edges, under uniform pressure. The steps
are those of [Walkthrough 1](walkthrough-solid-static.md); this page covers only what is new
for shells: the shell modeling type, the thickness, the normal direction, point groups, and
results that are forces and moments per unit length.

| Item | Value |
|---|---|
| Geometry | Square plate, a = 1000 mm, thickness t = 10 mm, in the XY plane |
| Material | Steel, E = 210,000 MPa, ν = 0.3 |
| Supports | `DZ` = 0 on all four edges (simple support, rotations free); in-plane rigid-body motion restrained at two corners |
| Load | 0.01 MPa pressure on the whole plate, acting along −Z |
| Elements | 20 × 20 `QUAD4`, modeling type `DKT` (thin plate, Kirchhoff) |
| Checks | Center deflection, center bending moment and the reaction sum, against the Navier solution |

## 1. Mesh

A shell is meshed as a surface. `input/mesh.geo`:

<!-- example: tests/fixtures/shell_static/input/mesh.geo -->
```text
// shell_static: simply supported square plate, mid-surface in the XY plane (DKT/DKQ shell).
// Units: mm. Regenerate with:  gmsh -2 mesh.geo -format med -o mesh.med
// Four quadrants so that the plate centre is a mesh node (group CENTER).
a = 1000;   // side length
n = 10;     // elements per quadrant edge -> 20 x 20 QUAD4 over the plate
h = a/2;

Point(1) = {0, 0, 0};  Point(2) = {h, 0, 0};  Point(3) = {a, 0, 0};
Point(4) = {0, h, 0};  Point(5) = {h, h, 0};  Point(6) = {a, h, 0};
Point(7) = {0, a, 0};  Point(8) = {h, a, 0};  Point(9) = {a, a, 0};

// Boundary edges
Line(1) = {1, 2};  Line(2) = {2, 3};  Line(3) = {3, 6};  Line(4) = {6, 9};
Line(5) = {9, 8};  Line(6) = {8, 7};  Line(7) = {7, 4};  Line(8) = {4, 1};
// Interior lines through the centre
Line(9) = {2, 5};  Line(10) = {5, 8};  Line(11) = {4, 5};  Line(12) = {5, 6};

// Counter-clockwise loops seen from +Z, so element normals point to +Z.
Curve Loop(1) = {1, 9, -11, 8};    Plane Surface(1) = {1};
Curve Loop(2) = {2, 3, -12, -9};   Plane Surface(2) = {2};
Curve Loop(3) = {12, 4, 5, -10};   Plane Surface(3) = {3};
Curve Loop(4) = {11, 10, 6, 7};    Plane Surface(4) = {4};

Transfinite Curve {1:12} = n + 1;
Transfinite Surface {1:4};
Recombine Surface {1:4};

Physical Surface("PLATE") = {1, 2, 3, 4};
Physical Curve("EDGES") = {1:8};          // simply supported: DZ = 0
Physical Point("CENTER") = {5};           // maximum deflection
Physical Point("CORNER_A") = {1};         // in-plane rigid-body restraint DX = DY = 0
Physical Point("CORNER_B") = {3};         // in-plane rigid-body restraint DY = 0

Mesh.ElementOrder = 1;
Mesh.SaveAll = 0;
```

```bash
cd input && gmsh -2 mesh.geo -format med -o mesh.med && cd ..
```

Note `-2`: a surface mesh. Besides the plate (`PLATE`, 400 `QUAD4`) and its edges (`EDGES`, 80
`SEG2`), three physical *points* are named: `CENTER`, `CORNER_A`, `CORNER_B`. Gmsh writes each
as a `POI1` point element on a plate node (`tests/fixtures/shell_static/output/run.mess:118`–`:120`).
That is convenient (the command file can name the nodes it needs), but the mesh check of
`LIRE_MAILLAGE` reports each one with warning `MODELISA8_14`, "POI1 element is included in
another element". Here it is intended, so the command file ignores it (step 2).

## 2. Command file

The fixture's `input/run.comm`, unchanged:

<!-- example: tests/fixtures/shell_static/input/run.comm -->
```python
# shell_static -- simply supported square plate under uniform pressure (DKT, QUAD4 -> DKQ).
# codeaster-en test fixture (task 4.1). Units: mm, N, MPa.
# Plate a=1000, thickness t=10, E=210000, NU=0.3, pressure q=0.01 on the whole plate.
# Edges: DZ=0 (hard simple support, rotations free); two corners restrain in-plane rigid motion.
# Reference: Navier double series (Timoshenko & Woinowsky-Krieger, Theory of Plates and
# Shells, 2nd ed., sec. 30 and table 8): w_max = alpha q a^4 / D, M_x = beta q a^2 at the centre.
# Modelled on astest ssls101n (DKT, ORIE_NORM_COQUE, PRES_REP, TEST_RESU on DEPL DZ).
# VALE_CALC values are the solver's own results from the first run (task 4.2, code_aster
# 17.4.22 image, see ADR-011); TEST_RESU checks them at the default TOLE_MACHINE.

# The Gmsh mesh stores the point groups (CENTER, CORNER_A, CORNER_B) as POI1 cells on plate
# nodes, which the LIRE_MAILLAGE mesh check reports as alarm MODELISA8_14 ("POI1 cell included
# in another"). That is intended, so the alarm is ignored. ERREUR=_F(ALARME="EXCEPTION") cannot
# be kept with it: Utmess.py turns the alarm into an error before IGNORE_ALARM is consulted
# (seen in the first run, task 4.2). Any other alarm still shows in run.mess as <A> and makes
# the job diagnostic <A>_ALARM instead of OK, which tests/test_fixture_outputs.py rejects.
DEBUT(CODE="OUI", IGNORE_ALARM=("MODELISA8_14",))

Q = 0.01  # uniform pressure [MPa]
T = 10.0  # thickness [mm]

MAIL = LIRE_MAILLAGE(FORMAT="MED", UNITE=20)

MAIL = DEFI_GROUP(reuse=MAIL, MAILLAGE=MAIL, CREA_GROUP_NO=_F(TOUT_GROUP_MA="OUI"))

# Mesh normals already point to +Z; this makes the orientation explicit and checked.
MAIL = MODI_MAILLAGE(
    reuse=MAIL,
    MAILLAGE=MAIL,
    ORIE_NORM_COQUE=_F(GROUP_MA="PLATE", GROUP_NO="CENTER", VECT_NORM=(0.0, 0.0, 1.0)),
)

MODE = AFFE_MODELE(
    MAILLAGE=MAIL, AFFE=_F(GROUP_MA="PLATE", PHENOMENE="MECANIQUE", MODELISATION="DKT")
)

CARA = AFFE_CARA_ELEM(MODELE=MODE, COQUE=_F(GROUP_MA="PLATE", EPAIS=T, ANGL_REP=(0.0, 0.0)))

ACIER = DEFI_MATERIAU(ELAS=_F(E=210000.0, NU=0.3))

MATE = AFFE_MATERIAU(MAILLAGE=MAIL, AFFE=_F(GROUP_MA="PLATE", MATER=ACIER))

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

RESU = MECA_STATIQUE(
    MODELE=MODE,
    CHAM_MATER=MATE,
    CARA_ELEM=CARA,
    EXCIT=(_F(CHARGE=APPUI), _F(CHARGE=PRESS)),
    SOLVEUR=_F(METHODE="MUMPS"),
)

RESU = CALC_CHAMP(
    reuse=RESU, RESULTAT=RESU, CONTRAINTE=("EFGE_ELNO", "EFGE_NOEU"), FORCE="REAC_NODA"
)

REAC = POST_RELEVE_T(
    ACTION=_F(
        OPERATION="EXTRACTION",
        INTITULE="REAC_EDGES",
        RESULTAT=RESU,
        NOM_CHAM="REAC_NODA",
        GROUP_NO="EDGES",
        RESULTANTE=("DX", "DY", "DZ"),
    )
)

IMPR_TABLE(TABLE=REAC, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=30)

IMPR_RESU(
    FORMAT="MED",
    UNITE=80,
    RESU=_F(RESULTAT=RESU, CARA_ELEM=CARA, NOM_CHAM=("DEPL", "EFGE_NOEU", "REAC_NODA")),
)

TEST_RESU(
    RESU=(
        # Centre deflection: w = alpha q a^4 / D, alpha = 0.00406235 (NU=0.3), D = E t^3/(12(1-NU^2)).
        _F(
            NUME_ORDRE=1,
            RESULTAT=RESU,
            NOM_CHAM="DEPL",
            GROUP_NO="CENTER",
            NOM_CMP="DZ",
            REFERENCE="ANALYTIQUE",
            VALE_REFE=-2.11242,
            VALE_CALC=-2.112263828055923,
            PRECISION=1.0e-2,
            LEGENDE="W_CENTER",
        ),
        # Centre bending moment per unit length: M_x = -beta q a^2, beta = 0.0478864 (NU=0.3).
        # Negative: in the first run (task 4.2) EFGE_NOEU MXX = MYY < 0 at the centre while the
        # plate sags (DZ < 0), so the sagging moment is negative in code_aster's convention.
        _F(
            NUME_ORDRE=1,
            RESULTAT=RESU,
            NOM_CHAM="EFGE_NOEU",
            GROUP_NO="CENTER",
            NOM_CMP="MXX",
            REFERENCE="ANALYTIQUE",
            VALE_REFE=-478.864,
            VALE_CALC=-479.645314641979,
            PRECISION=3.0e-2,
            LEGENDE="MXX_CENTER",
        ),
        # Reaction sum = +q a^2 (whole REAC_NODA field; only supported nodes carry reactions).
        # Positive: REAC_NODA is the support reaction, opposite to the -Z load (first run, 4.2).
        _F(
            NUME_ORDRE=1,
            RESULTAT=RESU,
            NOM_CHAM="REAC_NODA",
            NOM_CMP="DZ",
            TYPE_TEST="SOMM",
            REFERENCE="ANALYTIQUE",
            VALE_REFE=10000.0,
            VALE_CALC=9999.999999999982,
            PRECISION=1.0e-3,
            LEGENDE="REAC_DZ_SUM",
        ),
    )
)

FIN()
```

For your own study, change `DEBUT(CODE="OUI", IGNORE_ALARM=("MODELISA8_14",))` to
`DEBUT(IGNORE_ALARM=("MODELISA8_14",))`: `CODE` is for test cases. You can keep `TEST_RESU`; it
prints `OK` or `NOOK` in the log for each check.

What is new compared with the solid:

- **Node groups from every element group.** `CREA_GROUP_NO=_F(TOUT_GROUP_MA="OUI")` makes a node
  group for each element group in one call, so `EDGES`, `CENTER` and the corners are available
  as node groups too ([`DEFI_GROUP`](../commands/DEFI_GROUP.md)).
- **The shell normal.** A shell has two faces, and its normal decides which way a pressure
  pushes and which face is "upper" for stresses. [`MODI_MAILLAGE`](../commands/MODI_MAILLAGE.md)
  `ORIE_NORM_COQUE` makes all normals of `PLATE` consistent and points them along
  `VECT_NORM` (+Z) at the `CENTER` node. Do it on every shell group.
- **The modeling type.** `MODELISATION="DKT"` makes thin-plate elements: on `QUAD4` they are
  `MEDKQU4` (DKQ), on `TRIA3` `MEDKTR3` (`tests/fixtures/shell_static/output/run.mess:197`). The
  model is assigned on `PLATE` only, so 400 of the 483 elements become finite elements
  (`:194`); edges and points stay mesh-only, which is fine because the supports act on their
  nodes. For when to use `DST` or `COQUE_3D` instead, see [Modeling types](modelisations.md).
- **The thickness.** [`AFFE_CARA_ELEM`](../commands/AFFE_CARA_ELEM.md) `COQUE` gives the
  thickness, `EPAIS=10.0`, and the reference direction for the local axes, `ANGL_REP=(0.0, 0.0)`:
  local x is the projection of global X on each element. Shell results are reported in these
  local axes. The element properties must then be passed to `MECA_STATIQUE` (`CARA_ELEM=CARA`)
  and to `IMPR_RESU`.
- **Supports on a plate.** `DZ=0.0` on the edges alone leaves the plate free to slide and spin
  in its own plane: three in-plane rigid-body motions. `CORNER_A` (DX, DY) and `CORNER_B` (DY)
  remove exactly those three without adding in-plane stress. The log counts 83 restrained DOF:
  80 edge nodes in Z, plus 3 at the corners (`tests/fixtures/shell_static/output/run.mess:328`–`:329`).
  Rotations are left free: that is what "simply supported" means here.
- **The pressure sign.** A positive `PRES` pushes against the shell normal. The normal is +Z, so
  `PRES=0.01` pushes the plate down, along −Z (comment at
  `tests/fixtures/shell_static/input/run.comm:52`; [`AFFE_CHAR_MECA`](../commands/AFFE_CHAR_MECA.md)).
- **Results are resultants.** `CALC_CHAMP CONTRAINTE=("EFGE_ELNO", "EFGE_NOEU")` computes the
  shell forces and moments per unit length (`NXX`, ..., `MXX`, `MYY`, `MXY`, `QX`, `QY`). Stress
  through the thickness is a separate request (see [Result fields](fields.md)).

## 3. Run and check the log

Run as in [Walkthrough 1, step 5](walkthrough-solid-static.md#5-run), using the
`run.export` of the fixture (`tests/fixtures/shell_static/input/run.export`; the same units as
the solid). The job diagnostic is `OK`. The `FIN` summary lists the ignored warning with a `(*)`:

```text
 ║     Les alarmes que vous avez choisies d'ignorer sont précédées de (*).                        ║
 ║     Nombre d'occurrences pour chacune des alarmes :                                            ║
 ║        (*) MODELISA8_14         émise    3 fois                                                ║
```

(`tests/fixtures/shell_static/output/run.mess:503`–`:505`: "warnings you chose to ignore are
marked (*)", "issued 3 times".) An ignored warning does not change the job diagnostic.

Do not combine `IGNORE_ALARM` with `ERREUR=_F(ALARME="EXCEPTION")`: the warning is turned into an
error before the ignore list is read, so the run stops anyway
([`DEBUT`](../commands/DEBUT.md), Pitfalls).

## 4. Check the result

The Navier double series for a simply supported square plate under uniform pressure gives
(Timoshenko and Woinowsky-Krieger, *Theory of Plates and Shells*, 2nd ed., §30 and table 8;
values computed in `tests/fixtures/hand_values.py`):

- plate stiffness D = E t³ / (12 (1 − ν²)) = 1.923 × 10⁷ N·mm,
- center deflection w = 0.00406235 q a⁴ / D = 2.11242 mm (downward),
- center bending moment M = 0.0478864 q a² = 478.864 N·mm/mm.

| Check | Hand value | Run | Difference |
|---|---|---|---|
| Center `DZ` of `DEPL` | −2.11242 mm | −2.11226 mm | 0.007 % |
| Center `MXX` of `EFGE_NOEU` | −478.864 N·mm/mm | −479.645 N·mm/mm | 0.16 % |
| Sum of `REAC_NODA` `DZ` | 10,000 N (q a²) | 10,000.000 N | 0 |

(`tests/fixtures/README.md`, "Hand values"; `tests/fixtures/shell_static/output/tables/reactions.csv`.)

Two sign points, both confirmed by the run:

- The deflection is negative: the plate moves along −Z under a load along −Z.
- The sagging moment `MXX` is negative in this model. The sign of a shell moment depends on the
  normal: flip `VECT_NORM` and the sign flips. Check the sign on a case you know before you
  label a face "in tension" (`TODO(verify)` the general convention, see
  [Result fields](fields.md#shell-and-beam-resultants-efge_-dege_-sipo_)).

The bending stress at the plate surface follows from the moment (engineering judgement, thin
plate): σ = 6 M / t² = 6 × 479.6 / 10² = 28.8 MPa at the center.

With `caen`:

```console
$ caen results extrema tests/fixtures/shell_static/output EFGE_NOEU MXX
EFGE_NOEU bending moment XX (MXX), whole model (step 1, 441 values):
  min -479.6 at node 5 (500, 500, 0)
  max 0.3661 at node 45 (1000, 950, 0)
```

## Things to watch on shells

- **Normals of several groups.** `ORIE_NORM_COQUE` orients each group from its own seed. Two
  groups that share an edge can end up with opposite normals if you give them different
  `VECT_NORM`; their moments then have opposite signs across the joint (engineering
  judgement).
- **Warped quadrangles.** A `QUAD4` that is not flat gives warning `PLATE1_81` ("can lead to
  wrong results"); see [Modeling types](modelisations.md).
- **Mesh in the mid-surface.** `DKT` elements sit on the mid-surface of the plate. Model a
  plate of thickness t by its mid-plane, not by one face (engineering judgement; the usual shell
  convention, `TODO(verify)` against U3 documentation for `DKT` offsets).

Next: [Walkthrough 3: natural frequencies](walkthrough-modal.md).
