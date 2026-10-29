# Nozzle in cylindrical shell, internal pressure

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

Cylindrical shell (Ri 100, Ro 120, H 300 mm) with a radial nozzle (ri 25, ro 35 mm, open end at X = 220 mm), base fixed, 2 MPa internal pressure. Linear tetrahedra, linear elastic steel.

*This report was produced by software from the results of one run. It documents what the solver computed; it is not a verdict on compliance with any design code.*

## Summary

| Item | Value |
| --- | --- |
| Analysis | linear static |
| Outcome | completed |
| Model size | 4622 nodes, 18778 elements |
| Elapsed time (whole job) | 3.560 s |
| CPU time (sum of commands) | 1.590 s |
| Peak memory | 854.2 MB |

Headline results:

- Maximum displacement magnitude: 0.007749 mm at node 279 (-24.19, 97.03, 300.0).
- Maximum von Mises stress (`SIEQ_NOEU`): 34.74 MPa at node 9 (100.0, -9.185e-15, 175.0).
- Equilibrium check: support reactions balance the applied loads to less than 0.000001 % of the applied resultant.

*Source: solver log (outcome, times, memory), results file (model size, extrema), command file and results file (balance).*

## Model

| Applied to | Physics | Modeling type | Command file line |
| --- | --- | --- | --- |
| whole mesh (`TOUT`) | mechanical (`MECANIQUE`) | 3D solid (`3D`) | 23 |

The mesh has 4622 nodes and 18778 elements.

| Element type | Count |
| --- | ---: |
| 4-node tetrahedron (`TETRA4`) | 14439 |
| 3-node triangle (`TRIA3`) | 4339 |
| **Total** | **18778** |

| Axis | Min [mm] | Max [mm] | Extent [mm] |
| --- | ---: | ---: | ---: |
| X | -120.0 | 220.0 | 340.0 |
| Y | -120.0 | 120.0 | 240.0 |
| Z | 0 | 300.0 | 300.0 |

*Source: mesh in `output/run.rmed`; model assignment from the command file.*

## Materials

### Material `ACIER`

Assigned to: Shell and nozzle (`SOLID`).

Law: linear elastic (`ELAS`).

| Property | Value | Unit |
| --- | ---: | --- |
| Young's modulus (`E`) | 210.0e3 | MPa |
| Poisson's ratio (`NU`) | 0.3000 | – |

*Source: command file line 25.*

## Loads and boundary conditions

| Load | Type | Kind | Applied to | Values | In load case |
| --- | --- | --- | --- | --- | --- |
| `FIXE` | imposed DOF (`DDL_IMPO`) | boundary condition ¹ | Fixed base (Z = 0) (`BASE`) | `DX` = 0; `DY` = 0; `DZ` = 0 | yes |
| `PRESS` | distributed pressure (`PRES_REP`) | load | Shell inner wall (pressure) (`P_SHELL`), Nozzle bore (pressure) (`P_NOZZLE`) | `PRES` = 2.000 | yes |

The load case is the `EXCIT` list of `MECA_STATIQUE`: `FIXE`, `PRESS`.

¹ Boundary conditions are enforced by Lagrange multipliers (`AFFE_CHAR_MECA`: Lagrange multipliers; `AFFE_CHAR_CINE`: eliminated).

*Source: command file line 29, 31; values in model units.*

## Solution

| Item | Value |
| --- | --- |
| Solve command | linear static analysis (`MECA_STATIQUE`) |
| Linear solver | MUMPS direct solver (`MUMPS`) |
| Renumbering | `AUTO` |
| Equations (degrees of freedom) | 14730 |
| Physical degrees of freedom | 13866 on 4622 nodes |
| Lagrange multipliers | 864 for 432 dualized linear relations |
| Solve time | 0.5900 s CPU, 0.8300 s elapsed |

*Source: solver settings from the command echo in the solver log (defaults filled in); degrees of freedom from the solver log message FACTOR_1.*

## Results: displacements

