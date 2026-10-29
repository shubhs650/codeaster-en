---
guide: walkthrough modal
title: "Walkthrough 3: natural frequencies of a cantilever"
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
sources:
  - tests/fixtures/modal/
  - en/commands/CALC_MODES.md
  - en/commands/NORM_MODE.md
doc_fr: none (our own guide, not a translation)
status: assisted
method: assisted
reviewed_by:
reviewed_on:
written_by: agent, in session (task 5.4)
---

# Walkthrough 3: natural frequencies of a cantilever

> **Assisted guide.** Built from our `modal` fixture and its committed run (code_aster 17.4.22).
> Hand checks are engineering judgement and are marked as such. Not reviewed by an engineer.

A steel bar clamped at one end, modeled with 3D solid elements: find its six lowest natural
frequencies and mode shapes, and check them against beam theory. Read
[Walkthrough 1](walkthrough-solid-static.md) first; this page covers what is new for a modal
analysis: density, matrices, the eigensolver, mode normalization and effective mass.

| Item | Value |
|---|---|
| Geometry | Bar 400 mm long along X, section 20 mm (Y) × 10 mm (Z) |
| Material | Steel, E = 210,000 MPa, ν = 0.3, ρ = 7.85e-9 t/mm³ |
| Supports | Face X = 0 clamped (`DX` = `DY` = `DZ` = 0) |
| Elements | 80 × 4 × 2 `HEXA20` (20-node quadratic bricks), modeling type `3D` |
| Units | mm, N, MPa, tonne, s (so frequencies come out in Hz) |
| Checks | Frequencies against Euler–Bernoulli bending and Saint-Venant torsion; mode 1 generalized mass = 1 |

## 1. Mesh

`input/mesh.geo` builds a structured mesh: a meshed end face extruded along X.

<!-- example: tests/fixtures/modal/input/mesh.geo -->
```text
// modal: 3D cantilever beam, rectangular section, quadratic hexahedra (HEXA20).
// Units: mm. Regenerate with:  gmsh -3 mesh.geo -format med -o mesh.med
// Axis X (length L), width b along Y, depth h along Z.
L = 400;  b = 20;  h = 10;
nx = 80;  ny = 4;  nz = 2;   // 5 mm hexahedra

Point(1) = {0, 0, 0};  Point(2) = {0, b, 0};  Point(3) = {0, b, h};  Point(4) = {0, 0, h};
Line(1) = {1, 2};  Line(2) = {2, 3};  Line(3) = {3, 4};  Line(4) = {4, 1};
Curve Loop(1) = {1, 2, 3, 4};  Plane Surface(1) = {1};
Transfinite Curve {1, 3} = ny + 1;
Transfinite Curve {2, 4} = nz + 1;
Transfinite Surface {1};
Recombine Surface {1};
ext[] = Extrude {L, 0, 0} { Surface{1}; Layers{nx}; Recombine; };
// ext[0] = end face at X = L, ext[1] = volume

Physical Volume("BEAM") = {ext[1]};
Physical Surface("CLAMP") = {1};      // X = 0, all DOF fixed
Physical Surface("TIP") = {ext[0]};   // X = L, free end

Mesh.ElementOrder = 2;
Mesh.SecondOrderIncomplete = 1;       // 20-node serendipity hexahedra
Mesh.SaveAll = 0;
```

```bash
cd input && gmsh -3 mesh.geo -format med -o mesh.med && cd ..
```

Quadratic bricks (`Mesh.ElementOrder = 2` with `SecondOrderIncomplete`, giving 20-node
`HEXA20`) are a good choice for a bending-dominated solid model: linear elements of the same
size would be much too stiff in bending (engineering judgement). Two elements through the 10 mm
depth are enough with `HEXA20`, as the results below show.

## 2. Command file

The fixture's `input/run.comm`:

