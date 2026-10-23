# Architecture — codeaster-en

## 1. Problem statement

code_aster is the strongest open-source structural solver available (shells, contact, nonlinear, 3800+ validated test cases, 20,000 pages of documentation), and it is almost entirely in French: command keywords, catalog help strings, diagnostics, log files, documentation. Three groups suffer:

1. **End users** of a platform built on it see French warnings and French reports (SimScale ships French output verbatim).
2. **Contributors** who don't read French cannot tell what a keyword does without the French U4 doc.
3. **LLM coding agents** are far less reliable when the reference material is French, and the official machine-translated English is unreliable precisely where precision matters (keyword semantics).

Translating the solver source is not an option: it is ~1.5 million lines, moves continuously, and its French keywords *are* its public API. Renaming them would orphan every test case, doc and forum answer — the body of validation that is the reason to choose code_aster at all.

## 2. Approach: a sidecar overlay

Everything English lives **beside** the solver, keyed to upstream identifiers that never change (command names, keyword paths, message family + number, doc IDs). Upstream is consumed read-only and re-pinned on a schedule.

```
┌──────────────────────────────── github.com/<org> ─────────────────────────────────┐
│                                                                                   │
│  code_aster  (mirror repo)            codeaster-en  (this repo)                   │
│  ───────────────────────              ───────────────────────────────────────     │
│  branch main ← gitlab main            upstream/  ──submodule──▶ code_aster@<tag>  │
│  tags       ← gitlab tags             en/        glossary, commands, messages,    │
│  synced nightly by Action                        docs, guide                      │
│  never edited by humans               tools/     codeaster_en package + caen CLI  │
│                                       tests/     fixtures from docker runs        │
│                                       docs/      this folder                      │
└───────────────────────────────────────────────────────────────────────────────────┘
                                                        │
                                                        ▼ pip install codeaster-en
                                       ClearFEA solver worker (code_aster adapter)
```

### Why two repos and a submodule, not one fork

| Option | Upstream sync | Repo size seen by agents | Merge conflicts | LLM context noise |
|---|---|---|---|---|
| Single fork, overlay committed in-tree | `git merge upstream` — works, but any shared file (README, CI config) conflicts forever | Huge (Fortran, tests, history) | Yes, recurring | High |
| **Mirror repo + overlay repo with submodule (chosen)** | Bump the submodule pointer; zero conflicts by construction | Overlay is tiny; upstream only materialises when checked out | None | Low |
| Overlay repo, no submodule, fetch on demand | Same as above, but reproducibility depends on network | Tiny | None | Low, but sandbox network blocks gitlab |

The chosen layout also gives the owner's original wish — "copy the GitLab repo to GitHub" — as a first-class artefact: `github.com/<org>/code_aster` is a faithful, automatically synchronised mirror that anyone (and the sandbox) can clone.

### Why not AsterStudy / Salome-Meca

AsterStudy is the Salome GUI module that builds `.comm` files; Salome-Meca is the desktop bundle. ClearFEA has its own web UI and meshes with Gmsh/Netgen directly. We take exactly two things from AsterStudy: its existing French→English translation dictionary (seed for our glossary) and, as reading material, how it launches the solver. Nothing is translated or vendored from it.

## 3. Upstream anatomy (what we read, verified in Phase 0)

The pinned upstream (`UPSTREAM_VERSION`) is the latest stable tag on the mirror at bootstrap time. Expected structure (post-15.2 "pythonic" layout):

- `code_aster/Cata/Commands/<cmd>.py` — one Python file per command, built with the `Syntax` DSL (`OPER`, `MACRO`, `SIMP`, `FACT`, `BLOC`): keyword names, types (`'R'`, `'I'`, `'TXM'`, concept types), cardinality, defaults, allowed values (`into=`), and French `fr=` help strings. **This is the solver's API specification** and the primary extraction source.
- `code_aster/Cata/Language/` — the DSL itself; importable as pure Python without building the solver (verify). If so, extraction = import catalog, walk the object tree.
- `code_aster/Messages/<family>.py` — `cata_msg = {1: _("""French text with %(k1)s ..."""), ...}`. Families are upper-case names (`MECANONLINE`, `CALCULEL`, `MODELISA`, ...). The `.mess` log prints `<FAMILY_N>` next to each diagnostic, which is our join key.
- `code_aster/Utilities/` — look for gettext/localisation machinery. **If upstream already wraps messages in gettext and honours a locale, an English `.po/.mo` catalog makes the solver itself emit English, and the runtime translator becomes a fallback only.** Phase 1 task 1.1 settles this.
- `astest/<name>.comm|.export|.mail|.med|.com0…` — test cases. Each `.comm` is a worked example; the astest index maps command → test cases that use it, so every command reference can cite real examples.
- `doc/` — developer docs (build, waf). Not user docs; user docs are PDFs on code-aster.org and must be attached by the owner (network-blocked in the sandbox).
- `bibfor/`, `bibc/`, `bibcxx/`, `catalo/`, `waftools/` — solver internals. Never read beyond curiosity.

