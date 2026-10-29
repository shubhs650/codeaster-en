# Block under remote, body and water loads

| Item | Value |
| --- | --- |
| Project | codeaster-en fixtures |
| Revision | A |
| Author | codeaster-en |
| Date | 2026-10-29 |
| Solver | code_aster 17.4.22 |
| English overlay pinned to | code_aster 17.4.26 |
| Report generator | codeaster-en 17.4.26.1 |
| Units | SI-mm (mm, N, MPa, t, s) |

Steel block 200 x 100 x 100 mm on a clamped base under gravity, rotation about Z, water pressure on one face, a remote force and moment spread over the top face (RBE3), with a spring to a fixed ground node. Linear hexahedra, linear elastic steel.

*This report was produced by software from the results of one run. It documents what the solver computed; it is not a verdict on compliance with any design code.*

## Summary

| Item | Value |
| --- | --- |
| Analysis | linear static |
| Outcome | completed |
| Model size | 1379 nodes, 1410 elements |
| Elapsed time (whole job) | 4.610 s |
| CPU time (sum of commands) | 1.650 s |
| Peak memory | 832.4 MB |

Headline results:

- Maximum displacement magnitude: 140.6e-6 mm at node 27 (200.0, 100.0, 100.0).
- Maximum von Mises stress (`SIEQ_NOEU`): 0.3569 MPa at node 9 (200.0, 100.0, 0).
- Equilibrium check: not made, because some applied loads are not summed by this report (see Results: reactions).

*Source: solver log (outcome, times, memory), results file (model size, extrema), command file and results file (balance).*

## Model

| Applied to | Physics | Modeling type | Command file line |
| --- | --- | --- | --- |
| whole mesh (`TOUT`) | mechanical (`MECANIQUE`) | 3D solid (`3D`) | 31 |
| Spring to ground (`SPRING`) | mechanical | translational discrete element (spring/mass) (`DIS_T`) | 31 |
| Remote point (100, 50, 200) (`MASTER`) | mechanical | translational+rotational discrete element (`DIS_TR`) | 31 |

The mesh has 1379 nodes and 1410 elements.

| Element type | Count |
| --- | ---: |
| 8-node hexahedron (`HEXA8`) | 1024 |
| point element (1 node) (`POI1`) | 1 |
| 4-node quadrangle (`QUAD4`) | 384 |
| 2-node segment (`SEG2`) | 1 |
| **Total** | **1410** |

| Axis | Min [mm] | Max [mm] | Extent [mm] |
| --- | ---: | ---: | ---: |
| X | 0 | 250.0 | 250.0 |
| Y | 0 | 100.0 | 100.0 |
| Z | 0 | 200.0 | 200.0 |

*Source: mesh in `output/run.rmed`; model assignment from the command file.*

## Materials

### Material `ACIER`

Assigned to: Block (`BLOCK`).

Law: linear elastic (`ELAS`).

| Property | Value | Unit |
| --- | ---: | --- |
| Young's modulus (`E`) | 210.0e3 | MPa |
| Poisson's ratio (`NU`) | 0.3000 | – |
| density (`RHO`) | 7.850e-9 | t/mm³ |

*Source: command file line 40.*

## Element properties

| Property | Applied to | Values |
| --- | --- | --- |
| discrete element properties (`DISCRET`) | Spring to ground (`SPRING`) | `REPERE` = `"GLOBAL"`; `CARA` = `"K_T_D_L"`; `VALE` = (1000, 1000, 1000) |
| discrete element properties | Spring to ground (`SPRING`) | `CARA` = `"M_T_D_L"`; `VALE` = (0) |
| discrete element properties | Remote point (100, 50, 200) (`MASTER`) | `REPERE` = `"GLOBAL"`; `CARA` = `"K_TR_D_N"`; `VALE` = (0, 0, 0, 0, 0, 0) |
| discrete element properties | Remote point (100, 50, 200) (`MASTER`) | `CARA` = `"M_TR_D_N"`; `VALE` = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0) |

*Source: command file line 44; values in model units.*

## Loads and boundary conditions

