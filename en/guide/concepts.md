---
guide: concepts
title: Concepts of a code_aster study
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
sources:
  - tests/fixtures/solid_static/
  - tests/fixtures/shell_static/
  - tests/fixtures/modal/
  - en/commands/
  - upstream/code_aster/Messages/Utmess.py
  - tools/codeaster_en/mess/commlines.py
doc_fr: none (our own guide, not a translation)
status: assisted
method: assisted
reviewed_by:
reviewed_on:
written_by: agent, in session (task 5.4)
---

# Concepts of a code_aster study

> **Assisted guide.** Our own English note, written in session from our command references and
> the committed fixture runs. Claims about solver behavior cite their source. Not reviewed by
> an engineer.

This page names the pieces of a code_aster study and shows how they connect. The walkthroughs
then use each piece on a real model. French names in code font are the solver's own and stay
French; the English next to them is the glossary term (`en/glossary.yaml`).

## The workflow

```text
 mesher (Gmsh, Salome)         you write                  run_aster (in Docker)
 ─────────────────────   ─────────────────────   ───────────────────────────────────────────
 mesh.med  ───────────▶  run.comm  (commands)  ─▶  reads unit 20, runs run.comm line by line
 named groups            run.export (file list)    writes run.mess (log), run.rmed (results),
                                                   tables/*.csv (printed tables)
```

1. **Mesh.** Make the geometry and mesh in a mesher and save it in MED format. Name every
   region you will need later (the body, each support, each loaded face) as a *physical group*
   in Gmsh: these become the element groups and node groups the command file refers to.
2. **Command file** (`run.comm`). A Python script. Each line calls one French command, which
   creates one *result object* (`concept` in French: the mesh, the model, a material, a load, a
   result). Commands run in order, top to bottom.
3. **Export file** (`run.export`). The list of files the job reads and writes, each with its
   *logical unit* number, plus the time and memory limits.
4. **Run.** `run_aster run.export` copies the input files into a scratch directory under their
   unit names (`fort.20` for unit 20), runs the command file and copies the result files back
   (`tests/fixtures/solid_static/output/run_aster.stdout:119`, `:653`–`:656`).
5. **Read.** The log (`.mess`) says what each command did and whether the run succeeded. The
   result file (`.rmed`) holds the fields; the tables hold the numbers you printed.

## The pieces of a command file

The order below is the order of every static analysis in this guide. Each row is one command
(or two) and one result object.

| Step | Command | Result object | What it is in usual FE terms |
|---|---|---|---|
| Start | [`DEBUT`](../commands/DEBUT.md) | — | Opens the study. Sets what to do on errors and warnings, and the message language. |
| Mesh | [`LIRE_MAILLAGE`](../commands/LIRE_MAILLAGE.md) | mesh (`maillage`) | Nodes, elements and named groups, read from the MED file. |
| Groups and orientation | [`DEFI_GROUP`](../commands/DEFI_GROUP.md), [`MODI_MAILLAGE`](../commands/MODI_MAILLAGE.md) | the same mesh, updated | Make node groups from element groups; turn face normals the right way before applying pressure. |
| Model | [`AFFE_MODELE`](../commands/AFFE_MODELE.md) | model | Which elements of the mesh take part, and as what: the physics (`PHENOMENE="MECANIQUE"`) and the modeling type (`MODELISATION`: `3D` solid, `DKT` shell, ...). This is where the element formulation is chosen. See [Modeling types](modelisations.md). |
| Material | [`DEFI_MATERIAU`](../commands/DEFI_MATERIAU.md) | material | One material's properties: `ELAS=_F(E=..., NU=..., RHO=...)`. |
| Material field | [`AFFE_MATERIAU`](../commands/AFFE_MATERIAU.md) | material field (`CHAM_MATER`) | Which material goes on which element group. |
| Element properties | [`AFFE_CARA_ELEM`](../commands/AFFE_CARA_ELEM.md) | element properties (`CARA_ELEM`) | Shell thickness, beam sections, spring stiffness. Not needed for a 3D solid. |
| Loads and supports | [`AFFE_CHAR_MECA`](../commands/AFFE_CHAR_MECA.md) | load | Supports *and* loads are both made by this command: `DDL_IMPO` (imposed DOF) fixes displacements, `PRES_REP` (distributed pressure) applies a pressure, `FORCE_NODALE`, `PESANTEUR`, and so on. |
| Solve | [`MECA_STATIQUE`](../commands/MECA_STATIQUE.md) | linear static result (`EVOL_ELAS`) | Assembles and solves K u = F for the load case. |
| Post-process | [`CALC_CHAMP`](../commands/CALC_CHAMP.md) | the same result, with more fields | Stress, equivalent stress, reactions: computed after the solve, on request. |
| Extract | [`POST_RELEVE_T`](../commands/POST_RELEVE_T.md), [`POST_ELEM`](../commands/POST_ELEM.md) | table | Numbers: reaction resultants on a group, mass and center of gravity. |
| Write | [`IMPR_TABLE`](../commands/IMPR_TABLE.md), [`IMPR_RESU`](../commands/IMPR_RESU.md) | — | Print a table to a text file; write fields to a MED result file. |
| Check | [`TEST_RESU`](../commands/TEST_RESU.md) | — | Compare a computed value with a reference; prints `OK` or `NOOK`. |
| End | [`FIN`](../commands/FIN.md) | — | Closes the study and prints the list of warnings issued. |