## 4. The overlay, layer by layer

### 4.1 Glossary — `en/glossary.yaml`

The controlled vocabulary. One entry per French identifier or term:

```yaml
- fr: GROUP_MA
  en: element group
  kind: keyword            # command | keyword | value | concept | term | abbrev
  note: "MA = maille (element). GROUP_NO is the node-group counterpart."
  status: reviewed         # proposed | machine | reviewed
  aliases_en: [cell group]  # strings we must NOT use; listed so the validator can flag them
```

Optional `source` records provenance as `<path under upstream/>:<line>` where the identifier is defined in the pinned catalog (added from task 0.6 on; `tests/test_glossary_coverage.py` checks it resolves).

Rules: a `fr` key appears once; `en` is the only permitted translation; `aliases_en` are forbidden synonyms. Seeded from AsterStudy's dictionary plus the terms in `docs/COMMAND-SET.md`; grows by PR. The validator greps every English artefact for forbidden synonyms and for French terms that have no entry.

### 4.2 Command references — `en/commands/<COMMAND>.{json,md}`

- `.json` is **generated** by `caen extract catalog` from the pinned upstream: full keyword tree, types, defaults, cardinality, allowed values, French `fr=` strings, source file + line, upstream tag.
- `.md` is **written** (LLM-drafted, engineer-reviewed): purpose in one paragraph; keyword table (French keyword · type · default · English meaning · when to use); common patterns; pitfalls; links to translated doc ID and 2–3 astest examples; `status` and provenance header.
- A `caen check commands` step verifies every keyword in the `.md` table exists in the `.json` (no invented keywords) and every required keyword is covered.

These two files per command are what an LLM gets as context when asked to write a `.comm`.

### 4.3 Message catalogue — `en/messages/<FAMILY>.en.json`

```json
{
  "_generated_from": {"upstream": "17.2.11", "file": "code_aster/Messages/mecanonline.py"},
  "family": "MECANONLINE",
  "messages": {
    "20": {
      "fr": "...%(k1)s...",
      "en": "...%(k1)s...",
      "severity_hint": "warning",
      "method": "machine",
      "reviewed_by": null
    }
  }
}
```

Produced in bulk by `caen translate messages` (LLM, glossary-locked, placeholder-validated), reviewed selectively: families that fire during the in-scope analyses get an engineer's pass. If Phase 1 confirms gettext support, the same data is also emitted as `en/messages/codeaster_en.po` so the solver can print English natively.

### 4.4 Documentation — `en/docs/<DOC-ID>.md` and `en/guide/`

- `en/docs/` — translations of official U-docs for in-scope commands (U4.xx.yy reference pages, plus the handful of U1/U2 usage docs an engineer needs). Input: PDFs attached by the owner, converted to text, chunked, translated with the glossary, re-assembled. Header keeps EDF attribution, doc ID, upstream doc version, our translation status.
- `en/guide/` — our own short English guide: "code_aster for a structural engineer": concepts (concept/SD, model, material field, element characteristics, loads vs boundary conditions, result objects and field names, logical units), a minimal linear-static walkthrough, a shell walkthrough, a modal walkthrough, reading the `.mess` log, reading results. Written from the command references, not translated.

### 4.5 Runtime: `.mess` parser and English renderer — `tools/codeaster_en/mess/`

The `.mess` file is the solver's log. The parser produces a structured list of events: timestamped stages (command start/end with CPU/elapsed), diagnostics (`<A>` alarm/warning, `<E>`/`<F>` errors, `<EXCEPTION>`, each with `<FAMILY_N>` and the rendered French text), convergence tables for nonlinear runs, final summary. The renderer looks up `FAMILY_N` in `en/messages/`, formats the English template with the same arguments (recovered by diffing French template vs printed text, or, preferably, from the solver's own structured output if gettext/JSON logging exists), and emits English events. Unknown IDs are rendered as `[FAMILY_N] <original French>` with a `untranslated: true` flag so they are visible and never silently dropped.

### 4.6 Results readers — `tools/codeaster_en/results/`

