# Upstream inventory

What the pinned upstream contains, counted. Written by task 0.4 (S1); task 1.5 extends it with
tier coverage and astest usage statistics once the extractors exist.

- **Upstream:** `17.4.26` (commit `5d2a06d2a4afe589468f96617080e7aabac3e4f2`, `UPSTREAM_VERSION`)
- **Counted on:** 2026-10-23, Python 3.13 + numpy 2.5, no solver build
- **Method:** catalog counts by importing `code_aster.Cata.Commands` and walking the object tree;
  message counts by an AST walk of `code_aster/Messages/*.py` (the package cannot be imported
  without the solver, see §2); test cases by counting `astest/*.export`. One-off scripts, not
  committed; tasks 1.2 and 1.3 turn them into `caen extract`.

## 1. Command catalogs

| Item | Count | Notes |
|---|---:|---|
| Catalog modules `code_aster/Cata/Commands/*.py` | 269 | excluding `__init__.py` |
| Commands (`Command` objects in `commandStore`) | 268 | 135 `OPER`, 116 `MACRO`, 16 `PROC` (incl. `FIN` via `FIN_PROC`), 1 `FORM` |
| Non-command entries | 1 | `VARIABLE` (`VariableSupport`, from `variable.py`) |
| Shared keyword factories `code_aster/Cata/Commons/*.py` | 26 | `C_SOLVEUR`, `C_COMPORTEMENT`, … expanded into each command |
| Keyword occurrences (all commands, Commons expanded) | 18,917 | 17,595 simple (`SIMP`) + 1,322 factor (`FACT`) |
| Conditional blocks (`BLOC`) | 2,847 | |
| Distinct keyword names | 4,227 | |
| Commands with a `fr=` help string | 258 of 268 | |
| Keyword occurrences with a `fr=` help string | 2,509 of 18,917 (13 %) | French help is sparse; most keywords have none |
| Distinct `fr=` strings (commands + keywords) | 1,973 | |
| `ang=` (English) help strings | 0 | |

**DSL.** `code_aster/Cata/Language/Syntax.py` defines `OPER`, `MACRO`, `PROC`, `FIN_PROC`,
`FORM`, `SIMP`, `FACT`, `BLOC` and the rules `AU_MOINS_UN`, `UN_PARMI`, `EXCLUS`,
`PRESENT_PRESENT`, `PRESENT_ABSENT`, `ENSEMBLE`, `NON_VIDE`. Help strings are wrapped in
`tr(...)`, a `Translation` object whose function is set at runtime (`tr.set_translator`).

**Importable without the solver: yes.** `import code_aster.Cata.Commands` works in a plain venv
with numpy installed. `code_aster/__init__.py` wraps the `libaster`/`aster_core` imports in
`try/except ImportError`, and `Cata` only needs numpy (`affe_cara_elem.py`,
`Language/SyntaxChecker.py`, `Language/SyntaxUtils.py`). `commandStore` (in
`Cata/Commands/__init__.py`) is a dict of all commands; each object exposes `.definition`
(an ordered dict) and `.definition.entities` (keywords and blocks). Task 1.2 can extract by
import; the AST fallback is not needed. Set `PYTHONDONTWRITEBYTECODE=1` so no `__pycache__`
is written under `upstream/`.

**`POURSUITE` has no catalog of its own.** `code_aster/CodeCommands/debut.py` defines both
`DEBUT` and `POURSUITE` as partials of one `Starter` class that uses the `DEBUT` catalog
(`DEBUT(MODE='POURSUITE')` is the equivalent). `docs/COMMAND-SET.md` Tier 1 lists `POURSUITE`;
its reference must document it as an alias of `DEBUT`'s syntax. All other commands named in
`docs/COMMAND-SET.md` exist in `commandStore`.

## 2. Messages

| Item | Count | Notes |
|---|---:|---|
| Message families (files `code_aster/Messages/<family>.py`) | 277 | excluding `__init__.py`, `Utmess.py`; ID = `<FILE NAME UPPER>_<N>`, e.g. `mecanonline10.py` → `MECANONLINE10_3` |
| Messages (`cata_msg` entries) | 6,890 | |
| … plain form | 6,849 | `N: _("""…""")`; includes the unwrapped and f-string cases below |
| … dict form | 41 | `N: {"message": _("""…"""), "flags": "DECORATED"}` |
| … not wrapped in `_()` | 15 | gettext can never translate these |
| … f-strings inside `_()` | 2 | `POST0_55`, `POST0_56` interpolate module-level `_nota_lign_coupe_axis`; xgettext cannot extract them |
| … numbered ≥ 100 | 4 | `ALGORITH9_100`, `CALCULEL3_100`, `CALCULEL3_101`, `XFEM_100` — unreachable: `Utmess.decode_idmess` asserts `0 < N < 100` |
| Largest family | `ALGELINE6` (99) | |

