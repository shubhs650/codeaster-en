---
command: POST_RELEVE_T
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/post_releve_t.py:26
doc_fr: U4.81.21
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3d)
examples: [ssll14a, forma02a, forma21a, ssnv197a, ssls502a, ssll11a, tpll01a]
---

# POST_RELEVE_T — extract field values to a table

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

`POST_RELEVE_T` reads the values of a field on a set of nodes and writes them, or a quantity
computed from them, to a table (`table_sdaster`). Each `ACTION` occurrence is one extraction
and adds its rows to the same table, identified by its `INTITULE`. The field comes from a
result (`RESULTAT` + `NOM_CHAM`) or is given directly (`CHAM_GD`). Four operations exist:
`EXTRACTION` (values at nodes, or their resultant and moment), `MOYENNE` (mean and first moment
along a line of nodes), `MOYENNE_ARITH` (arithmetic mean over a set) and `EXTREMA` (minimum and
maximum). It is the Tier 1 way to get numbers out of a run: reaction sums on a support,
displacements at a point, stresses along a line. The table then goes to `IMPR_TABLE` (file),
`TEST_TABLE` (check) or Python (`.EXTR_TABLE()`). The command reads only nodal or element-node
fields: Gauss-point fields are refused (`POSTRELE_47`).

| Fact | Value |
|---|---|
| Catalog description (fr) | «Extraire des valeurs de composantes de champs de grandeurs pour y effectuer des calculs (moyenne,invariants,..) ou pour les exprimer dans d'autres repères» |
| Kind | `OPER` (Fortran operator 51, `upstream/bibfor/op/op0051.F90`) |
| Result | `table_sdaster` |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.81.21 — from the catalog `docu=` |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `ACTION`, `OPERATION`, `RESULTANTE`, `MOMENT`, `INTITULE`, `GROUP_NO`, `NOM_CMP` |

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `ACTION` | factor keyword, required, repeatable | — | *extraction action*. One extraction. Repeat it to put several extractions (several groups, fields or operations) in one table; each keeps its `INTITULE` in the first column. |
| `ACTION / OPERATION` | text, required, list of up to 2 | — | *operation*. One of `'EXTRACTION'`, `'MOYENNE'`, `'MOYENNE_ARITH'`, `'EXTREMA'`. `EXTRACTION`: values at each node, or with `RESULTANTE` their sum. `MOYENNE`: along an ordered line of nodes, gives `MOMENT_0`, `MOMENT_1`, `MINIMUM`, `MAXIMUM`, `MOYE_INT`, `MOYE_EXT` (`upstream/bibfor/postrele/rvtamo.F90:68`), at most 6 components (`POSTRELE_7`); used for through-thickness averages (`upstream/astest/forma21a.comm:200`). `MOYENNE_ARITH`: arithmetic mean over the selected nodes or elements (`upstream/bibfor/postrele/rvmoye.F90`). `EXTREMA`: minimum and maximum of each component and where they occur (`upstream/bibfor/algorith/rvmima.F90`). |
| `ACTION / INTITULE` | text, required | — | *label*. Name of the extraction, written in the `INTITULE` column of every row it produces (`tests/fixtures/solid_static/output/tables/reactions.csv`). Use a short, unique name per action to filter the table later. |
| `ACTION / CHAM_GD` | `cham_no_sdaster` or `cham_elem`, optional | — | *field (physical quantity)*. A field object (for example from `CREA_CHAMP`) instead of a result (`upstream/astest/ssll11a.comm:326`). Rule: exactly one of `RESULTAT`, `CHAM_GD`. |
| `ACTION / RESULTAT` | `resultat_sdaster`, optional | — | *result*. The result to read; the field is chosen by `NOM_CHAM` and the steps by the selection keywords below. |
| `ACTION / NOM_CHAM` | text, required | — | *field name*. Only when `exists("RESULTAT")`. The field of the result (233 names; see the .json): `'DEPL'`, `'REAC_NODA'`, `'SIGM_NOEU'`, `'SIEQ_ELNO'`, … It must exist in the result (`POSTRELE_46`): compute it first with `CALC_CHAMP`. |
| `ACTION / TOUT_ORDRE` | text, optional | — | *all steps*. One of `'OUI'`. Only when `exists("RESULTAT")`. Every step of the result: one set of rows per step (`upstream/astest/ssll14a.comm:208`). |
| `ACTION / NUME_ORDRE` | integer, optional, list | — | *step index*. Only when `exists("RESULTAT")`. These steps only. |
| `ACTION / LIST_ORDRE` | `listis_sdaster`, optional | — | Only when `exists("RESULTAT")`. These steps, from a list of integers. |
| `ACTION / NUME_MODE` | integer, optional, list | — | Only when `exists("RESULTAT")`. These mode numbers of a modal result. |
| `ACTION / LIST_MODE` | `listis_sdaster`, optional | — | Only when `exists("RESULTAT")`. These mode numbers, from a list. |
| `ACTION / NOEUD_CMP` | text, optional, list | — | Only when `exists("RESULTAT")`. Static modes of a `MODE_STATIQUE` result, by node and component. Not used in Tier 1. |
| `ACTION / NOM_CAS` | text, optional, list | — | Only when `exists("RESULTAT")`. Load cases of a `mult_elas` result, by name. Not used in Tier 1. |
| `ACTION / FREQ` | real, optional, list | — | *frequency*. Only when `exists("RESULTAT")`. These frequencies. |
| `ACTION / LIST_FREQ` | `listr8_sdaster`, optional | — | Only when `exists("RESULTAT")`. These frequencies, from a list. |
| `ACTION / INST` | real, optional, list | — | *time step (pseudo-time)*. Only when `exists("RESULTAT")`. These times; a time not in the result gives `POSTRELE_49`. |
| `ACTION / LIST_INST` | `listr8_sdaster`, optional | — | *time-step list*. Only when `exists("RESULTAT")`. These times, from a list. |
| `ACTION / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `exists("RESULTAT")`. How `INST`/`FREQ` are matched. |
| `ACTION / PRECISION` | real, optional | `1e-06` | *tolerance*. Only when `exists("RESULTAT") and equal_to("CRITERE", 'RELATIF')`. |
| `ACTION / PRECISION` | real, required | — | *tolerance*. Only when `exists("RESULTAT") and equal_to("CRITERE", 'ABSOLU')`. |
| `ACTION / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Only when `equal_to('OPERATION', 'EXTREMA')`; or `is_in('OPERATION', 'MOYENNE_ARITH')`; or `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. The whole mesh: the usual choice for `EXTREMA`. |
| `ACTION / GROUP_MA` | element group, optional, list | — | *element group*. Only when `equal_to('OPERATION', 'EXTREMA')`; or `is_in('OPERATION', 'MOYENNE_ARITH')`; or `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. These elements. For element fields (`_ELEM`) it is the only way to select (`POSTRELE_66`). For `EXTRACTION` and `MOYENNE` a node selection is still required (rule), and `GROUP_MA` then restricts the elements whose values are used at those nodes; with `MOYENNE` use it only on segment elements (U4.81.21 §4.1.2). |
| `ACTION / GROUP_NO` | node group, optional, list | — | *node group*. Only when `equal_to('OPERATION', 'EXTREMA')`; or `is_in('OPERATION', 'MOYENNE_ARITH')`; or `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. The nodes to read; required for `EXTRACTION` and `MOYENNE` (rule). Several groups or single-node groups can be listed (`upstream/astest/ssll14a.comm:211`). For `MOYENNE`, the nodes must form a line (`POSTRELE_6`). |
| `ACTION / TOUT_CMP` | text, optional | — | One of `'OUI'`. Only when `equal_to('OPERATION', 'EXTREMA')`; or `is_in('OPERATION', 'MOYENNE_ARITH')`; or `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. All components of the field. |
| `ACTION / NOM_CMP` | text, optional, list | — | *component name*. Only when `equal_to('OPERATION', 'EXTREMA')`; or `is_in('OPERATION', 'MOYENNE_ARITH')`; or `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. These components only, for example `('DX', 'DY', 'DZ')` or `'VMIS'`. A name the field does not have gives `POSTRELE_65`. |
| `ACTION / INVARIANT` | text, optional | — | One of `'OUI'`. Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. The invariants of a tensor field instead of its components (`upstream/astest/ssnv197a.comm:223`); the fields accepted are listed in `POSTRELE_33`. The table gets the columns `VON_MIS`, `TRESCA`, `TRACE` and `DETER` (U4.81.21 §5.2.7, §7.4). |
| `ACTION / ELEM_PRINCIPAUX` | text, optional | — | One of `'OUI'`. Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. The principal values of a tensor field, in increasing order, in the columns `VAL_PR_1`, `VAL_PR_2`, `VAL_PR_3` (U4.81.21 §5.2.8, §7.4). |
| `ACTION / RESULTANTE` | text, optional, list | — | *resultant components*. One of `'DX'`, `'DY'`, `'DZ'`, `'NXX'`, `'NYY'`, `'NXY'`, `'PRE1'`, `'PRE2'`, `'TEMP'`. Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. The sum of these components over the selected nodes: one row per step instead of one per node. Meant for nodal forces (`REAC_NODA`, `FORC_NODA`; comment at `upstream/bibfor/op/op0051.F90:149`): the reaction sum of a support (`tests/fixtures/solid_static/input/run.comm:48`). Only with `EXTRACTION` (`POSTRELE_67`). |
| `ACTION / MOMENT` | text, optional, list | — | *moment components*. One of `'DRX'`, `'DRY'`, `'DRZ'`, `'MXX'`, `'MYY'`, `'MXY'`. Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. With `RESULTANTE` and `POINT`: the moment of the nodal forces about `POINT` (`upstream/astest/ssll14a.comm:213`). Same length as `RESULTANTE`, 2 or 3 (`POSTRELE_42`). |
| `ACTION / POINT` | real, optional, list | — | *reference point*. Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. Coordinates of the point about which `MOMENT` is computed: 2 or 3 values (`POSTRELE_43`). |
| `ACTION / REPERE` | text, optional | `'GLOBAL'` | *coordinate system*. One of `'GLOBAL'`, `'LOCAL'`, `'POLAIRE'`, `'UTILISATEUR'`, `'CYLINDRIQUE'`. Axes in which vector and tensor components are written. `'UTILISATEUR'`: global axes rotated by `ANGL_NAUT`. `'CYLINDRIQUE'`: about the axis `ORIGINE`/`AXE_Z` (`upstream/astest/ssls502a.comm:90`). `'POLAIRE'`: polar axes in a plane mesh (`POSTRELE_28`). `'LOCAL'`: the local axes; required for shell and beam fields such as `EFGE_NOEU`, which only make sense there (`POSTRELE_70`). With `RESULTANTE`, only `'GLOBAL'` or `'UTILISATEUR'` (`POSTRELE_68`). |
| `ACTION / ANGL_NAUT` | real, optional, list of up to 3, at least 3 | — | Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. Three nautical angles, in degrees, that rotate the global axes into the user axes of `REPERE='UTILISATEUR'`. The usual nautical angles: a rotation about Z, then about the new Y, then about the new X (U4.81.21 §5.2.4; defined in U4.44.01 §3.9.3). |
| `ACTION / ORIGINE` | real, optional, list of up to 3, at least 3 | — | Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. A point of the axis of `REPERE='CYLINDRIQUE'`. Rule: with `AXE_Z`. A node on the axis cannot be expressed in cylindrical axes (`POSTRELE_31`). |
| `ACTION / AXE_Z` | real, optional, list of up to 3, at least 3 | — | Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. Direction of the axis of `REPERE='CYLINDRIQUE'`. |
| `ACTION / TRAC_NOR` | text, optional | — | One of `'OUI'`. Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. The normal trace of the field: for a flux, the flux through the line; for a stress, the traction on it (`upstream/astest/tpll01a.comm:294`). Plane meshes only (`POSTRELE_32`); fields accepted listed in `POSTRELE_34`. |
| `ACTION / TRAC_DIR` | text, optional | — | One of `'OUI'`. Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. The trace of the field along `DIRECTION` (fields listed in `POSTRELE_35`). Use it instead of `TRAC_NOR` in 3D. |
| `ACTION / DIRECTION` | real, optional, list | — | *direction*. Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. The direction vector of `TRAC_DIR`; a zero vector gives `POSTRELE_36`. |
| `ACTION / VECT_Y` | real, optional, list | — | Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. A vector that fixes the local Y axis along a line of nodes for `REPERE='LOCAL'`; needs one group of at least 2 nodes (`POSTRELE_21`, `POSTRELE_22`). For a 3D line, the projection of `VECT_Y` on the plane normal to the line is the normal; local components come in the order tangent, normal, binormal. Where the line bends, cut it into pieces with their own `VECT_Y` (U4.81.21 §5.2.4). |
| `ACTION / MOYE_NOEUD` | text, optional | `'OUI'` | One of `'OUI'`, `'NON'`. Only when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`. For element-node fields (`_ELNO`): `'OUI'` averages the values of the elements around each node; `'NON'` keeps one row per element and node, with a `MAILLE` column (`upstream/bibfor/postrele/rvpost.F90:159`, `upstream/bibfor/postrele/rvpara.F90:369`). Use `'NON'` to see the jump between elements. |
| `ACTION / FORMAT_C` | text, optional | `'MODULE'` | One of `'MODULE'`, `'REEL'`, `'IMAG'`. For complex fields (harmonic results): write the modulus, the real part or the imaginary part. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. |
| `TITRE` | text, optional | — | *title*. Title of the table. |