| Load | Type | Kind | Applied to | Values | In load case |
| --- | --- | --- | --- | --- | --- |
| `FIXE` | imposed DOF (`DDL_IMPO`) | boundary condition ¹ | Clamped base (Z = 0) (`BASE`) | `DX` = 0; `DY` = 0; `DZ` = 0 | yes |
| `SOL` | imposed DOF | boundary condition ¹ | `GROUND` | `DX` = 0; `DY` = 0; `DZ` = 0 | yes |
| `REMOTE` | RBE3 distributed coupling (`LIAISON_RBE3`) | boundary condition ¹ | Remote point (100, 50, 200) (`MASTER`), Top face (RBE3 slave nodes) (`TOP`) | `DDL_MAIT` = (`"DX"`, `"DY"`, `"DZ"`, `"DRX"`, `"DRY"`, `"DRZ"`); `DDL_ESCL` = `"DX-DY-DZ"`; `COEF_ESCL` = 1.000 | yes |
| `REMOTE` | nodal force (`FORCE_NODALE`) | load | Remote point (100, 50, 200) (`MASTER`) | `FX` = 200.0; `FY` = 0; `FZ` = -500.0; `MX` = 0; `MY` = 0; `MZ` = 20000 | yes |
| `PESA` | gravity (`PESANTEUR`) | load | Block (`BLOCK`) | `GRAVITE` = 9810; `DIRECTION` = (0, 0, -1.000) | yes |
| `ROTA` | rotation (centrifugal load) (`ROTATION`) | load | Block (`BLOCK`) | `VITESSE` = 20.00; `AXE` = (0, 0, 1.000); `CENTRE` = (0, 0, 0) | yes |
| `HYDRO` | distributed pressure (`PRES_REP`) | load | Water face (Y = 0) (`WET`) | `PRES` = `P_HYDRO` | yes |

The load case is the `EXCIT` list of `MECA_STATIQUE`: `FIXE`, `SOL`, `REMOTE`, `PESA`, `ROTA`, `HYDRO`.

¹ Boundary conditions are enforced by Lagrange multipliers (`AFFE_CHAR_MECA`: Lagrange multipliers; `AFFE_CHAR_CINE`: eliminated).

`P_HYDRO` is a formula (`FORMULE`) of `Z`: `max(1.0e-9 * 9810.0 * (1000.0 - Z), 0.0)`.

*Source: command file line 60, 62, 64, 76, 80, 86, 88; values in model units.*

## Solution

| Item | Value |
| --- | --- |
| Solve command | linear static analysis (`MECA_STATIQUE`) |
| Linear solver | MUMPS direct solver (`MUMPS`) |
| Renumbering | `AUTO` |
| Equations (degrees of freedom) | 5076 |
| Physical degrees of freedom | 4140 on 1379 nodes |
| Lagrange multipliers | 936 for 468 dualized linear relations |
| Solve time | 0.5500 s CPU, 0.7700 s elapsed |

*Source: solver settings from the command echo in the solver log (defaults filled in); degrees of freedom from the solver log message FACTOR_1.*

## Results: displacements

Maximum displacement magnitude: **140.6e-6 mm** at node 27 (200.0, 100.0, 100.0).

Displacement magnitude (`DEPL`, translations), per group:

| Group | Component | Min | At | Max | At | Unit |
| --- | --- | ---: | --- | ---: | --- | --- |
| whole model | magnitude | 0 | node 28 (250.0, 50.00, 50.00) | 140.6e-6 | node 27 (200.0, 100.0, 100.0) | mm |
| Block (`BLOCK`) | magnitude | 0 | node 46 (37.50, 50.00, 0) | 140.6e-6 | node 27 (200.0, 100.0, 100.0) | mm |
| Clamped base (Z = 0) (`BASE`) | magnitude | 0 | node 46 (37.50, 50.00, 0) | 3.261e-21 | node 341 (162.5, 87.50, 0) | mm |

Displacement components, whole model:

| Group | Component | Min | At | Max | At | Unit |
| --- | --- | ---: | --- | ---: | --- | --- |
| whole model | X translation (`DX`) | 0 | node 1 (0, 0, 0) | 101.4e-6 | node 23 (200.0, 0, 100.0) | mm |
| whole model | Y translation (`DY`) | -22.05e-6 | node 19 (0, 0, 100.0) | 96.17e-6 | node 27 (200.0, 100.0, 100.0) | mm |
| whole model | Z translation (`DZ`) | -89.31e-6 | node 27 (200.0, 100.0, 100.0) | 21.11e-6 | node 196 (0, 12.50, 100.0) | mm |
| whole model | rotation about X (`DRX`) | -233.4e-9 | node 29 (100.0, 50.00, 200.0) | 0 | node 1 (0, 0, 0) | rad |
| whole model | rotation about Y (`DRY`) | 0 | node 1 (0, 0, 0) | 296.3e-9 | node 29 (100.0, 50.00, 200.0) | rad |
| whole model | rotation about Z (`DRZ`) | 0 | node 1 (0, 0, 0) | 468.1e-9 | node 29 (100.0, 50.00, 200.0) | rad |

