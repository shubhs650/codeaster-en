# Progress log

Newest entry first. One entry per session. Keep entries short; detail belongs in the PR.

Template:

```
## YYYY-MM-DD — <task id> <title> — <agent|owner>
Done: …
Open: …
Decisions: (ADR refs or "none")
Needs owner: …
```

---

## 2026-10-23 — 0.4 verify upstream anatomy (S1) — agent
Done: verified CLAUDE.md §6 and ARCHITECTURE.md §3 against 17.4.26 and corrected both in place;
`docs/INVENTORY.md` with counts. **268 commands** (135 OPER, 116 MACRO, 16 PROC, 1 FORM; + `VARIABLE`)
in 269 modules; **18,917 keyword occurrences** (17,595 simple, 1,322 factor; 2,847 blocs), 4,227
distinct names; `fr=` on only 13 % of keywords. **277 message families, 6,890 messages**, 51
placeholder formats (all named, + `%%`). **4,496 test cases** (`.export`), no expected `.mess` in
astest. `code_aster.Cata.Commands` imports in a plain venv (numpy only) → task 1.2 extracts by
import. `code_aster.Messages` does **not** import without the solver (`Utmess` → `aster_core`) →
task 1.3 must use `ast`. Upstream gettext: `_()` → domain `aster_messages`, switched on only by
`DEBUT(LANG=...)`, `.mo` built only with `--enable-i18n`. Upstream `en-US/aster_messages.po` covers
3,308/6,890 current messages (48 %) verbatim, literal 2016 quality.
Open: ADR-004 drafted (status proposed) — owner decision. Task 4.2 must check whether the official
image ships an English `.mo` and whether `ASTER_LOCALEDIR` can be overridden.
Decisions: none taken; ADR-004 draft recommends `en/messages` as source of truth + generated `.mo`
via `DEBUT(LANG='EN')` + runtime renderer as fallback.
Findings for later tasks: `POURSUITE` has no catalog (runs on `DEBUT`'s) — its Tier 1 reference
should say so; 4 messages numbered ≥ 100 are unreachable (`Utmess` asserts N < 100); `POST0_55/56`
are f-strings interpolating a module constant; 15 messages are not wrapped in `_()`; plain `I`
messages print without their ID in `.mess`. Licence headers GPL-3.0-or-later as ADR-007 assumes;
`.po`/`.ts` have no own licence header (owner to confirm reuse under GPL with attribution).
Needs owner: ADR-004 decision; confirm reuse of the Crowdin `.po`/`.ts` translations.
Branch is `claude/project-thread-ux6ket` (session-assigned) rather than `task/0-4-…`.

## 2026-10-23 — 0.3 + 0.5 upstream pin and tooling skeleton — agent
Done: `upstream/` submodule → github.com/shubhs650/code_aster (shallow), pinned to **17.4.26**
(commit 5d2a06d, 2026-07-06; same commit as tags `17.5.0` and `stable`). `UPSTREAM_VERSION` =
17.4.26. `tools/` package `codeaster_en` + `caen` CLI (typer) with stubs extract, translate, mess,
report, upstream, bundle; `caen validate [glossary]` implemented (unique fr, non-empty en, kind
and status in allowed sets, aliases_en ≠ en, unique en within kind=command). `ci.yml`: checks the
submodule commit equals the UPSTREAM_VERSION tag, then ruff check/format, pytest, caen validate.
`tests/test_glossary.py` (36 tests). Root `ruff.toml` / `pytest.ini`; `.gitmodules.example`
replaced by the real `.gitmodules`.
Open: task 0.4 (S1). `CONTAINER_TAG` not created (Docker Hub `codeastersolver/codeaster-seq`
lists only `latest` and `14.4.0`; image ↔ 17.4.26 mapping is for task 4.2).
Decisions: tag rule — upstream README defines `stable` as "the latest frozen state of the stable
version in the maintenance branch"; it points at 17.4.26 = 17.5.0. 17.5.1–17.5.8 are
`stable-updates` (unfrozen maintenance head of `v17`); 18.0.x/18.1.x are `main`/`testing`
(18.0.25 = `testing`, so "even minor" alone would have picked a development tag). Glossary is
loaded with YAML 1.2 booleans so `fr: NO` stays the string "NO", not `False`. Ruff limited to
Python files (ruff ≥ 0.17 also reformats Markdown code blocks in docs/).
Needs owner: confirm 17.4.26 (vs. latest stable-update 17.5.8); upstream already ships English
localisation — `i18n/en-US/aster_messages.po` (Crowdin, 2016, ~6.7k msgids, v13 paths) and
`i18n/catapy_en_US.ts` (catalog strings, ~1.5k entries) — task 0.4/1.1 should assess reuse.
Branch is `claude/project-thread-mmwu8d` (session-assigned) rather than `task/0-3-…`.

## 2026-10-22 — kickoff — owner
Done: Doc set written (README, CLAUDE.md, ARCHITECTURE, PLAN, COMMAND-SET, TRANSLATION-GUIDE,
REPORT-SPEC, CLEARFEA-INTEGRATION, DECISIONS, LICENSING, SESSION-PROMPTS), seed glossary,
mirror sync workflow. No code.
Open: Tasks 0.1–0.2 (owner: create mirror repo, import, add sync workflow). Then S0 session.
Decisions: ADR-001…009 recorded.
Needs owner: choose GitHub org/user for both repos; attach AsterStudy translation dictionary
file for task 0.6; decide whether `code_aster` mirror keeps all tags or `main` only (after
blob-size check).
