---
command: NORM_MODE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/norm_mode.py:40
doc_fr: U4.52.11
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 6.4)
examples: [forma12a, sdls505c, sdld02f]
---

# NORM_MODE — normalize modes

> **Assisted reference.** Written in session from the pinned catalog, the solver source it
> calls, the message catalog, upstream test cases and the committed fixture runs. Every behavior
> claim cites its source. Not reviewed by an engineer.

Normalizes eigenmodes by a criterion chosen by the user.

`NORM_MODE` rescales the mode shapes of a modal result (`mode_meca`, `mode_flamb`) so that each
mode satisfies one normalization rule: unit generalized mass, largest translation equal to 1, a
unit component at a chosen node, and so on. It changes the amplitude of the shapes and the modal
parameters that depend on it (generalized mass and stiffness, participation factors), never the
frequencies or the effective masses. It is used in place (`reuse=`): the solver refuses a new
name for an existing result (`ALGELINE4_33`, `upstream/bibfor/op/op0037.F90:132`). Without it,
`CALC_MODES` leaves each shape scaled so that its largest component, Lagrange multipliers
excluded, is 1 (`upstream/bibfor/algeline/vppara.F90:130`, `vpnorx.F90:34`). Normalize to
`MASS_GENE` before any modal superposition or when the report must show participation factors in
a known convention; the `NORM_MODE` keyword of `CALC_MODES` does the same inside that command.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Normer des modes propres en fonction d'un critère choisi par l'utilisateur» |
| Kind | `OPER` |
| Result | `mode_meca`, `mode_meca_c`, `mode_flamb` (depends on the keywords given) |
| Can reuse its input (`reuse=`) | yes (the object given in `MODE`); catalog `reentrant='f:MODE'` |
| French reference | U4.52.11 — from en/doc-ids.yaml (status: proposed) |
| Scope tier | 2 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `MASS_INER`, `NORME`, `FILTRE_MODE`, `CRIT_EXTR`, `MASS_EFFE_UN`, `SEUIL` |

