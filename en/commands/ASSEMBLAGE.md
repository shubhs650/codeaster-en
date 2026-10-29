---
command: ASSEMBLAGE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/assemblage.py:80
doc_fr: U4.61.21
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 6.4)
examples: [supv003h, ssls141f, zzzz351b]
---

# ASSEMBLAGE — assemble matrices and vectors

> **Assisted reference.** Written in session from the pinned catalog, the solver source it
> calls, the message catalog, upstream test cases and the committed fixture runs. Every behavior
> claim cites its source. Not reviewed by an engineer.

Computes assembled matrices and vectors.

`ASSEMBLAGE` is the one-call form of the matrix path: for each requested matrix it runs
`CALC_MATR_ELEM`, builds the DOF numbering once (`NUME_DDL`) and assembles (`ASSE_MATRICE`),
and it can assemble load vectors the same way (`CALC_VECT_ELEM`, `ASSE_VECTEUR`)
(`upstream/code_aster/MacroCommands/assemblage_ops.py:143`, `:154`, `:161`). It returns no value:
each output is a new concept named with `CO("NAME")` under `MATRICE`, `VECTEUR` and
`NUME_DDL`. The stiffness occurrence is moved first so the numbering is built from it, with the
Lagrange multipliers of `CHARGE` (`:85`). Use it for a modal analysis when the element matrices
are not needed on their own (`upstream/astest/forma12a.comm:49`); the English builder writes the
explicit three-command form instead, as the modal fixture does.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Calcul des matrices et vecteurs assemblés» |
| Kind | `MACRO` |
| Result | `nume_ddl_sdaster`, `matr_asse_depl_r`, `matr_asse_pres_c`, `matr_asse_temp_r`, `matr_asse_depl_c`, `cham_no_sdaster` (depends on the keywords given) |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.61.21 — from en/doc-ids.yaml (status: proposed) |
| Scope tier | 2 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `MATR_ASSE`, `RIGI_MECA`, `MASS_MECA`, `CHARGE` |

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MODELE` | `modele_sdaster`, required | — | *model*. The model (passed to every `CALC_MATR_ELEM` call). |
| `CHAM_MATER` | `cham_mater`, optional | — | *material field*. The material field, passed to every element computation: needed for stiffness (`E`, `NU`) and mass (`RHO`). |
| `INST` | real, optional | `0.0` | *time step (pseudo-time)*. Time at which time-dependent material data are evaluated, as in `CALC_MATR_ELEM`. |
| `CARA_ELEM` | `cara_elem`, optional | — | *element properties*. Element properties (shell thickness, beam sections, discrete values), passed to every element computation (`upstream/astest/ssls141f.comm:139`). |
| `CHARGE` | `char_meca` or `char_ther` or `char_acou`, optional, list | — | *load*. The loads whose dualized boundary conditions are added to the stiffness and numbered (`assemblage_ops.py:126`); for `VECT_ASSE` they also supply the applied forces. Not passed to `RIGI_GEOM` (`:127`). |
| `CHAR_CINE` | `char_cine_meca` or `char_cine_ther` or `char_cine_acou`, optional | — | Kinematic boundary conditions (`AFFE_CHAR_CINE`), eliminated in every assembled matrix (`assemblage_ops.py:160`). |
| `NUME_DDL` | `nume_ddl_sdaster` or `CO`, required | — | *DOF numbering*. The DOF numbering: `CO("NAME")` to create it (it is built from the stiffness occurrence, or from `MODELE` and `CHARGE`, `assemblage_ops.py:27`), or an existing `NUME_DDL` to reuse. Creating one without `MATR_ASSE` is fatal (`MATRICE0_5`). |
| `MATR_ASSE` | factor keyword, optional, repeatable | — | *assembled matrices*. One assembled matrix to build. Repeat it for stiffness, mass, damping (`upstream/astest/forma12a.comm:54`). |
| `MATR_ASSE / MATRICE` | `CO`, required | — | The name of the assembled matrix to create, as `CO("NAME")`; after the call, `NAME` is a variable of the command file. |
| `MATR_ASSE / OPTION` | text, required | — | *option*. One of `'RIGI_MECA'`, `'MASS_MECA'`, `'MASS_MECA_DIAG'`, `'AMOR_MECA'`, `'RIGI_MECA_HYST'`, `'IMPE_MECA'`, `'ONDE_FLUI'`, `'RIGI_FLUI_STRU'`, `'MASS_FLUI_STRU'`, `'RIGI_ROTA'`, `'RIGI_GEOM'`, `'MECA_GYRO'`, … (17 values; see the .json). The matrix, with the meanings of `CALC_MATR_ELEM` `OPTION`: `'RIGI_MECA'` and `'MASS_MECA'` for a modal analysis. `'AMOR_MECA'` and `'RIGI_MECA_HYST'` need `RIGI_MECA` (and for `AMOR_MECA` also `MASS_MECA`) in the same call (`MATRICE0_10`, `MATRICE0_11`, `assemblage_ops.py:104`). |
| `MATR_ASSE / GROUP_MA` | element group, optional, list | — | *element group*. Only when `is_in("OPTION", ('RIGI_GYRO', 'MECA_GYRO', 'IMPE_MECA', 'AMOR_MECA', 'MASS_MECA', 'RIGI_MECA', 'MASS_MECA_DIAG','MASS_FLUI_STRU'))`. Compute this matrix on these element groups only. |
| `MATR_ASSE / MODE_FOURIER` | integer, optional | `0` | Only when `equal_to("OPTION", 'RIGI_MECA')`; or `equal_to("OPTION", 'RIGI_GEOM')`; or `equal_to("OPTION", 'RIGI_THER')`. Fourier harmonic number for `AXIS_FOURIER` models. Not used in Tier 2. |
| `MATR_ASSE / SIEF_ELGA` | `cham_elem`, required | — | *stress at Gauss points*. Only when `equal_to("OPTION", 'RIGI_GEOM')`. The prestress for the geometric stiffness (`RIGI_GEOM`), buckling (Tier 3). |
| `MATR_ASSE / AMOR_FLUI` | text, optional | `'OUI'` | One of `'OUI'`, `'NON'`. Only when `equal_to("OPTION", 'AMOR_MECA')`. As in `CALC_MATR_ELEM`: include the damping of fluid elements. Out of scope. |
| `MATR_ASSE / VNOR` | real, optional | `1.0` | One of `1.0`, `-1.0`. Only when `equal_to("OPTION", 'AMOR_MECA')`; or `equal_to("OPTION", 'IMPE_MECA')`; or `equal_to("OPTION", 'AMOR_ACOU')`. As in `CALC_MATR_ELEM`: sign of the normal velocity of impedance boundaries. Out of scope. |
| `MATR_ASSE / TYPE_AMOR` | text, optional | `'TOUT'` | One of `'TOUT'`, `'ABSO'`. Only when `equal_to("OPTION", 'AMOR_MECA')`. As in `CALC_MATR_ELEM`: full damping or absorbing-boundary terms only. |
| `VECT_ASSE` | factor keyword, optional, repeatable | — | One assembled load vector to build (`assemblage_ops.py:167`), from the loads of `CHARGE` and of its own `CHARGE`. At least one load is needed (`MATRICE0_8`). Used by solvers that take vectors, such as `DYNA_VIBRA` (Tier 3). |
| `VECT_ASSE / VECTEUR` | `CO`, required | — | The name of the assembled vector to create, as `CO("NAME")` (`upstream/astest/ahlv101a.comm:63`). Not the glossary's shell reference vector: in `ASSEMBLAGE`, `VECTEUR` is an output name. |
| `VECT_ASSE / OPTION` | text, required | — | *option*. One of `'CHAR_MECA'`, `'CHAR_ACOU'`, `'CHAR_THER'`. `'CHAR_MECA'` mechanical loads, `'CHAR_THER'` thermal, `'CHAR_ACOU'` acoustic (which needs `CHAM_MATER`, `MATRICE0_7`). |
| `VECT_ASSE / CHARGE` | `char_meca`, optional, list | — | *load*. Only when `equal_to("OPTION", 'CHAR_MECA')`. Extra mechanical loads for this vector, added to the command-level `CHARGE` (`assemblage_ops.py:176`). |
| `VECT_ASSE / MODE_FOURIER` | integer, optional | `0` | Only when `equal_to("OPTION", 'CHAR_MECA')`. Fourier harmonic number for `AXIS_FOURIER` models. |
| `VECT_ASSE / CHARGE` | `char_ther`, optional, list | — | *load*. Only when `equal_to("OPTION", 'CHAR_THER')`. Extra thermal loads for this vector. |
| `VECT_ASSE / CHARGE` | `char_acou`, optional, list | — | *load*. Only when `equal_to("OPTION", 'CHAR_ACOU')`. Extra acoustic loads for this vector. |
| `TITRE` | text, optional | — | *title*. A title. Optional. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. Verbosity passed to `NUME_DDL`: `1` prints the system size, as in the modal fixture log. |

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at least one of `MATR_ASSE`, `VECT_ASSE` must be given (`AU_MOINS_UN`).

## Patterns

### Stiffness and mass for a modal analysis

Source: `upstream/astest/forma12a.comm:49`; `CALC_MODES` follows at line 60.

```python
ASSEMBLAGE(
    MODELE=MODELE,
    CHAM_MATER=CHMAT,
    CHARGE=BLOCAGE,
    NUME_DDL=CO("NUMEDDL"),
    MATR_ASSE=(
        _F(MATRICE=CO("RIGIDITE"), OPTION="RIGI_MECA"),
        _F(MATRICE=CO("MASSE"), OPTION="MASS_MECA"),
    ),
)
```

### Shell model: element properties

Source: `upstream/astest/ssls141f.comm:139`.

```python
ASSEMBLAGE(
    MODELE=MO2,
    CHAM_MATER=CHMAT2,
    CARA_ELEM=EP2,
    CHARGE=CL2,
    NUME_DDL=CO("NU2"),
    MATR_ASSE=(
        _F(MATRICE=CO("MATASS2"), OPTION="RIGI_MECA"),
        _F(MATRICE=CO("MATASM2"), OPTION="MASS_MECA"),
    ),
)
```

### The equivalent explicit form

What the English builder writes (`Builder.modal`), from `tests/fixtures/modal/input/run.comm:33`:
`CALC_MATR_ELEM` twice, `NUME_DDL` from the stiffness, `ASSE_MATRICE` twice. The two forms
give the same matrices (`assemblage_ops.py:143`–`:163` calls exactly these commands).

## Pitfalls

- **Outputs are `CO()` names.** `ASSEMBLAGE` is not assigned (`X = ASSEMBLAGE(...)` is wrong):
  each output is named with `CO("NAME")`, then used as `NAME` (`upstream/astest/forma12a.comm:61`).
- **The stiffness defines the numbering.** The multipliers of `CHARGE` are numbered from the
  `RIGI_MECA` occurrence, which the macro moves first (`assemblage_ops.py:85`); without a
  stiffness occurrence, the numbering comes from `MODELE` and `CHARGE`.
- **Vectors with an existing numbering need the same `CHARGE`.** Assembling only vectors on a
  `NUME_DDL` built earlier without giving `CHARGE` again warns `MATRICE0_6`: the Dirichlet
  rows may not match.

## See also

- French reference: U4.61.21 (from en/doc-ids.yaml, status: proposed; translation:
  `en/docs/U4.61.21.md` once task 5.x lands)
- Catalog: `en/commands/ASSEMBLAGE.json` (generated from `upstream/code_aster/Cata/Commands/assemblage.py:80`)
- Implementation: `upstream/code_aster/MacroCommands/assemblage_ops.py`
- Same steps one by one: [CALC_MATR_ELEM](CALC_MATR_ELEM.md), [NUME_DDL](NUME_DDL.md),
  [ASSE_MATRICE](ASSE_MATRICE.md)
- Next steps: [CALC_MODES](CALC_MODES.md)
- Example: `upstream/astest/forma12a.comm` (line 49)
- Example: `upstream/astest/ssls141f.comm` (line 139)
