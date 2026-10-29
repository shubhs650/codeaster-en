---
command: IMPR_TABLE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/impr_table.py:26
doc_fr: U4.91.03
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3d)
examples: [forma40a, sdls114b, distr01a, ssnv158c, forma20b, cont003a, sslv159d]
---

# IMPR_TABLE — write a table to a file

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the message catalog, upstream test cases and the committed fixture runs. Every
> behavior claim cites its source. Not reviewed by an engineer.

`IMPR_TABLE` writes a table (`table_sdaster`) to a file: the output of `POST_RELEVE_T`,
`POST_ELEM` and the other post-processing commands. Before writing it can keep only some rows
(`FILTRE`), sort them (`TRI`) and keep only some columns (`NOM_PARA`). The default format is a
text table; with `SEPARATEUR=","` it is a CSV-like file that a spreadsheet, `pandas` or `caen`
can read. It is the Tier 1 way to get reaction sums, masses and extracted values out of a run.
It is a Python macro: it creates no object.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Impression du contenu d'une table dans un fichier» |
| Kind | `MACRO` (Python: `upstream/code_aster/MacroCommands/impr_table_ops.py`) |
| Result | none (writes a file) |
| Can reuse its input (`reuse=`) | not applicable |
| French reference | U4.91.03 — from en/doc-ids.yaml (status: proposed) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `TABLE`, `FORMAT`, `TABLEAU`, `ASTER`, `SEPARATEUR`, `UNITE` |

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `TABLE` | `table_sdaster`, required | — | *table*. The table to write: from `POST_RELEVE_T`, `POST_ELEM`, `CREA_TABLE`, a modal result's parameters, …. |
| `FORMAT` | text, optional | `'TABLEAU'` | *file format*. One of `'TABLEAU'`, `'ASTER'`, `'TABLEAU_CROISE'`, `'AGRAF'`, `'XMGRACE'`, `'NUMPY'`. `'TABLEAU'` (default): text columns, the Tier 1 choice; with `SEPARATEUR=","` it gives a CSV-like file (`tests/fixtures/solid_static/input/run.comm:59`). `'ASTER'`: text framed by `#DEBUT_TABLE`/`#FIN_TABLE` with a line of column types, readable back by `LIRE_TABLE` (`upstream/code_aster/Objects/table_py.py:222`). `'TABLEAU_CROISE'`: a table of 3 parameters printed as a two-way grid. `'AGRAF'`: `TABLEAU` for the AGRAF plotter. `'XMGRACE'`: a plot (Grace file or image, see `PILOTE`). `'NUMPY'`: a binary `.npy` array, numeric columns only (`table_py.py:160`). |
| `PILOTE` | text, optional | `''` | Output driver; PNG/JPEG/PDF are not available in every xmgrace installation. One of `''`, `'POSTSCRIPT'`, `'EPS'`, `'MIF'`, `'SVG'`, `'PNM'`, `'PNG'`, `'JPEG'`, `'PDF'`, `'INTERACTIF'`, `'INTERACTIF_BG'`. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'`: the output type. `''` writes a Grace project file; `'PNG'`, `'PDF'`, `'SVG'`, … write an image (`upstream/astest/cont003a.comm:137`). |
| `UNITE` | `UnitDefault`, optional | `29` | *logical unit*. Logical unit of the file (fort.N) to write to. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'`: logical unit of the plot file (default 29). |
| `UNITE` | `UnitDefault`, optional | `8` | *logical unit*. Logical unit of the file (fort.N) to write to. Only when `not equal_to("FORMAT", 'XMGRACE')`. Logical unit of the file (default 8, the run's `.resu` file). The file is opened in append mode, so several `IMPR_TABLE` calls to one unit add up in one file (`upstream/code_aster/Objects/table_py.py:87`, `:150`). Declare the unit in the `.export` to keep the file. |
| `FILTRE` | factor keyword, optional, repeatable | — | Keep only the rows that pass a test on one column. Several occurrences combine with AND (`upstream/code_aster/MacroCommands/impr_table_ops.py:88`–`:96`). Each filter is recorded in the table title. |
| `FILTRE / NOM_PARA` | text, required | — | *parameter name*. The column to test, for example `'INST'` (`upstream/astest/forma40a.comm:187`). A name the table does not have stops the run. |
| `FILTRE / CRIT_COMP` | text, optional | `'EQ'` | One of `'EQ'`, `'LT'`, `'GT'`, `'NE'`, `'LE'`, `'GE'`, `'VIDE'`, `'NON_VIDE'`, `'MAXI'`, `'MAXI_ABS'`, `'MINI'`, `'MINI_ABS'`. The test: `'EQ'`, `'NE'`, `'LT'`, `'GT'`, `'LE'`, `'GE'` against `VALE…`; `'VIDE'`/`'NON_VIDE'` empty or filled entry; `'MAXI'`, `'MINI'`, `'MAXI_ABS'`, `'MINI_ABS'` keep the row(s) holding the extreme value of the column (`upstream/code_aster/Objects/table_py.py:860`–`:915`). |
| `FILTRE / VALE` | real, optional, list | — | *value(s)*. Only when `is_in("CRIT_COMP", ('EQ','NE','GT','LT','GE','LE'))`. Real value(s) to compare with. |
| `FILTRE / VALE_I` | integer, optional, list | — | Only when `is_in("CRIT_COMP", ('EQ','NE','GT','LT','GE','LE'))`. Integer value(s) to compare with, for example a `NUME_ORDRE`. |
| `FILTRE / VALE_C` | complex, optional, list | — | *complex values*. Only when `is_in("CRIT_COMP", ('EQ','NE','GT','LT','GE','LE'))`. Complex value(s) to compare with. |
| `FILTRE / VALE_K` | text, optional, list | — | Only when `is_in("CRIT_COMP", ('EQ','NE','GT','LT','GE','LE'))`. Text value(s) to compare with, for example an `INTITULE` or a node name; leading and trailing blanks are ignored (`upstream/code_aster/Objects/table_py.py:828`). |
| `FILTRE / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `is_in("CRIT_COMP", ('EQ','NE'))`. For `'EQ'`/`'NE'` on reals: relative or absolute tolerance. |
| `FILTRE / PRECISION` | real, optional | `0.001` | *tolerance*. Only when `is_in("CRIT_COMP", ('EQ','NE'))`. The tolerance of the real comparison. |
| `TRI` | factor keyword, optional | — | Sort the rows (one occurrence) (`upstream/code_aster/MacroCommands/impr_table_ops.py:106`). |
| `TRI / NOM_PARA` | text, required, list | — | *parameter name*. The sort keys, first key first (`upstream/astest/sdls114b.comm:189`). |
| `TRI / ORDRE` | text, optional | `'CROISSANT'` | One of `'CROISSANT'`, `'DECROISSANT'`. Increasing (`'CROISSANT'`) or decreasing (`'DECROISSANT'`). |
| `PAGINATION` | text, optional, list | — | Columns by which the printout is split into blocks, one per value (for example one block per `INST`) (`upstream/astest/ssnv158c.comm:176`). They must be among the printed columns, or warning `TABLE0_8`. |
| `FORMAT_R` | text, optional | `'E12.5'` | Fortran edit descriptor for real values, converted to a Python format (`upstream/code_aster/MacroCommands/impr_table_ops.py:153`). Default `E12.5` (5 significant decimals, as in the fixture tables); use `1PE24.12` or similar for more digits (`upstream/astest/forma20b.comm:206`). |
| `NOM_PARA` | text, optional, list | — | *parameter name*. The columns to print, in this order, for example `("COOR_X", "DZ")`. A name the table does not have gives warning `TABLE0_7` (`upstream/code_aster/MacroCommands/impr_table_ops.py:116`). Columns that are empty after filtering are dropped (`:119`). |
| `IMPR_FONCTION` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. `'OUI'`: also print the functions whose names appear in the `FONCTION`/`FONCTION_C` columns of the table (`upstream/code_aster/MacroCommands/impr_table_ops.py:169`). |
| `DEBUT_TABLE` | text, optional | — | Header written before the table (default: a line of dashes). Only when `equal_to("FORMAT", 'TABLEAU')`. |
| `FIN_TABLE` | text, optional | `''` | Text written after the table. Only when `equal_to("FORMAT", 'TABLEAU')`. |
| `SEPARATEUR` | text, optional | `' '` | *column separator*. Column separator of the table (e.g. ' ', ';', ...). Only when `equal_to("FORMAT", 'TABLEAU')`. Use `','` for a file that spreadsheets and `pandas` read as CSV (our fixtures). With a separator that holds no blank, header names are stripped but text entries keep their padding (`upstream/code_aster/Objects/table_py.py:229`). |
| `COMMENTAIRE` | text, optional | `'#'` | Character that tells the function plotter that the line can be ignored. Only when `equal_to("FORMAT", 'TABLEAU')`. Starts the title and header lines (`#` by default), so that plotting tools skip them. |
| `COMM_PARA` | text, optional | `''` | Character used to comment out the line of column labels. Only when `equal_to("FORMAT", 'TABLEAU')`. Put before the line of column names, to comment it out as well. |
| `DEBUT_LIGNE` | text, optional | `''` | Line-start character. Only when `equal_to("FORMAT", 'TABLEAU')`. |
| `FIN_LIGNE` | text, optional | `'\n'` | Line-end character. Only when `equal_to("FORMAT", 'TABLEAU')`. |
| `LEGENDE` | text, optional | — | Legend of the function. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `STYLE` | integer, optional | — | Style of the line that represents the function. Range: ≥ 0. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `COULEUR` | integer, optional | — | Color of the function. Range: ≥ 0. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `MARQUEUR` | integer, optional | — | Type of the marker of the function. Range: ≥ 0. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `FREQ_MARQUEUR` | integer, optional | `0` | How often the marker of the function is drawn. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `BORNE_X` | real, optional, list of up to 2, at least 2 | — | Range of the abscissas. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `BORNE_Y` | real, optional, list of up to 2, at least 2 | — | Range of the ordinates. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `ECHELLE_X` | text, optional | `'LIN'` | Scale type of the abscissas. One of `'LIN'`, `'LOG'`. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `ECHELLE_Y` | text, optional | `'LIN'` | Scale type of the ordinates. One of `'LIN'`, `'LOG'`. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `GRILLE_X` | real, optional | — | Spacing of the vertical grid lines. Range: ≥ 0.0. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `GRILLE_Y` | real, optional | — | Spacing of the horizontal grid lines. Range: ≥ 0.0. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `LEGENDE_X` | text, optional | — | Label of the abscissa axis. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `LEGENDE_Y` | text, optional | — | Label of the ordinate axis. Only when `equal_to("FORMAT", 'XMGRACE')`. `FORMAT='XMGRACE'` only: plot setting. |
| `TITRE` | text, optional | — | *title*. Title written above the table, before the title stored in the table (`upstream/code_aster/MacroCommands/impr_table_ops.py:85`). |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `2` prints the name of the table being written. |



## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- when `is_in("CRIT_COMP", ('EQ','NE','GT','LT','GE','LE'))`: exactly one of `VALE`, `VALE_I`, `VALE_K`, `VALE_C` must be given (`UN_PARMI`).

## What the solver does

In order (`upstream/code_aster/MacroCommands/impr_table_ops.py`): apply each `FILTRE` (`:88`), sort
(`:106`), check the `NOM_PARA` columns (`:114`), drop empty columns (`:119`), set the format
options, write (`:166`). The file is opened in append mode for every format
(`upstream/code_aster/Objects/table_py.py:87`–`:92`).

A `TABLEAU` file from our solid fixture (`tests/fixtures/solid_static/output/tables/reactions.csv`):

```text
#
#--------------------------------------------------------------------------------
##ASTER 17.04.22 CONCEPT 0000002a CALCULE LE 29/10/2026 A 02:15:32 DE TYPE
INTITULE,RESU,NOM_CHAM,NUME_ORDRE,INST,DX,DY,DZ
REAC_BASE       ,00000007,REAC_NODA       ,           1, 0.00000E+00, 3.89164E+03,-1.77693E-10, 1.27073E-10
```

The first three lines are the default header (`DEBUT_TABLE`) and the table title; the fourth
is the column names.

## Patterns

### Tier 1 table as CSV

Source: `tests/fixtures/solid_static/input/run.comm:59`.

```python
IMPR_TABLE(TABLE=REAC, FORMAT="TABLEAU", SEPARATEUR=",", UNITE=30)
```

### Rows of one time, two columns, as a plot

Source: `upstream/astest/forma40a.comm:187`.

```python
IMPR_TABLE(
    TABLE=DEFO,
    FORMAT="XMGRACE",
    UNITE=29,
    FILTRE=_F(NOM_PARA="INST", CRIT_COMP="EQ", VALE=2.0),
    NOM_PARA=("COOR_X", "DZ"),
)
```

### Sorted rows

Source: `upstream/astest/sdls114b.comm:189`.

```python
IMPR_TABLE(TABLE=KT2, TRI=_F(NOM_PARA=("ABSC_CURV", "INST"), ORDRE="CROISSANT"))
```

### One block per time step

Source: `upstream/astest/ssnv158c.comm:176`.

```python
IMPR_TABLE(
    TABLE=DEP,
    TRI=(_F(NOM_PARA="INST", ORDRE="CROISSANT"),),
    PAGINATION="INST",
    NOM_PARA=("INST", "DY", "DX"),
)
```

### Table that `LIRE_TABLE` can read back

Source: `upstream/astest/distr01a.comm:104`.

```python
IMPR_TABLE(TABLE=VMIS, UNITE=38, FORMAT="ASTER", NOM_PARA=("ABSC_CURV", "VMIS"))
```

### More digits

Inside a loop in the source (indentation kept).

Source: `upstream/astest/forma20b.comm:206`.

```python
    IMPR_TABLE(TABLE=ENER[num_calc], FORMAT_R="1PE24.12")
```

## Pitfalls

- **Five significant digits by default.** `FORMAT_R='E12.5'` prints `3.89164E+03`, not the
  computed `3891.6428…`. Checks against tight tolerances should use `TEST_TABLE` or
  `TEST_RESU` in the run, or set a wider `FORMAT_R`.
- **Files accumulate.** Every format appends (`upstream/code_aster/Objects/table_py.py:87`); two
  tables written to one unit end up in one file, one after the other, each with its header.
  Only `XMGRACE` warns (`TABLE0_6`). Use one unit per table when a program reads the file.
- **Internal names in table entries.** Columns that name objects (`RESU` in a `POST_RELEVE_T` table,
  `LIEU` in `POST_ELEM`) hold internal names such as `00000007`, not the Python variable name
  (fixture above). Text entries are padded to 16 characters even with `SEPARATEUR=","`; strip
  them when reading.
- **Header lines start with `#`.** Readers must skip lines starting with `COMMENTAIRE` (`#`)
  before the column names; the line of names itself is not commented unless `COMM_PARA` is set.
- **`NOM_PARA` names that do not exist are only a warning** (`TABLE0_7`); the column is just
  missing. A `FILTRE` on a missing column stops the run.
- **`NUMPY` needs numeric columns.** A table with text columns stops the run with `TABLE0_5`,
  whose message text (about a line format) does not match the cause
  (`upstream/code_aster/Objects/table_py.py:164`).

## See also

- French reference: U4.91.03 (translation: `en/docs/U4.91.03.md` once task 5.x lands)
- Catalog: `en/commands/IMPR_TABLE.json` (generated from `upstream/code_aster/Cata/Commands/impr_table.py:26`)
- Implementation: `upstream/code_aster/MacroCommands/impr_table_ops.py`;
  `upstream/code_aster/Objects/table_py.py` (`Table.Impr`, `ReprTable`)
- Before: [POST_RELEVE_T](POST_RELEVE_T.md), [POST_ELEM](POST_ELEM.md)
- Related: `TEST_TABLE` (check a table value in the run), `LIRE_TABLE` (read a table back),
  [IMPR_RESU](IMPR_RESU.md) (fields)
- Example: `tests/fixtures/solid_static/input/run.comm` (line 59)
- Example: `tests/fixtures/modal/input/run.comm` (line 31)
- Example: `upstream/astest/forma40a.comm` (line 187)
