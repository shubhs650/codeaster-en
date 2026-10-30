---
guide: index
title: code_aster for structural engineers
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
sources:
  - tests/fixtures/
  - en/commands/
  - en/guide/
  - docs/CLEARFEA-INTEGRATION.md
doc_fr: none (our own guide, not a translation)
status: assisted
method: assisted
reviewed_by:
reviewed_on:
written_by: agent, in session (task 5.4)
---

# code_aster for structural engineers

> **Assisted guide.** Our own English guide, written in session from the pinned command
> catalogs, our English command references, and the committed fixture runs. It is not a
> translation of an official document. Claims about what the solver does cite their source.
> Engineering advice is marked as judgement. Where a point should be checked against the
> official documentation, it says `TODO(verify)`. Not reviewed by an engineer.

This guide is for a structural engineer who knows finite element analysis from another
program and has never used code_aster. After reading it you should be able to build a linear
static or modal model, run it, find out why it failed when it does, and read the results.

code_aster is a general-purpose finite element solver written by EDF R&D and distributed under
the GPL. It has no graphical interface of its own. You describe the whole analysis in a
**command file** (`.comm`), a Python script whose commands and keywords are French
(`AFFE_MODELE`, `GROUP_MA`, `PRES_REP`). Those French names are the solver's API: this guide
explains them in English but never renames them, and every example is a file the solver
accepts as written.

## Reading order

| Page | What it covers | Read it when |
|---|---|---|
| [Concepts](concepts.md) | The pieces of a study and how they connect: mesh, model, materials, element properties, loads, load case, results, files, units | First. Everything else assumes it. |
| [Walkthrough 1: solid under pressure](walkthrough-solid-static.md) | A complete linear static study of a 3D solid, from mesh to checked result, that you can run yourself | Second. This is the one to do with your own hands. |
| [Walkthrough 2: plate in bending](walkthrough-shell-static.md) | The same steps for a shell model: thickness, normals, moment results | When you model plates or shells. |
| [Walkthrough 3: natural frequencies](walkthrough-modal.md) | A modal analysis: density, mass and stiffness matrices, modes, effective mass | When you need natural frequencies. |
| [Reading the log](reading-logs.md) | What the `.mess` log contains, how to find the problem in it, how to get it in English | The first time a run fails. |
| [Reading the results](reading-results.md) | Result objects, fields and components, tables, extrema, reactions, the English report | After your first successful run. |
| [Warnings and errors FAQ](faq.md) | Every warning and error our fixture runs have produced, what it means, what to do | When the log shows a message ID you do not know. |

Two reference pages from earlier tasks go deeper on single topics:

- [Modeling types](modelisations.md): which `MODELISATION` to choose for solids, shells,
  2D models, beams and springs.
- [Result fields](fields.md): every field name (`DEPL`, `SIEQ_NOEU`, `EFGE_NOEU`, ...) and
  component (`VMIS`, `MXX`, ...) with its English label.

Each command used in this guide has an English reference in [`en/commands/`](../commands/):
the keywords, their types and defaults, the catalog rules, and the warnings the command can
raise. The walkthroughs link to them at each step.

## What you need

| Tool | Why | Notes |
|---|---|---|
| Docker | runs the solver | We use the image pinned in `CONTAINER_IMAGE` (`simvia/code_aster:17.4.22`, ADR-011). code_aster can also be installed natively; this guide does not cover that. |
| Gmsh | makes the meshes of the walkthroughs | Version 4.15.2 wrote our fixture meshes (`tests/fixtures/README.md`). Any mesher that writes MED files with named groups works, for example Salome. |
| A results viewer | looks at the `.rmed` result file | ParaView reads MED files (with its MED reader plugin) and so does Salome. Our own `caen results` command prints extrema and reactions without a viewer. |
| `codeaster-en` (optional) | the English log, results and report tools | `pip install -e "tools[dev]"` from this repository. Not needed to run the solver. |

## Scope and limits

The guide covers what our three alpha fixtures exercise (`tests/fixtures/README.md`): linear
elastic, small-displacement statics of solids and shells, and modal analysis. It does not
cover nonlinear analysis, contact, dynamics beyond natural frequencies, thermal analysis or
fatigue. The commands it uses are the Tier 1 and Tier 2 sets of `docs/COMMAND-SET.md`.

Every number quoted from a run comes from the committed fixture outputs, produced with
code_aster 17.4.22 (the closest published image to the pinned 17.4.26 source, ADR-011). The
line numbers of upstream files refer to 17.4.26.

If you are writing code that drives code_aster rather than writing command files by hand,
read `docs/CLEARFEA-INTEGRATION.md`: the `codeaster_en.comm` builder writes these same command
files from an English Python API.
