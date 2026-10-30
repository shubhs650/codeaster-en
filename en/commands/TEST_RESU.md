---
command: TEST_RESU
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/test_resu.py:26
doc_fr: U4.92.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3d)
examples: [hslv304a, hpla310a, cont002b, sdnd105e, zzzz169a]
---

# TEST_RESU — check computed values

> **Assisted reference.** Written in session from the pinned catalog, the shared keyword
> definitions, the solver source and the Python reporting code it calls, the message catalog,
> upstream test cases and the committed fixture runs. Every behavior claim cites its source.
> Not reviewed by an engineer.
> Citations such as "U4.44.01 §3.8" are sections of the official French documents (v16
> edition, `en/docs/_src/`); where one disagrees with the pinned catalog or solver source, the code wins.

`TEST_RESU` checks values computed in the run against expected values and prints an `OK` or
`NOOK` line for each. Each occurrence picks one value: a component of a field at a node or
element point, a global sum or extremum of a field (`TYPE_TEST`), a result parameter such as a
frequency (`PARA`), or a mesh count. It always runs a non-regression test against `VALE_CALC`
(the value an earlier run of this code version gave, tolerance 1e-6) and, when `REFERENCE` is
given, a second test against an independent `VALE_REFE` (tolerance `PRECISION`, 0.1 % by
default). Upstream test cases and our fixtures end with it, and a `NOOK` line marks the whole
job `NOOK_TEST_RESU` (`upstream/run_aster/status.py:225`). For a study it is the way to
assert, inside the run, that a result matches a hand calculation.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Extraction d'une valeur d'une structure de donnée et comparaison à une valeur de référence» |
| Kind | `PROC` (Fortran operator 23, `upstream/bibfor/op/op0023.F90`) |
| Result | none (prints the test report) |
| Can reuse its input (`reuse=`) | not applicable |
| French reference | U4.92.01 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `RESU`, `VALE_CALC`, `VALE_REFE`, `REFERENCE`, `PRECISION` |

## Keywords

