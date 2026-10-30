---
guide: walkthrough solid_static
title: "Walkthrough 1: a solid under internal pressure"
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
sources:
  - tests/fixtures/solid_static/
  - en/commands/
doc_fr: none (our own guide, not a translation)
status: assisted
method: assisted
reviewed_by:
reviewed_on:
written_by: agent, in session (task 5.4)
---

# Walkthrough 1: a solid under internal pressure

> **Assisted guide.** Built from our `solid_static` fixture. The files below were run exactly as
> printed, in session, with the pinned image, and gave the results quoted. Hand checks and advice
> are engineering judgement and are marked as such. Not reviewed by an engineer.

This walkthrough takes you through a complete linear static analysis: a short steel cylinder
with a radial nozzle, fixed at its base and loaded by internal pressure. You will make the
mesh, write the command file and the export file, run the solver, check the log, and check the
result against a hand calculation. Read [Concepts](concepts.md) first; this page assumes its
vocabulary.

| Item | Value |
|---|---|
| Geometry | Cylinder, inner radius 100 mm, outer radius 120 mm, height 300 mm, axis Z. Radial nozzle on +X at Z = 150 mm, bore radius 25 mm, outer radius 35 mm, open end at X = 220 mm. |
| Material | Steel, E = 210,000 MPa, ν = 0.3 |
| Supports | Base (Z = 0) fixed in X, Y and Z |
| Load | 2 MPa on the inner wall of the cylinder and on the nozzle bore. No end caps. |
| Elements | 4-node tetrahedra (`TETRA4`), modeling type `3D` |
| Units | mm, N, MPa |
| Check | The sum of the support reactions balances the pressure resultant: 3891.64 N along +X |

## 1. Set up the study directory

```bash
mkdir -p study/input study/output
cd study
```

Everything you write goes in `input/`; the solver writes to `output/`. This is the job layout
of our fixtures and of ClearFEA (`docs/CLEARFEA-INTEGRATION.md` §3).

## 2. Make the mesh

Save this Gmsh script as `input/mesh.geo`. It builds the solid with OpenCASCADE booleans and
names six regions as physical groups. The names are what the command file will use.

<!-- example: tests/fixtures/solid_static/input/mesh.geo -->
```text
// solid_static: short cylindrical shell with one radial nozzle (3D, linear tetrahedra).
// Units: mm. Regenerate with:  gmsh -3 mesh.geo -format med -o mesh.med
// Physical groups become MED groups read by run.comm (LIRE_MAILLAGE).
SetFactory("OpenCASCADE");

Ri = 100;  Ro = 120;  H = 300;     // shell inner/outer radius, height (axis = Z)
ri = 25;   ro = 35;   Ln = 220;    // nozzle bore/outer radius, end position on +X
Zn = H/2;                          // nozzle axis height
e  = 1e-3;                         // bounding-box tolerance

Cylinder(1) = {0, 0, 0, 0, 0, H, Ro};
Cylinder(2) = {0, 0, Zn, Ln, 0, 0, ro};
Cylinder(3) = {0, 0, 0, 0, 0, H, Ri};
Cylinder(4) = {0, 0, Zn, Ln, 0, 0, ri};
outer() = BooleanUnion{ Volume{1}; Delete; }{ Volume{2}; Delete; };
BooleanDifference(10) = { Volume{outer()}; Delete; }{ Volume{3, 4}; Delete; };

base()  = Surface In BoundingBox{-Ro-e, -Ro-e, -e, Ro+e, Ro+e, e};
top()   = Surface In BoundingBox{-Ro-e, -Ro-e, H-e, Ro+e, Ro+e, H+e};
nend()  = Surface In BoundingBox{Ln-e, -ro-e, Zn-ro-e, Ln+e, ro+e, Zn+ro+e};
wall()  = Surface In BoundingBox{-Ri-e, -Ri-e, -e, Ri+e, Ri+e, H+e};
bore()  = Surface In BoundingBox{0, -ri-e, Zn-ri-e, Ln+e, ri+e, Zn+ri+e};

Physical Volume("SOLID") = {10};
Physical Surface("BASE") = {base()};        // fixed (all DOF)
Physical Surface("TOP") = {top()};          // free
Physical Surface("NOZ_END") = {nend()};     // free, open nozzle end
Physical Surface("P_SHELL") = {wall()};     // internal pressure, shell inner wall
Physical Surface("P_NOZZLE") = {bore()};    // internal pressure, nozzle bore

Mesh.MeshSizeMin = 6;
Mesh.MeshSizeMax = 14;
// Refine around the shell/nozzle junction.
Field[1] = Distance;  Field[1].SurfacesList = {bore()};
Field[2] = Threshold; Field[2].InField = 1;
Field[2].SizeMin = 6; Field[2].SizeMax = 14; Field[2].DistMin = 10; Field[2].DistMax = 60;
Background Field = 2;
Mesh.MeshSizeExtendFromBoundary = 0;
Mesh.MeshSizeFromPoints = 0;
Mesh.ElementOrder = 1;
Mesh.Optimize = 1;
Mesh.SaveAll = 0;
```

