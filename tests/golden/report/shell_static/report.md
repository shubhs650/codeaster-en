# Simply supported square plate, uniform pressure

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

Simply supported square plate (a 1000 mm, t 10 mm), uniform pressure 0.01 MPa, DKT shell on a 20 x 20 QUAD4 mesh, linear elastic steel.

*This report was produced by software from the results of one run. It documents what the solver computed; it is not a verdict on compliance with any design code.*

## Summary

| Item | Value |
| --- | --- |
| Analysis | linear static |
| Outcome | completed |
| Model size | 441 nodes, 483 elements |
| Elapsed time (whole job) | 2.350 s |
| CPU time (sum of commands) | 0.7000 s |
| Peak memory | 780.3 MB |
| Warnings ignored by the command file | `MODELISA8_14` |

Headline results:

- Maximum displacement magnitude: 2.112 mm at node 5 (500.0, 500.0, 0).
- Equilibrium check: support reactions balance the applied loads to less than 0.000001 % of the applied resultant.

*Source: solver log (outcome, times, memory), results file (model size, extrema), command file and results file (balance).*

## Model

| Applied to | Physics | Modeling type | Command file line |
| --- | --- | --- | --- |
| Plate (`PLATE`) | mechanical (`MECANIQUE`) | thin shell (DKT) (`DKT`) | 33 |

The mesh has 441 nodes and 483 elements.

| Element type | Count |
| --- | ---: |
| point element (1 node) (`POI1`) | 3 |
| 4-node quadrangle (`QUAD4`) | 400 |
| 2-node segment (`SEG2`) | 80 |
| **Total** | **483** |

| Axis | Min [mm] | Max [mm] | Extent [mm] |
| --- | ---: | ---: | ---: |
| X | 0 | 1000 | 1000 |
| Y | 0 | 1000 | 1000 |
| Z | 0 | 0 | 0 |

*Source: mesh in `output/run.rmed`; model assignment from the command file.*

## Materials

### Material `ACIER`

Assigned to: Plate (`PLATE`).

Law: linear elastic (`ELAS`).

| Property | Value | Unit |
| --- | ---: | --- |
| Young's modulus (`E`) | 210.0e3 | MPa |
| Poisson's ratio (`NU`) | 0.3000 | – |

*Source: command file line 39.*

## Element properties

| Property | Applied to | Values |
| --- | --- | --- |
| shell properties (`COQUE`) | Plate (`PLATE`) | `EPAIS` = 10.00; `ANGL_REP` = (0, 0) |

*Source: command file line 37; values in model units.*

## Loads and boundary conditions

| Load | Type | Kind | Applied to | Values | In load case |
| --- | --- | --- | --- | --- | --- |
| `APPUI` | imposed DOF (`DDL_IMPO`) | boundary condition ¹ | Simply supported edges (`EDGES`) | `DZ` = 0 | yes |
| `APPUI` | imposed DOF | boundary condition ¹ | Corner (0, 0), in-plane restraint (`CORNER_A`) | `DX` = 0; `DY` = 0 | yes |
| `APPUI` | imposed DOF | boundary condition ¹ | Corner (1000, 0), in-plane restraint (`CORNER_B`) | `DY` = 0 | yes |
| `PRESS` | distributed pressure (`PRES_REP`) | load | Plate (`PLATE`) | `PRES` = 0.01000 | yes |

The load case is the `EXCIT` list of `MECA_STATIQUE`: `APPUI`, `PRESS`.

¹ Boundary conditions are enforced by Lagrange multipliers (`AFFE_CHAR_MECA`: Lagrange multipliers; `AFFE_CHAR_CINE`: eliminated).

*Source: command file line 43, 53; values in model units.*

## Solution

| Item | Value |
| --- | --- |
| Solve command | linear static analysis (`MECA_STATIQUE`) |
| Linear solver | MUMPS direct solver (`MUMPS`) |
| Renumbering | `AUTO` |
| Equations (degrees of freedom) | 2812 |
| Physical degrees of freedom | 2646 on 441 nodes |
| Lagrange multipliers | 166 for 83 dualized linear relations |
| Solve time | 0.2200 s CPU, 0.2400 s elapsed |

*Source: solver settings from the command echo in the solver log (defaults filled in); degrees of freedom from the solver log message FACTOR_1.*

## Results: displacements

Maximum displacement magnitude: **2.112 mm** at node 5 (500.0, 500.0, 0).

Displacement magnitude (`DEPL`, translations), per group:

