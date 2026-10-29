# Notices

codeaster-en is an English overlay for code_aster. It is not part of code_aster, is not
affiliated with or endorsed by EDF, and its translations are not official. "code_aster" and
"Salome-Meca" are trademarks of EDF.

Everything in this repository and in the `codeaster-en` package is distributed under the GNU
General Public License, version 3 or (at your option) any later version (`LICENSE`).
Policy: `docs/LICENSING.md`.

## Third-party material

| Material | Where it is used | Copyright and licence |
|---|---|---|
| code_aster command catalogs (`code_aster/Cata/`), messages (`code_aster/Messages/`) and test cases (`astest/`) | Extracted into `en/commands/*.json` and the `fr` fields of `en/messages/*.en.json`; cited in references | Copyright (C) 1991 - 2026 EDF, www.code-aster.org; GPL-3.0-or-later |
| code_aster English localization (`i18n/en-US/aster_messages.po`, `i18n/catapy_en_US.ts`, 2016) | Seed for messages with `method: machine` and for catalog help strings | EDF R&D and code_aster translators; distributed with code_aster under the GPL |
| AsterStudy translation dictionary (`GLOBAL_DICT`) | Seed of `en/glossary.yaml` (entries with `asterstudy:`) | Copyright 2016 EDF R&D; GPL-3 |

Each generated file names its upstream tag and commit in `_generated_from` (or its header), and
each English text records its translation method.
