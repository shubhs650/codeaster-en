---
command: DEFI_FONCTION
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/defi_fonction.py:43
doc_fr: U4.31.02
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3c)
examples: [ssll06a, forma00a, ssll11b, sdll23a, fdlv116a, sdnd125e, zzzz270b]
---

# DEFI_FONCTION — define function

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

`DEFI_FONCTION` defines a tabulated function of one real parameter: a list of points
(abscissa, ordinate), the parameter's name (`NOM_PARA`), how to interpolate between the points
(`INTERPOL`) and what to do outside them (`PROL_GAUCHE`, `PROL_DROITE`). The result is a
`fonction_sdaster` (real values) or, with `VALE_C`, a `fonction_c` (complex values). Other
commands evaluate it when they need a value: a load multiplier in `MECA_STATIQUE`
(`EXCIT/FONC_MULT`, parameter `'INST'`), a temperature-dependent material property in
`DEFI_MATERIAU/ELAS_FO` (parameter `'TEMP'`), or a load that varies in space in
`AFFE_CHAR_MECA_F` (parameter `'X'`, `'Y'` or `'Z'`). The parameter name must be the one the
calling command evaluates: the function is evaluated by name, so a function of `'X'` given where
`'INST'` is read does not adapt to it. The decisions it encodes are the data points, the
interpolation law and whether a value outside the data range is an error (the default) or an
extrapolation.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Définit une fonction réelle ou complexe d'une variable réelle» |
| Kind | `OPER` |
| Result | `fonction_sdaster`, `fonction_c` (depends on the keywords given) |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.31.02 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `NOM_PARA`, `VALE`, `PROL_DROITE`, `GAUCHE`, `INTERPOL`, `PRES_REP`, `FONC_MULT` |

