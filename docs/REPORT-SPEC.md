# Report specification — English engineering report from a code_aster run

Purpose: turn a run directory into a report a working engineer can attach to a calculation note, with **no French anywhere**. This is the deliverable that answers "SimScale shows French" and the first runtime module ClearFEA imports. ClearFEA's own report (CalculiX today) and this one must share structure, so the section list below mirrors ClearFEA's report plan.

## 1. Inputs

A run directory produced by `run_aster` (or ClearFEA's worker) containing:

| File | Role |
|---|---|
| `*.comm` | Command file — the authoritative description of model, materials, loads |
| `*.export` | Run parameters: solver version, time/memory limits, MPI procs, file units |
| `*.mess` | Solver log — stages, diagnostics, timings, convergence tables |
| `*.rmed` / `*.med` | Results (MED/HDF5): mesh, fields by result object and time step |
| `*.csv` / `*.resu` / tables | `IMPR_TABLE` output (reactions, resultants, modal tables) |
| `run.json` (optional, ClearFEA) | Job metadata: user-facing names for groups, units chosen, title block |

Everything in the report must be traceable to one of these. The generator never computes physics; it extracts, labels, and formats. (The only arithmetic allowed: sums, extrema, percentages, unit conversion.)

## 2. Output

- `report.md` (source of truth, golden-file tested), `report.html` (Jinja2 + CSS, print-ready), `report.pdf` (WeasyPrint). Optional `report.docx` later via Pandoc.
- Deterministic: same inputs → identical `.md` (timestamps come from `run.json` or the `.mess`, not from `now()`).
- English only. CI runs a tripwire: the rendered `.md` must not contain any of the top-200 French function words/engineering terms (`le`, `la`, `les`, `des`, `maillage`, `modèle`, `contrainte`, `déplacement`, `calcul`, `erreur`, `alarme`…) outside fenced code blocks that quote the `.comm`.

## 3. Sections (all switchable via config; defaults in bold)

1. **Title block** — project/title/revision/author/date from `run.json`; logo slot; solver `code_aster <version>` and `codeaster-en <version>`; upstream tag; a one-line "analysis tool, not a compliance verdict" statement (ClearFEA positioning).
2. **Summary** — analysis type (linear static / modal / …), model size (nodes, elements by type), run outcome (completed / completed with warnings / failed), wall and CPU time, peak memory if in the log, 3–5 headline numbers (max displacement, max von Mises with location, reaction sum vs applied load check, first natural frequency).
3. **Model** — from `.comm` + MED: modeling types per group (`3D`, `DKT`…, in English with the French keyword in parentheses once), element counts per type, mesh quality if available (later), geometry extents/bounding box from MED.
4. **Materials** — table per material: name, law (`ELAS` → "linear elastic"), E, ν, ρ, α, assigned groups. Temperature-dependent properties as tables.
5. **Element properties** — shell thicknesses per group, offsets, layers (`COQUE_NCOU`), spring stiffnesses.
6. **Loads and boundary conditions** — one row per load/BC block in `.comm`: type (English), group, values, direction, load-case multiplier (`FONC_MULT`); kinematic vs dualised noted in a footnote.
7. **Solution** — solver method (MUMPS…), from `.mess`: factorisation time, number of DOF, number of Lagrange multipliers; for modal: eigen solver, shift, requested band.
8. **Results — displacements** — global max |U| and per-component extrema with node ID and coordinates; per-group extrema table if groups are flagged "report" in `run.json`.
9. **Results — stresses** — von Mises (`VMIS`), Tresca, principal (`PRIN_1..3`), per group; location (element/node, coordinates); for shells: per layer position (`SUP`/`MOY`/`INF`) stated explicitly; averaging method stated (`ELNO` vs `NOEU`).
10. **Results — reactions** — reaction resultant per constrained group (from `POST_RELEVE_T` table or `REAC_NODA` sum), applied-load resultant, balance check with percentage error. If no table was requested, say so and show what the `.comm` would need (`POST_RELEVE_T` snippet).
11. **Results — modal** — table of mode, frequency (Hz), period, effective mass per direction and cumulative %, from `POST_ELEM`/`EXTR_MODE` tables; mode shape thumbnails if images enabled.
12. **Cut lines / linearisation** (pressure-vessel users) — if `MACR_LIGN_COUPE` or `POST_RCCM` tables exist: membrane / membrane+bending / peak per line with coordinates.
13. **Diagnostics** — every `<A>`/`<E>`/`<F>` from the `.mess`, deduplicated with counts, rendered in English from `en/messages/`; each with family/number for traceability; untranslated ones shown with the ID and flagged. Grouped: warnings that affect results (e.g. unoriented pressure faces) first.
14. **Verification** — if `TEST_RESU` blocks exist: table of computed vs reference, pass/fail by the solver's own criterion. Otherwise a note that no verification checks were requested.
15. **Appendix A — command file** — the `.comm` verbatim (code block, French keywords), with an English one-line comment per command block generated from `en/commands` purpose lines.
16. **Appendix B — run parameters** — `.export` contents, English-labelled.
17. **Appendix C — full log** — the English-rendered `.mess` (optional, long).

## 4. Labels and units

- Field and component labels come from the glossary (`DEPL/DX` → "Displacement, X"; `SIEQ_NOEU/VMIS` → "von Mises stress (nodal average)"). The French name is printed once in parentheses at first use in each table header, never again.
- Units: code_aster is unit-agnostic. `run.json` declares the consistent unit system (`SI`, `SI_mm` = mm–N–MPa–tonne, …); the report prints units from that declaration. Without `run.json`, print "model units" and say which system is assumed from the magnitude of E (heuristic, flagged).
- Numbers: engineering notation, 4 significant figures by default, locations with full precision in a tooltip/footnote.

## 5. Failure reports

If the run failed, the report still generates: sections 1–7 and 13 only, with a prominent "Run failed at command `<CMD>`" line, the fatal message in English, the last 50 log lines (English), and a **cause classification** used by ClearFEA billing: `user-model` (bad group, missing material, unoriented faces, singular matrix from missing BC), `user-resources` (time/memory limit), `platform` (I/O, container, licence/version mismatch), `unknown`. Classification rules live in `tools/codeaster_en/mess/classify.py` and are keyed by message family/number; unknown IDs → `unknown`.

## 6. Implementation notes

- `report/collect.py` builds a single `RunModel` dataclass from the inputs; `report/render.py` renders templates from it. Tests target `RunModel` (JSON-serialisable, committed as golden files for each fixture).
- Parsing the `.comm` for model/material/load tables: use upstream's own command-language parser if `code_aster.Cata` imports standalone (it yields the keyword tree with values); fallback is a restricted Python AST walk (the `.comm` is Python).
- MED access: `codeaster_en.results` (task 4.5), a native `h5py` reader of the MED layout (ADR-015). It reads nodal, element-node, Gauss-point and per-element fields; a field missing from the `.rmed` (not in `IMPR_RESU NOM_CHAM`) is reported as unavailable instead of failing. Effective modal masses are not in the `.rmed`: they come from a printed `RECU_TABLE` of the modal result.
- Images (`report/images.py`): pyvista off-screen; feature-flagged; CI without GL skips and the report shows a placeholder line.