Thin wrappers over `medcoupling` (pip wheels exist) with a `meshio` fallback: open `.rmed`, list results and fields, map French field names (`DEPL`, `SIEQ_NOEU`, `SIGM_ELNO`, `REAC_NODA`, `EFGE_ELNO`) and components (`DX`, `VMIS`, `SIXX`, `TRESCA`) to English labels via the glossary; extract per-group extrema; read `IMPR_TABLE` outputs (CSV/ASTER format) into dataframes. No plotting here; images are optional and come later via pyvista.

### 4.7 English report generator — `tools/codeaster_en/report/`

Input: a run directory (`.comm`, `.export`, `.mess`, `.rmed`, tables). Output: a structured engineering report (Markdown → HTML → PDF via WeasyPrint) in English only. Content spec is `docs/REPORT-SPEC.md`. This is the piece that directly fixes the "SimScale shows French" problem and is the first runtime deliverable ClearFEA consumes.

### 4.8 Command-file builder — `tools/codeaster_en/comm/` (Phase 6)

A typed Python builder with English method names that emits a French `.comm`:

```python
m = Model.from_med("mesh.med")                       # LIRE_MAILLAGE + AFFE_MODELE
m.assign_solid(group="ALL", modelisation="3D")
m.material("steel", E=200e9, nu=0.3, rho=7850).assign_to("ALL")
m.fix(group="FIXED")                                  # AFFE_CHAR_MECA DDL_IMPO
m.pressure(group="INNER", value=2.0e6)                # PRES_REP
m.linear_static()                                     # MECA_STATIQUE + CALC_CHAMP + IMPR_RESU
m.write("run.comm")
```

Every method is validated against `en/commands/*.json` at build time, so the builder cannot emit a keyword the pinned upstream doesn't know. ClearFEA's code_aster adapter is a client of this builder.

## 5. Upstream synchronisation

**Mirror repo** `code_aster` — `.github/workflows/sync-upstream.yml` (in `mirror-repo/` here, copied into that repo): nightly `git fetch` from GitLab, force-update `main` and tags, push. The initial copy can be done with GitHub's "Import repository" from `https://gitlab.com/codeaster/src.git`, or by running the same workflow once with `workflow_dispatch`. Check for blobs > 100 MB before the first push (`git rev-list --objects --all | git cat-file --batch-check` → sort by size); if any exist, mirror `main` only or route them through Git LFS.

**Overlay repo** — `caen upstream bump --to <tag>`: updates the submodule, writes `UPSTREAM_VERSION`, re-runs extraction, and produces a diff report: commands/keywords added, removed, or changed; messages added, removed, or whose French text changed (those are marked `stale` in the English catalogue). This diff is the Phase 7 maintenance loop; it is deliberately mechanical so an agent can do it.

## 6. Testing without building the solver

- **Unit tests** (`tests/test_*.py`): extractor against a committed snapshot of a few catalog files; validator rules; `.mess` parser against fixture logs; report generator against fixture runs; builder round-trips (emit `.comm` → parse back → equal).
- **Fixtures** (`tests/fixtures/<case>/`): three reference cases chosen to cover the alpha scope — `solid_static` (nozzle-in-shell block, 3D tets, pressure + fixed), `shell_static` (DKT/COQUE_3D plate, pressure + simply supported), `modal` (cantilever, first 6 modes). Each has `.comm`, `.export`, mesh `.med`, and the outputs the solver produced: `.mess`, `.rmed`, tables. Outputs are produced by running the official `codeastersolver/codeaster-seq` image with `scripts/run-fixture.sh`, either in a Claude Code cloud session (Docker is available there) or in the **`solver-fixtures.yml`** GitHub Action, and are committed. Unit tests read the committed outputs, so they never need Docker or the solver.
- **Physics sanity** lives in the fixture `.comm` files themselves (`TEST_RESU` against hand values), so a fixture that fails upstream's own test is rejected by the Action.
- **CI** (`ci.yml`): ruff + pytest + `caen validate` on every PR; `solver-fixtures.yml` on demand and on upstream bump.

## 7. Interfaces exposed to ClearFEA

See `docs/CLEARFEA-INTEGRATION.md`. In one line: `pip install codeaster-en` gives `catalog`, `messages`, `mess`, `results`, `report`, `comm` as importable modules plus the `en/` data as package data; ClearFEA's worker never parses French.

## 8. Non-goals

- Translating Fortran/C/C++ source, element catalogs, or test-case comments.
- Translating any command outside `docs/COMMAND-SET.md` tiers in play.
- Building or packaging the solver (use official containers).
- A GUI. AsterStudy is not replaced here; ClearFEA is the UI.
- Theory (R) and validation (V) docs. Link to the French originals.
