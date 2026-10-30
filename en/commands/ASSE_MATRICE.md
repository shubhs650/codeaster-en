---
command: ASSE_MATRICE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/asse_matrice.py:42
doc_fr: U4.61.22
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 6.4)
examples: [zzzz289d, sdlv126a, sdld400b]
---

# ASSE_MATRICE — assemble matrix

> **Assisted reference.** Written in session from the pinned catalog, the solver source it
> calls, the message catalog, upstream test cases and the committed fixture runs. Every behavior
> claim cites its source. Not reviewed by an engineer.

Builds an assembled matrix.

`ASSE_MATRICE` assembles element matrices into one global matrix on a DOF numbering: the
stiffness K and mass M that `CALC_MODES` takes as `MATR_RIGI` and `MATR_MASS`. It is the last
step of the explicit matrix path (`CALC_MATR_ELEM` → `NUME_DDL` → `ASSE_MATRICE`). Kinematic
boundary conditions (`AFFE_CHAR_CINE`) enter here, through `CHAR_CINE`: their DOFs are
eliminated from the assembled matrix instead of being dualized
(`upstream/code_aster/MacroCommands/asse_matrice_ops.py:70`). The result type follows the
element matrices (`matr_asse_depl_r` for mechanical real matrices).

| Fact | Value |
|---|---|
| Catalog description (fr) | «Construction d'une matrice assemblée» |
| Kind | `MACRO` |
| Result | `matr_asse_depl_r`, `matr_asse_depl_c`, `matr_asse_temp_r`, `matr_asse_pres_c` (depends on the keywords given) |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.61.22 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 2 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `MATR_ASSE`, `RIGI_MECA`, `MASS_MECA`, `CHARGE` |

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MATR_ELEM` | `matr_elem_depl_r` or `matr_elem_depl_c` or `matr_elem_temp_r` or `matr_elem_pres_c`, required, list | — | *element matrices*. The element matrices to assemble, all of the same kind (`asse_matrice_ops.py:62`): one `CALC_MATR_ELEM` result, or several that are summed (for example the stiffness of two parts). Mixing real and complex, or mechanical and thermal, element matrices is refused ("Incompatible elementary matrices", `:64`). |
| `NUME_DDL` | `nume_ddl_sdaster`, required | — | *DOF numbering*. The numbering to assemble on (`asse_matrice_ops.py:67`). Every matrix of one modal analysis uses the same one (`tests/fixtures/modal/input/run.comm:39`, `:41`). |
| `SYME` | text, optional | — | One of `'OUI'`. `'OUI'` replaces a nonsymmetric matrix by its symmetric part (`asse_matrice_ops.py:75`, `upstream/astest/wdnp101a.comm:882`). Not needed for elastic stiffness and mass, which are symmetric. |
| `CHAR_CINE` | `char_cine_meca` or `char_cine_ther` or `char_cine_acou`, optional, list | — | *kinematic loads*. Kinematic boundary conditions (`AFFE_CHAR_CINE`) applied by elimination while assembling (`asse_matrice_ops.py:71`). Give the same `CHAR_CINE` to the stiffness and the mass so that both matrices hold the same constrained DOFs (`upstream/astest/sdll02b.comm:63`, `:65`). This is how a modal analysis uses kinematic supports. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `1` (default) or `2` for more output. Nothing is printed at level 1 (fixture log, `tests/fixtures/modal/output/run.mess:300`). |

## Patterns

### Stiffness and mass on one numbering

Source: `tests/fixtures/modal/input/run.comm:39`.

```python
RIGI = ASSE_MATRICE(MATR_ELEM=RIGI_EL, NUME_DDL=NUME)

MASS = ASSE_MATRICE(MATR_ELEM=MASS_EL, NUME_DDL=NUME)
```

### Kinematic supports, for a modal analysis

Source: `upstream/astest/sdll02b.comm:63`; `CALC_MODES` follows at line 70.

```python
MATASSR2 = ASSE_MATRICE(MATR_ELEM=MELR2, NUME_DDL=NUM2, CHAR_CINE=(CH2, CH3))

MATASSM2 = ASSE_MATRICE(MATR_ELEM=MELM2, NUME_DDL=NUM2, CHAR_CINE=(CH2, CH3))
```

## Pitfalls

- **Same `CHAR_CINE` on both matrices.** A kinematic support given to the stiffness but not to
  the mass leaves the two matrices with different constrained rows. Give the same list to both,
  as `sdll02b` does.
- **Dualized supports are not given here.** `AFFE_CHAR_MECA` supports go to `CALC_MATR_ELEM`
  (`CHARGE`); `CHAR_CINE` takes only `AFFE_CHAR_CINE` loads (catalog types `char_cine_*`).
- **One numbering.** Assembling the stiffness and the mass on two different `NUME_DDL` makes
  `CALC_MODES` work on inconsistent matrices; build one `NUME_DDL` and reuse it.

## See also

- French reference: U4.61.22 (from en/doc-ids.yaml, status: verified; French text:
  `en/docs/_src/U4.61.22.fr.md`; no English translation yet (Tier 2, not in `en/docs/scope.yaml`))
- Catalog: `en/commands/ASSE_MATRICE.json` (generated from `upstream/code_aster/Cata/Commands/asse_matrice.py:42`)
- Implementation: `upstream/code_aster/MacroCommands/asse_matrice_ops.py`
- Before: [CALC_MATR_ELEM](CALC_MATR_ELEM.md), [NUME_DDL](NUME_DDL.md),
  [AFFE_CHAR_CINE](AFFE_CHAR_CINE.md)
- Next steps: [CALC_MODES](CALC_MODES.md); all in one call: [ASSEMBLAGE](ASSEMBLAGE.md)
- Example: `tests/fixtures/modal/input/run.comm` (line 39)
- Example: `upstream/astest/sdll02b.comm` (line 63)
