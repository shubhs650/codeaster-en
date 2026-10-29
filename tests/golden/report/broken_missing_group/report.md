# code_aster run broken_missing_group

| Item | Value |
| --- | --- |
| Solver | code_aster 17.4.22 |
| English overlay pinned to | code_aster 17.4.26 |
| Report generator | codeaster-en 0.1.0 |
| Units | model units |

*This report was produced by software from the results of one run. It documents what the solver computed; it is not a verdict on compliance with any design code.*

## Summary

**Run failed at command `AFFE_CHAR_MECA` (command file line 33).**

Fatal message [`MODELISA7_77`]:

> GROUP_MA EDGE is not part of mesh: 00000001

Cause classification: **user-model**, a group named in the command file does not exist in the mesh. Solver diagnostic: `<S>_ERROR`.

Last lines of the solver log (English rendering):

```text
  File "/opt/spack/opt/spack/linux-zen2/code-aster-17.4.22-qvronprjirskcxaala43j55z7obyclfv/lib64/aster/code_aster/Supervis/ExecuteCommand.py", line 516, in exec_
    self._call_oper(syntax)
  File "/opt/spack/opt/spack/linux-zen2/code-aster-17.4.22-qvronprjirskcxaala43j55z7obyclfv/lib64/aster/code_aster/Supervis/ExecuteCommand.py", line 282, in _call_oper
    return libaster.call_oper(syntax, 0)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
libaster.AsterError: 
 ╔================================================================================================╗
 ║ <EXCEPTION> <MODELISA7_77>                                                                     ║
 ║                                                                                                ║
 ║  GROUP_MA  EDGE  is not part of mesh:  00000001                                                ║
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
| CPU time (sum of commands) | 0.2300 s |
| Peak memory | 769.3 MB |
| Warnings | `MODELISA8_14` × 3 |

**Units.** No unit system is declared (run.json units); values are in model units. Young's modulus E = 210000 suggests SI-mm (mm, N, MPa, t, s); this is an assumption, so units are not printed.

*Source: solver log (outcome, times, memory), results file (model size, extrema), command file and results file (balance).*

## Model

| Applied to | Physics | Modeling type | Command file line |
| --- | --- | --- | --- |
| `PLATE` | mechanical (`MECANIQUE`) | thin shell (DKT) (`DKT`) | 23 |

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

*Source: command file line 29.*

## Element properties

| Property | Applied to | Values |
| --- | --- | --- |
| shell properties (`COQUE`) | `PLATE` | `EPAIS` = 10.00; `ANGL_REP` = (0, 0) |

*Source: command file line 27; values in model units.*

## Loads and boundary conditions

| Load | Type | Kind | Applied to | Values | In load case |
| --- | --- | --- | --- | --- | --- |
| `APPUI` | imposed DOF (`DDL_IMPO`) | boundary condition ¹ | `EDGE` | `DZ` = 0 | yes |
| `APPUI` | imposed DOF | boundary condition ¹ | `CORNER_A` | `DX` = 0; `DY` = 0 | yes |
| `APPUI` | imposed DOF | boundary condition ¹ | `CORNER_B` | `DY` = 0 | yes |
| `PRESS` | distributed pressure (`PRES_REP`) | load | `PLATE` | `PRES` = 0.01000 | yes |

The load case is the `EXCIT` list of `MECA_STATIQUE`: `APPUI`, `PRESS`.

¹ Boundary conditions are enforced by Lagrange multipliers (`AFFE_CHAR_MECA`: Lagrange multipliers; `AFFE_CHAR_CINE`: eliminated).

*Source: command file line 33, 44; values in model units.*

## Solution

| Item | Value |
| --- | --- |
| Solve command | linear static analysis (`MECA_STATIQUE`) |
| Linear solver | MUMPS direct solver (`MUMPS`) |

*Source: solver settings from the command file; degrees of freedom from the solver log message FACTOR_1.*

## Diagnostics

| Severity | Message | Count | Command | Text (first occurrence) |
| --- | --- | --- | --- | --- |
| error | `MODELISA7_77` | 1 | `AFFE_CHAR_MECA` | GROUP_MA EDGE is not part of mesh: 00000001 |
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
