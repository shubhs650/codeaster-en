---
guide: reading logs
title: Reading the solver log
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
sources:
  - tests/fixtures/
  - tools/codeaster_en/mess/
  - docs/ENGLISH-LOCALE.md
  - docs/CLEARFEA-INTEGRATION.md
doc_fr: none (our own guide, not a translation)
status: assisted
method: assisted
reviewed_by:
reviewed_on:
written_by: agent, in session (task 5.4)
---

# Reading the solver log

> **Assisted guide.** Written from the committed logs of our fixture runs, good and broken, and
> from our log parser. Not reviewed by an engineer.

Every run writes a log, `output/run.mess` (logical unit 6). It is long, it is mostly in French,
and it holds everything you need to know about the run: what each command did, every warning
and error, the size of the problem, times and memory. This page shows how to find what matters
in it.

## Did the run succeed?

Look at the **last lines**, of `run.mess` or of the runner's output (`run_aster.stdout` in our
fixtures):

```text
------------------------------------------------------------
--- DIAGNOSTIC JOB : OK
------------------------------------------------------------
```

| Job diagnostic | Meaning | `run_aster` exit code |
|---|---|---|
| `OK` | No error, no warning (ignored warnings do not count). | 0 |
| `<A>_ALARM` | Finished, but with warnings. The results exist; read every warning before using them. | 0 |
| `<S>_ERROR` | A command stopped with an error. Results computed before it may exist. | 1 |
| `<F>_SYNTAX_ERROR` | The command file is not valid Python. Nothing ran. | 1 |

The exit codes are those of our fixtures (`docs/CLEARFEA-INTEGRATION.md` §4). Time and memory
limits give other diagnostics, `<S>_CPU_LIMIT` and `<S>_MEMORY_ERROR` (upstream
`run_aster/status.py`); no fixture has hit them yet, so `TODO(verify)` their exact log text.

Do not judge by the line `<I> <FIN> ARRET NORMAL DANS "FIN" ...` ("normal stop in FIN"). `FIN`
still runs after an error raised as an exception, so this line also appears in failed runs
(`tests/fixtures/broken_missing_group/output/run.mess:360`, a run that ended `<S>_ERROR` at `:408`).

## The layout of a log

From top to bottom (line numbers from `tests/fixtures/solid_static/output/run.mess`):

1. **Banner** (`:8`–`:33`): code_aster version, date, machine, library versions, and the message
   language (`Langue des messages`).
2. **One block per command**, in the order they run. Each block is framed the same way:

   ```text
   # Commande #0002 de run.comm.changed.py, ligne 28
   MAIL = LIRE_MAILLAGE(FORMAT='MED',
                        INFO=1,
                        ...)
   ...what the command printed...
   # Résultat commande #0002 (LIRE_MAILLAGE): MAIL ('<00000001>') de type <Mesh>
   # Mémoire (Mo) :   647.01 /   641.55 /   207.82 /   183.73 (VmPeak / VmSize / Optimum / Minimum)
   # Fin commande #0002   user+syst:        0.13s (syst:        0.00s, elaps:        0.13s)
   ```

   "Command #2 of run.comm.changed.py, line 28", then the command **as the solver understood
   it, with every default filled in**. That echo is the best way to see what defaults you got:
   for example, the `MECA_STATIQUE` echo shows the whole `SOLVEUR` block of MUMPS settings
   (`:268`–`:292`). Then the command's own output, then "result of command #2: MAIL, of type
   Mesh", the memory, and the time it took.
3. **`FIN`**: the list of warnings issued during the run (`<I> <CATAMESS_89>`, `:433`), the
   normal-stop line, memory statistics, and a table of CPU and elapsed time per command
   (`:477`–`:500`).
4. **The job diagnostic** (`:514`).

