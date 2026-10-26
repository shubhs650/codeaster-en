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

## 7. Tier coverage and astest usage (task 1.5)

<!-- caen:inventory:begin (generated by `caen extract inventory`; do not edit) -->
- **Data:** `en/commands/` (268 files), `en/messages/` (277 files), `en/astest-index.json`, all extracted from upstream `17.4.26` (commit `5d2a06d`); tiers from `docs/COMMAND-SET.md`.
- **Regenerate:** `caen extract inventory` (rewrites only this block).

### 7.1 Totals

| Item | Count |
|---|---:|
| Catalog commands | 268 (1 `FORM`, 116 `MACRO`, 135 `OPER`, 16 `PROC`) |
| Keyword occurrences (`SIMP` + `FACT`) | 18917 |
| … with a `fr=` help string | 2509 |
| Conditional blocks (`BLOC`) | 2847 |
| Message families (files) | 277 |
| Message families (name without trailing number) | 146 |
| Messages | 6890 |
| Test cases (`astest/*.export`) | 4496 |
| Command files parsed | 4708 |
| Commands used by at least one test case | 279 of 280 |

### 7.2 Tier commands

Keyword counts are occurrences in the command's tree (a keyword repeated in several blocs counts each time). *Cases* = test cases that call the command; *rank* = its position among all commands by cases.

| Tier | Command | Catalog | Keywords | with `fr=` | Blocs | Cases | Calls | Rank |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `DEBUT` | MACRO | 39 | 24 | 0 | 4295 | 4305 | 2 |
| 1 | `FIN` | PROC | 3 | 3 | 0 | 4435 | 4796 | 1 |
| 1 | `POURSUITE` | not in catalog (`code_commands`) | — | — | — | 274 | 345 | 41 |
| 1 | `LIRE_MAILLAGE` | OPER | 11 | 3 | 3 | 4055 | 4388 | 4 |
| 1 | `MODI_MAILLAGE` | OPER | 42 | 4 | 2 | 1208 | 1422 | 17 |
| 1 | `DEFI_GROUP` | OPER | 122 | 0 | 24 | 1957 | 2598 | 13 |
| 1 | `CREA_MAILLAGE` | OPER | 69 | 23 | 2 | 783 | 950 | 22 |
| 1, 2 | `AFFE_MODELE` | OPER | 31 | 8 | 10 | 4079 | 5038 | 3 |
| 1 | `DEFI_MATERIAU` | MACRO | 3255 | 335 | 24 | 3978 | 5653 | 5 |
| 1, 2 | `AFFE_MATERIAU` | MACRO | 23 | 0 | 2 | 3818 | 4777 | 6 |
| 1, 2 | `AFFE_CARA_ELEM` | OPER | 258 | 49 | 60 | 1506 | 1915 | 14 |
| 1, 2 | `AFFE_CHAR_MECA` | OPER | 491 | 46 | 20 | 3160 | 6522 | 7 |
| 1 | `AFFE_CHAR_CINE` | OPER | 100 | 1 | 1 | 610 | 906 | 27 |
| 1, 2 | `DEFI_FONCTION` | OPER | 17 | 6 | 3 | 2277 | 5116 | 10 |
| 1 | `DEFI_CONSTANTE` | OPER | 3 | 0 | 0 | 911 | 4275 | 20 |
| 1 | `MECA_STATIQUE` | MACRO | 86 | 4 | 20 | 757 | 1290 | 24 |
| 1 | `CALC_CHAMP` | OPER | 124 | 66 | 8 | 1966 | 4230 | 12 |
| 1 | `POST_RELEVE_T` | OPER | 58 | 0 | 6 | 782 | 2420 | 23 |
| 1, 2 | `POST_ELEM` | OPER | 355 | 2 | 55 | 302 | 697 | 39 |
| 1, 2 | `CREA_CHAMP` | OPER | 87 | 0 | 25 | 1451 | 6113 | 15 |
| 1 | `IMPR_RESU` | PROC | 170 | 3 | 45 | 755 | 1316 | 25 |
| 1 | `IMPR_TABLE` | MACRO | 43 | 23 | 6 | 992 | 2903 | 19 |
| 1 | `TEST_RESU` | PROC | 147 | 0 | 25 | 2861 | 11474 | 9 |
| 1 | `MACR_LIGN_COUPE` | MACRO | 56 | 2 | 16 | 104 | 281 | 68 |
| 1 | `POST_RCCM` | OPER | 303 | 241 | 27 | 20 | 146 | 129 |
| 2 | `CALC_MODES` | MACRO | 693 | 34 | 191 | 578 | 1088 | 29 |
| 2 | `ASSEMBLAGE` | MACRO | 29 | 0 | 10 | 304 | 406 | 38 |
| 2 | `CALC_MATR_ELEM` | MACRO | 67 | 1 | 19 | 590 | 1657 | 28 |
| 2 | `NUME_DDL` | MACRO | 4 | 0 | 1 | 562 | 772 | 32 |
| 2 | `ASSE_MATRICE` | MACRO | 5 | 0 | 0 | 565 | 1625 | 31 |
| 2 | `NORM_MODE` | OPER | 17 | 7 | 1 | 123 | 195 | 60 |
| 2 | `EXTR_MODE` | OPER | 18 | 0 | 2 | 33 | 56 | 111 |
| 2 | `THER_LINEAIRE` | MACRO | 107 | 1 | 28 | 251 | 317 | 44 |
| 2 | `AFFE_CHAR_THER` | OPER | 93 | 2 | 2 | 195 | 280 | 52 |
| 2 | `AFFE_CHAR_MECA_F` | OPER | 254 | 23 | 5 | 673 | 977 | 26 |
| 3 | `STAT_NON_LINE` | OPER | 314 | 16 | 78 | 1974 | 3269 | 11 |
| 3 | `DEFI_CONTACT` | OPER | 219 | 13 | 88 | 272 | 306 | 42 |
| 3 | `DEFI_LIST_INST` | OPER | 70 | 46 | 30 | 794 | 929 | 21 |
| 3 | `DEFI_LIST_REEL` | OPER | 8 | 0 | 0 | 2901 | 4470 | 8 |
| 3 | `CALC_EUROPLEXUS` | **not found** | — | — | — | 0 | 0 | — |
| 3 | `DYNA_VIBRA` | OPER | 577 | 16 | 141 | 261 | 544 | 43 |
| 3 | `MODE_NON_LINE` | OPER | 98 | 0 | 21 | 5 | 7 | 197 |
| 3 | `CALC_FATIGUE` | OPER | 47 | 0 | 15 | 9 | 63 | 167 |
| 3 | `POST_CHAMP` | OPER | 37 | 15 | 3 | 132 | 467 | 58 |
| 3 | `CALC_G` | OPER | 41 | 0 | 16 | 101 | 700 | 70 |

