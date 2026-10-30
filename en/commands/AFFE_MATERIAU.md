---
command: AFFE_MATERIAU
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/affe_materiau.py:26
doc_fr: U4.43.03
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3b)
examples: [zzzz505d, sslv114a, ssls147a, ssnp126a, tpls102a, zzzz118a, ssnl127a]
---

# AFFE_MATERIAU — assign material

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

`AFFE_MATERIAU` builds a material field (`cham_mater`): it says which material
(`DEFI_MATERIAU`) holds on which element groups, and optionally which external state variables
(temperature, drying, irradiation, ...) act on them (`AFFE_VARC`). The analysis commands take it
as `CHAM_MATER`. It is built on the mesh (`MAILLAGE`) or on a model (`MODELE`), and
assignments can overlap: an element covered by several `AFFE` occurrences gets the material of
the last one (`upstream/bibfor/modelisa/rcmate.F90:73`, `upstream/bibfor/calculel/tecart.F90:32`).
The decisions it encodes are the material of each part and, through `AFFE_VARC`, the thermal
state of the structure: a thermal expansion coefficient (`ALPHA`) only acts where a temperature
and its reference value are assigned here.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Affecter des matériaux à des zones géométriques d'un maillage» |
| Kind | `MACRO` |
| Result | `cham_mater` |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.43.03 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `AFFE`, `GROUP_MA`, `MATER`, `AFFE_VARC`, `NOM_VARC`, `TEMP`, `VALE_REF`, `CHAM_GD` |

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MAILLAGE` | `maillage_sdaster` or `maillage_p`, optional | — | *mesh*. The mesh the field is built on. The usual form (all our fixtures). Give `MAILLAGE`, `MODELE` or both. |
| `MODELE` | `modele_sdaster`, optional | — | *model*. Build the field on the mesh of this model (`upstream/code_aster/MacroCommands/affe_materiau_ops.py:45`); with `MODELE`, element groups are resolved against the model (`upstream/bibfor/modelisa/rcmate.F90:82`). If `MAILLAGE` is given too, it must be the model's mesh (`MODELISA2_11`). |
| `AFFE` | factor keyword, optional, repeatable | — | One material assignment (catalog translation: "Material assignement"). Repeat it for parts with different materials (`upstream/astest/ssnp126a.comm:62`). An element in several occurrences takes the material of the last one, so a `TOUT='OUI'` occurrence followed by `GROUP_MA` occurrences sets a default material and then overrides it on some groups. |
| `AFFE / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Every element of the mesh. |
| `AFFE / GROUP_MA` | element group, optional, list | — | *element group*. The groups that get this material. Give at least every group of the model that has a finite element needing a material; boundary face elements that only carry a pressure do not need one, as our `solid_static` fixture shows (material on `SOLID` only, `tests/fixtures/solid_static/input/run.comm:27`). |
| `AFFE / MATER` | `mater_sdaster`, required, list of up to 30 | — | *material*. The material from `DEFI_MATERIAU`. Normally one. A list assigns several materials to the same elements (`upstream/code_aster/MacroCommands/affe_materiau_ops.py:228`); a list is needed only when the nonlinear behavior is built with `DEFI_COMPOR` (multifiber beams, polycrystals); U4.43.03 §4.3.3 limits it to 26 materials, the catalog to 30. |
| `CHAM_MATER` | `cham_mater`, optional | — | *material field*. Copy the material assignments of an existing field instead of giving `AFFE` (`upstream/code_aster/MacroCommands/affe_materiau_ops.py:52`), typically to add `AFFE_VARC` to it (`upstream/astest/ssnl127a.comm:83`). The source field must be on the same mesh (`MATERIAL2_60`); its own external state variables are not copied (warning `MATERIAL2_61`). |
| `AFFE_COMPOR` | factor keyword, optional, repeatable | — | Behavior assignment (catalog translation: "Behaviour assignement"): assigns a behavior object from `DEFI_COMPOR`. The catalog comment limits it to multifiber beams "for now" (`upstream/code_aster/Cata/Commands/affe_materiau.py:47`). Out of Tier 1 scope. |
| `AFFE_COMPOR / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. |
| `AFFE_COMPOR / GROUP_MA` | element group, optional, list | — | *element group*. |
| `AFFE_COMPOR / COMPOR` | `compor_sdaster`, required | — | *behavior*. The object from `DEFI_COMPOR`. |
| `AFFE_VARC` | factor keyword, optional, repeatable | — | *external state variable assignment*. Imposes a known field of a state variable (temperature, drying, hydration, irradiation, ...) on the material, for the whole analysis. The material parameters that depend on it (`ELAS_FO` functions of `TEMP`) are evaluated with it, and `TEMP` produces thermal strain where the material has `ALPHA`. Without `TOUT` or `GROUP_MA` it applies to the whole mesh (`upstream/code_aster/MacroCommands/affe_materiau_ops.py:143`). |
| `AFFE_VARC / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. |
| `AFFE_VARC / GROUP_MA` | element group, optional, list | — | *element group*. Restrict the variable to these groups. |
| `AFFE_VARC / NOM_VARC` | text, required | — | *external state variable name*. One of `'TEMP'`, `'GEOM'`, `'CORR'`, `'IRRA'`, `'HYDR'`, `'SECH'`, `'EPSA'`, `'M_ACIER'`, `'M_ZIRC'`, `'NEUT1'`, `'NEUT2'`, `'NEUT3'`, `'PTOT'`. Tier 1/2 use `'TEMP'` (temperature). The others serve concrete (`'HYDR'` hydration, `'SECH'` drying), metallurgy (`'M_ACIER'`, `'M_ZIRC'`) and user variables (`'NEUT1'`–`'NEUT3'`); out of scope. |
| `AFFE_VARC / CHAM_GD` | `cham_gd_sdaster`, optional | — | *field (physical quantity)*. A field that is constant in time, for example a temperature field built with `CREA_CHAMP(TYPE_CHAM='NOEU_TEMP_R', ...)` (`upstream/astest/tpls102a.comm:62`) or computed by a linear thermal solve (`upstream/astest/hplv102a.comm:58`). Use it for a static analysis under one temperature distribution. |
| `AFFE_VARC / EVOL` | `evol_sdaster`, optional | — | *time-dependent result*. A result with several time steps, typically the `evol_ther` of a thermal transient (`THER_LINEAIRE`, `THER_NON_LINE`); the variable is read at each time of the mechanical analysis (`upstream/astest/zzzz118a.comm:146`). |
| `AFFE_VARC / NOM_CHAM` | text, optional | — | *field name*. One of `'TEMP'`, `'CORR'`, `'IRRA'`, `'NEUT'`, `'GEOM'`, `'HYDR_ELNO'`, `'HYDR_NOEU'`, `'META_ELNO'`, `'META_NOEU'`, `'EPSA_ELNO'`, `'EPSA_NOEU'`, `'PTOT'`, … (14 values; see the .json). Only when `exists("EVOL")`. The field of `EVOL` to read. Default from `NOM_VARC`: `'TEMP'` for `'TEMP'`, `'HYDR_ELNO'` for `'HYDR'`, `'META_ELNO'` for the metallurgical phases, `'NEUT'` for `'NEUT1'`–`'NEUT3'` (`upstream/code_aster/MacroCommands/affe_materiau_ops.py:178`). |
| `AFFE_VARC / PROL_DROITE` | text, optional | `'EXCLU'` | *right extrapolation*. One of `'CONSTANT'`, `'LINEAIRE'`, `'EXCLU'`. Only when `exists("EVOL")`. What to do when the mechanical analysis asks for a time after the last time of `EVOL`. `'EXCLU'` (the default) refuses it; `'CONSTANT'` keeps the last field; `'LINEAIRE'` extrapolates linearly. With `'EXCLU'` the run stops with `UTILITAI8_33` ("Extrapolation cannot be made on the right") followed by `UTILITAI8_37`, which names the result, field and time (`upstream/bibfor/resu_util/rsinch.F90:225`, called with stop level 2 by `upstream/bibfor/calculel/vrcin1.F90:304`); `PROL_GAUCHE` gives `UTILITAI8_32` (U4.43.03 §4.4.4). |
| `AFFE_VARC / PROL_GAUCHE` | text, optional | `'EXCLU'` | *left extrapolation*. One of `'CONSTANT'`, `'LINEAIRE'`, `'EXCLU'`. Only when `exists("EVOL")`. Same, before the first time of `EVOL`. |
| `AFFE_VARC / FONC_INST` | `fonction_sdaster` or `formule`, optional | — | Only when `exists("EVOL")`. A function of time attached to the `EVOL` reading (`upstream/code_aster/MacroCommands/affe_materiau_ops.py:192`). It maps the time of the analysis to the time of `EVOL`: `t_evol = FONC_INST(t_calc)`. Use it to shift the thermal transient, or to repeat one computed temperature cycle for a cyclic mechanical load (U4.43.03 §4.4.4; test case `zzzz223a`). |
| `AFFE_VARC / VALE_REF` | real, required | — | *reference state value*. Only when `is_in("NOM_VARC", ('TEMP','SECH'))`. For `'TEMP'`, the reference (stress-free) temperature T_ref: thermal strain is ALPHA × (T − T_ref) (`upstream/bibfor/modelisa/verift.F90:264`), and `ELAS_FO/ALPHA` is re-based from `TEMP_DEF_ALPHA` to it (`upstream/bibfor/mate_util/alfint.F90:192`). Usually the assembly temperature, for example 20 °C (`upstream/astest/zzzz118a.comm:146`). |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `2` prints the content of the material field (`upstream/bibfor/op/op0006.F90:99`). |

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at least one of `MAILLAGE`, `MODELE` must be given (`AU_MOINS_UN`).
- command: exactly one of `AFFE`, `CHAM_MATER` must be given (`UN_PARMI`).
- `AFFE`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- `AFFE_COMPOR`: exactly one of `TOUT`, `GROUP_MA` must be given (`UN_PARMI`).
- `AFFE_VARC`: at most one of `GROUP_MA`, `TOUT` may be given (`EXCLUS`).
- `AFFE_VARC`: exactly one of `EVOL`, `CHAM_GD` must be given (`UN_PARMI`).

