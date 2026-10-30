---
command: CALC_MODES
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/calc_modes.py:70
doc_fr: U4.52.02
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 6.4)
examples: [zzzz351b, rtool01a, sdll18b]
---

# CALC_MODES — compute natural modes

> **Assisted reference.** Written in session from the pinned catalog, the solver source it
> calls, the message catalog, upstream test cases and the committed fixture runs. Every behavior
> claim cites its source. Not reviewed by an engineer.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

Computes the eigenmodes (natural vibration or buckling modes) of a structure.

`CALC_MODES` solves the eigenvalue problem of a structure from its assembled matrices: natural
frequencies and mode shapes, K φ = ω² M φ (`TYPE_RESU='DYNAMIQUE'`, the default), or buckling
load factors with the geometric stiffness (`'MODE_FLAMB'`), or a general A x = λ B x
(`'GENERAL'`). It takes assembled matrices, not a model: `MATR_RIGI` and `MATR_MASS` come from
`ASSE_MATRICE` or `ASSEMBLAGE` on one numbering, with the supports already in them. `OPTION`
says which part of the spectrum to compute (the lowest `NMAX_FREQ` modes, a frequency band, the
modes near a frequency...), and every run checks its own result: error norm of each mode and a
Sturm count of the frequencies in the computed range (`VERI_MODE`). The result (`mode_meca`)
holds the shapes as `DEPL` fields and, per mode, the frequency, generalized mass and stiffness,
participation factors and effective masses (`upstream/bibfor/algeline/vpstor.F90:83`), which the
report reads through `RECU_TABLE` (`tests/fixtures/modal/input/run.comm:50`). It is a Python
macro: it calls `MODE_ITER_SIMULT` (subspace methods) or `MODE_ITER_INV` (inverse iteration)
and then, if asked, `NORM_MODE` and `EXTR_MODE`
(`upstream/code_aster/MacroCommands/Modal/calc_modes_ops.py:90`, `:137`).

| Fact | Value |
|---|---|
| Catalog description (fr) | «Calculer les modes propres ou de flambement d'une structure» |
| Kind | `MACRO` |
| Result | `mode_flamb`, `mode_meca`, `mode_meca_c`, `mode_acou`, `mode_gene`, `DataStructure` (depends on the keywords given) |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.52.02 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 2 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `OPTION`, `PLUS_PETITE`, `BANDE`, `CENTRE`, `CALC_FREQ`, `NMAX_FREQ`, `FREQ`, `SOLVEUR_MODAL`, `MATR_RIGI`, `MATR_MASS`, `MODELE`, `CHAM_MATER` |

