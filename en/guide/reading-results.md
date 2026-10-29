---
guide: reading results
title: Reading the results
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
sources:
  - tests/fixtures/
  - tools/codeaster_en/results/
  - tools/codeaster_en/report/
  - en/guide/fields.md
doc_fr: none (our own guide, not a translation)
status: assisted
method: assisted
reviewed_by:
reviewed_on:
written_by: agent, in session (task 5.4)
---

# Reading the results

> **Assisted guide.** Written from our fixture outputs and the `caen results` and `caen report`
> tools. Advice on checking results is engineering judgement. Not reviewed by an engineer.

A run leaves its numbers in two places: the **result file** (`output/run.rmed`, MED format),
which holds whole fields over the mesh, and the **tables** (`output/tables/*.csv`), which hold
the values you extracted with `POST_RELEVE_T`, `POST_ELEM` or `RECU_TABLE`. Neither is written
unless the command file asks: only the fields listed in `IMPR_RESU` reach the result file, and
only the tables printed with `IMPR_TABLE` reach a CSV.

## What is in a result

A result object holds steps, each step holds fields, each field holds components
([Result fields](fields.md) has the full list and every English label):

| Level | Static example (`solid_static`) | Modal example (`modal`) |
|---|---|---|
| result object | `RESU`, linear static result (`EVOL_ELAS`) | `MODES`, modal result (`MODE_MECA`) |
| step | one step, `INST` = 0 | six steps, one per mode, with `FREQ` |
| field | `DEPL`, `SIGM_NOEU`, `SIEQ_NOEU`, `REAC_NODA` | `DEPL` (the mode shapes) |
| component | `DX`, ...; `SIXX`, ...; `VMIS`, `TRESCA`, ...; `DX`, ... | `DX`, `DY`, `DZ` |

`caen results fields` lists them from the file:

```console
$ caen results fields tests/fixtures/solid_static/output/run.rmed
RESU DEPL (displacement): at nodes
  components: DX, DY, DZ
  steps (NUME_ORDRE, INST or FREQ): 1 (0)
RESU REAC_NODA (nodal reactions): at nodes
  components: DX, DY, DZ
  steps (NUME_ORDRE, INST or FREQ): 1 (0)
RESU SIEQ_NOEU (equivalent stress (nodal average)): at nodes
  components: VMIS, TRESCA, PRIN_1, PRIN_2, PRIN_3, VMIS_SG, VECT_1_X, VECT_1_Y, VECT_1_Z, VECT_2_X, VECT_2_Y, VECT_2_Z, VECT_3_X, VECT_3_Y, VECT_3_Z, TRSIG, TRIAX
  steps (NUME_ORDRE, INST or FREQ): 1 (0)
RESU SIGM_NOEU (stress (nodal average)): at nodes
  components: SIXX, SIYY, SIZZ, SIXY, SIXZ, SIYZ
  steps (NUME_ORDRE, INST or FREQ): 1 (0)
node groups: BASE
element groups: BASE, NOZ_END, P_NOZZLE, P_SHELL, SOLID, TOP
```

The field name tells you where the values live: `_NOEU` at nodes (averaged over the elements
around each node), `_ELNO` at the nodes of each element (not averaged, so it shows the jump
between elements), `_ELGA` at Gauss points. `DEPL` and `REAC_NODA` are nodal without a suffix.
A shell model adds rotations `DRX`, `DRY`, `DRZ` to `DEPL` and has `EFGE_NOEU` (forces and
moments per unit length) instead of stresses.

## Looking at fields in a viewer

Open `run.rmed` in Salome (ParaVis) or in ParaView with a MED reader. Each field appears under
the name `<result>____<field>`, the result name padded to 8 characters with underscores
(`RESU____SIEQ_NOEU`; the names are chosen by `IMPR_RESU`, see the command echo at
`tests/fixtures/solid_static/output/run.mess:385`). `TODO(verify)` which ParaView builds read
MED files without Salome.

What to look at first (engineering judgement):

1. **The deformed shape** (`DEPL`, scaled). Does it move the way the loads push it? Are the
   supports holding where they should, and nowhere else?
2. **The displacement magnitude.** Is the order of magnitude plausible?
3. **Equivalent stress** (`SIEQ_NOEU`, `VMIS`). Where are the peaks? A peak at a re-entrant
   corner, a point support or a point load is a singularity: it grows without limit as the mesh
   is refined, and its value means nothing. A peak at a smooth notch, such as the nozzle
   corner of Walkthrough 1, converges with refinement, and you must refine to find it.
4. **Averaged against unaveraged stress.** Compare `SIGM_NOEU` with `SIGM_ELNO` at the peak.
   A large difference means the mesh is too coarse there.

## Numbers without a viewer: `caen results`

`caen results` reads `run.rmed` and the tables with English labels. Give it the result file or
the job's `output/` directory.

**Extrema**, over the whole model and per group, with the node and its coordinates:

