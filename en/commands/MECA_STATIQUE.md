---
command: MECA_STATIQUE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/meca_statique.py:33
doc_fr: U4.51.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3d)
examples: [sslv114a, ssls147a, hplv109d, forma02a, petsc05a]
---

# MECA_STATIQUE — linear static analysis

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

`MECA_STATIQUE` solves the linear elastic static problem K·u = f for a model, a material
field, optional element properties and a list of loads, and returns an `evol_elas` result. Each
time value it is given (`INST`, or each value of `LIST_INST`) is a separate linear solve, stored
as one step of the result with the displacement field `DEPL`
(`upstream/code_aster/MacroCommands/meca_statique_ops.py:253`). Time here is a pseudo-time: it
only selects the value of the load multipliers (`FONC_MULT`) and of external state variables
such as a temperature field, never inertia. After the solve the command computes the stress at
Gauss points `SIEF_ELGA` by calling `CALC_CHAMP` (`meca_statique_ops.py:178`), unless
`OPTION='SANS'`. The decision it encodes is "this structure is linear and the load is static":
no material nonlinearity, no contact, no large displacements. Everything else (nodal stresses,
von Mises, reactions) comes afterwards from `CALC_CHAMP`.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Résoudre un problème de mécanique statique linéaire» |
| Kind | `MACRO` (Python: `code_aster.MacroCommands.meca_statique_ops`) |
| Result | `evol_elas` |
| Can reuse its input (`reuse=`) | yes (the object given in `RESULTAT`); catalog `reentrant='f:RESULTAT'` |
| French reference | U4.51.01 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `MODELE`, `CHAM_MATER`, `CARA_ELEM`, `EXCIT`, `CHARGE`, `FONC_MULT`, `SOLVEUR`, `METHODE`, `MUMPS`, `MULT_FRONT`, `RESI_RELA`, `OPTION` |

## Keywords