The COMMAND-SET "Modal post" row groups `NORM_MODE`, `EXTR_MODE` and `POST_ELEM MASS_INER`, so
the key keywords above mix the three: only `NORME` belongs to `NORM_MODE`. `FILTRE_MODE`,
`CRIT_EXTR` (value `MASS_EFFE_UN`) and `SEUIL` are [EXTR_MODE](EXTR_MODE.md) keywords and
`MASS_INER` is a [POST_ELEM](POST_ELEM.md) one.

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MODE` | `mode_meca` or `mode_flamb`, required | — | The modal result to normalize, from `CALC_MODES` (`mode_meca`, or `mode_flamb` for buckling). Give the same concept as `reuse=`. A result of another type stops the command (`ALGELINE2_33`, `upstream/bibfor/op/op0037.F90:183`). |
| `NORME` | text, optional | — | *norm*. Predefined norm: generalized mass, Euclidean, ... One of `'MASS_GENE'`, `'RIGI_GENE'`, `'EUCL'`, `'EUCL_TRAN'`, `'TRAN'`, `'TRAN_ROTA'`. Normalization rule (`upstream/bibfor/op/op0037.F90:344`, `upstream/bibfor/algeline/vpnorm.F90:75`). `'MASS_GENE'`: generalized mass φᵀMφ = 1 for each mode, the usual convention for modal superposition (`upstream/astest/forma12a.comm:64`). `'RIGI_GENE'`: generalized stiffness = 1. `'TRAN'`: the largest of `DX`, `DY`, `DZ` over all nodes = 1. `'TRAN_ROTA'`: the same over translations and rotations (`DRX`, `DRY`, `DRZ`). `'EUCL'`: Euclidean norm of the vector = 1. `'EUCL_TRAN'`: Euclidean norm over the translations = 1. `MASS_GENE`/`RIGI_GENE` need a result computed from assembled matrices (`ALGELINE2_35`). |
| `GROUP_NO` | node group, optional | — | *node group*. Given component at the single node of a group set equal to 1. A group holding one node: the mode is scaled so that component `NOM_CMP` at that node is 1 (`upstream/astest/sdll15a.comm:347`). A group with several nodes uses its first node and warns (`SOUSTRUC_87`); an unknown group is fatal (`ELEMENTS_67`, `upstream/bibfor/op/op0037.F90:430`). Use it to get mode shapes in units of the displacement at a measuring point. |
| `NOM_CMP` | text, required | — | *component name*. Only when `exists("GROUP_NO")`. The component set to 1 at the `GROUP_NO` node, for example `'DZ'`. The node or the component absent from the model is fatal (`ALGELINE2_36`, `ALGELINE2_37`). |
| `AVEC_CMP` | text, optional, list | — | Components used for the scaling: each mode is divided by its largest value among these components (`upstream/bibfor/algeline/vpnorm.F90:88`). `AVEC_CMP='DX'` (`upstream/astest/sdll148a.comm:89`) makes the largest axial displacement 1. A mode whose selected components are all zero is fatal (`MODAL_23`). |
| `SANS_CMP` | text, optional, list | — | The opposite of `AVEC_CMP`: every component except these is used for the scaling (`upstream/bibfor/op/op0037.F90:496`). No test case read for it. |
| `MODE_SIGNE` | factor keyword, optional | — | Imposes a sign on one of the components of the modes. Fixes the sign of every mode, after normalization, from the sign of one component at one node: a mode whose value there has the wrong sign is multiplied by −1 (`upstream/bibfor/op/op0037.F90:600`). Use it so that two runs, or two meshes, give comparable shapes (`upstream/astest/sdld02a.comm:156`). Ignored with a warning on complex modes (`ALGELINE2_43`). |
| `MODE_SIGNE / GROUP_NO` | node group, optional | — | *node group*. Group of a single node where the sign is imposed. The group holding the reference node (single node; as for `GROUP_NO` above, `SOUSTRUC_87` / `ELEMENTS_67`). |
| `MODE_SIGNE / NOM_CMP` | text, required | — | *component name*. Component of the node where the sign is imposed. The reference component at that node, for example `'DY'`. |
| `MODE_SIGNE / SIGNE` | text, optional | `'POSITIF'` | Choice of the sign. One of `'NEGATIF'`, `'POSITIF'`. `'POSITIF'` (default) makes the reference component positive in every mode; `'NEGATIF'` makes it negative. A mode whose reference component is exactly zero keeps its sign (`upstream/bibfor/algeline/vpnorm.F90:171`). |
| `MASSE` | `matr_asse_depl_r` or `matr_asse_gene_r` or `matr_asse_pres_r`, optional | — | *mass*. Mass matrix to use for `MASS_GENE` and to update the modal parameters. Only needed for a modal basis that does not carry its matrices (`DEFI_BASE_MODALE`); otherwise the matrices stored by `CALC_MODES` are used and this keyword is not read (`upstream/bibfor/op/op0037.F90:247`, `ALGELINE_3`). |
| `RAIDE` | `matr_asse_depl_r` or `matr_asse_depl_c` or `matr_asse_gene_r` or `matr_asse_pres_r`, optional | — | Stiffness matrix, under the same rule as `MASSE` (`ALGELINE_2`). Missing both for such a basis is fatal (`ALGELINE_1` + `ALGELINE_6`). |
| `AMOR` | `matr_asse_depl_r` or `matr_asse_gene_r`, optional | — | Damping matrix, for complex modes of a modal basis normalized by `MASS_GENE` or `RIGI_GENE` (`ALGELINE_8`). Not used for real modes. |
| `TITRE` | text, optional | — | *title*. A title stored with the result. Optional. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `1` prints the rule applied (`ALGELINE7_5`); `2` also prints the scaling coefficient of each mode. TODO(verify) the level-2 output. |

2 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: exactly one of `NORME`, `GROUP_NO`, `AVEC_CMP`, `SANS_CMP` must be given (`UN_PARMI`).
- `MODE_SIGNE`: exactly one of `GROUP_NO`, `NOEUD` must be given (`UN_PARMI`).

`NORME`, `GROUP_NO`, `AVEC_CMP` and `SANS_CMP` are alternatives: exactly one of them per call.
`MODE_SIGNE` can be added to any of them.

## Patterns

### Unit generalized mass, in place

The usual call, after `CALC_MODES`. Source: `upstream/astest/forma12a.comm:64`.

```python
MODES = NORM_MODE(reuse=MODES, MODE=MODES, NORME="MASS_GENE")
```

### The same inside CALC_MODES

`CALC_MODES` calls `NORM_MODE` itself when its `NORM_MODE` keyword is given
(`upstream/code_aster/MacroCommands/Modal/calc_modes_post.py:35`). Source:
`upstream/astest/sdll07a.comm:205` (excerpt of the `CALC_MODES` call).

```python
    NORM_MODE=_F(NORME="MASS_GENE"),