```console
$ caen results extrema tests/fixtures/solid_static/output SIEQ_NOEU VMIS -g P_NOZZLE -g BASE
SIEQ_NOEU von Mises (VMIS), whole model (step 1, 4622 values):
  min 2.135 at node 1810 (140.6, -0.0818181, 115)
  max 34.74 at node 9 (100, -9.18485e-15, 175)
SIEQ_NOEU von Mises (VMIS), P_NOZZLE (step 1, 652 values):
  min 3.251 at node 4363 (105.878, 24.9984, 149.715)
  max 34.74 at node 9 (100, -9.18485e-15, 175)
SIEQ_NOEU von Mises (VMIS), BASE (step 1, 144 values):
  min 6.11 at node 4 (120, -2.93915e-14, 0)
  max 12.12 at node 255 (-10.4528, -99.4522, 0)
```

Several components give their magnitude: `caen results extrema output DEPL DX DY DZ`.
`--step N` picks a step (the last by default), `--json` prints JSON.

**Reactions**, summed from `REAC_NODA` and from any printed table:

```console
$ caen results reactions tests/fixtures/shell_static/output
all supports (RESU____REAC_NODA): DX 0, DY 0, DZ 1e+04, DRX 2.189e-09, DRY 4.3e-09, DRZ 0
table:reactions.csv:REAC_EDGES: DX 0, DY 0, DZ 1e+04
```

**Modal table**, frequencies, periods and effective mass fractions with their running sums
([Walkthrough 3](walkthrough-modal.md#4-check-the-result)):

```console
$ caen results modal tests/fixtures/modal/output
```

## Tables

`IMPR_TABLE(FORMAT="TABLEAU", SEPARATEUR=",")` writes a CSV with three header lines before the
column names. The column names are French keywords:

```text
#
#--------------------------------------------------------------------------------
##ASTER 17.04.22 CONCEPT 0000002a CALCULE LE 29/10/2026 A 02:15:32 DE TYPE
INTITULE,RESU,NOM_CHAM,NUME_ORDRE,INST,DX,DY,DZ
REAC_BASE       ,00000007,REAC_NODA       ,           1, 0.00000E+00, 3.89164E+03,-1.77693E-10, 1.27073E-10
```

(`tests/fixtures/solid_static/output/tables/reactions.csv`; the third line says "computed on
29/10/2026 at 02:15:32".) Skip the lines starting with `#` to read it as a spreadsheet.

| Column | English | Meaning |
|---|---|---|
| `INTITULE` | label | The `INTITULE` you gave in `POST_RELEVE_T`. |
| `RESU` | result | Internal name of the result object. |
| `NOM_CHAM` | field name | The field the values come from. |
| `NUME_ORDRE` | step index | The step. |
| `INST` | time step | The time of the step (0 for a single static step). |
| `DX`, `DY`, `DZ` | X, Y, Z translation | Here, with `RESULTANTE`, the sum over the group: the reaction resultant. |

The mass table of `POST_ELEM MASS_INER` (`tests/fixtures/modal/output/tables/mass_inertia.csv`)
has `MASSE` (mass), `CDG_X`, `CDG_Y`, `CDG_Z` (center of gravity), `IX_G` ... `IYZ_G` (inertia
about the center of gravity), and principal inertias and their angles. `caen results` and the
report give these columns English labels.

## Checks to make on every result

These are engineering judgement, and the report generator makes the first one for you.

| Check | How | In our fixtures |
|---|---|---|
| Equilibrium | Sum of reactions = − applied resultant, in every direction | `solid_static` 3891.64 N; `shell_static` 10,000 N = q a² |
| Hand value | One quantity you can estimate by hand: a membrane stress, a beam deflection, a first frequency | Mean hoop stress 10.0 MPa ([Walkthrough 1](walkthrough-solid-static.md#7-check-the-result)); Navier plate; cantilever frequencies |
| Mass | `POST_ELEM MASS_INER` against the mass you expect | `modal`: 6.28e-4 t |
| Mesh | Refine, or switch to quadratic elements, and compare the quantities you report | `solid_static` peak 34.7 → 46.7 MPa with `TETRA10` |
| Warnings | `FIN` lists none, or only ones you understand and ignore on purpose | all fixtures |

## The English report

`caen report <job>` writes an engineering report from a job directory (`input/` with `run.comm`,
`run.export` and `run.json`, plus `output/`): title block, model, materials, loads and
supports, solution settings, displacement, stress and reaction tables, an equilibrium check,
the solver diagnostics and the command file. `run.json` (`docs/schemas/run.schema.json`) gives
the title, the unit system and an English display name for each group.

```bash
caen report tests/fixtures/solid_static --out report --no-pdf
```

Every value in the report names its source (log, result file or command file). The report says
what the solver computed; it does not judge compliance with a design code. Options: `--log`
adds the English log as an appendix, `--images` adds pictures of the deformed shape, von Mises
stress and mode shapes (needs `pyvista`), `--no-pdf` skips the PDF (which needs WeasyPrint).
The report layout is specified in `docs/REPORT-SPEC.md`.