The `SOLVEUR` keywords come from the common catalog `upstream/code_aster/Cata/Commons/c_solveur.py`,
shared by every command that solves a linear system. Which ones exist depends on `METHODE`
(and, for `GCPC`/`PETSC`, on `PRE_COND`): the same keyword name can appear in several blocs with
a different default, which is why some rows below repeat. For Tier 1 work only `METHODE`,
`RESI_RELA`, `NPREC` and `STOP_SINGULIER` matter; the defaults of the others are what the
fixtures ran with (`tests/fixtures/solid_static/output/run.mess`, echo of the command).

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `RESULTAT` | `evol_elas`, optional | — | *result*. With `reuse=`, the existing result to extend: new steps are stored after its last step (`meca_statique_ops.py:247`) and, with `LIST_INST`, the first time defaults to its last time (`meca_statique_ops.py:88`). Use it to add load steps to an earlier static result. |
| `MODELE` | `modele_sdaster`, required | — | *model*. The finite element model (`AFFE_MODELE`). |
| `CHAM_MATER` | `cham_mater`, optional | — | *material field*. The material field (`AFFE_MATERIAU`). The catalog says it is required unless the model contains only discrete elements (`DIS_*` modelings). In practice always give it. |
| `CARA_ELEM` | `cara_elem`, optional | — | *element properties*. The element properties (`AFFE_CARA_ELEM`): thickness of shells, sections of beams, stiffness of springs. Required as soon as the model has structural elements (catalog help). Rule: at least one of `CHAM_MATER`, `CARA_ELEM`. |
| `EXCIT` | factor keyword, optional, repeatable | — | *applied loads*. Only when `exists("CARA_ELEM")`. One occurrence per load: boundary conditions and forces are both loads here. Optional (U4.51.01 §2): without a load object the only loading is what the material field carries, such as thermal expansion from `AFFE_VARC` (§1); the model must still be held, for example by springs. |
| `EXCIT / CHARGE` | `char_meca` or `char_cine_meca`, required | — | *load*. A load from `AFFE_CHAR_MECA`, `AFFE_CHAR_MECA_F` or `AFFE_CHAR_CINE`. Supports and forces go in separate occurrences (`tests/fixtures/solid_static/input/run.comm:36`). |
| `EXCIT / FONC_MULT` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional | — | *load multiplier function*. A function of `INST` that multiplies this load at each time value: a load history over the steps of `LIST_INST` (`upstream/astest/hplv109d.comm:144`). Without it the multiplier is 1. |
| `EXCIT / TYPE_CHARGE` | text, optional | `'FIXE_CSTE'` | *load type*. One of `'FIXE_CSTE'`: a fixed (not follower) load. The only value in a linear analysis; leave it out. |
| `EXCIT` | factor keyword, required, repeatable | — | *applied loads*. Only when `not exists("CARA_ELEM")`. Same content as the row above, but required. |
| `INST` | real, optional | — | *time step (pseudo-time)*. The single time of the solve. Default `0.0` (rule `UN_PARMI(..., INST=0.0)`). Give it when a `FONC_MULT` or a time-dependent temperature must be read at a time other than 0 (`upstream/astest/petsc05a.comm:106`). |
| `LIST_INST` | `listr8_sdaster`, optional | — | *time-step list*. A list of times (`DEFI_LIST_REEL`): one linear solve and one stored step per time. Use it for load histories through `FONC_MULT` or to follow a thermal result through `AFFE_VARC` (`upstream/astest/forma02a.comm:83`). |
| `INST_INIT` | real, optional | — | Only when `exists("LIST_INST")`. Only the times of `LIST_INST` strictly after `INST_INIT` are computed. Default: the last time of `RESULTAT` when reusing, so only later times are added; otherwise none, and every time of the list is computed (`meca_statique_ops.py:86`–`:91`, `upstream/code_aster/Solvers/Main/time_stepper.py:103`). |
| `INST_FIN` | real, optional | — | *end time*. Only when `exists("LIST_INST")`. Last time of `LIST_INST` to compute. Times are matched with a relative tolerance of 1e-6 (`meca_statique_ops.py:91`). |
| `OPTION` | text, optional | `'SIEF_ELGA'` | *option*. One of `'SIEF_ELGA'`, `'SANS'`. `'SIEF_ELGA'` computes the stress at Gauss points after the solve (and `STRX_ELGA` for multifiber beams, `meca_statique_ops.py:175`). `'SANS'` stores only `DEPL`: for large models where stresses are computed later on a few groups with `CALC_CHAMP`. |
| `SOLVEUR` | factor keyword, optional, present by default | — | *linear solver*. Settings of the linear solver. Present by default with `METHODE='MUMPS'`. |
| `SOLVEUR / METHODE` | text, optional | `'MUMPS'` | *method*. One of `'MULT_FRONT'`, `'LDLT'`, `'MUMPS'`, `'GCPC'`, `'PETSC'`. `MUMPS` (default) and `MULT_FRONT` are direct solvers; `LDLT` is a direct solver for small systems; `GCPC` (conjugate gradient, catalog bloc help) and `PETSC` are iterative. Keep the default. `MUMPS` is the only one that factorizes matrices that are not positive definite (`FACTOR_10` advice). |
| `SOLVEUR / RENUM` | text, optional | `'MDA'` | *renumbering*. One of `'MD'`, `'MDA'`. Only when `equal_to("METHODE", 'MULT_FRONT')`. Reordering of the equations before factorization, to reduce fill-in: minimum degree (`MD`) or approximate minimum degree (`MDA`). Leave the default. |
| `SOLVEUR / NPREC` | integer, optional | `8` | *singularity threshold (digits)*. Only when `equal_to("METHODE", 'MULT_FRONT')`; or `equal_to("METHODE", 'LDLT')`; or `equal_to("METHODE", 'MUMPS')`. The number of decimal digits that a pivot may lose during factorization before the matrix is declared singular (`FACTOR_10`). Values below 0 or above 13 print `FACTOR_9` (`upstream/bibfor/algorith/cresol.F90:100`); a negative value switches the detection off for `MUMPS` (`upstream/bibfor/algeline/tldlg3.F90:372`). Keep 8. |
| `SOLVEUR / ELIM_LAGR` | text, optional | `'NON'` | *Lagrange multiplier elimination*. One of `'OUI'`, `'NON'`. Only when `equal_to("METHODE", 'MULT_FRONT')`; or `equal_to("METHODE", 'LDLT')`; or `equal_to("METHODE", 'GCPC')`; or `equal_to("METHODE", 'PETSC')`. `'OUI'` eliminates the Lagrange multipliers of the `AFFE_CHAR_MECA` conditions before solving; refused with kinematic loads (`ELIMLAGR_4`). Leave `'NON'`. |
| `SOLVEUR / STOP_SINGULIER` | text, optional | `'OUI'` | *stop on singular matrix*. One of `'OUI'`, `'NON'`. Only when `equal_to("METHODE", 'MULT_FRONT')`; or `equal_to("METHODE", 'LDLT')`; or `equal_to("METHODE", 'MUMPS')`. `'OUI'`: a matrix that loses more than `NPREC` digits stops the run with an error. `'NON'`: only a warning, unless the factorization cannot finish (`upstream/bibfor/algeline/tldlg3.F90:30`). Never set `'NON'` to get past an unsupported structure. |
| `SOLVEUR / RENUM` | text, optional | `'RCMK'` | *renumbering*. One of `'RCMK'` (reverse Cuthill–McKee). Only when `equal_to("METHODE", 'LDLT')`; or `equal_to("METHODE", 'GCPC') and equal_to("PRE_COND", 'LDLT_INC')`; or `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'LDLT_INC')`. |
| `SOLVEUR / RENUM` | text, optional | `'AUTO'` | *renumbering*. One of `'AMD'`, `'AMF'`, `'PORD'`, `'METIS'`, `'QAMD'`, `'SCOTCH'`, `'AUTO'`, `'PARMETIS'`, `'PTSCOTCH'`. Only when `equal_to("METHODE", 'MUMPS')`. The ordering tool MUMPS uses; `'AUTO'` lets MUMPS choose. |
| `SOLVEUR / ELIM_LAGR` | text, optional | `'LAGR2'` | *Lagrange multiplier elimination*. One of `'OUI'`, `'NON'`, `'LAGR2'`. Only when `equal_to("METHODE", 'MUMPS')`. `'LAGR2'` (default) removes the second multiplier of each doubly dualized condition inside MUMPS; it is switched to `'NON'` automatically when a determinant is needed (`FACTOR_88`). `FACTOR_73` advises `'NON'` for models with many conditions and links. `'LAGR2'` removes the second Lagrange equation of each condition and keeps the first; `'OUI'` eliminates the conditions altogether (method in R3.03.05; in parallel it needs `DISTRIBUTION='CENTRALISE'`) (U4.50.01 §3.2). |
| `SOLVEUR / TYPE_RESOL` | text, optional | `'AUTO'` | One of `'NONSYM'`, `'SYMGEN'`, `'SYMDEF'`, `'AUTO'`. Only when `equal_to("METHODE", 'MUMPS')`. How MUMPS treats the matrix: nonsymmetric, general symmetric, or symmetric positive definite; `'AUTO'` decides from the matrix. Leave the default. |
| `SOLVEUR / ACCELERATION` | text, optional | `'AUTO'` | One of `'AUTO'`, `'FR'`, `'FR+'`, `'FR++'`, `'LR'`, `'LR+'`, `'LR++'`. Only when `equal_to("METHODE", 'MUMPS')`. MUMPS acceleration: full-rank (`FR*`) or block low-rank compression (`LR*`). For very large models only (more than about 2 million DOFs). `'FR'` is standard MUMPS; `'FR+'` adds aggressive internal options such as block analysis; `'FR++'` also speeds up factorization and solution but can upset singularity detection and memory estimates; `'LR'` adds low-rank compression set by `LOW_RANK_SEUIL`; `'LR+'` favors time and `'LR++'` memory. `'AUTO'` is `'FR'` with public MUMPS builds. The `+` levels need a consortium MUMPS build (U4.50.01 §3.5.5). |
| `SOLVEUR / LOW_RANK_SEUIL` | real, optional | `0.0` | *threshold*. Only when `equal_to("METHODE", 'MUMPS')`; or `equal_to("METHODE", 'GCPC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`. Compression threshold of the low-rank factorization. Only with an `LR*` acceleration or a low-rank preconditioner. |
| `SOLVEUR / PRETRAITEMENTS` | text, optional | `'AUTO'` | One of `'SANS'`, `'AUTO'`. Only when `equal_to("METHODE", 'MUMPS')`. Scaling and permutation of the matrix before factorization. `FACTOR_73` advises checking it is on when MUMPS meets numerical difficulties. |
| `SOLVEUR / POSTTRAITEMENTS` | text, optional | `'AUTO'` | One of `'SANS'`, `'AUTO'`, `'FORCE'`, `'MINI'`. Only when `equal_to("METHODE", 'MUMPS')`. Iterative refinement of the MUMPS solution. `'FORCE'` allows more refinement iterations (`FACTOR_62`); `'MINI'` appears in tests that want a cheap solve (`upstream/astest/ssls106a.comm:57`). |
| `SOLVEUR / PCENT_PIVOT` | integer, optional | `35` | *pivoting memory margin (%)*. Range: ≥ 1. Only when `equal_to("METHODE", 'MUMPS')`. Extra memory, in percent, that MUMPS reserves for pivoting. MUMPS retries with larger values on its own (`FACTOR_58`) and stops with `FACTOR_53` if that fails; then raise it. |
| `SOLVEUR / REDUCTION_MPI` | integer, optional | `0` | Range: ≥ 0. Only when `equal_to("METHODE", 'MUMPS')`. With a consortium MUMPS build and MPI only: inside MUMPS, trades MPI processes for OpenMP threads, then restores the launch layout (U4.50.01 §3.5.5). Not used in Tier 1. |
| `SOLVEUR / NB_RHS` | integer, optional | `1` | Range: ≥ 1, ≤ 32. Only when `equal_to("METHODE", 'MUMPS')`. Number of right-hand sides solved together. Leave the default. |
| `SOLVEUR / RESI_RELA` | real, optional | `1e-06` | *relative residual tolerance*. Only when `equal_to("METHODE", 'MUMPS')`; or `equal_to("METHODE", 'GCPC')`; or `equal_to("METHODE", 'PETSC')`. For MUMPS, the largest relative error accepted on the solution of the linear system; above it the command stops (`FACTOR_57`). A negative value switches the check off (`upstream/astest/epicu03a.comm:1325`). For the iterative methods, the convergence criterion. Loosen it (`2e-05`, `upstream/astest/ssls147a.comm:50`) only when `FACTOR_57` reports an error just above the default. |
| `SOLVEUR / GESTION_MEMOIRE` | text, optional | `'AUTO'` | One of `'IN_CORE'`, `'OUT_OF_CORE'`, `'AUTO'`, `'EVAL'`. Only when `equal_to("METHODE", 'MUMPS')`. Whether MUMPS keeps its factors in memory or on disk; `'EVAL'` only estimates the memory needed. `'EVAL'` prints the memory needed in-core and out-of-core at the first MUMPS factorization, then stops with a fatal error so the run can be relaunched with a chosen mode (U4.50.01 §3.5.4). |
| `SOLVEUR / MATR_DISTRIBUEE` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Only when `equal_to("METHODE", 'MUMPS')`; or `equal_to("METHODE", 'PETSC')`. `'OUI'` distributes the assembled matrix between MPI processes in a parallel run (catalog comment: only in `MECA_STATIQUE` and `MECA_NON_LINE`, `c_solveur.py:89`). Serial runs: leave `'NON'`. |
| `SOLVEUR / NIVE_REMPLISSAGE` | integer, optional | `0` | Only when `equal_to("METHODE", 'GCPC') and equal_to("PRE_COND", 'LDLT_INC')`; or `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'LDLT_INC')`. Fill level of the incomplete factorization preconditioner (catalog bloc «factorisation incomplète»). |
| `SOLVEUR / RENUM` | text, optional | `'PARMETIS'` | *renumbering*. One of `'SANS'`, `'METIS'`, `'PARMETIS'`. Only when `equal_to("METHODE", 'GCPC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`. Ordering used by the single-precision or low-rank factorization preconditioner. |
| `SOLVEUR / REAC_PRECOND` | integer, optional | `30` | Only when `equal_to("METHODE", 'GCPC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`. When the factorization preconditioner is recomputed: it is kept while the iterative solver converges in fewer than this many iterations, and refactorized when it needs more (U4.50.01 §3.6). |
| `SOLVEUR / PCENT_PIVOT` | integer, optional | `20` | *pivoting memory margin (%)*. Range: ≥ 1. Only when `equal_to("METHODE", 'GCPC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`. Same as above for the preconditioner; raise it when `ALGELINE5_76` or `PETSC_15` reports a lack of memory. |
| `SOLVEUR / GESTION_MEMOIRE` | text, optional | `'AUTO'` | One of `'IN_CORE'`, `'AUTO'`. Only when `equal_to("METHODE", 'GCPC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`. Memory mode of the preconditioner factorization. |
| `SOLVEUR / PRE_COND` | text, optional | `'LDLT_INC'` | One of `'LDLT_INC'`, `'LDLT_SP'`, `'LDLT_DP'`. Only when `equal_to("METHODE", 'GCPC')`. Preconditioner of the conjugate gradient: incomplete factorization, or a full factorization in single (`SP`) or double (`DP`) precision (catalog bloc help). |
| `SOLVEUR / NMAX_ITER` | integer, optional | `0` | Only when `equal_to("METHODE", 'GCPC')`; or `equal_to("METHODE", 'PETSC')`. Maximum number of iterations of the iterative solver; `0` sets it to half the number of equations for `GCPC`, and to 10000 for `PETSC` (100 with `PRE_COND='LDLT_SP'`) (U4.50.01 §3.6, §3.7). |
| `SOLVEUR / REMPLISSAGE` | real, optional | `1.0` | Only when `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'LDLT_INC')`. Size factor of the `LDLT_INC` preconditioner relative to fill level 0, so that PETSc can reserve its memory; too small an estimate only costs time while PETSc enlarges it (U4.50.01 §3.7). |
| `SOLVEUR / RENUM` | text, optional | `'SANS'` | *renumbering*. One of `'SANS'`. Only when `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'ML')`; or `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'BOOMER')`; or `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'GAMG')`; or `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'HPDDM')`; or `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'BLOC_LAGR')`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('FIELDSPLIT'))`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('UTILISATEUR'))`. No renumbering with these preconditioners. |
| `SOLVEUR / TYPE_RESOL` | text, optional | `'AUTO'` | One of `'AUTO'`, `'GENEO'`, `'HARMO'`. Only when `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'HPDDM')`. Variant of the HPDDM Schwarz preconditioner (catalog bloc «Schwarz HPDDM»). Out of scope. |
| `SOLVEUR / NB_MODE` | integer, optional | — | Range: ≥ 1. Only when `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'HPDDM')`. Number of modes of the HPDDM coarse space; `30` when neither it nor `SEUIL` is given (rule). Out of scope. |
| `SOLVEUR / SEUIL` | real, optional | — | *threshold*. Range: ≥ 0.0. Only when `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'HPDDM')`. Alternative to `NB_MODE` for the HPDDM coarse space. Out of scope. |
| `SOLVEUR / PARTITION_CMP` | integer, optional, list | — | Only when `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('FIELDSPLIT'))`. Sizes of the blocks of components for the PETSc field-split preconditioner, with `NOM_CMP`. Out of scope. |
| `SOLVEUR / NOM_CMP` | text, optional, list | — | *component name*. Only when `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('FIELDSPLIT'))`. The components split into blocks. Out of scope. |
| `SOLVEUR / KSP_UTIL` | `not_checked`, optional | — | Only when `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('UTILISATEUR'))`. A Python function that configures the PETSc solver object (KSP) itself (`upstream/astest/petsc05a.comm:105`). Out of scope. |
| `SOLVEUR / RENUM` | text, optional | `'SANS'` | *renumbering*. One of `'SANS'`, `'RCMK'`. Only when `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('JACOBI','SOR','SANS'))`. |
| `SOLVEUR / ALGORITHME` | text, optional | `'FGMRES'` | One of `'CG'`, `'CR'`, `'GMRES'`, `'GCR'`, `'FGMRES'`, `'GMRES_LMP'`. Only when `equal_to("METHODE", 'PETSC')`. The PETSc Krylov method (conjugate gradient, conjugate residual, GMRES variants). |
| `SOLVEUR / OPTION_PETSC` | text, optional | `''` | Only when `equal_to("METHODE", 'PETSC')`. Extra PETSc command-line options passed as text. Out of scope. |
| `SOLVEUR / PRE_COND` | text, optional | `'LDLT_SP'` | One of `'LDLT_INC'`, `'LDLT_SP'`, `'LDLT_DP'`, `'JACOBI'`, `'SOR'`, `'ML'`, `'BOOMER'`, `'GAMG'`, `'BLOC_LAGR'`, `'FIELDSPLIT'`, `'UTILISATEUR'`, `'HPDDM'`, … (13 values; see the .json). Only when `equal_to("METHODE", 'PETSC')`. The PETSc preconditioner: factorizations as for `GCPC`, Jacobi, SOR, algebraic multigrids (`ML`, `BOOMER` from HYPRE, `GAMG`), the augmented Lagrangian `BLOC_LAGR`, field split, user-defined, or the HPDDM Schwarz method (catalog bloc help). |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `2` also prints timing statistics at the end (`meca_statique_ops.py:289`). |
| `TITRE` | text, optional | — | *title*. Title stored in a new result (`meca_statique_ops.py:203`). |