COMMAND-SET also lists a "`MODELE`+`CHAM_MATER` form". There is none: `CALC_MODES` has no
`MODELE` keyword, and `CHAM_MATER` and `CARA_ELEM` are only stored in the result (and used for
the center of gravity, see below). The model is found from the numbering of `MATR_RIGI`
(`upstream/code_aster/MacroCommands/Modal/calc_modes_simult.py:50`). The matrices must be built
first (`ASSEMBLAGE` or `CALC_MATR_ELEM` + `NUME_DDL` + `ASSE_MATRICE`).

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `TYPE_RESU` | text, optional | `'DYNAMIQUE'` | *result type*. Type of analysis. One of `'DYNAMIQUE'`, `'MODE_FLAMB'`, `'GENERAL'`. The problem. `'DYNAMIQUE'` (default): free vibration, K φ = ω² M φ, frequencies f = ω / 2π. `'MODE_FLAMB'`: linear buckling, from the elastic stiffness and the geometric stiffness of a prestress (`MATR_RIGI_GEOM`); the eigenvalues are critical load factors (`CHAR_CRIT`, `upstream/code_aster/MacroCommands/Modal/calc_modes_simult.py:54`). `'GENERAL'`: A x = λ B x for any two matrices. Tier 2 uses `'DYNAMIQUE'` only. |
| `CHAM_MATER` | `cham_mater`, optional | — | *material field*. The material field. Not needed to solve: it is stored in the result, so later post-processing (`CALC_CHAMP` stresses on modes) finds it, and with it the macro computes the center of gravity with `POST_ELEM MASS_INER` and passes it to the solver (`upstream/code_aster/MacroCommands/Modal/calc_modes_simult.py:70`, `:85`). Give it, with `CARA_ELEM`, when the modes will be post-processed. |
| `CARA_ELEM` | `cara_elem`, optional | — | *element properties*. Element properties, stored in the result like `CHAM_MATER` (`calc_modes_ops.py:181`). Give it for shell, beam or discrete models whose modes will be post-processed. |
| `MATR_RIGI` | `matr_asse_depl_r` or `matr_asse_depl_c` or `matr_asse_temp_r` or `matr_asse_gene_r` or `matr_asse_gene_c` or `matr_asse_pres_r` or `matr_asse_elim_r`, required | — | *stiffness matrix*. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE')`. The assembled stiffness matrix K (`matr_asse_depl_r` from `ASSE_MATRICE` or `ASSEMBLAGE`, `tests/fixtures/modal/input/run.comm:43`). It must be built with the supports: without them the structure is free and the lowest modes are rigid-body modes at 0 Hz. |
| `MATR_MASS` | `matr_asse_depl_r` or `matr_asse_gene_r` or `matr_asse_pres_r` or `matr_asse_temp_r` or `matr_asse_elim_r`, required | — | *mass matrix*. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE')`. The assembled mass matrix M, on the same numbering as `MATR_RIGI`. |
| `MATR_AMOR` | `matr_asse_depl_r` or `matr_asse_gene_r`, optional | — | Only when `equal_to("TYPE_RESU", 'DYNAMIQUE')`. An assembled damping matrix C: the problem becomes quadratic (complex modes, `mode_meca_c`) and is solved with `APPROCHE`. Not used in Tier 2 (real modes, no damping). |
| `NORM_MODE` | factor keyword, optional | — | *normalize modes*. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE')`; or `equal_to("TYPE_RESU", 'MODE_FLAMB')`; or `equal_to("TYPE_RESU", 'GENERAL')`. Normalize the modes before returning them, with [NORM_MODE](NORM_MODE.md) in place (`upstream/code_aster/MacroCommands/Modal/calc_modes_post.py:35`). Without it each mode keeps the solver's scaling: largest component 1 (`upstream/bibfor/algeline/vppara.F90:130`). |
| `NORM_MODE / NORME` | text, optional | `'TRAN_ROTA'` | *norm*. One of `'MASS_GENE'`, `'RIGI_GENE'`, `'EUCL'`, `'EUCL_TRAN'`, `'TRAN'`, `'TRAN_ROTA'`. The rule, as `NORM_MODE` `NORME`: `'MASS_GENE'` for unit generalized mass (`upstream/astest/sdll07a.comm:205`), `'TRAN_ROTA'` (default here) for a largest displacement or rotation of 1. |
| `NORM_MODE / INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `2` prints the normalization coefficients. See [NORM_MODE](NORM_MODE.md). |
| `OPTION` | text, optional | `'PLUS_PETITE'` | *option*. Choice of the search range. One of `'PLUS_PETITE'`, `'PLUS_GRANDE'`, `'BANDE'`, `'CENTRE'`, `'TOUT'`, `'SEPARE'`, `'AJUSTE'`, `'PROCHE'`. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE')`. Which modes to compute. `'PLUS_PETITE'` (default): the `NMAX_FREQ` lowest frequencies, the usual choice (`tests/fixtures/modal/input/run.comm:43`). `'BANDE'`: every mode between two frequencies (`upstream/astest/forma12a.comm:60`); with more than two values, several bands solved separately, in parallel if MPI is used (`upstream/code_aster/MacroCommands/Modal/calc_modes_ops.py:83`). `'CENTRE'`: the `NMAX_FREQ` modes closest to `FREQ` (`upstream/astest/sdld106a.comm:70`). `'PLUS_GRANDE'`: the highest. `'TOUT'`: all of them (small problems, `METHODE='QZ'`). `'PROCHE'`, `'SEPARE'`, `'AJUSTE'`: inverse iteration from given frequency estimates, to refine a few modes (`calc_modes_ops.py:94`). |
| `CALC_FREQ` | factor keyword, optional, present by default | — | *frequency search settings*. Search for all the natural frequencies. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE') and equal_to("OPTION", 'TOUT')`. What to search for with `OPTION='TOUT'`. The settings below (`NMAX_FREQ`, `NMAX_ITER_SHIFT`, `PREC_SHIFT`, `SEUIL_FREQ`) are the same under every `OPTION` except where a row says otherwise. |
| `CALC_FREQ / NMAX_FREQ` | integer, optional | `10` | *number of frequencies*. Range: ≥ 0. How many modes: with `PLUS_PETITE` (default 10), `CENTRE` (default 10) and `TOUT`, the number of frequencies wanted (`tests/fixtures/modal/input/run.comm:43`: 6). |
| `CALC_FREQ / NMAX_ITER_SHIFT` | integer, optional | `3` | Range: ≥ 0. When the shifted matrix K − σM cannot be factorized (σ is too close to a frequency), the shift is moved and the factorization retried, up to this many times (`upstream/bibfor/algeline/vpfopr.F90:221`; message `ALGELINE6_45`). |
| `CALC_FREQ / PREC_SHIFT` | real, optional | `0.05` | Range: ≥ 0.0. Size of each shift move, as a fraction of the shift (5 % by default, `vpfopr.F90:235`). |
| `CALC_FREQ / SEUIL_FREQ` | real, optional | `0.01` | *rigid-body frequency threshold*. Range: ≥ 0.0. Frequency, in Hz, below which a mode counts as a rigid-body mode (`upstream/bibfor/algeline/vpinis.F90:184`); a shift below it is set to it (`ALGELINE6_44`, `vpfopr.F90:222`). Raise it only for a free structure with many near-zero modes. |
| `CALC_FREQ` | factor keyword, optional, present by default | — | *frequency search settings*. Search for the lowest natural frequencies. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE') and equal_to("OPTION", 'PLUS_PETITE')`. What to search for with `OPTION='PLUS_PETITE'`: `NMAX_FREQ` (default 10) and the shift settings. |
| `CALC_FREQ` | factor keyword, optional, present by default | — | *frequency search settings*. Search for the highest natural frequencies. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE') and equal_to("OPTION", 'PLUS_GRANDE')`. With `OPTION='PLUS_GRANDE'`: `NMAX_FREQ` (default 1) and the shift settings. |
| `CALC_FREQ / NMAX_FREQ` | integer, optional | `1` | *number of frequencies*. Range: ≥ 0. With `PLUS_GRANDE`, the number of highest frequencies (default 1). |
| `CALC_FREQ` | factor keyword, optional, present by default | — | *frequency search settings*. Search for the natural frequencies closest to a given value. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE') and equal_to("OPTION", 'CENTRE')`. With `OPTION='CENTRE'`: the central `FREQ`, `NMAX_FREQ` and the shift settings. |
| `CALC_FREQ / FREQ` | real, required | — | *frequency*. Frequency around which the natural frequencies are sought. The frequency, in Hz, around which `CENTRE` searches. |
| `CALC_FREQ / AMOR_REDUIT` | real, optional | — | Range: ≥ 0.0, ≤ 1.0. Reduced damping ratio of the central value, for the quadratic problem (`MATR_AMOR`). Not used in Tier 2. |
| `CALC_FREQ` | factor keyword, optional, present by default | — | *frequency search settings*. Search for the natural frequencies in a given band. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE') and equal_to("OPTION", 'BANDE')`. With `OPTION='BANDE'`: the band limits `FREQ` and the shift settings. |
| `CALC_FREQ / FREQ` | real, required, list, at least 2 | — | *frequency*. Frequencies that bound the search band(s). The band limits, in Hz, in increasing order: `(f_min, f_max)` (`upstream/astest/forma12a.comm:61`), or more values for consecutive sub-bands solved one by one (`upstream/astest/fdlv112b.comm:151`). |
| `CALC_FREQ / TABLE_FREQ` | `table_sdaster`, optional | — | A table from `INFO_MODE` that already counts the modes per band, so the count is not done again. Optional. |
| `CALC_FREQ / NIVEAU_PARALLELISME` | text, optional | `'COMPLET'` | One of `'PARTIEL'`, `'COMPLET'`. Only when `size('FREQ') > 2`. With several sub-bands and MPI: `'COMPLET'` (default) solves the bands in parallel and, with enough processors and `MUMPS`, also parallelizes each band's linear solver; `'PARTIEL'` keeps only the linear-solver (`MUMPS`) level, to lower the memory peak when nothing else helps (U4.52.02 §3.14). See messages `MODAL_10`–`MODAL_12` for processor counts. |
| `CALC_FREQ` | factor keyword, optional, present by default | — | *frequency search settings*. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE') and equal_to("OPTION", 'PROCHE')`; or `equal_to("TYPE_RESU", 'DYNAMIQUE') and is_in("OPTION", ('SEPARE','AJUSTE'))`. With `PROCHE`, `SEPARE`, `AJUSTE`: the frequency estimates `FREQ` and the shift settings. |
| `CALC_FREQ / FREQ` | real, required, list | — | *frequency*. The frequency estimates, in Hz, one per mode to compute, in increasing order without repeats (catalog validators, `calc_modes.py:229`); from an earlier run or a hand calculation. |
| `CALC_FREQ / AMOR_REDUIT` | real, optional, list | — | Reduced damping estimates, with `FREQ`, for the quadratic problem. Not used in Tier 2. |
| `CALC_FREQ / NMAX_FREQ` | integer, optional | `0` | *number of frequencies*. Range: ≥ 0. Ignored with `PROCHE`, `SEPARE`, `AJUSTE` (catalog comment at `upstream/code_aster/Cata/Commands/calc_modes.py:232`): one mode is computed per `FREQ` value. |
| `SOLVEUR_MODAL` | factor keyword, optional, present by default | — | *eigensolver settings*. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE') and is_in("OPTION", ('PLUS_PETITE','PLUS_GRANDE','BANDE','CENTRE','TOUT'))`; or `equal_to("TYPE_RESU", 'DYNAMIQUE') and is_in("OPTION", ('SEPARE','AJUSTE','PROCHE'))`; or `equal_to("TYPE_RESU", 'MODE_FLAMB') and is_in("OPTION", ('PLUS_PETITE','BANDE','CENTRE','TOUT'))`; or `equal_to("TYPE_RESU", 'MODE_FLAMB') and is_in("OPTION", ('SEPARE','AJUSTE','PROCHE'))`; or `equal_to("TYPE_RESU", 'GENERAL') and is_in("OPTION", ('PLUS_PETITE','BANDE','CENTRE','TOUT'))`; or `equal_to("TYPE_RESU", 'GENERAL') and is_in("OPTION", ('SEPARE','AJUSTE','PROCHE'))`. The eigensolver and its settings, for the subspace options (`PLUS_PETITE`, `PLUS_GRANDE`, `BANDE`, `CENTRE`, `TOUT`); for `PROCHE`, `SEPARE`, `AJUSTE` it holds the inverse-iteration settings instead. Defaults are fine for Tier 2; the fixture log prints them (`tests/fixtures/modal/output/run.mess:348`). |
| `SOLVEUR_MODAL / METHODE` | text, optional | `'SORENSEN'` | *method*. One of `'TRI_DIAG'`, `'JACOBI'`, `'SORENSEN'`, `'QZ'`. `'SORENSEN'` (default): implicitly restarted Arnoldi (ARPACK), robust for a few modes of a large model (fixture log: «Méthode de Sorensen (code ARPACK)», `tests/fixtures/modal/output/run.mess:380`). `'TRI_DIAG'`: Lanczos; `'JACOBI'`: Bathe–Wilson subspace iteration; `'QZ'`: dense QZ algorithm that computes every mode, for small models only (`upstream/astest/sdld102a.comm:1081`–`:1089` runs all four). |
| `SOLVEUR_MODAL / PREC_ORTHO` | real, optional | `1e-12` | Range: ≥ 0.0. Only when `equal_to("METHODE", 'TRI_DIAG')`. Lanczos (`TRI_DIAG`): orthogonality tolerance of the Lanczos vectors (`upstream/bibfor/algeline/vpinis.F90:202`). Leave the default. |
| `SOLVEUR_MODAL / NMAX_ITER_ORTHO` | integer, optional | `5` | Range: ≥ 0. Only when `equal_to("METHODE", 'TRI_DIAG')`. Lanczos: maximum re-orthogonalization passes. Leave the default. |
| `SOLVEUR_MODAL / PREC_LANCZOS` | real, optional | `1e-08` | Range: ≥ 0.0. Only when `equal_to("METHODE", 'TRI_DIAG')`. Lanczos: tolerance of the Lanczos process. Leave the default. |
| `SOLVEUR_MODAL / NMAX_ITER_QR` | integer, optional | `30` | Range: ≥ 0. Only when `equal_to("METHODE", 'TRI_DIAG')`. Lanczos: maximum iterations of the QR step on the tridiagonal matrix. Leave the default. |
| `SOLVEUR_MODAL / MODE_RIGIDE` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Only when `equal_to("METHODE", 'TRI_DIAG')`. Lanczos only: `'OUI'` finds the rigid-body modes of a free structure first, by an algebraic method, and Lanczos then computes the others; they are returned only if they are among the modes asked for. Without it the rigid-body eigenvalues come out near zero, not exactly zero (U4.52.02 §3.7; `upstream/code_aster/MacroCommands/Modal/calc_modes_simult.py:140`). |
| `SOLVEUR_MODAL / PREC_BATHE` | real, optional | `1e-10` | Range: ≥ 0.0. Only when `equal_to("METHODE", 'JACOBI')`. Subspace iteration (`JACOBI`): convergence tolerance. Leave the default. |
| `SOLVEUR_MODAL / NMAX_ITER_BATHE` | integer, optional | `40` | Range: ≥ 0. Only when `equal_to("METHODE", 'JACOBI')`. Subspace iteration: maximum iterations. |
| `SOLVEUR_MODAL / PREC_JACOBI` | real, optional | `0.01` | Range: ≥ 0.0. Only when `equal_to("METHODE", 'JACOBI')`. Subspace iteration: tolerance of the inner Jacobi diagonalization. |
| `SOLVEUR_MODAL / NMAX_ITER_JACOBI` | integer, optional | `12` | Range: ≥ 0. Only when `equal_to("METHODE", 'JACOBI')`. Subspace iteration: maximum Jacobi sweeps. |
| `SOLVEUR_MODAL / PREC_SOREN` | real, optional | `0.0` | Range: ≥ 0.0. Only when `equal_to("METHODE", 'SORENSEN')`. Sorensen: convergence tolerance passed to ARPACK; `0.0` (default) means the machine precision, about 2.22e-16 in double precision (U4.52.02 §3.7). |
| `SOLVEUR_MODAL / NMAX_ITER_SOREN` | integer, optional | `20` | Range: ≥ 1. Only when `equal_to("METHODE", 'SORENSEN')`. Sorensen: maximum restarts. The fixture needed 4 (`tests/fixtures/modal/output/run.mess:385`). |
| `SOLVEUR_MODAL / PARA_ORTHO_SOREN` | real, optional | `0.717` | Only when `equal_to("METHODE", 'SORENSEN')`. Sorensen: re-orthogonalization parameter (Kahan–Parlett criterion). Leave the default. |
| `SOLVEUR_MODAL / TYPE_QZ` | text, optional | `'QZ_SIMPLE'` | One of `'QZ_QR'`, `'QZ_SIMPLE'`, `'QZ_EQUI'`. Only when `equal_to("METHODE", 'QZ')`. QZ: variant of the dense algorithm (`'QZ_SIMPLE'`, `'QZ_QR'`, `'QZ_EQUI'`). Leave the default. |
| `SOLVEUR_MODAL / APPROCHE` | text, optional | `'REEL'` | Choice of the pseudo scalar product for solving the quadratic problem. One of `'REEL'`, `'IMAG'`, `'COMPLEXE'`. Quadratic problem only (`MATR_AMOR` given): how it is reduced to a linear one (real, imaginary or complex scalar product). Ignored without damping. |
| `SOLVEUR_MODAL / DIM_SOUS_ESPACE` | integer, optional | — | *subspace size*. Size of the projection subspace. By default the solver chooses it: twice the number of modes for Sorensen and Jacobi, four times for Lanczos (`ALGELINE5_77`; fixture log: "on la prend égale à : 12" for 6 modes, `tests/fixtures/modal/output/run.mess:377`). Give it, or `COEF_DIM_ESPACE`, only when the error norm is poor (`ALGELINE5_77` advice). |
| `SOLVEUR_MODAL / COEF_DIM_ESPACE` | integer, optional | — | Subspace size as a multiple of the number of modes, instead of `DIM_SOUS_ESPACE` (exclusive, catalog rule). |
| `SOLVEUR_MODAL / NMAX_ITER_SEPARE` | integer, optional | `30` | Range: ≥ 1. Inverse iteration (`SEPARE`, `AJUSTE`): maximum iterations of the separation (bisection) step. |
| `SOLVEUR_MODAL / PREC_SEPARE` | real, optional | `0.0001` | Range: ≥ 1e-70. Inverse iteration: tolerance of the separation step. |
| `SOLVEUR_MODAL / NMAX_ITER_AJUSTE` | integer, optional | `15` | Range: ≥ 1. Inverse iteration (`AJUSTE`): maximum iterations of the adjustment (secant) step. |
| `SOLVEUR_MODAL / PREC_AJUSTE` | real, optional | `0.0001` | Range: ≥ 1e-70. Inverse iteration: tolerance of the adjustment step. |
| `SOLVEUR_MODAL / OPTION_INV` | text, optional | `'DIRECT'` | One of `'DIRECT'`, `'RAYLEIGH'`. Inverse iteration: `'DIRECT'` (fixed shift) or `'RAYLEIGH'` (accelerated by the Rayleigh quotient; generalized problems only). For quadratic problems `'DIRECT'` is Jennings' variant (U4.52.02 §3.7.2.3). |
| `SOLVEUR_MODAL / PREC_INV` | real, optional | `1e-05` | Convergence tolerance. Range: ≥ 1e-70. Inverse iteration: convergence tolerance of each mode. |
| `SOLVEUR_MODAL / NMAX_ITER_INV` | integer, optional | `30` | Range: ≥ 1. Inverse iteration: maximum iterations per mode. |
| `SOLVEUR` | factor keyword, optional, present by default | — | *linear solver*. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE') and equal_to("OPTION", 'PROCHE')`; or `equal_to("TYPE_RESU", 'DYNAMIQUE') and is_in("OPTION", ('SEPARE','AJUSTE')) and not exists("MATR_AMOR")`; or `equal_to("TYPE_RESU", 'DYNAMIQUE') and is_in("OPTION", ('SEPARE','AJUSTE')) and exists("MATR_AMOR")`; or `equal_to("TYPE_RESU", 'DYNAMIQUE') and is_in("OPTION", ('PLUS_PETITE','PLUS_GRANDE','BANDE','CENTRE','TOUT'))`; or `equal_to("TYPE_RESU", 'MODE_FLAMB') and is_in("OPTION", ('SEPARE','AJUSTE', 'PROCHE'))`; or `equal_to("TYPE_RESU", 'MODE_FLAMB') and is_in("OPTION", ('PLUS_PETITE','BANDE','CENTRE', 'TOUT'))`; or `equal_to("TYPE_RESU", 'GENERAL') and is_in("OPTION", ('SEPARE','AJUSTE', 'PROCHE'))`; or `equal_to("TYPE_RESU", 'GENERAL') and is_in("OPTION", ('PLUS_PETITE','BANDE','CENTRE', 'TOUT'))`. The linear solver used to factorize the shifted matrix K − σM (once per shift, and again for the Sturm check). Defaults to MUMPS (fixture log, `tests/fixtures/modal/output/run.mess:335`). As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). Differences from `MECA_STATIQUE`: only `MULT_FRONT`, `LDLT` and `MUMPS` are offered, and `ACCELERATION` defaults to `'FR'`. |
| `SOLVEUR / RENUM` | text, optional | `'MDA'` | *renumbering*. One of `'MD'`, `'MDA'`. Only when `equal_to("METHODE", 'MULT_FRONT')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / NPREC` | integer, optional | `8` | *singularity threshold (digits)*. Only when `equal_to("METHODE", 'MULT_FRONT')`; or `equal_to("METHODE", 'LDLT')`; or `equal_to("METHODE", 'MUMPS')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). A loss of more than `NPREC` digits in the factorization of a shifted matrix makes the solver move the shift (`CALC_FREQ/NMAX_ITER_SHIFT`). |
| `SOLVEUR / RENUM` | text, optional | `'RCMK'` | *renumbering*. One of `'RCMK'`. Only when `equal_to("METHODE", 'LDLT')`; or `equal_to("METHODE", 'GCPC') and equal_to("PRE_COND", 'LDLT_INC')`; or `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'LDLT_INC')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / RENUM` | text, optional | `'AUTO'` | *renumbering*. One of `'AMD'`, `'AMF'`, `'PORD'`, `'METIS'`, `'QAMD'`, `'SCOTCH'`, `'AUTO'`, `'PARMETIS'`, `'PTSCOTCH'`. Only when `equal_to("METHODE", 'MUMPS')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / ELIM_LAGR` | text, optional | `'LAGR2'` | *Lagrange multiplier elimination*. One of `'NON'`, `'LAGR2'`. Only when `equal_to("METHODE", 'MUMPS')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / TYPE_RESOL` | text, optional | `'AUTO'` | One of `'NONSYM'`, `'SYMGEN'`, `'SYMDEF'`, `'AUTO'`. Only when `equal_to("METHODE", 'MUMPS')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / ACCELERATION` | text, optional | `'FR'` | One of `'AUTO'`, `'FR'`, `'FR+'`, `'FR++'`, `'LR'`, `'LR+'`, `'LR++'`. Only when `equal_to("METHODE", 'MUMPS')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). Default `'FR'` (full rank) here. |
| `SOLVEUR / LOW_RANK_SEUIL` | real, optional | `0.0` | Only when `equal_to("METHODE", 'MUMPS')`; or `equal_to("METHODE", 'GCPC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / PRETRAITEMENTS` | text, optional | `'AUTO'` | One of `'SANS'`, `'AUTO'`. Only when `equal_to("METHODE", 'MUMPS')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / POSTTRAITEMENTS` | text, optional | `'AUTO'` | One of `'SANS'`, `'AUTO'`, `'FORCE'`, `'MINI'`. Only when `equal_to("METHODE", 'MUMPS')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / PCENT_PIVOT` | integer, optional | `35` | *pivoting memory margin (%)*. Range: ≥ 1. Only when `equal_to("METHODE", 'MUMPS')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / NB_RHS` | integer, optional | `1` | Range: ≥ 1, ≤ 32. Only when `equal_to("METHODE", 'MUMPS')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / RESI_RELA` | real, optional | `-1.0` | *relative residual tolerance*. Only when `equal_to("METHODE", 'MUMPS')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). Default `-1.0` here: MUMPS does not check the residual of each solve. |
| `SOLVEUR / GESTION_MEMOIRE` | text, optional | `'AUTO'` | One of `'IN_CORE'`, `'OUT_OF_CORE'`, `'AUTO'`, `'EVAL'`. Only when `equal_to("METHODE", 'MUMPS')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / NIVE_REMPLISSAGE` | integer, optional | `0` | Only when `equal_to("METHODE", 'GCPC') and equal_to("PRE_COND", 'LDLT_INC')`; or `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'LDLT_INC')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / RENUM` | text, optional | `'PARMETIS'` | *renumbering*. One of `'SANS'`, `'METIS'`, `'PARMETIS'`. Only when `equal_to("METHODE", 'GCPC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / REAC_PRECOND` | integer, optional | `30` | Only when `equal_to("METHODE", 'GCPC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / PCENT_PIVOT` | integer, optional | `20` | *pivoting memory margin (%)*. Range: ≥ 1. Only when `equal_to("METHODE", 'GCPC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / GESTION_MEMOIRE` | text, optional | `'AUTO'` | One of `'IN_CORE'`, `'AUTO'`. Only when `equal_to("METHODE", 'GCPC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('LDLT_SP', 'LDLT_DP'))`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / PRE_COND` | text, optional | `'LDLT_INC'` | One of `'LDLT_INC'`, `'LDLT_SP'`, `'LDLT_DP'`. Only when `equal_to("METHODE", 'GCPC')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / RESI_RELA` | real, optional | `1e-06` | *relative residual tolerance*. Only when `equal_to("METHODE", 'GCPC')`; or `equal_to("METHODE", 'PETSC')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / NMAX_ITER` | integer, optional | `0` | Only when `equal_to("METHODE", 'GCPC')`; or `equal_to("METHODE", 'PETSC')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / REMPLISSAGE` | real, optional | `1.0` | Only when `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'LDLT_INC')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / RENUM` | text, optional | `'SANS'` | *renumbering*. One of `'SANS'`. Only when `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'ML')`; or `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'BOOMER')`; or `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'GAMG')`; or `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'HPDDM')`; or `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'BLOC_LAGR')`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('FIELDSPLIT'))`; or `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('UTILISATEUR'))`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / TYPE_RESOL` | text, optional | `'AUTO'` | One of `'AUTO'`, `'GENEO'`, `'HARMO'`. Only when `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'HPDDM')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / NB_MODE` | integer, optional | — | Range: ≥ 1. Only when `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'HPDDM')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / SEUIL` | real, optional | — | *threshold*. Range: ≥ 0.0. Only when `equal_to("METHODE", 'PETSC') and equal_to("PRE_COND", 'HPDDM')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / PARTITION_CMP` | integer, optional, list | — | Only when `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('FIELDSPLIT'))`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / NOM_CMP` | text, optional, list | — | *component name*. Only when `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('FIELDSPLIT'))`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / KSP_UTIL` | `not_checked`, optional | — | Only when `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('UTILISATEUR'))`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / RENUM` | text, optional | `'SANS'` | *renumbering*. One of `'SANS'`, `'RCMK'`. Only when `equal_to("METHODE", 'PETSC') and is_in("PRE_COND", ('JACOBI','SOR','SANS'))`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / ALGORITHME` | text, optional | `'FGMRES'` | One of `'CG'`, `'CR'`, `'GMRES'`, `'GCR'`, `'FGMRES'`, `'GMRES_LMP'`. Only when `equal_to("METHODE", 'PETSC')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / OPTION_PETSC` | text, optional | `''` | Only when `equal_to("METHODE", 'PETSC')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / PRE_COND` | text, optional | `'LDLT_SP'` | One of `'LDLT_INC'`, `'LDLT_SP'`, `'LDLT_DP'`, `'JACOBI'`, `'SOR'`, `'ML'`, `'BOOMER'`, `'GAMG'`, `'BLOC_LAGR'`, `'FIELDSPLIT'`, `'UTILISATEUR'`, `'HPDDM'`, … (13 values; see the .json). Only when `equal_to("METHODE", 'PETSC')`. As in [MECA_STATIQUE](MECA_STATIQUE.md) (same common catalog, `upstream/code_aster/Cata/Commons/c_solveur.py`). |
| `SOLVEUR / METHODE` | text, optional | `'MUMPS'` | *method*. One of `'MULT_FRONT'`, `'LDLT'`, `'MUMPS'`. The linear solver: `'MUMPS'` (default), `'MULT_FRONT'` or `'LDLT'` (`upstream/code_aster/Cata/Commons/c_solveur.py`). Keep MUMPS. |
| `SOLVEUR / METHODE` | text, optional | `'MULT_FRONT'` | *method*. One of `'MULT_FRONT'`, `'LDLT'`. With `SEPARE`/`AJUSTE` and a damping matrix: `'MULT_FRONT'` (default) or `'LDLT'` (`upstream/code_aster/Cata/Commons/c_solveur.py:196`). |
| `FILTRE_MODE` | factor keyword, optional | — | *mode filter*. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE') and is_type("MATR_RIGI")==matr_asse_depl_r`. Keep only the significant modes after the computation, with [EXTR_MODE](EXTR_MODE.md) (`upstream/code_aster/MacroCommands/Modal/calc_modes_post.py:46`): physical matrices only (`matr_asse_depl_r`). Use it to drop modes that move no mass before a spectral combination. |
| `FILTRE_MODE / CRIT_EXTR` | text, optional | `'MASS_EFFE_UN'` | *mode selection criterion*. One of `'MASS_EFFE_UN'`, `'MASS_GENE'`, `'INER_EFFE_UN'`. The criterion, as in `EXTR_MODE`: unit effective mass (default), generalized mass, or unit effective inertia. |
| `FILTRE_MODE / SEUIL` | real, optional | `0.001` | *threshold*. Threshold of the criterion (default 0.001 = 0.1 % of the mass in at least one direction) (`upstream/astest/fdlv112b.comm:152`). |
| `IMPRESSION` | factor keyword, optional | — | Only when `equal_to("TYPE_RESU", 'DYNAMIQUE') and is_type("MATR_RIGI")==matr_asse_depl_r`. Print the effective mass table of the modes kept (`EXTR_MODE` `IMPRESSION`) and, with `TOUT_PARA='OUI'`, every stored parameter of every mode (`IMPR_RESU FORMAT='RESULTAT'`) to the message file (`calc_modes_post.py:52`, `:59`). |
| `IMPRESSION / TOUT_PARA` | text, optional | `'OUI'` | One of `'OUI'`, `'NON'`. `'OUI'` (default): also print all the modal parameters (`calc_modes_post.py:60`). |
| `IMPRESSION / CUMUL` | text, optional | `'OUI'` | One of `'OUI'`, `'NON'`. `'OUI'` (default here): add the running totals of the criterion per direction, the check that enough mass is captured. |
| `IMPRESSION / CRIT_EXTR` | text, optional | `'MASS_EFFE_UN'` | *mode selection criterion*. One of `'MASS_EFFE_UN'`, `'MASS_GENE'`, `'INER_EFFE_UN'`. Which parameter the table shows; default unit effective mass. |
| `VERI_MODE` | factor keyword, optional, present by default | — | *mode checks*. Only when `equal_to("TYPE_RESU", 'DYNAMIQUE') and is_in("OPTION", ('PLUS_PETITE','PLUS_GRANDE','CENTRE','TOUT'))`; or `equal_to("TYPE_RESU", 'DYNAMIQUE') and equal_to("OPTION", 'BANDE')`; or `equal_to("TYPE_RESU", 'DYNAMIQUE') and is_in("OPTION", ('SEPARE','AJUSTE','PROCHE'))`; or `equal_to("TYPE_RESU", 'MODE_FLAMB') and is_in("OPTION", ('PLUS_PETITE','CENTRE','TOUT', 'BANDE'))`; or `equal_to("TYPE_RESU", 'MODE_FLAMB') and is_in("OPTION", ('SEPARE','AJUSTE','PROCHE'))`; or `equal_to("TYPE_RESU", 'GENERAL') and is_in("OPTION", ('PLUS_PETITE','CENTRE','TOUT', 'BANDE'))`; or `equal_to("TYPE_RESU", 'GENERAL') and is_in("OPTION", ('SEPARE','AJUSTE','PROCHE'))`. Checks run on the computed modes (`upstream/bibfor/algeline/vpcntl.F90`): each mode's error norm ‖Kφ − ω²Mφ‖ / ‖Kφ‖ against `SEUIL`, and a Sturm count, from a factorization, of the eigenvalues in the computed range, which must equal the number of modes found. The fixture passes both ("Dans l'intervalle ( 5.22086E+01 , 1.50077E+03 ) il y a bien 6 fréquence(s)", `tests/fixtures/modal/output/run.mess:424`). A failed check with `STOP_ERREUR='OUI'` stops the run (`ALGELINE2_74`, `upstream/bibfor/algeline/vppost.F90:245`). This occurrence: subspace options except `BANDE`. |
| `VERI_MODE / STOP_ERREUR` | text, optional | `'OUI'` | *stop on failed check*. One of `'OUI'`, `'NON'`. `'OUI'` (default): a failed check is an error (`ALGELINE2_74`, raised as a solver error, so `run_aster` ends `<S>`). `'NON'`: the run continues with warnings, as some upstream tests do (`upstream/astest/sdll05a.comm:120`). Keep `'OUI'`: a missed mode makes every later modal result wrong. |
| `VERI_MODE / SEUIL` | real, optional | `1e-06` | *threshold*. Limit accepted for the a posteriori error of the modes. Range: ≥ 0.0. Largest accepted error norm per mode (default 1e-6). The fixture's worst mode is 2.5e-8 (`tests/fixtures/modal/output/run.mess:405`). A mode above it gives `ALGELINE5_15` + `ALGELINE5_18`. |
| `VERI_MODE / PREC_SHIFT` | real, optional | `0.005` | Range: ≥ 0.0. Relative widening of the range used for the Sturm check, in ω² (default 0.5 %, about 0.25 % in frequency): the fixture's range 52.34–1497.03 Hz is checked as (52.2086, 1500.77) (`tests/fixtures/modal/output/run.mess:424`; `upstream/bibfor/algeline/vpinis.F90:236`). |
| `VERI_MODE / STURM` | text, optional | `'OUI'` | *Sturm check*. One of `'OUI'`, `'NON'`. `'OUI'` (default): do the Sturm count. A different count gives `ALGELINE5_24` ("in the interval ... there is theoretically N frequencies and one computed M") and `ALGELINE5_26` (multiple modes, high modal density) (`upstream/bibfor/algeline/vpcntl.F90:179`). |
| `VERI_MODE / STURM` | text, optional | `'GLOBAL'` | *Sturm check*. One of `'GLOBAL'`, `'LOCAL'`, `'OUI'`, `'NON'`. With `BANDE`: `'GLOBAL'` (default) counts over the whole band, `'LOCAL'` per sub-band; `'OUI'` is taken as a count, `'NON'` skips it (`upstream/code_aster/MacroCommands/Modal/calc_modes_simult.py:180`). |
| `VERI_MODE / SEUIL` | real, optional | `0.01` | *threshold*. Limit accepted for the a posteriori error of the modes. Range: ≥ 0.0. Largest accepted error norm with inverse iteration (default 0.01). |
| `VERI_MODE / STURM` | text, optional | `'NON'` | *Sturm check*. One of `'OUI'`, `'NON'`. With inverse iteration (`PROCHE`, `SEPARE`, `AJUSTE`): no count by default (`'NON'`), since only a few modes of the range are computed. |
| `MATR_RIGI` | `matr_asse_depl_r` or `matr_asse_gene_r` or `matr_asse_pres_r`, required | — | *stiffness matrix*. Only when `equal_to("TYPE_RESU", 'MODE_FLAMB')`. The assembled elastic stiffness matrix (buckling). |
| `MATR_RIGI_GEOM` | `matr_asse_depl_r` or `matr_asse_gene_r` or `matr_asse_pres_r`, required | — | Only when `equal_to("TYPE_RESU", 'MODE_FLAMB')`. Buckling: the assembled geometric stiffness of the prestress (`CALC_MATR_ELEM OPTION='RIGI_GEOM'` from a static stress field) (`upstream/astest/sdls504a.comm:158`). Tier 3. |
| `OPTION` | text, optional | `'PLUS_PETITE'` | *option*. Choice of the search range. One of `'PLUS_PETITE'`, `'BANDE'`, `'CENTRE'`, `'TOUT'`, `'SEPARE'`, `'AJUSTE'`, `'PROCHE'`. Only when `equal_to("TYPE_RESU", 'MODE_FLAMB')`; or `equal_to("TYPE_RESU", 'GENERAL')`. As for `DYNAMIQUE`, applied to critical load factors (`CALC_CHAR_CRIT`); `'PLUS_GRANDE'` is not offered. |
| `CALC_CHAR_CRIT` | factor keyword, optional, present by default | — | Search for all the eigenvalues. Only when `equal_to("TYPE_RESU", 'MODE_FLAMB') and equal_to("OPTION", 'TOUT')`; or `equal_to("TYPE_RESU", 'GENERAL') and equal_to("OPTION", 'TOUT')`. Buckling: what to search for, as `CALC_FREQ` does for vibration but on critical load factors. Settings below, shared by every `OPTION`. Tier 3. |
| `CALC_CHAR_CRIT / NMAX_CHAR_CRIT` | integer, optional | `10` | Range: ≥ 0. Buckling: number of critical load factors wanted (default 10). |
| `CALC_CHAR_CRIT / NMAX_ITER_SHIFT` | integer, optional | `3` | Range: ≥ 0. Buckling: as `CALC_FREQ / NMAX_ITER_SHIFT`. |
| `CALC_CHAR_CRIT / PREC_SHIFT` | real, optional | `0.05` | Range: ≥ 0.0. Buckling: as `CALC_FREQ / PREC_SHIFT`. |
| `CALC_CHAR_CRIT / SEUIL_CHAR_CRIT` | real, optional | `0.01` | Range: ≥ 0.0. Buckling: as `CALC_FREQ / SEUIL_FREQ`, on load factors (not converted, `upstream/bibfor/algeline/vpinis.F90:189`). |
| `CALC_CHAR_CRIT` | factor keyword, optional, present by default | — | Search for the lowest eigenvalues. Only when `equal_to("TYPE_RESU", 'MODE_FLAMB') and equal_to("OPTION", 'PLUS_PETITE')`; or `equal_to("TYPE_RESU", 'GENERAL') and equal_to("OPTION", 'PLUS_PETITE')`. Buckling with `PLUS_PETITE`: `NMAX_CHAR_CRIT` and the shift settings. |
| `CALC_CHAR_CRIT` | factor keyword, optional, present by default | — | Only when `equal_to("TYPE_RESU", 'MODE_FLAMB') and equal_to("OPTION", 'CENTRE')`; or `equal_to("TYPE_RESU", 'MODE_FLAMB') and is_in("OPTION", ('SEPARE','AJUSTE','PROCHE'))`; or `equal_to("TYPE_RESU", 'GENERAL') and equal_to("OPTION", 'CENTRE')`; or `equal_to("TYPE_RESU", 'GENERAL') and is_in("OPTION", ('SEPARE','AJUSTE','PROCHE'))`. Buckling with `CENTRE`, `PROCHE`, `SEPARE`, `AJUSTE`: the central or estimated values `CHAR_CRIT`. |
| `CALC_CHAR_CRIT / CHAR_CRIT` | real, required | — | Critical load around which the critical loads are sought. Buckling with `CENTRE`: the central load factor. |
| `CALC_CHAR_CRIT` | factor keyword, optional, present by default | — | Search for the natural frequencies in a given band. Only when `equal_to("TYPE_RESU", 'MODE_FLAMB') and equal_to("OPTION", 'BANDE')`; or `equal_to("TYPE_RESU", 'GENERAL') and equal_to("OPTION", 'BANDE')`. Buckling with `BANDE`: the band limits `CHAR_CRIT`. |
| `CALC_CHAR_CRIT / CHAR_CRIT` | real, required, list of up to 2, at least 2 | — | The two critical loads that bound the search band. Buckling with `BANDE`: the two limits of the band (`upstream/astest/sdls504a.comm:163`). Give the lower then the upper limit; values may be negative (U4.52.02 §3.9.1). The Sturm messages print the band in the solver's own sign, as (−max, −min) (`upstream/bibfor/algeline/vpcntl.F90:188`). |
| `CALC_CHAR_CRIT / TABLE_CHAR_CRIT` | `table_sdaster`, optional | — | Buckling: an `INFO_MODE` table with the count per band, as `TABLE_FREQ` (`upstream/astest/sdls504a.comm:163`). |
| `CALC_CHAR_CRIT / CHAR_CRIT` | real, required, list | — | Buckling with `PROCHE`, `SEPARE`, `AJUSTE`: estimates, one per mode. |
| `CALC_CHAR_CRIT / NMAX_CHAR_CRIT` | integer, optional | `0` | Range: ≥ 0. Ignored with `PROCHE`, `SEPARE`, `AJUSTE`, as for `NMAX_FREQ`. |
| `MATR_A` | `matr_asse_depl_r` or `matr_asse_gene_r` or `matr_asse_pres_r`, required | — | Only when `equal_to("TYPE_RESU", 'GENERAL')`. `TYPE_RESU='GENERAL'`: the matrix A of A x = λ B x. |
| `MATR_B` | `matr_asse_depl_r` or `matr_asse_gene_r` or `matr_asse_pres_r`, required | — | Only when `equal_to("TYPE_RESU", 'GENERAL')`. `TYPE_RESU='GENERAL'`: the matrix B. |
| `STOP_BANDE_VIDE` | text, optional | `'OUI'` | *stop on empty band*. One of `'OUI'`, `'NON'`. `'OUI'` (default): an empty band stops the run (`MODAL_1`, `upstream/bibfor/algeline/vpini1.F90:293`; `MODAL_6` for one empty sub-band). `'NON'`: an empty band gives an empty result and the run continues (`upstream/code_aster/MacroCommands/Modal/calc_modes_multi_bandes.py:347`). |
| `AMELIORATION` | text, optional | `'NON'` | *mode refinement*. One of `'OUI'`, `'NON'`. `'OUI'`: after the main computation, refine every mode by inverse iteration (`OPTION='PROCHE'` from the frequencies just found) (`upstream/code_aster/MacroCommands/Modal/calc_modes_ops.py:98`); the checks of the first pass are silenced and run on the second. Not compatible with `PROCHE`, `SEPARE`, `AJUSTE` (`ALGELINE5_21`). Use it when the error norms are close to `SEUIL`. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `1` (default) prints the problem size, the solver statistics, the frequency table with error norms and the Sturm check, as in the fixture log (`tests/fixtures/modal/output/run.mess:360`–`:425`). `2` prints more. |
| `TITRE` | text, optional | — | *title*. A title stored with the result. |