| Group | Component | Min | At | Max | At | Unit |
| --- | --- | ---: | --- | ---: | --- | --- |
| whole model | magnitude | 0 | node 1 (0, 0, 0) | 2.112 | node 5 (500.0, 500.0, 0) | mm |
| Plate (`PLATE`) | magnitude | 0 | node 1 (0, 0, 0) | 2.112 | node 5 (500.0, 500.0, 0) | mm |
| Simply supported edges (`EDGES`) | magnitude | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | mm |
| Plate centre (`CENTER`) | magnitude | 2.112 | node 5 (500.0, 500.0, 0) | 2.112 | node 5 (500.0, 500.0, 0) | mm |

Displacement components, whole model:

| Group | Component | Min | At | Max | At | Unit |
| --- | --- | ---: | --- | ---: | --- | --- |
| whole model | X translation (`DX`) | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | mm |
| whole model | Y translation (`DY`) | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | mm |
| whole model | Z translation (`DZ`) | -2.112 | node 5 (500.0, 500.0, 0) | 0 | node 1 (0, 0, 0) | mm |
| whole model | rotation about X (`DRX`) | -0.007000 | node 2 (500.0, 0, 0) | 0.007000 | node 8 (500.0, 1000, 0) | rad |
| whole model | rotation about Y (`DRY`) | -0.007000 | node 6 (1000, 500.0, 0) | 0.007000 | node 4 (0, 500.0, 0) | rad |
| whole model | rotation about Z (`DRZ`) | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | rad |

*Source: results file field `RESU____DEPL`, last stored step.*

## Results: stresses

Shell results are reported as stress resultants per unit length (force and moment), in the element local axes; no through-thickness stress field was written, so no layer position applies.

Shell stress resultants: shell/beam resultants (nodal average) (`EFGE_NOEU`), nodal average (values of adjoining elements averaged at each node).

| Group | Component | Min | At | Max | At | Unit |
| --- | --- | ---: | --- | ---: | --- | --- |
| whole model | membrane force XX (`NXX`) | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | N/mm |
| Plate (`PLATE`) | membrane force XX | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | N/mm |
| Simply supported edges (`EDGES`) | membrane force XX | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | N/mm |
| Plate centre (`CENTER`) | membrane force XX | 0 | node 5 (500.0, 500.0, 0) | 0 | node 5 (500.0, 500.0, 0) | N/mm |
| whole model | membrane force YY (`NYY`) | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | N/mm |
| Plate (`PLATE`) | membrane force YY | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | N/mm |
| Simply supported edges (`EDGES`) | membrane force YY | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | N/mm |
| Plate centre (`CENTER`) | membrane force YY | 0 | node 5 (500.0, 500.0, 0) | 0 | node 5 (500.0, 500.0, 0) | N/mm |
| whole model | membrane shear force XY (`NXY`) | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | N/mm |
| Plate (`PLATE`) | membrane shear force XY | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | N/mm |
| Simply supported edges (`EDGES`) | membrane shear force XY | 0 | node 1 (0, 0, 0) | 0 | node 1 (0, 0, 0) | N/mm |
| Plate centre (`CENTER`) | membrane shear force XY | 0 | node 5 (500.0, 500.0, 0) | 0 | node 5 (500.0, 500.0, 0) | N/mm |
| whole model | bending moment XX (`MXX`) | -479.6 | node 5 (500.0, 500.0, 0) | 0.3661 | node 45 (1000, 950.0, 0) | N·mm/mm |
| Plate (`PLATE`) | bending moment XX | -479.6 | node 5 (500.0, 500.0, 0) | 0.3661 | node 45 (1000, 950.0, 0) | N·mm/mm |
| Simply supported edges (`EDGES`) | bending moment XX | -1.283 | node 9 (1000, 1000, 0) | 0.3661 | node 45 (1000, 950.0, 0) | N·mm/mm |
| Plate centre (`CENTER`) | bending moment XX | -479.6 | node 5 (500.0, 500.0, 0) | -479.6 | node 5 (500.0, 500.0, 0) | N·mm/mm |
| whole model | bending moment YY (`MYY`) | -479.6 | node 5 (500.0, 500.0, 0) | 0.3661 | node 10 (50.00, 0, 0) | N·mm/mm |
| Plate (`PLATE`) | bending moment YY | -479.6 | node 5 (500.0, 500.0, 0) | 0.3661 | node 10 (50.00, 0, 0) | N·mm/mm |
| Simply supported edges (`EDGES`) | bending moment YY | -1.283 | node 7 (0, 1000, 0) | 0.3661 | node 10 (50.00, 0, 0) | N·mm/mm |
| Plate centre (`CENTER`) | bending moment YY | -479.6 | node 5 (500.0, 500.0, 0) | -479.6 | node 5 (500.0, 500.0, 0) | N·mm/mm |
| whole model | twisting moment XY (`MXY`) | -319.9 | node 3 (1000, 0, 0) | 319.9 | node 1 (0, 0, 0) | N·mm/mm |
| Plate (`PLATE`) | twisting moment XY | -319.9 | node 3 (1000, 0, 0) | 319.9 | node 1 (0, 0, 0) | N·mm/mm |
| Simply supported edges (`EDGES`) | twisting moment XY | -319.9 | node 3 (1000, 0, 0) | 319.9 | node 1 (0, 0, 0) | N·mm/mm |
| Plate centre (`CENTER`) | twisting moment XY | 14.60e-12 | node 5 (500.0, 500.0, 0) | 14.60e-12 | node 5 (500.0, 500.0, 0) | N·mm/mm |
| whole model | transverse shear force X (`QX`) | -2.727 | node 4 (0, 500.0, 0) | 2.727 | node 6 (1000, 500.0, 0) | N/mm |
| Plate (`PLATE`) | transverse shear force X | -2.727 | node 4 (0, 500.0, 0) | 2.727 | node 6 (1000, 500.0, 0) | N/mm |
| Simply supported edges (`EDGES`) | transverse shear force X | -2.727 | node 4 (0, 500.0, 0) | 2.727 | node 6 (1000, 500.0, 0) | N/mm |
| Plate centre (`CENTER`) | transverse shear force X | -649.5e-15 | node 5 (500.0, 500.0, 0) | -649.5e-15 | node 5 (500.0, 500.0, 0) | N/mm |
| whole model | transverse shear force Y (`QY`) | -2.727 | node 2 (500.0, 0, 0) | 2.727 | node 8 (500.0, 1000, 0) | N/mm |
| Plate (`PLATE`) | transverse shear force Y | -2.727 | node 2 (500.0, 0, 0) | 2.727 | node 8 (500.0, 1000, 0) | N/mm |
| Simply supported edges (`EDGES`) | transverse shear force Y | -2.727 | node 2 (500.0, 0, 0) | 2.727 | node 8 (500.0, 1000, 0) | N/mm |
| Plate centre (`CENTER`) | transverse shear force Y | 1.942e-12 | node 5 (500.0, 500.0, 0) | 1.942e-12 | node 5 (500.0, 500.0, 0) | N/mm |