2 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: exactly one of `INST`, `LIST_INST` must be given; if none is given, `INST=0.0` is assumed (`UN_PARMI`).
- command: at least one of `CHAM_MATER`, `CARA_ELEM` must be given (`AU_MOINS_UN`).
- command: if `reuse` is given, `RESULTAT` must all be given (`PRESENT_PRESENT`).
- when `equal_to("PRE_COND", 'HPDDM')`: exactly one of `SEUIL`, `NB_MODE` must be given; if none is given, `NB_MODE=30` is assumed (`UN_PARMI`).

`compat_syntax` copies `reuse` into `RESULTAT` when only `reuse=` is given
(`upstream/code_aster/Cata/Commands/meca_statique.py:29`).

## What the solver does

From `upstream/code_aster/MacroCommands/meca_statique_ops.py`:

1. Collects the `EXCIT` loads (`:52`) and numbers the DOFs, Lagrange multipliers included (`:215`).
2. Builds the linear solver from `SOLVEUR` (`:218`).
3. For each time value: assembles the elastic stiffness matrix with the dual (Lagrange) terms
   (`:120`) and factorizes it, but only at the first time unless the coded material is not
   constant, for example temperature-dependent (`:240`, `:257`); assembles the right-hand side from the
   imposed values, surface and volume loads, and thermal strains (`:147`–`:156`); solves with the
   kinematic conditions (`:265`); stores `DEPL` (`:270`).