COMMAND-SET lists `PRES_REP` and `FONC_MULT` here because they are where a function is used:
`PRES_REP` of `AFFE_CHAR_MECA_F` takes a function of space, `FONC_MULT` of `MECA_STATIQUE` a
function of time. Neither is a keyword of `DEFI_FONCTION`; see the patterns below.

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `NOM_PARA` | text, required | — | *parameter name*. One of `'DX'`, `'DY'`, `'DZ'`, `'DRX'`, `'DRY'`, `'DRZ'`, `'DTAN'`, `'TEMP'`, `'TSEC'`, `'INST'`, `'X'`, `'Y'`, … (44 values; see the .json). The name of the abscissa. Use `'INST'` for a function of time (load multiplier, `upstream/astest/ssll11b.comm:158`), `'TEMP'` for a function of temperature (material data, `upstream/astest/ssll06a.comm:49`), `'X'`/`'Y'`/`'Z'` for a function of position (`upstream/astest/forma00a.comm:84`), `'FREQ'` for a function of frequency. |
| `NOM_RESU` | text, optional | `'TOUTRESU'` | *result name*. A name for the ordinate, stored with the function (`upstream/code_aster/CodeCommands/defi_fonction.py:115`). Some commands (`CALC_FONCTION`, `DEFI_MATERIAU`, …) check that the parameter and result names suit their use, for example a tensile curve with `NOM_PARA='EPSI'` and `NOM_RESU='SIGM'` (U4.31.02 §3.2). Otherwise leave the default. |
| `VALE` | real, optional, list, at least 2 | — | *value(s)*. The points as one flat list of pairs: x1, y1, x2, y2, ... (catalog translation "Coordinates"). The usual form. The number of values must be even (`UTILITAI2_67`, see Pitfalls). |
| `ABSCISSE` | real, optional, list, at least 2 | — | *abscissas*. The x values, as a separate list; give the y values in `ORDONNEE`. Convenient when the two lists are computed in Python (`upstream/astest/sdnd125e.comm:148`). |
| `ORDONNEE` | real, required, list, at least 2 | — | *ordinates*. Only when `exists("ABSCISSE")`. The y values, one per abscissa; lists of different lengths stop the command (`UTILITAI2_77`, `upstream/code_aster/CodeCommands/defi_fonction.py:94`). |
| `VALE_C` | real, optional, list, at least 2 | — | *complex values*. A complex function, as a flat list of triplets: x, real part, imaginary part (`upstream/astest/zzzz180a.comm:66`). Used for frequency-domain data (spectra, transfer functions); not needed in Tier 1. |
| `VALE_PARA` | `listr8_sdaster`, optional | — | *parameter values*. The x values as a list of reals made by `DEFI_LIST_REEL` (catalog translation "List of X-coordinate"); give the y values in `VALE_FONC` (`upstream/astest/fdlv116a.comm:171`). |
| `VALE_FONC` | `listr8_sdaster`, required | — | *function values*. Only when `exists("VALE_PARA")`. The y values as a `DEFI_LIST_REEL` list (catalog translation "List of Y-coordinate"), as long as `VALE_PARA`. |
| `NOEUD_PARA` | node, optional, list | — | *parameter nodes*. A function of the curvilinear abscissa along a line of nodes (catalog translation "Nodes as X-coordinate"): the abscissa of each point is its distance along the mesh from the first node (`upstream/bibfor/utilitai/defcur.F90:22`); `VALE_Y` gives the values. Takes node names, which our meshes from Gmsh do not carry meaningfully; out of Tier 1 use (`upstream/astest/sdll152c.comm:64`). |
| `MAILLAGE` | `maillage_sdaster`, required | — | *mesh*. Only when `exists("NOEUD_PARA")`. The mesh the nodes belong to. |
| `VALE_Y` | real, required, list | — | Only when `exists("NOEUD_PARA")`. One value per node of `NOEUD_PARA` (catalog translation "Y-coordinates"); a different count stops the command (`UTILITAI2_69`). |
| `INTERPOL` | text, optional, list of up to 2 | `'LIN'` | *interpolation*. One of `'LIN'`, `'LOG'`. How values between two points are computed: linear (`'LIN'`) or linear in the logarithm (`'LOG'`). One value applies to both axes; two values set the abscissa and the ordinate separately, so `('LOG', 'LIN')` is logarithmic in x only (`upstream/code_aster/CodeCommands/defi_fonction.py:117`). Keep `'LIN'` for loads and material data. `'LOG'` suits spectra over frequency decades (`upstream/astest/sdll23a.comm:301`); it needs all abscissas (and, on the ordinate, all ordinates) > 0 (`UTILITAI2_71`) and a real function (`UTILITAI5_92`). |
| `PROL_DROITE` | text, optional | `'EXCLU'` | *right extrapolation*. One of `'CONSTANT'`, `'LINEAIRE'`, `'EXCLU'`. What the function returns for a parameter above the last abscissa: `'EXCLU'` (the default) refuses, and the command that evaluates the function stops with `FONCT0_20` (`upstream/bibfor/utilitai/fointr.F90:216`); `'CONSTANT'` returns the last ordinate; `'LINEAIRE'` extends the last segment. Set `'CONSTANT'` for material data that may be evaluated a little outside the measured range (`upstream/astest/ssll06a.comm:49`); keep `'EXCLU'` when a value outside the range would mean an input error. |
| `PROL_GAUCHE` | text, optional | `'EXCLU'` | *left extrapolation*. One of `'CONSTANT'`, `'LINEAIRE'`, `'EXCLU'`. Same, below the first abscissa (`FONCT0_19`, `upstream/bibfor/utilitai/fointr.F90:143`). |
| `VERIF` | text, optional | `'CROISSANT'` | *check*. One of `'CROISSANT'`, `'NON'`. `'CROISSANT'` (the default) requires strictly increasing abscissas and stops otherwise (`FONCT0_44`); `'NON'` sorts the points by abscissa instead (`upstream/code_aster/CodeCommands/defi_fonction.py:96`). Keep the default: an unsorted list is more often a typing error than a choice. `'NON'` is for computed lists that are known to be unsorted (`upstream/astest/zzzz270b.comm:231`). |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `2` prints the function. Only the Fortran path (`NOEUD_PARA`) is seen to print at level 2 (`upstream/bibfor/op/op0003.F90:289`); the Python implementation that handles the other forms does not read `INFO` (`upstream/code_aster/CodeCommands/defi_fonction.py:45`). U4.31.02 §3.10 says level 2 prints the parameters and the first 10 values; TODO(verify) by a run that 17.4 still does so for `VALE`. |
| `TITRE` | text, optional | — | *title*. A free title stored with the function. |

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: exactly one of `VALE`, `VALE_C`, `VALE_PARA`, `NOEUD_PARA`, `ABSCISSE` must be given (`UN_PARMI`).

