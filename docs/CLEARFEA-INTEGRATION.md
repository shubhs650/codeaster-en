# ClearFEA integration contract

ClearFEA's solver worker is built around CalculiX first. code_aster is added as a second solver behind the same job interface. This repo is the adapter's foundation; ClearFEA holds the adapter itself. This doc fixes the boundary so both sides can be developed independently and so an agent in either repo knows what it may assume.

## 1. Division of responsibility

| Concern | codeaster-en (this repo) | ClearFEA |
|---|---|---|
| Solver binaries / container | Pins the solver image in `CONTAINER_IMAGE` (closest published image to `UPSTREAM_VERSION`, ADR-011); documents run invocation | Builds its own worker image `FROM <CONTAINER_IMAGE>` + `pip install codeaster-en` |
| Catalog knowledge (what keywords exist, types, defaults) | `codeaster_en.catalog` (from `en/commands/*.json`) | Consumes; never hard-codes keyword names outside the builder |
| Building the `.comm` | `codeaster_en.comm` typed builder (English API → French file) | Maps its UI/job model onto builder calls; owns defaults policy |
| Meshing | — (Gmsh/Netgen are ClearFEA's) | Produces `.med` (Gmsh `-format med`) with named physical groups |
| Running the solver | `codeaster_en.run` thin helper: writes `.export`, invokes `run_aster`, returns exit status + paths | Queue, metering, timeouts, cancellation, per-second billing |
| Log → English | `codeaster_en.mess` parser + renderer; live-tail capable (line-by-line) | Streams English events to the UI |
| Results access | `codeaster_en.results` (MED, tables) → extrema, reactions, modal tables | Viewer (VTK export, contours) and storage |
| English report | `codeaster_en.report` → md/html/pdf | Adds title block/logo from user profile, stores artefact |
| Failure classification | `codeaster_en.mess.classify` → `user-model | user-resources | platform | unknown` | Billing decision (user pays vs refund) and UI copy |
| Messages/docs for UI help | `en/commands/*.md`, `en/guide/` | Renders help panels; links |

## 2. Package API (target signatures, Phase 6 finalises)

```python
from codeaster_en import catalog, comm, run, mess, results, report, version

version.upstream()            # "17.2.11"
version.overlay()             # "0.3.0"

# --- catalog ---
spec = catalog.command("AFFE_CHAR_MECA")     # CommandSpec: keywords tree, types, defaults, english help
catalog.commands(tier=1)                     # list[str]
catalog.validate_comm("run.comm")            # list[Issue]  (unknown keyword, bad enum, missing required)

# --- builder ---
b = comm.Builder(units="SI_mm")
mesh = b.read_mesh("mesh.med")                           # LIRE_MAILLAGE
b.orient_faces(mesh, groups=["INNER"])                   # MODI_MAILLAGE/ORIE_PEAU
model = b.model(mesh, solids=["BODY"], shells={"PLATE": "DKT"})
steel = b.material("steel", E=200e3, nu=0.3, rho=7.85e-9)
b.assign_material({"BODY": steel, "PLATE": steel})
b.shell_thickness({"PLATE": 10.0})
b.fix("FIXED")                                           # AFFE_CHAR_CINE/MECA_IMPO
b.pressure("INNER", 2.0)                                 # PRES_REP
b.remote_force("NOZZLE", point=(0,0,500), F=(0,0,-5000), M=(0,0,0))   # RBE3 (Tier 2)
b.linear_static(outputs=["DEPL","SIEQ_NOEU","SIGM_NOEU","REAC_NODA"], reactions_on=["FIXED"])
b.write("run.comm")                                      # also returns the string

# --- run ---
res = run.run_aster(workdir, comm="run.comm", mesh="mesh.med", ncpus=4, time_limit=3600, memory_mb=8000)
res.exit_code, res.mess_path, res.rmed_path, res.tables

# --- log ---
for ev in mess.stream(res.mess_path, lang="en"):         # live tail; yields Stage/Diagnostic/Table/Summary
    ...
diag = mess.parse(res.mess_path).render("en")            # whole-file
cls  = mess.classify(diag)                               # FailureClass

# --- results ---
r = results.open(res.rmed_path)
r.fields()                                               # [("EVOL_ELAS","DEPL",[1]), ("EVOL_ELAS","SIEQ_NOEU",[1]), ...]
r.extrema("SIEQ_NOEU", "VMIS", groups=["BODY","PLATE"])  # list[Extremum(value, entity_id, xyz, group)]
r.reactions(res.tables)                                  # ReactionSummary(per_group, total, applied, balance_pct)
r.modal(res.tables)                                      # ModalTable

# --- report ---
report.build(workdir, config=report.Config(sections=..., title_block=..., logo=..., images=False), out="report")
# → report.md, report.html, report.pdf
```

All public objects are plain dataclasses, JSON-serialisable (`.to_dict()`), so ClearFEA can store them in D1/R2 and render in the browser without importing the package client-side.

## 3. Job directory layout (both sides agree)

```
<job>/
├── input/   mesh.med  run.comm  run.export  run.json
├── output/  run.mess  run.rmed  tables/*.csv  exit_code
└── report/  report.md report.html report.pdf run_model.json
```

`run.json` schema lives in `docs/schemas/run.schema.json`: title block, unit system, group display names, sections to include, solver settings requested.

## 4. Container contract

- Base: the image in `CONTAINER_IMAGE` (today `simvia/code_aster:17.4.22`, an MPI-enabled Spack build; ADR-011). `caen upstream bump` updates `CONTAINER_IMAGE` too.
- Entry: `run_aster run.export` from `input/`, with `--ncpus`, time and memory in the `.export`. ClearFEA wraps with its own timeout and cgroup limits; the `.export` limits are the inner guard.
- If ADR-004 chose gettext: the image build installs `en/messages/*.mo` and sets `LANG=en_US.UTF-8` (or whatever upstream honours) so `run.mess` is English natively; the renderer still runs for IDs and classification.
- Exit codes: `run_aster` returns 0 success, 1 solver error (`<F>`/`<EXCEPTION>`), 4 time limit, other non-zero platform; mapping is verified in Phase 4.2 and recorded in `mess/classify.py`.

## 5. Failure classification → billing

| Class | Examples (message ID or `run_aster` diagnostic; rules in `mess/classify.py`, task 4.3) | ClearFEA action |
|---|---|---|
| `user-model` | unknown group (`MODELISA7_77`), missing material on group, unoriented pressure face (warning that becomes a wrong result), singular stiffness from a missing BC (`FACTOR_11`), bad keyword in bring-your-own `.comm` (`SUPERVIS_4`), invalid Python (`<F>_SYNTAX_ERROR`) | Charge; show English message + the command reference link |
| `user-resources` | time limit (`<S>_CPU_LIMIT`), memory limit in `.export` (`<S>_MEMORY_ERROR`); from `run_aster/status.py`, no fixture yet | Charge; suggest bigger machine |
| `platform` | image missing, MED write I/O error, MPI launch failure, version mismatch between builder and solver | Refund; alert |
| `unknown` | anything untranslated/unclassified | Charge provisionally, flag for review; add rule |

Pre-run checks (`catalog.validate_comm` + mesh-group presence check against the `.med`) run before any machine is billed; these catch most `user-model` cases for free, which is the ClearFEA policy.

## 6. Versioning

- `codeaster-en` version `MAJOR.MINOR.PATCH+<upstream tag>` (PEP 440 local version, e.g. `0.3.0+17.2.11`). `MAJOR` bumps on builder API breaks.
- ClearFEA pins exact `codeaster-en` and `CONTAINER_IMAGE` together in its worker image; upgrades are a PR there, triggered by this repo's release.

## 7. What ClearFEA should not do

- Parse `.mess` or `.comm` itself. All French-touching code lives here.
- Hard-code keyword names outside `comm` builder calls (so an upstream rename is a one-place fix here).
- Show any string from the solver to a user without passing it through `mess.render("en")`.

## 8. Open items for Phase 6

- Live tailing granularity for the UI (per line vs per stage).
- Whether the builder should also target the newer `code_aster` Python API (`from code_aster.Commands import *` run in-process) instead of `.comm` + `run_aster`; `.comm` is kept for now because it is inspectable, downloadable, and version-stable.
- Parallel (MPI) image and `.export` flags for the priority tier.