4. Computes `SIEF_ELGA` with `CALC_CHAMP` if `OPTION='SIEF_ELGA'` (`:286`).

The message file shows the size of the system, for example for our solid fixture: 14,730
equations, of which 864 are Lagrange multipliers for the 432 dualized conditions of the clamped
base (`tests/fixtures/solid_static/output/run.mess`, after the echo of `MECA_STATIQUE`).

## Patterns

### One load case, solid model

The minimal call: model, material, supports and loads. The result has one step, at `INST=0.0`.

Source: `upstream/astest/sslv114a.comm:59`.

```python
MES1 = MECA_STATIQUE(MODELE=MOD1, CHAM_MATER=CHMAT_2D, EXCIT=_F(CHARGE=CH1))
```

### Supports and pressure as separate loads, explicit MUMPS

The form of our solid fixture: one `EXCIT` occurrence per load object.

Source: `tests/fixtures/solid_static/input/run.comm:33`.

```python
RESU = MECA_STATIQUE(
    MODELE=MODE,
    CHAM_MATER=MATE,
    EXCIT=(_F(CHARGE=FIXE), _F(CHARGE=PRESS)),
    SOLVEUR=_F(METHODE="MUMPS"),
)
```

### Shells: element properties are required

Source: `tests/fixtures/shell_static/input/run.comm:55`.

