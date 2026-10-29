---
command: AFFE_CARA_ELEM
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/affe_cara_elem.py:481
doc_fr: U4.42.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3b)
examples: [zzzz505d, sslx102f, ssnl130f, tpls102a, ssls119c, sdll135f, ssnd112a]
---

# AFFE_CARA_ELEM — assign element properties

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.

`AFFE_CARA_ELEM` gives structural elements the data that the mesh cannot carry: shell
thickness and local axes (`COQUE`), the stiffness, mass or damping of discrete elements
(`DISCRET`), beam sections (`POUTRE`), bar areas, and so on. It works on a model
(`MODELE`) and returns an element properties object (`cara_elem`) that the analysis commands
take as `CARA_ELEM`. A model made only of 3D solid or 2D elements needs none; a model with
shells (`DKT`, `DST`, `COQUE_3D`), beams or discrete elements (`DIS_T`, `DIS_TR`) needs it,
and the command itself refuses to run when such elements are present but their keyword is
missing (`AFFECARAELEM_32`, then fatal `AFFECARAELEM_33`, `upstream/bibfor/modelisa/ace_verif_affe.F90:129`).
The decisions it encodes are the section data of each structural part and the local axes in
which shell stresses and forces are reported.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Affectation de caractéristiques à des éléments de structure» |
| Kind | `OPER` |
| Result | `cara_elem` (depends on the keywords given) |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.42.01 — from en/doc-ids.yaml (status: proposed) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `COQUE`, `EPAIS`, `VECTEUR`, `ANGL_REP`, `COQUE_NCOU`, `DISCRET`, `DIS_T`, `DIS_TR`, `CARA`, `K_T_D_N`, `K_TR_D_N`, `VALE`, `REPERE` |

`DIS_T` and `DIS_TR` are `AFFE_MODELE` modeling types, listed here because the `DISCRET`
values only apply to elements of those modelings ([AFFE_MODELE](AFFE_MODELE.md)).

## Keywords