Maximum displacement magnitude: **0.007749 mm** at node 279 (-24.19, 97.03, 300.0).

Displacement magnitude (`DEPL`, translations), per group:

| Group | Component | Min | At | Max | At | Unit |
| --- | --- | ---: | --- | ---: | --- | --- |
| whole model | magnitude | 0 | node 48 (116.8, 27.67, 0) | 0.007749 | node 279 (-24.19, 97.03, 300.0) | mm |
| Shell and nozzle (`SOLID`) | magnitude | 0 | node 48 (116.8, 27.67, 0) | 0.007749 | node 279 (-24.19, 97.03, 300.0) | mm |
| Fixed base (Z = 0) (`BASE`) | magnitude | 0 | node 48 (116.8, 27.67, 0) | 193.3e-21 | node 231 (30.90, 95.11, 0) | mm |

Displacement components, whole model:

| Group | Component | Min | At | Max | At | Unit |
| --- | --- | ---: | --- | ---: | --- | --- |
| whole model | X translation (`DX`) | -0.005666 | node 3564 (-100.0, 0.6487, 242.0) | 0.003640 | node 2974 (87.67, 48.11, 124.8) | mm |
| whole model | Y translation (`DY`) | -0.007154 | node 2677 (13.21, -99.12, 174.7) | 0.007135 | node 2742 (24.09, 97.06, 162.2) | mm |
| whole model | Z translation (`DZ`) | -0.003628 | node 289 (-99.76, -6.976, 300.0) | 0.001384 | node 8 (220.0, 6.123e-15, 175.0) | mm |

*Source: results file field `RESU____DEPL`, last stored step.*

## Results: stresses

Stresses: equivalent stress (nodal average) (`SIEQ_NOEU`), nodal average (values of adjoining elements averaged at each node).

| Group | Component | Min | At | Max | At | Unit |
| --- | --- | ---: | --- | ---: | --- | --- |
| whole model | von Mises (`VMIS`) | 2.135 | node 1810 (140.6, -0.08182, 115.0) | 34.74 | node 9 (100.0, -9.185e-15, 175.0) | MPa |
| Shell and nozzle (`SOLID`) | von Mises | 2.135 | node 1810 (140.6, -0.08182, 115.0) | 34.74 | node 9 (100.0, -9.185e-15, 175.0) | MPa |
| Fixed base (Z = 0) (`BASE`) | von Mises | 6.110 | node 4 (120.0, -29.39e-15, 0) | 12.12 | node 255 (-10.45, -99.45, 0) | MPa |
| whole model | Tresca (`TRESCA`) | 2.417 | node 1810 (140.6, -0.08182, 115.0) | 36.17 | node 9 (100.0, -9.185e-15, 175.0) | MPa |
| Shell and nozzle (`SOLID`) | Tresca | 2.417 | node 1810 (140.6, -0.08182, 115.0) | 36.17 | node 9 (100.0, -9.185e-15, 175.0) | MPa |
| Fixed base (Z = 0) (`BASE`) | Tresca | 6.814 | node 4 (120.0, -29.39e-15, 0) | 13.55 | node 230 (43.84, 89.88, 0) | MPa |
| whole model | 1st principal (`PRIN_1`) | -14.98 | node 64 (-60.00, 103.9, 0) | 2.154 | node 6 (100.0, -24.49e-15, 0) | MPa |
| Shell and nozzle (`SOLID`) | 1st principal | -14.98 | node 64 (-60.00, 103.9, 0) | 2.154 | node 6 (100.0, -24.49e-15, 0) | MPa |
| Fixed base (Z = 0) (`BASE`) | 1st principal | -14.98 | node 64 (-60.00, 103.9, 0) | 2.154 | node 6 (100.0, -24.49e-15, 0) | MPa |
| whole model | 3rd principal (`PRIN_3`) | -3.185 | node 64 (-60.00, 103.9, 0) | 36.14 | node 9 (100.0, -9.185e-15, 175.0) | MPa |
| Shell and nozzle (`SOLID`) | 3rd principal | -3.185 | node 64 (-60.00, 103.9, 0) | 36.14 | node 9 (100.0, -9.185e-15, 175.0) | MPa |
| Fixed base (Z = 0) (`BASE`) | 3rd principal | -3.185 | node 64 (-60.00, 103.9, 0) | 15.07 | node 260 (55.92, -82.90, 0) | MPa |