Things that surprise engineers coming from other programs:

- **Supports are loads.** There is no separate boundary-condition object. `AFFE_CHAR_MECA`
  with `DDL_IMPO` makes a load object that holds the restraint, and it goes into the load case
  with the other loads. By default the restraint is enforced with Lagrange multipliers, so the
  equation count in the log is larger than the number of physical DOF: in `solid_static`,
  13,866 physical DOF plus 864 Lagrange parameters for 432 restrained DOF
  (`tests/fixtures/solid_static/output/run.mess:294`–`:298`). [`AFFE_CHAR_CINE`](../commands/AFFE_CHAR_CINE.md)
  eliminates the restrained DOF instead.
- **The load case is a list.** `MECA_STATIQUE(EXCIT=(_F(CHARGE=FIXE), _F(CHARGE=PRESS)))`: the
  `EXCIT` keyword (applied loads) lists the load objects that act together, supports included.
  A load object that is not in `EXCIT` does nothing.
- **Stresses are not computed by the solve.** `MECA_STATIQUE` stores the displacement (`DEPL`)
  and the stress at Gauss points (`SIEF_ELGA`). Nodal stress, von Mises and reactions come
  from `CALC_CHAMP` afterward (see [Result fields](fields.md)).
- **A result object can be updated in place.** `RESU = CALC_CHAMP(reuse=RESU, RESULTAT=RESU, ...)`
  adds fields to `RESU` instead of making a new result. `DEFI_GROUP` and `MODI_MAILLAGE` use
  `reuse=MAIL` the same way on the mesh.
- **Pressure is positive into the surface.** A positive `PRES` pushes against the element
  normal. On the skin of a solid, after `MODI_MAILLAGE ORIE_PEAU` has turned the normals
  outward, a positive pressure pushes inward on the solid
  ([`AFFE_CHAR_MECA`](../commands/AFFE_CHAR_MECA.md), "Signs and directions").
- **Reactions are the force the support applies.** `REAC_NODA` at a fixed node is the
  reaction on the structure, so its sum is opposite to the applied load
  (`tests/fixtures/README.md`, "Signs").

## Command file syntax

A command file is Python 3, run by the solver's Python. A command call has this shape:

```python
NAME = COMMAND(KEYWORD=value, FACTOR_KEYWORD=_F(SUB_KEYWORD=value, ...))
```

- A **simple keyword** takes a value: a number, a string in quotes (`"OUI"`, `"3D"`), a result
  object name (`MODELE=MODE`), or a tuple for a list (`GROUP_MA=("P_SHELL", "P_NOZZLE")`).
- A **factor keyword** (`AFFE`, `DDL_IMPO`, `PRES_REP`, `EXCIT`) groups keywords inside
  `_F(...)`. Many can be repeated: give a tuple of `_F(...)`, one per occurrence, for example
  one `DDL_IMPO` occurrence per support.
- `"OUI"` and `"NON"` mean yes and no. `TOUT="OUI"` means "the whole mesh".
- Python works between commands: variables (`P = 2.0`), arithmetic, loops, `print`. The
  fixtures put every load value in a named variable at the top of the file.
- The solver checks each command against its catalog before running it. A misspelled keyword
  or a missing required one stops the run with `SUPERVIS_4` (see [the FAQ](faq.md)).

The command reference pages list every keyword of each command, with the catalog rules
("exactly one of", "at least one of") that decide which combinations are allowed.

## Groups

Every load, support, material and model assignment names its target by group:

| Keyword | English | What it holds |
|---|---|---|
| `GROUP_MA` | element group | Elements: volumes, faces, edges or point elements (`POI1`). |
| `GROUP_NO` | node group | Nodes. |
| `TOUT="OUI"` | whole mesh | Every element. |

