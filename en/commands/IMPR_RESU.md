---
command: IMPR_RESU
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/impr_resu.py:25
doc_fr: U4.91.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3d)
examples: [hplv101b, forma30a, forma04b, ahlv100a, hsnv132c]
---

# IMPR_RESU — write mesh and results to a file

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.

`IMPR_RESU` writes a mesh, a field or a result to a file, for viewing in a post-processor or
for reading by a program. The default and Tier 1 format is MED (the `.rmed` file ParaVis and
`caen` read); `'RESULTAT'` prints values as text, `'GMSH'` and `'IDEAS'` feed those tools.
Each `RESU` occurrence selects what to write: which result or field, which fields
(`NOM_CHAM`), which steps, which components and which region (`GROUP_MA`, `GROUP_NO`). It is a
procedure: it creates no object. Only fields that exist in the result are written, so derived
fields (`SIGM_NOEU`, `SIEQ_NOEU`, `REAC_NODA`) must come from `CALC_CHAMP` first.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Imprimer un maillage et/ou les résultats d'un calcul (différents formats)» |
| Kind | `PROC` (operator 39; Python wrapper `upstream/code_aster/CodeCommands/impr_resu.py`) |
| Result | none (writes a file) |
| Can reuse its input (`reuse=`) | not applicable |
| French reference | U4.91.01 — from en/doc-ids.yaml (status: proposed; docs/PLAN.md 5.1 says U4.81.01) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `FORMAT`, `MED`, `RESU`, `RESULTAT`, `NOM_CHAM`, `GROUP_MA`, `UNITE` |

## Keywords