**Not importable without the solver.** `code_aster/Messages/__init__.py` imports `Utmess.py`,
which imports `aster_core` and `libaster`. Every family module goes through the package
`__init__`, so task 1.3 must parse the files with `ast` (the `cata_msg` assignment is a literal
dict; values are `_()` calls on string constants, with the f-string and dict exceptions above).

**Placeholders.** 51 distinct formats; all named (`%(k1)s` strings, `%(iN)` integers, `%(rN)`
reals), no positional `%s`. 3,744 `k`, 1,520 `i`, 1,211 `r` occurrences, plus 45 literal `%%`.
The regex in task 1.3 must cover flags, width and precision:

| Count | Format | Count | Format | Count | Format |
|---:|---|---:|---|---:|---|
| 3714 | `%(kN)s` | 16 | `%(rN).15E` | 4 | `%(rN)10.2E` |
| 1398 | `%(iN)d` | 12 | `%(rN).4f` | 4 | `%(rN).0f` |
| 695 | `%(rN)f` | 12 | `%(rN)8.2f` | 4 | `%(iN)-17d` |
| 134 | `%(rN)12.5E` | 11 | `%(iN)10d` | 3 | `%(kN)24s` |
| 64 | `%(rN)19.12e` | 11 | `%(kN)-8s` | 3 | `%(rN)1.1f` |
| 57 | `%(rN)g` | 11 | `%(iN)12d` | 3 | `%(rN)4.3G` |
| 48 | `%(rN).2f` | 10 | `%(iN)5d` | 3 | `%(rN)19.8e` |
| 45 | `%%` | 9 | `%(iN)8d` | 3 | `%(iN)04d` |
| 37 | `%(iN)i` | 8 | `%(kN)8s` | 2 | `%(rN)9.2E` |
| 33 | `%(rN)12.5e` | 7 | `%(rN)12.4E` | 2 | `%(rN)+.2f` |
| 31 | `%(iN)4d` | 6 | `%(rN).2e` | 2 | `%(rN)G` |
| 22 | `%(rN)e` | 6 | `%(rN).3f` | 2 | `%(rN)17.10e` |
| 22 | `%(rN)13.6G` | 6 | `%(rN)16.9g` | 1 each | `%(rN)10.3e`, `%(iN)2d`, `%(kN)3s`, `%(kN)-20s`, `%(rN).6f`, `%(rN)6.3f`, `%(kN)-12s`, `%(rN).3e` |
| 21 | `%(rN)E` | 5 | `%(kN)-16s` | | |
| 16 | `%(rN)10.3E` | 5 | `%(iN)3d` | | |
| | | 5 | `%(rN)12.2f` | | |

Regex used for the count: `%(?:\(([a-z]+)(\d+)\))?([-+ #0]*\d*(?:\.\d+)?)([sdifeEgGr%])`.

**How a diagnostic appears in the log** (`Utmess.MessageLog.format_message`): messages of type
`A`, `E`, `S`, `F`, or any message with the `DECORATED` flag, are boxed and start with
`<TYPE> <FAMILY_N>` (e.g. `<A> <MECANONLINE_3>`). Informational (`I`) messages without
`DECORATED` print **only the body, with no ID**. Fortran calls (`utmess` → `utprin` in
`bibc/supervis/aster_core_module.c`) go through the same Python `MessageLog`.

## 3. Localisation already in upstream

| Item | Path | Content |
|---|---|---|
| gettext wrapper | `code_aster/Utilities/i18n.py` | `Language` singleton, domain `aster_messages`, locale dir `$ASTER_LOCALEDIR` or `$ASTER_ROOT/share/locale`; `_` = `translate` |
| Switch | `DEBUT(LANG=...)` (`Cata/Commands/debut.py`, handled in `CodeCommands/debut.py:229`) | calls `localization.translation(LANG)` and `tr.set_translator(...)`; nothing else selects a language |
| Build | `i18n/wscript` | `waf build` compiles `.po` → `.mo`, installs to `<LOCALEDIR>/<lang>/LC_MESSAGES/aster_messages.mo`; **disabled unless configured with `--enable-i18n`** (option default `False`) |
| Runtime env | `data/profile.sh.tmpl` | `export ASTER_LOCALEDIR=${RUNASTER_ROOT}/@RELATIVE_LOCALEDIR@` |
| Test | `astest/supv003a.comm` | `DEBUT(LANG="EN")`; passes whether or not `en-US/LC_MESSAGES/aster_messages.mo` exists |
| English messages | `i18n/en-US/aster_messages.po` | Crowdin export, POT date 2016-05-13, one translator, `X-Crowdin-File: /v13/code_aster.po` (source refs are v13 `bibpyt/` paths) |
| English catalog help | `i18n/catapy_en_US.ts` | Qt Linguist file for `fr=` strings (used by Eficas/AsterStudy) |
| Other languages | `i18n/ja-JP/`, `i18n/ro-RO/`, `catapy_ja_JP.ts`, `catapy_ro_RO.ts` | out of scope |

