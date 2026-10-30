---
command: DEBUT
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/debut.py:45
doc_fr: U4.11.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3d)
examples: [asrun01b, supv003a, adlv301a, comp012d, adlv100a, sslv155c, mumps05a]
---

# DEBUT — start a study

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, upstream test cases and the committed fixture
> runs. Every behavior claim cites its source. Not reviewed by an engineer.

`DEBUT` is the first command of every command file. It starts the memory manager and the
databases, and sets how the run reacts to errors and warnings, which warnings to ignore, the
time and memory reserves, and the message language. A study that continues a previous run uses
`POURSUITE` instead, which takes the same keywords (it has no catalog of its own) and reloads
the saved objects. In practice most studies call `DEBUT()` with no keyword or with `ERREUR` and
`IGNORE_ALARM` only; the other keywords are tuning or developer settings. `FIN` closes the
study.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Initialisation des ressources, démarrage ou reprise d'un calcul.» |
| Kind | `MACRO` (operator 0; Python: `upstream/code_aster/CodeCommands/debut.py`) |
| Result | none |
| Can reuse its input (`reuse=`) | not applicable |
| French reference | U4.11.01 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `CODE`, `ERREUR`, `DEBUG`, `IGNORE_ALARM` |

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `IMPR_MACRO` | text, optional | `'NON'` | Prints the sub-commands that macro-commands generate in the message file (.mess). One of `'OUI'`, `'NON'`. `'OUI'` echoes in the message file the commands that macro-commands (for example `IMPR_TABLE`, `MACR_*`) run internally (`upstream/code_aster/CodeCommands/debut.py:226`). Use it to see what a macro did. |
| `BASE` | factor keyword, optional, up to 2 | — | Parameters of the JEVEUX databases. Size parameters of the global and volatile JEVEUX databases (read by `upstream/bibfor/supervis/ibbase.F90:114`). Developer setting; leave the default. |
| `BASE / FICHIER` | text, required | — | Database name. One of `'GLOBALE'`, `'VOLATILE'`. Which database the occurrence sets: `'GLOBALE'` (saved, used by `POURSUITE`) or `'VOLATILE'` (scratch). |
| `BASE / TITRE` | text, optional | — | *title*. Title stored in the database. |
| `BASE / CAS` | text, optional | — | Name of the study stored in the database. TODO(verify) against U4.11.01. |
| `BASE / NMAX_ENRE` | integer, optional | — | Maximum number of records. Developer setting; leave the default. |
| `BASE / LONG_ENRE` | integer, optional | — | Record length. Developer setting; leave the default. |
| `BASE / LONG_REPE` | integer, optional | — | Directory length. Developer setting; leave the default. |
| `CATALOGUE` | factor keyword, optional, up to 10 | — | Load element or command catalogs from files instead of the installed ones (`upstream/bibfor/supervis/ibcata.F90:73`). Developer setting; leave the default. |
| `CATALOGUE / FICHIER` | text, required | — | Which catalog the file replaces. |
| `CATALOGUE / UNITE` | `UnitDefault`, optional | — | *logical unit*. Logical unit of the catalog file. |
| `CODE` | text, optional | — | *test-case mode*. Parameter reserved for test cases (errors, coverage file, ...). One of `'OUI'`, `'NON'`. `'OUI'`: test-case mode. A fatal error aborts the process instead of raising a Python exception, and command coverage is recorded (`upstream/code_aster/CodeCommands/debut.py:182`–`:186`). Upstream test cases and our fixtures use it (`tests/fixtures/modal/input/run.comm:14`). Studies normally omit it. It also changes the default `RESERVE_CPU` to 10 s. |
| `ERREUR` | factor keyword, optional | — | *error handling*. Behavior on error. How errors and warnings stop the run. |
| `ERREUR / ERREUR_F` | text, optional | — | One of `'ABORT'`, `'EXCEPTION'`. What a fatal error (`<F>`) does: `'ABORT'` stops the process; `'EXCEPTION'` raises a Python exception that the command file can catch with `try`/`except` (`upstream/code_aster/CodeCommands/debut.py:191`). Default: `'ABORT'` with `CODE='OUI'`, `'EXCEPTION'` otherwise (`:179`–`:186`). TODO(verify) whether the global database is saved after an uncaught `'EXCEPTION'`, against U4.11.01. |
| `ERREUR / ALARME` | text, optional | — | One of `'ALARME'`, `'EXCEPTION'`. `'EXCEPTION'`: every warning (`<A>`) becomes a fatal error (`upstream/code_aster/CodeCommands/debut.py:197`; `upstream/code_aster/Messages/Utmess.py:181`). Upstream test cases and our solid and modal fixtures use it, so that a new warning breaks the test. `'ALARME'`: warnings stay warnings. |
| `DEBUG` | factor keyword, optional, present by default | — | *debug settings*. Debugging option reserved for developers. Developer checks. |
| `DEBUG / JXVERI` | text, optional | `'NON'` | Checks the integrity of the memory segmentation. One of `'OUI'`, `'NON'`. `'OUI'` checks the memory manager's integrity after each command (`upstream/code_aster/CodeCommands/debut.py:205`). Slow; for developers. |
| `DEBUG / SDVERI` | text, optional | `'NON'` | Checks that the data structures produced by the commands are valid. One of `'OUI'`, `'NON'`. `'OUI'` checks every data structure produced by each command (`upstream/code_aster/CodeCommands/debut.py:209`). Common in upstream test cases (`upstream/astest/adlv301a.comm:22`); slows the run. |
| `DEBUG / JEVEUX` | text, optional | `'NON'` | Forces offloading to disk. One of `'OUI'`, `'NON'`. `'OUI'` forces the memory manager to write objects to disk, to expose memory errors (`upstream/code_aster/CodeCommands/debut.py:213`). For developers. |
| `DEBUG / ENVIMA` | text, optional | — | Prints the values defined in ENVIMA. One of `'TEST'`. Developer setting; leave the default. |
| `DEBUG / VERI_BASE` | text, optional | — | Runs a verification test on the databases. One of `'GLOBALE'`, `'VOLATILE'`. Developer setting; leave the default. |
| `DEBUG / VERI_BASE_NB` | integer, optional | `125` | Percentage of the database size to write. Developer setting; leave the default. |
| `MESURE_TEMPS` | factor keyword, optional, present by default | — | Displays the time taken by the main calculation steps. Timing printout in the message file. |
| `MESURE_TEMPS / NIVE_DETAIL` | integer, optional | `1` | Level of detail of the printed output. One of `0`, `1`, `2`, `3`. `0` nothing; `1` main timings at the end of each command; `2` main and secondary timings; `3` also at each time step (catalog comment, `upstream/code_aster/Cata/Commands/debut.py:143`). |
| `MESURE_TEMPS / MOYENNE` | text, optional | `'NON'` | Displays means and standard deviations in parallel runs. One of `'OUI'`, `'NON'`. Parallel runs: also print means and standard deviations over processes (`upstream/astest/mumps05a.comm:59`). |
| `MEMOIRE` | factor keyword, optional, present by default | — | Memory management mode. Memory layout settings (read by `upstream/bibfor/supervis/ibdbgs.F90:83`). |
| `MEMOIRE / TAILLE_BLOC` | real, optional | `800.0` | Block size used to store assembled matrices out of core. TODO(verify) the unit against U4.11.01. Rarely changed (`upstream/astest/ssnv503b.comm:26`). |
| `MEMOIRE / TAILLE_GROUP_ELEM` | integer, optional | `1000` | Maximum number of elements in one group of elements of the same type that are computed together. TODO(verify) against U4.11.01. |
| `RESERVE_CPU` | factor keyword, optional, present by default | — | Time reserved to finish a run. Part of the time limit kept back so that the run can stop cleanly (save the database, close files) before the batch system kills it. Default: 10 % of the limit, or 10 s in test mode (`upstream/bibfor/supervis/ibtcpu.F90:54`–`:60`). The reserve is printed (`SUPERVIS_64`). |
| `RESERVE_CPU / VALE` | integer, optional | — | *value(s)*. Range: ≥ 0. Reserve in seconds (`upstream/astest/adlv100a.comm:21`). More than the time limit stops the run (`SUPERVIS_31`). |
| `RESERVE_CPU / POURCENTAGE` | real, optional | — | Range: ≥ 0.0, ≤ 1.0. Reserve as a fraction of the time limit (0.1 = 10 %). |
| `RESERVE_MEMOIRE` | factor keyword, optional, present by default | — | Memory reserved for external libraries. Memory kept back from code_aster's own memory manager for external libraries (MUMPS, PETSc). Applied only when the memory limit exceeds 1024 MB: the limit is reduced by `VALE`, else by `POURCENTAGE` × limit, default 10 % (`upstream/code_aster/CodeCommands/debut.py:132`–`:135`). |
| `RESERVE_MEMOIRE / VALE` | integer, optional | — | *value(s)*. Range: ≥ 0. Reserve in MB (`upstream/astest/sslv155c.comm:20`). |
| `RESERVE_MEMOIRE / POURCENTAGE` | real, optional | — | Range: ≥ 0.0, ≤ 1.0. Reserve as a fraction of the memory limit. |
| `IGNORE_ALARM` | text, optional, list | — | *warnings to ignore*. Warnings that the user deliberately chooses to ignore. Message IDs of warnings to silence, for example `("MODELISA8_14",)` when the warning is understood and intended (`tests/fixtures/shell_static/input/run.comm:17`). They no longer print or count (`upstream/code_aster/Messages/Utmess.py:466`, `:554`). Does not work together with `ERREUR=_F(ALARME='EXCEPTION')`: the warning is turned into an error before the ignore list is read (`Utmess.py:181`, `:186`). |
| `LANG` | text, optional | — | Selects the language of the messages (if available). Language of the messages, for example `'EN'` (`upstream/astest/supv003a.comm:27`): sets the gettext translation of the `aster_messages` domain (`upstream/code_aster/CodeCommands/debut.py:231`). It has an effect only if a compiled catalog for that language is installed. TODO(verify) which languages the official 17.4 image ships (see ADR-004). |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. |
| `MODE` | text, optional | `'AUTO'` | One of `'AUTO'`, `'DEBUT'`, `'POURSUITE'`. Start or restart. `'DEBUT'`: always start a new study. `'POURSUITE'`: restart from the saved database of a previous run, like the `POURSUITE` command. `'AUTO'` (default): restart if a saved database is available, else start (`upstream/code_aster/CodeCommands/debut.py:150`–`:158`). |