*Source: results file field `RESU____DEPL`, last stored step.*

## Results: stresses

Stresses: equivalent stress (nodal average) (`SIEQ_NOEU`), nodal average (values of adjoining elements averaged at each node).

| Group | Component | Min | At | Max | At | Unit |
| --- | --- | ---: | --- | ---: | --- | --- |
| whole model | von Mises (`VMIS`) | 0.008035 | node 152 (37.50, 100.0, 50.00) | 0.3569 | node 9 (200.0, 100.0, 0) | MPa |
| Block (`BLOCK`) | von Mises | 0.008035 | node 152 (37.50, 100.0, 50.00) | 0.3569 | node 9 (200.0, 100.0, 0) | MPa |
| Clamped base (Z = 0) (`BASE`) | von Mises | 0.01669 | node 59 (25.00, 100.0, 0) | 0.3569 | node 9 (200.0, 100.0, 0) | MPa |
| whole model | Tresca (`TRESCA`) | 0.009145 | node 152 (37.50, 100.0, 50.00) | 0.3804 | node 9 (200.0, 100.0, 0) | MPa |
| Block (`BLOCK`) | Tresca | 0.009145 | node 152 (37.50, 100.0, 50.00) | 0.3804 | node 9 (200.0, 100.0, 0) | MPa |
| Clamped base (Z = 0) (`BASE`) | Tresca | 0.01884 | node 59 (25.00, 100.0, 0) | 0.3804 | node 9 (200.0, 100.0, 0) | MPa |
| whole model | 1st principal (`PRIN_1`) | -0.5331 | node 9 (200.0, 100.0, 0) | 0.05081 | node 1 (0, 0, 0) | MPa |
| Block (`BLOCK`) | 1st principal | -0.5331 | node 9 (200.0, 100.0, 0) | 0.05081 | node 1 (0, 0, 0) | MPa |
| Clamped base (Z = 0) (`BASE`) | 1st principal | -0.5331 | node 9 (200.0, 100.0, 0) | 0.05081 | node 1 (0, 0, 0) | MPa |
| whole model | 3rd principal (`PRIN_3`) | -0.1527 | node 9 (200.0, 100.0, 0) | 0.2052 | node 1 (0, 0, 0) | MPa |
| Block (`BLOCK`) | 3rd principal | -0.1527 | node 9 (200.0, 100.0, 0) | 0.2052 | node 1 (0, 0, 0) | MPa |
| Clamped base (Z = 0) (`BASE`) | 3rd principal | -0.1527 | node 9 (200.0, 100.0, 0) | 0.2052 | node 1 (0, 0, 0) | MPa |

*Source: results file field `RESU____SIEQ_NOEU`, last stored step.*

## Results: reactions

Sum of nodal reactions per support group (the force each support exerts on the structure):

| Group | Nodes | Force X (`DX`) [N] | Force Y (`DY`) [N] | Force Z (`DZ`) [N] | Moment about X (`DRX`) [N·mm] | Moment about Y (`DRY`) [N·mm] | Moment about Z (`DRZ`) [N·mm] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Clamped base (Z = 0) (`BASE`) | 153 | -828.0 | -500.4 | 654.0 | 0 | 0 | 0 |
| Spring to ground (`SPRING`) | 2 | -0.03791 | -0.03674 | 0.03242 | 0 | 0 | 0 |
| **All supports** | – | **-828.0** | **-500.4** | **654.0** | **0** | **0** | **-20000** |

Nodes tied by linear relations (`LIAISON_RBE3`) also carry reactions, the relation forces. They cancel in the force sums, so the totals are still the support reactions; the rotation columns of the totals hold the reaction of a remote point to its applied moment, not a support moment.

*Source: results file field `RESU____REAC_NODA`, sum over the group's nodes.*

Reaction resultants printed by `POST_RELEVE_T`:

| Table entry | File | X [N] | Y [N] | Z [N] |
| --- | --- | ---: | ---: | ---: |
| `MOMENT_SUPPORTS` | `moments.csv` | -828.0 | -500.4 | 654.0 |
| `REAC_SUPPORTS` | `reactions.csv` | -828.0 | -500.4 | 654.0 |