*Source: results file field `RESU____SIEQ_NOEU`, last stored step.*

## Results: reactions

Sum of nodal reactions per support group (the force each support exerts on the structure):

| Group | Nodes | Force X (`DX`) [N] | Force Y (`DY`) [N] | Force Z (`DZ`) [N] |
| --- | ---: | ---: | ---: | ---: |
| Fixed base (Z = 0) (`BASE`) | 144 | 3892 | 0 | 0 |
| **All supports** | – | **3892** | **0** | **0** |

*Source: results file field `RESU____REAC_NODA`, sum over the group's nodes.*

Reaction resultants printed by `POST_RELEVE_T`:

| Table entry | File | X [N] | Y [N] | Z [N] |
| --- | --- | ---: | ---: | ---: |
| `REAC_BASE` | `reactions.csv` | 3892 | 0 | 0 |

### Applied loads

| Load | Type | Applied to | Status | Basis | X [N] | Y [N] | Z [N] |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `PRESS` | distributed pressure (`PRES_REP`) | Shell inner wall (pressure) (`P_SHELL`), Nozzle bore (pressure) (`P_NOZZLE`) | summed | -PRES × vector area of 3843 faces | -3892 | 0 | 0 |

*Source: load values from the command file; areas, lengths and node counts from the mesh in `output/run.rmed`.*

### Equilibrium check

|  | X [N] | Y [N] | Z [N] |
| --- | ---: | ---: | ---: |
| Support reactions (sum) | 3892 | 0 | 0 |
| Applied loads (resultant) | -3892 | 0 | 0 |
| Residual (reactions + applied) | 0 | 0 | 0 |

Balance error: **less than 0.000001 %** (magnitude of the residual over the magnitude of the applied resultant).

*Source: reactions from results file field `RESU____REAC_NODA` (sum of all nodes); applied loads summed from the command file over the result mesh.*

## Diagnostics

The solver issued no warning or error.

*Source: solver log, rendered in English from the overlay's message catalog.*

## Verification

| Check | Quantity | Reference type | Reference | Computed | Error | Tolerance | Verdict |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `REAC_DX_SUM` | Sum of X reactions at the base [N] | analytical (`ANALYTIQUE`) | 3891.64 | 3891.642819 | 7.243164E-05% | 0.1% | pass |

1 of 1 non-regression checks (computed value against the value stored in the command file) passed.

*Source: `TEST_RESU` output in the solver log; pass or fail by the solver's own tolerance.*

## Appendix A: command file

`input/run.comm` as run, verbatim. Command and keyword names are the solver's own (French) API. Lines starting with `# >>` are added by this report: an English one-line description of the command below.

