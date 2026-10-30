---
command: EXTR_MODE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/extr_mode.py:41
doc_fr: U4.52.12
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 6.4)
examples: [sdls300b, sdll129a, zzzz115c]
---

# EXTR_MODE — extract/filter modes

> **Assisted reference.** Written in session from the pinned catalog, the solver source it
> calls, the message catalog, upstream test cases and the committed fixture runs. Every behavior
> claim cites its source. Not reviewed by an engineer.

Extracts selected modes from modal data structures.

`EXTR_MODE` builds a new modal result from selected modes of one or more modal results: by
number, by frequency range, or by a significance criterion such as the unit effective mass. It
is the step that keeps only the modes that matter before a response-spectrum or transient
combination, and its `IMPRESSION` option prints the effective mass fractions with their running
total, which tells whether enough modes were computed (codes often ask for 90 % of the mass in
each direction). The modes are copied with their parameters; their numbers (`NUME_MODE`) are
kept and the output is renumbered by order (`NUME_ORDRE`). Every input result must come from the
same matrices (`ALGELINE3_9`, `upstream/bibfor/op/op0168.F90:143`). `CALC_MODES` calls it
itself when its `FILTRE_MODE` or `IMPRESSION` keyword is given
(`upstream/code_aster/MacroCommands/Modal/calc_modes_post.py:43`).

| Fact | Value |
|---|---|
| Catalog description (fr) | «Extraire séléctivement des modes des structures de données modales» |
| Kind | `OPER` |
| Result | `mode_meca`, `mode_meca_c`, `mode_gene` (depends on the keywords given) |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.52.12 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 2 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `MASS_INER`, `NORME`, `FILTRE_MODE`, `CRIT_EXTR`, `MASS_EFFE_UN`, `SEUIL` |