The value keywords (`VALE_CALC`, `VALE_REFE`, `REFERENCE`, `PRECISION`, `TOLE_MACHINE`,
`CRITERE`, `ORDRE_GRANDEUR`, `LEGENDE`, …) are shared by every factor keyword
(`upstream/code_aster/Cata/Commons/c_test_reference.py:26`); their rows repeat the same text.

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `CHAM_NO` | factor keyword, optional, repeatable | — | Test one value of a nodal field object (for example from `CREA_CHAMP`) (`upstream/astest/hslv304a.comm:175`). |
| `CHAM_NO / CHAM_GD` | `cham_no_sdaster`, required | — | *field (physical quantity)*. The nodal field. |
| `CHAM_NO / GROUP_NO` | node group, optional | — | *node group*. The node, as a group of exactly one node (U4.92.01 §4.3); a larger group stops with `CALCULEL5_20` (`upstream/bibfor/test/trchno.F90:316`, `utnono.F90`). |
| `CHAM_NO / NOM_CMP` | text, optional | — | *component name*. The component, for example `'DX'`. |
| `CHAM_NO / VALE_CALC` | real, optional, list | — | *computed value (regression)*. Only when `True`. The value this code version computed, copied from an earlier run: the non-regression test compares the new value with it, at `TOLE_MACHINE` (`upstream/code_aster/Supervis/TestResult.py:71`). Always give it; with `REFERENCE`, the same occurrence also tests against `VALE_REFE`. Our fixtures copy it with all digits from the first run (`tests/fixtures/solid_static/input/run.comm:81`). |
| `CHAM_NO / ORDRE_GRANDEUR` | real, optional | — | Only when `True and exists("VALE_CALC") and abs(VALE_CALC if type(VALE_CALC) not in (list, tuple) else VALE_CALC[0]) < 1.e-16`. Only when `VALE_CALC` is zero (below 1e-16): the scale of the quantity, so that the non-regression test becomes absolute with tolerance `TOLE_MACHINE` × `ORDRE_GRANDEUR` (`upstream/code_aster/Supervis/TestResult.py:104`; `upstream/bibfor/test/tresu_ordgrd.F90:51`). Without it a zero non-regression value is not tested (`TEST0_11`, `TEST0_12`) (`upstream/astest/cont002b.comm:117`). |
| `CHAM_NO / LEGENDE` | text, optional | — | Only when `True`. A label printed in the `LEGENDE` column of the test report, to find the line in the `.mess` file (`tests/fixtures/solid_static/output/run.mess:416`). Give each test a unique one. |
| `CHAM_NO / VALE_CALC_I` | integer, optional, list | — | Only when `True`. Integer computed value, for integer quantities (counts, integer fields). |
| `CHAM_NO / VALE_CALC_C` | complex, optional, list | — | Only when `True`. Complex computed value, for complex fields (harmonic results). |
| `CHAM_NO / VALE_ABS` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Only when `True`. `'OUI'`: compare the absolute values of the reference and computed values, ignoring the sign (U4.92.01 §4.7). |
| `CHAM_NO / TYPE_TEST` | text, optional | — | One of `'SOMM_ABS'`, `'SOMM'`, `'MAX'`, `'MIN'`. Only when `True`. Test a global quantity of the whole field instead of one value: sum (`'SOMM'`), sum of absolute values (`'SOMM_ABS'`), maximum (`'MAX'`) or minimum (`'MIN'`) over all components given and all nodes or points. A `GROUP_NO` or `GROUP_MA` given with it is ignored, with warning `CALCULEL6_96` (`upstream/bibfor/test/trresu.F90:317`). Our solid fixture uses `'SOMM'` for the reaction sum (`tests/fixtures/solid_static/input/run.comm:78`). |
| `CHAM_NO / TOLE_MACHINE` | real, optional | `1e-06` | Only when `True`. Relative tolerance of the non-regression test (`VALE_CALC`), default 1e-6 (`upstream/bibfor/test/tresu_tole.F90:55`). Raise it only for values known to vary between platforms. |
| `CHAM_NO / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `True`. `'RELATIF'`: error ≤ tolerance × |expected|; `'ABSOLU'`: error ≤ tolerance (× `ORDRE_GRANDEUR` for the non-regression test) (`upstream/code_aster/Supervis/TestResult.py:94`–`:105`). Applies to both tests of the occurrence. |
| `CHAM_NO / VALE_REFE` | real, optional, list | — | *reference value*. Only when `True and exists("REFERENCE")`. The independent reference value: analytical solution, another code, experiment. Compared with the computed value at `PRECISION`. |
| `CHAM_NO / PRECISION` | real, optional | `0.001` | *tolerance*. Only when `True and exists("REFERENCE")`. Tolerance of the reference test, relative by default (1e-3 = 0.1 %). Set it to the accuracy you expect of the model against the reference, for example `1.0e-2` for a coarse mesh (`tests/fixtures/shell_static/input/run.comm:98`). |
| `CHAM_NO / VALE_REFE_I` | integer, optional, list | — | Only when `True and exists("REFERENCE")`. Integer reference value. |
| `CHAM_NO / VALE_REFE_C` | complex, optional, list | — | Only when `True and exists("REFERENCE")`. Complex reference value. |
| `CHAM_NO / REFERENCE` | text, optional | — | *reference type*. One of `'ANALYTIQUE'`, `'SOURCE_EXTERNE'`, `'AUTRE_ASTER'`, `'NON_DEFINI'`. Only when `True`. Where `VALE_REFE` comes from: `'ANALYTIQUE'` (closed-form solution), `'SOURCE_EXTERNE'` (literature, another code, test), `'AUTRE_ASTER'` (another code_aster computation), `'NON_DEFINI'`. Its presence turns on the reference test; the name is printed in the `REFERENCE` column (`tests/fixtures/solid_static/output/run.mess:417`). |
| `CARTE` | factor keyword, optional, repeatable | — | Test one value of a constant-per-element map (`carte`). Not used in Tier 1. |
| `CARTE / CHAM_GD` | `carte_sdaster`, required | — | *field (physical quantity)*. The map. |
| `CARTE / GROUP_MA` | element group, optional | — | *element group*. The element, as a group of one element. |
| `CARTE / NOM_CMP` | text, required | — | *component name*. The component. |
| `CARTE / VALE_CALC` | real, optional | — | *computed value (regression)*. Only when `True`. The value this code version computed, copied from an earlier run: the non-regression test compares the new value with it, at `TOLE_MACHINE` (`upstream/code_aster/Supervis/TestResult.py:71`). Always give it; with `REFERENCE`, the same occurrence also tests against `VALE_REFE`. Our fixtures copy it with all digits from the first run (`tests/fixtures/solid_static/input/run.comm:81`). |
| `CARTE / ORDRE_GRANDEUR` | real, optional | — | Only when `True and exists("VALE_CALC") and abs(VALE_CALC if type(VALE_CALC) not in (list, tuple) else VALE_CALC[0]) < 1.e-16`. Only when `VALE_CALC` is zero (below 1e-16): the scale of the quantity, so that the non-regression test becomes absolute with tolerance `TOLE_MACHINE` × `ORDRE_GRANDEUR` (`upstream/code_aster/Supervis/TestResult.py:104`; `upstream/bibfor/test/tresu_ordgrd.F90:51`). Without it a zero non-regression value is not tested (`TEST0_11`, `TEST0_12`) (`upstream/astest/cont002b.comm:117`). |
| `CARTE / LEGENDE` | text, optional | — | Only when `True`. A label printed in the `LEGENDE` column of the test report, to find the line in the `.mess` file (`tests/fixtures/solid_static/output/run.mess:416`). Give each test a unique one. |
| `CARTE / VALE_CALC_I` | integer, optional | — | Only when `True`. Integer computed value, for integer quantities (counts, integer fields). |
| `CARTE / VALE_CALC_C` | complex, optional | — | Only when `True`. Complex computed value, for complex fields (harmonic results). |
| `CARTE / TOLE_MACHINE` | real, optional | `1e-06` | Only when `True`. Relative tolerance of the non-regression test (`VALE_CALC`), default 1e-6 (`upstream/bibfor/test/tresu_tole.F90:55`). Raise it only for values known to vary between platforms. |
| `CARTE / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `True`. `'RELATIF'`: error ≤ tolerance × |expected|; `'ABSOLU'`: error ≤ tolerance (× `ORDRE_GRANDEUR` for the non-regression test) (`upstream/code_aster/Supervis/TestResult.py:94`–`:105`). Applies to both tests of the occurrence. |
| `CARTE / VALE_REFE` | real, optional | — | *reference value*. Only when `True and exists("REFERENCE")`. The independent reference value: analytical solution, another code, experiment. Compared with the computed value at `PRECISION`. |
| `CARTE / PRECISION` | real, optional | `0.001` | *tolerance*. Only when `True and exists("REFERENCE")`. Tolerance of the reference test, relative by default (1e-3 = 0.1 %). Set it to the accuracy you expect of the model against the reference, for example `1.0e-2` for a coarse mesh (`tests/fixtures/shell_static/input/run.comm:98`). |
| `CARTE / VALE_REFE_I` | integer, optional | — | Only when `True and exists("REFERENCE")`. Integer reference value. |
| `CARTE / VALE_REFE_C` | complex, optional | — | Only when `True and exists("REFERENCE")`. Complex reference value. |
| `CARTE / REFERENCE` | text, optional | — | *reference type*. One of `'ANALYTIQUE'`, `'SOURCE_EXTERNE'`, `'AUTRE_ASTER'`, `'NON_DEFINI'`. Only when `True`. Where `VALE_REFE` comes from: `'ANALYTIQUE'` (closed-form solution), `'SOURCE_EXTERNE'` (literature, another code, test), `'AUTRE_ASTER'` (another code_aster computation), `'NON_DEFINI'`. Its presence turns on the reference test; the name is printed in the `REFERENCE` column (`tests/fixtures/solid_static/output/run.mess:417`). |
| `CHAM_ELEM` | factor keyword, optional, repeatable | — | Test one value of an element field object (`upstream/astest/hpla310a.comm:330`). |
| `CHAM_ELEM / CHAM_GD` | `cham_elem`, required | — | *field (physical quantity)*. The element field. |
| `CHAM_ELEM / GROUP_MA` | element group, optional | — | *element group*. The element, as a group of one element. |
| `CHAM_ELEM / POINT` | integer, optional | — | *reference point*. For `ELGA` fields: the Gauss point number in the element. |
| `CHAM_ELEM / SOUS_POINT` | integer, optional | — | For fields with sub-points (shell layers, beam fibers): the sub-point number. |
| `CHAM_ELEM / GROUP_NO` | node group, optional | — | *node group*. For `ELNO` fields: the node of the element, as a group of one node. |
| `CHAM_ELEM / NOM_CMP` | text, optional | — | *component name*. The component, for example `'SIYY'`. |
| `CHAM_ELEM / VALE_CALC` | real, optional, list | — | *computed value (regression)*. Only when `True`. The value this code version computed, copied from an earlier run: the non-regression test compares the new value with it, at `TOLE_MACHINE` (`upstream/code_aster/Supervis/TestResult.py:71`). Always give it; with `REFERENCE`, the same occurrence also tests against `VALE_REFE`. Our fixtures copy it with all digits from the first run (`tests/fixtures/solid_static/input/run.comm:81`). |
| `CHAM_ELEM / ORDRE_GRANDEUR` | real, optional | — | Only when `True and exists("VALE_CALC") and abs(VALE_CALC if type(VALE_CALC) not in (list, tuple) else VALE_CALC[0]) < 1.e-16`. Only when `VALE_CALC` is zero (below 1e-16): the scale of the quantity, so that the non-regression test becomes absolute with tolerance `TOLE_MACHINE` × `ORDRE_GRANDEUR` (`upstream/code_aster/Supervis/TestResult.py:104`; `upstream/bibfor/test/tresu_ordgrd.F90:51`). Without it a zero non-regression value is not tested (`TEST0_11`, `TEST0_12`) (`upstream/astest/cont002b.comm:117`). |
| `CHAM_ELEM / LEGENDE` | text, optional | — | Only when `True`. A label printed in the `LEGENDE` column of the test report, to find the line in the `.mess` file (`tests/fixtures/solid_static/output/run.mess:416`). Give each test a unique one. |
| `CHAM_ELEM / VALE_CALC_I` | integer, optional, list | — | Only when `True`. Integer computed value, for integer quantities (counts, integer fields). |
| `CHAM_ELEM / VALE_CALC_C` | complex, optional, list | — | Only when `True`. Complex computed value, for complex fields (harmonic results). |
| `CHAM_ELEM / VALE_ABS` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Only when `True`. `'OUI'`: compare the absolute values of the reference and computed values, ignoring the sign (U4.92.01 §4.7). |
| `CHAM_ELEM / TYPE_TEST` | text, optional | — | One of `'SOMM_ABS'`, `'SOMM'`, `'MAX'`, `'MIN'`. Only when `True`. Test a global quantity of the whole field instead of one value: sum (`'SOMM'`), sum of absolute values (`'SOMM_ABS'`), maximum (`'MAX'`) or minimum (`'MIN'`) over all components given and all nodes or points. A `GROUP_NO` or `GROUP_MA` given with it is ignored, with warning `CALCULEL6_96` (`upstream/bibfor/test/trresu.F90:317`). Our solid fixture uses `'SOMM'` for the reaction sum (`tests/fixtures/solid_static/input/run.comm:78`). |
| `CHAM_ELEM / TOLE_MACHINE` | real, optional | `1e-06` | Only when `True`. Relative tolerance of the non-regression test (`VALE_CALC`), default 1e-6 (`upstream/bibfor/test/tresu_tole.F90:55`). Raise it only for values known to vary between platforms. |
| `CHAM_ELEM / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `True`. `'RELATIF'`: error ≤ tolerance × |expected|; `'ABSOLU'`: error ≤ tolerance (× `ORDRE_GRANDEUR` for the non-regression test) (`upstream/code_aster/Supervis/TestResult.py:94`–`:105`). Applies to both tests of the occurrence. |
| `CHAM_ELEM / VALE_REFE` | real, optional, list | — | *reference value*. Only when `True and exists("REFERENCE")`. The independent reference value: analytical solution, another code, experiment. Compared with the computed value at `PRECISION`. |
| `CHAM_ELEM / PRECISION` | real, optional | `0.001` | *tolerance*. Only when `True and exists("REFERENCE")`. Tolerance of the reference test, relative by default (1e-3 = 0.1 %). Set it to the accuracy you expect of the model against the reference, for example `1.0e-2` for a coarse mesh (`tests/fixtures/shell_static/input/run.comm:98`). |
| `CHAM_ELEM / VALE_REFE_I` | integer, optional, list | — | Only when `True and exists("REFERENCE")`. Integer reference value. |
| `CHAM_ELEM / VALE_REFE_C` | complex, optional, list | — | Only when `True and exists("REFERENCE")`. Complex reference value. |
| `CHAM_ELEM / REFERENCE` | text, optional | — | *reference type*. One of `'ANALYTIQUE'`, `'SOURCE_EXTERNE'`, `'AUTRE_ASTER'`, `'NON_DEFINI'`. Only when `True`. Where `VALE_REFE` comes from: `'ANALYTIQUE'` (closed-form solution), `'SOURCE_EXTERNE'` (literature, another code, test), `'AUTRE_ASTER'` (another code_aster computation), `'NON_DEFINI'`. Its presence turns on the reference test; the name is printed in the `REFERENCE` column (`tests/fixtures/solid_static/output/run.mess:417`). |
| `RESU` | factor keyword, optional, repeatable | — | Test one value stored in a result: a component of a field at a node, an element point or over the whole field (`TYPE_TEST`), or a result parameter such as a frequency (`PARA`). The Tier 1 form (`tests/fixtures/shell_static/input/run.comm:86`). |
| `RESU / RESULTAT` | `resultat_sdaster`, required | — | *result*. The result. |
| `RESU / NUME_ORDRE` | integer, optional | — | *step index*. The step, by index. Exactly one step must be selected (`upstream/bibfor/test/trresu.F90:200`). |
| `RESU / INST` | real, optional | — | *time step (pseudo-time)*. The step, by time. Matched with the second value of `TOLE_MACHINE` and `CRITERE`, if given (`upstream/bibfor/calculel/trprec.F90:19`). |
| `RESU / FREQ` | real, optional | — | *frequency*. The step, by frequency. |
| `RESU / NUME_MODE` | integer, optional | — | The step, by mode number (modal result). |
| `RESU / NOEUD_CMP` | text, optional, list of up to 2, at least 2 | — | The static mode, by node and component. Not used in Tier 1. |
| `RESU / NOM_CAS` | text, optional | — | The load case, by name. Not used in Tier 1. |
| `RESU / ANGLE` | real, optional | — | The Fourier angle. Not used in Tier 1. |
| `RESU / PARA` | text, optional | — | Test a result parameter instead of a field value, for example `'FREQ'` of a mode (`tests/fixtures/modal/input/run.comm:49`). Its type must match the value given (`CALCULEL6_95`). |
| `RESU / NOM_CHAM` | text, optional | — | *field name*. One of `'ENDO_ELNO'`, `'VARI_ELNO'`, `'UT02_ELGA'`, `'UT10_NOEU'`, `'VARI_ELGA'`, `'HHO_VITE'`, `'COEF_H'`, `'EPMQ_NOEU'`, `'QIZ2_ELEM'`, `'EPFP_ELGA'`, `'VITE_VENT'`, `'SOUR_ELGA'`, … (227 values; see the .json). The field of the result, for example `'DEPL'`, `'SIEQ_NOEU'`, `'REAC_NODA'`. It must have been computed. |
| `RESU / NOM_CMP` | text, optional | — | *component name*. The component, for example `'DZ'` or `'VMIS'`. |
| `RESU / NOM_VARI` | text, optional | — | For internal variable fields (`VARI_*`): the variable by name instead of `V1`, `V2`, … (`upstream/astest/sdnd105e.comm:255`). |
| `RESU / GROUP_MA` | element group, optional | — | *element group*. For element fields (`ELNO`, `ELGA`, `ELEM`): the element, as a group of exactly one element (`TEST0_20`, `upstream/bibfor/test/trresu.F90:509`). Required for those fields (`MODELISA7_89`), forbidden for nodal fields (`MODELISA7_90`, `:290`). |
| `RESU / GROUP_NO` | node group, optional, list | — | *node group*. The node, as a group of exactly one node. A group with more nodes is fatal (`CALCULEL5_20`). For `ELNO` fields: the node of the element given by `GROUP_MA`. |
| `RESU / POINT` | integer, optional | — | *reference point*. For `ELGA` fields: the Gauss point number in the element. Forbidden for nodal fields (`CALCULEL6_97`, `upstream/bibfor/test/trresu.F90:456`). |
| `RESU / SOUS_POINT` | integer, optional | — | For fields with sub-points: the sub-point number. |
| `RESU / VALE_CALC` | real, optional, list | — | *computed value (regression)*. Only when `True`. The value this code version computed, copied from an earlier run: the non-regression test compares the new value with it, at `TOLE_MACHINE` (`upstream/code_aster/Supervis/TestResult.py:71`). Always give it; with `REFERENCE`, the same occurrence also tests against `VALE_REFE`. Our fixtures copy it with all digits from the first run (`tests/fixtures/solid_static/input/run.comm:81`). |
| `RESU / ORDRE_GRANDEUR` | real, optional | — | Only when `True and exists("VALE_CALC") and abs(VALE_CALC if type(VALE_CALC) not in (list, tuple) else VALE_CALC[0]) < 1.e-16`. Only when `VALE_CALC` is zero (below 1e-16): the scale of the quantity, so that the non-regression test becomes absolute with tolerance `TOLE_MACHINE` × `ORDRE_GRANDEUR` (`upstream/code_aster/Supervis/TestResult.py:104`; `upstream/bibfor/test/tresu_ordgrd.F90:51`). Without it a zero non-regression value is not tested (`TEST0_11`, `TEST0_12`) (`upstream/astest/cont002b.comm:117`). |
| `RESU / LEGENDE` | text, optional | — | Only when `True`. A label printed in the `LEGENDE` column of the test report, to find the line in the `.mess` file (`tests/fixtures/solid_static/output/run.mess:416`). Give each test a unique one. |
| `RESU / VALE_CALC_I` | integer, optional, list | — | Only when `True`. Integer computed value, for integer quantities (counts, integer fields). |
| `RESU / VALE_CALC_C` | complex, optional, list | — | Only when `True`. Complex computed value, for complex fields (harmonic results). |
| `RESU / VALE_ABS` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Only when `True`. `'OUI'`: compare the absolute values of the reference and computed values, ignoring the sign (U4.92.01 §4.7). |
| `RESU / TYPE_TEST` | text, optional | — | One of `'SOMM_ABS'`, `'SOMM'`, `'MAX'`, `'MIN'`. Only when `True`. Test a global quantity of the whole field instead of one value: sum (`'SOMM'`), sum of absolute values (`'SOMM_ABS'`), maximum (`'MAX'`) or minimum (`'MIN'`) over all components given and all nodes or points. A `GROUP_NO` or `GROUP_MA` given with it is ignored, with warning `CALCULEL6_96` (`upstream/bibfor/test/trresu.F90:317`). Our solid fixture uses `'SOMM'` for the reaction sum (`tests/fixtures/solid_static/input/run.comm:78`). |
| `RESU / TOLE_MACHINE` | real, optional, list of up to 2 | — | Only when `True`. One or two values. The first is the relative tolerance of the non-regression test (default 1e-6); the second is the tolerance used to find `INST`/`FREQ` in the result (default the first) (`upstream/bibfor/test/tresu_tole.F90:30`–`:34`). |
| `RESU / CRITERE` | text, optional, list of up to 2 | — | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `True`. One or two values: the comparison type of the tests (`'RELATIF'`/`'ABSOLU'`) and, second, of the `INST`/`FREQ` search (`upstream/bibfor/calculel/trprec.F90:19`). Default `'RELATIF'`. |
| `RESU / VALE_REFE` | real, optional, list | — | *reference value*. Only when `True and exists("REFERENCE")`. The independent reference value: analytical solution, another code, experiment. Compared with the computed value at `PRECISION`. |
| `RESU / PRECISION` | real, optional | `0.001` | *tolerance*. Only when `True and exists("REFERENCE")`. Tolerance of the reference test, relative by default (1e-3 = 0.1 %). Set it to the accuracy you expect of the model against the reference, for example `1.0e-2` for a coarse mesh (`tests/fixtures/shell_static/input/run.comm:98`). |
| `RESU / VALE_REFE_I` | integer, optional, list | — | Only when `True and exists("REFERENCE")`. Integer reference value. |
| `RESU / VALE_REFE_C` | complex, optional, list | — | Only when `True and exists("REFERENCE")`. Complex reference value. |
| `RESU / REFERENCE` | text, optional | — | *reference type*. One of `'ANALYTIQUE'`, `'SOURCE_EXTERNE'`, `'AUTRE_ASTER'`, `'NON_DEFINI'`. Only when `True`. Where `VALE_REFE` comes from: `'ANALYTIQUE'` (closed-form solution), `'SOURCE_EXTERNE'` (literature, another code, test), `'AUTRE_ASTER'` (another code_aster computation), `'NON_DEFINI'`. Its presence turns on the reference test; the name is printed in the `REFERENCE` column (`tests/fixtures/solid_static/output/run.mess:417`). |
| `GENE` | factor keyword, optional, repeatable | — | Test one value of a generalized (modal-basis) result. Not used in Tier 1. |
| `GENE / RESU_GENE` | `vect_asse_gene` or `tran_gene` or `mode_gene` or `harm_gene`, required | — | The generalized result or vector. |
| `GENE / NUME_CMP_GENE` | integer, required | — | Only when `is_type("RESU_GENE") == vect_asse_gene`; or `is_type("RESU_GENE") == harm_gene`; or `is_type("RESU_GENE") == tran_gene`. The generalized component (modal coordinate) number. |
| `GENE / NOM_CHAM` | text, optional | — | *field name*. One of `'ACCE'`, `'ACCE_ABSOLU'`, `'COEF_H'`, `'COMPORTEMENT'`, `'COMPORTHER'`, `'CONT_ELEM'`, `'CONT_NOEU'`, `'DEGE_ELGA'`, `'DEGE_ELNO'`, `'DEGE_NOEU'`, `'DEPL'`, `'DEPL_ABSOLU'`, … (233 values; see the .json). Only when `is_type("RESU_GENE") == mode_gene`. The field of a modal generalized result. |
| `GENE / NUME_CMP_GENE` | integer, optional | — | Only when `is_type("RESU_GENE") == mode_gene`. The generalized component number, for a `mode_gene`. |
| `GENE / PARA` | text, optional | — | Only when `is_type("RESU_GENE") == mode_gene`. A parameter of a `mode_gene` (for example `'FREQ'`) instead of a field value. |
| `GENE / NUME_ORDRE` | integer, optional | — | *step index*. Only when `is_type("RESU_GENE") == mode_gene`; or `is_type("RESU_GENE") == harm_gene`; or `is_type("RESU_GENE") == tran_gene`. The step, by index. |
| `GENE / NUME_MODE` | integer, optional | — | Only when `is_type("RESU_GENE") == mode_gene`. The mode number. |
| `GENE / FREQ` | real, optional | — | *frequency*. Only when `is_type("RESU_GENE") == mode_gene`; or `is_type("RESU_GENE") == harm_gene`. The step, by frequency. |
| `GENE / NOM_CHAM` | text, required | — | *field name*. One of `'ACCE'`, `'ACCE_ABSOLU'`, `'COEF_H'`, `'COMPORTEMENT'`, `'COMPORTHER'`, `'CONT_ELEM'`, `'CONT_NOEU'`, `'DEGE_ELGA'`, `'DEGE_ELNO'`, `'DEGE_NOEU'`, `'DEPL'`, `'DEPL_ABSOLU'`, … (233 values; see the .json). Only when `is_type("RESU_GENE") == harm_gene`; or `is_type("RESU_GENE") == tran_gene`. The field (`'DEPL'`, `'VITE'`, `'ACCE'`) of a harmonic or transient generalized result. |
| `GENE / INST` | real, optional | — | *time step (pseudo-time)*. Only when `is_type("RESU_GENE") == tran_gene`. The time of a transient generalized result. |
| `GENE / VALE_CALC` | real, optional, list | — | *computed value (regression)*. Only when `True`. The value this code version computed, copied from an earlier run: the non-regression test compares the new value with it, at `TOLE_MACHINE` (`upstream/code_aster/Supervis/TestResult.py:71`). Always give it; with `REFERENCE`, the same occurrence also tests against `VALE_REFE`. Our fixtures copy it with all digits from the first run (`tests/fixtures/solid_static/input/run.comm:81`). |
| `GENE / ORDRE_GRANDEUR` | real, optional | — | Only when `True and exists("VALE_CALC") and abs(VALE_CALC if type(VALE_CALC) not in (list, tuple) else VALE_CALC[0]) < 1.e-16`. Only when `VALE_CALC` is zero (below 1e-16): the scale of the quantity, so that the non-regression test becomes absolute with tolerance `TOLE_MACHINE` × `ORDRE_GRANDEUR` (`upstream/code_aster/Supervis/TestResult.py:104`; `upstream/bibfor/test/tresu_ordgrd.F90:51`). Without it a zero non-regression value is not tested (`TEST0_11`, `TEST0_12`) (`upstream/astest/cont002b.comm:117`). |
| `GENE / LEGENDE` | text, optional | — | Only when `True`. A label printed in the `LEGENDE` column of the test report, to find the line in the `.mess` file (`tests/fixtures/solid_static/output/run.mess:416`). Give each test a unique one. |
| `GENE / VALE_CALC_I` | integer, optional, list | — | Only when `True`. Integer computed value, for integer quantities (counts, integer fields). |
| `GENE / VALE_CALC_C` | complex, optional, list | — | Only when `True`. Complex computed value, for complex fields (harmonic results). |
| `GENE / VALE_ABS` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Only when `True`. `'OUI'`: compare the absolute values of the reference and computed values, ignoring the sign (U4.92.01 §4.7). |
| `GENE / TOLE_MACHINE` | real, optional, list of up to 2 | — | Only when `True`. Relative tolerance of the non-regression test (`VALE_CALC`), default 1e-6 (`upstream/bibfor/test/tresu_tole.F90:55`). Raise it only for values known to vary between platforms. As for `RESU`, a second value sets the search tolerance. |
| `GENE / CRITERE` | text, optional, list of up to 2 | — | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `True`. `'RELATIF'`: error ≤ tolerance × |expected|; `'ABSOLU'`: error ≤ tolerance (× `ORDRE_GRANDEUR` for the non-regression test) (`upstream/code_aster/Supervis/TestResult.py:94`–`:105`). Applies to both tests of the occurrence. As for `RESU`, a second value sets the search criterion. |
| `GENE / VALE_REFE` | real, optional, list | — | *reference value*. Only when `True and exists("REFERENCE")`. The independent reference value: analytical solution, another code, experiment. Compared with the computed value at `PRECISION`. |
| `GENE / PRECISION` | real, optional | `0.001` | *tolerance*. Only when `True and exists("REFERENCE")`. Tolerance of the reference test, relative by default (1e-3 = 0.1 %). Set it to the accuracy you expect of the model against the reference, for example `1.0e-2` for a coarse mesh (`tests/fixtures/shell_static/input/run.comm:98`). |
| `GENE / VALE_REFE_I` | integer, optional, list | — | Only when `True and exists("REFERENCE")`. Integer reference value. |
| `GENE / VALE_REFE_C` | complex, optional, list | — | Only when `True and exists("REFERENCE")`. Complex reference value. |
| `GENE / REFERENCE` | text, optional | — | *reference type*. One of `'ANALYTIQUE'`, `'SOURCE_EXTERNE'`, `'AUTRE_ASTER'`, `'NON_DEFINI'`. Only when `True`. Where `VALE_REFE` comes from: `'ANALYTIQUE'` (closed-form solution), `'SOURCE_EXTERNE'` (literature, another code, test), `'AUTRE_ASTER'` (another code_aster computation), `'NON_DEFINI'`. Its presence turns on the reference test; the name is printed in the `REFERENCE` column (`tests/fixtures/solid_static/output/run.mess:417`). |
| `OBJET` | factor keyword, optional, repeatable | — | Test a checksum of an internal memory object by name, for developers (`upstream/astest/fdlv108a.comm:116`). Not used in Tier 1. |
| `OBJET / NOM` | text, required | — | The internal object name (24 characters). |
| `OBJET / VALE_CALC` | real, optional | — | *computed value (regression)*. Only when `True`. The value this code version computed, copied from an earlier run: the non-regression test compares the new value with it, at `TOLE_MACHINE` (`upstream/code_aster/Supervis/TestResult.py:71`). Always give it; with `REFERENCE`, the same occurrence also tests against `VALE_REFE`. Our fixtures copy it with all digits from the first run (`tests/fixtures/solid_static/input/run.comm:81`). |
| `OBJET / ORDRE_GRANDEUR` | real, optional | — | Only when `True and exists("VALE_CALC") and abs(VALE_CALC if type(VALE_CALC) not in (list, tuple) else VALE_CALC[0]) < 1.e-16`. Only when `VALE_CALC` is zero (below 1e-16): the scale of the quantity, so that the non-regression test becomes absolute with tolerance `TOLE_MACHINE` × `ORDRE_GRANDEUR` (`upstream/code_aster/Supervis/TestResult.py:104`; `upstream/bibfor/test/tresu_ordgrd.F90:51`). Without it a zero non-regression value is not tested (`TEST0_11`, `TEST0_12`) (`upstream/astest/cont002b.comm:117`). |
| `OBJET / LEGENDE` | text, optional | — | Only when `True`. A label printed in the `LEGENDE` column of the test report, to find the line in the `.mess` file (`tests/fixtures/solid_static/output/run.mess:416`). Give each test a unique one. |
| `OBJET / VALE_CALC_I` | integer, optional | — | Only when `True`. Integer computed value, for integer quantities (counts, integer fields). |
| `OBJET / VALE_ABS` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Only when `True`. `'OUI'`: compare the absolute values of the reference and computed values, ignoring the sign (U4.92.01 §4.7). |
| `OBJET / TOLE_MACHINE` | real, optional | `1e-06` | Only when `True`. Relative tolerance of the non-regression test (`VALE_CALC`), default 1e-6 (`upstream/bibfor/test/tresu_tole.F90:55`). Raise it only for values known to vary between platforms. |
| `OBJET / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `True`. `'RELATIF'`: error ≤ tolerance × |expected|; `'ABSOLU'`: error ≤ tolerance (× `ORDRE_GRANDEUR` for the non-regression test) (`upstream/code_aster/Supervis/TestResult.py:94`–`:105`). Applies to both tests of the occurrence. |
| `OBJET / VALE_REFE` | real, optional | — | *reference value*. Only when `True and exists("REFERENCE")`. The independent reference value: analytical solution, another code, experiment. Compared with the computed value at `PRECISION`. |
| `OBJET / PRECISION` | real, optional | `0.001` | *tolerance*. Only when `True and exists("REFERENCE")`. Tolerance of the reference test, relative by default (1e-3 = 0.1 %). Set it to the accuracy you expect of the model against the reference, for example `1.0e-2` for a coarse mesh (`tests/fixtures/shell_static/input/run.comm:98`). |
| `OBJET / VALE_REFE_I` | integer, optional | — | Only when `True and exists("REFERENCE")`. Integer reference value. |
| `OBJET / REFERENCE` | text, optional | — | *reference type*. One of `'ANALYTIQUE'`, `'SOURCE_EXTERNE'`, `'AUTRE_ASTER'`, `'NON_DEFINI'`. Only when `True`. Where `VALE_REFE` comes from: `'ANALYTIQUE'` (closed-form solution), `'SOURCE_EXTERNE'` (literature, another code, test), `'AUTRE_ASTER'` (another code_aster computation), `'NON_DEFINI'`. Its presence turns on the reference test; the name is printed in the `REFERENCE` column (`tests/fixtures/solid_static/output/run.mess:417`). |
| `MAILLAGE` | factor keyword, optional, repeatable | — | *mesh*. Test a count on a mesh: number of elements, nodes, groups, or elements or nodes in a group (`upstream/astest/zzzz169a.comm:89`). Useful to check a mesh read or built by `CREA_MAILLAGE`/`DEFI_GROUP`. |
| `MAILLAGE / MAILLAGE` | `maillage_sdaster`, required | — | *mesh*. The mesh. |
| `MAILLAGE / CARA` | text, required | — | One of `'NB_MAILLE'`, `'NB_NOEUD'`, `'NB_GROUP_MA'`, `'NB_GROUP_NO'`, `'NB_MA_GROUP_MA'`, `'NB_NO_GROUP_NO'`. What to count: `'NB_MAILLE'` elements, `'NB_NOEUD'` nodes, `'NB_GROUP_MA'`/`'NB_GROUP_NO'` groups, `'NB_MA_GROUP_MA'` elements in `NOM_GROUP_MA`, `'NB_NO_GROUP_NO'` nodes in `NOM_GROUP_NO`. |
| `MAILLAGE / NOM_GROUP_MA` | element group, optional | — | The element group, for `CARA='NB_MA_GROUP_MA'`. |
| `MAILLAGE / NOM_GROUP_NO` | node group, optional | — | The node group, for `CARA='NB_NO_GROUP_NO'`. |
| `MAILLAGE / VALE_CALC` | real, optional | — | *computed value (regression)*. Only when `True`. The value this code version computed, copied from an earlier run: the non-regression test compares the new value with it, at `TOLE_MACHINE` (`upstream/code_aster/Supervis/TestResult.py:71`). Always give it; with `REFERENCE`, the same occurrence also tests against `VALE_REFE`. Our fixtures copy it with all digits from the first run (`tests/fixtures/solid_static/input/run.comm:81`). |
| `MAILLAGE / ORDRE_GRANDEUR` | real, optional | — | Only when `True and exists("VALE_CALC") and abs(VALE_CALC if type(VALE_CALC) not in (list, tuple) else VALE_CALC[0]) < 1.e-16`. Only when `VALE_CALC` is zero (below 1e-16): the scale of the quantity, so that the non-regression test becomes absolute with tolerance `TOLE_MACHINE` × `ORDRE_GRANDEUR` (`upstream/code_aster/Supervis/TestResult.py:104`; `upstream/bibfor/test/tresu_ordgrd.F90:51`). Without it a zero non-regression value is not tested (`TEST0_11`, `TEST0_12`) (`upstream/astest/cont002b.comm:117`). |
| `MAILLAGE / LEGENDE` | text, optional | — | Only when `True`. A label printed in the `LEGENDE` column of the test report, to find the line in the `.mess` file (`tests/fixtures/solid_static/output/run.mess:416`). Give each test a unique one. |
| `MAILLAGE / VALE_CALC_I` | integer, optional | — | Only when `True`. Integer computed value, for integer quantities (counts, integer fields). |
| `MAILLAGE / VALE_ABS` | text, optional | `'NON'` | One of `'OUI'`, `'NON'`. Only when `True`. `'OUI'`: compare the absolute values of the reference and computed values, ignoring the sign (U4.92.01 §4.7). |
| `MAILLAGE / TYPE_TEST` | text, optional | — | One of `'SOMM_ABS'`, `'SOMM'`, `'MAX'`, `'MIN'`. Only when `True`. Test a global quantity of the whole field instead of one value: sum (`'SOMM'`), sum of absolute values (`'SOMM_ABS'`), maximum (`'MAX'`) or minimum (`'MIN'`) over all components given and all nodes or points. A `GROUP_NO` or `GROUP_MA` given with it is ignored, with warning `CALCULEL6_96` (`upstream/bibfor/test/trresu.F90:317`). Our solid fixture uses `'SOMM'` for the reaction sum (`tests/fixtures/solid_static/input/run.comm:78`). |
| `MAILLAGE / TOLE_MACHINE` | real, optional | `1e-06` | Only when `True`. Relative tolerance of the non-regression test (`VALE_CALC`), default 1e-6 (`upstream/bibfor/test/tresu_tole.F90:55`). Raise it only for values known to vary between platforms. |
| `MAILLAGE / CRITERE` | text, optional | `'RELATIF'` | *tolerance type*. One of `'RELATIF'`, `'ABSOLU'`. Only when `True`. `'RELATIF'`: error ≤ tolerance × |expected|; `'ABSOLU'`: error ≤ tolerance (× `ORDRE_GRANDEUR` for the non-regression test) (`upstream/code_aster/Supervis/TestResult.py:94`–`:105`). Applies to both tests of the occurrence. |
| `MAILLAGE / VALE_REFE` | real, optional | — | *reference value*. Only when `True and exists("REFERENCE")`. The independent reference value: analytical solution, another code, experiment. Compared with the computed value at `PRECISION`. |
| `MAILLAGE / PRECISION` | real, optional | `0.001` | *tolerance*. Only when `True and exists("REFERENCE")`. Tolerance of the reference test, relative by default (1e-3 = 0.1 %). Set it to the accuracy you expect of the model against the reference, for example `1.0e-2` for a coarse mesh (`tests/fixtures/shell_static/input/run.comm:98`). |
| `MAILLAGE / VALE_REFE_I` | integer, optional | — | Only when `True and exists("REFERENCE")`. Integer reference value. |
| `MAILLAGE / REFERENCE` | text, optional | — | *reference type*. One of `'ANALYTIQUE'`, `'SOURCE_EXTERNE'`, `'AUTRE_ASTER'`, `'NON_DEFINI'`. Only when `True`. Where `VALE_REFE` comes from: `'ANALYTIQUE'` (closed-form solution), `'SOURCE_EXTERNE'` (literature, another code, test), `'AUTRE_ASTER'` (another code_aster computation), `'NON_DEFINI'`. Its presence turns on the reference test; the name is printed in the `REFERENCE` column (`tests/fixtures/solid_static/output/run.mess:417`). |
| `TEST_NAN` | text, optional | — | One of `'OUI'`, `'NON'`. `'OUI'`: check that floating-point traps work, by computing with a NaN; for platform verification (`upstream/bibfor/op/op0023.F90:51`). Not used in Tier 1. |



## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at least one of `CHAM_NO`, `CHAM_ELEM`, `CARTE`, `RESU`, `GENE`, `OBJET`, `TEST_NAN`, `MAILLAGE` must be given (`AU_MOINS_UN`).
- `CHAM_NO`: if `GROUP_NO` is given, `NOM_CMP` must all be given (`PRESENT_PRESENT`).
- when `True`: exactly one of `VALE_CALC`, `VALE_CALC_I`, `VALE_CALC_C` must be given (`UN_PARMI`).
- when `exists("REFERENCE")`: exactly one of `VALE_REFE`, `VALE_REFE_I`, `VALE_REFE_C` must be given (`UN_PARMI`).
- `CHAM_ELEM`: at most one of `GROUP_NO`, `POINT` may be given (`EXCLUS`).
- `CHAM_ELEM`: if `GROUP_NO` is given, `NOM_CMP` must all be given (`PRESENT_PRESENT`).
- `CHAM_ELEM`: if `POINT` is given, `NOM_CMP` must all be given (`PRESENT_PRESENT`).
- `RESU`: exactly one of `NUME_ORDRE`, `INST`, `FREQ`, `NUME_MODE`, `NOEUD_CMP`, `NOM_CAS`, `ANGLE` must be given (`UN_PARMI`).
- `RESU`: exactly one of `NOM_CHAM`, `PARA` must be given (`UN_PARMI`).
- `RESU`: if `PARA` is given, none of `GROUP_MA`, `GROUP_NO`, `POINT`, `NOM_CMP`, `NOM_VARI` may be given (`PRESENT_ABSENT`).
- `RESU`: at most one of `GROUP_NO`, `POINT` may be given (`EXCLUS`).
- `RESU`: at most one of `NOM_CMP`, `NOM_VARI` may be given (`EXCLUS`).
- when `is_type("RESU_GENE") == mode_gene`: exactly one of `NUME_ORDRE`, `FREQ`, `NUME_MODE` must be given (`UN_PARMI`).
- when `is_type("RESU_GENE") == mode_gene`: exactly one of `NOM_CHAM`, `PARA` must be given (`UN_PARMI`).
- when `is_type("RESU_GENE") == mode_gene`: if `NOM_CHAM` is given, `NUME_CMP_GENE` must all be given (`PRESENT_PRESENT`).
- when `is_type("RESU_GENE") == harm_gene`: exactly one of `NUME_ORDRE`, `FREQ` must be given (`UN_PARMI`).
- when `is_type("RESU_GENE") == tran_gene`: exactly one of `NUME_ORDRE`, `INST` must be given (`UN_PARMI`).
- when `True`: exactly one of `VALE_CALC`, `VALE_CALC_I` must be given (`UN_PARMI`).
- when `exists("REFERENCE")`: exactly one of `VALE_REFE`, `VALE_REFE_I` must be given (`UN_PARMI`).

