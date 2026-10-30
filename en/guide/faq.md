---
guide: faq
title: Warnings and errors FAQ
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
sources:
  - tests/fixtures/
  - en/messages/
  - en/commands/
  - upstream/code_aster/Messages/
doc_fr: none (our own guide, not a translation)
status: assisted
method: assisted
reviewed_by:
reviewed_on:
written_by: agent, in session (task 5.4)
---

# Warnings and errors FAQ

> **Assisted guide.** Every message on this page was printed by a real run: a committed fixture
> log, a first run recorded in the fixture notes, or a run of the walkthrough files made in
> session (task 5.4). Each entry says which. The English message texts are our translations
> (`en/messages/`), not reviewed yet. Advice on what to do is engineering judgement unless it
> cites a source. Not reviewed by an engineer.

How to use this page: find the message ID in the log (the second tag of the box header, for
example `MODELISA8_14` in `<A> <MODELISA8_14>`), then find it below. For an ID that is not
here, the English text is in `en/messages/<FAMILY>.en.json` (family = the part before the
underscore), and [Reading the log](reading-logs.md) explains how to trace it to a command.

| ID | Level | One-line meaning |
|---|---|---|
| [`SUPERVIS_22`](#supervis_22-code-and-debug-are-for-test-cases) | information | `DEBUT(CODE=...)` is for test cases |
| [`CATAMESS_89`](#catamess_89-the-list-of-warnings-at-the-end) | information | the list of warnings at the end of the run |
| [`MODELISA8_14`](#modelisa8_14-a-poi1-element-is-included-in-another-element) | warning | a point element sits on a node of another element |
| [`DISCRETS_26`](#discrets_26-a-discrete-element-has-no-mass) | warning | a discrete element (spring, remote point) has no mass assigned |
| [`MODELISA7_77`](#modelisa7_77-the-group-is-not-in-the-mesh) | error | a group named in the command file is not in the mesh |
| [`FACTOR_11`](#factor_11-the-matrix-is-singular) | error | the stiffness matrix is singular: a rigid-body motion is free |
| [`SUPERVIS_4`](#supervis_4-the-command-does-not-follow-its-catalog) | error | a command breaks its catalog rules: bad or missing keyword |
| [`SyntaxError`](#python-syntaxerror) | fatal | the command file is not valid Python |

## Information

### `SUPERVIS_22`: `CODE` and `DEBUG` are for test cases

```text
<I> <SUPERVIS_22>
The CODE and DEBUG keywords of DEBUT/POURSUITE are reserved for test cases. [...]
Do not use them in studies: they change some default values of the DEBUT/POURSUITE
commands, which affects the behavior when an error occurs and the performance.
```

**Seen in:** every fixture log, because the fixtures are test cases and use
`DEBUT(CODE="OUI", ...)` (`tests/fixtures/solid_static/output/run.mess:38`).
**What to do:** in a study, leave `CODE` out: write `DEBUT()`. With `CODE="OUI"` a fatal error
aborts the process instead of raising a Python exception ([`DEBUT`](../commands/DEBUT.md),
`CODE`). The walkthrough command file of [Walkthrough 1](walkthrough-solid-static.md) has no
`CODE`, and its run in session printed no `SUPERVIS_22`.

### `CATAMESS_89`: the list of warnings at the end

```text
<I> <CATAMESS_89>
List of the warnings issued during the analysis.
    Warnings you chose to ignore are marked with (*).
    Number of occurrences of each warning:
        (*) MODELISA8_14         issued    3 times
```

**Seen in:** every log, printed by `FIN`. In a clean run it says "aucune alarme" (none),
`tests/fixtures/solid_static/output/run.mess:433`–`:440`; in `shell_static` it lists the
ignored `MODELISA8_14` (`tests/fixtures/shell_static/output/run.mess:499`–`:505`).
**What to do:** read it on every run. It is the one place that lists every warning, including
those printed long before.

## Warnings

### `MODELISA8_14`: a `POI1` element is included in another element

```text
<A> <MODELISA8_14>
POI1 element 1 is included in another element.

This is a warning. If you do not understand what it means, you may get unexpected results!
```

**Seen in:** the four broken fixtures, three times each, by `LIRE_MAILLAGE`
(`tests/fixtures/broken_missing_group/output/run.mess:119`). They use the `shell_static` mesh
with a plain `DEBUT()`. `shell_static` itself ignores it.
**Cause:** the mesh check of `LIRE_MAILLAGE` finds a point element (`POI1`) on a node that also
belongs to another element. Gmsh writes one `POI1` for each physical point (`CENTER`,
`CORNER_A`, `CORNER_B` in `tests/fixtures/shell_static/input/mesh.geo`).
**What to do:** if the point elements are only there to name nodes, the warning is harmless.
Either ignore it, `DEBUT(IGNORE_ALARM=("MODELISA8_14",))` as `shell_static` does
(`tests/fixtures/shell_static/input/run.comm:17`), or avoid point elements: name the node in
the command file instead, for example with `DEFI_GROUP CREA_GROUP_NO OPTION="ENV_SPHERE"`
around its coordinates, as `solid_loads` does for the free end of its spring
(`tests/fixtures/solid_loads/input/run.comm:25`). If a `POI1` is meant to carry a discrete
element (a spring or a lumped mass), it is not harmless: check that it sits where you meant.

Do not combine `IGNORE_ALARM` with `ERREUR=_F(ALARME="EXCEPTION")`. The warning is turned into
an error before the ignore list is read, so the run stops anyway. This happened on the first
run of `shell_static` (comment at `tests/fixtures/shell_static/input/run.comm:11`–`:16`;
[`DEBUT`](../commands/DEBUT.md), Pitfalls).

### `DISCRETS_26`: a discrete element has no mass

```text
<A> <DISCRETS_26>
You use the mass matrix for discrete %(k1)s whereas you do not have affected
the characteristics of masses. By default the mass is null.
It is necessary to check the assignments under AFFE_CARA_ELEM/DISCRET.
```

(Machine English, from upstream's 2016 translation: "you have not assigned mass properties".)
**Seen in:** the first run of `solid_loads` (task 6.4), raised as an error because that fixture
sets `ALARME="EXCEPTION"`. Gravity (`PESANTEUR`) and rotation (`ROTATION`) loads need the mass
matrix, and the spring and the remote point had stiffness but no mass
(`tests/fixtures/README.md`, `solid_loads` notes).
**What to do:** give every discrete element a mass in `AFFE_CARA_ELEM DISCRET`, even a zero
one (`M_T_D_L` for a two-node spring, `M_T_D_N` or `M_TR_D_N` for a node). The committed
`solid_loads` run does this and prints no warning. Our `.comm` builder adds the zero masses
itself (`docs/CLEARFEA-INTEGRATION.md` §2.1, `element_properties`).

## Errors

### `MODELISA7_77`: the group is not in the mesh

```text
<EXCEPTION> <MODELISA7_77>
 GROUP_MA  EDGE  is not part of mesh:  00000001
```

**Seen in:** `tests/fixtures/broken_missing_group` (`DDL_IMPO` on `GROUP_MA="EDGE"`; the mesh
has `EDGES`; `output/run.mess:297`), and in session on Walkthrough 1 with `GROUP_MA="BASES"`.
The command that names the group stops; here `AFFE_CHAR_MECA`.
**What to do:** compare the name with the physical group names of the mesh, letter by letter.
`00000001` is the internal name of the mesh. A node group (`GROUP_NO`) must exist too: make it
from the element group with `DEFI_GROUP CREA_GROUP_NO` before using it. Before a run,
`codeaster_en.job.precheck(comm_text, mesh_path)` reports every literal group name that is not
in the `.med` file nor created by a `DEFI_GROUP` of the file (`docs/CLEARFEA-INTEGRATION.md`
§2.2).

### `FACTOR_11`: the matrix is singular

```text
Degré de liberté physique associé au noeud 87 et à la composante DX.

<EXCEPTION> <FACTOR_11>
Problem: the matrix is singular or nearly singular:
  During the factorization of the matrix, a problem was found
  (zero or nearly zero pivot) at row 517, which corresponds to the degree of freedom given above.

Risks and advice:
   * If the row is a physical degree of freedom, a rigid-body motion is probably
     not restrained.
     Check the boundary conditions.
   [...]
   * If the row is a Lagrange degree of freedom, a boundary condition is probably
     redundant.
```

**Seen in:** `tests/fixtures/broken_singular_matrix` (the supports left out of `EXCIT`;
`output/run.mess:354`–`:358`), and in session on Walkthrough 1 with the support removed from
`EXCIT`. `MECA_STATIQUE` stops while factorizing the stiffness matrix.
**What to do:** read the line just before the box. It names the degree of freedom where the
factorization failed: "physical DOF of node 87, component DX". That is where the structure is
free to move. Then check:

- every support is in the `EXCIT` list of the solve, not only defined;
- a 3D solid needs its six rigid-body motions restrained; a plate restrained only out of plane
  (`DZ`) still slides and spins in its plane (see the corners of
  [Walkthrough 2](walkthrough-shell-static.md#2-command-file));
- every part of the model is connected: two meshes that touch without sharing nodes are two
  structures (engineering judgement);
- every element group has a material and, for shells and discrete elements, element properties.

If the line before the box names a Lagrange DOF instead, two conditions fix the same DOF in
conflicting ways, for example the same node in two `DDL_IMPO` with different values.

### `SUPERVIS_4`: the command does not follow its catalog

```text
<EXCEPTION> <SUPERVIS_4>
Syntax error in AFFE_CHAR_MECA

At least one argument of ('PRES', 'CISA_2D') must be defined

The exception is detailed below.
```

**Seen in:** `tests/fixtures/broken_bad_keyword` (`PRES_REP=_F(..., PRESSION=Q)` instead of
`PRES=Q`; `output/run.mess:314`–`:318`), and in session on Walkthrough 1 with `PRESSION=P`.
The command stops before it runs; the box is printed three times, inside the Python traceback.
**What to do:** the middle line, in English already, is the catalog rule that failed. "At
least one argument of ('PRES', 'CISA_2D') must be defined" means `PRES_REP` needs `PRES` or
`CISA_2D`. Open the command's reference page, find the factor keyword, and compare the
spelling. The rule names (`AU_MOINS_UN` "at least one of", `UN_PARMI` "exactly one of",
`EXCLUS` "at most one of") are listed under "Rules" on each reference page. Our `.comm` builder
checks commands against the same catalog before the run, so its output cannot hit this error.

### Python `SyntaxError`

```text
  File "run.comm.changed.py", line 49
    _F(GROUP_MA="EDGES", DZ=0.0)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
SyntaxError: invalid syntax. Perhaps you forgot a comma?
[...]
--- DIAGNOSTIC JOB : <F>_SYNTAX_ERROR
```

**Seen in:** `tests/fixtures/broken_python_syntax` (a comma missing between two `_F(...)` of a
tuple; `output/run.mess:12`–`:22`). The log has no banner: Python could not read the file, so
no command ran.
**What to do:** the line number is that of `run.comm.changed.py`; in your file the line is
about a dozen lines earlier (`caen mess translate` gives "line 37 of the command file"). The
usual causes are a missing comma between keywords or between `_F(...)` occurrences, and an
unclosed parenthesis. `python -m py_compile run.comm` finds these without the solver, and
gives the line of your own file (line 37 for this fixture, checked in session).

## Other questions

### The log ends with "ARRET NORMAL" but the job failed

`<I> <FIN> ARRET NORMAL DANS "FIN" PAR APPEL A "JEFINI"` ("normal stop in FIN") is printed
whenever `FIN` runs, and `FIN` still runs after an error raised as an exception
(`tests/fixtures/broken_missing_group/output/run.mess:360`). Trust the job diagnostic at the
end, not this line ([Reading the log](reading-logs.md#did-the-run-succeed)).

### `PermissionError: ... run.mess` when running in Docker

Seen in session when the walkthrough was run without `--user`: the image's default user
(uid 1000) could not write to an `output/` directory owned by another user. Run the container
as yourself, `docker run --user "$(id -u):$(id -g)" -e HOME=/tmp ...`
([Walkthrough 1, step 5](walkthrough-solid-static.md#5-run)), or make `output/` writable for
uid 1000.

### The line numbers in the log do not match my file

The log quotes lines of `run.comm.changed.py`, the copy of your file that `run_aster` runs with
some lines of imports added. `caen mess translate` maps them back
([Concepts](concepts.md#line-numbers-in-the-log)).

### `ORIE_PEAU` says 0 elements were oriented

`0 MAILLE(S) ONT ETE ORIENTEE(S)` ("0 elements were oriented") means the normals already
pointed out of the solid; nothing was wrong (`tests/fixtures/solid_static/output/run.mess:167`).
Keep the command anyway: another mesher, or a later change to the geometry, can reverse them.

### Where is the English text of a message?

In `en/messages/<FAMILY>.en.json`, under the message number: `MODELISA7_77` is message `77`
of `en/messages/MODELISA7.en.json`. Each entry holds the French original (`fr`), our English
(`en`), and how it was translated (`method`: `machine` for upstream's 2016 English, `assisted`
for ours).