```python
# solid_static -- cylindrical shell with a radial nozzle under internal pressure.
# codeaster-en test fixture (task 4.1). Units: mm, N, MPa.
# Geometry: shell Ri=100 Ro=120 H=300 (axis Z); nozzle ri=25 ro=35 on +X at Z=150, open end at X=220.
# Base (Z=0) fully fixed; internal pressure P on the shell inner wall and the nozzle bore.
# Check: the reaction sum at the base balances the applied pressure resultant. With an open
# nozzle end the resultant is P * (area of the bore opening) along -X; see run.json "checks".
# Modelled on astest forma01a (LIRE_MAILLAGE MED, ORIE_PEAU, PRES_REP, CALC_CHAMP SIEQ_NOEU)
# and zzzz341b (POST_RELEVE_T RESULTANTE on REAC_NODA).
# VALE_CALC values are the solver's own results from the first run (task 4.2, code_aster
# 17.4.22 image, see ADR-011); TEST_RESU checks them at the default TOLE_MACHINE.

# >> DEBUT: begin study
DEBUT(CODE="OUI", ERREUR=_F(ALARME="EXCEPTION"))

P = 2.0  # internal pressure [MPa]

# >> LIRE_MAILLAGE: read mesh
MAIL = LIRE_MAILLAGE(FORMAT="MED", UNITE=20)

# >> DEFI_GROUP: define groups
MAIL = DEFI_GROUP(reuse=MAIL, MAILLAGE=MAIL, CREA_GROUP_NO=_F(GROUP_MA="BASE"))

# >> MODI_MAILLAGE: modify mesh
MAIL = MODI_MAILLAGE(reuse=MAIL, MAILLAGE=MAIL, ORIE_PEAU=_F(GROUP_MA_PEAU=("P_SHELL", "P_NOZZLE")))

# TOUT="OUI" so the pressure faces (TRIA3 skin cells) get boundary elements, as in forma01a.
# >> AFFE_MODELE: assign model
MODE = AFFE_MODELE(MAILLAGE=MAIL, AFFE=_F(TOUT="OUI", PHENOMENE="MECANIQUE", MODELISATION="3D"))

# >> DEFI_MATERIAU: define material
ACIER = DEFI_MATERIAU(ELAS=_F(E=210000.0, NU=0.3))

# >> AFFE_MATERIAU: assign material
MATE = AFFE_MATERIAU(MAILLAGE=MAIL, AFFE=_F(GROUP_MA="SOLID", MATER=ACIER))

# >> AFFE_CHAR_MECA: assign mechanical loads and BCs
FIXE = AFFE_CHAR_MECA(MODELE=MODE, DDL_IMPO=_F(GROUP_MA="BASE", DX=0.0, DY=0.0, DZ=0.0))

# >> AFFE_CHAR_MECA: assign mechanical loads and BCs
PRESS = AFFE_CHAR_MECA(MODELE=MODE, PRES_REP=_F(GROUP_MA=("P_SHELL", "P_NOZZLE"), PRES=P))

# >> MECA_STATIQUE: linear static analysis
RESU = MECA_STATIQUE(
    MODELE=MODE,
    CHAM_MATER=MATE,
    EXCIT=(_F(CHARGE=FIXE), _F(CHARGE=PRESS)),
    SOLVEUR=_F(METHODE="MUMPS"),
)

# >> CALC_CHAMP: compute derived fields
RESU = CALC_CHAMP(
    reuse=RESU,
    RESULTAT=RESU,
    CONTRAINTE=("SIGM_ELNO", "SIGM_NOEU"),
    CRITERES=("SIEQ_ELNO", "SIEQ_NOEU"),
    FORCE="REAC_NODA",
)

# >> POST_RELEVE_T: extract values to table
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

# >> IMPR_TABLE: write table
IMPR_TABLE(TABLE=REAC, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=30)

# >> IMPR_RESU: write results
IMPR_RESU(
    FORMAT="MED",
    UNITE=80,
    RESU=_F(RESULTAT=RESU, NOM_CHAM=("DEPL", "SIGM_NOEU", "SIEQ_NOEU", "REAC_NODA")),
)

# Reaction sum over the whole REAC_NODA field (non-zero only on the fixed base nodes).
# TYPE_TEST sums the whole field; GROUP_NO is not combined with it (see bibfor/test/trresu.F90).
# The reference is signed: REAC_NODA is the support reaction, so its sum is +X, opposite to the
# applied resultant along -X. Confirmed by the first run (task 4.2): DX sum = +3891.64 N.
# >> TEST_RESU: test result value
TEST_RESU(
    RESU=(
        _F(
            NUME_ORDRE=1,
            RESULTAT=RESU,
            NOM_CHAM="REAC_NODA",
            NOM_CMP="DX",
            TYPE_TEST="SOMM",
            REFERENCE="ANALYTIQUE",
            VALE_REFE=3891.64,
            VALE_CALC=3891.6428187786923,
            PRECISION=1.0e-3,
            LEGENDE="REAC_DX_SUM",
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
