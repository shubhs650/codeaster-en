---
command: DEFI_MATERIAU
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/defi_materiau.py:51
doc_fr: U4.43.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3b)
examples: [zzzz503g, zzzz505d, forma12b, zzzz118a, hplv102a, zzzz239a]
---

# DEFI_MATERIAU — define material

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.

`DEFI_MATERIAU` defines one material (`mater_sdaster`): a named set of parameter groups, one
factor keyword per behavior (`ELAS` for linear elasticity, `THER` for heat conduction,
`ECRO_LINE` for linear hardening, and about 250 more). It does not say where the material is:
`AFFE_MATERIAU` assigns it to element groups, and the analysis command reads from it only the
groups it needs (a linear static run reads `ELAS`; a modal run also needs `RHO`). The decisions
it encodes are which behaviors the material has, whether each parameter is a constant (`ELAS`)
or a function of temperature or another variable (`ELAS_FO`), and the unit system: the solver
has no units, so `E`, `RHO` and the mesh coordinates must use one consistent set. Our fixtures
use mm, N, MPa and tonne, so steel is `E=210000.0` (MPa) and `RHO=7.85e-9` (t/mm³)
(`tests/fixtures/modal/input/run.comm:2`). Tier 1 needs `ELAS` and `ELAS_FO` only; the other
behaviors are listed under [Other keywords](#other-keywords).

| Fact | Value |
|---|---|
| Catalog description (fr) | «Définition des paramètres décrivant le comportement d un matériau» |
| Kind | `MACRO` |
| Result | `mater_sdaster` |
| Can reuse its input (`reuse=`) | yes (the object given in `MATER`); catalog `reentrant='f:MATER'` |
| French reference | U4.43.01 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `ELAS`, `NU`, `RHO`, `ALPHA`, `ELAS_FO` |

## Keywords

Top-level simple keywords and the key factor keywords from docs/COMMAND-SET.md are expanded
below; the other factor keywords are listed under [Other keywords](#other-keywords).

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MATER` | `mater_sdaster`, optional | — | *material*. An existing material to enrich: the call adds the behaviors it defines to that material, written `M = DEFI_MATERIAU(reuse=M, MATER=M, ...)` (`upstream/astest/zzzz239a.comm:82`). Use it to add a behavior to a material defined elsewhere, for example in an included file. A behavior group that the material already has cannot be given twice (the `EXCLUS` rules below). |
| `ELAS` | factor keyword, optional | — | *linear elastic*. Isotropic linear elasticity with constant parameters (catalog translation: "Linear isotropic elasticity"). The usual choice. Give exactly one pair of elastic constants: (`E`, `NU`), (`K`, `MU`) or (`CELE_P`, `CELE_S`) with `RHO`; the command converts the other two pairs to `E` and `NU` and prints the result (`MATERIAL1_12`, `upstream/code_aster/CodeCommands/defi_materiau.py:233`). |
| `ELAS / E` | real, optional | — | *Young's modulus*. Range: ≥ 0.0. In the unit of stress of the model (MPa with lengths in mm, Pa with m). Given with `NU`. |
| `ELAS / NU` | real, optional | — | *Poisson's ratio*. Range: ≥ -1.0, ≤ 0.5. Dimensionless. |
| `ELAS / K` | real, optional | — | Bulk modulus. Range: ≥ 0.0. Given with `MU`; converted with E = 9 K MU / (3 K + MU) and NU = (3 K − 2 MU) / (6 K + 2 MU) (`upstream/code_aster/CodeCommands/defi_materiau.py:266`). Must be > 0 (`MATERIAL1_14`). Use it when the data sheet gives K and G, as in `upstream/astest/comp012d.comm:54`. |
| `ELAS / MU` | real, optional | — | Shear modulus. Range: ≥ 0.0. Given with `K`. Must be > 0 (`MATERIAL1_14`). |
| `ELAS / CELE_P` | real, optional | — | Compression (P) wave speed (célérité). Range: ≥ 0.0. Given with `CELE_S` and `RHO`; converted with E = RHO CELE_S² (3 CELE_P² − 4 CELE_S²) / (CELE_P² − CELE_S²) and NU = (CELE_P² − 2 CELE_S²) / (2 (CELE_P² − CELE_S²)) (`upstream/code_aster/CodeCommands/defi_materiau.py:274`). CELE_P / CELE_S must be at least 2/√3 (`MATERIAL1_15`). Use it for soils characterized by measured wave speeds. |
| `ELAS / CELE_S` | real, optional | — | Shear (S) wave speed. Range: ≥ 0.0. Must be > 0 (`MATERIAL1_14`). |
| `ELAS / RHO` | real, optional | — | *density*. Mass per unit volume, in the mass unit of the model (t/mm³ with mm, N, MPa; kg/m³ with m, N, Pa). Needed for every mass-dependent calculation: mass matrices (modal and dynamic analyses), gravity and rotation loads, `POST_ELEM/MASS_INER`. Our `modal` fixture gives it (`tests/fixtures/modal/input/run.comm:22`); the static fixtures do not need it. |
| `ELAS / ALPHA` | real, optional | — | *thermal expansion coefficient*. In 1/°C (or 1/K). Gives a thermal strain ALPHA × (T − T_ref) wherever `AFFE_MATERIAU/AFFE_VARC` supplies a temperature T and its reference value T_ref (`VALE_REF`) (`upstream/bibfor/modelisa/verift.F90:264`). With no temperature assigned there is no thermal strain (`upstream/bibfor/modelisa/verift.F90:104`), so `ALPHA` alone changes nothing. |
| `ELAS / AMOR_ALPHA` | real, optional | — | *stiffness-proportional damping coefficient*. Rayleigh damping: the element damping matrix is AMOR_ALPHA × K + AMOR_BETA × M (`upstream/bibfor/te/te0121.F90:174`; catalog translation "Stiffness damping"). Note the order: in code_aster the **alpha** coefficient multiplies the **stiffness**, the reverse of the common textbook notation C = αM + βK. For a damping ratio ξ at two frequencies f1 and f2, `upstream/astest/forma12b.comm:44` uses AMOR_ALPHA = ξ / (π (f1 + f2)). Used by dynamic analyses that build a damping matrix (`AMOR_MECA`). |
| `ELAS / AMOR_BETA` | real, optional | — | *mass-proportional damping coefficient*. Multiplies the mass matrix in the Rayleigh damping matrix (catalog translation "Mass damping"); `upstream/astest/forma12b.comm:46` uses AMOR_BETA = 4 π ξ f1 f2 / (f1 + f2). |
| `ELAS / AMOR_HYST` | real, optional | — | Hysteretic damping coefficient (catalog translation "Hysteretic damping"). TODO(verify) how it enters the complex stiffness of harmonic analyses, against U4.43.01. |
| `ELAS / K_DESSIC` | real, optional | `0.0` | Drying-shrinkage coefficient ("retrait de dessiccation", `upstream/bibfor/comport/nmisot.F90:266`). Concrete only; leave at 0. TODO(verify) the strain law and the drying variable (`SECH`) against U4.43.01. |
| `ELAS / B_ENDOGE` | real, optional | `0.0` | Autogenous-shrinkage coefficient ("retrait endogène", same source). Concrete only; leave at 0. TODO(verify) the strain law and the hydration variable (`HYDR`) against U4.43.01. |
| `ELAS / LONG_CARA` | real, optional | — | *characteristic length*. Range: ≥ 0.0. Read with `COEF_AMOR` by the absorbing-boundary elements (`*_ABSO` modelings, `upstream/bibfor/te/te0553.F90:64`). Not used in Tier 1. TODO(verify) its role against U4.43.01. |
| `ELAS / COEF_AMOR` | real, optional | `1.0` | *damping coefficient*. Read by the absorbing-boundary elements with `LONG_CARA` (same source). Not used in Tier 1. |
| `ELAS_FO` | factor keyword, optional | — | *linear elastic (temperature-dependent)*. Isotropic linear elasticity whose parameters are functions, usually of temperature (`DEFI_FONCTION(NOM_PARA='TEMP', ...)`) or constants from `DEFI_CONSTANTE`. The function is evaluated at the value of its parameter, which `AFFE_MATERIAU/AFFE_VARC` supplies. Use it when the properties vary over the temperature range of the analysis. |
| `ELAS_FO / E` | `fonction_sdaster` or `nappe_sdaster` or `formule`, required | — | *Young's modulus*. Function of the state variable(s). |
| `ELAS_FO / NU` | `fonction_sdaster` or `nappe_sdaster` or `formule`, required | — | *Poisson's ratio*. Function; for a constant, `DEFI_CONSTANTE(VALE=0.3)` (`upstream/astest/sslv113a.comm:32`). |
| `ELAS_FO / RHO` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional | — | *density*. Function. Needed for mass-dependent calculations, as in `ELAS`. |
| `ELAS_FO / TEMP_DEF_ALPHA` | real, optional | — | *definition temperature of ALPHA*. Required with `ALPHA`. The temperature from which the `ALPHA` function measures expansion: the function gives the mean (secant) coefficient between `TEMP_DEF_ALPHA` and T. The solver re-bases it on the reference temperature `VALE_REF` of `AFFE_MATERIAU/AFFE_VARC` (`upstream/bibfor/mate_util/alfint.F90:192`). Data sheets usually give the mean coefficient from 20 °C, so `TEMP_DEF_ALPHA=20.0` (`upstream/astest/zzzz118a.comm:141`). |
| `ELAS_FO / PRECISION` | real, optional | `1.0` | *tolerance*. Temperature interval, in the unit of temperature, used when re-basing `ALPHA`: within it of `VALE_REF` the solver uses the derivative of the function instead of the secant formula (`upstream/bibfor/mate_util/alfint.F90:190`). Lower it only if the run stops with `MATERIAL1_3`, as that message advises. |
| `ELAS_FO / ALPHA` | `fonction_sdaster` or `formule`, optional | — | *thermal expansion coefficient*. Mean coefficient as a function of temperature, from `TEMP_DEF_ALPHA`. Must be a `DEFI_FONCTION` function: a formula or a two-variable function (nappe) is refused (`MATERIAL1_1`). |
| `ELAS_FO / AMOR_ALPHA` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional | — | *stiffness-proportional damping coefficient*. As in `ELAS`, as a function. |
| `ELAS_FO / AMOR_BETA` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional | — | *mass-proportional damping coefficient*. As in `ELAS`, as a function. |
| `ELAS_FO / AMOR_HYST` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional | — | Hysteretic damping coefficient, as a function. As in `ELAS`. |
| `ELAS_FO / K_DESSIC` | real, optional | `0.0` | Drying-shrinkage coefficient, as in `ELAS`. |
| `ELAS_FO / B_ENDOGE` | real, optional | `0.0` | Autogenous-shrinkage coefficient, as in `ELAS`. |
| `ELAS_FO / LONG_CARA` | real, optional | — | *characteristic length*. Range: ≥ 0.0. As in `ELAS`. |
| `ELAS_FO / COEF_AMOR` | real, optional | `1.0` | *damping coefficient*. As in `ELAS`. |
| `COMP_THM` | text, optional | — | One of `'LIQU_SATU'`, `'LIQU_GAZ'`, `'GAZ'`, `'LIQU_GAZ_ATM'`, `'LIQU_VAPE_GAZ'`, `'LIQU_VAPE'`, `'LIQU_AD_GAZ_VAPE'`, `'LIQU_AD_GAZ'`. Selects the fluid phases of a coupled thermo-hydro-mechanical (THM) material; the values name the phases (liquid, gas, vapor, dissolved air). Out of Tier 1 scope. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. |

1 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at most one of `ELAS`, `ELAS_FO`, `ELAS_VISCO`, `ELAS_FLUI`, `ELAS_ISTR`, `ELAS_ISTR_FO`, `ELAS_VISCO_ISTR`, `ELAS_ORTH`, `ELAS_ORTH_FO`, `ELAS_VISCO_ORTH`, `ELAS_COQUE`, `ELAS_COQUE_FO`, `ELAS_HYPER`, `ELAS_HYPER_VISC`, `ELAS_GLRC`, `ELAS_DHRC` may be given (`EXCLUS`).
- command: at most one of `HYPER_HILL` may be given (`EXCLUS`).
- command: at most one of `THER`, `THER_FO`, `THER_ORTH`, `THER_NL_ORTH`, `THER_NL`, `THER_HYDR`, `THER_COQUE`, `THER_COQUE_FO` may be given (`EXCLUS`).
- command: at most one of `ECRO_LINE`, `ECRO_LINE_FO`, `ECRO_PUIS`, `ECRO_COOK`, `ECRO_COOK_FO` may be given (`EXCLUS`).
- command: at most one of `ENDO_HETEROGENE` may be given (`EXCLUS`).
- command: at most one of `TAHERI`, `TAHERI_FO` may be given (`EXCLUS`).
- command: at most one of `ECRO_NL`, `ECRO_NL_FO` may be given (`EXCLUS`).
- command: at most one of `KICHENIN_NL`, `KICHENIN_NL_FO` may be given (`EXCLUS`).
- command: if `KICHENIN_NL` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `KICHENIN_NL_FO` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: at most one of `ENDO_SCALAIRE`, `ENDO_SCALAIRE_FO` may be given (`EXCLUS`).
- command: at most one of `ENDO_LOCA_EXP`, `ENDO_LOCA_EXP_FO` may be given (`EXCLUS`).
- command: at most one of `ENDO_LOCA_TC`, `ENDO_LOCA_TC_FO` may be given (`EXCLUS`).
- command: at most one of `ENDO_FISS_EXP`, `ENDO_FISS_EXP_FO` may be given (`EXCLUS`).
- command: at most one of `ROUSSELIER`, `ROUSSELIER_FO` may be given (`EXCLUS`).
- command: at most one of `VISC_SINH`, `VISC_SINH_FO` may be given (`EXCLUS`).
- command: at most one of `NORTON`, `NORTON_FO` may be given (`EXCLUS`).
- command: if `ROUSSELIER` is given, `TRACTION` must all be given (`PRESENT_PRESENT`).
- command: if `ROUSSELIER_FO` is given, `TRACTION` must all be given (`PRESENT_PRESENT`).
- command: at most one of `CIN1_CHAB`, `CIN1_CHAB_FO` may be given (`EXCLUS`).
- command: at most one of `CIN2_CHAB`, `CIN2_CHAB_FO` may be given (`EXCLUS`).
- command: at most one of `VISCOCHAB`, `VISCOCHAB_FO` may be given (`EXCLUS`).
- command: at most one of `LEMAITRE`, `LEMAITRE_FO`, `VISC_IRRA_LOG`, `LEMA_SEUIL`, `LEMA_SEUIL_FO`, `LEMAITRE_IRRA` may be given (`EXCLUS`).
- command: at most one of `VENDOCHAB`, `VENDOCHAB_FO` may be given (`EXCLUS`).
- command: at most one of `VISC_ENDO`, `VISC_ENDO_FO` may be given (`EXCLUS`).
- command: at most one of `VISC_ISOT_PLAS`, `VISC_ISOT_PLAS_FO` may be given (`EXCLUS`).
- command: if `VISC_ISOT_PLAS` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `VISC_ISOT_PLAS_FO` is given, `ELAS_FO` must all be given (`PRESENT_PRESENT`).
- command: at most one of `META_LEMA_ANI`, `META_LEMA_ANI_FO` may be given (`EXCLUS`).
- command: at most one of `Iwan`, `Iwan_FO` may be given (`EXCLUS`).
- command: at most one of `MohrCoulombAS`, `MohrCoulombAS_FO` may be given (`EXCLUS`).
- command: at most one of `NLH_CSRM`, `NLH_CSRM_FO` may be given (`EXCLUS`).
- command: at most one of `MCC`, `MCC_FO` may be given (`EXCLUS`).
- command: at most one of `BETON_AGEING`, `BETON_AGEING_FO` may be given (`EXCLUS`).
- command: at most one of `BETON_BURGER`, `BETON_BURGER_FO` may be given (`EXCLUS`).
- command: at most one of `MetaAcierEPIL_PT`, `MetaAcierEPIL_PT_FO` may be given (`EXCLUS`).
- command: if `BPEL_ACIER` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `ETCC_ACIER` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `RELAX_ACIER` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: at most one of `ETCC_ACIER`, `BPEL_ACIER` may be given (`EXCLUS`).
- command: at most one of `ETCC_BETON`, `BPEL_BETON` may be given (`EXCLUS`).
- command: at most one of `RCCM`, `RCCM_FO` may be given (`EXCLUS`).
- command: at most one of `WEIBULL`, `WEIBULL_FO` may be given (`EXCLUS`).
- command: if `LAIGLE` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `LETK` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `LKR` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `DRUCK_PRAGER` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `VISC_DRUC_PRAG` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `VISC_MAXWELL` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `VISC_MAXWELL_MT` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `HOEK_BROWN` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: at most one of `MAZARS`, `MAZARS_FO` may be given (`EXCLUS`).
- command: if `JOINT_BA` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `CABLE` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `MOHR_COULOMB` is given, `ELAS` must all be given (`PRESENT_PRESENT`).
- command: if `ELAS_GLRC` is given, `GLRC_DM` must all be given (`PRESENT_PRESENT`).
- command: at most one of `HAYHURST`, `HAYHURST_FO` may be given (`EXCLUS`).
- command: at most one of `POST_ROCHE`, `POST_ROCHE_FO` may be given (`EXCLUS`).
- command: if `BETON_BURGER` is given, `BETON_DESORP` must all be given (`PRESENT_PRESENT`).
- command: if `BETON_BURGER_FO` is given, `BETON_DESORP` must all be given (`PRESENT_PRESENT`).
- command: if `SECH_RFT` is given, `BETON_DESORP` must all be given (`PRESENT_PRESENT`).
- command: at least one of `TABLE`, `ELAS`, `ELAS_FO`, `ELAS_FLUI`, `ELAS_ISTR`, `ELAS_ISTR_FO`, `ELAS_ORTH`, `ELAS_ORTH_FO`, `ELAS_VISCO`, `ELAS_VISCO_ISTR`, `ELAS_VISCO_ORTH`, `ELAS_COQUE`, `ELAS_COQUE_FO`, `ELAS_MEMBRANE`, `BETON_DESORP`, `SECOND_ELAS`, `FONDA_SUPERFI`, `ELAS_HYPER`, `ELAS_HYPER_VISC`, `ELAS_GLRC`, `ELAS_GLRC_FO`, `ELAS_DHRC`, `HYPER_HILL`, `CABLE`, `VERI_BORNE`, `TRACTION`, `ECRO_LINE`, `ENDO_HETEROGENE`, `ECRO_LINE_FO`, `ECRO_PUIS`, `ECRO_PUIS_FO`, `ECRO_NL`, `ECRO_NL_FO`, `KICHENIN_NL`, `KICHENIN_NL_FO`, `ECRO_COOK`, `ECRO_COOK_FO`, `BETON_ECRO_LINE`, `BETON_REGLE_PR`, `ENDO_ORTH_BETON`, `PRAGER`, `PRAGER_FO`, `TAHERI`, `TAHERI_FO`, `ROUSSELIER`, `ROUSSELIER_FO`, `VISC_SINH`, `VISC_SINH_FO`, `CIN1_CHAB`, `CIN1_CHAB_FO`, `CIN2_CHAB`, `CIN2_CHAB_FO`, `CIN2_NRAD`, `MEMO_ECRO`, `MEMO_ECRO_FO`, `VISCOCHAB`, `VISCOCHAB_FO`, `LEMAITRE`, `LEMAITRE_IRRA`, `VISC_IRRA_LOG`, `GRAN_IRRA_LOG`, `LEMA_SEUIL`, `LEMA_SEUIL_FO`, `IRRAD3M`, `LEMAITRE_FO`, `ARME`, `ASSE_CORN`, `DIS_CONTACT`, `ENDO_SCALAIRE`, `ENDO_SCALAIRE_FO`, `ENDO_LOCA_EXP`, `ENDO_LOCA_EXP_FO`, `ENDO_LOCA_TC`, `ENDO_LOCA_TC_FO`, `ENDO_FISS_EXP`, `ENDO_FISS_EXP_FO`, `DIS_GRICRA`, `BETON_DOUBLE_DP`, `MAZARS`, `MAZARS_FO`, `JOINT_BA`, `VENDOCHAB`, `VENDOCHAB_FO`, `HAYHURST`, `HAYHURST_FO`, `VISC_ENDO`, `VISC_ENDO_FO`, `PINTO_MENEGOTTO`, `BPEL_BETON`, `BPEL_ACIER`, `ETCC_BETON`, `ETCC_ACIER`, `RELAX_ACIER`, `MOHR_COULOMB`, `RANKINE`, `CAM_CLAY`, `CJS`, `HUJEUX`, `ECRO_ASYM_LINE`, `BETON_GRANGER`, `V_BETON_GRANGER`, `BETON_UMLV`, `BETON_RAG`, `FLUA_PORO_BETON`, `ENDO_PORO_BETON`, `FLUA_ENDO_PORO`, `RGI_BETON`, `RGI_BETON_BA`, `GLRC_DM`, `DHRC`, `CORR_ACIER`, `CABLE_GAINE_FROT`, `DIS_ECRO_CINE`, `DIS_VISC`, `DIS_ECRO_TRAC`, `DIS_BILI_ELAS`, `DIS_CHOC_ENDO`, `DIS_CHOC_ELAS`, `HHO`, `JONC_ENDO_PLAS`, `THER_NL`, `THER_HYDR`, `THER`, `THER_FO`, `THER_ORTH`, `THER_NL_ORTH`, `THER_COQUE`, `THER_COQUE_FO`, `SECH_GRANGER`, `SECH_MENSI`, `SECH_BAZANT`, `SECH_NAPPE`, `SECH_RFT`, `META_ACIER_REVENU`, `META_ACIER`, `META_ZIRC`, `DURT_META`, `ELAS_META`, `ELAS_META_FO`, `META_ECRO_LINE`, `META_TRACTION`, `META_VISC_FO`, `META_PT`, `META_RE`, `FLUIDE`, `COMP_THM`, `FATIGUE`, `DOMMA_LEMAITRE`, `CISA_PLAN_CRIT`, `THM_RUPT`, `WEIBULL`, `WEIBULL_FO`, `NON_LOCAL`, `RUPT_FRAG`, `RUPT_FRAG_FO`, `RUPT_TURON`, `CZM_LAB_MIX`, `RUPT_DUCT`, `CZM_ELAS`, `JOINT_MECA_RUPT`, `JOINT_MECA_FROT`, `JOINT_MECA_ENDO`, `RCCM`, `RCCM_FO`, `LAIGLE`, `LETK`, `LKR`, `DRUCK_PRAGER`, `VISC_DRUC_PRAG`, `HOEK_BROWN`, `JOINT_BANDIS`, `VISC_MAXWELL`, `VISC_MAXWELL_MT`, `MONO_VISC1`, `MONO_VISC2`, `MONO_ISOT1`, `MONO_ISOT2`, `MONO_CINE1`, `MONO_CINE2`, `MONO_DD_KR`, `MONO_DD_CFC`, `MONO_DD_CFC_IRRA`, `MONO_DD_FAT`, `MONO_DD_CC`, `MONO_DD_CC_IRRA`, `MFRONT`, `MFRONT_FO`, `UMAT`, `UMAT_FO`, `CRIT_RUPT`, `REST_ECRO`, `BETON_GLRC`, `VISC_ELAS`, `POST_ROCHE`, `POST_ROCHE_FO`, `RUPT_FM`, `NORTON`, `NORTON_FO`, `GTN`, `VISC_ISOT_PLAS`, `VISC_ISOT_PLAS_FO`, `META_LEMA_ANI`, `META_LEMA_ANI_FO`, `BETON_BURGER`, `BETON_BURGER_FO`, `MetaAcierEPIL_PT`, `MetaAcierEPIL_PT_FO`, `Iwan`, `Iwan_FO`, `MohrCoulombAS`, `MohrCoulombAS_FO`, `GonfElas`, `GonfElas_FO`, `NLH_CSRM`, `NLH_CSRM_FO`, `MCC`, `MCC_FO`, `Barcelone`, `Barcelone_FO`, `CSSM`, `CSSM_FO`, `BETON_AGEING`, `BETON_AGEING_FO` must be given (`AU_MOINS_UN`).
- `ELAS`: exactly one of `E`, `K`, `CELE_P` must be given (`UN_PARMI`).
- `ELAS`: `E`, `NU` are given all together or not at all (`ENSEMBLE`).
- `ELAS`: `K`, `MU` are given all together or not at all (`ENSEMBLE`).
- `ELAS`: `CELE_P`, `CELE_S` are given all together or not at all (`ENSEMBLE`).
- `ELAS`: if `CELE_P` is given, `RHO` must all be given (`PRESENT_PRESENT`).
- `ELAS_FO`: if `ALPHA` is given, `TEMP_DEF_ALPHA` must all be given (`PRESENT_PRESENT`).

## Other keywords

Factor keywords outside this draft's scope (sub-keywords are in `en/commands/DEFI_MATERIAU.json`):

- `ARME`
- `ASSE_CORN`
- `BETON_AGEING`
- `BETON_AGEING_FO`
- `BETON_BURGER`
- `BETON_BURGER_FO`
- `BETON_DESORP`
- `BETON_DOUBLE_DP`
- `BETON_ECRO_LINE`
- `BETON_GLRC`
- `BETON_GRANGER`
- `BETON_RAG`
- `BETON_REGLE_PR`
- `BETON_UMLV`
- `BPEL_ACIER`
- `BPEL_BETON`
- `Barcelone`
- `Barcelone_FO`
- `CABLE`
- `CABLE_GAINE_FROT`
- `CAM_CLAY`
- `CIN1_CHAB`
- `CIN1_CHAB_FO`
- `CIN2_CHAB`
- `CIN2_CHAB_FO`
- `CIN2_NRAD`
- `CISA_PLAN_CRIT`
- `CJS`
- `CORR_ACIER`
- `CRIT_RUPT`
- `CSSM`
- `CSSM_FO`
- `CZM_ELAS`
- `CZM_LAB_MIX`
- `DHRC`
- `DIS_BILI_ELAS`: Bilinear law for discrete elements.
- `DIS_CHOC_ELAS`: Impact law with nonlinear elastic behavior.
- `DIS_CHOC_ENDO`: Law for a discrete element with a plastic threshold and variable stiffness and damping.
- `DIS_CONTACT`
- `DIS_ECRO_CINE`: Law for discrete elements with kinematic hardening.
- `DIS_ECRO_TRAC`: Law for a discrete element with isotropic or kinematic hardening.
- `DIS_GRICRA`
- `DIS_VISC`: Law for a viscous discrete element: generalized Zener.
- `DOMMA_LEMAITRE`
- `DRUCK_PRAGER`
- `DURT_META`
- `ECRO_ASYM_LINE`
- `ECRO_COOK`
- `ECRO_COOK_FO`
- `ECRO_LINE`
- `ECRO_LINE_FO`
- `ECRO_NL`
- `ECRO_NL_FO`
- `ECRO_PUIS`
- `ECRO_PUIS_FO`
- `ELAS_COQUE`
- `ELAS_COQUE_FO`
- `ELAS_DHRC`
- `ELAS_FLUI`
- `ELAS_GLRC`
- `ELAS_GLRC_FO`
- `ELAS_HYPER`
- `ELAS_HYPER_VISC`
- `ELAS_ISTR`
- `ELAS_ISTR_FO`
- `ELAS_MEMBRANE`
- `ELAS_META`
- `ELAS_META_FO`
- `ELAS_ORTH`
- `ELAS_ORTH_FO`
- `ELAS_VISCO`
- `ELAS_VISCO_ISTR`
- `ELAS_VISCO_ORTH`
- `ENDO_FISS_EXP`
- `ENDO_FISS_EXP_FO`
- `ENDO_HETEROGENE`
- `ENDO_LOCA_EXP`
- `ENDO_LOCA_EXP_FO`
- `ENDO_LOCA_TC`
- `ENDO_LOCA_TC_FO`
- `ENDO_ORTH_BETON`
- `ENDO_PORO_BETON`
- `ENDO_SCALAIRE`
- `ENDO_SCALAIRE_FO`
- `ETCC_ACIER`
- `ETCC_BETON`
- `FATIGUE`
- `FLUA_ENDO_PORO`
- `FLUA_PORO_BETON`
- `FLUIDE`
- `FONDA_SUPERFI`
- `GLRC_DM`
- `GRAN_IRRA_LOG`
- `GTN`
- `GonfElas`
- `GonfElas_FO`
- `HAYHURST`
- `HAYHURST_FO`
- `HHO`
- `HOEK_BROWN`
- `HUJEUX`
- `HYPER_HILL`
- `IRRAD3M`
- `Iwan`
- `Iwan_FO`
- `JOINT_BA`
- `JOINT_BANDIS`
- `JOINT_MECA_ENDO`
- `JOINT_MECA_FROT`
- `JOINT_MECA_RUPT`
- `JONC_ENDO_PLAS`
- `KICHENIN_NL`
- `KICHENIN_NL_FO`
- `LAIGLE`
- `LEMAITRE`
- `LEMAITRE_FO`
- `LEMAITRE_IRRA`
- `LEMA_SEUIL`
- `LEMA_SEUIL_FO`
- `LETK`
- `LKR`
- `MAZARS`
- `MAZARS_FO`
- `MCC`
- `MCC_FO`
- `MEMO_ECRO`
- `MEMO_ECRO_FO`
- `META_ACIER`
- `META_ACIER_REVENU`
- `META_ECRO_LINE`
- `META_LEMA_ANI`
- `META_LEMA_ANI_FO`
- `META_PT`
- `META_RE`
- `META_TRACTION`
- `META_VISC_FO`
- `META_ZIRC`
- `MFRONT`
- `MFRONT_FO`
- `MOHR_COULOMB`
- `MONO_CINE1`
- `MONO_CINE2`
- `MONO_DD_CC`
- `MONO_DD_CC_IRRA`
- `MONO_DD_CFC`
- `MONO_DD_CFC_IRRA`
- `MONO_DD_FAT`
- `MONO_DD_KR`
- `MONO_ISOT1`
- `MONO_ISOT2`
- `MONO_VISC1`
- `MONO_VISC2`
- `MetaAcierEPIL_PT`
- `MetaAcierEPIL_PT_FO`
- `MohrCoulombAS`
- `MohrCoulombAS_FO`
- `NLH_CSRM`
- `NLH_CSRM_FO`
- `NON_LOCAL`
- `NORTON`
- `NORTON_FO`
- `PINTO_MENEGOTTO`
- `POST_ROCHE`
- `POST_ROCHE_FO`
- `PRAGER`
- `PRAGER_FO`
- `RANKINE`
- `RCCM`
- `RCCM_FO`
- `RELAX_ACIER`
- `REST_ECRO`
- `RGI_BETON`
- `RGI_BETON_BA`
- `ROUSSELIER`
- `ROUSSELIER_FO`
- `RUPT_DUCT`
- `RUPT_FM`
- `RUPT_FRAG`
- `RUPT_FRAG_FO`
- `RUPT_TURON`
- `SECH_BAZANT`
- `SECH_GRANGER`
- `SECH_MENSI`
- `SECH_NAPPE`
- `SECH_RFT`
- `SECOND_ELAS`
- `TABLE` — *table*
- `TAHERI`
- `TAHERI_FO`
- `THER`
- `THER_COQUE`
- `THER_COQUE_FO`
- `THER_FO`
- `THER_HYDR`
- `THER_NL`
- `THER_NL_ORTH`
- `THER_ORTH`
- `THM_AIR_DISS`
- `THM_DIFFU`
- `THM_GAZ`
- `THM_INIT`
- `THM_LIQU`
- `THM_RUPT`
- `THM_VAPE_GAZ`
- `TRACTION`
- `UMAT`
- `UMAT_FO`
- `VENDOCHAB`
- `VENDOCHAB_FO`
- `VERI_BORNE`
- `VISCOCHAB`
- `VISCOCHAB_FO`
- `VISC_DRUC_PRAG`
- `VISC_ELAS`
- `VISC_ENDO`
- `VISC_ENDO_FO`
- `VISC_IRRA_LOG`
- `VISC_ISOT_PLAS`
- `VISC_ISOT_PLAS_FO`
- `VISC_MAXWELL`
- `VISC_MAXWELL_MT`
- `VISC_SINH`
- `VISC_SINH_FO`
- `V_BETON_GRANGER`
- `WEIBULL`
- `WEIBULL_FO`

## Patterns

### Linear elastic steel, static analysis

`E` and `NU` are all a linear static analysis reads.

Source: `tests/fixtures/solid_static/input/run.comm:25` (also `upstream/astest/zzzz503g.py:39`).

```python
ACIER = DEFI_MATERIAU(ELAS=_F(E=210000.0, NU=0.3))
```

The log echoes the call with the defaults filled in (`tests/fixtures/shell_static/output/run.mess`):

```python
ACIER = DEFI_MATERIAU(ELAS=_F(B_ENDOGE=0.0,
                              COEF_AMOR=1.0,
                              E=210000.0,
                              K_DESSIC=0.0,
                              NU=0.3),
                      INFO=1)
```

### Add the density for a modal analysis

Units mm, N, MPa, so the density is in t/mm³.

Source: `tests/fixtures/modal/input/run.comm:22`.

```python
ACIER = DEFI_MATERIAU(ELAS=_F(E=210000.0, NU=0.3, RHO=7.85e-9))
```

### Rayleigh damping for a dynamic analysis

The two coefficients are computed for a damping ratio `xi` between two frequencies `f1` and
`f2` (lines 44–46 of the same file). `AMOR_ALPHA` multiplies stiffness, `AMOR_BETA` mass.

Source: `upstream/astest/forma12b.comm:54`.

```python
MAT = DEFI_MATERIAU(ELAS=_F(E=E, NU=nu, RHO=rho, AMOR_ALPHA=alpha, AMOR_BETA=beta))
```

### Thermal expansion with a constant coefficient

`ALPHA` acts only together with a temperature field assigned in `AFFE_MATERIAU`.

Source: `upstream/astest/hplv102a.comm:65`.

```python
MA = DEFI_MATERIAU(ELAS=_F(E=200000.0, NU=0.3, ALPHA=1e-06))

CM = AFFE_MATERIAU(
    MAILLAGE=M,
    AFFE=_F(TOUT="OUI", MATER=MA),
    AFFE_VARC=_F(TOUT="OUI", VALE_REF=0.0, CHAM_GD=TEMP, NOM_VARC="TEMP"),
)
```

### Temperature-dependent properties

`YOUN`, `NU` and `ALPH` are functions of `TEMP` defined with `DEFI_FONCTION` (`ALPH` at line
120, the mean coefficient from 20 °C). `TEMP_DEF_ALPHA=20.0` says so, and `VALE_REF=20.0` in
`AFFE_MATERIAU` sets the stress-free temperature.

Source: `upstream/astest/zzzz118a.comm:141`.

```python
MAT1 = DEFI_MATERIAU(ELAS_FO=_F(E=YOUN, NU=NU, TEMP_DEF_ALPHA=20.0, ALPHA=ALPH))

CHMAT1 = AFFE_MATERIAU(
    MAILLAGE=MA,
    AFFE=_F(GROUP_MA=("STRIA1", "STRIA2", "SQUA"), MATER=MAT1),
    AFFE_VARC=_F(TOUT="OUI", EVOL=TEMPER1, NOM_VARC="TEMP", NOM_CHAM="TEMP", VALE_REF=20.0),
)
```

### Elasticity plus a plasticity law

Other behaviors go in the same call; here linear isotropic hardening (`ECRO_LINE`, slope
`D_SIGM_EPSI`, yield stress `SY`), used by nonlinear analyses.

Source: `upstream/astest/zzzz505d.py:32`.

```python
acier = DEFI_MATERIAU(ELAS=_F(E=200000.0, NU=0.3), ECRO_LINE=_F(D_SIGM_EPSI=2000.0, SY=200000.0))
```

## Pitfalls

- **Inconsistent units.** The solver does not check units. With the mesh in mm and `E` in MPa,
  `RHO` must be in t/mm³ (7.85e-9 for steel), not kg/m³ (7850): the latter gives masses 10¹²
  times too large and frequencies 10⁶ times too low. Our `modal` fixture states its unit system
  in its header (`tests/fixtures/modal/input/run.comm:2`).
- **Missing `RHO`.** A mass matrix, gravity load or rotation load needs the density. Without it
  the elementary calculation stops, with message `MODELISA9_77` naming the missing parameter
  and then the fatal `MODELISA6_4` (`upstream/bibfor/calcul/rcvals.F90:41`); beam and fracture
  commands have their own messages (`POUTRE0_42`, `RUPTURE1_26`).
- **Rayleigh coefficients swapped.** `AMOR_ALPHA` is the stiffness coefficient and `AMOR_BETA`
  the mass coefficient (`upstream/bibfor/te/te0121.F90:174`). Copying α and β from a reference
  that writes C = αM + βK swaps them silently.
- **`ALPHA` without a temperature does nothing.** Thermal strain needs `AFFE_MATERIAU/AFFE_VARC`
  with `NOM_VARC='TEMP'` and `VALE_REF` (`upstream/bibfor/modelisa/verift.F90:104`).
- **`TEMP_DEF_ALPHA` is not the reference temperature.** `TEMP_DEF_ALPHA` (in `ELAS_FO`) says how
  the `ALPHA` data were measured; `VALE_REF` (in `AFFE_MATERIAU`) is the stress-free
  temperature. They differ in general; the solver converts between them (`MATERIAL1_2` if
  the reference is missing). An `ALPHA` function with a single point works only when the two
  temperatures are equal within 1 degree (`MATERIAL1_42`, `upstream/bibfor/mate_util/alfint.F90:147`), unless the function is extended as a constant.
- **Two elasticity groups in one material.** `ELAS`, `ELAS_FO`, `ELAS_ORTH` and the other
  elasticity groups are mutually exclusive (first `EXCLUS` rule below); a material enriched with
  a second one through `MATER` stops calculations with `COMPOR5_56` (`upstream/bibfor/mate_util/rccoma.F90:89`).

## See also

- French reference: U4.43.01 (French text: `en/docs/_src/U4.43.01.fr.md`; translation: `en/docs/U4.43.01.md` once task 5.2 lands)
- Catalog: `en/commands/DEFI_MATERIAU.json` (generated from `upstream/code_aster/Cata/Commands/defi_materiau.py:51`)
- Implementation: `upstream/code_aster/CodeCommands/defi_materiau.py` (conversion of `K`/`MU` and
  `CELE_P`/`CELE_S`); re-basing of `ALPHA` `upstream/bibfor/mate_util/alfint.F90`; thermal strain
  `upstream/bibfor/modelisa/verift.F90`
- Before: `DEFI_FONCTION`, `DEFI_CONSTANTE` (for `ELAS_FO`)
- Next steps: `AFFE_MATERIAU` (assign the material to element groups)
- Example: `upstream/astest/zzzz503g.py` (line 39)
- Example: `upstream/astest/zzzz505d.py` (lines 32, 152)
- Example: `upstream/astest/forma12b.comm` (line 54)
- Example: `upstream/astest/zzzz118a.comm` (line 141)
- Example: `tests/fixtures/modal/input/run.comm` (line 22)