| Physical group | Dimension | Used for |
|---|---|---|
| `SOLID` | volume | the material |
| `BASE` | surface | the support |
| `P_SHELL`, `P_NOZZLE` | surface | the pressure |
| `TOP`, `NOZ_END` | surface | nothing (free edges); named so you can look at them later |

Mesh it and write MED:

```bash
cd input
gmsh -3 mesh.geo -format med -o mesh.med
cd ..
```

With Gmsh 4.15.2 the mesh has 4,622 nodes, 14,439 `TETRA4` and 4,339 `TRIA3`
(`tests/fixtures/solid_static/output/run.mess:115`–`:119`). Another Gmsh version can give a
slightly different mesh, and the numbers below will then differ in the last digits.

Two points matter here, and they are easy to miss:

- **The surface groups must be meshed too.** The pressure is applied on face elements
  (`TRIA3`), not on the faces of the tetrahedra. Gmsh writes the face elements because each
  pressure surface is in a physical group (`Mesh.SaveAll = 0` writes only elements in physical
  groups).
- **Linear tetrahedra are stiff.** `Mesh.ElementOrder = 1` keeps the run fast for a tutorial.
  For a design check, use quadratic elements (`Mesh.ElementOrder = 2`, giving `TETRA10`) or a
  finer mesh. This is engineering judgement; see step 7 for what it does to this result.

## 3. Write the command file

Save this as `input/run.comm`:

<!-- example-study: tests/fixtures/solid_static/input/run.comm -->
```python
# Cylindrical shell with a radial nozzle under internal pressure.
# Units: mm, N, MPa.

DEBUT()

P = 2.0  # internal pressure [MPa]

# 1. Mesh, node group of the base, outward normals on the pressure faces
MAIL = LIRE_MAILLAGE(FORMAT="MED", UNITE=20)

MAIL = DEFI_GROUP(reuse=MAIL, MAILLAGE=MAIL, CREA_GROUP_NO=_F(GROUP_MA="BASE"))

MAIL = MODI_MAILLAGE(reuse=MAIL, MAILLAGE=MAIL, ORIE_PEAU=_F(GROUP_MA_PEAU=("P_SHELL", "P_NOZZLE")))

# 2. Model: 3D solid elements on the whole mesh (the skin faces carry the pressure)
MODE = AFFE_MODELE(MAILLAGE=MAIL, AFFE=_F(TOUT="OUI", PHENOMENE="MECANIQUE", MODELISATION="3D"))

# 3. Material
ACIER = DEFI_MATERIAU(ELAS=_F(E=210000.0, NU=0.3))

MATE = AFFE_MATERIAU(MAILLAGE=MAIL, AFFE=_F(GROUP_MA="SOLID", MATER=ACIER))

# 4. Support and load
FIXE = AFFE_CHAR_MECA(MODELE=MODE, DDL_IMPO=_F(GROUP_MA="BASE", DX=0.0, DY=0.0, DZ=0.0))

PRESS = AFFE_CHAR_MECA(MODELE=MODE, PRES_REP=_F(GROUP_MA=("P_SHELL", "P_NOZZLE"), PRES=P))

# 5. Solve
RESU = MECA_STATIQUE(
    MODELE=MODE,
    CHAM_MATER=MATE,
    EXCIT=(_F(CHARGE=FIXE), _F(CHARGE=PRESS)),
    SOLVEUR=_F(METHODE="MUMPS"),
)

# 6. Stresses, von Mises, reactions
RESU = CALC_CHAMP(
    reuse=RESU,
    RESULTAT=RESU,
    CONTRAINTE=("SIGM_ELNO", "SIGM_NOEU"),
    CRITERES=("SIEQ_ELNO", "SIEQ_NOEU"),
    FORCE="REAC_NODA",
)

# 7. Reaction resultant on the base, printed to tables/reactions.csv
REAC = POST_RELEVE_T(
    ACTION=_F(
        OPERATION="EXTRACTION",
        INTITULE="REAC_BASE",
        RESULTAT=RESU,
        NOM_CHAM="REAC_NODA",
        GROUP_NO="BASE",
        RESULTANTE=("DX", "DY", "DZ"),
    )
)

IMPR_TABLE(TABLE=REAC, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=30)

# 8. Fields for the viewer, written to run.rmed
IMPR_RESU(
    FORMAT="MED",
    UNITE=80,
    RESU=_F(RESULTAT=RESU, NOM_CHAM=("DEPL", "SIGM_NOEU", "SIEQ_NOEU", "REAC_NODA")),
)

FIN()
```

