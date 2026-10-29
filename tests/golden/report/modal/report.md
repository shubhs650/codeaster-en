# Cantilever beam, natural frequencies

| Item | Value |
| --- | --- |
| Project | codeaster-en fixtures |
| Revision | A |
| Author | codeaster-en |
| Date | 2026-10-23 |
| Solver | code_aster 17.4.22 |
| English overlay pinned to | code_aster 17.4.26 |
| Report generator | codeaster-en 0.1.0 |
| Units | SI-mm (mm, N, MPa, t, s) |

Cantilever beam L 400 mm, section 20 mm (Y) x 10 mm (Z), clamped at X = 0, first six natural frequencies (five bending, one torsion). HEXA20 mesh, linear elastic steel.

*This report was produced by software from the results of one run. It documents what the solver computed; it is not a verdict on compliance with any design code.*

## Summary

| Item | Value |
| --- | --- |
| Analysis | modal (natural frequencies) |
| Outcome | completed |
| Model size | 4197 nodes, 656 elements |
| Elapsed time (whole job) | 4.440 s |
| CPU time (sum of commands) | 2.010 s |
| Peak memory | 907.7 MB |

Headline results:

- First natural frequency: 52.34 Hz.

*Source: solver log (outcome, times, memory), results file (model size, extrema), command file and results file (balance).*

## Model

| Applied to | Physics | Modeling type | Command file line |
| --- | --- | --- | --- |
| Beam (`BEAM`) | mechanical (`MECANIQUE`) | 3D solid (`3D`) | 18 |

The mesh has 4197 nodes and 656 elements.

| Element type | Count |
| --- | ---: |
| 20-node hexahedron (`HEXA20`) | 640 |
| 8-node quadrangle (`QUAD8`) | 16 |
| **Total** | **656** |

| Axis | Min [mm] | Max [mm] | Extent [mm] |
| --- | ---: | ---: | ---: |
| X | 0 | 400.0 | 400.0 |
| Y | 0 | 20.00 | 20.00 |
| Z | 0 | 10.00 | 10.00 |

*Source: mesh in `output/run.rmed`; model assignment from the command file.*

## Materials

### Material `ACIER`

Assigned to: Beam (`BEAM`).

Law: linear elastic (`ELAS`).

| Property | Value | Unit |
| --- | ---: | --- |
| Young's modulus (`E`) | 210.0e3 | MPa |
| Poisson's ratio (`NU`) | 0.3000 | – |
| density (`RHO`) | 7.850e-9 | t/mm³ |

*Source: command file line 22.*

## Loads and boundary conditions

| Load | Type | Kind | Applied to | Values | In load case |
| --- | --- | --- | --- | --- | --- |
| `ENCAS` | imposed DOF (`DDL_IMPO`) | boundary condition ¹ | Clamped end (X = 0) (`CLAMP`) | `DX` = 0; `DY` = 0; `DZ` = 0 | no |

The load case is the `EXCIT` list of `CALC_MODES`: none.

¹ Boundary conditions are enforced by Lagrange multipliers (`AFFE_CHAR_MECA`: Lagrange multipliers; `AFFE_CHAR_CINE`: eliminated).

*Source: command file line 26; values in model units.*

## Solution

| Item | Value |
| --- | --- |
| Solve command | compute natural modes (`CALC_MODES`) |
| Linear solver | MUMPS direct solver (`MUMPS`) |
| Renumbering | `AUTO` |
| Equations (degrees of freedom) | 12813 |
| Active degrees of freedom | 12480 |
| Lagrange multipliers | 222 |
| Eigensolver | Sorensen eigensolver (ARPACK) (`SORENSEN`) |
| Modes sought | smallest (frequencies) (`PLUS_PETITE`) |
| Number of modes requested | 6 |
| Frequency shift [Hz] | 0 |
| Solve time | 0.9500 s CPU, 1.380 s elapsed |

*Source: solver settings from the command echo in the solver log (defaults filled in); degrees of freedom from the solver log message ALGELINE7_17.*

## Results: natural modes

| Mode | Frequency [Hz] | Period [s] | Effective mass X [%] | Cumulative X [%] | Effective mass Y [%] | Cumulative Y [%] | Effective mass Z [%] | Cumulative Z [%] |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 52.34 | 0.01911 | 0.00 | 0.00 | 0.00 | 0.00 | 61.23 | 61.23 |
| 2 | 104.4 | 0.009576 | 0.00 | 0.00 | 61.26 | 61.26 | 0.00 | 61.23 |
| 3 | 327.1 | 0.003057 | 0.00 | 0.00 | 0.00 | 61.26 | 18.84 | 80.06 |
| 4 | 647.0 | 0.001546 | 0.00 | 0.00 | 18.93 | 80.18 | 0.00 | 80.06 |
| 5 | 911.7 | 0.001097 | 0.00 | 0.00 | 0.00 | 80.18 | 6.49 | 86.55 |
| 6 | 1497 | 668.0e-6 | 0.00 | 0.00 | 0.00 | 80.18 | 0.00 | 86.55 |

Total mass of the model: 628.0e-6 t.

*Source: `table:mass_inertia.csv:MASSE`, `table:modal_parameters.csv`, `rmed:MODES___DEPL step values (frequencies)`.*

## Diagnostics

The solver issued no warning or error.

*Source: solver log, rendered in English from the overlay's message catalog.*

## Verification

