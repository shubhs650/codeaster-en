# Licensing notes

Not legal advice. Written so an agent and the owner apply one consistent policy; the owner should confirm against the actual licence files in the pinned upstream.

## Upstream

- **code_aster source** — GPL (file headers in recent versions read "GNU General Public License … either version 3 of the License, or (at your option) any later version"). Task 0.4 verifies the exact text in `upstream/LICENSE*` and the header of a few files, and records it here.
- **code_aster documentation (PDFs on code-aster.org)** — recorded in task 5.1 (ADR-026): every page of the 35 documents ingested (U1.03.01, the Tier 1/2 U4 documents, U7.05.21) carries "Document diffusé sous licence GNU FDL (http://www.gnu.org/copyleft/fdl.html)", © EDF R&D, no version named. GFDL §10 then allows any published version; we use **GFDL 1.3** (`en/docs/_src/LICENSE-GFDL-1.3.txt`). It allows verbatim copies (§2) and translations as modified versions (§4, §8) provided the licence notice, copyright and title history travel with them. Translations remain **unofficial, attributed, and keep the original notice**.
- **AsterStudy translation dictionary** — GPL-3 per its header ("Copyright 2016 EDF R&D … GPL Version 3"). Our glossary seed cites it; the glossary file carries the attribution line.
- **Official container images** — same GPL code; we only run them.
- **Trademark** — "code_aster" and "Salome-Meca" are EDF marks. We say "English overlay for code_aster", never imply endorsement; README carries the disclaimer.

## This repository

- **Everything we author** (tools, glossary, command references, guide, report templates, fixtures) — **GPL-3.0-or-later** (`LICENSE` file = GPL-3.0 text; SPDX header `SPDX-License-Identifier: GPL-3.0-or-later` in each source file).
  - Message translations are derived from GPL source → GPL is the safe choice.
  - GPL-3.0 is compatible with ClearFEA's AGPL-3.0 (GPLv3 §13 / AGPLv3 §13 allow combining).
- **French document text (`en/docs/_src/`)** — verbatim extracted text of the GFDL documents, committed with each file's copyright and licence notice (`licence_notice` field, `.fr.md` front matter). **GFDL 1.3, not GPL.**
- **Translated official docs (`en/docs/`)** — modified versions of GFDL documents, so **GFDL 1.3, not GPL**: carry original doc ID, date and revision, "© EDF R&D", the GFDL notice, our translation notice ("Unofficial English translation … The French original prevails") and a history entry naming the translation. They are separate works aggregated with the GPL code (GFDL §7). `en/commands/*.md` (our own prose, citing doc IDs) stays GPL.
- **Extracted catalog JSON and French message texts (`en/commands/*.json`, `fr` fields in `en/messages/`)** — verbatim copies of GPL material; GPL applies; attribution via the `_generated_from` header.
- **Fixtures** — our own `.comm`/meshes (GPL-3.0-or-later); solver outputs are data.

## Obligations checklist (release time)

- `LICENSE` (GPL-3.0) at repo root; `NOTICE.md` listing upstream copyright, AsterStudy dictionary attribution, doc attributions. Both added in task 6.2.
- Wheel includes `LICENSE` and `NOTICE.md` (under `codeaster_en/_data/`); metadata carries the SPDX expression `License-Expression: GPL-3.0-or-later`, which replaces the `License ::` classifier (setuptools ≥ 77 refuses both together; ADR-020).
- Each `en/docs/*.md` header complete (see TRANSLATION-GUIDE §5).
- No EDF logos or document layouts reproduced; text only.

## Contributions

Developer Certificate of Origin (DCO) sign-off on commits (`git commit -s`); no CLA. Same policy as ClearFEA.