<!-- example: tests/fixtures/modal/input/run.comm -->
```python
# modal -- 3D cantilever beam, first 6 natural frequencies (HEXA20).
# codeaster-en test fixture (task 4.1). Units: mm, N, MPa, tonne, s (density in t/mm3).
# Beam L=400 along X, section b=20 (Y) x h=10 (Z), steel E=210000, NU=0.3, RHO=7.85e-9.
# Face X=0 clamped. Reference: Euler-Bernoulli cantilever,
#   f_n = lambda_n^2 / (2 pi L^2) * sqrt(E I / (RHO A)),
#   lambda_n = 1.8751, 4.6941, 7.8548, 10.9955; I = b h^3/12 (bending in Z) or h b^3/12 (in Y).
# Mode 6 is the first torsion mode, f = 1/(4L) sqrt(G J / (RHO Ip)), Saint-Venant J (warping
# ignored). Expected order: Z1, Y1, Z2, Y2, Z3, T1 (Z4 ~ 1.80 kHz and axial ~ 3.2 kHz are higher).
# Modelled on astest sdlv100a (CALC_MATR_ELEM/NUME_DDL/ASSE_MATRICE, POST_ELEM MASS_INER,
# TEST_RESU on PARA="FREQ") and sdll05a (CALC_MODES OPTION="PLUS_PETITE", NMAX_FREQ).
# VALE_CALC values are the solver's own results from the first run (task 4.2, code_aster
# 17.4.22 image, see ADR-011); TEST_RESU checks them at the default TOLE_MACHINE.

DEBUT(CODE="OUI", ERREUR=_F(ALARME="EXCEPTION"))

MAIL = LIRE_MAILLAGE(FORMAT="MED", UNITE=20)

MODE = AFFE_MODELE(
    MAILLAGE=MAIL, AFFE=_F(GROUP_MA="BEAM", PHENOMENE="MECANIQUE", MODELISATION="3D")
)

ACIER = DEFI_MATERIAU(ELAS=_F(E=210000.0, NU=0.3, RHO=7.85e-9))

MATE = AFFE_MATERIAU(MAILLAGE=MAIL, AFFE=_F(GROUP_MA="BEAM", MATER=ACIER))

ENCAS = AFFE_CHAR_MECA(MODELE=MODE, DDL_IMPO=_F(GROUP_MA="CLAMP", DX=0.0, DY=0.0, DZ=0.0))

# Mass and inertia of the model: mass = RHO * b * h * L = 6.28e-4 t.
MASSE = POST_ELEM(MODELE=MODE, CHAM_MATER=MATE, MASS_INER=_F(TOUT="OUI"))

IMPR_TABLE(TABLE=MASSE, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=30)

RIGI_EL = CALC_MATR_ELEM(MODELE=MODE, CHAM_MATER=MATE, CHARGE=ENCAS, OPTION="RIGI_MECA")

MASS_EL = CALC_MATR_ELEM(MODELE=MODE, CHAM_MATER=MATE, CHARGE=ENCAS, OPTION="MASS_MECA")

NUME = NUME_DDL(MATR_RIGI=RIGI_EL)

RIGI = ASSE_MATRICE(MATR_ELEM=RIGI_EL, NUME_DDL=NUME)

MASS = ASSE_MATRICE(MATR_ELEM=MASS_EL, NUME_DDL=NUME)

MODES = CALC_MODES(MATR_RIGI=RIGI, MATR_MASS=MASS, OPTION="PLUS_PETITE", CALC_FREQ=_F(NMAX_FREQ=6))

# CALC_MODES scales each shape to a largest component of 1 (bibfor/algeline/vppara.F90); NORM_MODE
# rescales them to a unit generalized mass, the usual form for modal superposition (task 6.4).
MODES = NORM_MODE(reuse=MODES, MODE=MODES, NORME="MASS_GENE")

IMPR_RESU(FORMAT="MED", UNITE=80, RESU=_F(RESULTAT=MODES, NOM_CHAM="DEPL"))

# Modal parameters stored by CALC_MODES (bibfor/algeline/vpstor.F90), printed for the modal
# table of the results reader and the report (task 4.5): frequency, generalized mass and the
# effective masses per direction. RECU_TABLE with NOM_PARA as in astest zzzz399a.
PARA = RECU_TABLE(
    CO=MODES,
    NOM_PARA=(
        "FREQ",
        "MASS_GENE",
        "MASS_EFFE_DX",
        "MASS_EFFE_DY",
        "MASS_EFFE_DZ",
        "MASS_EFFE_UN_DX",
        "MASS_EFFE_UN_DY",
        "MASS_EFFE_UN_DZ",
    ),
)

IMPR_TABLE(TABLE=PARA, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=31)

TEST_RESU(
    RESU=(
        _F(
            NUME_ORDRE=1,
            PARA="FREQ",
            RESULTAT=MODES,
            REFERENCE="ANALYTIQUE",
            VALE_REFE=52.2198,
            VALE_CALC=52.3396441683678,
            PRECISION=2.0e-2,
            LEGENDE="F1_BENDING_Z1",
        ),
        _F(
            NUME_ORDRE=2,
            PARA="FREQ",
            RESULTAT=MODES,
            REFERENCE="ANALYTIQUE",
            VALE_REFE=104.440,
            VALE_CALC=104.42992528937033,
            PRECISION=2.0e-2,
            LEGENDE="F2_BENDING_Y1",
        ),
        _F(
            NUME_ORDRE=3,
            PARA="FREQ",
            RESULTAT=MODES,
            REFERENCE="ANALYTIQUE",
            VALE_REFE=327.256,
            VALE_CALC=327.0652475459293,
            PRECISION=2.0e-2,
            LEGENDE="F3_BENDING_Z2",
        ),
        _F(
            NUME_ORDRE=4,
            PARA="FREQ",
            RESULTAT=MODES,
            REFERENCE="ANALYTIQUE",
            VALE_REFE=654.512,
            VALE_CALC=646.9886423229167,
            PRECISION=2.0e-2,
            LEGENDE="F4_BENDING_Y2",
        ),
        _F(
            NUME_ORDRE=5,
            PARA="FREQ",
            RESULTAT=MODES,
            REFERENCE="ANALYTIQUE",
            VALE_REFE=916.326,
            VALE_CALC=911.6795505473701,
            PRECISION=3.0e-2,
            LEGENDE="F5_BENDING_Z3",
        ),
        _F(
            NUME_ORDRE=6,
            PARA="FREQ",
            RESULTAT=MODES,
            REFERENCE="ANALYTIQUE",
            VALE_REFE=1485.22,
            VALE_CALC=1497.0292704690783,
            PRECISION=3.0e-2,
            LEGENDE="F6_TORSION_1",
        ),
        # Generalized mass of mode 1 after NORM_MODE NORME='MASS_GENE'.
        _F(
            NUME_ORDRE=1,
            PARA="MASS_GENE",
            RESULTAT=MODES,
            REFERENCE="ANALYTIQUE",
            VALE_REFE=1.0,
            VALE_CALC=1.0,
            PRECISION=1.0e-6,
            LEGENDE="M1_MASS_GENE",
        ),
    )
)

FIN()
```

