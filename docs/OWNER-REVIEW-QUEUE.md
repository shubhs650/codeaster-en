# Owner review queue

Since ADR-010 (full autodrive) nothing waits on the owner. This file lists what would benefit from an engineer's eye, or needs an input only the owner can give, so it can be picked up asynchronously. Agents append entries in the PR that creates the item; the owner (or an agent, once the owner has acted) strikes them.

Only the owner sets `status: reviewed`.

## Reviews (asynchronous, not blocking)

| Added | Item | What to check | Source |
|---|---|---|---|
| 2026-10-29 | Glossary seed (task 0.6, PR #3) | All entries are `proposed`; spot-check the English for terms with structural meaning (loads, element types, results fields). | `en/glossary.yaml` |
| 2026-10-29 | COMMAND-SET revision proposals (task 1.5) | The 8 proposals in `docs/INVENTORY.md` §8. The agent may apply them under ADR-010; check the result. | `docs/INVENTORY.md` §8 |
| 2026-10-29 | ADR-007 licence | Status still reads "owner to confirm after reading upstream licence headers". | `docs/DECISIONS.md` |

## Inputs only the owner can give (tasks skip and continue)

| Added | Input | Needed by | Note |
|---|---|---|---|
| 2026-10-29 | French U4 PDFs for Tier 1 commands, U1.03.01, U4.81.01 | 5.1–5.3 | code-aster.org is unreachable from the sandbox. |
| 2026-10-29 | API key for bulk LLM message translation | 3.2 (bulk path) | Without it, families are translated in-session. |