1 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- `RESERVE_CPU`: at most one of `VALE`, `POURCENTAGE` may be given (`EXCLUS`).
- `RESERVE_MEMOIRE`: at most one of `VALE`, `POURCENTAGE` may be given (`EXCLUS`).

## What the solver does

- Before the syntax check, the memory limit is reduced by `RESERVE_MEMOIRE` (`upstream/code_aster/CodeCommands/debut.py:132`).
- Start or restart is decided from `MODE`, the command name (`DEBUT` or `POURSUITE`), the
  command-line options and whether a saved database exists (`upstream/code_aster/CodeCommands/debut.py:148`–`:167`).
- Then: test mode and error behavior (`debut.py:179`–`:200`), debug flags (`:203`–`:216`),
  `IMPR_MACRO`, `LANG` and `IGNORE_ALARM` (`:225`–`:235`), and the Fortran initialization of
  databases, catalogs, memory and time reserve (`upstream/bibfor/supervis/`).
- Deprecated keywords `PAR_LOT` and `FORMAT_HDF` are accepted and dropped with a deprecation
  warning (`compat_syntax`, `upstream/code_aster/Cata/Commands/debut.py:28`).

## Patterns

### Plain study start

The minimal form; everything else keeps its default. It appears in a command file written by
an upstream run-script test.