The line numbers in the `Commande` headers are those of `run.comm.changed.py`, the copy of
your file that `run_aster` runs, about a dozen lines further down than in your file
([Concepts](concepts.md#line-numbers-in-the-log)). `caen mess translate` maps them back.

### What to read in a successful run

| Command | Line to look for | What it tells you |
|---|---|---|
| `LIRE_MAILLAGE` | `NOMBRE DE NOEUDS`, `NOMBRE DE MAILLES` and one line per element type | Node and element counts: is this the mesh you meant? (`:115`–`:119`) |
| `MODI_MAILLAGE ORIE_PEAU` | `n MAILLE(S) ONT ETE ORIENTEE(S)` | How many face elements were turned over (`:166`–`:169`). |
| `AFFE_MODELE` | `Sur les N mailles du maillage ..., on a pu en affecter M` and the table *modeling type / element type / finite element / count* | Which elements became which finite elements; elements left out (`:190`–`:194`). |
| `MECA_STATIQUE` | `Le système linéaire à résoudre a N degrés de liberté` | Equations: physical DOF, and Lagrange multipliers for supports and relations (`:294`–`:298`). |
| `CALC_MODES` | `numéro fréquence (HZ) norme d'erreur` and `Vérification à posteriori des modes` | Frequencies, error norms and the Sturm check ([Walkthrough 3](walkthrough-modal.md#3-run-and-read-the-log)). |
| `TEST_RESU` | lines starting `OK` or `NOOK` | Each check, its reference, computed value and error (`:415`–`:417`). |
| `FIN` | `<I> <CATAMESS_89>` | Every warning of the run, with its count. "aucune alarme" means none. |

## Finding the problem in a failed run

1. **Read the job diagnostic** at the end.
2. **Search for the first error box**: `<EXCEPTION>`, `<F>` or `<E>`. In a study errors are
   raised as exceptions, so expect `<EXCEPTION>`. Our broken runs:

   ```text
    ╔================================================================================================╗
    ║ <EXCEPTION> <MODELISA7_77>                                                                     ║
    ║                                                                                                ║
    ║ le GROUP_MA  EDGE  ne fait pas partie du maillage :  00000001                                  ║
    ╚================================================================================================╝
   ```

   (`tests/fixtures/broken_missing_group/output/run.mess:296`–`:300`: "GROUP_MA EDGE is not part
   of mesh 00000001".) `00000001` is the internal name of the mesh; the command block header
   tells you it is `MAIL`.
3. **Look up the command it belongs to**: the nearest `# Commande #N de run.comm.changed.py,
   ligne L` above the box (`:280`, `AFFE_CHAR_MECA`). The result object that command was
   making is deleted ("Destruction du concept ... suite à l'erreur précédente", `:302`).
4. **Ignore the repeats.** The same box is printed again inside the Python traceback that
   follows, once or more (three times in all for `SUPERVIS_4`). Only the first copy matters.
5. **Read the text around the box.** Some errors name their location in a line just before the
   box. For a singular matrix: "Degré de liberté physique associé au noeud 87 et à la
   composante DX", physical DOF of node 87, component DX
   (`tests/fixtures/broken_singular_matrix/output/run.mess:354`).
6. **Look up the ID** in [the FAQ](faq.md) or in `en/messages/<FAMILY>.en.json`, and the
   command in its reference page.

Two errors look different:

- **A catalog error** (`SUPERVIS_4`): the command broke a rule of its catalog, such as a
  misspelled or missing keyword. The box quotes the reason, and that reason is already in
  English because it comes from the Python checker: "At least one argument of ('PRES',
  'CISA_2D') must be defined" (`tests/fixtures/broken_bad_keyword/output/run.mess:316`–`:318`).
  It means the occurrence of `PRES_REP` had neither `PRES` nor `CISA_2D`; the misspelled
  `PRESSION` is what took the place of `PRES`.
- **A Python syntax error**: the log has no banner and no command blocks, only a Python
  traceback ending in `SyntaxError` and the diagnostic `<F>_SYNTAX_ERROR`
  (`tests/fixtures/broken_python_syntax/output/run.mess:12`–`:22`). The line number is that of
  `run.comm.changed.py` again.

## Getting the log in English

There are two ways, and they combine.

**After the run: `caen mess translate`.** Renders any log in English, maps line numbers back to
your command file, and prints a one-line verdict:

```console
$ caen mess translate tests/fixtures/broken_missing_group/output/run.mess --out-dir out
mess translate: wrote out/run.en.mess and out/run.en.json
  diagnostics in English: 5/5
  AFFE_CHAR_MECA (command file line 33) failed: GROUP_MA EDGE is not part of mesh: 00000001 [error MODELISA7_77]
```

`run.en.mess` is the whole log in English; `run.en.json` lists every event with its message
ID, severity and command. `caen mess parse` prints the verdict and the failure class only:

```console
$ caen mess parse tests/fixtures/broken_missing_group/output/run.mess
  diagnostic <S>_ERROR, exit code 1, errors ['MODELISA7_77'], alarms {'MODELISA8_14': 3}
  failure: user-model in AFFE_CHAR_MECA (command #9): a group named in the command file does not exist in the mesh
```

**During the run: `DEBUT(LANG="EN")`** with our English message catalog mounted in the
container. The solver then prints the warning and error boxes and the informational messages
of the analysis commands in English. The banner, the `# Commande #` block headers and the
normal-stop line stay French, some on purpose because `run_aster` and log readers look for
them (`docs/ENGLISH-LOCALE.md`, "What becomes English and what does not", which also gives
the setup). Our fixtures' English-locale logs are
in `tests/fixtures/<case>/output_en/`.

The message texts are our translations, mostly `machine` or `assisted`; none is reviewed yet.
If an English text reads oddly, the French original is in the same file
(`en/messages/<FAMILY>.en.json`, field `fr`).

## Warnings

A warning box starts `<A>`. It ends with "Ceci est une alarme. Si vous ne comprenez pas le sens
de cette alarme, vous pouvez obtenir des résultats inattendus !": "This is a warning. If you
do not understand what it means, you may get unexpected results!" Take it literally: find out
what each warning means before using the results. Then either fix the cause or, if it is
intended, silence that ID with `DEBUT(IGNORE_ALARM=("ID",))` so that new warnings stand out
([Walkthrough 2](walkthrough-shell-static.md#3-run-and-check-the-log)).