## What the report says

Each occurrence prints a header naming what was tested, then one line per test
(`upstream/code_aster/Supervis/TestResult.py:71`). From our shell fixture
(`tests/fixtures/shell_static/output/run.mess:472`):

```text
 ---- RESULTAT         NUME_ORDRE       NOM_CHAM         NOM_CMP          GROUP_NO
      00000008         1                EFGE_NOEU        MXX              CENTER
      REFERENCE        LEGENDE          VALE_REFE           VALE_CALC           ERREUR           TOLE
 OK   NON_REGRESSION   MXX_CENTER       -479.645314641979   -479.645314641979   0.0%             9.999999999999999E-05%
 OK   ANALYTIQUE       MXX_CENTER       -478.864            -479.645314641979    1.631600E-01%   3.0%
```

| Column | Meaning |
|---|---|
| first | `OK`, `NOOK`, `SKIP` (test not run, for example a zero `VALE_CALC` without `ORDRE_GRANDEUR`), or `-` (non-regression line ignored in a validation test case) |
| `REFERENCE` | `NON_REGRESSION` for the `VALE_CALC` test, else the `REFERENCE` value |
| `LEGENDE` | the `LEGENDE` keyword, or the component name |
| `VALE_REFE` | the expected value (`VALE_CALC` on the non-regression line) |
| `VALE_CALC` | the value computed in this run |
| `ERREUR`, `TOLE` | error and tolerance, in % for relative tests |