Source: `upstream/astest/asrun01b.88:17`.

```python
DEBUT()
```

### Test-style start: abort on error, warnings are errors

What our solid and modal fixtures use, so that any new warning fails the run.

Source: `tests/fixtures/solid_static/input/run.comm:12`.

```python
DEBUT(CODE="OUI", ERREUR=_F(ALARME="EXCEPTION"))
```

### Ignore one understood warning

Source: `tests/fixtures/shell_static/input/run.comm:17`.

```python
DEBUT(CODE="OUI", IGNORE_ALARM=("MODELISA8_14",))
```

### Errors as Python exceptions

Lets the command file catch a fatal error with `try`/`except`.

Source: `upstream/astest/comp012d.comm:23`.

```python
DEBUT(CODE="OUI", ERREUR=_F(ERREUR_F="EXCEPTION", ALARME="EXCEPTION"), DEBUG=_F(SDVERI="OUI"))
```

### Messages in English

Source: `upstream/astest/supv003a.comm:27`.

```python
DEBUT(CODE="OUI", ERREUR=_F(ALARME="EXCEPTION"), LANG="EN")
```

### More time kept back for the end of the run

Source: `upstream/astest/adlv100a.comm:21`.

```python
DEBUT(CODE="OUI", DEBUG=_F(SDVERI="NON"), RESERVE_CPU=_F(VALE=60))
```