1 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- `SOLVEUR_MODAL`: at most one of `DIM_SOUS_ESPACE`, `COEF_DIM_ESPACE` may be given (`EXCLUS`).
- when `equal_to("PRE_COND", 'HPDDM')`: exactly one of `SEUIL`, `NB_MODE` must be given; if none is given, `NB_MODE=30` is assumed (`UN_PARMI`).

Most keywords depend on `TYPE_RESU` and `OPTION` (catalog blocks): `CALC_FREQ`, `SOLVEUR_MODAL`,
`SOLVEUR` and `VERI_MODE` appear several times above, once per block, with different defaults.

## Patterns

### The lowest modes (the modal fixture)

Written by the English builder (`Builder.modal`). Source:
`tests/fixtures/modal/input/run.comm:43`.

```python
MODES = CALC_MODES(MATR_RIGI=RIGI, MATR_MASS=MASS, OPTION="PLUS_PETITE", CALC_FREQ=_F(NMAX_FREQ=6))
```

The log (`tests/fixtures/modal/output/run.mess:403`) prints each frequency with its error norm,
then the Sturm check:

```text
numéro    fréquence (HZ)     norme d'erreur

1       5.23396E+01        2.53716E-08
...
6       1.49703E+03        1.34435E-10
...
Dans l'intervalle ( 5.22086E+01 , 1.50077E+03 ) il y a bien 6 fréquence(s).
```