The COMMAND-SET "Modal post" row groups `NORM_MODE`, `EXTR_MODE` and `POST_ELEM MASS_INER`;
`MASS_INER` and `NORME` in the key keywords above are [POST_ELEM](POST_ELEM.md) and
[NORM_MODE](NORM_MODE.md) keywords.

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `FILTRE_MODE` | factor keyword, required, repeatable | — | *mode filter*. One selection: an input result and one filter (catalog rule). Repeat it to take modes from several results, or several sets from one result (`upstream/astest/sdll113a.comm:305`); the output holds them in that order. |
| `FILTRE_MODE / MODE` | `mode_meca` or `mode_meca_c` or `mode_gene`, required | — | The modal result to take modes from. All the occurrences must reference the same stiffness, mass and damping matrices, or the command stops (`ALGELINE3_9`). |
| `FILTRE_MODE / TOUT_ORDRE` | text, optional | — | *all steps*. One of `'OUI'`, `'NON'`. `'OUI'`: every mode of `MODE` (a plain copy). |
| `FILTRE_MODE / NUME_ORDRE` | integer, optional, list | — | *step index*. The modes at these storage indices (1, 2, … in the order stored). An index that does not exist gives warning `ALGELINE4_55` and is skipped (`upstream/bibfor/op/op0168.F90:188`). |
| `FILTRE_MODE / NUME_MODE` | integer, optional, list | — | *mode number*. The modes with these mode numbers (`NUME_MODE` parameter of the result; the same as the storage index for a single `CALC_MODES` call) (`upstream/astest/zzzz115c.comm:101`). |
| `FILTRE_MODE / NUME_MODE_EXCLU` | integer, optional, list | — | Every mode except those with these mode numbers (`upstream/bibfor/op/op0168.F90:224`). |
| `FILTRE_MODE / FREQ_MIN` | real, optional | — | Lower bound of a frequency range, in Hz (with `FREQ_MAX`): the modes with FREQ_MIN − `PRECISION` ≤ f ≤ FREQ_MAX + `PRECISION` are kept (`upstream/bibfor/op/op0168.F90:254`, `upstream/astest/forma12c.comm:189`). |
| `FILTRE_MODE / CRIT_EXTR` | text, optional | — | *mode selection criterion*. One of `'MASS_EFFE_UN'`, `'MASS_GENE'`, `'MASS_EFFE'`, `'INER_EFFE_UN'`, `'INER_EFFE'`. Keep the modes whose stored parameter reaches `SEUIL` (or `SEUIL_X/Y/Z` for one direction): `'MASS_EFFE_UN'` the unit effective mass, that is the effective mass as a fraction of the total mass, the usual choice (`upstream/astest/sdls300b.comm:57`); `'MASS_EFFE'` the effective mass itself (model units); `'INER_EFFE_UN'`/`'INER_EFFE'` the effective rotational inertia, unit or absolute; `'MASS_GENE'` the generalized mass as a fraction of the sum over all modes (`upstream/bibfor/op/op0168.F90:282`, `:422`). With `SEUIL`, a mode is kept if any of the three directions reaches it. |
| `FILTRE_MODE / FREQ_MAX` | real, required | — | Only when `exists("FREQ_MIN")`. Upper bound of the frequency range, in Hz. |
| `FILTRE_MODE / PRECISION` | real, optional | `0.001` | *tolerance*. Only when `exists("FREQ_MIN")`. Absolute tolerance, in Hz, added on both sides of the range (`upstream/bibfor/op/op0168.F90:256`). |
| `FILTRE_MODE / SEUIL` | real, optional | — | *threshold*. Only when `exists("CRIT_EXTR")`. Threshold for `CRIT_EXTR`, in the units of the criterion: a fraction (0.001 = 0.1 %) for the `_UN` criteria and `MASS_GENE`. A mode is kept if its value in at least one direction is ≥ `SEUIL`. |
| `FILTRE_MODE / SEUIL_X` | real, optional | — | Only when `exists("CRIT_EXTR")`. Threshold for direction X only: a mode is kept if its X value is ≥ `SEUIL_X` (`upstream/bibfor/op/op0168.F90:298`). |
| `FILTRE_MODE / SEUIL_Y` | real, optional | — | Only when `exists("CRIT_EXTR")`. Threshold for direction Y only. |
| `FILTRE_MODE / SEUIL_Z` | real, optional | — | Only when `exists("CRIT_EXTR")`. Threshold for direction Z only. |
| `TITRE` | text, optional | — | *title*. A title stored with the result. Optional. |
| `IMPRESSION` | factor keyword, optional | — | Print a table of the extracted modes to the message file (`.mess`): mode number, frequency and, per direction, the criterion value (`ALGELINE6_50`/`ALGELINE6_51`, `upstream/bibfor/op/op0168.F90:544`). The report generator does not read this table; it reads the `RECU_TABLE` printout of the parameters instead. |
| `IMPRESSION / CUMUL` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. `'OUI'` adds, for each direction, the running total of the criterion over the extracted modes (`CUMUL_DX` …): the check that the retained modes reach the mass fraction a code requires. `'NON'` (default) prints the values only. |
| `IMPRESSION / CRIT_EXTR` | text, optional | `'MASS_EFFE_UN'` | *mode selection criterion*. One of `'MASS_EFFE_UN'`, `'MASS_GENE'`, `'MASS_EFFE'`, `'INER_EFFE_UN'`, `'INER_EFFE'`. Which parameter the table prints: unit effective masses (default), effective masses, generalized masses or effective inertias. Independent of the `CRIT_EXTR` used to filter. |

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- `FILTRE_MODE`: exactly one of `TOUT_ORDRE`, `NUME_ORDRE`, `NUME_MODE`, `NUME_MODE_EXCLU`, `FREQ_MIN`, `CRIT_EXTR` must be given (`UN_PARMI`).
- when `exists("CRIT_EXTR")`: at least one of `SEUIL`, `SEUIL_X`, `SEUIL_Y`, `SEUIL_Z` must be given (`AU_MOINS_UN`).

Each `FILTRE_MODE` occurrence takes one filter: `TOUT_ORDRE`, `NUME_ORDRE`, `NUME_MODE`,
`NUME_MODE_EXCLU`, `FREQ_MIN` (with `FREQ_MAX`) or `CRIT_EXTR` (with a threshold).

## Patterns

### Keep the modes above 0.1 % of the mass, print the running total

The usual call before a spectral combination. Source: `upstream/astest/sdls300b.comm:57`.

```python
mode1 = EXTR_MODE(
    FILTRE_MODE=_F(CRIT_EXTR="MASS_EFFE_UN", MODE=modes, SEUIL=0.001), IMPRESSION=_F(CUMUL="OUI")
)
```