## Patterns

### One material on one group

Source: `tests/fixtures/solid_static/input/run.comm:27`.

```python
MATE = AFFE_MATERIAU(MAILLAGE=MAIL, AFFE=_F(GROUP_MA="SOLID", MATER=ACIER))
```

### One material everywhere

Source: `upstream/astest/zzzz505d.py:34`.

```python
mater = AFFE_MATERIAU(MAILLAGE=mesh, AFFE=_F(TOUT="OUI", MATER=acier))
```

### A default material, overridden on one group

The second occurrence wins on `CUBEDEG`.

Source: `upstream/astest/ssnp126a.comm:62`.

```python
CM = AFFE_MATERIAU(
    MAILLAGE=MA, AFFE=(_F(TOUT="OUI", MATER=ACIER), _F(GROUP_MA="CUBEDEG", MATER=BOND))
)
```

### Static temperature field

`TEMP1` is a nodal temperature field from `CREA_CHAMP` (lines 53–67 of the same file);
`VALE_REF=0` is the stress-free temperature. `ACIER` has `ALPHA=1.0e-5`.

Source: `upstream/astest/tpls102a.comm:71`.

```python
CHMAT = AFFE_MATERIAU(
    MAILLAGE=MAIL,
    AFFE=_F(TOUT="OUI", MATER=ACIER),
    AFFE_VARC=_F(NOM_VARC="TEMP", CHAM_GD=TEMP1, VALE_REF=0),
)
```