## Patterns

### Temperature-dependent property, constant outside the data

A function of temperature for `DEFI_MATERIAU/ELAS_FO`. With `PROL_*='CONSTANT'` the material
can be evaluated at any temperature; this one is a constant 2e11 written as a function.

Source: `upstream/astest/ssll06a.comm:49`.

```python
E1 = DEFI_FONCTION(
    NOM_PARA="TEMP", PROL_DROITE="CONSTANT", PROL_GAUCHE="CONSTANT", VALE=(21.1, 2e11, 21.101, 2e11)
)
```

### Load ramp in time

A linear multiplier, 0 at `INST=0` and 10 at `INST=10`, applied with `FONC_MULT`; the static
analysis is solved at each time of `LT` (0.5, 1.0, 1.5), so the load is multiplied by 0.5, 1.0
and 1.5.

Source: `upstream/astest/ssll11b.comm:158`.

```python
F1 = DEFI_FONCTION(NOM_PARA="INST", VALE=(0.0, 0.0, 10.0, 10.0))

LT = DEFI_LIST_REEL(DEBUT=0.5, INTERVALLE=_F(JUSQU_A=1.5, PAS=0.5))

V = MECA_STATIQUE(
    MODELE=MOD, CHAM_MATER=CHMAT, CARA_ELEM=CAREL, LIST_INST=LT, EXCIT=_F(CHARGE=CH, FONC_MULT=F1)
)
```

### Pressure that varies with position (hydrostatic)

A pressure of 200000 at y = 0 falling linearly to 0 at y = 4, applied by `AFFE_CHAR_MECA_F`,
which evaluates the function at the position of the loaded faces. This is the form for
hydrostatic pressure; `FONC_MULT` cannot do it, because it multiplies the whole load by a
function of time.

Source: `upstream/astest/forma00a.comm:84`.

```python
f_y = DEFI_FONCTION(NOM_PARA="Y", VALE=(0.0, 200000.0, 4.0, 0.0))

charg = AFFE_CHAR_MECA_F(MODELE=modl, PRES_REP=_F(GROUP_MA=("LDA",), PRES=f_y))
```

The defaults `PROL_*='EXCLU'` hold here: the loaded edge must lie within 0 ≤ y ≤ 4, or the
evaluation stops with `FONCT0_19`/`FONCT0_20`.

### Abscissas and ordinates as two lists

Source: `upstream/astest/sdnd125e.comm:148`.

```python
FDECR_1 = DEFI_FONCTION(NOM_PARA="DX", ABSCISSE=X, ORDONNEE=Y1)
```

### Logarithmic interpolation for a spectrum

Source: `upstream/astest/sdll23a.comm:301`.

```python
ACCE_X = DEFI_FONCTION(
    NOM_PARA="FREQ", INTERPOL="LOG", VALE=(0.2, 2.4, 2.0, 25.0, 7.70, 25.0, 20.0, 10.0, 100.0, 10.0)
)
```

### Points from `DEFI_LIST_REEL` lists

`LINST` and `ACCE` are two lists of the same length built earlier in the file.

Source: `upstream/astest/fdlv116a.comm:171`.