2 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- `ACTION`: exactly one of `RESULTAT`, `CHAM_GD` must be given (`UN_PARMI`).
- when `exists("RESULTAT")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `LIST_ORDRE`, `NUME_MODE`, `LIST_MODE`, `INST`, `LIST_INST`, `FREQ`, `LIST_FREQ`, `NOEUD_CMP`, `NOM_CAS` may be given (`EXCLUS`).
- when `equal_to('OPERATION', 'EXTREMA')`: at most one of `TOUT_CMP`, `NOM_CMP` may be given (`EXCLUS`).
- when `is_in('OPERATION', 'MOYENNE_ARITH')`: at most one of `TOUT_CMP`, `NOM_CMP` may be given (`EXCLUS`).
- when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`: at least one of `GROUP_NO`, `NOEUD` must be given (`AU_MOINS_UN`).
- when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`: exactly one of `TOUT_CMP`, `NOM_CMP`, `INVARIANT`, `ELEM_PRINCIPAUX`, `RESULTANTE` must be given (`UN_PARMI`).
- when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`: if `TRAC_DIR` is given, `DIRECTION` must all be given (`PRESENT_PRESENT`).
- when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`: `MOMENT`, `POINT` are given all together or not at all (`ENSEMBLE`).
- when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`: if `MOMENT` is given, `RESULTANTE` must all be given (`PRESENT_PRESENT`).
- when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`: if `TOUT_CMP` is given, none of `TRAC_DIR`, `TRAC_NOR` may be given (`PRESENT_ABSENT`).
- when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`: at most one of `TRAC_DIR`, `TRAC_NOR` may be given (`EXCLUS`).
- when `not is_in('OPERATION', ('EXTREMA', 'MOYENNE_ARITH'))`: if `ORIGINE` is given, `AXE_Z` must all be given (`PRESENT_PRESENT`).