Top-level simple keywords and the key factor keywords from docs/COMMAND-SET.md are expanded
below; the other factor keywords are listed under [Other keywords](#other-keywords).

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MODELE` | `modele_sdaster`, required | — | *model*. The model whose structural elements get the properties. Element groups are checked against it. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `1` prints the number of structural elements of each kind in the model ("LE MODELE ... CONTIENT : 400 ELEMENT(S) COQUE" in `tests/fixtures/shell_static/output/run.mess`; `upstream/bibfor/modelisa/ace_verif_affe.F90:81`). `2` also prints the values assigned, for example each `DISCRET` occurrence (`upstream/bibfor/modelisa/aceadi.F90:189`). |
| `VERIF` | text, optional | — | *check*. One of `'OUI'`, `'NON'`. Without it, or with `'OUI'`, the command checks that each keyword is used on a model that has that kind of element, that each kind of structural element present in the model (shell, beam, discrete, ...) has its keyword, and that `DISCRET` groups hold the right element type (`upstream/bibfor/op/op0019.F90:177`). `'NON'` skips these checks (`upstream/bibfor/modelisa/ace_verif_affe.F90:91`). Keep the default. |
| `COQUE` | factor keyword, optional, repeatable | — | *shell properties*. Thickness and local axes of `DKT`, `DST` and `COQUE_3D` elements. One occurrence per group with its own data. |
| `COQUE / GROUP_MA` | element group, required, list | — | *element group*. The shell groups. Cover every shell element of the model: an element without shell data stops the calculation with `CALCUL_21` (`upstream/bibfor/calcul/jevech.F90:192`). |
| `COQUE / EPAIS` | real, optional | — | *thickness*. Constant shell thickness, in the length unit of the mesh. Exactly one of `EPAIS`, `EPAIS_FO`. |
| `COQUE / EPAIS_FO` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional | — | Thickness as a function. Use it for a thickness that varies over the shell. TODO(verify) the function parameters accepted (coordinates `X`, `Y`, `Z`), against U4.42.01. |
| `COQUE / ANGL_REP` | real, optional, list of up to 2, at least 2 | — | *local-axis angles*. Two angles α, β in degrees that define a reference direction d = (cos β cos α, cos β sin α, −sin β) in the global axes. Its projection on each element's plane is the local x axis in which shell stresses and generalized forces are reported (`upstream/bibfor/elements/coqrep.F90:43`). Without `ANGL_REP` or `VECTEUR` the angles are 0, so d is the global X axis (`upstream/bibfor/modelisa/aceaco.F90:130`; message `PLATE1_40`). Give it whenever the stresses are read in local axes. |
| `COQUE / VECTEUR` | real, optional, list of up to 3, at least 3 | — | *reference vector (local x)*. The reference direction d given as a vector instead of angles; it is converted to `ANGL_REP` (`upstream/bibfor/modelisa/aceaco.F90:164`). Exclusive with `ANGL_REP`. Usually easier to write than the angles. |
| `COQUE / A_CIS` | real, optional | `0.8333333` | *transverse shear correction factor*. The 5/6 shear correction coefficient. Read by the `COQUE_3D` elements (`upstream/bibfor/elements/vdxrig.F90`, `upstream/bibfor/elements/vdesga.F90:74`); `DKT` / `DST` use a fixed 5/6 (`upstream/bibfor/elements/dxmate.F90:196`). Keep the default. |
| `COQUE / COEF_RIGI_DRZ` | real, optional | `1e-05` | *drilling stiffness coefficient*. Plate elements have no stiffness for the rotation about their normal (`DRZ`); a positive value adds one equal to this coefficient times the smallest bending rotation stiffness of the element, to keep the assembled matrix regular (`upstream/bibfor/elements/dxtloc.F90:125`). A negative value switches the `DKT` / `DST` elements to a drilling formulation scaled by its absolute value (`upstream/bibfor/elements/dkqrig.F90:134`; used in `upstream/astest/sdll135f.comm:66`). Keep the default. |
| `COQUE / COQUE_NCOU` | integer, optional | `1` | *number of shell layers*. Number of layers through the thickness at which stresses are integrated and stored; post-processing selects a layer with `NUME_COUCHE` and a level in it with `NIVE_COUCHE` (`'INF'`, `'MOY'`, `'SUP'`) (`upstream/astest/ssls119c.comm:57`). Linear elastic analyses can keep 1; use more for nonlinear materials (TODO(verify) the recommended count, against U4.42.01). |
| `COQUE / EXCENTREMENT` | real, optional | — | *shell offset*. Distance along the normal between the mesh surface and the shell mid-surface. Use it when the mesh is drawn on a face of the plate rather than its mid-plane. Giving it also sets `INER_ROTA='OUI'` (`upstream/bibfor/modelisa/aceaco.F90:180`). |
| `COQUE / EXCENTREMENT_FO` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional | — | Offset as a function. Exclusive with `EXCENTREMENT`. |
| `COQUE / INER_ROTA` | text, optional | — | One of `'OUI'`. Takes rotational inertia into account in the shell mass matrix. Required with an offset (catalog rule; set automatically, `upstream/bibfor/modelisa/aceaco.F90:180`). TODO(verify) its effect without an offset, against U4.42.01. |
| `COQUE / MODI_METRIQUE` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Metric correction through the thickness for the curvature of the shell. TODO(verify) which elements read it (the routine `upstream/bibfor/elements/carcou.F90:43` refers to it for pipe elements), against U4.42.01. Keep `'NON'`. |
| `DISCRET` | factor keyword, optional, repeatable | — | *discrete element properties*. Stiffness (`K_...`), mass (`M_...`) or damping (`A_...`) matrices of `DIS_T` / `DIS_TR` elements (catalog comment, `upstream/code_aster/Cata/Commands/affe_cara_elem.py:855`). One occurrence per group and matrix kind; give stiffness and mass in separate occurrences (`upstream/astest/sdll135f.comm:51`). |
| `DISCRET / REPERE` | text, optional | `'GLOBAL'` | *coordinate system*. One of `'LOCAL'`, `'GLOBAL'`. `'GLOBAL'`: the values are in the global axes. `'LOCAL'`: in the local axes of the element (`upstream/astest/ssnd102a.comm:557`). TODO(verify) how the local axes of a `POI1` are set (`ORIENTATION`), against U4.42.01. |
| `DISCRET / AMOR_HYST` | real, optional | — | Hysteretic damping coefficient of the discrete element. TODO(verify) its use in harmonic analyses, against U4.42.01. |
| `DISCRET / SYME` | text, optional | `'OUI'` | One of `'OUI'`, `'NON'`. `'OUI'` (default): symmetric matrix, given as its upper triangle column by column. `'NON'`: full matrix, column by column (catalog help of the `VALE` blocs). |
| `DISCRET / CARA` | text, optional | — | One of `'K_T_D_N'`, `'K_T_D_L'`, `'K_TR_D_N'`, `'K_TR_D_L'`, `'K_T_N'`, `'K_T_L'`, `'K_TR_N'`, `'K_TR_L'`, `'M_T_D_N'`, `'M_T_D_L'`, `'M_TR_D_N'`, `'M_TR_D_L'`, … (24 values; see the .json). Only when `equal_to("SYME", 'OUI')`. Which matrix is given, coded as kind (`K` stiffness, `M` mass, `A` damping), degrees of freedom (`T` translations, `TR` translations and rotations), `D` for diagonal, and support (`N` node, a `POI1` element; `L` line, a `SEG2` element). See [Discrete values](#discrete-values). |
| `DISCRET / GROUP_MA` | element group, required, list | — | *element group*. The `DIS_T` / `DIS_TR` element groups. With `CARA` ending in `_N` they must hold `POI1` elements, otherwise `SEG2`; a wrong type stops the run with `MODELISA_56` (`upstream/bibfor/modelisa/aceadi.F90:181`). |
| `DISCRET / VALE` | real, required, list of up to 3, at least 3 | — | *value(s)*. With `CARA` = `K_T_D_N`, `K_T_D_L` (or `A_...`): 3 diagonal terms, one per translation. |
| `DISCRET / VALE` | real, required, list of up to 6, at least 6 | — | *value(s)*. With `CARA` = `K_TR_D_N`, `K_TR_D_L` (or `A_...`): 6 diagonal terms, translations then rotations; or `K_T_N` / `A_T_N` / `M_T_N`: the upper triangle of a 3 × 3 matrix. |
| `DISCRET / VALE` | real, required, list of up to 21, at least 21 | — | *value(s)*. With `CARA` = `K_T_L`, `K_TR_N` (or `A_`, `M_`): upper triangle of a 6 × 6 matrix. |
| `DISCRET / VALE` | real, required, list of up to 78, at least 78 | — | *value(s)*. With `CARA` = `K_TR_L` (or `A_`, `M_`): upper triangle of a 12 × 12 matrix. |
| `DISCRET / VALE` | real, required | — | *value(s)*. With `CARA` = `M_T_D_N`, `M_T_D_L`: 1 mass value. |
| `DISCRET / VALE` | real, required, list of up to 10, at least 10 | — | *value(s)*. With `CARA` = `M_TR_D_N`: 1 mass, 6 terms of the inertia tensor, 3 components of the offset vector (catalog help, `upstream/code_aster/Cata/Commands/affe_cara_elem.py:920`). |
| `DISCRET / VALE` | real, required, list of up to 4, at least 4 | — | *value(s)*. With `CARA` = `M_TR_D_L`: 1 mass, 3 terms of the inertia tensor (catalog help). |
| `DISCRET / CARA` | text, optional | — | One of `'K_T_N'`, `'K_T_L'`, `'K_TR_N'`, `'K_TR_L'`, `'M_T_N'`, `'M_T_L'`, `'M_TR_N'`, `'M_TR_L'`, `'A_T_N'`, `'A_T_L'`, `'A_TR_N'`, `'A_TR_L'`. Only when `equal_to("SYME", 'NON')`. Full (non-symmetric) matrices; same coding as above. |
| `DISCRET / VALE` | real, required, list of up to 9, at least 9 | — | *value(s)*. `SYME='NON'`, `CARA` = `K_T_N` (or `A_`, `M_`): full 3 × 3 matrix, column by column. |
| `DISCRET / VALE` | real, required, list of up to 36, at least 36 | — | *value(s)*. `SYME='NON'`, `CARA` = `K_T_L`, `K_TR_N` (or `A_`, `M_`): full 6 × 6 matrix. |
| `DISCRET / VALE` | real, required, list of up to 144, at least 144 | — | *value(s)*. `SYME='NON'`, `CARA` = `K_TR_L` (or `A_`, `M_`): full 12 × 12 matrix. |
| `GEOM_FIBRE` | `gfibre_sdaster`, optional | — | Name of the data structure that groups all the fiber groups (from DEFI_GEOM_FIBRE). Required with `MULTIFIBRE` (multifiber beams); out of Tier 1 scope. |

### Discrete values

For a symmetric matrix (`SYME='OUI'`) the number of values is that of the upper triangle; for
`SYME='NON'`, that of the full matrix (catalog help strings of the `VALE` blocs,
`upstream/code_aster/Cata/Commands/affe_cara_elem.py:856`).

| `CARA` | Support | Matrix | `VALE` count (sym / full) |
|---|---|---|---|
| `K_T_D_N`, `A_T_D_N` | `POI1` | diagonal, 3 translations | 3 / — |
| `K_TR_D_N`, `A_TR_D_N` | `POI1` | diagonal, 3 translations + 3 rotations | 6 / — |
| `K_T_D_L`, `A_T_D_L` | `SEG2` | diagonal, 3 translations | 3 / — |
| `K_TR_D_L`, `A_TR_D_L` | `SEG2` | diagonal, 3 translations + 3 rotations | 6 / — |
| `K_T_N`, `A_T_N`, `M_T_N` | `POI1` | 3 × 3 | 6 / 9 |
| `K_TR_N`, `A_TR_N`, `M_TR_N` | `POI1` | 6 × 6 | 21 / 36 |
| `K_T_L`, `A_T_L`, `M_T_L` | `SEG2` | 6 × 6 | 21 / 36 |
| `K_TR_L`, `A_TR_L`, `M_TR_L` | `SEG2` | 12 × 12 | 78 / 144 |
| `M_T_D_N`, `M_T_D_L` | `POI1`, `SEG2` | mass | 1 / — |
| `M_TR_D_N` | `POI1` | mass, inertia tensor, offset | 10 / — |
| `M_TR_D_L` | `SEG2` | mass, inertia tensor | 4 / — |

The diagonal terms follow the element's degrees of freedom: `DX`, `DY`, `DZ`, then `DRX`,
`DRY`, `DRZ`. For instance `VALE=(0.0, pena, 0.0)` with `K_T_D_N` gives a spring along Y only
(`upstream/astest/ssnd112a.comm:177`). TODO(verify) this order against U4.42.01.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at least one of `BARRE`, `CABLE`, `COQUE`, `DISCRET`, `DISCRET_2D`, `GRILLE`, `MASSIF`, `MASS_REP`, `MEMBRANE`, `MULTIFIBRE`, `POUTRE`, `RIGI_PARASOL` must be given (`AU_MOINS_UN`).
- command: if `MULTIFIBRE` is given, `GEOM_FIBRE` must all be given (`PRESENT_PRESENT`).
- command: at most one of `DISCRET`, `DISCRET_2D` may be given (`EXCLUS`).
- `COQUE`: at most one of `ANGL_REP`, `VECTEUR` may be given (`EXCLUS`).
- `COQUE`: if `EXCENTREMENT` is given, `INER_ROTA` must all be given (`PRESENT_PRESENT`).
- `COQUE`: if `EXCENTREMENT_FO` is given, `INER_ROTA` must all be given (`PRESENT_PRESENT`).
- `COQUE`: exactly one of `EPAIS`, `EPAIS_FO` must be given (`UN_PARMI`).
- `COQUE`: at most one of `EXCENTREMENT`, `EXCENTREMENT_FO` may be given (`EXCLUS`).

Checked by the solver unless `VERIF='NON'` (`upstream/bibfor/modelisa/ace_verif_affe.F90`):

- a keyword given for a kind of element the model does not contain is an error
  (`AFFECARAELEM_31`), for example `COQUE` on a model without shells;
- structural elements of the model whose keyword is not given at all are reported
  (`AFFECARAELEM_32`);
- either case then stops the command (`AFFECARAELEM_33`).

## Other keywords

Factor keywords outside this draft's scope (sub-keywords are in `en/commands/AFFE_CARA_ELEM.json`):

- `BARRE`
- `CABLE`
- `DISCRET_2D`
- `GRILLE`
- `MASSIF`
- `MASS_AJOU`
- `MASS_REP`: Mass distributed over POI1 elements, weighted by the area of the connected elements.
- `MEMBRANE`
- `MULTIFIBRE`
- `ORIENTATION`
- `POUTRE`
- `POUTRE_FLUI`
- `RIGI_GRILLE`
- `RIGI_MISS_3D`
- `RIGI_PARASOL`

## Patterns

### Plate thickness and local axes

`ANGL_REP=(0.0, 0.0)` makes the default explicit: the local x axis is the projection of the
global X axis, so the shell forces of this plate in the XY plane are in X and Y.

Source: `tests/fixtures/shell_static/input/run.comm:37`.

```python
CARA = AFFE_CARA_ELEM(MODELE=MODE, COQUE=_F(GROUP_MA="PLATE", EPAIS=T, ANGL_REP=(0.0, 0.0)))
```

The log shows the defaults filled in (`tests/fixtures/shell_static/output/run.mess`):

```python
CARA = AFFE_CARA_ELEM(COQUE=_F(ANGL_REP=(0.0, 0.0),
                               A_CIS=0.8333333,
                               COEF_RIGI_DRZ=1e-05,
                               COQUE_NCOU=1,
                               EPAIS=10.0,
                               GROUP_MA='PLATE',
                               MODI_METRIQUE='NON'),
                      INFO=1,
                      MODELE=MODE)
```

### Several layers through the thickness

Three layers, for stresses at the bottom, middle and top skins of each layer.

Source: `upstream/astest/tpls102a.comm:77`.

```python
CARAELEM = AFFE_CARA_ELEM(MODELE=MODELE, COQUE=_F(GROUP_MA="POUTRE", COQUE_NCOU=3, EPAIS=0.1))
```

### Quadratic shell

Source: `upstream/astest/ssls119c.comm:34`.

```python
CAR_ELE = AFFE_CARA_ELEM(MODELE=MO, COQUE=_F(GROUP_MA="TOUT_ELT", EPAIS=0.0508))
```

### Grounded spring on a node

`PX1` is a `POI1` group modeled with `DIS_T` (`upstream/astest/ssnd112a.comm:63`); the
stiffness acts along Y only. The same call also gives `MASSIF` data for the solid.

Source: `upstream/astest/ssnd112a.comm:174`.

```python
ORIEN = AFFE_CARA_ELEM(
    MODELE=TROISD,
    MASSIF=_F(GROUP_MA="VOL", ANGL_EULER=(phi1, phi, phi2)),
    DISCRET=_F(GROUP_MA=("PX1",), CARA="K_T_D_N", VALE=(0.0, pena, 0.0)),
)
```

### Shell plus a discrete element on a created point

`CREA_MAILLAGE/CREA_POI1` first puts a `POI1` element on node group `Point_A`
(`upstream/astest/sdll135f.comm:33`), modeled with `DIS_TR` (line 41). Stiffness and mass are
separate occurrences; here both are zero.

Source: `upstream/astest/sdll135f.comm:51`.

```python
CARAC = AFFE_CARA_ELEM(
    MODELE=MODELE,
    COQUE=_F(GROUP_MA=("Tuyau", "Encas", "Libre"), EPAIS=epaisseur),
    DISCRET=(
        _F(GROUP_MA="POI_A", CARA="K_TR_D_N", VALE=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
        _F(
            GROUP_MA="POI_A",
            CARA="M_TR_D_N",
            VALE=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ),
    ),
)
```

## Pitfalls

- **Forgetting `CARA_ELEM` in the analysis.** The properties are used only if the analysis
  command gets `CARA_ELEM=`; without it, a shell element stops the calculation with
  `CALCUL_21`, whose first advice is exactly that (`upstream/bibfor/calcul/jevech.F90:192`).
  Our `shell_static` fixture passes it to `MECA_STATIQUE`
  (`tests/fixtures/shell_static/input/run.comm:58`).
- **Shell groups not all covered.** Every `DKT` / `DST` / `COQUE_3D` element needs `COQUE`
  data. A model with shells and no `COQUE` keyword at all fails in `AFFE_CARA_ELEM` itself
  (`AFFECARAELEM_32`, `AFFECARAELEM_33`); a shell group missing from `COQUE/GROUP_MA` fails later,
  in the analysis (`CALCUL_21`).
- **Default local axis normal to the shell.** With no `ANGL_REP` / `VECTEUR`, the local x axis
  is the projection of global X. On a shell perpendicular to X (a wall in the YZ plane) that
  projection is zero, and the calculation stops with `PLATE1_40`, which asks for `ANGL_REP` or
  `VECTEUR` (`upstream/bibfor/elements/coqrep.F90:56`). Give `VECTEUR` for every shell group
  that is not roughly horizontal, and use the same direction wherever stresses are compared.
- **Local axes vary with element orientation.** Shell stresses and forces (`SIGM_ELNO`,
  `EFGE_ELNO`) are reported in each element's local axes. On a curved shell those axes rotate
  from element to element, so components such as `NXX` are not directly comparable across the
  model. TODO(verify) the recommended post-processing (`MODI_REPERE`) against U4.42.01.
- **Discrete matrix on the wrong element type.** `_N` matrices need `POI1` groups and `_L`
  matrices `SEG2` groups (`MODELISA_56` otherwise). A node group cannot be given directly:
  create `POI1` elements on it with `CREA_MAILLAGE/CREA_POI1`
  ([CREA_MAILLAGE](CREA_MAILLAGE.md)) and model them with `DIS_T` or `DIS_TR`.
- **Thickness in the wrong unit.** `EPAIS` uses the mesh length unit, like `E` and `RHO` in
  `DEFI_MATERIAU`; our `shell_static` fixture uses mm throughout
  (`tests/fixtures/shell_static/input/run.comm:2`).

## See also

- French reference: U4.42.01 (translation: `en/docs/U4.42.01.md` once task 5.x lands)
- Catalog: `en/commands/AFFE_CARA_ELEM.json` (generated from `upstream/code_aster/Cata/Commands/affe_cara_elem.py:481`)
- Implementation: `upstream/code_aster/CodeCommands/affe_cara_elem.py`; `upstream/bibfor/op/op0019.F90`;
  `COQUE` in `upstream/bibfor/modelisa/aceaco.F90`; `DISCRET` in `upstream/bibfor/modelisa/aceadi.F90`;
  checks in `upstream/bibfor/modelisa/ace_verif_affe.F90`; shell local axes in
  `upstream/bibfor/elements/coqrep.F90`
- Before: `AFFE_MODELE` (shell and discrete modelings), `CREA_MAILLAGE` (`CREA_POI1`)
- Next steps: `MECA_STATIQUE` and the other analyses (`CARA_ELEM=`); `CALC_CHAMP` (`EFGE_ELNO`)
- Example: `upstream/astest/zzzz505d.py` (line 137, beams)
- Example: `upstream/astest/sslx102f.comm` (line 64, pipes)
- Example: `upstream/astest/sdll135f.comm` (line 51)
- Example: `tests/fixtures/shell_static/input/run.comm` (line 37)