- Tier 1: 25 commands first listed in this tier, 24 in the catalog; not in the catalog: `POURSUITE`.
- Tier 2: 10 commands first listed in this tier, 10 in the catalog.
- Tier 3: 10 commands first listed in this tier, 9 in the catalog; not in the catalog: `CALC_EUROPLEXUS`.

### 7.3 Key keywords named in COMMAND-SET.md

A key keyword is *found* when it is a keyword name, an `into=` value, or a command name in one of the row's commands.

| Tier | Function | Commands | Found | Not found |
|---|---|---|---:|---|
| 1 | Session | `DEBUT`, `FIN`, `POURSUITE` | 4/4 | — |
| 1 | Mesh in | `LIRE_MAILLAGE` | 4/4 | — |
| 1 | Mesh fix-ups | `MODI_MAILLAGE` | 2/2 | — |
| 1 | Groups | `DEFI_GROUP` | 10/10 | — |
| 1 | Mesh derive | `CREA_MAILLAGE` | 3/3 | — |
| 1 | Model | `AFFE_MODELE` | 12/12 | — |
| 1 | Material | `DEFI_MATERIAU` | 5/5 | — |
| 1 | Material field | `AFFE_MATERIAU` | 4/4 | — |
| 1 | Element props | `AFFE_CARA_ELEM` | 6/6 | — |
| 1 | Loads & BCs | `AFFE_CHAR_MECA` | 13/13 | — |
| 1 | BCs (kinematic) | `AFFE_CHAR_CINE` | 1/1 | — |
| 1 | Functions | `DEFI_FONCTION`, `DEFI_CONSTANTE` | 4/5 | `GAUCHE` |
| 1 | Solve | `MECA_STATIQUE` | 12/12 | — |
| 1 | Post fields | `CALC_CHAMP` | 14/14 | — |
| 1 | Post extract | `POST_RELEVE_T` | 10/10 | — |
| 1 | Post elem | `POST_ELEM` | 2/2 | — |
| 1 | Field ops | `CREA_CHAMP` | 5/5 | — |
| 1 | Output | `IMPR_RESU` | 7/7 | — |
| 1 | Output tables | `IMPR_TABLE` | 6/6 | — |
| 1 | Verification | `TEST_RESU` | 5/5 | — |
| 1 | Cut lines | `MACR_LIGN_COUPE` | 6/6 | — |
| 1 | Linearisation | `POST_RCCM` | 3/3 | — |
| 2 | Modal | `CALC_MODES` | 11/12 | `MODELE` |
| 2 | Modal matrices | `ASSEMBLAGE`, `CALC_MATR_ELEM`, `NUME_DDL`, `ASSE_MATRICE` | 4/4 | — |
| 2 | Modal post | `NORM_MODE`, `EXTR_MODE`, `POST_ELEM` | 6/6 | — |
| 2 | Remote load | `AFFE_CHAR_MECA` | 6/6 | — |
| 2 | Bonded contact | `AFFE_CHAR_MECA` | 4/4 | — |
| 2 | Springs | `AFFE_CARA_ELEM`, `AFFE_MODELE` | 8/8 | — |
| 2 | Temperature load | `AFFE_MATERIAU`, `CREA_CHAMP` | 5/5 | — |
| 2 | Thermal (steady) | `THER_LINEAIRE`, `AFFE_CHAR_THER` | 4/4 | — |
| 2 | Hydrostatic | `DEFI_FONCTION`, `AFFE_CHAR_MECA`, `AFFE_CHAR_MECA_F` | 1/2 | `FONC_MULT` |

