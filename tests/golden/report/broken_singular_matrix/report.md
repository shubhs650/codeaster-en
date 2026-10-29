# code_aster run broken_singular_matrix

| Item | Value |
| --- | --- |
| Solver | code_aster 17.4.22 |
| English overlay pinned to | code_aster 17.4.26 |
| Report generator | codeaster-en 0.1.0 |
| Units | model units |

*This report was produced by software from the results of one run. It documents what the solver computed; it is not a verdict on compliance with any design code.*

## Summary

**Run failed at command `MECA_STATIQUE` (command file line 44).**

Fatal message [`FACTOR_11`]:

> Problem: the matrix is singular or nearly singular: During the factorization of the matrix, a problem was found (zero or nearly zero pivot) at row 517, which corresponds to the degree of freedom given above.

> Risks and advice: * If the row is a physical degree of freedom, a rigid-body motion is probably not restrained. Check the boundary conditions. If you use contact, the structure must not be held by contact alone. Also check the material properties (Young's modulus, ...).

> * If the row is a Lagrange degree of freedom, a boundary condition is probably redundant. In particular, the redundant linear relation may come from the contact conditions. You may need to exclude some nodes from the contact conditions (keywords SANS_NOEUD and SANS_GROUP_NO).

> * If the solver is LDLT or MULT_FRONT, you can use the MUMPS solver instead: it is the only one that can factorize matrices that are not positive definite.

> * In parallel, the MUMPS singularity detection criterion is sometimes too pessimistic! It is still often possible to complete the analysis by relaxing this criterion (increase the value of the NPREC keyword by 1 or 2) or by switching it off (NPREC=-1), or by running the analysis on fewer processors.

> * With X-FEM this can also be quite normal when the crack passes very close to a node. If the number of lost decimal digits is not too large (at most 10), you can rerun the analysis with a larger number of allowed lost digits: keyword NPREC of the factor keyword SOLVEUR. Otherwise, contact the development team.

Cause classification: **user-model**, the stiffness matrix is singular (rigid-body motion not restrained, or redundant conditions). Solver diagnostic: `<S>_ERROR`.

Last lines of the solver log (English rendering):

```text
 ║      possible to complete the analysis by relaxing this criterion (increase the value of the   ║
 ║      NPREC keyword by 1 or 2) or                                                               ║
 ║      by switching it off (NPREC=-1), or by running the analysis on fewer processors.           ║
 ║                                                                                                ║
 ║    * With X-FEM this can also be quite normal when the crack passes                            ║
 ║      very close to a node.                                                                     ║
 ║      If the number of lost decimal digits is not too large (at most 10),                       ║
 ║      you can rerun the analysis with a larger number of allowed lost digits:                   ║
 ║      keyword NPREC of the factor keyword SOLVEUR.                                              ║
 ║      Otherwise, contact the development team.                                                  ║
 ╚================================================================================================╝


[1 line(s) printed by the solver outside the message catalog]


[1 line(s) printed by the solver outside the message catalog]

[1 line(s) printed by the solver outside the message catalog]

 ╔================================================================================================╗
 ║ <I> <CATAMESS_89>                                                                              ║
 ║                                                                                                ║
 ║     List of the warnings issued during the analysis.                                           ║
 ║                                                                                                ║
 ║     Warnings you chose to ignore are marked with (*).                                          ║
 ║     Number of occurrences of each warning:                                                     ║
 ║        MODELISA8_14  issued    3 times                                                         ║
 ╚================================================================================================╝

<I> <FIN> NORMAL STOP IN "FIN" BY CALL TO "JEFINI".
  
[3 line(s) printed by the solver outside the message catalog]
  
[1 line(s) printed by the solver outside the message catalog]
  
[9 line(s) printed by the solver outside the message catalog]
  
[9 line(s) printed by the solver outside the message catalog]
  
[14 line(s) printed by the solver outside the message catalog]

[1 line(s) printed by the solver outside the message catalog]



------------------------------------------------------------
--- DIAGNOSTIC JOB : <S>_ERROR
------------------------------------------------------------

```

| Item | Value |
| --- | --- |
| Analysis | linear static |
| Outcome | failed |
| Model size | 441 nodes, 483 elements |
| CPU time (sum of commands) | 0.4200 s |
| Peak memory | 778.1 MB |
| Warnings | `MODELISA8_14` × 3 |

**Units.** No unit system is declared (run.json units); values are in model units. Young's modulus E = 210000 suggests SI-mm (mm, N, MPa, t, s); this is an assumption, so units are not printed.

*Source: solver log (outcome, times, memory), results file (model size, extrema), command file and results file (balance).*

## Model

| Applied to | Physics | Modeling type | Command file line |
| --- | --- | --- | --- |
| `PLATE` | mechanical (`MECANIQUE`) | thin shell (DKT) (`DKT`) | 22 |

The mesh has 441 nodes and 483 elements.

| Element type | Count |
| --- | ---: |
| point element (1 node) (`POI1`) | 3 |
| 4-node quadrangle (`QUAD4`) | 400 |
| 2-node segment (`SEG2`) | 80 |
| **Total** | **483** |

| Axis | Min | Max | Extent |
| --- | ---: | ---: | ---: |
| X | 0 | 1000 | 1000 |
| Y | 0 | 1000 | 1000 |
| Z | 0 | 0 | 0 |

*Source: mesh in `input/mesh.med`; model assignment from the command file.*

## Materials

### Material `ACIER`

Assigned to: `PLATE`.

Law: linear elastic (`ELAS`).

| Property | Value | Unit |
| --- | ---: | --- |
| Young's modulus (`E`) | 210.0e3 | – |
| Poisson's ratio (`NU`) | 0.3000 | – |

*Source: command file line 28.*

## Element properties

| Property | Applied to | Values |
| --- | --- | --- |
| shell properties (`COQUE`) | `PLATE` | `EPAIS` = 10.00; `ANGL_REP` = (0, 0) |

*Source: command file line 26; values in model units.*

## Loads and boundary conditions

| Load | Type | Kind | Applied to | Values | In load case |
| --- | --- | --- | --- | --- | --- |
| `APPUI` | imposed DOF (`DDL_IMPO`) | boundary condition ¹ | `EDGES` | `DZ` = 0 | no |
| `APPUI` | imposed DOF | boundary condition ¹ | `CORNER_A` | `DX` = 0; `DY` = 0 | no |
| `APPUI` | imposed DOF | boundary condition ¹ | `CORNER_B` | `DY` = 0 | no |
| `PRESS` | distributed pressure (`PRES_REP`) | load | `PLATE` | `PRES` = 0.01000 | yes |

The load case is the `EXCIT` list of `MECA_STATIQUE`: `PRESS`.

¹ Boundary conditions are enforced by Lagrange multipliers (`AFFE_CHAR_MECA`: Lagrange multipliers; `AFFE_CHAR_CINE`: eliminated).

*Source: command file line 32, 42; values in model units.*

## Solution

| Item | Value |
| --- | --- |
| Solve command | linear static analysis (`MECA_STATIQUE`) |
| Linear solver | MUMPS direct solver (`MUMPS`) |
| Renumbering | `AUTO` |
| Equations (degrees of freedom) | 2646 |
| Physical degrees of freedom | 2646 on 441 nodes |
| Lagrange multipliers | 0 for 0 dualized linear relations |
| Solve time | 0.1600 s CPU, 0.1700 s elapsed |

*Source: solver settings from the command echo in the solver log (defaults filled in); degrees of freedom from the solver log message FACTOR_1.*

## Diagnostics

| Severity | Message | Count | Command | Text (first occurrence) |
| --- | --- | --- | --- | --- |
| error | `FACTOR_11` | 1 | `MECA_STATIQUE` | Problem: the matrix is singular or nearly singular: During the factorization of the matrix, a problem was found (zero or nearly zero pivot) at row 517, which corresponds to the degree of freedom given above. Risks and advice: * If the row is a physical degree of freedom, a rigid-body motion is probably not restrained. Check the boundary conditions. If you use contact, the structure must not be held by contact alone. Also check the material properties (Young's modulus, ...). * If the row is a Lagrange degree of freedom, a boundary condition is probably redundant. In particular, the redundant linear relation may come from the contact conditions. You may need to exclude some nodes from the contact conditions (keywords SANS_NOEUD and SANS_GROUP_NO). * If the solver is LDLT or MULT_FRONT, you can use the MUMPS solver instead: it is the only one that can factorize matrices that are not positive definite. * In parallel, the MUMPS singularity detection criterion is sometimes too pessimistic! It is still often possible to complete the analysis by relaxing this criterion (increase the value of the NPREC keyword by 1 or 2) or by switching it off (NPREC=-1), or by running the analysis on fewer processors. * With X-FEM this can also be quite normal when the crack passes very close to a node. If the number of lost decimal digits is not too large (at most 10), you can rerun the analysis with a larger number of allowed lost digits: keyword NPREC of the factor keyword SOLVEUR. Otherwise, contact the development team. |
| warning | `MODELISA8_14` | 3 | `LIRE_MAILLAGE` | POI1 element 1 is included in another element. |

*Source: solver log, rendered in English from the overlay's message catalog.*

## Report notes

- Section “Results: displacements” omitted: the run failed (REPORT-SPEC §5).
- Section “Results: stresses” omitted: the run failed (REPORT-SPEC §5).
- Section “Results: reactions” omitted: the run failed (REPORT-SPEC §5).
- Section “Results: natural modes” omitted: the run failed (REPORT-SPEC §5).
- Section “Verification” omitted: the run failed (REPORT-SPEC §5).
- Section “Appendix A: command file” omitted: the run failed (REPORT-SPEC §5).
- Section “Appendix B: run parameters” omitted: the run failed (REPORT-SPEC §5).
- Full-precision values and the source of every number are in `run_model.json`.