### Lowest modes, normalized in the same call

Source: `upstream/astest/sdll05a.comm:114`. `STOP_ERREUR='NON'` is a test-case choice; keep the
default in production.

```python
MODES = CALC_MODES(
    MATR_MASS=MAT_M,
    MATR_RIGI=MAT_K,
    OPTION="PLUS_PETITE",
    CALC_FREQ=_F(NMAX_FREQ=2),
    NORM_MODE=_F(NORME="TRAN_ROTA"),
    VERI_MODE=_F(STOP_ERREUR="NON"),
)
```

### Every mode in a band

Source: `upstream/astest/forma12a.comm:60`.

```python
MODES = CALC_MODES(
    MATR_RIGI=RIGIDITE, OPTION="BANDE", CALC_FREQ=_F(FREQ=(0, 50.0)), MATR_MASS=MASSE
)
```

### Several sub-bands, filtered by effective mass

Source: `upstream/astest/fdlv112b.comm:146`.

```python
mode_rig = CALC_MODES(
    MATR_RIGI=MATRIGI,
    VERI_MODE=_F(STOP_ERREUR="NON"),
    NORM_MODE=_F(INFO=1, NORME="TRAN_ROTA"),
    OPTION="BANDE",
    CALC_FREQ=_F(FREQ=(0.1, 10.0, 20.0, 30.0, 40.0)),
    FILTRE_MODE=_F(SEUIL=0.0003),
    MATR_MASS=MATMASS,
)
```