187 of 190 key keywords found.

### 7.4 Tier 1 message families (COMMAND-SET.md "Likely" list)

A listed name matches every file whose name without its trailing number equals it (`MODELISA` → `MODELISA`, `MODELISA2`…`MODELISA10`).

| Family | Exists | Files | Messages |
|---|---|---:|---:|
| `SUPERVIS` | yes | 2 | 81 |
| `JEVEUX` | yes | 2 | 146 |
| `MODELISA` | yes | 10 | 509 |
| `CALCULEL` | yes | 7 | 372 |
| `MECASTATIQUE` | **no** | 0 | 0 |
| `MECANONLINE` | yes | 14 | 390 |
| `ALGELINE` | yes | 7 | 473 |
| `FACTOR` | yes | 3 | 74 |
| `MATERIAL` | yes | 2 | 33 |
| `CHARGES` | yes | 9 | 173 |
| `POSTRELE` | yes | 1 | 67 |
| `PREPOST` | yes | 6 | 209 |
| `MED` | yes | 3 | 106 |
| `UTILITAI` | yes | 8 | 403 |
| `ELEMENTS` | yes | 6 | 170 |
| `COMPOR` | yes | 7 | 258 |
| `DVP` | yes | 1 | 10 |

### 7.5 Messages that reference Tier 1/2 commands

*Family by name*: families named after the command (name without underscores, trailing number ignored). *Mentions*: messages whose French text contains the command name as a whole word, with the families holding most of them. Both are heuristics: they show where a command's own diagnostics live, not every message it can raise.

