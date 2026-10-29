# Owner review queue

Since ADR-010 (full autodrive) nothing waits on the owner. This file lists what would benefit from an engineer's eye, or needs an input only the owner can give, so it can be picked up asynchronously. Agents append entries in the PR that creates the item; the owner (or an agent, once the owner has acted) strikes them.

Only the owner sets `status: reviewed`.

## Reviews (asynchronous, not blocking)

| Added | Item | What to check | Source |
|---|---|---|---|
| 2026-10-29 | Glossary seed (task 0.6, PR #3) | All entries are `proposed`; spot-check the English for terms with structural meaning (loads, element types, results fields). | `en/glossary.yaml` |
| 2026-10-29 | Glossary: specific calls (task 0.6) | `AFFE_VARC`/`NOM_VARC` "external state variable" (upstream says "command variable"); `TODO(verify)` entries `PM_PB`, `K_T_D_N`/`K_TR_D_N`, `VOLUMOGRAMME`, `DIFFE`, `RESI_RELA`, `VALE_REF`, `VITESSE`, `CRITERE`; `BANDE` broadened to "band"; where AsterStudy GLOBAL_DICT differs (`asterstudy:` field), e.g. `UNITE` "Filename" vs "logical unit", `PESANTEUR`, `PRECISION`, `INST`. | `en/glossary.yaml` |
| 2026-10-29 | Glossary notes (task 2.1) | All entries are now `machine` with a `note`. Spot-check notes that explain engineering meaning: `REAC_NODA`/`FORC_NODA`, `SIGM_ELNO`/`SIGM_NOEU`, `LIAISON_RBE3`, `ORIE_PEAU`, `INST` (pseudo-time). Open `TODO(verify)`: `VERI_MAIL` (APLAT), `REAC_NODA`, `PRIN_1`/`PRIN_3` ordering, `LONG_CARA`, `COEF_AMOR`. | `en/glossary.yaml` |
| 2026-10-29 | COMMAND-SET revision proposals (task 1.5) | The 8 proposals in `docs/INVENTORY.md` §8. The agent may apply them under ADR-010; check the result. | `docs/INVENTORY.md` §8 |
| 2026-10-29 | Fixture solver image (task 4.2, ADR-011) | Runtime is code_aster 17.4.22 (`simvia/code_aster`, not an EDF image) while the pin is 17.4.26. Confirm that is acceptable, or point to an official 17.4.x image. | `CONTAINER_IMAGE`, `docs/DECISIONS.md` ADR-011 |
| 2026-10-29 | Fixture sign conventions (task 4.2) | Reaction sums are positive (support reaction) and the plate centre `MXX` is negative under sagging; references are now signed. | `tests/fixtures/README.md` |
| 2026-10-29 | ADR-007 licence | Status still reads "owner to confirm after reading upstream licence headers". | `docs/DECISIONS.md` |
| 2026-10-29 | U4 doc IDs for Tier 1 (task 2.2) | 24 IDs in `en/doc-ids.yaml` are agent recall (`status: proposed`), not checked against the PDFs. One conflict: PLAN.md 5.1 names U4.81.01 for `IMPR_RESU`; the file says U4.91.01. Set `status: verified` (or fix) when the PDFs are at hand. | `en/doc-ids.yaml` |
| 2026-10-29 | Catalog help translations (task 2.2) | 220 `fr=` strings translated in-session (`method: machine`). Spot-check the RCC-M ones (`POST_RCCM`: "Elastic limit used to compute thermal ratcheting", "Data for the Fen calculation", "Stress intensity factors (weld)") and `CREA_MAILLAGE` "elements with a discontinuity". | `en/catalog-help.yaml` |
| 2026-10-29 | Mesh command references (task 2.3a) | `status: assisted`. Least-sure claims, check first. LIRE_MAILLAGE: `APLAT` is the shortest/longest node-distance ratio (read from `chckma.F90`, not the doc); no `NOM_MED` = first mesh in the file; POI1 point groups from Gmsh trigger `MODELISA8_14`. MODI_MAILLAGE: `ORIE_FISSURE` use case (joint bands); `SYMETRIE` and normals; operation order taken from `op0154.F90`. DEFI_GROUP: `CRIT_NOEUD='CENTRE'` = face/volume center nodes; `SEGM_DROI_ORDO` `CRITERE='RELATIF'` reference length; `TUNNEL` description. CREA_MAILLAGE: `COQU_VOLU` `PLAN`/`TRANSLATION` sides (from `cmcovo.F90`, no test case); `CREA_FISS` 2D-only; `REPERE` table source. 11 `TODO(verify)` in total. | `en/commands/{LIRE_MAILLAGE,MODI_MAILLAGE,DEFI_GROUP,CREA_MAILLAGE}.md` |
| 2026-10-29 | Possible upstream bug: `DEFI_GROUP` `TYPE_MAILLE` (task 2.3a) | When no element of the selection has the requested `TYPE_MAILLE`, `sscgma.F90` warns `SOUSTRUC_36` ("group is empty, not created") but then creates the group with the unfiltered list (`cgmftm.F90` returns the input list on failure). Not tested by running. If confirmed, a candidate upstream report (DECISIONS.md style); our reference documents it as a pitfall. | `upstream/bibfor/soustruc/sscgma.F90:505`–`520` |

## Inputs only the owner can give (tasks skip and continue)

| Added | Input | Needed by | Note |
|---|---|---|---|
| 2026-10-29 | French U4 PDFs for Tier 1 commands, U1.03.01, U4.81.01 | 5.1–5.3 | code-aster.org is unreachable from the sandbox. |
| 2026-10-29 | Cloud environment settings: delete the `CODEASTER_IMAGE` variable and re-paste `scripts/env-setup.sh` (it now pre-pulls the ADR-011 image) | sessions only (not blocking) | The old value points at a 2019 image; nothing reads the variable since task 4.2. |
| 2026-10-29 | API key for bulk LLM message translation | 3.2 (bulk path) | Without it, families are translated in-session. |