### Modes near a frequency

Source: `upstream/astest/sdld106a.comm:70`.

```python
MODES = CALC_MODES(
    MATR_RIGI=MATRRIGI, OPTION="CENTRE", CALC_FREQ=_F(NMAX_FREQ=1, FREQ=(f1e,)), MATR_MASS=MATRMASS
)
```

### Another eigensolver

Source: `upstream/astest/sdld102a.comm:1081` (the test repeats the call with `JACOBI` and `QZ`).

```python
    MATR_RIGI=K_ASSE, OPTION="PLUS_GRANDE", MATR_MASS=M_ASSE, SOLVEUR_MODAL=_F(METHODE="TRI_DIAG")
```

## What the solver does

`calc_modes_ops` (`upstream/code_aster/MacroCommands/Modal/calc_modes_ops.py`) picks the path
from `OPTION`: several bands go to `calc_modes_multi_bandes` (`:83`), the subspace options to
`MODE_ITER_SIMULT` (`:90`, op0045), the inverse-iteration options to `MODE_ITER_INV` (`:94`,
op0044). `MODE_ITER_SIMULT` (`upstream/bibfor/op/op0045.F90`):

1. reads the settings (`vpinis`) and factorizes K − σM at the shift σ chosen from `OPTION`
   (0 for `PLUS_PETITE`; fixture log: "La valeur de décalage en fréquence est : 0.00000E+00"),
   moving σ if the factorization fails (`vpfopr`, `CALC_FREQ/NMAX_ITER_SHIFT`, `PREC_SHIFT`);