*Source: results file field `RESU____EFGE_NOEU`, last stored step.*

## Results: reactions

Sum of nodal reactions per support group (the force each support exerts on the structure):

| Group | Nodes | Force X (`DX`) [N] | Force Y (`DY`) [N] | Force Z (`DZ`) [N] | Moment about X (`DRX`) [N·mm] | Moment about Y (`DRY`) [N·mm] | Moment about Z (`DRZ`) [N·mm] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Simply supported edges (`EDGES`) | 80 | 0 | 0 | 10000 | 0 | 0 | 0 |
| Corner (0, 0), in-plane restraint (`CORNER_A`) | 1 | 0 | 0 | -620.3 | 0 | 0 | 0 |
| Corner (1000, 0), in-plane restraint (`CORNER_B`) | 1 | 0 | 0 | -620.3 | 0 | 0 | 0 |
| **All supports** | – | **0** | **0** | **10000** | **0** | **0** | **0** |

*Source: results file field `RESU____REAC_NODA`, sum over the group's nodes.*

Reaction resultants printed by `POST_RELEVE_T`:

| Table entry | File | X [N] | Y [N] | Z [N] |
| --- | --- | ---: | ---: | ---: |
| `REAC_EDGES` | `reactions.csv` | 0 | 0 | 10000 |

### Applied loads

| Load | Type | Applied to | Status | Basis | X [N] | Y [N] | Z [N] |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `PRESS` | distributed pressure (`PRES_REP`) | Plate (`PLATE`) | summed | -PRES × vector area of 400 faces | 0 | 0 | -10000 |

*Source: load values from the command file; areas, lengths and node counts from the mesh in `output/run.rmed`.*

### Equilibrium check

|  | X [N] | Y [N] | Z [N] |
| --- | ---: | ---: | ---: |
| Support reactions (sum) | 0 | 0 | 10000 |
| Applied loads (resultant) | 0 | 0 | -10000 |
| Residual (reactions + applied) | 0 | 0 | 0 |

Balance error: **less than 0.000001 %** (magnitude of the residual over the magnitude of the applied resultant).

*Source: reactions from results file field `RESU____REAC_NODA` (sum of all nodes); applied loads summed from the command file over the result mesh.*

## Diagnostics

The solver issued no warning or error.

Warnings the command file chose to ignore: `MODELISA8_14`.

*Source: solver log, rendered in English from the overlay's message catalog.*

## Verification

