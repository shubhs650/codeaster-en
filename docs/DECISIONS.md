# Decisions (ADR log)

Format: ID, date, status, decision, why, consequences. Append; never rewrite history — supersede with a new entry.

---

## ADR-001 — Overlay, not fork; no source translation
**Date:** 2026-10-22 · **Status:** accepted

**Decision.** code_aster source is consumed read-only as a pinned submodule. English material is a sidecar keyed by stable upstream identifiers (command names, keyword paths, message family+number, doc IDs). No identifier is ever renamed.

**Why.** ~1.5 M lines, continuous upstream change, French keywords are the public API that every test case, doc and forum answer depends on. A translated fork cannot merge upstream and loses the validation corpus — the reason to choose code_aster.

**Consequences.** Upstream bumps are a submodule pointer change plus a mechanical diff. Agents must never write under `upstream/`. LLM-friendliness comes from English *explanations* and a glossary, not English identifiers.

---

## ADR-002 — Two repos: `code_aster` (mirror) + `codeaster-en` (overlay)
**Date:** 2026-10-22 · **Status:** accepted

**Decision.** `github.com/<org>/code_aster` is a plain, action-synchronised mirror of `gitlab.com/codeaster/src` (never edited). `codeaster-en` references it as a submodule pinned to a stable tag.

**Why.** Keeps the overlay small and conflict-free; the Claude Code cloud sandbox can reach GitHub but not GitLab; fulfils "copy the GitLab repo to GitHub" as a reusable public artefact.

**Consequences.** Need the sync workflow and an initial import; blob-size check before first push; two repos to administer.

---

## ADR-003 — Scope is driven by `docs/COMMAND-SET.md` tiers
**Date:** 2026-10-22 · **Status:** accepted

**Decision.** Only commands/messages/docs in the active tier get English prose. Catalog and message *extraction* runs over everything (cheap, needed for diffs).

**Why.** Thousands of keywords and ~10k messages exist; most are irrelevant to a structural platform. Translating only what is used keeps review feasible and quality high.

**Consequences.** Users of exotic commands get French; the runtime renderer shows the ID and original text rather than hiding it.

---

## ADR-004 — Message strategy: gettext catalog vs runtime mapping
**Date:** — · **Status:** proposed (resolved in Phase 1, task 1.1)

**Options.** (a) Runtime only: parse `.mess`, map `FAMILY_N` → English. Works with any image, no solver change. (b) If upstream wraps messages in gettext and honours a locale, ship an English `.po/.mo`; solver prints English natively; runtime renderer remains for IDs/classification and as fallback.

**Leaning.** (b) if feasible because it also fixes messages that escape to stdout/exception text; (a) always exists regardless.

---

## ADR-005 — Report is generated from artefacts, never from physics
**Date:** 2026-10-22 · **Status:** accepted

**Decision.** `codeaster_en.report` extracts, labels, sums and formats; it never computes stresses, linearises, or judges compliance. Anything not in the run outputs is absent from the report, with a note saying what to request in the `.comm`.

**Why.** Traceability for an engineering document; ClearFEA's "analysis tool, not a verdict" positioning; keeps the module testable with golden files.

---

## ADR-006 — Translation provenance and status are mandatory fields
**Date:** 2026-10-22 · **Status:** accepted

**Decision.** Every English artefact carries upstream tag, source location, `method` (`machine` / `assisted` / `reviewed`), reviewer, date; stale-on-upstream-change is tracked by the bump tool.

**Why.** Machine translations will be wrong sometimes; users and agents must be able to tell what has been checked by an engineer.

---

## ADR-007 — Licence: GPL-3.0-or-later for the overlay
**Date:** 2026-10-22 · **Status:** accepted (owner to confirm after reading upstream licence headers)

**Decision.** Tools, translations and own docs under GPL-3.0-or-later; translated official docs carry EDF attribution and the original doc ID and are treated as derivative works of EDF's documentation.

**Why.** Message translations are derivative of GPL source; GPL-3.0-or-later is compatible with ClearFEA's AGPL-3.0. See `docs/LICENSING.md`.

---

## ADR-008 — Builder emits `.comm` files, not in-process Python API calls
**Date:** 2026-10-22 · **Status:** accepted for Phase 6, revisit later

**Decision.** `codeaster_en.comm` produces a textual `.comm` run by `run_aster`, even though modern code_aster can be driven in-process from Python.

**Why.** A `.comm` is a downloadable, inspectable, version-stable artefact (ClearFEA's "view/download the solver input" requirement), is what the test corpus is written in, and keeps the worker process isolated from the solver process.

---

## ADR-009 — Salome-Meca / AsterStudy are not vendored or translated
**Date:** 2026-10-22 · **Status:** accepted

**Decision.** Only AsterStudy's translation dictionary is used (as glossary seed, with attribution). Nothing else from Salome is a dependency.

**Why.** ClearFEA has its own UI and meshing; the Salome desktop stack is heavy and unnecessary in a cloud worker.

---

## Template

## ADR-NNN — <title>
**Date:** YYYY-MM-DD · **Status:** proposed | accepted | superseded by ADR-MMM

**Decision.** …

**Why.** …

**Consequences.** …