2. runs the eigensolver (`vpcals` Sorensen, `vpcalt` Lanczos, `vpcalj` Jacobi, `vpcalq` QZ,
   `op0045.F90:135`–`:152`);
3. normalizes each mode to a unit largest component and computes the modal parameters: generalized
   mass and stiffness, participation factors, effective masses, unit effective masses
   (`vppara.F90`);
4. checks the error norms and the Sturm count (`vpcntl.F90`) and stops on failure with
   `STOP_ERREUR='OUI'` (`vppost.F90:244`);
5. stores the modes with their parameters (`vpstor.F90`).

Then the macro runs `NORM_MODE` and `EXTR_MODE` if `NORM_MODE`, `FILTRE_MODE` or `IMPRESSION`
were given (`calc_modes_post.py`), and stores the model, numbering, matrices, `CHAM_MATER` and
`CARA_ELEM` in the result (`calc_modes_ops.py:149`–`:186`).

Units: frequencies are in Hz when the model units are consistent (the fixture: mm, N, tonne,
s). Effective masses are in the model's mass unit (tonne in mm/N/MPa models); unit effective
masses are fractions of the total.

## Pitfalls

- **Supports are in the matrices, not in `CALC_MODES`.** Boundary conditions enter through the
  `CHARGE` of `CALC_MATR_ELEM`/`ASSEMBLAGE` or the `CHAR_CINE` of `ASSE_MATRICE`. A model
  without supports gives rigid-body modes near 0 Hz first; these count as modes in
  `NMAX_FREQ`.