## What the table contains

- `RESULTANTE`: one row per step with `INTITULE`, `RESU`, `NOM_CHAM`, `NUME_ORDRE`, `INST` and one
  column per component. Our solid fixture gives `REAC_BASE, …, REAC_NODA, 1, 0.0, 3.89164E+03,
  -1.77693E-10, 1.27073E-10` (`tests/fixtures/solid_static/output/tables/reactions.csv`).
- Plain `EXTRACTION`: one row per node and step, with the node name (`NOEUD`), the curvilinear
  abscissa along the node list (`ABSC_CURV`) and the coordinates (`COOR_X`, …) before the
  components (`upstream/bibfor/postrele/rvtec0.F90:221`–`:237`).
- `MOYENNE`: the columns of `rvtamo.F90:68` per component.

## Patterns

### Reaction sum on a support

The Tier 1 equilibrium check: the sum of `REAC_NODA` on the clamped nodes balances the applied
load.

Source: `tests/fixtures/solid_static/input/run.comm:48`.

```python
REAC = POST_RELEVE_T(
    ACTION=_F(
        OPERATION="EXTRACTION",
        INTITULE="REAC_BASE",
        RESULTAT=RESU,
        NOM_CHAM="REAC_NODA",
        GROUP_NO="BASE",
        RESULTANTE=("DX", "DY", "DZ"),
    )
)
```

