# codeaster-en

**An English overlay for [code_aster](https://www.code-aster.org)** — EDF's open-source thermo-mechanical finite element solver — built so that engineers, contributors and AI coding agents can work with code_aster without reading French.

This repository does **not** fork or rewrite the solver. It adds, alongside a pristine copy of upstream:

| What | Where | Why |
|---|---|---|
| A controlled French → English **glossary** of commands, keywords, values and terms | `en/glossary.yaml` | Single source of truth that every other translation must obey |
| **English-annotated command references** (schema + meaning + examples) for the commands a structural engineer actually uses | `en/commands/` | The LLM-ready "API spec" of the solver |
| **English message catalogue** (warnings, errors, alarms) keyed by upstream message ID | `en/messages/` | So users and agents never see a French diagnostic |
| **English reference docs** for the same command set, translated from the official U-docs with the glossary enforced | `en/docs/` | Better than the official machine translation |
| A Python package `codeaster_en` with extraction, validation, `.mess` log translation and an **English engineering report generator** | `tools/` | Runtime layer: French in, English out |
| Example runs with committed outputs (solid static, shell static, modal) | `tests/fixtures/` | Deterministic test data; no solver build needed to develop here |

The solver itself lives in a sibling repository, `code_aster` (a plain GitHub mirror of `gitlab.com/codeaster/src`, kept in sync by a GitHub Action), and is pinned here as the `upstream/` git submodule.

## Status

Pre-alpha. See [`docs/PLAN.md`](docs/PLAN.md) for phases and [`docs/PROGRESS.md`](docs/PROGRESS.md) for where things stand.

## Who this is for

- **ClearFEA** — this repo is the code_aster adapter layer for the ClearFEA cloud platform (CalculiX first, code_aster second). The contract is in [`docs/CLEARFEA-INTEGRATION.md`](docs/CLEARFEA-INTEGRATION.md).
- Anyone running code_aster who wants English diagnostics and English reports.
- Anyone pointing an LLM at code_aster: `caen bundle --tier 1` writes our guide, the Tier 1 command references and the glossary as one Markdown file that fits a 200k-token context window (ADR-025). The latest build is attached to the `llm-bundle` pre-release on GitHub.

## Principles (short version)

1. **Upstream is untouchable.** No edits to solver source. Everything English is an overlay.
2. **French keywords stay French.** `AFFE_MODELE` is the API. We explain it; we don't rename it.
3. **Translate only what is used.** Scope is driven by [`docs/COMMAND-SET.md`](docs/COMMAND-SET.md), not by the size of the codebase.
4. **Glossary is law.** A term is translated one way, everywhere.
5. **Every translation carries provenance and review status.** Machine-translated until a human says otherwise.

## Quick start (tooling only — no solver build)

```bash
git clone --recurse-submodules https://github.com/<org>/codeaster-en
cd codeaster-en
python -m venv .venv && source .venv/bin/activate
pip install -e tools[dev]
caen --help
pytest
```

## Licence

code_aster is GPL. This overlay — translations, tooling, docs — is released under **GPL-3.0-or-later** to stay compatible. Translated documentation retains EDF R&D attribution and the original document identifiers. See [`docs/LICENSING.md`](docs/LICENSING.md).

code_aster is a trademark of EDF. This project is not affiliated with or endorsed by EDF.