What each block does, with the reference page for each command:

1. [`DEBUT`](../commands/DEBUT.md) opens the study with default settings. Our fixture uses
   `DEBUT(CODE="OUI", ...)`, which is reserved for test cases: the solver prints `SUPERVIS_22`
   to say so (`tests/fixtures/solid_static/output/run.mess:38`). In a study, leave it out.
2. [`LIRE_MAILLAGE`](../commands/LIRE_MAILLAGE.md) reads unit 20 (the `.med` file).
   [`DEFI_GROUP`](../commands/DEFI_GROUP.md) makes a node group `BASE` from the element group
   `BASE`, for the reaction table in step 7. [`MODI_MAILLAGE`](../commands/MODI_MAILLAGE.md)
   `ORIE_PEAU` turns the normals of the pressure faces outward, so that a positive pressure
   pushes into the solid. Gmsh already had them outward here, so it turned none
   (`tests/fixtures/solid_static/output/run.mess:166`–`:169`), but do it every time: a reversed
   normal reverses the load, and `AFFE_CHAR_MECA` stops on it (`MODELISA8_56`).
3. [`AFFE_MODELE`](../commands/AFFE_MODELE.md) makes `3D` solid elements on the tetrahedra and
   face elements on the triangles (`MECA_TETRA4`, `MECA_FACE3`,
   `tests/fixtures/solid_static/output/run.mess:192`–`:194`). `TOUT="OUI"` matters: if the
   model were assigned on `SOLID` only, the pressure faces would have no elements to carry the
   pressure.
4. [`DEFI_MATERIAU`](../commands/DEFI_MATERIAU.md) and [`AFFE_MATERIAU`](../commands/AFFE_MATERIAU.md)
   define steel and put it on the volume group. Face elements need no material.
5. Two [`AFFE_CHAR_MECA`](../commands/AFFE_CHAR_MECA.md) calls: `FIXE` holds the support,
   `PRESS` the pressure. Keeping them separate lets you reuse the support with other loads.
6. [`MECA_STATIQUE`](../commands/MECA_STATIQUE.md) solves the load case `EXCIT` = support +
   pressure, with the MUMPS direct solver.
7. [`CALC_CHAMP`](../commands/CALC_CHAMP.md) adds stress (`SIGM_ELNO`, `SIGM_NOEU`), equivalent
   stress (`SIEQ_ELNO`, `SIEQ_NOEU`, which hold von Mises and Tresca) and the nodal reactions
   (`REAC_NODA`) to `RESU`.
8. [`POST_RELEVE_T`](../commands/POST_RELEVE_T.md) sums `REAC_NODA` over the `BASE` nodes and
   [`IMPR_TABLE`](../commands/IMPR_TABLE.md) prints it as CSV to unit 30.