| Command | Family by name (messages) | Mentions | Top families |
|---|---|---:|---|
| `AFFE_CARA_ELEM` | `AFFECARAELEM` (27) | 72 | `AFFECARAELEM` 27, `DISCRETS` 7, `MODELISA` 6 |
| `AFFE_CHAR_CINE` | — | 20 | `ALGELINE2` 4, `CHARGES5` 4, `CALCULEL` 2 |
| `AFFE_CHAR_MECA` | — | 19 | `ALGELINE2` 3, `CHARGES7` 2, `CHARGES9` 2 |
| `AFFE_CHAR_MECA_F` | — | 0 | — |
| `AFFE_CHAR_THER` | — | 4 | `CHARGES` 1, `CHARGES2` 1, `CREACHAMP1` 1 |
| `AFFE_MATERIAU` | — | 30 | `CALCUL` 5, `MODELISA9` 4, `COMPOR4` 3 |
| `AFFE_MODELE` | — | 23 | `MODELE1` 5, `CONTACT2` 3, `CONTACT3` 2 |
| `ASSEMBLAGE` | — | 0 | — |
| `ASSE_MATRICE` | — | 0 | — |
| `CALC_CHAMP` | `CALCCHAMP`, `CALCCHAMP1` (20) | 20 | `PREPOST` 6, `CALCCHAMP1` 4, `CALCULEL4` 2 |
| `CALC_MATR_ELEM` | — | 2 | `ASSEMBLA` 1, `MEMBRANE` 1 |
| `CALC_MODES` | — | 25 | `MODAL` 21, `ALGELINE5` 4 |
| `CREA_CHAMP` | `CREACHAMP1` (6) | 37 | `CALCULEL4` 6, `UTILITAI` 6, `CALCULEL2` 4 |
| `CREA_MAILLAGE` | — | 12 | `CONTACT2` 2, `CONTACT4` 2, `MESH1` 2 |
| `DEBUT` | — | 5 | `SUPERVIS` 2, `CATAMESS` 1, `CONTACT` 1 |
| `DEFI_CONSTANTE` | — | 0 | — |
| `DEFI_FONCTION` | — | 6 | `DISCRETS` 3, `RUPTURE2` 2, `UTILITAI8` 1 |
| `DEFI_GROUP` | — | 7 | `SOUSTRUC` 3, `ALGELINE3` 1, `CONTACT` 1 |
| `DEFI_MATERIAU` | — | 60 | `FATIGUE1` 22, `ALGORITH4` 4, `MEMBRANE` 4 |
| `EXTR_MODE` | — | 1 | `MODELISA2` 1 |
| `FIN` | — | 5 | `MODELISA6` 2, `MODELISA4` 1, `SUPERVIS` 1 |
| `IMPR_RESU` | — | 7 | `MED` 2, `RESULT3` 2, `CALCULEL4` 1 |
| `IMPR_TABLE` | — | 3 | `ALGELINE2` 2, `UTILITAI4` 1 |
| `LIRE_MAILLAGE` | — | 3 | `AFFECARAELEM` 1, `MESH4` 1, `MODELE1` 1 |
| `MACR_LIGN_COUPE` | — | 8 | `POST0` 7, `POSTRCCM` 1 |
| `MECA_STATIQUE` | — | 2 | `MEMBRANE` 1, `RUPTURE1` 1 |
| `MODI_MAILLAGE` | — | 26 | `INTEMAIL` 4, `MODELISA` 4, `ALGORITH16` 3 |
| `NORM_MODE` | — | 1 | `ALGELINE3` 1 |
| `NUME_DDL` | — | 21 | `CALCESSAI0` 2, `CALCULEL4` 2, `MATRICE0` 2 |
| `POST_ELEM` | `POSTELEM` (10) | 17 | `UTILITAI3` 6, `POSTELEM` 5, `UTILITAI7` 3 |
| `POST_RCCM` | `POSTRCCM` (55) | 2 | `CALCULEL2` 1, `POSTRCCM` 1 |
| `POST_RELEVE_T` | — | 4 | `POSTRELE` 3, `SOUSTRUC` 1 |
| `POURSUITE` | — | 4 | `SUPERVIS` 3, `CATAMESS` 1 |
| `TEST_RESU` | — | 0 | — |
| `THER_LINEAIRE` | — | 2 | `CALCUL` 1, `ELEMENTS3` 1 |

### 7.6 Top 50 commands across astest

Ranked by number of test cases that call the command, then by number of calls.