```python
ACCE_T = DEFI_FONCTION(NOM_PARA="INST", VALE_PARA=LINST, VALE_FONC=ACCE)
```

## Pitfalls

- **Evaluated outside its range.** The default extrapolation is `'EXCLU'` on both sides, so
  a function evaluated below its first or above its last abscissa stops the run where it is
  used, not where it is defined (`FONCT0_19`, `FONCT0_20`, `upstream/bibfor/utilitai/fointr.F90:143`).
  Typical cases: a material function of `'TEMP'` and a temperature outside the table; a load
  ramp of `'INST'` and a `LIST_INST` that runs past its last time. Extend the data or set
  `PROL_GAUCHE`/`PROL_DROITE`.
- **A ramp that starts at zero, solved without `LIST_INST`.** Without `INST` or `LIST_INST`,
  `MECA_STATIQUE` solves at `INST=0.0` (catalog default, `upstream/code_aster/Cata/Commands/meca_statique.py:41`;
  our fixture logs show it filled in, `tests/fixtures/solid_static/output/run.mess:274`). A
  `FONC_MULT` that is 0 at time 0 then multiplies the load by zero.
- **Wrong parameter name.** The calling command evaluates the function by the name it expects.
  `ELAS_FO` reads `'TEMP'` (with `AFFE_MATERIAU/AFFE_VARC`), `FONC_MULT` reads `'INST'`, a
  space-varying load reads `'X'`, `'Y'` or `'Z'`. TODO(verify) the message raised when the name
  does not match, against U4.31.02.
- **Odd number of values in `VALE`.** The command stops, but with `UTILITAI2_67`, whose text
  says that triplets are needed (`upstream/code_aster/CodeCommands/defi_fonction.py:68`): the
  message meant for `VALE_C`. Read it as "`VALE` needs pairs". The `VALE_C` check in turn
  raises `UTILITAI2_66` ("not enough values", line 77).
- **Abscissas not increasing.** `FONCT0_44` names the function. Usually a typing error in
  `VALE` (a y value read as an x value after a missing number); `VERIF='NON'` hides it by
  sorting.
- **`'LOG'` with zero or negative values.** `INTERPOL='LOG'` needs strictly positive
  abscissas (and ordinates when it applies to them); a ramp that starts at 0 cannot use it
  (`UTILITAI2_71`, `upstream/code_aster/CodeCommands/defi_fonction.py:124`).

## See also

- French reference: U4.31.02 (French text: `en/docs/_src/U4.31.02.fr.md`; translation: `en/docs/U4.31.02.md`)
- Catalog: `en/commands/DEFI_FONCTION.json` (generated from `upstream/code_aster/Cata/Commands/defi_fonction.py:43`)
- Implementation: `upstream/code_aster/CodeCommands/defi_fonction.py`; `upstream/bibfor/op/op0003.F90`
  (`NOEUD_PARA` only); evaluation `upstream/bibfor/utilitai/fointr.F90`
- Related: `DEFI_CONSTANTE` (a constant as a function), `FORMULE` (a function given as a
  Python expression), `DEFI_LIST_REEL`
- Used by: [AFFE_CHAR_MECA](AFFE_CHAR_MECA.md) (through `AFFE_CHAR_MECA_F`),
  [DEFI_MATERIAU](DEFI_MATERIAU.md) (`ELAS_FO`), [AFFE_CHAR_CINE](AFFE_CHAR_CINE.md) (through
  `AFFE_CHAR_CINE_F`), `MECA_STATIQUE` (`EXCIT/FONC_MULT`)
- Example: `upstream/astest/ssll06a.comm` (lines 49, 53, 57)
- Example: `upstream/astest/ssll11b.comm` (line 158)
- Example: `upstream/astest/forma00a.comm` (line 84)
- Example: `upstream/astest/func02b.py` (lines 30, 31, 38, 39)
- Example: `upstream/astest/ssll07a.comm` (lines 52, 56, 60)