### Applied loads

| Load | Type | Applied to | Status | Basis | X [N] | Y [N] | Z [N] |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `REMOTE` | nodal force (`FORCE_NODALE`) | Remote point (100, 50, 200) (`MASTER`) | summed | force × 1 nodes (full force at every node) | 200.0 | 0 | -500.0 |
| `PESA` | gravity (`PESANTEUR`) | Block (`BLOCK`) | not evaluated | body load: needs the mass distribution, not summed | – | – | – |
| `ROTA` | rotation (centrifugal load) (`ROTATION`) | Block (`BLOCK`) | not evaluated | body load: needs the mass distribution, not summed | – | – | – |
| `HYDRO` | distributed pressure (`PRES_REP`) | Water face (Y = 0) (`WET`) | not evaluated | values are functions: not evaluated | – | – | – |

*Source: load values from the command file; areas, lengths and node counts from the mesh in `output/run.rmed`.*

### Equilibrium check

|  | X [N] | Y [N] | Z [N] |
| --- | ---: | ---: | ---: |
| Support reactions (sum) | -828.0 | -500.4 | 654.0 |
| Applied loads (resultant) | 200.0 | 0 | -500.0 |
| Residual (reactions + applied) | -628.0 | -500.4 | 154.0 |

Note: some loads were not evaluated, so the applied resultant is partial and the balance is indicative only.

*Source: reactions from results file field `RESU____REAC_NODA` (sum of all nodes); applied loads summed from the command file over the result mesh.*

## Diagnostics

The solver issued no warning or error.

*Source: solver log, rendered in English from the overlay's message catalog.*

## Verification

| Check | Quantity | Reference type | Reference | Computed | Error | Tolerance | Verdict |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `REAC_DX_SUM` | Sum of X reactions over the whole field [N] | analytical (`ANALYTIQUE`) | -828 | -828 | 1.235726E-13% | 0.01% | pass |
| `REAC_DY_SUM` | Sum of Y reactions over the whole field [N] | analytical | -500.39 | -500.39 | 6.815894E-14% | 0.01% | pass |
| `REAC_DZ_SUM` | Sum of Z reactions over the whole field [N] | analytical | 654.017 | 654.017 | 0.0% | 0.01% | pass |

3 of 3 non-regression checks (computed value against the value stored in the command file) passed.

*Source: `TEST_RESU` output in the solver log; pass or fail by the solver's own tolerance.*

## Appendix A: command file

`input/run.comm` as run, verbatim. Command and keyword names are the solver's own (French) API. Lines starting with `# >>` are added by this report: an English one-line description of the command below.