For your own study, write `DEBUT()` instead of `DEBUT(CODE="OUI", ...)`, as in Walkthrough 1.

What is new:

- **Density.** A modal analysis needs mass: `RHO` in `DEFI_MATERIAU ELAS`, in t/mm³ for these
  units. Check the total mass before anything else. [`POST_ELEM`](../commands/POST_ELEM.md)
  `MASS_INER` prints it to `tables/mass_inertia.csv`: `MASSE` = 6.28e-4 t = ρ × 20 × 10 × 400,
  center of gravity (200, 10, 5) (`tests/fixtures/modal/output/tables/mass_inertia.csv`).
  A wrong density unit shows up here at once.
- **Matrices.** A modal analysis works on assembled stiffness and mass matrices, built in three
  steps: [`CALC_MATR_ELEM`](../commands/CALC_MATR_ELEM.md) computes the element matrices
  (`OPTION="RIGI_MECA"` stiffness, `"MASS_MECA"` mass), [`NUME_DDL`](../commands/NUME_DDL.md)
  numbers the equations, and [`ASSE_MATRICE`](../commands/ASSE_MATRICE.md) assembles. The
  supports enter here, through `CHARGE=ENCAS` on the stiffness matrix: there is no `EXCIT` in
  a modal analysis. [`ASSEMBLAGE`](../commands/ASSEMBLAGE.md) does the three steps in one call.
- **The eigensolver.** [`CALC_MODES`](../commands/CALC_MODES.md) `OPTION="PLUS_PETITE"` with
  `CALC_FREQ=_F(NMAX_FREQ=6)` asks for the 6 lowest modes. The result is a modal result
  (`MODE_MECA`): one step per mode, accessed by `NUME_ORDRE` or `NUME_MODE`, with the frequency
  `FREQ` stored as a parameter.
- **Normalization.** `CALC_MODES` scales each mode shape so that its largest component is 1.
  [`NORM_MODE`](../commands/NORM_MODE.md) `NORME="MASS_GENE"` rescales them to unit generalized
  mass, the usual form for modal superposition. Frequencies and effective masses do not change.
- **The modal table.** `RECU_TABLE` copies the stored modal parameters into a table: frequency,
  generalized mass (`MASS_GENE`), effective mass per direction (`MASS_EFFE_DX` ...) and
  effective mass fraction (`MASS_EFFE_UN_DX` ...). `IMPR_TABLE` prints it to unit 31.
- **Results file.** Only `DEPL` is written: for a modal result it holds the mode shapes, one per
  step.

The export file adds the second table:

<!-- example: tests/fixtures/modal/input/run.export -->
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
F libr ../output/tables/mass_inertia.csv R 30
F libr ../output/tables/modal_parameters.csv R 31
F rmed ../output/run.rmed R 80
```

## 3. Run and read the log

Run as in [Walkthrough 1, step 5](walkthrough-solid-static.md#5-run). The job diagnostic is
`OK`. `CALC_MODES` prints the frequencies and a check in the log
(`tests/fixtures/modal/output/run.mess:403`–`:424`, shown here from the English-locale run
`tests/fixtures/modal/output_en/run.mess`, blank lines removed):

```text
number    frequency (HZ)     error norm

