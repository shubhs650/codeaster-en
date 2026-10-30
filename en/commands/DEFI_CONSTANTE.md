---
command: DEFI_CONSTANTE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/defi_constante.py:26
doc_fr: U4.31.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3e)
examples: [sslp100a, ssla103a, sslv121a]
---

# DEFI_CONSTANTE — define constant function

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls and upstream test cases. Every behavior claim
> cites its source. Not reviewed by an engineer.

`DEFI_CONSTANTE` turns one real number into a function that returns it wherever it is
evaluated. Some keywords accept only functions: every value of `AFFE_CHAR_MECA_F`
(`upstream/code_aster/Cata/Commands/affe_char_meca_f.py:120`) and every property of
`DEFI_MATERIAU/ELAS_FO` (`upstream/code_aster/Cata/Commands/defi_materiau.py:429`); a constant
one is given with `DEFI_CONSTANTE`. The evaluator returns a constant's value without looking at
the parameter (`upstream/bibfor/utilitai/fointe.F90:190`), so it fits a function of `'X'`,
`'TEMP'` or `'INST'` alike. Checked in our run (`docs/reference-checks/cut-lines/`): supports
given as `DEFI_CONSTANTE(VALE=0.0)` in `AFFE_CHAR_MECA_F` gave the fixture's reaction.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Définir la valeur d'une grandeur invariante» |
| Kind | `OPER` |
| Result | `fonction_sdaster` |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.31.01 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `NOM_PARA`, `VALE`, `PROL_DROITE`, `GAUCHE`, `INTERPOL` |

COMMAND-SET lists `DEFI_CONSTANTE` in the same row as `DEFI_FONCTION`, so the draft copied that
row's keywords. Only `VALE` is a keyword of `DEFI_CONSTANTE`; the parameter name,
interpolation and extrapolation are fixed by the command (see above) and cannot be set.

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `VALE` | real, required | — | *value(s)*. The constant: one real number, in the units the caller expects (`DEFI_CONSTANTE(VALE=0.3)` for a Poisson's ratio, `upstream/astest/sslv121a.comm:32`). Always required. |
| `NOM_RESU` | text, optional | `'TOUTRESU'` | *result name*. A name for the ordinate, stored with the function (`upstream/code_aster/CodeCommands/defi_constante.py:53`). A label only, as for `DEFI_FONCTION`; leave the default. |
| `TITRE` | text, optional | — | *title*. A free title stored with the function. |

## Patterns

### Zero and fixed displacements in a function load

`AFFE_CHAR_MECA_F` takes only functions, so the fixed supports (zero) and the imposed
displacement (2.0) are written as constants beside a `FORMULE` that varies in space. Use this
when one load object mixes position-dependent values with constant ones; a load with only
constant values belongs in `AFFE_CHAR_MECA` with plain numbers.

Source: `upstream/astest/sslp100a.comm:28` (`ZERO = DEFI_CONSTANTE(VALE=0.0)`,
`DEUX = DEFI_CONSTANTE(VALE=2.0)`) and `:48`.

```python
CHBL = AFFE_CHAR_MECA_F(
    MODELE=MO,
    DDL_IMPO=(
        #                    J , N8, N17, N25 :
        _F(GROUP_NO=("N8", "N17", "N25"), DX=ZERO, DY=ZERO),
        _F(GROUP_NO=("N35",), DX=DEUX),
    ),
```

### Constant properties in a temperature-dependent material

`ELAS_FO` requires functions for `E` and `NU`; when the data do not depend on temperature,
each is a constant. The material can then be combined with a temperature field (external state
variable) without inventing a temperature table.

Source: `upstream/astest/ssla103a.comm:26`.

```python
E = DEFI_CONSTANTE(VALE=3.0e10)

NU = DEFI_CONSTANTE(VALE=0.2)

ALPHA = DEFI_CONSTANTE(VALE=1.0e-5)

BETON = DEFI_MATERIAU(
    ELAS_FO=_F(E=E, NU=NU, K_DESSIC=1.66e-5, B_ENDOGE=1.5e-5, ALPHA=ALPHA, TEMP_DEF_ALPHA=20)
)
```

## Pitfalls

- `VALE` takes one number. The catalog declares `VALE` as a single real with no `max`
  (`upstream/code_aster/Cata/Commands/defi_constante.py:33`; one value when `max` is absent, `upstream/code_aster/Cata/Language/SyntaxChecker.py:264`), so a list is refused by the syntax
  check before the command runs. For a value that varies, use `DEFI_FONCTION`.
- A constant carries no parameter name (it is `TOUTPARA`), so it documents nothing about units
  or what the caller evaluates. Name the Python variable after its meaning (`NU`, `ZERO`).
- Where the caller accepts a plain number (`AFFE_CHAR_MECA`, `DEFI_MATERIAU/ELAS`), give the
  number: a constant function there is a type error, because those keywords are typed `R`
  (`upstream/code_aster/Cata/Commands/defi_materiau.py:410` for `ELAS/E`).

## See also

- [`DEFI_FONCTION`](DEFI_FONCTION.md) for values that vary; [`AFFE_CHAR_MECA_F`](AFFE_CHAR_MECA_F.md)
  for loads defined by functions.
- French reference: U4.31.01 (French text: `en/docs/_src/U4.31.01.fr.md`; translation: `en/docs/U4.31.01.md` once task 5.2 lands)
- Catalog: `en/commands/DEFI_CONSTANTE.json` (generated from `upstream/code_aster/Cata/Commands/defi_constante.py:26`)
- Example: `upstream/astest/sslp100a.comm` (lines 28, 48)
- Example: `upstream/astest/ssla103a.comm` (lines 26, 28, 30)
- Example: `upstream/astest/sslv121a.comm` (lines 26, 28, 30, 32, 34, 36)