### Temperature history from a thermal analysis

`TEMPER1` is a transient thermal result; its `TEMP` field is read at each mechanical time.

Source: `upstream/astest/zzzz118a.comm:143`.

```python
CHMAT1 = AFFE_MATERIAU(
    MAILLAGE=MA,
    AFFE=_F(GROUP_MA=("STRIA1", "STRIA2", "SQUA"), MATER=MAT1),
    AFFE_VARC=_F(TOUT="OUI", EVOL=TEMPER1, NOM_VARC="TEMP", NOM_CHAM="TEMP", VALE_REF=20.0),
)
```

### Add a state variable to an existing material field

Source: `upstream/astest/ssnl127a.comm:83`.

```python
CHMAT1 = AFFE_MATERIAU(
    MAILLAGE=MA, CHAM_MATER=CHSIMPL, AFFE_VARC=_F(NOM_VARC="CORR", CHAM_GD=CHCOR)
)
```

## Pitfalls

- **Elements left without material.** `AFFE_MATERIAU` does not check that every element of the
  model has a material; the analysis does, element by element, and stops with `CALCUL_20`
  ("the material is needed on element ..."), whose advice is to check `CHAM_MATER` and the
  `AFFE_MATERIAU` assignments (`upstream/bibfor/calcul/jevech.F90:190`). Assign the material
  by `TOUT='OUI'` or list every structural group.