The catalog defines one `UNITE` (with its own default) and one `RESU` per `FORMAT`; this table
merges the `RESU` blocks and says in each row which formats accept the keyword.

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `FORMAT` | text, optional | `'MED'` | *file format*. One of `'RESULTAT'`, `'IDEAS'`, `'ASTER'`, `'MED'`, `'GMSH'`. `'MED'` (default): binary MED file for ParaVis/Salome, the Tier 1 output and what `caen` reads. `'RESULTAT'`: readable text listing of values. `'GMSH'`: Gmsh post-processing file. `'IDEAS'`: I-DEAS universal file. `'ASTER'`: mesh only, in the native mesh format (`RESULT3_70`, `upstream/bibfor/prepost/irmfac.F90:246`). |
| `PROC0` | text, optional | — | One of `'OUI'`, `'NON'`. Parallel runs: `'OUI'` writes from process 0 only. When not given it is set to `'OUI'`, or to `'NON'` in HPC mode (parallel mesh) (`upstream/code_aster/CodeCommands/impr_resu.py:72`). |
| `MODELE` | `modele_sdaster`, optional | — | *model*. Only when `not equal_to("FORMAT", 'MED')`. Formats other than MED: the model, to know which elements carry the field. With a result it is read from the result (`upstream/bibfor/prepost/irmfac.F90:175`). |
| `UNITE` | `UnitDefault`, optional | `8` | *logical unit*. Only when `equal_to("FORMAT", 'RESULTAT')`. Logical unit of the text listing; 8 is the run's `.resu` file. |
| `UNITE` | `UnitDefault`, optional | `30` | *logical unit*. Only when `equal_to("FORMAT", 'IDEAS')`. Logical unit of the I-DEAS file. |
| `VERSION` | integer, optional | `5` | One of `4`, `5`. Only when `equal_to("FORMAT", 'IDEAS')`. I-DEAS universal file version. Not used in Tier 1. |
| `UNITE` | `UnitDefault`, optional | `26` | *logical unit*. Only when `equal_to("FORMAT", 'ASTER')`. Logical unit of the mesh file. |
| `UNITE` | `UnitMed`, optional | `80` | *logical unit*. Only when `equal_to("FORMAT", 'MED')`. Logical unit of the MED file. 80 is the usual `rmed` output unit; the unit must be declared in the `.export` (or by `DEFI_FICHIER`) for the file to be kept. |
| `FICHIER_UNIQUE` | text, optional | `'NON'` | Parameter to write the results into a single file. One of `'OUI'`, `'NON'`. Only when `equal_to("FORMAT", 'MED')`. Parallel runs: write one file for all processes. Only with a parallel mesh; otherwise it is forced to `'NON'` (`upstream/code_aster/CodeCommands/impr_resu.py:99`). |
| `VERSION_MED` | text, optional | `'3.3.1'` | Choice of the MED file version. One of `'3.3.1'`, `'4.0.0'`, `'4.1.0'`, `'4.2.0'`. Only when `equal_to("FORMAT", 'MED') and equal_to("FICHIER_UNIQUE", 'NON')`. MED file format version. Keep the default unless the post-processor needs another. |
| `VERSION_MED` | text, optional | `'4.2.0'` | Choice of the MED file version. One of `'4.2.0'`. Only when `equal_to("FORMAT", 'MED') and equal_to("FICHIER_UNIQUE", "OUI")`. MED file format version for a single parallel file. |
| `UNITE` | `UnitDefault`, optional | `37` | *logical unit*. Only when `equal_to("FORMAT", 'GMSH')`. Logical unit of the Gmsh file. |
| `VERSION` | real, optional | `1.2` | One of `1.0`, `1.2`. Only when `equal_to("FORMAT", 'GMSH')`. Gmsh file format version. Not used in Tier 1. |
| `RESU` | factor keyword, required, repeatable | — | Only when `equal_to("FORMAT", 'MED')`; or `equal_to("FORMAT", 'RESULTAT')`; or `equal_to("FORMAT", 'GMSH')`; or `equal_to("FORMAT", 'IDEAS')`; or `equal_to("FORMAT", 'ASTER')`. One block to write: a mesh, a field object or a result, with the fields, steps, components and region to keep. Repeat it to write several results or selections to the same file. The catalog defines one `RESU` per `FORMAT`; the keywords below say where they apply. |
| `RESU / MAILLAGE` | `maillage_sdaster` or `squelette`, optional | — | *mesh*. The mesh to write. Alone, it writes the mesh only (`upstream/astest/hplv101b.comm:89`); with a result, mesh and fields. A mesh different from the model's mesh is refused (`RESULT3_66`). |
| `RESU / CARA_ELEM` | `cara_elem`, optional | — | *element properties*. Element properties. Give it for shells, beams and pipes so that fields with sub-points (layers, fibers) are written with their structure (`tests/fixtures/shell_static/input/run.comm:83`). TODO(verify) the effect on the MED file against U4.91.01. |
| `RESU / VISU_SP` | text, optional | — | One of `'NON'`. Only when `not exists("CARA_ELEM")`. MED, without `CARA_ELEM`: `'NON'` writes no sub-point information (`upstream/bibfor/prepost/irmfac.F90:139`). TODO(verify) against U4.91.01. |
| `RESU / CHAM_GD` | `cham_gd_sdaster`, optional | — | *field (physical quantity)*. A field object (for example from `CREA_CHAMP`) instead of a result. In MED it is named after its Python variable (`upstream/code_aster/CodeCommands/impr_resu.py:57`). |
| `RESU / RESULTAT` | `resultat_sdaster`, optional | — | *result*. The result to write. The usual Tier 1 choice, with `NOM_CHAM`. |
| `RESU / TYPE_NOM` | text, optional | `'NUME_ORDRE'` | One of `'NUME_ORDRE'`, `'NOM_CAS'`. Only when `is_type("RESULTAT") == mult_elas`. MED, `mult_elas` results: name the stored fields by step index or by load case name. Not used in Tier 1. |
| `RESU / INFO_MAILLAGE` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. MED only (`RESULT3_63`): `'OUI'` prints information on the written mesh in the message file. |
| `RESU / PARTIE` | text, optional | — | One of `'REEL'`, `'IMAG'`, `'MODULE'`, `'PHASE'`. For complex fields (harmonic results): which part to write. Required for complex fields in MED and GMSH (`RESULT3_69`, `upstream/bibfor/prepost/irmfac.F90:196`). Formats MED and RESULTAT. |
| `RESU / IMPR_NOM_VARI` | text, optional | `'OUI'` | One of `'OUI'`, `'NON'`. MED: `'OUI'` writes the names of the internal variables of `VARI_ELGA`/`VARI_NOEU` with the field, so that post-processors show names instead of `V1`, `V2`, … (`upstream/bibfor/prepost/irmfac.F90:333`). |
| `RESU / TOUT_CHAM` | text, optional | — | One of `'OUI'`, `'NON'`. Only when `exists("RESULTAT")`. With `RESULTAT`: `'OUI'` writes every field stored in the result. In MED it is the default when `NOM_CHAM` is not given (catalog rule `UN_PARMI("TOUT_CHAM", "NOM_CHAM", TOUT_CHAM="OUI")`). |
| `RESU / NOM_CHAM` | text, optional, list | — | *field name*. One of `'ACCE'`, `'ACCE_ABSOLU'`, `'COEF_H'`, `'COMPORTEMENT'`, `'COMPORTHER'`, `'CONT_ELEM'`, `'CONT_NOEU'`, `'DEGE_ELGA'`, `'DEGE_ELNO'`, `'DEGE_NOEU'`, `'DEPL'`, `'DEPL_ABSOLU'`, … (233 values; see the .json). Only when `exists("RESULTAT")`. With `RESULTAT`: the fields to write, for example `("DEPL", "SIGM_NOEU", "SIEQ_NOEU", "REAC_NODA")` (`tests/fixtures/solid_static/input/run.comm:64`). They must have been computed (by `CALC_CHAMP` for derived fields). In MED, each is named `<result name, 8 characters padded with _><field>`, for example `RESU____DEPL` (`upstream/code_aster/CodeCommands/impr_resu.py:49`; fixture `tests/fixtures/solid_static/output/run.rmed`). |
| `RESU / TOUT_ORDRE` | text, optional | — | One of `'OUI'`. Only when `exists("RESULTAT")`. With `RESULTAT`: every step (the default). |
| `RESU / NUME_ORDRE` | integer, optional, list | — | *step index*. Only when `exists("RESULTAT")`. With `RESULTAT`: these steps only. |
| `RESU / NUME_MODE` | integer, optional, list | — | Only when `exists("RESULTAT")`. With `RESULTAT`: these modes only (modal result). |
| `RESU / LIST_ORDRE` | `listis_sdaster`, optional | — | Only when `exists("RESULTAT")`. With `RESULTAT`: steps from a list. |
| `RESU / NOEUD_CMP` | text, optional, list | — | Only when `exists("RESULTAT")`. With `RESULTAT`: these static modes. Not used in Tier 1. |
| `RESU / NOM_CAS` | text, optional, list | — | Only when `exists("RESULTAT")`. With `RESULTAT`: these load cases. Not used in Tier 1. |
| `RESU / ANGLE` | real, optional, list | — | Only when `exists("RESULTAT")`. With `RESULTAT`: these Fourier angles. Not used in Tier 1. |
| `RESU / FREQ` | real, optional, list | — | *frequency*. Only when `exists("RESULTAT")`. With `RESULTAT`: these frequencies. |
| `RESU / LIST_FREQ` | `listr8_sdaster`, optional | — | Only when `exists("RESULTAT")`. With `RESULTAT`: frequencies from a list. |
| `RESU / INST` | real, optional, list | — | *time step (pseudo-time)*. Only when `exists("RESULTAT")`. With `RESULTAT`: these times only (`upstream/astest/forma04b.comm:198`). |
| `RESU / LIST_INST` | `listr8_sdaster`, optional | — | *time-step list*. Only when `exists("RESULTAT")`. With `RESULTAT`: times from a list. |
| `RESU / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `exists("RESULTAT") and (exists("ANGLE"))or(exists("FREQ"))or(exists("LIST_FREQ"))or(exists("INST"))or(exists("LIST_INST"))`. How `INST`/`FREQ`/`ANGLE` are matched. |
| `RESU / PRECISION` | real, optional | `1e-06` | *tolerance*. Only when `exists("RESULTAT") and (exists("ANGLE"))or(exists("FREQ"))or(exists("LIST_FREQ"))or(exists("INST"))or(exists("LIST_INST")) and equal_to("CRITERE", 'RELATIF')`. Matching tolerance. |
| `RESU / PRECISION` | real, required | — | *tolerance*. Only when `exists("RESULTAT") and (exists("ANGLE"))or(exists("FREQ"))or(exists("LIST_FREQ"))or(exists("INST"))or(exists("LIST_INST")) and equal_to("CRITERE", 'ABSOLU')`. Matching tolerance, required with `'ABSOLU'`. |
| `RESU / NOM_PARA` | text, optional, list | — | *parameter name*. With `RESULTAT`: the result parameters (for example `INST`, `FREQ`) to print with the fields. Formats MED and RESULTAT. TODO(verify) the MED effect against U4.91.01. |
| `RESU / TOUT_CMP` | text, optional | — | One of `'OUI'`. All components (formats MED and RESULTAT). |
| `RESU / NOM_CMP` | text, optional, list | — | *component name*. Formats MED and RESULTAT (and GMSH with `TYPE_CHAM='SCALAIRE'`): write only these components, for example `('VMIS', 'TRSIG')`. In MED it cannot be combined with `NOM_RESU_MED` (`MED3_6`). |
| `RESU / NOM_CHAM_MED` | text, optional, list | — | Only when `exists("CHAM_GD") or exists("RESULTAT")`. MED: the names to give the fields in the file, one per field (at most 64 characters), instead of the automatic `<result>_<field>` name (`upstream/astest/ahlv100a.comm:430`). Rule: not with `NOM_RESU_MED`. |
| `RESU / NOM_RESU_MED` | text, optional | — | Only when `exists("CHAM_GD") or exists("RESULTAT")`. MED: the result prefix (at most 8 characters) used to name fields instead of the result's variable name. |
| `RESU / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. The whole mesh (formats MED and RESULTAT). |
| `RESU / GROUP_NO` | node group, optional, list | — | *node group*. Formats MED and RESULTAT: restrict the output to these nodes. |
| `RESU / GROUP_MA` | element group, optional, list | — | *element group*. Restrict the output to these elements (formats MED, RESULTAT and GMSH). Use it to write a region of a large model. |
| `RESU / SOUS_TITRE` | text, optional | — | *subtitle*. Subtitle (formats MED and RESULTAT). |
| `RESU / TOUT_PARA` | text, optional | — | One of `'OUI'`, `'NON'`. RESULTAT format: print all result parameters for each step (`'OUI'`) or none (`'NON'`). Rule: not with `NOM_PARA`. |
| `RESU / FORM_TABL` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`, `'EXCEL'`. RESULTAT format: print the values as a table (`'OUI'`), as tab-separated columns for a spreadsheet (`'EXCEL'`), or in the default listing layout (`'NON'`) (`upstream/bibfor/prepost/irmfac.F90:118`). |
| `RESU / VALE_MAX` | text, optional | — | One of `'OUI'`. RESULTAT format: print only the maximum of each component, and where it occurs (`upstream/astest/forma30a.comm:108`). |
| `RESU / VALE_MIN` | text, optional | — | One of `'OUI'`. RESULTAT format: print only the minimum of each component, and where it occurs. |
| `RESU / BORNE_SUP` | real, optional | — | RESULTAT format: print only values below this bound. TODO(verify) against U4.91.01. |
| `RESU / BORNE_INF` | real, optional | — | RESULTAT format: print only values above this bound. TODO(verify) against U4.91.01. |
| `RESU / IMPR_COOR` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. RESULTAT format: `'OUI'` also prints the node coordinates (`upstream/bibfor/prepost/irmfac.F90:148`). |
| `RESU / FORMAT_R` | text, optional | `'1PE21.14'` | RESULTAT format: Fortran edit descriptor of real values (default `1PE21.14`, 14 decimals). |
| `RESU / PARTIE` | text, optional | — | One of `'REEL'`, `'IMAG'`. GMSH format: real or imaginary part of a complex field. |
| `RESU / TYPE_CHAM` | text, optional | `'SCALAIRE'` | *field type*. One of `'VECT_2D'`, `'VECT_3D'`, `'SCALAIRE'`, `'TENS_2D'`, `'TENS_3D'`. GMSH format: how the components are drawn: one scalar view per component (`'SCALAIRE'`), as a 2D or 3D vector, or as a 2D or 3D tensor. |
| `RESU / NOM_CMP` | text, required, list of up to 2, at least 2 | — | *component name*. Only when `equal_to("TYPE_CHAM", 'VECT_2D')`. GMSH, `TYPE_CHAM='VECT_2D'`: the two components of the vector, for example `('DX', 'DY')`. |
| `RESU / NOM_CMP` | text, required, list of up to 3, at least 3 | — | *component name*. Only when `equal_to("TYPE_CHAM", 'VECT_3D')`. GMSH, `TYPE_CHAM='VECT_3D'`: the three components of the vector. |
| `RESU / NOM_CMP` | text, required, list of up to 4, at least 4 | — | *component name*. Only when `equal_to("TYPE_CHAM", 'TENS_2D')`. GMSH, `TYPE_CHAM='TENS_2D'`: the four components of the tensor. |
| `RESU / NOM_CMP` | text, required, list of up to 6, at least 6 | — | *component name*. Only when `equal_to("TYPE_CHAM", 'TENS_3D')`. GMSH, `TYPE_CHAM='TENS_3D'`: the six components of the tensor. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. |

1 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- `RESU`: at least one of `CHAM_GD`, `RESULTAT`, `MAILLAGE` must be given (`AU_MOINS_UN`).
- `RESU`: at most one of `CHAM_GD`, `RESULTAT` may be given (`EXCLUS`).
- `RESU`: at most one of `TOUT_CMP`, `NOM_CMP` may be given (`EXCLUS`).
- when `exists("RESULTAT")`: exactly one of `TOUT_CHAM`, `NOM_CHAM` must be given; if none is given, `TOUT_CHAM='OUI'` is assumed (`UN_PARMI`).
- when `exists("RESULTAT")`: at most one of `TOUT_ORDRE`, `NUME_ORDRE`, `INST`, `FREQ`, `NUME_MODE`, `NOEUD_CMP`, `LIST_INST`, `LIST_FREQ`, `LIST_ORDRE`, `NOM_CAS`, `ANGLE` may be given (`EXCLUS`).
- when `exists("CHAM_GD") or exists("RESULTAT")`: at most one of `NOM_CHAM_MED`, `NOM_RESU_MED` may be given (`EXCLUS`).
- `RESU`: at most one of `TOUT_PARA`, `NOM_PARA` may be given (`EXCLUS`).
- when `exists("RESULTAT")`: at most one of `TOUT_CHAM`, `NOM_CHAM` may be given (`EXCLUS`).

## What the solver does

- Before the solver runs, the Python wrapper names MED fields: with `NOM_CHAM`, each field gets
  `NOM_CHAM_MED = <result name truncated to 8 characters, padded with "_"> + <field name>`;
  without `NOM_CHAM`, `NOM_RESU_MED` is set to the result name. A field object gets its variable
  name. Objects without a user name get the automatic name and warning `MED3_2`
  (`upstream/code_aster/CodeCommands/impr_resu.py:34`–`:62`).
- Our fixtures show the result: `RESU____DEPL`, `RESU____SIGM_NOEU`, `RESU____SIEQ_NOEU`,
  `RESU____REAC_NODA` (solid), `RESU____EFGE_NOEU` (shell), `MODES___DEPL` (modal)
  (the `output/run.rmed` file of each fixture under `tests/fixtures/`).
- `PROC0` and `FICHIER_UNIQUE` are adjusted for parallel runs (`impr_resu.py:72`, `:99`).

## Patterns

### Tier 1 MED output of a static result

The fields named must exist in the result: here `CALC_CHAMP` computed `SIGM_NOEU`, `SIEQ_NOEU`
and `REAC_NODA` before.

Source: `tests/fixtures/solid_static/input/run.comm:61`.

```python
IMPR_RESU(
    FORMAT="MED",
    UNITE=80,
    RESU=_F(RESULTAT=RESU, NOM_CHAM=("DEPL", "SIGM_NOEU", "SIEQ_NOEU", "REAC_NODA")),
)
```

### Shell result with element properties

Source: `tests/fixtures/shell_static/input/run.comm:80`.

```python
IMPR_RESU(
    FORMAT="MED",
    UNITE=80,
    RESU=_F(RESULTAT=RESU, CARA_ELEM=CARA, NOM_CHAM=("DEPL", "EFGE_NOEU", "REAC_NODA")),
)
```

### Mesh only

To check a mesh and its groups in a viewer.

Source: `upstream/astest/hplv101b.comm:89`.

```python
IMPR_RESU(FORMAT="MED", RESU=_F(MAILLAGE=MAI))
```

### Text listing of values at a node group

Source: `upstream/astest/forma04b.comm:198`.

```python
IMPR_RESU(
    FORMAT="RESULTAT",
    UNITE=17,
    RESU=_F(RESULTAT=STNL, GROUP_NO="C1", INST=1.0, NOM_CHAM=("PRES_NOEU")),
)
```

### Extreme values only, at chosen times

Source: `upstream/astest/forma30a.comm:108`.

```python
IMPR_RESU(
    FORMAT="RESULTAT",
    RESU=_F(
        RESULTAT=TEMPE,
        INST=(0.0, 0.10000000000000001, 4.0, 10.0, 100.0),
        VALE_MAX="OUI",
        VALE_MIN="OUI",
    ),
)
```

### Gmsh output

Source: `upstream/astest/hsnv132c.comm:149`.

```python
IMPR_RESU(FORMAT="GMSH", UNITE=37, RESU=_F(RESULTAT=RES_XFEM, NOM_CHAM="DEPL"))
```

## Pitfalls

- **Only stored fields are written.** `NOM_CHAM="SIEQ_NOEU"` writes nothing useful unless
  `CALC_CHAMP` computed it. Compute first, then write.
- **MED field names are built from the variable name.** Renaming the Python variable of the
  result renames the fields in the file (`RESU____DEPL` comes from a result called `RESU`).
  Names longer than 8 characters are truncated (`impr_resu.py:43`). Tools that look fields up by
  name (ParaVis states, `caen` readers) must follow.
- **Unit and `.export`.** The MED file reaches the user only if its unit (80 by default) is
  declared as an output in the `.export` or with `DEFI_FICHIER`.
- **Complex fields need `PARTIE`** in MED and GMSH (`RESULT3_69`).
- **`FORMAT='ASTER'` writes only a mesh.** Without `MAILLAGE` nothing is written (`RESULT3_70`).
- **`NOM_CMP` and `NOM_RESU_MED` do not mix** in MED (`MED3_6`): with `NOM_CMP` and no
  `NOM_CHAM`, the wrapper leaves the automatic naming (`impr_resu.py:53`).
- **Shell and beam fields.** Pass `CARA_ELEM` for structural elements so that sub-point fields
  are written with their layer or fiber structure (our shell fixture does). TODO(verify) what is
  written without it, against U4.91.01.

## See also

- French reference: U4.91.01 (translation: `en/docs/U4.91.01.md` once task 5.x lands). The ID
  is not settled: docs/PLAN.md 5.1 names U4.81.01 (recorded in en/doc-ids.yaml).
- Catalog: `en/commands/IMPR_RESU.json` (generated from `upstream/code_aster/Cata/Commands/impr_resu.py:25`)
- Implementation: `upstream/code_aster/CodeCommands/impr_resu.py`; `upstream/bibfor/prepost/irmfac.F90`
  (reads each `RESU` occurrence)
- Before: [CALC_CHAMP](CALC_CHAMP.md), [MECA_STATIQUE](MECA_STATIQUE.md)
- Related: [IMPR_TABLE](IMPR_TABLE.md) for tables
- Example: `tests/fixtures/solid_static/input/run.comm` (line 61)
- Example: `tests/fixtures/modal/input/run.comm` (line 47)
- Example: `upstream/astest/forma30a.comm` (line 108)