The test passes when |computed − expected| ≤ tolerance × |expected| (relative) or ≤ tolerance
× `ORDRE_GRANDEUR` (absolute) (`upstream/code_aster/Supervis/TestResult.py:94`–`:105`). The
non-regression line is printed as `-` and not judged when the `.export` declares the case a
validation test (`testlist … validation`), with message `TEST0_19` (`TestResult.py:47`–`:53`,
`:141`–`:152`).

## Patterns

### Displacement at a node against an analytical value

Source: `tests/fixtures/shell_static/input/run.comm:86`.

```python
TEST_RESU(
    RESU=(
        # Centre deflection: w = alpha q a^4 / D, alpha = 0.00406235 (NU=0.3), D = E t^3/(12(1-NU^2)).
        _F(
            NUME_ORDRE=1,
            RESULTAT=RESU,
            NOM_CHAM="DEPL",
            GROUP_NO="CENTER",
            NOM_CMP="DZ",
            REFERENCE="ANALYTIQUE",
            VALE_REFE=-2.11242,
            VALE_CALC=-2.112263828055923,
            PRECISION=1.0e-2,
            LEGENDE="W_CENTER",
        ),
    )
)
```

(The source continues with more occurrences; only the first is shown.)

### Reaction sum over a whole field

`TYPE_TEST="SOMM"` adds the component over all nodes; on `REAC_NODA` that is the support
reaction, which balances the applied load.