```python
RESU = MECA_STATIQUE(
    MODELE=MODE,
    CHAM_MATER=MATE,
    CARA_ELEM=CARA,
    EXCIT=(_F(CHARGE=APPUI), _F(CHARGE=PRESS)),
    SOLVEUR=_F(METHODE="MUMPS"),
)
```

### Load history: several steps with a multiplier function

The pressure load is scaled by `F_EVOL_PRES(INST)` at each time of `L_R`; the kinematic supports
are not scaled. The material field reads a thermal result through `AFFE_VARC`, so each step
also sees the temperature at that time.

Source: `upstream/astest/hplv109d.comm:141` (function at `:136`, time list at `:77`).

```python
RESU_MECA = MECA_STATIQUE(
    MODELE=MOD_MECA,
    CHAM_MATER=CHMAT_MECA,
    EXCIT=(_F(CHARGE=CHMECA, FONC_MULT=F_EVOL_PRES), _F(CHARGE=CHMECA_FIX)),
    LIST_INST=L_R,
)
```

### Thermo-elastic analysis over the times of a thermal result

Source: `upstream/astest/forma02a.comm:83` (temperature in the material field at `:67`).

```python
RESU = MECA_STATIQUE(MODELE=MODMECA, CHAM_MATER=CHMECATH, EXCIT=_F(CHARGE=CHMECA), LIST_INST=LINST)
```