- **Overlapping occurrences.** The last `AFFE` occurrence that covers an element wins
  (`upstream/bibfor/calculel/tecart.F90:32`). Put the general assignment first and the
  exceptions after it; the reverse order silently overrides the exceptions.
- **Thermal expansion needs `AFFE_VARC`.** `ALPHA` in `DEFI_MATERIAU` does nothing unless
  `AFFE_VARC` assigns `NOM_VARC='TEMP'` with a field and `VALE_REF`
  (`upstream/bibfor/modelisa/verift.F90:104`). With `ELAS_FO` and a temperature-dependent
  `ALPHA`, elements with the material but no reference temperature stop the run (`MATERIAL1_2`).
- **`VALE_REF` is not `TEMP_DEF_ALPHA`.** `VALE_REF` is the stress-free temperature of the
  structure; `TEMP_DEF_ALPHA` (in `DEFI_MATERIAU/ELAS_FO`) is the temperature the `ALPHA` data
  are measured from. See [DEFI_MATERIAU](DEFI_MATERIAU.md).
- **Mesh and model mismatch.** With both `MAILLAGE` and `MODELE`, the model must be built on
  that mesh (`MODELISA2_11`); with `CHAM_MATER`, the source field must be on the same mesh
  (`MATERIAL2_60`). Rebuild the material field after `CREA_MAILLAGE`, which makes a new mesh.

## See also

- French reference: U4.43.03 (French text: `en/docs/_src/U4.43.03.fr.md`; translation: `en/docs/U4.43.03.md`)
- Catalog: `en/commands/AFFE_MATERIAU.json` (generated from `upstream/code_aster/Cata/Commands/affe_materiau.py:26`);
  `AFFE_VARC` from `upstream/code_aster/Cata/Commons/c_affe_varc.py:25`
- Implementation: `upstream/code_aster/MacroCommands/affe_materiau_ops.py`;
  `upstream/bibfor/op/op0006.F90`
- Before: `DEFI_MATERIAU`; for `AFFE_VARC`, `CREA_CHAMP` or a thermal analysis
- Next steps: `MECA_STATIQUE` and the other analyses (`CHAM_MATER=`)
- Example: `upstream/astest/zzzz505d.py` (lines 34, 154)
- Example: `upstream/astest/sslv114a.comm` (lines 35, 37)
- Example: `upstream/astest/tpls102a.comm` (line 71)
- Example: `upstream/astest/zzzz118a.comm` (line 143)
- Example: `tests/fixtures/solid_static/input/run.comm` (line 27)