## Pitfalls

- **`ALARME='EXCEPTION'` and `IGNORE_ALARM` do not combine.** Warnings are turned into errors
  before the ignore list is read (`upstream/code_aster/Messages/Utmess.py:181`), so an ignored
  warning still stops the run. Our shell fixture drops `ALARME='EXCEPTION'` for this reason
  (comment at `tests/fixtures/shell_static/input/run.comm:13`).
- **`CODE='OUI'` is for test cases.** It turns fatal errors into process aborts and records
  coverage. In a study, omit it and choose `ERREUR_F` explicitly if needed.
- **Ignoring a warning hides it everywhere.** `IGNORE_ALARM` takes message IDs (`FAMILY_N`) and
  silences every occurrence for the whole run; list only warnings you have read and accepted.
- **`MODE='AUTO'` may restart.** If a saved database from an earlier run is present, `DEBUT`
  with the default mode restarts from it (`upstream/code_aster/CodeCommands/debut.py:157`).
  Use `MODE='DEBUT'` to force a clean start.
- **`LANG` needs installed translations.** Without a compiled catalog for the language,
  messages stay in French.
- **`DEBUG` slows the run.** `SDVERI`, `JXVERI` and `JEVEUX` are verification tools; do not
  leave them on in production studies.

## See also

- French reference: U4.11.01 (French text: `en/docs/_src/U4.11.01.fr.md`; translation: `en/docs/U4.11.01.md` once task 5.2 lands)
- Catalog: `en/commands/DEBUT.json` (generated from `upstream/code_aster/Cata/Commands/debut.py:45`)
- Implementation: `upstream/code_aster/CodeCommands/debut.py`; `upstream/bibfor/supervis/ibtcpu.F90`
  (time reserve), `ibdbgs.F90` (memory), `ibbase.F90` (databases), `ibcata.F90` (catalogs)
- `POURSUITE`: same keywords, restarts from a saved database
- End: [FIN](FIN.md)
- Message IDs to ignore: `en/messages/` (once translated) or the `.mess` file
- Example: `tests/fixtures/solid_static/input/run.comm` (line 12)
- Example: `tests/fixtures/shell_static/input/run.comm` (line 17)
- Example: `upstream/astest/supv003a.comm` (line 27)