- **Check the effective mass sum.** The six lowest modes of the fixture capture 61 + 19 + 6.5 %
  of the mass in Z and 61 + 19 % in Y, and 0 % in X (the axial mode is higher,
  `tests/fixtures/modal/output/tables/modal_parameters.csv`). Codes often ask for 90 %; compute
  more modes, or a band up to the frequency of interest, until the cumulative unit effective
  mass is enough (`IMPRESSION=_F(CUMUL='OUI')`).
- **A failed check is a solver error.** `ALGELINE2_74` stops the run as a solver exception: the
  `.mess` shows `<EXCEPTION>` and `run_aster` ends `<S>_ERROR`. The usual causes are repeated
  frequencies of a symmetric structure and a subspace too small (`ALGELINE5_26`,
  `ALGELINE5_77`); try `AMELIORATION='OUI'`, a larger `DIM_SOUS_ESPACE`, or a `BANDE`
  computation. Setting `STOP_ERREUR='NON'` hides the problem.
- **Mode shapes are not mass-normalized by default.** See [NORM_MODE](NORM_MODE.md); the
  frequencies and effective masses do not depend on it.
- **`CHAM_MATER` is optional but useful.** Without it the result carries no material field;
  post-processing the modes (`CALC_CHAMP` stresses) then needs `CHAM_MATER` again.
  TODO(verify) whether `CALC_CHAMP` finds the material from the matrices alone.
