# Licensing notes

Not legal advice. Written so an agent and the owner apply one consistent policy; the owner should confirm against the actual licence files in the pinned upstream.

## Upstream

- **code_aster source** — GPL (file headers in recent versions read "GNU General Public License … either version 3 of the License, or (at your option) any later version"). Task 0.4 verifies the exact text in `upstream/LICENSE*` and the header of a few files, and records it here.
- **code_aster documentation (PDFs on code-aster.org)** — licence is stated on the site/document footers (historically a permissive EDF documentation licence; some material under GNU FDL). Task 5.1 records the exact terms found on the PDFs ingested and what they allow (translation, redistribution, modification, attribution requirements). Until confirmed, treat translations as **derivative works that require attribution, keep the original notice, and are not presented as official**.
- **AsterStudy translation dictionary** — GPL-3 per its header ("Copyright 2016 EDF R&D … GPL Version 3"). Our glossary seed cites it; the glossary file carries the attribution line.
- **Official container images** — same GPL code; we only run them.
- **Trademark** — "code_aster" and "Salome-Meca" are EDF marks. We say "English overlay for code_aster", never imply endorsement; README carries the disclaimer.

## This repository

- **Everything we author** (tools, glossary, command references, guide, report templates, fixtures) — **GPL-3.0-or-later** (`LICENSE` file = GPL-3.0 text; SPDX header `SPDX-License-Identifier: GPL-3.0-or-later` in each source file).
  - Message translations are derived from GPL source → GPL is the safe choice.
  - GPL-3.0 is compatible with ClearFEA's AGPL-3.0 (GPLv3 §13 / AGPLv3 §13 allow combining).
- **Translated official docs (`en/docs/`)** — carry: original doc ID, version, "© EDF R&D", our translation notice, and the licence terms recorded in Task 5.1. If those terms turn out not to permit redistribution of translations, `en/docs/` is removed from the published package and kept only as a build-time, git-ignored local resource; `en/commands/*.md` (our own prose, citing doc IDs) remains.
- **Extracted catalog JSON and French message texts (`en/commands/*.json`, `fr` fields in `en/messages/`)** — verbatim copies of GPL material; GPL applies; attribution via the `_generated_from` header.
- **Fixtures** — our own `.comm`/meshes (GPL-3.0-or-later); solver outputs are data.

## Obligations checklist (release time)

- `LICENSE` (GPL-3.0) at repo root; `NOTICE.md` listing upstream copyright, AsterStudy dictionary attribution, doc attributions. Both added in task 6.2.
- Wheel includes `LICENSE` and `NOTICE.md` (under `codeaster_en/_data/`); metadata carries the SPDX expression `License-Expression: GPL-3.0-or-later`, which replaces the `License ::` classifier (setuptools ≥ 77 refuses both together; ADR-020).
- Each `en/docs/*.md` header complete (see TRANSLATION-GUIDE §5).
- No EDF logos or document layouts reproduced; text only.

## Contributions

Developer Certificate of Origin (DCO) sign-off on commits (`git commit -s`); no CLA. Same policy as ClearFEA.
