---
command: LIRE_MAILLAGE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/lire_maillage.py:87
doc_fr: U4.21.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3a)
examples: [cont201e, supv003c, cont200a, cont007a, sdnx101e, ssnv227a, zzzz139a]
---

# LIRE_MAILLAGE — read mesh

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.

`LIRE_MAILLAGE` reads a mesh file and returns a mesh result object (`maillage_sdaster`; a
`maillage_p` parallel mesh when `PARTITIONNEUR='PTSCOTCH'` is used in an MPI run). It is
normally the first command after `DEBUT`: everything else (model, materials, loads, groups)
refers to this mesh. The decisions it encodes are which file to read (`UNITE`, the logical
unit that the `.export` file binds to a path), which format that file is in (`FORMAT`), which
mesh to take when a MED file holds several (`NOM_MED`), and whether to run the mesh checks on
read (`VERI_MAIL`). Element groups and node groups stored in the file come with the mesh and
are what later commands use in `GROUP_MA` / `GROUP_NO`.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Crée un maillage par lecture d'un fichier» |
| Kind | `OPER` |
| Result | `maillage_sdaster`, `maillage_p` (depends on the keywords given) |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.21.01 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `FORMAT`, `MED`, `UNITE`, `VERI_MAIL` |

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `FORMAT` | text, optional | `'MED'` | *file format*. One of `'ASTER'`, `'GIBI'`, `'GMSH'`, `'IDEAS'`, `'MED'`. Use `'MED'` (the default) for meshes from Salome, Gmsh (MED export) and most pre-processors; it is also the only format that can be partitioned (`PARTITIONNEUR`). `'GMSH'`, `'GIBI'` and `'IDEAS'` files are first converted to the native `'ASTER'` text format by `PRE_GMSH` / `PRE_GIBI` / `PRE_IDEAS` and then read (`upstream/code_aster/CodeCommands/lire_maillage.py:76`). `'ASTER'` is the native text format, used mostly by test cases. |
| `VERI_MAIL` | factor keyword, optional, present by default | — | *mesh checks*. Mesh checks run right after reading. Present by default with `VERIF='OUI'`, so the checks run unless you switch them off. |
| `VERI_MAIL / VERIF` | text, optional | `'OUI'` | *check*. One of `'OUI'`, `'NON'`. `'OUI'` runs the checks of `chckma` (`upstream/bibfor/modelisa/chckma.F90`): orphan nodes (warning `MODELISA4_6`), nodes shared by more than 200 elements (`MODELISA4_7`), double elements with the same connectivity (`MODELISA4_8`), POI1 elements sitting on nodes of other elements (`MODELISA8_14`), flat elements (`MODELISA4_9`, see `APLAT`), and for quadratic meshes edges or faces that share their corner nodes but not their mid-side nodes (`MODELISA4_11`, `MODELISA4_12`, then fatal `MODELISA4_10`). Keep `'OUI'`. Use `'NON'` only to get past the check while you locate the bad elements, as the advice in `MODELISA4_10` suggests. |
| `VERI_MAIL / APLAT` | real, optional | `0.001` | Flatness threshold. For each element the check computes the ratio of the shortest to the longest distance between any two of its nodes; below `APLAT` the element is reported as degenerate (`MODELISA8_15` per element, then `MODELISA4_9`) (`upstream/bibfor/modelisa/chckma.F90:267`). Raise it to catch badly shaped elements earlier, lower it to silence warnings on meshes with intentionally thin elements. |
| `UNITE` | `UnitDefault`, optional | `20` | *logical unit*. Range: ≥ 2. Only when `not equal_to("FORMAT", 'MED')`. Logical unit of the mesh file. The `.export` file binds it to a path, for example `F msh ssnp152a.msh D 19` with `FORMAT='GMSH', UNITE=19` (`upstream/astest/cont007a.export`). Give it whenever the file is not on unit 20. |
| `UNITE` | `UnitMed`, optional | `20` | *logical unit*. Range: ≥ 2. Only when `equal_to("FORMAT", 'MED')`. Logical unit of the MED file, bound in the `.export` file by a line such as `F mmed mesh.med D 20` (`tests/fixtures/solid_static/input/run.export`). The default 20 matches the usual `.export` convention, so `UNITE` is often omitted. |
| `NOM_MED` | text, optional | — | Name of the mesh in the MED file. Only when `equal_to("FORMAT", 'MED')`. A MED file can hold several meshes. Without `NOM_MED` the first mesh in the file is read (`upstream/bibcxx/IOManager/MeshReader.cxx:299`); give it when the file holds more than one, as in `upstream/astest/zzzz139a.comm:217`. The mesh actually read is reported in the log as `MED_10` ("Nom MED du maillage"). |
| `INFO_MED` | integer, optional | `0` | One of `0`, `1`. Only when `equal_to("FORMAT", 'MED')`. `1` adds detailed MED-reader output and timings to the log (the code calls it a "cheat code for debugging", `upstream/code_aster/CodeCommands/lire_maillage.py:95`). Leave at `0` except to debug a reading problem. |
| `PARTITIONNEUR` | text, optional | `'SANS'` | Partitions the mesh for a parallel calculation. One of `'SANS'`, `'PTSCOTCH'`. Only when `equal_to("FORMAT", 'MED')`. `'PTSCOTCH'` in an MPI run returns a distributed `maillage_p` (each process holds part of the mesh). In a sequential run it is ignored with warning `MED_18` (`upstream/code_aster/CodeCommands/lire_maillage.py:119`). Keep `'SANS'` for sequential runs. |
| `CREA_GROUP_COUL` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Only when `equal_to("FORMAT", 'IDEAS')`. `'OUI'` creates one element group and one node group per I-DEAS color, named `COUL_<n>` (`upstream/bibfor/stbtrias/slecol.F90:111`, `snecol.F90:113`). Use it when the I-DEAS file carries colors but no named groups. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `0`, `1`, `2`. `1` prints the mesh summary (numbers of nodes, of elements per type, of groups) to the log; `2` prints more detail. |