| Rank | Command | Cases | Calls | Tier |
|---:|---|---:|---:|---|
| 1 | `FIN` | 4435 | 4796 | 1 |
| 2 | `DEBUT` | 4295 | 4305 | 1 |
| 3 | `AFFE_MODELE` | 4079 | 5038 | 1, 2 |
| 4 | `LIRE_MAILLAGE` | 4055 | 4388 | 1 |
| 5 | `DEFI_MATERIAU` | 3978 | 5653 | 1 |
| 6 | `AFFE_MATERIAU` | 3818 | 4777 | 1, 2 |
| 7 | `AFFE_CHAR_MECA` | 3160 | 6522 | 1, 2 |
| 8 | `DEFI_LIST_REEL` | 2901 | 4470 | 3 |
| 9 | `TEST_RESU` | 2861 | 11474 | 1 |
| 10 | `DEFI_FONCTION` | 2277 | 5116 | 1, 2 |
| 11 | `STAT_NON_LINE` | 1974 | 3269 | 3 |
| 12 | `CALC_CHAMP` | 1966 | 4230 | 1 |
| 13 | `DEFI_GROUP` | 1957 | 2598 | 1 |
| 14 | `AFFE_CARA_ELEM` | 1506 | 1915 | 1, 2 |
| 15 | `CREA_CHAMP` | 1451 | 6113 | 1, 2 |
| 16 | `TEST_TABLE` | 1423 | 13685 | — |
| 17 | `MODI_MAILLAGE` | 1208 | 1422 | 1 |
| 18 | `FORMULE` | 1125 | 4098 | — |
| 19 | `IMPR_TABLE` | 992 | 2903 | 1 |
| 20 | `DEFI_CONSTANTE` | 911 | 4275 | 1 |
| 21 | `DEFI_LIST_INST` | 794 | 929 | 3 |
| 22 | `CREA_MAILLAGE` | 783 | 950 | 1 |
| 23 | `POST_RELEVE_T` | 782 | 2420 | 1 |
| 24 | `MECA_STATIQUE` | 757 | 1290 | 1 |
| 25 | `IMPR_RESU` | 755 | 1316 | 1 |
| 26 | `AFFE_CHAR_MECA_F` | 673 | 977 | 2 |
| 27 | `AFFE_CHAR_CINE` | 610 | 906 | 1 |
| 28 | `CALC_MATR_ELEM` | 590 | 1657 | 2 |
| 29 | `CALC_MODES` | 578 | 1088 | 2 |
| 30 | `RECU_FONCTION` | 571 | 2699 | — |
| 31 | `ASSE_MATRICE` | 565 | 1625 | 2 |
| 32 | `NUME_DDL` | 562 | 772 | 2 |
| 33 | `CREA_RESU` | 430 | 740 | — |
| 34 | `TEST_FONCTION` | 383 | 1388 | — |
| 35 | `CALC_TABLE` | 359 | 2445 | — |
| 36 | `CREA_TABLE` | 357 | 1149 | — |
| 37 | `CALC_FONC_INTERP` | 322 | 917 | — |
| 38 | `ASSEMBLAGE` | 304 | 406 | 2 |
| 39 | `POST_ELEM` | 302 | 697 | 1, 2 |
| 40 | `IMPR_FONCTION` | 277 | 611 | — |
| 41 | `POURSUITE` | 274 | 345 | 1 |
| 42 | `DEFI_CONTACT` | 272 | 306 | 3 |
| 43 | `DYNA_VIBRA` | 261 | 544 | 3 |
| 44 | `THER_LINEAIRE` | 251 | 317 | 2 |
| 45 | `AFFE_CHAR_THER_F` | 238 | 296 | — |
| 46 | `DEFI_FISS_XFEM` | 237 | 351 | — |
| 47 | `MODI_MODELE_XFEM` | 229 | 249 | — |
| 48 | `CALC_FONCTION` | 227 | 915 | — |
| 49 | `CALC_VECT_ELEM` | 222 | 361 | — |
| 50 | `ASSE_VECTEUR` | 218 | 362 | — |

In the top 50 but in no tier (15): `TEST_TABLE`, `FORMULE`, `RECU_FONCTION`, `CREA_RESU`, `TEST_FONCTION`, `CALC_TABLE`, `CREA_TABLE`, `CALC_FONC_INTERP`, `IMPR_FONCTION`, `AFFE_CHAR_THER_F`, `DEFI_FISS_XFEM`, `MODI_MODELE_XFEM`, `CALC_FONCTION`, `CALC_VECT_ELEM`, `ASSE_VECTEUR`.
<!-- caen:inventory:end -->

**Cross-check.** `grep` over `astest/*.comm|*.com[0-9]|*.py` for `MECA_STATIQUE(` finds 758
file stems against 757 cases in §7.2 (the grep also matches commented-out calls), and 20 for
`POST_RCCM(` against 20.

## 8. Findings for the COMMAND-SET.md revision (task 1.5)

Proposals only; `docs/COMMAND-SET.md` is unchanged in this task. Each needs the owner's call.

1. **Tier 1 names all exist** in 17.4.26 except `POURSUITE`, which runs `DEBUT`'s catalog
   (§1); it is used by 274 test cases. `POST_RCCM` exists (`OPER`, 20 cases) and takes
   `TYPE_RESU_MECA` and `OPTION='PM_PB'`, so the "verify name" note in its row can go.