9. [`IMPR_RESU`](../commands/IMPR_RESU.md) writes four fields to the MED result file, unit 80.
10. [`FIN`](../commands/FIN.md) ends the study.

## 4. Write the export file

Save this as `input/run.export`:

<!-- example: tests/fixtures/solid_static/input/run.export -->
```text
P time_limit 600
P memory_limit 2048
P ncpus 1
P mpi_nbcpu 1
P mpi_nbnoeud 1
F comm run.comm D 1
F mmed mesh.med D 20
F mess ../output/run.mess R 6
F resu ../output/run.resu R 8
F libr ../output/tables/reactions.csv R 30
F rmed ../output/run.rmed R 80
```

Each `F` line is one file: its type, its path relative to `input/`, `D` (read) or `R`
(written), and its logical unit. The logical units must match the `UNITE=` values in the command
file: 20 for the mesh, 30 for the table, 80 for the results. Units 6 (the log) and 8 are
written by the solver itself. `P` lines set a 600 s time limit, 2048 MB of memory and one
processor ([Concepts](concepts.md#files-and-logical-units)).

## 5. Run

From the `study/` directory, with the image pinned in this repository's `CONTAINER_IMAGE`:

```bash
IMG=simvia/code_aster:17.4.22@sha256:ac8e68feee27329717f9350c2782f63d860dd4771b267c43e47bf588a00005eb
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$PWD/input:/work/input:ro" -v "$PWD/output:/work/output" \
  -w /work/input "$IMG" \
  bash -c 'source /opt/activate.sh && run_aster run.export' > output/run_aster.stdout 2>&1
echo "exit code $?"
```

- `--user "$(id -u):$(id -g)"` runs the solver as you, so it can write to `output/`. Without
  it the container runs as its own user (uid 1000) and, unless that is your uid, the run fails
  with `PermissionError` on `run.mess` (seen in session).
- `source /opt/activate.sh` puts `run_aster` on the path inside this image
  (`scripts/run-fixture.sh`).
- The run takes a few seconds. `run_aster` creates `output/tables/` itself.

If you work in this repository, `scripts/run-fixture.sh <case-dir>` does the same, and also
writes `exit_code` and `provenance.json`.

## 6. Check that it ran

Look at the last lines of `output/run_aster.stdout`:

```text
--- DIAGNOSTIC JOB : OK
```

`OK` means no error and no warning. `<A>_ALARM` means the run finished with warnings (read
them); `<S>_ERROR` or `<F>_...` means it stopped ([Reading the log](reading-logs.md)). The exit
code is 0 for `OK` and `<A>_ALARM`, 1 for an error (`docs/CLEARFEA-INTEGRATION.md` §4).

Then open `output/run.mess` and check three things:

1. **The mesh is what you expected:** the node and element counts after `LIRE_MAILLAGE`.
2. **The model took every element:** the table after `AFFE_MODELE` lists each element type
   and the finite element it became. "Sur les 18778 mailles du maillage ..., on a pu en
   affecter 18778" means all 18,778 elements were assigned
   (`tests/fixtures/solid_static/output/run.mess:190`).
3. **No warnings:** the box `<I> <CATAMESS_89>` printed by `FIN` lists the warnings of the
   whole run with their counts. Here it says "aucune alarme", none
   (`tests/fixtures/solid_static/output/run.mess:433`–`:440`).

If you have `codeaster-en` installed, `caen mess parse output/run.mess` gives the same verdict
in one line, and `caen mess translate output/run.mess` writes an English copy of the log.

## 7. Check the result

**Equilibrium first.** `output/tables/reactions.csv`:

```text
INTITULE,RESU,NOM_CHAM,NUME_ORDRE,INST,DX,DY,DZ
REAC_BASE       ,00000007,REAC_NODA       ,           1, 0.00000E+00, 3.89164E+03,-1.77693E-10, 1.27073E-10
```

The pressure on the inner wall of a complete cylinder cancels out. What does not cancel is the
pressure missing over the hole where the nozzle meets the wall: the nozzle bore is open at its
end, so nothing balances it, and the net applied force is P times the projected area of the
bore opening, along −X. For a true circle that is 2 × π × 25² = 3927 N; on the faceted mesh it
is 3891.64 N (`tests/fixtures/hand_values.py`). The reaction `DX` is +3891.64 N: equal and
opposite, as it must be, because `REAC_NODA` is the force the support applies to the structure.
`DY` and `DZ` are zero to round-off. If equilibrium does not hold, stop and find out why
before looking at stresses.

**Then the stresses.** With `caen` installed:

```console
$ caen results extrema output SIEQ_NOEU VMIS
SIEQ_NOEU von Mises (VMIS), whole model (step 1, 4622 values):
  min 2.135 at node 1810 (140.6, -0.0818181, 115)
  max 34.74 at node 9 (100, -9.18485e-15, 175)
```

Or open `output/run.rmed` in a viewer and plot `SIEQ_NOEU`, component `VMIS`. The maximum von
Mises stress, 34.7 MPa, is at the inner corner where the top of the nozzle bore meets the
cylinder wall (X = 100, Z = 175 = 150 + 25).

A hand check away from the nozzle (engineering judgement). Equilibrium of half the cylinder
fixes the hoop force per unit height exactly: the hoop stress averaged through the wall is
P Ri / (Ro − Ri) = 2 × 100 / 20 = 10.0 MPa, whatever the stress distribution. On the side
opposite the nozzle (X ≈ −100 to −120, |Y| < 15, Z = 200 to 260), the hoop stress `SIYY` of
`SIGM_NOEU` in the run is 10.7 MPa at the inner surface and 9.2 MPa at the outer surface, an
average of 9.9 MPa (computed in session from `output/run.rmed`). The thick-cylinder (Lamé)
values for a plain cylinder are 11.1 and 9.1 MPa. The average agrees within 1 %. The split
between inner and outer surfaces does not follow Lamé exactly, because the nozzle opening also
bends the wall, and linear tetrahedra, about two through the thickness, capture through-thickness
bending poorly.

The peak is where the mesh matters most. The same model with quadratic elements
(`Mesh.ElementOrder = 2`: 28,074 nodes, `TETRA10`, run in session) gives a maximum von Mises
stress of 46.7 MPa at the same node, 35 % above the linear mesh. Treat 34.7 MPa as a lower
bound: report a peak only when a refined or quadratic mesh agrees with it.

**Displacements:** the largest is 0.0077 mm, at the free top edge
(`caen results extrema output DEPL DX DY DZ`).

## 8. Write the report (optional)

`caen report` writes an English engineering report from the job directory. It needs a
`run.json` next to `run.comm` (title block, units, group names;
`docs/schemas/run.schema.json`); copy `tests/fixtures/solid_static/input/run.json` to start.

```bash
caen report . --no-pdf     # writes report/report.md, report.html, run_model.json
```

## Things to try next

Each of these changes one thing and shows one behavior. Rerun after each.

| Change | What you will see |
|---|---|
| Write `GROUP_MA="BASES"` in `FIXE` | The run stops in `AFFE_CHAR_MECA` with `<EXCEPTION> <MODELISA7_77>`: the group is not in the mesh ([FAQ](faq.md)). |
| Remove `_F(CHARGE=FIXE)` from `EXCIT` | The structure is free to move as a rigid body; the factorization stops with `FACTOR_11`, a singular matrix ([FAQ](faq.md)). |
| Write `PRESSION=P` instead of `PRES=P` | The catalog check stops `AFFE_CHAR_MECA` with `SUPERVIS_4` before it runs ([FAQ](faq.md)). |
| Set `Mesh.ElementOrder = 2` in `mesh.geo` | `TETRA10` and `TRIA6` elements, a run about 2.5 times longer, a von Mises peak of 46.7 MPa instead of 34.7, and a reaction `DX` of 3926.97 N: the curved faces now match the true circle, 2 × π × 25² = 3927 N. |
| Change `P` to 4.0 | Every displacement, stress and reaction doubles: the analysis is linear (not run; it follows from linearity). |

All four were run in session on this model and gave the result shown. The first three are
also our broken fixtures, made from `shell_static` (`tests/fixtures/README.md`, "Broken runs").

Next: [Walkthrough 2: plate in bending](walkthrough-shell-static.md).