**Reuse of `aster_messages.po` against 17.4.26:**

| Item | Count |
|---|---:|
| `.po` entries | 7,017 (6,737 active, 280 obsolete) |
| Active and translated, not fuzzy | 5,349 |
| Fuzzy / empty `msgstr` | 115 / 1,273 |
| Current messages whose French text matches a translated `msgid` exactly | 3,221 |
| … matching after whitespace normalisation only | 87 |
| **Reusable translations** | **3,308 of 6,890 (48.0 %)** |
| Current messages present in the `.po` but untranslated or fuzzy | 819 |
| Placeholder mismatch among reusable ones | 1 (`ALGORITH16_16`: `%(r1)e` → `%(r1)f`) |

Quality, from a spot check: literal and dated. Examples: `ALGORITH13_39` "choc mal défini … la
maille" → "badly definite shock … the mesh" (glossary: *maille* = element); `UTILITAI3_29`
"instant de rupture" → "time of fracture". Usable as a `method: machine` seed with provenance
pointing at the `.po`; every entry still needs glossary enforcement and review.

Coverage of message families that Tier 1 is likely to hit (reusable / total):
`SUPERVIS` 30/41, `CALCULEL` 39/70, `MODELISA` 22/42, `MED` 63/88, `ALGELINE` 82/91,
`FACTOR` 13/52, `MECANONLINE` 8/18, `CHARGES` 0/17, `AFFECARAELEM` 0/27, `MODELE1` 1/28,
`MESH1` 0/16, `MATERIAL1` 0/18, `POUTRE0` 0/28. Newer families (added after v13) have nothing.

**Reuse of `catapy_en_US.ts`:** 1,546 messages, 1,176 finished. 1,364 sources match one of
the 1,973 current `fr=` strings (whitespace-normalised); 1,033 of those have a finished
translation. Useful as a seed for keyword help in task 2.2, same caveats.

## 4. Test cases (`astest/`)

| Item | Count | Notes |
|---|---:|---|
| Test cases (`*.export`) | 4,496 | |
| `*.comm` files | 4,186 | plus 302 `*.py` command files and `*.com0`…`*.comN` continuation files |
| Mesh/data files | 1,654 `.mmed`, 563 `.mail`, 612 `.datg`, 125 `.med`, 31 `.msh`, 25 `.mgib` | |
| `testlist` tags | 4,176 `sequential`, 320 `parallel`, 2,432 `submit`, 90 `need_data`, 24 `ci` | all 4,496 carry `verification` |
| `mpi_nbcpu` > 1 | 275 | |
| Subdirectories | 10 | data directories (e.g. `zzzz144b/`, `cube_refined_x1-2p/`) |
| Expected-output `.mess` / `.resu` | **0** | the `.mess` parser samples must come from our own fixture runs (task 4.2) |

`.export` format: `P key value` lines (`time_limit`, `memory_limit`, `ncpus`, `mpi_nbcpu`,
`mpi_nbnoeud`, `testlist`) and `F type path D|R unit` lines.

## 5. Licence

`LICENSE` is the GPL-3.0 text. Every catalog and message file carries
`Copyright (C) 1991 - 20xx - EDF R&D - www.code-aster.org` and "either version 3 of the
License, or (at your option) any later version" (279 of 279 files in `Messages/`). This matches
ADR-007. The `.po`/`.ts` files carry no licence header of their own; they ship inside the GPL
repository. The owner confirmed on 2026-10-23 that the Crowdin translations may be reused under
GPL-3.0-or-later with attribution (provenance `upstream:i18n/...`).

## 6. Other layout facts

- `doc/` is the Sphinx developer guide (`devguide/`, `conf.py`). No user documentation (U/R/V)
  is in the repository.
- Solver internals are where CLAUDE.md §6 says: `bibfor/`, `bibc/`, `bibcxx/`, `catalo/`,
  plus `mfront/`, `libs/`, `extern/`, `waftools/`.
- Python code that implements commands is in `code_aster/CodeCommands/` and
  `code_aster/MacroCommands/`; it calls `UTMESS` with message IDs and is where to look to see
  which messages a command can emit.