Source: `tests/fixtures/solid_static/input/run.comm:71`.

```python
TEST_RESU(
    RESU=(
        _F(
            NUME_ORDRE=1,
            RESULTAT=RESU,
            NOM_CHAM="REAC_NODA",
            NOM_CMP="DX",
            TYPE_TEST="SOMM",
            REFERENCE="ANALYTIQUE",
            VALE_REFE=3891.64,
            VALE_CALC=3891.6428187786923,
            PRECISION=1.0e-3,
            LEGENDE="REAC_DX_SUM",
        ),
    )
)
```

### Natural frequency of a mode

Source: `tests/fixtures/modal/input/run.comm:49`.

```python
TEST_RESU(
    RESU=(
        _F(
            NUME_ORDRE=1,
            PARA="FREQ",
            RESULTAT=MODES,
            REFERENCE="ANALYTIQUE",
            VALE_REFE=52.2198,
            VALE_CALC=52.3396441683678,
            PRECISION=2.0e-2,
            LEGENDE="F1_BENDING_Z1",
        ),
    )
)
```

(Only the first occurrence is shown.)

### Stress at an element node of a field object

Source: `upstream/astest/hpla310a.comm:330`.

```python
TEST_RESU(
    CHAM_ELEM=_F(
        GROUP_NO="N4526",
        NOM_CMP="SIYY",
        GROUP_MA="M2787",
        CHAM_GD=SIGM1A,
        REFERENCE="ANALYTIQUE",
        VALE_REFE=4.584029e6,
        VALE_CALC=4585015.40061,
        PRECISION=1.0e-3,
    )
)
```

