# Translation guide

This governs every English artefact in `en/` whether written by a person, an LLM in a Claude Code session, or the batch translator. The validator (`caen validate`) enforces what it can; the rest is review discipline.

## 1. What is translated, what is not

| Artefact | Translate? | Form |
|---|---|---|
| Command / keyword / value identifiers (`AFFE_MODELE`, `GROUP_MA`, `'OUI'`) | **Never** | Kept verbatim; explained in prose |
| Catalog `fr=` help strings | Yes | `en/catalog-help.yaml` (translation memory, ADR-012), shown in the `.md` table |
| Message texts (`cata_msg`) | Yes | `en/messages/*.en.json`, placeholders untouched |
| Official U-docs (Tier scope) | Yes | `en/docs/<DOC-ID>.md`, structure preserved |
| Test-case comments | No | Index only |
| Solver source comments | No | Out of scope |
| Field / component names in MED (`DEPL`, `VMIS`) | Never renamed | Labelled in English at presentation time via glossary |
| Our own guide and report text | Written in English, not translated | `en/guide/`, report templates |

## 2. Glossary discipline

- Before translating anything, load `en/glossary.yaml` into the prompt (batch) or read it (session).
- A French term with an entry must be rendered with that `en`, every time, including inside message texts and doc prose. The validator scans for `aliases_en` (forbidden synonyms) and fails the build.
- A French term without an entry: add it in the same change with `status: proposed`, `kind`, and a `note` explaining the abbreviation or origin. Do not silently pick a translation.
- Abbreviations are expanded once in `note`, never in-line in every message: `MA` → "maille = element", `NO` → "noeud = node", `CARA` → "caractéristiques = properties", `CHAM` → "champ = field", `SIEF` → "stress (efforts) field", `EFGE` → "generalised forces (shell/beam resultants)", `ELGA` → "at Gauss points", `ELNO` → "at element nodes", `NOEU` → "at nodes (averaged)".
- When French engineering usage differs from English usage, follow English engineering usage and note the difference: *modélisation* → "modeling type" (not "modelization"); *chargement* → "load" or "load case"; *conditions aux limites* → "boundary conditions"; *dualisation* → "Lagrange-multiplier enforcement"; *maille* → "element" (never "cell"); *concept* → "result object (concept)"; *unité logique* → "logical unit (file slot)"; *alarme* → "warning"; *erreur fatale* → "fatal error".

## 3. Messages