### Looser MUMPS accuracy check

Source: `upstream/astest/ssls147a.comm:49`.

```python
reslin1 = MECA_STATIQUE(
    CHAM_MATER=fieldmat, EXCIT=_F(CHARGE=load1), MODELE=model, SOLVEUR=_F(RESI_RELA=2e-05)
)
```

## Pitfalls

- **Rigid-body motion or redundant supports.** A structure that is not fully supported makes
  the matrix singular: the factorization stops with `FACTOR_10` or `FACTOR_11` (direct solvers)
  or `FACTOR_42` (MUMPS). The message names the DOF of the row; on a physical DOF it is a
  missing support, on a Lagrange DOF a redundant condition (`FACTOR_10` text). Fix the supports;
  do not set `STOP_SINGULIER='NON'` or a negative `NPREC` to hide it (`FACTOR_9` warns that the
  problem solved is then not the one intended).
- **`INST` defaults to 0.** Without `INST` or `LIST_INST`, the solve happens at `INST=0.0`
  (catalog rule). A `FONC_MULT` that ramps from 0 at time 0 then gives a zero load, and a
  temperature field is read at time 0. Give `INST` explicitly with time-dependent data
  (`upstream/astest/petsc05a.comm:106`).
- **Only linear problems.** Material nonlinearity, contact and large displacements are not
  solved here (catalog description: «statique linéaire»); `TYPE_CHARGE` accepts only fixed loads.
  Use `MECA_NON_LINE` / `STAT_NON_LINE` (Tier 2+) for those.