### A value that should be zero

Absolute test with an order of magnitude; without `ORDRE_GRANDEUR` the zero non-regression
value would not be tested.

Source: `upstream/astest/cont002b.comm:108`.

```python
        _F(
            INST=1.0,
            TYPE_TEST="MIN",
            RESULTAT=RES,
            REFERENCE="ANALYTIQUE",
            NOM_CHAM="DEPL",
            LEGENDE="LAGS_C",
            NOM_CMP="LAGS_C",
            CRITERE="ABSOLU",
            ORDRE_GRANDEUR=1e-6,
            VALE_REFE=0.0,
            VALE_CALC=0.0,
        ),
```

### Mesh count

Source: `upstream/astest/zzzz169a.comm:89`.

```python
TEST_RESU(
    MAILLAGE=_F(
        MAILLAGE=mesh_glob_1,
        CARA="NB_MAILLE",
        REFERENCE="ANALYTIQUE",
        CRITERE="ABSOLU",
        VALE_REFE_I=50,
        VALE_CALC_I=50,
    )
)
```

## Pitfalls

- **`VALE_CALC` is not a reference.** It is the value this code gave before, so it only detects
  change. Physical correctness comes from `REFERENCE` + `VALE_REFE` with a meaningful
  `PRECISION`. Copy `VALE_CALC` with all digits from a first run (our fixtures note this in
  their headers).
