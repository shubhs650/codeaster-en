# ClearFEA integration contract

ClearFEA's solver worker is built around CalculiX first. code_aster is added as a second solver behind the same job interface. This repo is the adapter's foundation; ClearFEA holds the adapter itself. This doc fixes the boundary so both sides can be developed independently and so an agent in either repo knows what it may assume.

**Status:** final for `codeaster-en` 17.4.26.1 (task 6.3, 2026-10-29). Every signature in §2 is the built code (checked with `inspect` against the package in this repo), and the worked example in §9 runs in CI (`tests/test_clearfea_example.py`). Owner sign-off is pending (PLAN 6.3 acceptance; OWNER-REVIEW-QUEUE). Statements not yet proven by a solver run are marked `TODO(verify)`.

## 1. Division of responsibility

| Concern | codeaster-en (this repo) | ClearFEA |
|---|---|---|
| Solver binaries / container | Pins the solver image in `CONTAINER_IMAGE` (closest published image to `UPSTREAM_VERSION`, ADR-011); documents the run invocation (§4) | Builds its own worker image `FROM <CONTAINER_IMAGE>` + `pip install codeaster-en==<version>` |
| Catalog knowledge (what keywords exist, types, defaults) | `en/commands/*.json`, read by `codeaster_en.comm` (`load_command`, `CommandSpec`); every builder call is checked against it | Consumes through the builder; never hard-codes keyword names outside builder calls |
| Building the `.comm` | `codeaster_en.comm.Builder` (English API → French file, ADR-019) | Maps its UI/job model onto builder calls; owns the defaults policy |
| Meshing | — (Gmsh/Netgen are ClearFEA's) | Produces `mesh.med` (Gmsh `-format med`) with named physical groups |
| Job files and pre-run check | `codeaster_en.job`: `write_export` (logical units of §3), `precheck` (Python syntax, mesh groups) | Calls both before a machine is billed |
| Running the solver | — (the command in §4) | Queue, metering, timeouts, cancellation, per-second billing; runs `run_aster run.export` |
| Log → English | `codeaster_en.mess`: `parse`, `stream` (live tail), `translate`, `render_event` | Streams English events to the UI |
| Results access | `codeaster_en.results`: MED fields, per-group extrema, reactions, modal table | Viewer (VTK export, contours) and storage |
| English report | `codeaster_en.report`: `collect`, `build` → md/html/pdf + `run_model.json` | Adds title block/logo from the user profile, stores the artefact |
| Failure classification | `codeaster_en.mess.classify` → `user-model`, `user-resources`, `platform`, `unknown` | Billing decision (user pays vs refund) and UI copy |
| Help text for the UI | `en/commands/*.md`, `en/guide/` | Renders help panels; links |

## 2. Package API

Distribution `codeaster-en`, import `codeaster_en`, Python ≥ 3.11. Version and data paths:

```python
import codeaster_en
from codeaster_en import data

codeaster_en.__version__   # "17.4.26.1"  (<upstream tag>.<overlay serial>, ADR-020)
data.upstream_version()    # "17.4.26"    (UPSTREAM_VERSION shipped in the wheel)
data.localedir()           # Path | None: directory holding en/LC_MESSAGES/aster_messages.mo (wheel only)
data.commands_dir()        # Path: en/commands (catalog JSON + English references)
data.messages_dir()        # Path: en/messages
```

Nothing is read at import; each module reads its data on first use (ADR-020).

### 2.1 Builder — `codeaster_en.comm` (task 6.1, ADR-013, ADR-019)

`Builder()` writes one `.comm` file. Every method adds one French command, checked against the pinned catalog when it is added (unknown command or keyword, `BLOC` conditions, mandatory keywords, the catalog rules, counts, types, `into`, bounds); a bad call raises `CatalogError` or `CommSyntaxError` there, not in the solver. Methods that make a concept return a `Concept` (or a `Model`, which also knows its modelisation). `name=` overrides the generated French concept name. `Groups` is a group name or a sequence of them; `Real` is a number or a `Param`.

| Method | Command(s) written |
|---|---|
| `header(text)`, `comment(text)` | `#` comment block (file top / above the next statement) |
| `start(*, language="EN", testing=False, alarms_as_errors=False, ignore_alarms=())` | `DEBUT(..., LANG="EN")`; `language=None` leaves `LANG` out |
| `param(name, value, note=None) -> Param` | `NAME = value  # note` |
| `read_mesh(*, unit=20, name=None) -> Concept` | `LIRE_MAILLAGE(FORMAT="MED", UNITE=unit)` |
| `node_groups(mesh, *, from_groups=None, from_all_groups=False) -> Concept` | `DEFI_GROUP CREA_GROUP_NO` (node groups named after element groups) |
| `orient_skin(mesh, groups) -> Concept` | `MODI_MAILLAGE ORIE_PEAU` |
| `orient_shell_normals(mesh, group, *, normal, at_node_group) -> Concept` | `MODI_MAILLAGE ORIE_NORM_COQUE` |
| `model(mesh, kind, *, groups=None, modelisation=None, springs=(), remote_points=(), name=None) -> Model` | `AFFE_MODELE`; `kind` in `BODY_KINDS`: `solid`, `thin_shell`, `thick_shell`, `curved_shell`, `plane_stress`, `plane_strain`, `axisymmetric`; `springs` groups are modeled `DIS_T`, `remote_points` groups `DIS_TR` (ADR-022) |
| `material(name, *, E, nu, rho=None, alpha=None) -> Concept` | `DEFI_MATERIAU ELAS` |
| `assign_materials(mesh, {group or "*": material}, *, name=None) -> Concept` | `AFFE_MATERIAU` |
| `shell_properties(model, {group: thickness}, *, reference_angles=None, name=None) -> Concept` | `AFFE_CARA_ELEM COQUE` |
| `element_properties(model, *, shells=None, springs=None, reference_angles=None, name=None) -> Concept` | `AFFE_CARA_ELEM COQUE` + `DISCRET`: `springs` maps a spring group to `Spring((kx, ky, kz), to_ground=False)` (`K_T_D_L`, or `K_T_D_N`); remote points get a zero `K_TR_D_N` automatically; every discrete group must be covered |
| `fix(model, groups, *, kinematic=False, name=None) -> Concept` | all displacement (and rotation, for shells) DOF zero: `AFFE_CHAR_MECA DDL_IMPO`, or `AFFE_CHAR_CINE MECA_IMPO` with `kinematic=True` |
| `restrain(model, [Restraint({"DZ": 0.0}, groups=... or node_groups=...)], *, kinematic=False, name=None) -> Concept` | the same, per DOF |
| `pressure(model, groups, value, *, name=None) -> Concept` | `AFFE_CHAR_MECA PRES_REP` (positive acts against the element normal) |
| `hydrostatic_pressure(model, groups, *, density, free_surface, gravity=9.81, axis="Z", name=None) -> Concept` | `FORMULE` `max(rho*g*(h - Z), 0)` + `AFFE_CHAR_MECA_F PRES_REP` |
| `remote_load(model, point, faces, *, force=None, moment=None, name=None) -> Concept` | `AFFE_CHAR_MECA LIAISON_RBE3` (`DDL_ESCL="DX-DY-DZ"`) + `FORCE_NODALE` on the remote point |
| `rigid_link(model, groups, *, name=None) -> Concept` | `AFFE_CHAR_MECA LIAISON_SOLIDE` |
| `gravity(model, *, acceleration=9.81, direction=(0, 0, -1), groups=None, name=None) -> Concept` | `AFFE_CHAR_MECA PESANTEUR` |
| `rotation(model, *, speed, axis, center=(0, 0, 0), groups=None, name=None) -> Concept` | `AFFE_CHAR_MECA ROTATION` (speed in rad/s) |
| `linear_static(model, materials, loads, *, elements=None, solver="MUMPS", name=None) -> Concept` | `MECA_STATIQUE` |
| `compute_fields(result, *, stress=None, criteria=None, strain=None, forces=None, energy=None) -> Concept` | `CALC_CHAMP` (reuse) |
| `resultant(result, node_groups, *, title, field="REAC_NODA", components=("DX","DY","DZ"), name=None) -> Concept` | `POST_RELEVE_T` `RESULTANTE` table |
| `modal(model, materials, loads, *, count, elements=None, name=None) -> ModalMatrices` | `CALC_MATR_ELEM` ×2, `NUME_DDL`, `ASSE_MATRICE` ×2, `CALC_MODES` (`PLUS_PETITE`, `count` modes); `.modes` is the result |
| `normalize_modes(modes, *, norm="MASS_GENE") -> Concept` | `NORM_MODE` (reuse) |
| `filter_modes(modes, *, frequency_range=None, min_mass_fraction=None, name=None) -> Concept` | `EXTR_MODE` `FILTRE_MODE` (by `FREQ_MIN`/`FREQ_MAX` or `CRIT_EXTR="MASS_EFFE_UN"`), `IMPRESSION CUMUL="OUI"` |
| `mass_properties(model, materials, *, elements=None, name=None) -> Concept` | `POST_ELEM MASS_INER` |
| `modal_parameters(modes, *, parameters=MODAL_PARAMETERS, name=None) -> Concept` | `RECU_TABLE` (frequencies, generalized and effective masses) |
| `print_table(table, *, unit, separator=",")` | `IMPR_TABLE` to a logical unit (a CSV under `output/tables/`, §3) |
| `write_med(result, fields, *, unit=80, elements=None)` | `IMPR_RESU FORMAT="MED"` |
| `test_results([ResultCheck(...)])` | `TEST_RESU` (verification runs only) |
| `end()`; `text() -> str`; `write(path) -> str` | `FIN()`, added by `text`/`write` if missing |

Anything not covered yet (temperature loads, beams, nonlinear analyses, …) goes through the layer underneath with the same catalog checks:

```python
b.file.call("AFFE_CHAR_MECA", "LOAD", MODELE=model, PESANTEUR={"GRAVITE": 9810.0, "DIRECTION": (0.0, 0.0, -1.0)})
```

`CommandFile.call(command, result=None, *, reuse=False, result_type=None, **keywords) -> Concept | None` takes French names only; a dict is one factor-keyword occurrence (`_F`), a tuple of dicts several.

### 2.2 Job files and pre-run check — `codeaster_en.job` (task 6.3)

```python
job.write_export(job_dir, tables: Mapping[int, str] | None = None, *, time_limit_s=600, memory_mb=2048, ncpus=1) -> Path
job.export_text(tables=None, *, time_limit_s=600, memory_mb=2048, ncpus=1) -> str
job.table_units(["reactions.csv", ...]) -> {30: "reactions.csv", ...}
job.precheck(comm_text: str, mesh: Path | None = None) -> list[Problem]
# Problem(kind="syntax" | "missing_group", message, line, command, keyword, group, failure_class="user-model"); .to_dict()
```

`write_export` writes `<job>/input/run.export` with the units of §3 and creates `<job>/output/tables/`. `tables` maps the unit given to `Builder.print_table` to a file name (units 30–79). `ncpus` is threads in one process; MPI is not used yet (§8).

`precheck` runs before any machine is billed. It reports a command file that is not Python, and every literal group name given to a `GROUP_MA*` or `GROUP_NO*` keyword that is neither in `mesh.med` nor created by a `DEFI_GROUP` of the file. Against the committed broken fixtures it catches `broken_python_syntax` and `broken_missing_group` (the `MODELISA7_77` run) and passes the three good fixtures (`tests/test_job.py`). It does not follow names held in variables or check statement order; those faults still reach the solver and are classified from its log.

### 2.3 Log — `codeaster_en.mess` (tasks 4.3, 4.4)

```python
mess.parse(path, comm=None) -> ParsedLog                      # whole file; comm maps stages to .comm lines
mess.stream(path, comm=None, follow=True, poll=0.5, idle_timeout=600.0) -> Iterator[Event]   # live tail
mess.translate(log, catalog=None, exit_code=None) -> EnglishLog
mess.render_event(event, catalog: MessageCatalog) -> EnglishEvent   # one streamed event; .lines() -> list[str]
mess.classify(log: ParsedLog | None, exit_code: int | None = None) -> Classification
```

- `ParsedLog`: `.events`, `.diagnostics`, `.errors`, `.stages()`, `.summary()` (includes `exit_code`, `diagnostic_job`), `.to_dict()`, `.to_json()`.
- Events (dataclasses, `.kind`, `.lines`, `.to_dict()`): `Runner`, `Header`, `Stage` (command, concept, `comm_line`), `StageEnd` (cpu/elapsed/memory), `Diagnostic` (`severity`, `message_id` such as `MODELISA7_77`, `body`), `Notice`, `Table`, `Traceback`, `Summary`, `Text`, `Blank`.
- `EnglishLog`: `.diagnostics` (`RenderedDiagnostic`), `.problems()` (what stopped the run, as JSON-ready dicts: severity, message ID, English text, command, `.comm` line; empty for a successful run), `.coverage()`, `.classification`, `.to_text()`, `.to_json()`.
- `MessageCatalog` is `codeaster_en.mess.catalog.MessageCatalog()`; build it once per worker.
- `stream` stops after `run_aster`'s `DIAGNOSTIC JOB` trailer or after `idle_timeout` seconds without output. Granularity is one event (a diagnostic box, a command stage, a table), at most a few lines behind the writer (§8, decided).

Logs written with `DEBUT(LANG="EN")` and French logs both parse; the renderer keeps already-English boxes and translates French ones.

### 2.4 Results — `codeaster_en.results` (task 4.5, ADR-015)

```python
r = results.open(rmed_path, labels=None) -> Results            # context manager; .close()
r.fields() -> list[FieldInfo]          # result, field, label, locations, components, component_labels, steps
r.groups() -> dict[str, list[str]]     # {"node": [...], "element": [...]}
r.extrema(name, component, groups=None, nume_ordre=None, whole_model=True) -> list[GroupExtrema]
#   component: "VMIS" or a tuple ("DX","DY","DZ") for the norm; whole model first, then each group
#   GroupExtrema(field, component, label, group, nume_ordre, count, min, max: Extremum(value, entity, entity_id, xyz, node_id, point), location, note)
r.reactions(groups=None, tables=None, field_name="REAC_NODA", nume_ordre=None) -> ReactionSummary
r.modal(tables=None, result=None) -> ModalTable   # modes[Mode(nume_ordre, frequency_hz, period_s, generalized_mass, effective_mass, effective_mass_fraction, cumulative_fraction)], total_mass
r.nodal_values(name, component, nume_ordre=None) -> numpy.ndarray
results.read_table_dir(output / "tables") -> list[Table]       # IMPR_TABLE CSVs; also read_tables(path), parse_tables(text)
```

Every result object has `.to_dict()`; labels come from the glossary (`DEPL` → "Displacement").

### 2.5 Report — `codeaster_en.report` (tasks 4.6, 4.7, ADR-016, ADR-017)

```python
report.collect(job_dir, config=None) -> RunModel                          # JSON-ready (.to_dict(), .to_json())
report.build(job_dir, config=None, out=None, pdf=True) -> BuildResult     # out defaults to <job>/report
report.Config(sections=None, title_block=None, logo=None, images=False, glossary=None)
# BuildResult(model, markdown, html, run_model, pdf, warnings): paths of report.md, report.html, run_model.json, report.pdf
```

PDF needs the `report` extra (WeasyPrint + Pango); images need the `images` extra and off-screen OpenGL. `caen report <job>` is the same from the shell.

All public result objects are dataclasses with `.to_dict()`, so ClearFEA can store them as JSON and render in the browser without importing the package client-side.

## 3. Job directory layout (both sides agree)

```
<job>/
├── input/   mesh.med  run.comm  run.export  run.json
├── output/  run.mess  run.resu  run.rmed  tables/*.csv  exit_code
└── report/  report.md  report.html  report.pdf  run_model.json
```

`run_aster` runs with `input/` as working directory, so output paths in the `.export` are `../output/...`. Logical units (`codeaster_en.job` constants; the builder's defaults use the same numbers):

| Unit | File | Mode | Builder side |
|---|---|---|---|
| 1 | `run.comm` | D | — |
| 20 | `mesh.med` | D | `read_mesh(unit=20)` |
| 6 | `../output/run.mess` | R | — |
| 8 | `../output/run.resu` | R | — |
| 30–79 | `../output/tables/<name>.csv` | R | `print_table(table, unit=30)` |
| 80 | `../output/run.rmed` | R | `write_med(result, fields, unit=80)` |

`output/exit_code` holds `run_aster`'s exit status as one line, written by the worker. `run.json` (schema `docs/schemas/run.schema.json`) carries the title block, unit system, group display names, sections and solver settings; ClearFEA writes it from its job model. The report also accepts everything in one flat directory.

## 4. Container contract

- **Base image:** the line in `CONTAINER_IMAGE`, pinned by digest (today `simvia/code_aster:17.4.22`, an MPI-enabled Spack build; ADR-011; no image exists for 17.4.26). The solver is activated with `source /opt/activate.sh`; the default user is uid 1000. `caen upstream bump` (task 7.1) will update `CONTAINER_IMAGE` with `UPSTREAM_VERSION`.
- **Overlay:** `pip install codeaster-en==17.4.26.1` (version prefix = upstream tag; ADR-020). It is pure Python, so it can live in the worker image or in a separate controller; it never runs inside the solver process. TODO(verify): which Python ≥ 3.11 the worker image uses (the Spack Python of the solver image was not checked); a separate venv avoids clashing with the solver's packages. Publishing to PyPI is an owner step (OWNER-REVIEW-QUEUE); until then install the wheel built by the CI `package` job.
- **English messages (ADR-004, ADR-018):** copy `codeaster_en.data.localedir()` (holds `en/LC_MESSAGES/aster_messages.mo`) to `${PREFIX}/share/locale/aster/` in the image, or mount it there read-only; `PREFIX` is the default `RUNASTER_ROOT` of the image's `share/aster/profile.sh` (the exact lookup is in `docs/ENGLISH-LOCALE.md` and `scripts/run-fixture.sh`). `ASTER_LOCALEDIR` cannot be overridden (`profile.sh` resets it) and the system locale has no effect. The builder emits `DEBUT(..., LANG="EN")` by default. Supervisor lines (`SUPERVIS`) and the `<I> <FIN> ARRET NORMAL` line `run_aster` checks stay French; `mess.translate` covers them.
- **Entry:** from `<job>/input`, `bash -c 'source /opt/activate.sh && run_aster run.export'`; write its exit status to `<job>/output/exit_code`. ClearFEA wraps the call with its own timeout and cgroup limits; the `.export` limits (`time_limit`, `memory_limit`) are the inner guard. `scripts/run-fixture.sh` is the reference invocation (Docker, caller's uid, input read-only).
- **Exit codes:** 0 when the job diagnostic is `OK` or `<A>_ALARM`; 1 for a solver error (`<S>_ERROR`, `<F>_SYNTAX_ERROR`), seen in all four broken fixtures. Time and memory limits and crashes: `TODO(verify)` (read from upstream `run_aster/status.py`, no run yet). Classify by the log, not the exit code alone (§5).

## 5. Failure classification → billing

The worker decides in three steps:

1. **Before the run:** `job.precheck(comm, mesh)` and the builder's own checks. Any problem → reject the job as `user-model`, **no charge** (no machine time was used). This is ClearFEA's policy for faults found for free.
2. **No log at all** (`run.mess` missing or empty): `mess.classify(None)` → `platform` (image missing, launch failure).
3. **After the run:** `mess.classify(mess.parse(run.mess), exit_code)`. `failure_class is None` means success. Rules key on the first error's message ID, then on `run_aster`'s job diagnostic; each rule names its evidence (`mess/classify.py`).

| Class | Rule (message ID or job diagnostic) | Evidence | ClearFEA action |
|---|---|---|---|
| `user-model` | `MODELISA7_77` group not in mesh | `tests/fixtures/broken_missing_group` (also caught by `precheck`) | Charge; show the English problem + command reference link |
| `user-model` | `FACTOR_11` singular stiffness (missing restraint) | `tests/fixtures/broken_singular_matrix` | Charge; same |
| `user-model` | `SUPERVIS_4` command does not follow its catalog | `tests/fixtures/broken_bad_keyword` (builder output cannot hit it) | Charge; same |
| `user-model` | `<F>_SYNTAX_ERROR` not Python | `tests/fixtures/broken_python_syntax` (also caught by `precheck`) | Charge; same |
| `user-resources` | `<S>_CPU_LIMIT`, `<S>_MEMORY_ERROR` | upstream `run_aster/status.py`; TODO(verify) | Charge; suggest a bigger machine or longer limit |
| `platform` | `<F>_ABNORMAL_ABORT`; no log written | upstream `run_aster/status.py`; TODO(verify) | Refund; alert |
| `unknown` | anything else that failed | — | Charge provisionally, flag for review, add a rule here |

`Classification(failure_class, reason, message_id, diagnostic_job, evidence)`, `.failed`, `.to_dict()`. `failure_class` is a `StrEnum`, so `str()` gives the wire value above. A rule is added here (in `mess/classify.py`, with a fixture) whenever ClearFEA sees an `unknown` repeat.

## 6. Versioning

- Version `<upstream tag>.<overlay serial>`, e.g. `17.4.26.1` (ADR-020). `pip install "codeaster-en==17.4.*"` picks overlays for one solver line; the serial restarts at 1 on each upstream bump. Builder API breaks are listed in the PR and in PROGRESS; ClearFEA pins the exact version, so it never gets one silently.
- ClearFEA pins exact `codeaster-en` and `CONTAINER_IMAGE` together in its worker image; upgrades are a PR there, triggered by this repo's release.

## 7. What ClearFEA should not do

- Parse `.mess` or `.comm` itself. All French-touching code lives here.
- Hard-code keyword names outside builder calls (so an upstream rename is a one-place fix here).
- Show any string from the solver to a user without passing it through `mess.translate` / `mess.render_event`.

## 8. Decisions on the Phase 6 open items

- **Live tailing granularity:** one event (`mess.stream` + `mess.render_event`): a command stage, a diagnostic box or a table, as soon as it is complete. Stage start/end events give a progress bar; per-line streaming adds nothing the UI can label.
- **`.comm` + `run_aster`, not in-process Python:** kept (ADR-008). The file is inspectable, downloadable, version-stable, and the log parser and report rely on its line numbers.
- **MPI:** not used yet. `.export` sets `mpi_nbcpu 1`, `ncpus` is threads. The pinned image is MPI-enabled; a priority tier with `mpi_nbcpu > 1` needs a fixture run first (TODO(verify): solver choice and log layout under MPI). Recorded in OWNER-REVIEW-QUEUE.

## 9. Worked example: ClearFEA's `solver=code_aster` path

A simply supported plate under uniform pressure, end to end: build the `.comm` in English, write the job, check it, run, classify, read results, report. `run_solver` is ClearFEA's (container, queue, limits); everything else is this package. `tests/test_clearfea_example.py` runs this block with the `shell_static` fixture's mesh and committed solver output standing in for `run_solver`.

<!-- worked-example:start -->
```python
import json
import shutil
from pathlib import Path

from codeaster_en import comm, job, mess, report, results
from codeaster_en.comm import Restraint


def build_plate(pressure_mpa: float, thickness_mm: float) -> tuple[str, dict[int, str]]:
    """English job model -> French .comm text, plus the table files it writes."""
    b = comm.Builder()
    b.header("ClearFEA job: square plate, uniform pressure. Units: mm, N, MPa.")
    b.start(ignore_alarms=["MODELISA8_14"])  # DEBUT(..., LANG="EN"); point groups are POI1 cells
    mesh = b.read_mesh()  # unit 20 = input/mesh.med
    b.node_groups(mesh, from_all_groups=True)
    b.orient_shell_normals(mesh, "PLATE", normal=(0.0, 0.0, 1.0), at_node_group="CENTER")
    model = b.model(mesh, "thin_shell", groups="PLATE")  # DKT (ADR-013)
    cara = b.shell_properties(model, {"PLATE": thickness_mm})
    steel = b.material("STEEL", E=210000.0, nu=0.3)
    mate = b.assign_materials(mesh, {"PLATE": steel})
    supports = b.restrain(
        model,
        [
            Restraint({"DZ": 0.0}, groups="EDGES"),
            Restraint({"DX": 0.0, "DY": 0.0}, node_groups="CORNER_A"),
            Restraint({"DY": 0.0}, node_groups="CORNER_B"),
        ],
    )
    load = b.pressure(model, "PLATE", pressure_mpa)
    resu = b.linear_static(model, mate, [supports, load], elements=cara)
    b.compute_fields(resu, stress=("EFGE_ELNO", "EFGE_NOEU"), forces="REAC_NODA")
    tables = job.table_units(["reactions.csv"])
    reac = b.resultant(resu, "EDGES", title="REAC_EDGES")
    b.print_table(reac, unit=30)
    b.write_med(resu, ("DEPL", "EFGE_NOEU", "REAC_NODA"), elements=cara)
    return b.text(), tables


def submit(job_dir: Path, mesh_med: Path, run_json: dict, run_solver) -> dict:
    """One code_aster job; returns what ClearFEA stores (all JSON)."""
    inp = job_dir / "input"
    inp.mkdir(parents=True, exist_ok=True)
    shutil.copy(mesh_med, inp / "mesh.med")
    text, tables = build_plate(pressure_mpa=0.01, thickness_mm=10.0)
    (inp / "run.comm").write_text(text, encoding="utf-8")
    (inp / "run.json").write_text(json.dumps(run_json, indent=2), encoding="utf-8")
    job.write_export(job_dir, tables, time_limit_s=600, memory_mb=2048, ncpus=1)

    # 1. Free checks: reject without billing.
    problems = job.precheck(text, inp / "mesh.med")
    if problems:
        return {"status": "rejected", "billing": "none", "problems": [p.to_dict() for p in problems]}

    # 2. Run (ClearFEA): run_aster run.export in input/, exit status to output/exit_code.
    #    While it runs, a UI tail is: for ev in mess.stream(mess_path): render_event(ev, catalog).lines()
    exit_code = run_solver(job_dir)

    # 3. Classify and translate the log.
    mess_path = job_dir / "output" / "run.mess"
    log = mess.parse(mess_path, comm=inp / "run.comm") if mess_path.is_file() else None
    verdict = mess.classify(log, exit_code)
    if verdict.failed:
        problems = mess.translate(log, exit_code=exit_code).problems() if log else []
        billing = "refund" if verdict.failure_class == mess.FailureClass.PLATFORM else "charge"
        return {"status": "failed", "billing": billing, "classification": verdict.to_dict(), "problems": problems}

    # 4. Results for the viewer and the job summary.
    tables_out = results.read_table_dir(job_dir / "output" / "tables")
    with results.open(job_dir / "output" / "run.rmed") as r:
        peak = r.extrema("DEPL", ("DX", "DY", "DZ"))[0]  # whole model: max |U|
        reactions = r.reactions(groups=["EDGES"], tables=tables_out)

    # 5. English report.
    built = report.build(job_dir, report.Config(title_block={"author": "ClearFEA"}), pdf=False)
    return {
        "status": "ok",
        "billing": "charge",
        "classification": verdict.to_dict(),
        "max_displacement": peak.to_dict()["max"],  # value, node, xyz
        "reactions": reactions.to_dict(),
        "report": {"markdown": str(built.markdown), "html": str(built.html), "run_model": str(built.run_model)},
    }
```
<!-- worked-example:end -->

What the test checks on this path: the example's `.comm` passes `precheck` against the fixture mesh; the job returns `status: ok`; the maximum displacement is the fixture's centre deflection (2.11 mm); the reaction sum is 10,000 N (q·a²); the English report has no French tripwire words. With `EDGES` misspelled `EDGE` (the `broken_missing_group` fault), the job is `rejected` with `billing: none` and the solver is never called; with the `broken_singular_matrix` output, it is `failed`, `FACTOR_11`, `billing: charge`.