## Patterns

### Read a MED mesh (the normal case)

The default format is MED on logical unit 20, so the shortest call reads the MED file that the
`.export` file binds to unit 20. Our fixtures give both keywords explicitly; that is the form
to generate.

Source: `tests/fixtures/solid_static/input/run.comm:16` (also `upstream/astest/cont201e.comm:53`).

```python
MAIL = LIRE_MAILLAGE(FORMAT="MED", UNITE=20)
```

The log then echoes the call with every default filled in, which shows the effective settings
(`tests/fixtures/shell_static/output/run.mess`):

```python
MAIL = LIRE_MAILLAGE(FORMAT='MED',
                     INFO=1,
                     INFO_MED=0,
                     PARTITIONNEUR='SANS',
                     UNITE=20,
                     VERI_MAIL=_F(APLAT=0.001,
                                  VERIF='OUI'))
```

### Pick one mesh from a MED file that holds several

Source: `upstream/astest/zzzz139a.comm:217`.

```python
mail = LIRE_MAILLAGE(FORMAT="MED", NOM_MED="Plaque_Lin", UNITE=20)
```

### Read a Gmsh `.msh` file directly

Converted to the native format on the fly by `PRE_GMSH`. Use it when there is no MED export.
The `.export` file binds unit 19 to the `.msh` file (`F msh ssnp152a.msh D 19`).

Source: `upstream/astest/cont007a.comm:34`.

```python
MA = LIRE_MAILLAGE(FORMAT="GMSH", UNITE=19)
```

### Read without the mesh checks

Source: `upstream/astest/sdnx101e.comm:25`. Only for diagnosing a mesh that fails the checks.

```python
MAIL0 = LIRE_MAILLAGE(FORMAT="MED", VERI_MAIL=_F(VERIF="NON"))
```

## Pitfalls

- **POI1 point groups trigger a warning.** A Gmsh point physical group is stored as a POI1
  element on a node of the plate, which the mesh check reports as warning `MODELISA8_14`
  ("POI1 element included in another"). Our `shell_static` fixture hits this three times and
  ignores it on purpose with `DEBUT(IGNORE_ALARM=("MODELISA8_14",))`; with
  `DEBUT(ERREUR=_F(ALARME="EXCEPTION"))` the warning becomes an error
  (`tests/fixtures/shell_static/input/run.comm:11`).
- **Group names longer than 24 characters are dropped.** The MED reader warns with `MED_7` and
  leaves the group out of the mesh (`upstream/bibcxx/IOManager/MeshReader.cxx:527`, `:545`).
  Any later `GROUP_MA` / `GROUP_NO` that names it then fails. Keep group names at 24
  characters or fewer.
- **Double elements are a modeling error, not just a warning.** Warning `MODELISA4_8` says that
  two elements with the same nodes model the same material twice ("a model twice too heavy or
  twice too stiff") and that `TOUT='OUI'` assignments on such a mesh are unsafe. Fix the mesh
  rather than ignoring the warning.
- **Quadratic meshes with non-conforming mid-side nodes stop the run.** When two edges or
  faces share their corner nodes but not their mid-side nodes, the check raises `MODELISA4_11` /
  `MODELISA4_12` and then the fatal error `MODELISA4_10` (`upstream/bibfor/modelisa/chckma.F90:335`).
  This usually comes from joining separately meshed parts.
- **`PARTITIONNEUR='PTSCOTCH'` and data files.** In a parallel run with a relative mesh path,
  the MED file is copied a second time to a shared directory, and warning `MESH4_6` recommends
  giving the MED file by absolute path through `DEFI_FICHIER` instead
  (`upstream/code_aster/CodeCommands/lire_maillage.py:106`).

## See also

- French reference: U4.21.01 (French text: `en/docs/_src/U4.21.01.fr.md`; translation: `en/docs/U4.21.01.md`)
- Catalog: `en/commands/LIRE_MAILLAGE.json` (generated from `upstream/code_aster/Cata/Commands/lire_maillage.py:87`)
- Implementation: `upstream/code_aster/CodeCommands/lire_maillage.py`; mesh checks
  `upstream/bibfor/modelisa/chckma.F90`
- Next steps: `DEFI_GROUP` (add groups), `MODI_MAILLAGE` (orient boundary elements),
  `AFFE_MODELE`
- Example: `upstream/astest/cont201e.comm` (lines 53)
- Example: `upstream/astest/supv003c.py` (lines 63)
- Example: `upstream/astest/cont200a.comm` (lines 40)
- Example: `tests/fixtures/solid_static/input/run.comm` (line 16)