- **One node, one element.** `GROUP_NO` must hold exactly one node (`CALCULEL5_20`) and
  `GROUP_MA` exactly one element (`TEST0_20`). Make single-entity groups with `DEFI_GROUP`.
- **Location keywords follow the field.** Element fields need `GROUP_MA` (`MODELISA7_89`), nodal
  fields refuse it (`MODELISA7_90`) and refuse `POINT` (`CALCULEL6_97`).
- **`TYPE_TEST` ignores groups.** With `TYPE_TEST`, `GROUP_NO`/`GROUP_MA` are ignored and the
  whole field is used, with warning `CALCULEL6_96`. Our solid fixture relies on this: the sum of
  `REAC_NODA` over all nodes is the base reaction because the field is zero elsewhere
  (comment at `tests/fixtures/solid_static/input/run.comm:68`).
- **Zero expected values.** A zero `VALE_CALC` without `ORDRE_GRANDEUR` is skipped (`SKIP`,
  `TEST0_12`); a relative reference test against zero can never pass. Use
  `CRITERE='ABSOLU'` and `ORDRE_GRANDEUR`.
- **Signs follow code_aster's conventions.** Reactions oppose the load; shell moments sign
  with the local axes. Our fixtures record the sign found in the first run next to each
  reference (`tests/fixtures/shell_static/input/run.comm:103`).
- **Exactly one step.** The selection keywords must pick one stored step, else
  `CALCULEL6_94` or an assertion (`upstream/bibfor/test/trresu.F90:195`–`:200`).

## See also

- French reference: U4.92.01 (French text: `en/docs/_src/U4.92.01.fr.md`; translation: `en/docs/U4.92.01.md`)
- Catalog: `en/commands/TEST_RESU.json` (generated from `upstream/code_aster/Cata/Commands/test_resu.py:26`)
- Implementation: `upstream/bibfor/op/op0023.F90`; `upstream/bibfor/test/` (`trresu.F90` for
  `RESU`, `trchno.F90`, `trchel.F90`, `trcart.F90`, `trgene.F90`, `trjeve.F90`, `trmail.F90`);
  report lines from `upstream/code_aster/Supervis/TestResult.py`
- Related: `TEST_TABLE` (check a table value), `TEST_FONCTION` (check a function value)
- Before: [CALC_CHAMP](CALC_CHAMP.md), [MECA_STATIQUE](MECA_STATIQUE.md), [CREA_CHAMP](CREA_CHAMP.md)
- Example: `tests/fixtures/shell_static/input/run.comm` (line 86)
- Example: `tests/fixtures/solid_static/input/run.comm` (line 71)
- Example: `tests/fixtures/modal/input/run.comm` (line 49)