```

### Unit displacement at a node

Source: `upstream/astest/sdll15a.comm:347`.

```python
MD2 = NORM_MODE(reuse=MD2, MODE=MD2, GROUP_NO="N200", NOM_CMP="DZ")
```

### Largest translation equal to 1, with a fixed sign

Source: `upstream/astest/sdld02a.comm:152`.

```python
FREQ = NORM_MODE(
    reuse=FREQ,
    MODE=FREQ,
    NORME="TRAN_ROTA",
    MODE_SIGNE=_F(GROUP_NO="P2", NOM_CMP="DY", SIGNE="NEGATIF"),
)
```

## What the solver does

`op0037` (`upstream/bibfor/op/op0037.F90`) reads the matrices referenced by the result
(`:247`), builds the list of components the rule uses (`:344`), and scales each mode by one
coefficient (`upstream/bibfor/algeline/vpnorm.F90`): 1 / (largest component) for the component
rules, 1 / √(φᵀMφ) for `MASS_GENE`. The generalized mass and stiffness are multiplied by the
square of the coefficient and the participation factors by the coefficient (`vpnorm.F90:104`,
`:125`); frequencies and effective masses do not change. The rule applied is stored in the
result's `NORME` parameter (`op0037.F90:750`), which `RECU_TABLE` can print.

## Pitfalls

- **The default shape is not mass-normalized.** `CALC_MODES` alone scales each mode to a unit
  largest component (`upstream/bibfor/algeline/vppara.F90:130`). The modal fixture's
  generalized masses are about 1.57e-4 t, not 1
  (`tests/fixtures/modal/output/tables/modal_parameters.csv`). Normalize with `MASS_GENE`
  before reading participation factors or generalized coordinates.
- **In place only.** `NORM_MODE` on an existing result must reuse it: a new name for the output
  stops the command (`ALGELINE4_33`). A new name works only when the output does not exist yet
  (`upstream/astest/sdls505c.comm:117`).
- **Translation-only rules fail on rotation-only modes.** `TRAN` and `EUCL_TRAN` divide by zero
  on a mode that only rotates (a torsion mode of a shell or beam model): `MODAL_23`, which
  advises `TRAN_ROTA` or `EUCL` instead.
- **Effective masses are unaffected.** `MASS_EFFE_*` and `MASS_EFFE_UN_*` do not depend on the
  normalization; normalizing does not change what `EXTR_MODE` keeps with `CRIT_EXTR`.

## See also

- French reference: U4.52.11 (from en/doc-ids.yaml, status: proposed; translation:
  `en/docs/U4.52.11.md` once task 5.x lands)
- Catalog: `en/commands/NORM_MODE.json` (generated from `upstream/code_aster/Cata/Commands/norm_mode.py:40`)
- Implementation: `upstream/bibfor/op/op0037.F90`, `upstream/bibfor/algeline/vpnorm.F90`
- Before: [CALC_MODES](CALC_MODES.md)
- Next steps: [EXTR_MODE](EXTR_MODE.md), [IMPR_RESU](IMPR_RESU.md), `RECU_TABLE`
- Example: `upstream/astest/forma12a.comm` (line 64)
- Example: `upstream/astest/sdll15a.comm` (line 347)
- Example: `upstream/astest/sdld02a.comm` (line 152)