- **Each step is independent.** With `LIST_INST`, every time is a separate linear solve of the
  same structure with the loads scaled at that time (`meca_statique_ops.py:253`); there is no
  load path dependence. Steps are numbered from 1 and `NUME_ORDRE` in later commands refers to
  that index.
- **Stress is at Gauss points only.** The result holds `DEPL` and `SIEF_ELGA`. Nodal stresses,
  equivalent stresses and reactions are not there until `CALC_CHAMP` computes them; asking
  `IMPR_RESU` or `POST_RELEVE_T` for `SIGM_NOEU` before that fails (`POSTRELE_46`).
- **MUMPS accuracy stop.** `FACTOR_57` ("the solution of the linear system is too inaccurate")
  means the computed error exceeds `RESI_RELA`. It often signals a badly conditioned model
  (very different stiffnesses, stretched elements, `FACTOR_9` advice) rather than a setting to
  loosen.

## See also

- French reference: U4.51.01 (French text: `en/docs/_src/U4.51.01.fr.md`; translation: `en/docs/U4.51.01.md`). The
  `SOLVEUR` keywords have their own reference, U4.50.01 (agent recall, not yet in
  en/doc-ids.yaml); `FACTOR_9` points to the linear solver guide U2.08.03
- Catalog: `en/commands/MECA_STATIQUE.json` (generated from `upstream/code_aster/Cata/Commands/meca_statique.py:33`)
- Implementation: `upstream/code_aster/MacroCommands/meca_statique_ops.py`; solver settings
  `upstream/code_aster/Cata/Commons/c_solveur.py`, `upstream/bibfor/algorith/cresol.F90`;
  singularity detection `upstream/bibfor/algeline/tldlg3.F90`
- Before: [AFFE_MODELE](AFFE_MODELE.md), [AFFE_MATERIAU](AFFE_MATERIAU.md),
  [AFFE_CARA_ELEM](AFFE_CARA_ELEM.md), [AFFE_CHAR_MECA](AFFE_CHAR_MECA.md),
  [AFFE_CHAR_CINE](AFFE_CHAR_CINE.md), [DEFI_FONCTION](DEFI_FONCTION.md) (`FONC_MULT`)
- Next steps: [CALC_CHAMP](CALC_CHAMP.md) (stresses, reactions), [POST_RELEVE_T](POST_RELEVE_T.md),
  [IMPR_RESU](IMPR_RESU.md), [TEST_RESU](TEST_RESU.md)
- Example: `upstream/astest/sslv114a.comm` (lines 59, 143)
- Example: `upstream/astest/hplv109d.comm` (line 141)
- Example: `upstream/astest/forma02a.comm` (line 83)
- Example: `tests/fixtures/solid_static/input/run.comm` (line 33)
- Example: `tests/fixtures/shell_static/input/run.comm` (line 55)