Message texts are the most mechanical and the most dangerous to get wrong (they're what a user reads at 2 a.m.).

Rules:
1. Preserve every placeholder character-for-character: `%(k1)s`, `%(i1)d`, `%(r1)f`, `%(r1)12.5E`, `%(k1)-8s`, and literal `%%`. Reorder them if English word order requires; never rename, drop, or add.
2. Preserve line breaks and indentation structure where the French uses them for lists; the `.mess` formatter wraps text in a box and relies on `\n`.
3. Keep the register: short, direct, imperative where the French is. Do not soften errors or add explanation that is not in the source — put explanations in the `note` field for the reviewer, not in `en`.
4. Translate the **meaning**, not the words. `"Le concept %(k1)s n'existe pas"` → `"Result object %(k1)s does not exist"`, not "The concept …".
5. Severity hint: `warning` if the French says *alarme*, *attention*, *on continue*; `error` for *erreur*, *impossible*, *arrêt*; `fatal` for *fatale*, *arrêt du code*; `info` otherwise. This is a hint for the report, not a fact; the real severity comes from the `.mess` tag (`<A>`, `<E>`, `<F>`).
6. Record `method`: `machine` (batch LLM, no human), `assisted` (LLM in session, agent read context), `reviewed` (engineer). A message changed upstream after translation is marked `stale` by the bump tool and re-translated.

## 4. Command references (`en/commands/<CMD>.md`)

Template (`tools/codeaster_en/translate/templates/command.md.j2`):

```markdown
---
command: AFFE_MODELE
upstream: 17.2.11
source: code_aster/Cata/Commands/affe_modele.py
doc_fr: U4.41.01
status: assisted            # machine | assisted | reviewed
reviewed_by:
reviewed_on:
examples: [ssls101a, ssnv112a]
---

# AFFE_MODELE — assign a finite-element model to a mesh

One paragraph: what it produces (a `modele` result object), what it needs (a mesh), what decision it encodes (which element formulation each group uses).

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MAILLAGE` | mesh, required | — | The mesh to assign the model to. |
| `AFFE` | factor keyword, 1..n | — | One block per region. |
| `AFFE / TOUT` | `'OUI'` | — | Apply to the whole mesh; mutually exclusive with `GROUP_MA`. |
| `AFFE / MODELISATION` | enum, required | — | Element formulation. `3D` for solids, `DKT` thin shells, … (see guide/modelisations.md). |

## Patterns
### Solid body
```python
MODE = AFFE_MODELE(MAILLAGE=MAIL, AFFE=_F(TOUT='OUI', PHENOMENE='MECANIQUE', MODELISATION='3D'))
```
### Shell + solid in one model
…

## Pitfalls
- …

## See also
- Translated doc: en/docs/U4.41.01.md
- Examples: upstream/astest/ssls101a.comm (…)
```

Start from the draft: `caen translate command <CMD>` (or `--tier 1`) writes `en/commands/<CMD>.md` with `status: machine`: front matter, a facts table, the keyword table (types, defaults, allowed values, bloc conditions, glossary English, translated `fr=` help), the catalog rules, and calls lifted from astest. `TODO(2.3)` marks what the author writes; `TODO(translate)` marks a `fr=` string missing from `en/catalog-help.yaml`. Once you edit a draft, set `status: assisted`: the generator then leaves the file alone (ADR-012).

Rules:
- Every keyword in the table must exist in the `.json`; nested keywords use `PARENT / CHILD` paths.
- "Meaning and when to use" is mandatory and must be more than the type. If you cannot say when to use it, write `TODO(verify): …` and cite what you read.
- Patterns are real `.comm` fragments that would run; lift them from astest where possible and cite the case.
- Pitfalls come from message families (what warnings fire), test cases, and forum knowledge the author actually has. No speculation.

## 5. Documents (`en/docs/<DOC-ID>.md`)

Produced by `caen translate doc` (task 5.2, ADR-027) from the French text ingested by `caen docs ingest`/`fetch` (task 5.1, `en/docs/_src/`). Scope (documents, and chunks inside the large ones) is `en/docs/scope.yaml`.

- Keep the French document's section numbering and headings (translated) so cross-references (`§4.3`) still work. Out-of-scope chunks keep their French headings, marked *(not translated)*.
- Code blocks (syntax trees, listings, `.comm` examples) are never translated: the request shows them as `[[CODE n]]` markers and the tool puts the French block back verbatim. Tables keep their rows and cells; translate the cell text, not keyword names or values.
- Equations: the extraction marks formula lines `<!-- equation -->` and they are often garbled; copy them as they are. Figures stay `*[Figure, page N: not extracted]*`.
- Every answer is checked (markers, headings, list items, table shape, catalog identifiers, glossary synonyms, French left); `caen validate docs` re-runs the checks on the committed files.
- Header (generated; do not edit except `reviewed_by`/`reviewed_on`, owner only):

```markdown
---
doc_id: U4.41.01
title_fr: "Opérateur AFFE_MODELE"
title_en: "AFFE_MODELE operator"
commands: [AFFE_MODELE]
tier: 1
doc_date: 11/01/2024
doc_revision: 1f54feb5a1bf
source: https://code-aster.org/doc/v16/man_u/u4/u4.41.01.pdf
copyright: EDF R&D
licence: GFDL-1.3
checked_against_upstream: 17.4.26
method: machine
translation_source: session:task-5.2
chunks: {total: 8, translated: 8, stale: 0, pending: 0, out_of_scope: 0}
reviewed_by:
history: [...]
---
```

- The body opens with the notice *"Unofficial English translation of EDF R&D document U4.41.01 … The French original prevails."* and the GFDL 1.3 permission notice (docs/LICENSING.md).
- Each chunk starts with `<!-- chunk N fr=<sha> method=… source=… on=… -->`. An owner review sets `method=reviewed` on the chunks read; the tool never redoes those.

Usage:

```bash
caen translate doc --tier 1 --dry-run                     # chunks, tokens, cost; writes nothing
caen translate doc U4.41.01                               # Claude API (needs credentials; spends credit)
caen translate doc U4.41.01 --export-requests req/        # in-session path, step 1: req/U4.41.01/<n>.request.md
caen translate doc U4.41.01 --responses ans/ --source session:<task>   # step 2: ans/U4.41.01/<n>.md
caen translate doc --tier 1 --assemble-only               # rewrite headers, flag stale chunks
```

## 6. Batch translation prompt (for `caen translate`)

`caen translate messages` (task 3.1, ADR-014) builds every request the same way:

- **System prompt** (identical for every batch, cached): role and rules (§2–§3 condensed) and every glossary entry of `kind: term` or `abbrev`, with its forbidden synonyms.
- **User prompt**: the family name, the `command`/`keyword`/`value`/`concept` entries whose French appears in the batch, and the items as JSON (`id`, `fr`, `placeholders`, and `upstream_en` when the 2016 `.po` has the same French after whitespace normalization; it is a hint, labelled as dated and literal).
- **Output schema**: `translations[]` (`id`, `en`) and `glossary_additions[]` (`fr`, `en`, `kind`, `note`), enforced with structured output.

The tool rejects any item whose placeholder set differs from the French, or that uses a forbidden synonym of a glossary term present in the French, and asks again for only those items with the problems listed. Glossary additions are written to `en/glossary.yaml` as `proposed`, never applied automatically to other items in the same run. The severity hint is computed from the French wording (§3.5), not asked from the model.

Usage:

```bash
caen translate messages -f MODELISA8 --dry-run            # batches, tokens, cost; writes nothing
caen translate messages --all --seed-only                 # verbatim .po matches only, free
caen translate messages -f MODELISA8                      # Claude API (needs credentials; spends credit)
caen translate messages -f MODELISA8 --export-requests req.jsonl   # in-session path, step 1
caen translate messages -f MODELISA8 --responses ans.jsonl \
    --method assisted --source session:<task>             # step 2: import through the same checks
```

A run writes after every batch and skips translated messages, so it can be stopped and restarted. `--force` redoes translated messages but never `reviewed` ones.

## 7. Review checklist (engineer)

- Would I understand this warning without the French? Does it tell me what to change?
- Is each keyword's "when to use" true for the modeling types I use (3D, DKT/COQUE_3D, AXIS)?
- Did the translation keep the sign conventions, units, and defaults exactly?
- Does any sentence promise a behaviour I haven't seen in a test case? If so, demand the citation or mark `TODO(verify)`.
- Set `status: reviewed`, `reviewed_by`, `reviewed_on`.