### The same over two results, printed by unit effective mass

Source: `upstream/astest/sdll132a.comm:930`.

```python
EXTRMODE = EXTR_MODE(
    FILTRE_MODE=(
        _F(MODE=NORMM01, CRIT_EXTR="MASS_EFFE_UN", SEUIL=5.0e-4),
        _F(MODE=NORMM02, CRIT_EXTR="MASS_EFFE_UN", SEUIL=5.0e-4),
    ),
    IMPRESSION=_F(CUMUL="OUI", CRIT_EXTR="MASS_EFFE_UN"),
)
```

### Modes up to a cut-off frequency

Source: `upstream/astest/forma12c.comm:189`.

```python
dynaModes2 = EXTR_MODE(
    FILTRE_MODE=_F(MODE=dynaModes, FREQ_MIN=0.0, FREQ_MAX=2 * f_coup), IMPRESSION=_F(CUMUL="OUI")
)
```

### One mode by number

Source: `upstream/astest/zzzz115c.comm:101`.

```python
EXTR = EXTR_MODE(FILTRE_MODE=_F(MODE=MODMECA, NUME_MODE=1))
```

### Inside CALC_MODES

`CALC_MODES` with `FILTRE_MODE=_F(SEUIL=...)` runs the same extraction on its own result
(`upstream/code_aster/MacroCommands/Modal/calc_modes_post.py:46`); its default criterion is
`MASS_EFFE_UN` and its default threshold 0.001 (`upstream/code_aster/Cata/Commands/calc_modes.py:355`).

## What the solver does

`op0168` (`upstream/bibfor/op/op0168.F90`) checks that every input shares the reference
matrices (`:139`), builds the list of storage indices each filter keeps (`:150`–`:445`), copies
those modes and all their parameters into a new `mode_meca` (`vpstor`, `:478`), warns when two
extracted modes carry the same `NUME_MODE` (`ALGELINE4_57`, `:532`), and prints the
`IMPRESSION` table (`:540`). An empty selection overall is fatal (`ALGELINE3_11`, `:459`); an
occurrence that keeps no mode only warns (`ALGELINE4_56`, `:471`).

## Pitfalls

- **Effective masses must exist.** The `MASS_EFFE*` and `INER_EFFE*` criteria read parameters
  that `CALC_MODES` stores for physical matrices; a result without them stops the command
  (`ALGELINE3_10`, whose English text blames `NORM_MODE`). Modes recombined from a
  generalized basis may not carry them. TODO(verify) which results lack them.
- **Nothing kept is an error.** If no occurrence keeps a mode, the run stops with
  `ALGELINE3_11` ("no mode fills the criterion"). Lower `SEUIL` or check the modal result.
- **`SEUIL` is per mode, not cumulative.** `CRIT_EXTR` keeps each mode whose own fraction is
  above the threshold; reaching 90 % of the mass is checked with `IMPRESSION=_F(CUMUL='OUI')`,
  not by the filter. If the running total is too low, compute more modes in `CALC_MODES`.
- **Duplicate mode numbers.** Taking the same mode twice, or modes from two results numbered
  from 1, gives warning `ALGELINE4_57`; later commands that select by `NUME_MODE` then see
  ambiguous numbers. Select by `NUME_ORDRE` downstream.

## See also

- French reference: U4.52.12 (from en/doc-ids.yaml, status: verified; French text:
  `en/docs/_src/U4.52.12.fr.md`; no English translation yet (Tier 2, not in `en/docs/scope.yaml`))
- Catalog: `en/commands/EXTR_MODE.json` (generated from `upstream/code_aster/Cata/Commands/extr_mode.py:41`)
- Implementation: `upstream/bibfor/op/op0168.F90`
- Before: [CALC_MODES](CALC_MODES.md), [NORM_MODE](NORM_MODE.md)
- Next steps: `COMB_SISM_MODAL`, `DYNA_VIBRA` (Tier 3), [IMPR_RESU](IMPR_RESU.md)
- Example: `upstream/astest/sdls300b.comm` (line 57)
- Example: `upstream/astest/sdll132a.comm` (line 930)
- Example: `upstream/astest/forma12c.comm` (line 189)