### Resultant force and moment about a point, every step

Source: `upstream/astest/ssll14a.comm:203`.

```python
TAB_REAC = POST_RELEVE_T(
    ACTION=_F(
        RESULTAT=STATIQUE,
        INTITULE="REACTION",
        NOM_CHAM="REAC_NODA",
        TOUT_ORDRE="OUI",
        REPERE="GLOBAL",
        OPERATION="EXTRACTION",
        GROUP_NO=("N41", "N1"),
        RESULTANTE=("DX", "DY", "DZ"),
        MOMENT=("DRX", "DRY", "DRZ"),
        POINT=(10.0, 12.0, 0.0),
    )
)
```

### Displacements in cylindrical axes along a line

Source: `upstream/astest/ssls502a.comm:90`.

```python
DEP_NORM = POST_RELEVE_T(
    ACTION=_F(
        OPERATION="EXTRACTION",
        INTITULE="TAB_NORM",
        RESULTAT=RESU,
        NOM_CHAM="DEPL",
        GROUP_NO="CD",
        NOM_CMP=("DX", "DY", "DZ"),
        REPERE="CYLINDRIQUE",
        ORIGINE=(0.0, 0.0, 0.0),
        AXE_Z=(0.0, 1.0, 0.0),
    )
)
```

### Maximum equivalent stress over the model

