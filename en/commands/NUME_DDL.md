---
command: NUME_DDL
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/nume_ddl.py:24
doc_fr: U4.61.11
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 6.4)
examples: [zzzz289d, zzzz507a, sdlv126a]
---

# NUME_DDL — DOF numbering

> **Assisted reference.** Written in session from the pinned catalog, the solver source it
> calls, the message catalog, upstream test cases and the committed fixture runs. Every behavior
> claim cites its source. Not reviewed by an engineer.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

Builds the numbering of the degrees of freedom, with or without renumbering, and the matrix storage.

`NUME_DDL` builds the numbering of the unknowns (degrees of freedom, DOFs) of a model: which
node carries which component at which row of the global system, plus the Lagrange multipliers
of dualized boundary conditions, and the sparse storage pattern of the matrix. Assembled matrices
and vectors refer to it, so every matrix given to one `CALC_MODES` call must share one
numbering. It is the second step of the explicit matrix path (`CALC_MATR_ELEM` → `NUME_DDL` →
`ASSE_MATRICE`), usually built from the stiffness element matrix, which carries the Lagrange
terms. It prints the size of the system (`tests/fixtures/modal/output/run.mess:283`), the first
place to check that the supports were taken into account.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Etablissement de la numérotation des ddl avec ou sans renumérotation et du stockage de la matrice» |
| Kind | `MACRO` |
| Result | `nume_ddl_sdaster` |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.61.11 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 2 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `MATR_ASSE`, `RIGI_MECA`, `MASS_MECA`, `CHARGE` |

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MATR_RIGI` | `matr_elem_depl_r` or `matr_elem_depl_c` or `matr_elem_temp_r` or `matr_elem_pres_c`, optional, list of up to 100 | — | *stiffness matrix*. Build the numbering from these element matrices: their elements and the Lagrange terms they contain (`upstream/code_aster/MacroCommands/nume_ddl_ops.py:66`). Give the `RIGI_MECA` element matrix, so the multipliers of the `CHARGE` given to `CALC_MATR_ELEM` are numbered (`tests/fixtures/modal/input/run.comm:37`). |
| `MODELE` | `modele_sdaster`, optional | — | *model*. Build the numbering from a model and loads instead of element matrices (`nume_ddl_ops.py:57`, `upstream/astest/pynl01a.comm:93`). Use it when no element matrix exists yet, for example to assemble vectors first. |
| `CHARGE` | `char_meca` or `char_ther` or `char_acou`, optional, list | — | *load*. Only when `exists("MODELE")`. With `MODELE`: the loads whose dualized conditions add Lagrange multipliers to the numbering. Give the same loads as to the matrices that will use this numbering. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `1` prints the system size: total and physical DOFs with their nodes, Lagrange pairs and relations, matrix size, non-zero terms (symmetric and not) and fill rate. Our 17.4 run printed the same at level `2` and no column height, which U4.61.11 §4.3 (v16) still lists (`docs/reference-checks/todo-verify/`). |

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: exactly one of `MATR_RIGI`, `MODELE` must be given (`UN_PARMI`).

## Patterns

### From the stiffness element matrix

Source: `tests/fixtures/modal/input/run.comm:37`, its log at
`tests/fixtures/modal/output/run.mess:283`.

```python
NUME = NUME_DDL(MATR_RIGI=RIGI_EL)
```

```text
Le système linéaire à résoudre a 12813 degrés de liberté:
   - 12591 sont des degrés de liberté physiques
     (ils sont portés par 4197 noeuds du maillage)
   - 222 sont les couples de paramètres de Lagrange associés
     aux 111 relations linéaires dualisées.
```

That is 4197 nodes × 3 translations = 12591 physical DOFs, plus two multipliers for each of the
111 clamped DOFs (37 nodes × 3) of `DDL_IMPO`.

### From a model and its loads

Source: `upstream/astest/pynl01a.comm:93`.

```python
NU = NUME_DDL(MODELE=MO, CHARGE=CHARGE)
```

## Pitfalls

- **One numbering per set of matrices.** The stiffness and mass given to `CALC_MODES` must be
  assembled on the same `NUME_DDL` (`tests/fixtures/modal/input/run.comm:39`, `:41`).
- **Two multipliers per dualized condition.** Each `DDL_IMPO` component, `LIAISON_*` relation
  or `LIAISON_RBE3` equation adds two Lagrange unknowns (the default double Lagrange-multiplier enforcement), which
  is part of why `CALC_MODES` reports fewer "active" DOFs than the total: 12813 − 222
  multipliers − 111 clamped DOFs = 12480 (`tests/fixtures/modal/output/run.mess:360`). Kinematic conditions (`AFFE_CHAR_CINE` given to
  `ASSE_MATRICE`) add none.
- **`MATR_RIGI` and `MODELE` are exclusive** (catalog rule): give one of them.

## See also

- French reference: U4.61.11 (from en/doc-ids.yaml, status: verified; French text:
  `en/docs/_src/U4.61.11.fr.md`; translation: `en/docs/U4.61.11.md`)
- Catalog: `en/commands/NUME_DDL.json` (generated from `upstream/code_aster/Cata/Commands/nume_ddl.py:24`)
- Implementation: `upstream/code_aster/MacroCommands/nume_ddl_ops.py`
- Before: [CALC_MATR_ELEM](CALC_MATR_ELEM.md)
- Next steps: [ASSE_MATRICE](ASSE_MATRICE.md); all in one call: [ASSEMBLAGE](ASSEMBLAGE.md)
- Example: `tests/fixtures/modal/input/run.comm` (line 37)
- Example: `upstream/astest/pynl01a.comm` (line 93)