2. **`CALC_MODES` has no `MODELE` keyword.** The Tier 2 row says "`MATR_RIGI`/`MATR_MASS` or
   `MODELE`+`CHAM_MATER` form". In 17.4.26 the command takes assembled matrices only: `MATR_RIGI` is
   required for `TYPE_RESU='DYNAMIQUE'` and `'MODE_FLAMB'` (`calc_modes.py:89`, `:433`) and
   `MATR_A`/`MATR_B` for `'GENERAL'` (`:656-657`); `CHAM_MATER` and `CARA_ELEM` are optional
   top-level keywords (`calc_modes.py:83-84`). Proposal: drop "or `MODELE`+`CHAM_MATER` form" and keep the
   assembled-matrix route (`ASSEMBLAGE` or `CALC_MATR_ELEM`/`NUME_DDL`/`ASSE_MATRICE`, which
   fixture `modal` already uses). TODO(verify) what `CHAM_MATER`/`CARA_ELEM` do in
   `CALC_MODES`; the catalog gives no `fr=` for them.
3. **`FONC_MULT` is not an `AFFE_CHAR_MECA(_F)` keyword.** The Tier 2 "Hydrostatic" row puts it
   next to `PRES_REP`; it is `MECA_STATIQUE`'s `EXCIT/FONC_MULT` (a time multiplier). A
   pressure that varies with `Z` goes through `AFFE_CHAR_MECA_F` / `PRES_REP` / `PRES`, whose
   type is `fonction_sdaster`, `nappe_sdaster` or `formule` (catalog). Proposal: reword the row and add `FORMULE` (below).
4. **`PROL_DROITE/GAUCHE`** in the Tier 1 "Functions" row is shorthand; the keywords are
   `PROL_DROITE` and `PROL_GAUCHE`. Cosmetic.
5. **`CALC_EUROPLEXUS` is not in the 17.4.26 catalog** (Tier 3, already marked "no"). Proposal:
   remove it from the list.
6. **Message family `MECASTATIQUE` does not exist**, and no family is named after
   `MECA_STATIQUE` (§7.5: two messages mention it). Its implementation
   (`MacroCommands/meca_statique_ops.py`) raises no `UTMESS` of its own. Proposal: drop it from
   the "Likely" list and take the static-solve families from the fixture logs (task 4.2). The
   16 families that exist hold 3,474 of the 6,890 messages (50 %), which is too broad to be
   the "translate first" set; the fixture logs should narrow it.
7. **Top-50 commands in no tier** (§7.6), the ones a linear static/modal workflow is likely to
   need:
   - `FORMULE` (rank 18, 1,125 cases): analytic functions of `X`, `Y`, `Z`, `INST` for loads
     such as hydrostatic pressure. Candidate for Tier 1 or 2.
   - `TEST_TABLE` (rank 16): the table counterpart of `TEST_RESU`; fixtures that check
     `POST_RELEVE_T`/`POST_ELEM` tables need it. Candidate for Tier 1 next to `TEST_RESU`.
   - `DEFI_LIST_REEL` (rank 8, Tier 3 now): `MECA_STATIQUE` takes `LIST_INST` (rule
     `UN_PARMI("INST", "LIST_INST")`), so a multi-step static run needs it. Candidate for
     Tier 1.
   - `CALC_TABLE`, `CREA_TABLE` (ranks 35–36): table filtering and building, used in
     post-processing. Candidates for Tier 2.
   - `CALC_VECT_ELEM`, `ASSE_VECTEUR` (ranks 49–50): only needed if Tier 2 keeps the
     element-matrix route for more than modal matrices. No change proposed.
   The rest (`RECU_FONCTION`, `CREA_RESU`, `TEST_FONCTION`, `CALC_FONC_INTERP`,
   `IMPR_FONCTION`, `CALC_FONCTION`, `AFFE_CHAR_THER_F`, `DEFI_FISS_XFEM`,
   `MODI_MODELE_XFEM`) serve transient, thermal or XFEM work; no change proposed.
8. **Help strings are thin where Tier 1 matters most.** `fr=` coverage is 0 for `DEFI_GROUP`,
   `AFFE_MATERIAU`, `POST_RELEVE_T`, `CREA_CHAMP` and `TEST_RESU`, and 1–4 for
   `AFFE_CHAR_CINE`, `MECA_STATIQUE`, `MODI_MAILLAGE`, `IMPR_RESU` (§7.2). Task 2.2/2.3
   drafts for these must come from the U4 docs and astest examples, not the catalog. The U4
   PDFs are not in the repository (§6).