Source: `upstream/astest/forma02a.comm:90`.

```python
TA = POST_RELEVE_T(
    ACTION=_F(OPERATION="EXTREMA", INTITULE="VALEMAX", RESULTAT=RESU, NOM_CHAM="SIEQ_ELNO")
)
```

### Stress invariants at a point

Source: `upstream/astest/ssnv197a.comm:223`.

```python
TAB_SIG = POST_RELEVE_T(
    ACTION=_F(
        INTITULE="EQUI_NOEU_DEPL",
        GROUP_NO="C",
        RESULTAT=U1,
        NOM_CHAM="SIGM_NOEU",
        INVARIANT="OUI",
        OPERATION="EXTRACTION",
    )
)
```

### Mean along a line of nodes

`GM35` is a node group built from the edge elements `GM35` just before (`:196`).

Source: `upstream/astest/forma21a.comm:200`.

```python
    TMOYEN[num_calc] = POST_RELEVE_T(
        ACTION=_F(
            INTITULE="TMOYEN",
            GROUP_NO="GM35",
            RESULTAT=TEMP[num_calc],
            NOM_CHAM="TEMP",
            NOM_CMP=("TEMP"),
            OPERATION="MOYENNE",
        )
    )
```

### Arithmetic mean of a field object

Source: `upstream/astest/ssll11a.comm:326`.

