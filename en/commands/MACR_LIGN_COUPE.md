---
command: MACR_LIGN_COUPE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/macr_lign_coupe.py:25
doc_fr: U4.81.13
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3e)
examples: [sslv100c, sslv07a, sslv134b, sslv04h]
---

# MACR_LIGN_COUPE — extract along cut line

> **Assisted reference.** Written in session from the pinned catalog, the macro's Python
> implementation, the commands it calls, the message catalog and upstream test cases. Every
> behavior claim cites its source. Not reviewed by an engineer.

`MACR_LIGN_COUPE` reads a result along lines through the model and returns the values in a
table: a straight segment between two points, an arc, or a line of existing nodes or edge
elements. It meshes the lines with two-node segments
(`upstream/code_aster/MacroCommands/macr_lign_coupe_ops.py:348`), projects the field onto them
with `PROJ_CHAMP` (`:823`) and extracts with `POST_RELEVE_T` (`:953`), so the points need not be
nodes of the model. The default field is `SIGM_NOEU` (catalog
`upstream/code_aster/Cata/Commands/macr_lign_coupe.py:78`): compute it first with `CALC_CHAMP`.
Use it for stress profiles through a wall (the input of `POST_RCCM`), displacements along an
edge or temperature profiles. The decisions it encodes are where the lines run, how many points
they have, which field and components are read, and in which axes.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Extraction des valeurs d'un résultat dans une ou plusieurs tables sur des lignes de coupe définies par deux points et un intervalle» |
| Kind | `MACRO` |
| Result | `table_sdaster` |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.81.13 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `LIGN_COUPE`, `TYPE`, `SEGMENT`, `COOR_ORIG`, `COOR_EXTR`, `NB_POINTS` |

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `RESULTAT` | `evol_elas` or `evol_noli` or `evol_ther` or `evol_sech` or `mode_meca` or `comb_fourier` or `mult_elas` or `fourier_elas` or `dyna_trans`, optional | — | *result*. The result to read, usually the `MECA_STATIQUE` result after `CALC_CHAMP`. Exactly one of `RESULTAT`, `CHAM_GD` (rule). The model is taken from the result; a result without one needs `MODELE` (`POST0_9`, `macr_lign_coupe_ops.py:591`), except a `mode_meca` without a model, whose nodal fields are projected on the mesh (`POST0_23`). |
| `CHAM_GD` | `cham_gd_sdaster`, optional | — | *field (physical quantity)*. A single field instead of a result, for example one made by `CREA_CHAMP`. Needs `MODELE` (`POST0_10`, `:612`). The macro wraps it in a one-step result (`CREA_RESU`, `INST=0.0`, `:648`) and picks the field name from its physical quantity when `NOM_CHAM` is absent (`DEPL` for a displacement, `TEMP` for a temperature, `:619`–`:641`). |
| `NOM_CHAM` | text, optional | `'SIGM_NOEU'` (mechanical), `'TEMP'` (thermal), `'SECH'` (drying), none for `CHAM_GD` | *field name*. The field to read: one name. The default depends on the result type (catalog `upstream/code_aster/Cata/Commands/macr_lign_coupe.py:73`–`:124`). Nodal (`_NOEU`) and element-node (`_ELNO`) fields work; a Gauss-point field (`_ELGA`) gives `POST0_18` and probably a fatal error (`:797`). Common choices: `'SIGM_NOEU'` or `'SIGM_ELNO'` (stress, the input for `POST_RCCM`), `'DEPL'`, `'SIEQ_NOEU'` (von Mises and other equivalent stresses), `'TEMP'`. The field must exist in the result: compute it first with `CALC_CHAMP`. |
| `NUME_ORDRE` | integer, optional, list | — | *step index*. Only when `exists("RESULTAT")`. These steps only. Without any step keyword, all steps are read (`TOUT_ORDRE`, `:583`). |
| `NUME_MODE` | integer, optional, list | — | *mode number*. Only when `exists("RESULTAT")`. These modes of a `mode_meca` result. |
| `LIST_ORDRE` | `listis_sdaster`, optional | — | Only when `exists("RESULTAT")`. The steps as an integer list made by `DEFI_LIST_ENTI`. |
| `INST` | real, optional, list | — | *time step (pseudo-time)*. Only when `exists("RESULTAT")`. The steps at these times. |
| `LIST_INST` | `listr8_sdaster`, optional | — | *time-step list*. Only when `exists("RESULTAT")`. The times as a `DEFI_LIST_REEL` list. |
| `CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `INST` or `LIST_INST` is given. Whether `PRECISION` is relative or absolute when a time is matched to a stored step. |
| `PRECISION` | real, optional (relative) or required (absolute) | `1e-06` (relative) | *tolerance*. The tolerance of that match; required with `CRITERE='ABSOLU'`. |
| `MODELE` | `modele_sdaster`, optional | — | *model*. Required with `CHAM_GD`, or when the result carries no model (for example one built by `CREA_RESU` or `LIRE_RESU`); otherwise the result's model is used (`:604`). |
| `REPERE_INIT` | text, optional | — | One of `'GLOBAL'`, `'LOCAL'`. The axes the input field is written in. Only read when a cut line asks for other axes (`LIGN_COUPE/REPERE` other than `'INITIAL'`) and the field is an element field (`_ELNO`, `_ELGA`, `_ELEM`): the macro cannot tell in which axes such a field is written, so it stops with `POST0_55` unless told `'GLOBAL'` (`:655`–`:666`). `'LOCAL'` is refused (`POST0_56`). Give `'GLOBAL'` for solid-element stresses, which are in global axes. |
| `UNITE_MAILLAGE` | `UnitDefault`, optional | a free unit (`:545`) | The logical unit the line mesh is written to (in Aster format) before it is read back. Leave it out; give a unit only to keep the line mesh as a file. |
| `VIS_A_VIS` | factor keyword, optional, repeatable | — | Restricts where values are taken from: the projection uses only the listed elements of the model (passed to `PROJ_CHAMP` with `TOUT_2='OUI'`, `:789`–`:795`). Use it when a line crosses or runs along an interface between two parts or materials, to read the stress of one side instead of whichever element `PROJ_CHAMP` finds first. |
| `VIS_A_VIS / GROUP_MA_1` | element group, optional | — | The elements values are taken from. |
| `LIGN_COUPE` | factor keyword, required, repeatable | — | *cut line*. One occurrence per line. All lines of one call go into one table, told apart by `INTITULE`. |
| `LIGN_COUPE / INTITULE` | text, optional | `l.coupe1`, `l.coupe2`, … for segments and arcs, the group name for group lines (`:885`–`:889`) | *label*. The line's name in the `INTITULE` column. Give a short one: `POST_RCCM` and `TEST_TABLE` filter on it (`upstream/astest/sslv100c.comm:91`). |
| `LIGN_COUPE / TYPE` | text, optional | `'SEGMENT'` | *type*. One of `'SEGMENT'`, `'ARC'`, `'GROUP_NO'`, `'GROUP_MA'`. `'SEGMENT'`: a straight line from `COOR_ORIG` (or `GROUP_NO_ORIG`) to `COOR_EXTR` (or `GROUP_NO_EXTR`) with `NB_POINTS` evenly spaced points, ends included (`:369`). `'ARC'`: points on a circular arc. `'GROUP_NO'`: the nodes of a group, in the group's order (`:701`). `'GROUP_MA'`: the nodes of a group of edge elements (`SEG*` only, `POST0_15`), sorted along the line (`DEFI_GROUP` `NOEUD_ORDO`, `:735`). Arcs cannot be mixed with other types in one call (`POST0_16`). |
| `LIGN_COUPE / NB_POINTS` | integer, required | — | *number of points*. Range: ≥ 2. Only for `'SEGMENT'` and `'ARC'`. For a segment, the number of points including both ends (spacing = length / (`NB_POINTS` − 1)). For a full 360° arc, the points are 360°/`NB_POINTS` apart and the start is not repeated (`:397`). For a through-thickness stress profile, use enough points to follow the stress gradient: `upstream/astest/sslv100c.comm:62` uses 100 across a wall. |
| `LIGN_COUPE / COOR_ORIG` | real, list of 2 or 3 | — | *start point coordinates*. For `'SEGMENT'` (one of `COOR_ORIG`, `GROUP_NO_ORIG`) and `'ARC'` (required). As many coordinates as the mesh has dimensions, otherwise `POST0_11` (`:688`). On an arc, the first point of the arc. |
| `LIGN_COUPE / COOR_EXTR` | real, list of 2 or 3 | — | *end point coordinates*. For `'SEGMENT'` (one of `COOR_EXTR`, `GROUP_NO_EXTR`). |
| `LIGN_COUPE / GROUP_NO_ORIG` | node group, optional | — | For `'SEGMENT'`: the start point is the node of this one-node group (`POST0_27` otherwise, `:513`). For `'GROUP_MA'`: the node the ordering starts from; for a closed line it is required, with `GROUP_NO_EXTR` the same node (catalog comment, `upstream/code_aster/Cata/Commands/macr_lign_coupe.py:196`). |
| `LIGN_COUPE / GROUP_NO_EXTR` | node group, optional | — | The end point, as `GROUP_NO_ORIG`. |
| `LIGN_COUPE / CENTRE` | real, required, list of 2 or 3 | — | For `'ARC'`: the center of the arc. (The glossary label for the value `CENTRE` is about frequencies and does not apply here.) |
| `LIGN_COUPE / ANGLE` | real, required | — | For `'ARC'`: the angle swept from `COOR_ORIG`, in degrees (`360.0` for a full circle, `upstream/astest/sslv134b.comm:75`). The table gets an `ANGLE` column (`:969`). |
| `LIGN_COUPE / DNOR` | real, list of 2 or 3 | — | For `'ARC'` in 3D, required (`POST0_12`): the normal to the plane of the arc, which is also the axis of the cylindrical axes used with `REPERE='CYLINDRIQUE'` (`:244`). |
| `LIGN_COUPE / GROUP_NO` | node group, required | — | *node group*. For `'GROUP_NO'`: the nodes of the line; must exist in the mesh (`POST0_13`). |
| `LIGN_COUPE / GROUP_MA` | element group, required | — | *element group*. For `'GROUP_MA'`: the edge elements of the line (`POST0_14` if missing). |
| `LIGN_COUPE / MAILLAGE` | `maillage_sdaster`, required | — | *mesh*. For `'GROUP_MA'`: the mesh that holds `GROUP_MA` (copied to order its nodes, `:719`). |
| `LIGN_COUPE / VECT_ORIE` | real, list of up to 3 | — | For `'GROUP_MA'` on a closed line: a vector that sets the direction of travel (catalog comment, `upstream/code_aster/Cata/Commands/macr_lign_coupe.py:199`). |
| `LIGN_COUPE / OPERATION` | text, optional | `'EXTRACTION'` | *operation*. One of `'EXTRACTION'`, `'MOYENNE'`. `'EXTRACTION'`: one row per point. `'MOYENNE'`: integrals along the line instead, rows `MOMENT_0`, `MOMENT_1`, `MINIMUM`, `MAXIMUM`, `MOYE_INT`, `MOYE_EXT` (`QUANTITE` column; `POST_RELEVE_T` `MOYENNE`, `upstream/astest/sslv134b.comm:122`, `:138`). For stress linearization to code rules, prefer `POST_RCCM`. |
| `LIGN_COUPE / NOM_CMP` | text, optional, list | — | *component name*. These components only, for example `('SIXX', 'SIYY')`; default all components. At most one of `NOM_CMP`, `INVARIANT`, `ELEM_PRINCIPAUX`, `RESULTANTE` (rule). |
| `LIGN_COUPE / INVARIANT` | text, optional | — | One of `'OUI'`. The invariants of a tensor field instead of its components (`POST_RELEVE_T` `INVARIANT`). |
| `LIGN_COUPE / ELEM_PRINCIPAUX` | text, optional | — | One of `'OUI'`. The principal values and directions of a tensor field (`POST_RELEVE_T` `ELEM_PRINCIPAUX`). |
| `LIGN_COUPE / TRAC_NOR` | text, optional | — | One of `'OUI'`. With `NOM_CMP`: the traction (or flux) across the line, for plane models (`POST_RELEVE_T` `TRAC_NOR`). |
| `LIGN_COUPE / TRAC_DIR` | text, optional | — | One of `'OUI'`. With `NOM_CMP` and `DIRECTION`: the traction on a facet whose normal is `DIRECTION` (`POST_RELEVE_T` `TRAC_DIR`). |
| `LIGN_COUPE / DIRECTION` | real, optional, list | — | *direction*. The facet normal of `TRAC_DIR`. |
| `LIGN_COUPE / RESULTANTE` | text, optional, list | — | *resultant components*. One of `'DX'`, `'DY'`, `'DZ'`, `'NXX'`, `'NYY'`, `'NXY'`. Only for `'GROUP_NO'` and `'GROUP_MA'`. The sum of these components over the line's nodes (`POST_RELEVE_T` `RESULTANTE`): meaningful for nodal forces (`REAC_NODA`, `FORC_NODA`) and shell resultants. |
| `LIGN_COUPE / MOMENT` | text, optional, list | — | *moment components*. One of `'DRX'`, `'DRY'`, `'DRZ'`, `'MXX'`, `'MYY'`, `'MXY'`. Only for group lines, with `RESULTANTE` and `POINT`: the moment of the summed forces about `POINT`. |
| `LIGN_COUPE / POINT` | real, optional, list | — | *reference point*. The point `MOMENT` is taken about. |
| `LIGN_COUPE / REPERE` | text, optional | `'INITIAL'` | *coordinate system*. One of `'INITIAL'`, `'LOCAL'`, `'POLAIRE'`, `'UTILISATEUR'`, `'CYLINDRIQUE'`. The axes the components are written in. `'INITIAL'`: as in the result (global for solids). `'LOCAL'` (segments only): x along the line, y from `VECT_Y` (`:178`–`:216`); this is how a stress normal to a cut (`SIXX`) or across it is read. `'UTILISATEUR'`: global axes rotated by `ANGL_NAUT`. `'CYLINDRIQUE'`: about an axis (`ORIGINE`, `AXE_Z`; for an arc, its `CENTRE` and `DNOR`). `'POLAIRE'`: polar axes in 2D (`POST_RELEVE_T`, `:902`). Only `DEPL`, `SIGM_NOEU`, `SIGM_ELNO`, `SIEF_ELNO`, `FLUX_ELNO` and `FLUX_NOEU` are rotated; another field gives `POST0_17` and stays in the initial axes (`:893`–`:926`). An arc accepts only `'INITIAL'`, `'POLAIRE'` or `'CYLINDRIQUE'` (`POST0_5`); group lines refuse `'LOCAL'` (`POST0_57`). |
| `LIGN_COUPE / VECT_Y` | real, list of 3 | — | With `REPERE='LOCAL'`: a vector in the local x-y plane that fixes local y. Required in 3D (`POST0_50`), not used in 2D (`POST0_58`); must not be parallel to the line (`POST0_3`). |
| `LIGN_COUPE / ANGL_NAUT` | real, required, list of 3 | — | With `REPERE='UTILISATEUR'`: three nautical angles in degrees; only the first is used in 2D (`:223`–`:230`). |
| `LIGN_COUPE / ORIGINE` | real, list of 2 or 3 | — | With `REPERE='CYLINDRIQUE'` on a segment or group line: a point of the axis. |
| `LIGN_COUPE / AXE_Z` | real, list of 3 | — | With `REPERE='CYLINDRIQUE'` in 3D: the direction of the axis. |
| `LIGN_COUPE / DISTANCE_MAX` | real, optional | `0.0` | *maximum distance*. A point of the line farther than this from the model is ignored (catalog help). The macro always passes the value to `PROJ_CHAMP` (`macr_lign_coupe_ops.py:826`), and an explicit distance makes a point found in no element get no value instead of a fatal error (`upstream/bibfor/projection/pjefco.F90:121`, `upstream/bibfor/projection/pj4dco.F90:312`). So with the default `0.0`, points outside the elements are dropped (see Pitfalls); a small positive value lets a point just outside a curved or faceted surface take the value of the nearest element (`upstream/astest/sslv134b.comm:77`: 0.001 on an arc of radius 0.24 through a curved, faceted mesh). Only the smallest value over all occurrences is used, for every line (`POST0_53`, `:808`–`:818`). TODO(verify) the tolerance below which a point counts as inside an element. |
| `LIGN_COUPE / DISTANCE_ALARME` | real, optional | — | A point farther than this from the model gives a warning (catalog help). As `DISTANCE_MAX`, the smallest value applies to all lines (`POST0_54`). |

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: exactly one of `RESULTAT`, `CHAM_GD` must be given (`UN_PARMI`).
- when `exists("RESULTAT")`: at most one of `NUME_ORDRE`, `NUME_MODE`, `LIST_ORDRE`, `INST`, `LIST_INST` may be given (`EXCLUS`).
- `VIS_A_VIS`: at most one of `GROUP_MA_1`, `MAILLE_1` may be given (`EXCLUS`).
- `LIGN_COUPE`: at most one of `NOM_CMP`, `INVARIANT`, `ELEM_PRINCIPAUX`, `RESULTANTE` may be given (`EXCLUS`).
- `LIGN_COUPE`: if `TRAC_DIR` is given, `DIRECTION` must all be given (`PRESENT_PRESENT`).
- `LIGN_COUPE`: at most one of `TRAC_DIR`, `TRAC_NOR` may be given (`EXCLUS`).
- `LIGN_COUPE`: if `TRAC_DIR` is given, `NOM_CMP` must all be given (`PRESENT_PRESENT`).
- `LIGN_COUPE`: if `TRAC_NOR` is given, `NOM_CMP` must all be given (`PRESENT_PRESENT`).
- `LIGN_COUPE`: `MOMENT`, `POINT` are given all together or not at all (`ENSEMBLE`).
- when `equal_to("TYPE", 'GROUP_NO') or equal_to("TYPE", 'GROUP_MA')`: if `MOMENT` is given, `RESULTANTE` must all be given (`PRESENT_PRESENT`).
- when `equal_to("TYPE", 'SEGMENT')`: exactly one of `COOR_ORIG`, `GROUP_NO_ORIG` must be given (`UN_PARMI`).
- when `equal_to("TYPE", 'SEGMENT')`: exactly one of `COOR_EXTR`, `GROUP_NO_EXTR` must be given (`UN_PARMI`).

## Output table

For `'EXTRACTION'`, one row per point and step: `INTITULE`, `NOM_CHAM`, `NUME_ORDRE`, `INST`,
`ABSC_CURV` (distance from the line's start), `COOR_X`, `COOR_Y`, `COOR_Z`, then the components;
`ANGLE` for arcs. The line mesh's `NOEUD` and `RESU` columns are removed (`:971`–`:974`).
Dropped points (see Pitfalls) make fewer rows than `NB_POINTS`.

## Patterns

### Through-thickness stress profile for linearization

A segment across the wall of an axisymmetric cylinder, 15 points, on element-node stresses;
the table goes to `POST_RCCM` (`upstream/astest/sslv04h.comm:330`). Start on one surface, end on
the other, normal to the wall.

Source: `upstream/astest/sslv04h.comm:316`.

```python
T_RESU = MACR_LIGN_COUPE(
    RESULTAT=RESU,
    NOM_CHAM="SIGM_ELNO",
    LIGN_COUPE=(
        _F(
            TYPE="SEGMENT",
            NB_POINTS=15,
            INTITULE="LIGNE",
            COOR_ORIG=(0.1, 0.0),
            COOR_EXTR=(0.2, 0.0),
        )
    ),
)
```

### Stresses in the axes of the line (3D)

`REPERE='LOCAL'` writes the stresses with x along the segment and y set by `VECT_Y`;
`REPERE_INIT='GLOBAL'` states that the input is in global axes. Use it to read the stress normal
to a section, or the shear across it, without rotating by hand.

Source: `upstream/astest/sslv07a.comm:170`.

```python
ligne34 = MACR_LIGN_COUPE(
    RESULTAT=RESU,
    NOM_CHAM="SIGM_NOEU",
    REPERE_INIT="GLOBAL",
    LIGN_COUPE=_F(
        NB_POINTS=5,
        VECT_Y=(0.0, 1.0, 2.0),
        TYPE="SEGMENT",
        REPERE="LOCAL",
        COOR_ORIG=(-0.5, 0.5, 1.0),
        COOR_EXTR=(0.5, 0.5, 1.0),
    ),
)
```

### Full circle in cylindrical axes

Sixteen points on a 360° arc of radius 0.24 in a 3D solid (a cracked body, test case for
stress intensity factors), stresses written in cylindrical axes about the arc's normal (`DNOR`);
`DISTANCE_MAX` lets points that fall just outside the faceted mesh take the value of the nearest
element instead of being dropped. The table has an `ANGLE` column, used here to pick the 45°
point.

Source: `upstream/astest/sslv134b.comm:94`.

```python
TB2L = MACR_LIGN_COUPE(
    RESULTAT=CHAMDEPL,
    NOM_CHAM="SIGM_NOEU",
    LIGN_COUPE=_F(
        TYPE="ARC",
        NB_POINTS=16,
        CENTRE=(0.0, 2.0, 0.0),  # N1710
        COOR_ORIG=(9.18855088244361e-17, 1.76000036554081e00, -4.18878807815594e-04),  # N4968
        ANGLE=360.0,
        REPERE="CYLINDRIQUE",
        DNOR=(1.0, 0.0, 0.0),
        DISTANCE_MAX=0.001,
    ),
)
```

### Displacement from a single field

A displacement field (not a result) along a line; `MODELE` is then required.

Source: `upstream/astest/sslv07a.comm:355`.

```python
EXTRFO = MACR_LIGN_COUPE(
    CHAM_GD=DEPLFO,
    MODELE=MO,
    LIGN_COUPE=(
        _F(
            INTITULE="section1",
            TYPE="SEGMENT",
            NB_POINTS=3,
            DISTANCE_MAX=0.001,
            COOR_ORIG=(0.0, 0.0, 3.0),
            COOR_EXTR=(0.0, 0.0, 0.0),
        ),
    ),
)
```

## Pitfalls

- **The field must have been computed.** The default `'SIGM_NOEU'` is not produced by
  `MECA_STATIQUE`; add `CALC_CHAMP(CONTRAINTE='SIGM_NOEU')` (or `'SIGM_ELNO'`) first. Gauss-point
  fields (`_ELGA`) are refused in practice (`POST0_18`).
- **Points outside the elements are dropped, with a warning** (`POST0_8`, `POST0_24`,
  `macr_lign_coupe_ops.py:105`–`:141`). Ends on a curved surface (the radii of a vessel) can be
  lost to the faceting: in our run the outer point of a 20 mm wall was. Check the `ABSC_CURV`
  range, and set a small `DISTANCE_MAX` or move the ends slightly inside.
- **One axes choice per call.** Whether components are rotated is decided by the `REPERE` of the
  *last* `LIGN_COUPE` occurrence, for every line (`cut_axis_system`, set at `:680`, read at
  `:893`). Our run: a `'LOCAL'` line followed by an `'INITIAL'` one came out unrotated; the
  reverse order stopped with `ValueError: SEGMENT using INITIAL not handled`. Use one call per
  `REPERE`. Candidate upstream bug (`docs/OWNER-REVIEW-QUEUE.md`).
- **`REPERE='LOCAL'` reads the coordinates.** The local x axis comes from `COOR_ORIG` and
  `COOR_EXTR` (`:185`); give coordinates, not `GROUP_NO_ORIG`/`GROUP_NO_EXTR`. TODO(verify) the
  error otherwise.
- **Element stresses in other axes need `REPERE_INIT='GLOBAL'`** (`POST0_55`, `:655`–`:662`).
  That is true for solids; shell stresses are in local axes, where it would be false.
- **Element-node values at material interfaces.** An `_ELNO` field has one value per element at
  a shared node; `VIS_A_VIS` chooses the side.
- **Dimensions must match.** 2 coordinates on a 3D mesh stop the run (`POST0_11`).

## See also

- [`POST_RELEVE_T`](POST_RELEVE_T.md), which does the extraction (components, invariants,
  resultants, `MOYENNE`); [`POST_RCCM`](POST_RCCM.md), which linearizes the stresses this command
  extracts; [`CALC_CHAMP`](CALC_CHAMP.md), which computes the fields.
- French reference: U4.81.13 (French text: `en/docs/_src/U4.81.13.fr.md`; translation: `en/docs/U4.81.13.md` once task 5.2 lands)
- Catalog: `en/commands/MACR_LIGN_COUPE.json` (generated from `upstream/code_aster/Cata/Commands/macr_lign_coupe.py:25`)
- Implementation: `upstream/code_aster/MacroCommands/macr_lign_coupe_ops.py`
- Example: `upstream/astest/sslv100c.comm` (lines 62)
- Example: `upstream/astest/sslv07a.comm` (lines 170, 355)
- Example: `upstream/astest/sslv134b.comm` (lines 67, 94, 122)
- Example: `upstream/astest/sslv04h.comm` (lines 316)
