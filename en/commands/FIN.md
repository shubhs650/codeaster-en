---
command: FIN
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/fin.py:44
doc_fr: U4.11.02
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3d)
examples: [zzzz103b, sdld33a, supv002a]
---

# FIN — end study

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation and upstream test cases. Every behavior claim cites its source. Not reviewed by
> an engineer.

`FIN` is the last command of a command file. It saves the objects of the study (their Python
side is pickled and their data saved in the `glob.*` database files) so that a later run can
continue with `POURSUITE`, closes the memory manager and prints the run's timings
(`upstream/code_aster/CodeCommands/fin.py:25`–`:33`, `:105`–`:119`). It is also called
automatically when the run stops early on an error or a time limit (catalog comment,
`upstream/code_aster/Cata/Commands/fin.py:50`). The three keywords only add printouts or
compact the database.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Fin d'une étude, fin du travail engagé par une des commandes DEBUT ou POURSUITE» |
| Kind | `FIN_PROC` (operator 9999; Python: `upstream/code_aster/CodeCommands/fin.py`) |
| Result | none |
| Can reuse its input (`reuse=`) | not applicable |
| French reference | U4.11.02 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `CODE`, `ERREUR`, `DEBUG`, `IGNORE_ALARM` (these are `DEBUT` keywords; COMMAND-SET lists `DEBUT`/`FIN` in one row) |

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `RETASSAGE` | text, optional | `'NON'` | Repacks the GLOBALE database. One of `'OUI'`, `'NON'`. `'OUI'` repacks the global database before it is saved, removing the space left by destroyed objects (`upstream/code_aster/CodeCommands/fin.py:98`). Use it when the database is kept for a later `POURSUITE` and size matters (`upstream/astest/zzzz103b.comm:83`). |
| `INFO_BASE` | text, optional | — | Prints information on the objects in the global database, even if it is not saved. One of `'OUI'`, `'NON'`. `'OUI'` prints, in the message file, the list of objects in the global database (`upstream/code_aster/CodeCommands/fin.py:94`). For diagnosing database size. |
| `INFO_RESU` | text, optional | `'NON'` | Prints information on the result data structures. One of `'OUI'`, `'NON'`. `'OUI'` prints a summary of every result object: fields and steps stored (`upstream/code_aster/CodeCommands/fin.py:96`; `upstream/astest/sdld33a.comm:609`). A quick check that the expected fields were computed. |



## What the solver does

- Collects pending deletions, then saves the objects of the caller's context with
  `saveObjects` unless they were already saved (`upstream/code_aster/CodeCommands/fin.py:75`,
  `:110`–`:114`).
- Whether the global database is kept depends on the run options: it is saved unless this is
  the last step of a multi-step job without a request to keep it (`upstream/code_aster/CodeCommands/fin.py:84`–`:93`).
- Deprecated keywords `FORMAT_HDF` and `PROC0` are accepted and dropped with a deprecation
  warning (`compat_syntax`, `upstream/code_aster/Cata/Commands/fin.py:28`).

## Patterns

### End of a study

Source: `tests/fixtures/solid_static/input/run.comm:88`.

```python
FIN()
```

### Summary of the results at the end

Source: `upstream/astest/sdld33a.comm:609`.

```python
FIN(INFO_RESU="OUI")
```

### Compact the saved database

Source: `upstream/astest/zzzz103b.comm:83`.

```python
FIN(RETASSAGE="OUI")
```

## Pitfalls

- **`FIN` ends the study.** It closes the memory manager, and a second call returns at once (`upstream/code_aster/CodeCommands/fin.py:72`). Put
  post-processing before it.
- **Python objects that cannot be pickled are not saved.** Only objects that exist in the
  command file's context are saved for `POURSUITE`; TODO(verify) what happens to unpicklable
  Python objects against U4.11.02 and `upstream/code_aster/Supervis/Serializer.py`.

## See also

- French reference: U4.11.02 (French text: `en/docs/_src/U4.11.02.fr.md`; translation: `en/docs/U4.11.02.md` once task 5.2 lands)
- Catalog: `en/commands/FIN.json` (generated from `upstream/code_aster/Cata/Commands/fin.py:44`)
- Implementation: `upstream/code_aster/CodeCommands/fin.py`
- Start: [DEBUT](DEBUT.md); restart: `POURSUITE`
- Example: `tests/fixtures/solid_static/input/run.comm` (line 88)
- Example: `upstream/astest/sdld33a.comm` (line 609)
- Example: `upstream/astest/zzzz103b.comm` (line 83)