```python
T3 = POST_RELEVE_T(
    ACTION=_F(
        INTITULE="CH1", OPERATION="MOYENNE_ARITH", GROUP_NO=("GROUP_NO_GNAB", "C", "D"), CHAM_GD=CH1
    )
)
```

## Pitfalls

- **The field must exist first.** `POST_RELEVE_T` computes nothing: `REAC_NODA`, `SIGM_NOEU`,
  `SIEQ_NOEU` must be computed by `CALC_CHAMP` before; otherwise `POSTRELE_46` (field not allowed
  or no field exists).
- **Gauss-point fields are refused.** `SIEF_ELGA` and other `_ELGA` fields give `POSTRELE_47`.
  Extract `SIEF_ELNO`/`SIGM_NOEU` instead, or use `POST_ELEM` for integrals over elements.
- **`RESULTANTE` is a plain sum.** It adds the component values of the selected nodes. That is a
  force resultant only for nodal force fields (`REAC_NODA`, `FORC_NODA`); on `DEPL` or
  `SIGM_NOEU` the number has no physical meaning. Its sign is that of the field: `REAC_NODA` is
  the support reaction, opposite to the applied load (our fixtures: `+3891.64` N in X for a
  resultant pressure load along −X, `tests/fixtures/solid_static/input/run.comm:70`).
- **Shell and beam fields need `REPERE='LOCAL'`.** `EFGE_NOEU`, `SIGM_NOEU`, `SIEF_NOEU`,
  `DEGE_NOEU`, `EPSI_NOEU` on a model with structural elements only make sense in the element
  axes; any other `REPERE` gives warning `POSTRELE_70` (`upstream/bibfor/op/op0051.F90:181`).
- **Nodes outside the model.** Nodes that carry no value of the field (for example nodes of a
  group that no modeled element uses) give `POSTRELE_18` or `POSTRELE_64`. Check that the group
  is on the modeled elements.
- **Distributed parallel runs.** `MOYENNE`, `EXTREMA` and `MOYENNE_ARITH` are not allowed
  with a distributed mesh (`POSTRELE_24`).

## See also

- French reference: U4.81.21 (French text: `en/docs/_src/U4.81.21.fr.md`; translation: `en/docs/U4.81.21.md`). The
  catalog's `docu=` takes precedence over en/doc-ids.yaml.
- Catalog: `en/commands/POST_RELEVE_T.json` (generated from `upstream/code_aster/Cata/Commands/post_releve_t.py:26`)
- Implementation: `upstream/bibfor/op/op0051.F90`; `upstream/bibfor/postrele/rvpost.F90`
  (extraction), `rvmoye.F90` (`MOYENNE_ARITH`), `upstream/bibfor/algorith/rvmima.F90` (`EXTREMA`), `rvtamo.F90`
  (`MOYENNE` table), `rvtec0.F90` (extraction table)
- Before: [CALC_CHAMP](CALC_CHAMP.md), [MECA_STATIQUE](MECA_STATIQUE.md), `DEFI_GROUP` for the node
  groups
- Next steps: [IMPR_TABLE](IMPR_TABLE.md), `TEST_TABLE`, [TEST_RESU](TEST_RESU.md) for direct checks
- Example: `upstream/astest/ssll14a.comm` (line 203)
- Example: `upstream/astest/ssls502a.comm` (line 90)
- Example: `upstream/astest/forma02a.comm` (line 90)
- Example: `tests/fixtures/solid_static/input/run.comm` (line 48)
- Example: `tests/fixtures/shell_static/input/run.comm` (line 67)