```python
# solid_loads -- steel block on its base under the Tier 2 loads (task 6.4).
# codeaster-en test fixture. Units: mm, N, MPa, tonne, s (density in t/mm3).
# Block 200 (X) x 100 (Y) x 100 (Z), HEXA8, steel E=210000, NU=0.3, RHO=7.85e-9; base Z=0 clamped.
# Loads: gravity 9810 mm/s2 along -Z; rotation 20 rad/s about Z through the origin; water
# (1e-9 t/mm3, free surface Z=1000) on the face Y=0; F=(200, 0, -500) N and M=(0, 0, 2.0e4) N.mm
# at the remote point MASTER (100, 50, 200), spread over the top face by RBE3; a 1000 N/mm spring
# from (200, 50, 50) to a fixed ground node at (250, 50, 50).
# Check: the REAC_NODA sum over the whole field is minus the sum of the applied forces (see
# run.json "checks" and hand_values.py). Modelled on astest zzzz144a (DIS_TR point, LIAISON_RBE3,
# FORCE_NODALE), sdnv138c (pressure FORMULE), erreu01a (ROTATION) and forma01d (ENV_SPHERE).
# VALE_CALC values are the solver's own results from the first run (task 6.4c).

# >> DEBUT: begin study
DEBUT(CODE="OUI", ERREUR=_F(ALARME="EXCEPTION"))

# >> LIRE_MAILLAGE: read mesh
MAIL = LIRE_MAILLAGE(FORMAT="MED", UNITE=20)

# >> DEFI_GROUP: define groups
MAIL = DEFI_GROUP(reuse=MAIL, MAILLAGE=MAIL, CREA_GROUP_NO=_F(GROUP_MA=("BASE", "TOP", "MASTER")))

# The free end of the spring is not a mesh group: a POI1 there would be included in the SEG2
# and raise alarm MODELISA8_14.
# >> DEFI_GROUP: define groups
MAIL = DEFI_GROUP(
    reuse=MAIL,
    MAILLAGE=MAIL,
    CREA_GROUP_NO=_F(
        NOM="GROUND", OPTION="ENV_SPHERE", POINT=(250.0, 50.0, 50.0), RAYON=0.1, PRECISION=0.1
    ),
)

# >> MODI_MAILLAGE: modify mesh
MAIL = MODI_MAILLAGE(reuse=MAIL, MAILLAGE=MAIL, ORIE_PEAU=_F(GROUP_MA_PEAU="WET"))

# >> AFFE_MODELE: assign model
MODE = AFFE_MODELE(
    MAILLAGE=MAIL,
    AFFE=(
        _F(TOUT="OUI", PHENOMENE="MECANIQUE", MODELISATION="3D"),
        _F(GROUP_MA="SPRING", PHENOMENE="MECANIQUE", MODELISATION="DIS_T"),
        _F(GROUP_MA="MASTER", PHENOMENE="MECANIQUE", MODELISATION="DIS_TR"),
    ),
)

# >> DEFI_MATERIAU: define material
ACIER = DEFI_MATERIAU(ELAS=_F(E=210000.0, NU=0.3, RHO=7.85e-9))

# >> AFFE_MATERIAU: assign material
MATE = AFFE_MATERIAU(MAILLAGE=MAIL, AFFE=_F(GROUP_MA="BLOCK", MATER=ACIER))

# >> AFFE_CARA_ELEM: assign element properties
CARA = AFFE_CARA_ELEM(
    MODELE=MODE,
    DISCRET=(
        _F(REPERE="GLOBAL", CARA="K_T_D_L", GROUP_MA="SPRING", VALE=(1000.0, 1000.0, 1000.0)),
        _F(CARA="M_T_D_L", GROUP_MA="SPRING", VALE=(0.0,)),
        _F(
            REPERE="GLOBAL", CARA="K_TR_D_N", GROUP_MA="MASTER", VALE=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        ),
        _F(
            CARA="M_TR_D_N",
            GROUP_MA="MASTER",
            VALE=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ),
    ),
)

# >> AFFE_CHAR_MECA: assign mechanical loads and BCs
FIXE = AFFE_CHAR_MECA(MODELE=MODE, DDL_IMPO=_F(GROUP_MA="BASE", DX=0.0, DY=0.0, DZ=0.0))

# >> AFFE_CHAR_MECA: assign mechanical loads and BCs
SOL = AFFE_CHAR_MECA(MODELE=MODE, DDL_IMPO=_F(GROUP_NO="GROUND", DX=0.0, DY=0.0, DZ=0.0))

# >> AFFE_CHAR_MECA: assign mechanical loads and BCs
REMOTE = AFFE_CHAR_MECA(
    MODELE=MODE,
    LIAISON_RBE3=_F(
        GROUP_NO_MAIT="MASTER",
        GROUP_NO_ESCL="TOP",
        DDL_MAIT=("DX", "DY", "DZ", "DRX", "DRY", "DRZ"),
        DDL_ESCL="DX-DY-DZ",
        COEF_ESCL=1.0,
    ),
    FORCE_NODALE=_F(GROUP_NO="MASTER", FX=200.0, FY=0.0, FZ=-500.0, MX=0.0, MY=0.0, MZ=20000.0),
)

# >> AFFE_CHAR_MECA: assign mechanical loads and BCs
PESA = AFFE_CHAR_MECA(
    MODELE=MODE, PESANTEUR=_F(GROUP_MA="BLOCK", GRAVITE=9810.0, DIRECTION=(0.0, 0.0, -1.0))
)

# >> AFFE_CHAR_MECA: assign mechanical loads and BCs
ROTA = AFFE_CHAR_MECA(
    MODELE=MODE,
    ROTATION=_F(GROUP_MA="BLOCK", VITESSE=20.0, AXE=(0.0, 0.0, 1.0), CENTRE=(0.0, 0.0, 0.0)),
)

# Water pressure rho g (h - Z) in MPa: rho = 1e-9 t/mm3, g = 9810 mm/s2, h = 1000 mm.
P_HYDRO = FORMULE(VALE="max(1.0e-9 * 9810.0 * (1000.0 - Z), 0.0)", NOM_PARA="Z")

# >> AFFE_CHAR_MECA_F: assign mechanical loads and BCs (function-valued)
HYDRO = AFFE_CHAR_MECA_F(MODELE=MODE, PRES_REP=_F(GROUP_MA="WET", PRES=P_HYDRO))

# >> MECA_STATIQUE: linear static analysis
RESU = MECA_STATIQUE(
    MODELE=MODE,
    CHAM_MATER=MATE,
    CARA_ELEM=CARA,
    EXCIT=(
        _F(CHARGE=FIXE),
        _F(CHARGE=SOL),
        _F(CHARGE=REMOTE),
        _F(CHARGE=PESA),
        _F(CHARGE=ROTA),
        _F(CHARGE=HYDRO),
    ),
    SOLVEUR=_F(METHODE="MUMPS"),
)

# >> CALC_CHAMP: compute derived fields
RESU = CALC_CHAMP(reuse=RESU, RESULTAT=RESU, CRITERES="SIEQ_NOEU", FORCE="REAC_NODA")

# >> POST_RELEVE_T: extract values to table
REAC = POST_RELEVE_T(
    ACTION=_F(
        OPERATION="EXTRACTION",
        INTITULE="REAC_SUPPORTS",
        RESULTAT=RESU,
        NOM_CHAM="REAC_NODA",
        GROUP_NO=("BASE", "GROUND"),
        RESULTANTE=("DX", "DY", "DZ"),
    )
)

# >> IMPR_TABLE: write table
IMPR_TABLE(TABLE=REAC, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=30)

# Moment of the support reactions about the base center (100, 50, 0): minus the moment of the
# applied loads, including the remote moment MZ (hand_values.py; checked by tests/test_fixture_outputs.py).
# >> POST_RELEVE_T: extract values to table
MOMT = POST_RELEVE_T(
    ACTION=_F(
        OPERATION="EXTRACTION",
        INTITULE="MOMENT_SUPPORTS",
        RESULTAT=RESU,
        NOM_CHAM="REAC_NODA",
        GROUP_NO=("BASE", "GROUND"),
        RESULTANTE=("DX", "DY", "DZ"),
        MOMENT=("DRX", "DRY", "DRZ"),
        POINT=(100.0, 50.0, 0.0),
    )
)

# >> IMPR_TABLE: write table
IMPR_TABLE(TABLE=MOMT, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=32)

# >> POST_ELEM: element-based post-processing
MASSE = POST_ELEM(MODELE=MODE, CHAM_MATER=MATE, CARA_ELEM=CARA, MASS_INER=_F(TOUT="OUI"))

# >> IMPR_TABLE: write table
IMPR_TABLE(TABLE=MASSE, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=31)

# >> IMPR_RESU: write results
IMPR_RESU(
    FORMAT="MED",
    UNITE=80,
    RESU=_F(RESULTAT=RESU, CARA_ELEM=CARA, NOM_CHAM=("DEPL", "SIEQ_NOEU", "REAC_NODA")),
)

# Reaction sums over the whole REAC_NODA field: minus the applied force. The RBE3 relations
# pass forces between TOP and MASTER that cancel in the sum.
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
            VALE_REFE=-828.0,
            VALE_CALC=-828.000000000001,
            PRECISION=1.0e-4,
            LEGENDE="REAC_DX_SUM",
        ),
        _F(
            NUME_ORDRE=1,
            RESULTAT=RESU,
            NOM_CHAM="REAC_NODA",
            NOM_CMP="DY",
            TYPE_TEST="SOMM",
            REFERENCE="ANALYTIQUE",
            VALE_REFE=-500.39,
            VALE_CALC=-500.38999999999965,
            PRECISION=1.0e-4,
            LEGENDE="REAC_DY_SUM",
        ),
        _F(
            NUME_ORDRE=1,
            RESULTAT=RESU,
            NOM_CHAM="REAC_NODA",
            NOM_CMP="DZ",
            TYPE_TEST="SOMM",
            REFERENCE="ANALYTIQUE",
            VALE_REFE=654.017,
            VALE_CALC=654.017,
            PRECISION=1.0e-4,
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
| free-format file (tables) | `../output/tables/mass_inertia.csv` | output | 31 |
| free-format file (tables) | `../output/tables/moments.csv` | output | 32 |
| MED results | `../output/run.rmed` | output | 80 |

*Source: `input/run.export`.*