| Check | Quantity | Reference type | Reference | Computed | Error | Tolerance | Verdict |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `F1_BENDING_Z1` | Natural frequency of mode 1 [Hz], bending in Z, n = 1 | analytical (`ANALYTIQUE`) | 52.2198 | 52.33964417 | 2.294995E-01% | 2.0% | pass |
| `F2_BENDING_Y1` | Natural frequency of mode 2 [Hz], bending in Y, n = 1 | analytical | 104.44 | 104.4299253 | 9.646410E-03% | 2.0% | pass |
| `F3_BENDING_Z2` | Natural frequency of mode 3 [Hz], bending in Z, n = 2 | analytical | 327.256 | 327.0652475 | 5.828845E-02% | 2.0% | pass |
| `F4_BENDING_Y2` | Natural frequency of mode 4 [Hz], bending in Y, n = 2 | analytical | 654.512 | 646.9886423 | 1.149461E+00% | 2.0% | pass |
| `F5_BENDING_Z3` | Natural frequency of mode 5 [Hz], bending in Z, n = 3 | analytical | 916.326 | 911.6795505 | 5.070738E-01% | 3.0% | pass |
| `F6_TORSION_1` | Natural frequency of mode 6 [Hz], first torsion mode | analytical | 1485.22 | 1497.02927 | 7.951193E-01% | 3.0% | pass |

6 of 6 non-regression checks (computed value against the value stored in the command file) passed.

*Source: `TEST_RESU` output in the solver log; pass or fail by the solver's own tolerance.*

## Appendix A: command file

`input/run.comm` as run, verbatim. Command and keyword names are the solver's own (French) API. Lines starting with `# >>` are added by this report: an English one-line description of the command below.

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

# >> DEBUT: begin study
DEBUT(CODE="OUI", ERREUR=_F(ALARME="EXCEPTION"))

# >> LIRE_MAILLAGE: read mesh
MAIL = LIRE_MAILLAGE(FORMAT="MED", UNITE=20)

# >> AFFE_MODELE: assign model
MODE = AFFE_MODELE(
    MAILLAGE=MAIL, AFFE=_F(GROUP_MA="BEAM", PHENOMENE="MECANIQUE", MODELISATION="3D")
)

# >> DEFI_MATERIAU: define material
ACIER = DEFI_MATERIAU(ELAS=_F(E=210000.0, NU=0.3, RHO=7.85e-9))

# >> AFFE_MATERIAU: assign material
MATE = AFFE_MATERIAU(MAILLAGE=MAIL, AFFE=_F(GROUP_MA="BEAM", MATER=ACIER))

# >> AFFE_CHAR_MECA: assign mechanical loads and BCs
ENCAS = AFFE_CHAR_MECA(MODELE=MODE, DDL_IMPO=_F(GROUP_MA="CLAMP", DX=0.0, DY=0.0, DZ=0.0))

# Mass and inertia of the model: mass = RHO * b * h * L = 6.28e-4 t.
# >> POST_ELEM: element-based post-processing
MASSE = POST_ELEM(MODELE=MODE, CHAM_MATER=MATE, MASS_INER=_F(TOUT="OUI"))

# >> IMPR_TABLE: write table
IMPR_TABLE(TABLE=MASSE, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=30)

# >> CALC_MATR_ELEM: compute element matrices
RIGI_EL = CALC_MATR_ELEM(MODELE=MODE, CHAM_MATER=MATE, CHARGE=ENCAS, OPTION="RIGI_MECA")

# >> CALC_MATR_ELEM: compute element matrices
MASS_EL = CALC_MATR_ELEM(MODELE=MODE, CHAM_MATER=MATE, CHARGE=ENCAS, OPTION="MASS_MECA")

NUME = NUME_DDL(MATR_RIGI=RIGI_EL)

# >> ASSE_MATRICE: assemble matrix
RIGI = ASSE_MATRICE(MATR_ELEM=RIGI_EL, NUME_DDL=NUME)

# >> ASSE_MATRICE: assemble matrix
MASS = ASSE_MATRICE(MATR_ELEM=MASS_EL, NUME_DDL=NUME)

# >> CALC_MODES: compute natural modes
MODES = CALC_MODES(MATR_RIGI=RIGI, MATR_MASS=MASS, OPTION="PLUS_PETITE", CALC_FREQ=_F(NMAX_FREQ=6))

# >> IMPR_RESU: write results
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

# >> IMPR_TABLE: write table
IMPR_TABLE(TABLE=PARA, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=31)

# >> TEST_RESU: test result value
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
    )
)

# >> FIN: end study
FIN()
```

## Appendix B: run parameters

| Parameter | Name | Value | Unit |
| --- | --- | ---: | --- |
| Time limit | `time_limit` | 600 | s |
| Memory limit | `memory_limit` | 2048 | MB |
| OpenMP threads per process | `ncpus` | 1 | – |
| MPI processes | `mpi_nbcpu` | 1 | – |
| MPI nodes | `mpi_nbnoeud` | 1 | – |

| File | Path | Direction | Logical unit |
| --- | --- | --- | ---: |
| command file | `run.comm` | input | 1 |
| MED mesh | `mesh.med` | input | 20 |
| message log | `../output/run.mess` | output | 6 |
| text results | `../output/run.resu` | output | 8 |
| free-format file (tables) | `../output/tables/mass_inertia.csv` | output | 30 |
| free-format file (tables) | `../output/tables/modal_parameters.csv` | output | 31 |
| MED results | `../output/run.rmed` | output | 80 |

*Source: `input/run.export`.*