- **Empty band is fatal.** `OPTION='BANDE'` with no mode in the band stops the run (`MODAL_1`)
  unless `STOP_BANDE_VIDE='NON'`.

## See also

- French reference: U4.52.02 (from en/doc-ids.yaml, status: verified; French text:
  `en/docs/_src/U4.52.02.fr.md`; translation: `en/docs/U4.52.02.md`)
- Catalog: `en/commands/CALC_MODES.json` (generated from `upstream/code_aster/Cata/Commands/calc_modes.py:70`)
- Implementation: `upstream/code_aster/MacroCommands/Modal/calc_modes_ops.py` and its
  `calc_modes_*.py` helpers; `upstream/bibfor/op/op0045.F90` (`MODE_ITER_SIMULT`),
  `upstream/bibfor/op/op0044.F90` (`MODE_ITER_INV`); `upstream/bibfor/algeline/vp*.F90`
- Before: [ASSEMBLAGE](ASSEMBLAGE.md), or [CALC_MATR_ELEM](CALC_MATR_ELEM.md) +
  [NUME_DDL](NUME_DDL.md) + [ASSE_MATRICE](ASSE_MATRICE.md)
- Next steps: [NORM_MODE](NORM_MODE.md), [EXTR_MODE](EXTR_MODE.md), `RECU_TABLE` (modal
  parameters table, read by the report), [IMPR_RESU](IMPR_RESU.md) (mode shapes to MED),
  [TEST_RESU](TEST_RESU.md) (`PARA='FREQ'`)
- Guide: `en/guide/fields.md` (the `DEPL` field of a modal result)
- Example: `tests/fixtures/modal/input/run.comm` (line 43)
- Example: `upstream/astest/sdll05a.comm` (line 114)
- Example: `upstream/astest/forma12a.comm` (line 60)
- Example: `upstream/astest/fdlv112b.comm` (line 146)