1       5.23396E+01        2.53716E-08
2       1.04430E+02        5.58736E-09
3       3.27065E+02        7.69053E-10
4       6.46989E+02        1.61872E-10
5       9.11680E+02        1.64460E-10
6       1.49703E+03        1.34435E-10

Mean error norm   :  5.36480E-09
...
A posteriori check of the modes

In the interval ( 5.22086E+01 , 1.50077E+03 ) there are indeed 6 frequency(ies).
```

Two checks are made for you:

- **Error norm.** For each mode, how well the computed pair satisfies K φ = ω² M φ. Values near
  1e-8 are good.
- **Sturm count.** The solver counts the eigenvalues in the interval independently (from the
  factorization of the shifted matrix) and confirms that none was missed. If either check fails,
  `CALC_MODES` stops with `ALGELINE2_74` ([`CALC_MODES`](../commands/CALC_MODES.md), Pitfalls).

## 4. Check the result

`caen results modal tests/fixtures/modal/output` reads the modal table:

```text
mode  frequency [Hz]  period [s]  effective mass % X Y Z  cumulative % X Y Z
   1         52.3396     0.01911         0.0   0.0  61.2    0.0   0.0  61.2
   2        104.4299    0.009576         0.0  61.3   0.0    0.0  61.3  61.2
   3        327.0652    0.003057         0.0   0.0  18.8    0.0  61.3  80.1
   4        646.9886    0.001546         0.0  18.9   0.0    0.0  80.2  80.1
   5        911.6796    0.001097         0.0   0.0   6.5    0.0  80.2  86.6
   6       1497.0293    0.000668         0.0   0.0   0.0    0.0  80.2  86.6
```

**Frequencies against beam theory** (hand values from `tests/fixtures/hand_values.py`). For a
cantilever, f_n = λ_n² / (2π L²) × √(E I / (ρ A)), λ = 1.8751, 4.6941, 7.8548. Bending in Z
uses I = b h³ / 12, bending in Y uses I = h b³ / 12, so the Y modes are twice the Z modes. Mode
6 is the first torsion mode, f = (1 / 4L) √(G J / (ρ I_p)) with the Saint-Venant constant J.

| Mode | Shape | Hand value [Hz] | Run [Hz] | Difference |
|---|---|---|---|---|
| 1 | 1st bending in Z | 52.22 | 52.34 | +0.2 % |
| 2 | 1st bending in Y | 104.44 | 104.43 | −0.01 % |
| 3 | 2nd bending in Z | 327.26 | 327.07 | −0.06 % |
| 4 | 2nd bending in Y | 654.51 | 646.99 | −1.15 % |
| 5 | 3rd bending in Z | 916.33 | 911.68 | −0.5 % |
| 6 | 1st torsion | 1485.22 | 1497.03 | +0.8 % |

The higher bending modes come out a little lower than Euler–Bernoulli. That is expected
(engineering judgement): the 3D model includes shear deformation and rotary inertia, which
beam theory ignores and which matter more as the wavelength shortens relative to the depth;
mode 4 bends in the 20 mm direction. Torsion differs from the Saint-Venant value because the
clamped end restrains warping.

**Effective mass.** The unit effective mass in a direction is the fraction of the total mass
that a mode moves in that direction. Each bending mode moves mass in one direction only; the
first bending mode of a cantilever carries 61 % of it, the second 19 %, the third 6.5 %, as
beam theory predicts (61.3, 18.8, 6.5 %; `tests/fixtures/README.md`). No mode moves mass
along X: the axial mode is higher than mode 6. Design rules often ask for modes up to
90 % of the mass in each direction of excitation (engineering judgement; check your code):
here that would need more modes.

**Mode shapes.** Open `output/run.rmed` in a viewer and animate `DEPL`, one step per mode. With
`NORM_MODE NORME="MASS_GENE"` the amplitudes have no physical size: only the shape and the
relative values count. `TEST_RESU` checks the normalization: mode 1 generalized mass = 1
(`M1_MASS_GENE`).

## Things to watch in modal analysis

- **Rigid-body modes.** Forget a support and the first modes come out at about 0 Hz. They count
  among the `NMAX_FREQ` modes.
- **Density units.** In a mm–N–MPa model, ρ is in t/mm³ (steel 7.85e-9). Check the mass from
  `POST_ELEM`.
- **Enough modes.** Check the cumulative effective mass before using the modes for a response
  calculation.
- **Normalization.** Compare mode shapes from different programs only after normalizing both
  the same way.

Next: [Reading the log](reading-logs.md).