| Check | Quantity | Reference type | Reference | Computed | Error | Tolerance | Verdict |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `W_CENTER` | Deflection at the centre [mm] | analytical (`ANALYTIQUE`) | -2.11242 | -2.112263828 | 7.393035E-03% | 1.0% | pass |
| `MXX_CENTER` | Bending moment per unit length M_x at the centre [N mm/mm] | analytical | -478.864 | -479.6453146 | 1.631600E-01% | 3.0% | pass |
| `REAC_DZ_SUM` | Sum of Z reactions on the supports [N] | analytical | 10000 | 10000 | 1.818989E-13% | 0.1% | pass |

3 of 3 non-regression checks (computed value against the value stored in the command file) passed.

*Source: `TEST_RESU` output in the solver log; pass or fail by the solver's own tolerance.*

## Appendix A: command file

`input/run.comm` as run, verbatim. Command and keyword names are the solver's own (French) API. Lines starting with `# >>` are added by this report: an English one-line description of the command below.

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
# >> DEBUT: begin study
DEBUT(CODE="OUI", IGNORE_ALARM=("MODELISA8_14",))

Q = 0.01  # uniform pressure [MPa]
T = 10.0  # thickness [mm]

# >> LIRE_MAILLAGE: read mesh
MAIL = LIRE_MAILLAGE(FORMAT="MED", UNITE=20)

# >> DEFI_GROUP: define groups
MAIL = DEFI_GROUP(reuse=MAIL, MAILLAGE=MAIL, CREA_GROUP_NO=_F(TOUT_GROUP_MA="OUI"))

# Mesh normals already point to +Z; this makes the orientation explicit and checked.
# >> MODI_MAILLAGE: modify mesh
MAIL = MODI_MAILLAGE(
    reuse=MAIL,
    MAILLAGE=MAIL,
    ORIE_NORM_COQUE=_F(GROUP_MA="PLATE", GROUP_NO="CENTER", VECT_NORM=(0.0, 0.0, 1.0)),
)

# >> AFFE_MODELE: assign model
MODE = AFFE_MODELE(
    MAILLAGE=MAIL, AFFE=_F(GROUP_MA="PLATE", PHENOMENE="MECANIQUE", MODELISATION="DKT")
)

# >> AFFE_CARA_ELEM: assign element properties
CARA = AFFE_CARA_ELEM(MODELE=MODE, COQUE=_F(GROUP_MA="PLATE", EPAIS=T, ANGL_REP=(0.0, 0.0)))

# >> DEFI_MATERIAU: define material
ACIER = DEFI_MATERIAU(ELAS=_F(E=210000.0, NU=0.3))

# >> AFFE_MATERIAU: assign material
MATE = AFFE_MATERIAU(MAILLAGE=MAIL, AFFE=_F(GROUP_MA="PLATE", MATER=ACIER))

# >> AFFE_CHAR_MECA: assign mechanical loads and BCs
APPUI = AFFE_CHAR_MECA(
    MODELE=MODE,
    DDL_IMPO=(
        _F(GROUP_MA="EDGES", DZ=0.0),
        _F(GROUP_NO="CORNER_A", DX=0.0, DY=0.0),
        _F(GROUP_NO="CORNER_B", DY=0.0),
    ),
)

# Positive PRES acts against the element normal (+Z), i.e. downward (as in ssls101n).
# >> AFFE_CHAR_MECA: assign mechanical loads and BCs
PRESS = AFFE_CHAR_MECA(MODELE=MODE, PRES_REP=_F(GROUP_MA="PLATE", PRES=Q))

# >> MECA_STATIQUE: linear static analysis
RESU = MECA_STATIQUE(
    MODELE=MODE,
    CHAM_MATER=MATE,
    CARA_ELEM=CARA,
    EXCIT=(_F(CHARGE=APPUI), _F(CHARGE=PRESS)),
    SOLVEUR=_F(METHODE="MUMPS"),
)

# >> CALC_CHAMP: compute derived fields
RESU = CALC_CHAMP(
    reuse=RESU, RESULTAT=RESU, CONTRAINTE=("EFGE_ELNO", "EFGE_NOEU"), FORCE="REAC_NODA"
)

# >> POST_RELEVE_T: extract values to table
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

# >> IMPR_TABLE: write table
IMPR_TABLE(TABLE=REAC, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=30)

# >> IMPR_RESU: write results
IMPR_RESU(
    FORMAT="MED",
    UNITE=80,
    RESU=_F(RESULTAT=RESU, CARA_ELEM=CARA, NOM_CHAM=("DEPL", "EFGE_NOEU", "REAC_NODA")),
)

# >> TEST_RESU: test result value
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
| free-format file (tables) | `../output/tables/reactions.csv` | output | 30 |
| MED results | `../output/run.rmed` | output | 80 |

*Source: `input/run.export`.*