A Gmsh physical group of any dimension arrives as an element group with the same name.
`DEFI_GROUP(CREA_GROUP_NO=_F(GROUP_MA="BASE"))` makes a node group with the nodes of an element
group, which `POST_RELEVE_T` and `TEST_RESU` need (`tests/fixtures/solid_static/input/run.comm:18`).
A group name that is not in the mesh stops the command that uses it, with `MODELISA7_77`
(`tests/fixtures/broken_missing_group`).

## Units

code_aster has no units. It uses the numbers you give, so they must form a consistent set.
Our fixtures use millimeters (`tests/fixtures/README.md`, "Units"):

| Quantity | Unit | Steel value |
|---|---|---|
| length | mm | — |
| force | N | — |
| stress, pressure, Young's modulus | MPa (N/mm²) | E = 210,000 |
| mass | tonne (t) | — |
| density | t/mm³ | ρ = 7.85e-9 |
| time | s | — |
| frequency | Hz | — |

With these units a frequency comes out in Hz with no conversion. A density entered as 7850
(kg/m³) in a millimeter model gives frequencies wrong by a factor of about 10⁶ (engineering
judgement: frequency scales as 1/√ρ, and 7850 / 7.85e-9 = 10¹²).

## Files and logical units

The export file lists one file per line: `F <type> <path> <D|R> <unit>`. `D` marks a file the
job reads (data), `R` a file it writes (result). The logical unit is how the command file
refers to the file: `LIRE_MAILLAGE(UNITE=20)` reads the line with unit 20. Our convention
(`docs/CLEARFEA-INTEGRATION.md` §3):

| Unit | File | D/R | Written or read by |
|---|---|---|---|
| 1 | `run.comm` | D | the solver (the command file itself) |
| 20 | `mesh.med` | D | `LIRE_MAILLAGE(UNITE=20)` |
| 6 | `../output/run.mess` | R | the log |
| 8 | `../output/run.resu` | R | text results (empty in our fixtures) |
| 30 to 79 | `../output/tables/<name>.csv` | R | `IMPR_TABLE(UNITE=30)` |
| 80 | `../output/run.rmed` | R | `IMPR_RESU(FORMAT="MED", UNITE=80)` |

`P` lines set parameters: `time_limit` (seconds), `memory_limit` (MB), `ncpus`. Paths are
relative to the directory `run_aster` is started in, which is `input/` in our job layout, so
outputs go to `../output/`.

## Messages: information, warnings and errors

Every message the solver prints in a box starts with its level and its ID, for example
`<A> <MODELISA8_14>`. The ID is the message family and number; look it up in
`en/messages/<FAMILY>.en.json` or in [the FAQ](faq.md). The levels
(`upstream/code_aster/Messages/Utmess.py:650`):

| Box header | Meaning | What happens |
|---|---|---|
| `<I>` | information | Nothing; read it if it concerns you. |
| `<A>` | warning (`alarme`) | The run continues, but the solver suspects a problem. Each warning ID is printed at most 5 times, then `CATAMESS_41` says it will not be shown again (`upstream/code_aster/Messages/Utmess.py:101`, `:569`); `FIN` lists every warning with its count (`CATAMESS_89`). Read each one. |
| `<E>` | error | The box says a fatal error will follow (`upstream/code_aster/Messages/Utmess.py:618`), and the run then stops. |
| `<F>` | fatal error | The run stops. |
| `<S>` | fatal error, database saved | The run stops; the steps computed so far are saved in the database (`upstream/code_aster/Messages/Utmess.py:619`). |
| `<EXCEPTION>` | error raised as a Python exception | The command stops and the Python traceback follows. `<E>` and `<F>` print as `<EXCEPTION>` when errors are raised as exceptions, which is the default in a study (`upstream/code_aster/Messages/Utmess.py:658`; [`DEBUT`](../commands/DEBUT.md) `ERREUR_F`). This is how the errors of our broken fixtures appear. |

`DEBUT(ERREUR=_F(ALARME="EXCEPTION"))` turns every warning into an error, which our fixtures
use so that a new warning cannot pass unnoticed. `DEBUT(IGNORE_ALARM=("ID",))` silences a
warning you have understood ([`DEBUT`](../commands/DEBUT.md); the two do not combine).

## Line numbers in the log

The log quotes command file lines, but not of your file: `run_aster` adds about a dozen lines
of imports after `DEBUT` and runs the changed copy (`tools/codeaster_en/mess/commlines.py`). In
`solid_static`, `LIRE_MAILLAGE` is on line 16 of `run.comm` and the log calls it line 28
(`tests/fixtures/solid_static/output/run.mess:100`). `caen mess translate` maps the numbers back
to your file ([Reading the log](reading-logs.md)).
