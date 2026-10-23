# Command set — what gets translated, in what order

The scope is driven by what ClearFEA's code_aster path needs, not by the size of the catalog. Commands are listed by the function they serve in a run. Names are upstream names and must be verified against the pinned catalog in Phase 0 (a few may have been renamed or merged in recent versions — record any such finding in PROGRESS and correct here).

Status column is maintained by hand as references land: `—` not started · `json` extracted · `assisted` drafted · `reviewed` engineer-approved.

## Tier 1 — alpha: linear static, solids and shells (≈ 22 commands)

| Function | Command | Key keywords to cover first | Status |
|---|---|---|---|
| Session | `DEBUT`, `FIN`, `POURSUITE` | `CODE`, `ERREUR`, `DEBUG`, `IGNORE_ALARM` | — |
| Mesh in | `LIRE_MAILLAGE` | `FORMAT='MED'`, `UNITE`, `VERI_MAIL` | — |
| Mesh fix-ups | `MODI_MAILLAGE` | `ORIE_PEAU` (outward normals for pressure faces), `ORIE_NORM_COQUE` (shell normals) | — |
| Groups | `DEFI_GROUP` | `CREA_GROUP_MA` / `CREA_GROUP_NO` (`TOUT`, `UNION`, `INTERSEC`, `DIFFE`, `OPTION='NOEUD_ORDO'`, geometric selections `SPHERE`, `BANDE`) | — |
| Mesh derive | `CREA_MAILLAGE` | `QUAD_LINE`, `LINE_QUAD`, `COQU_VOLU` (later) | — |
| Model | `AFFE_MODELE` | `AFFE` × (`TOUT`/`GROUP_MA`, `PHENOMENE='MECANIQUE'`, `MODELISATION` ∈ {`3D`, `3D_SI`, `DKT`, `DST`, `COQUE_3D`, `AXIS`, `C_PLAN`, `D_PLAN`}) | — |
| Material | `DEFI_MATERIAU` | `ELAS` (`E`, `NU`, `RHO`, `ALPHA`), `ELAS_FO` (temperature-dependent) | — |
| Material field | `AFFE_MATERIAU` | `AFFE` × (`GROUP_MA`, `MATER`), `AFFE_VARC` (temperature field, Tier 2) | — |
| Element props | `AFFE_CARA_ELEM` | `COQUE` (`EPAIS`, `VECTEUR`, `ANGL_REP`, `COQUE_NCOU`), `DISCRET` (Tier 2 springs) | — |
| Loads & BCs | `AFFE_CHAR_MECA` | `DDL_IMPO`, `FACE_IMPO`, `PRES_REP`, `FORCE_FACE`, `FORCE_NODALE`, `FORCE_ARETE`, `PESANTEUR`, `ROTATION`, `LIAISON_DDL`, `LIAISON_UNIF`, `LIAISON_SOLIDE`, `LIAISON_MAIL` (bonded, Tier 2), `LIAISON_RBE3` (remote load, Tier 2) | — |
| BCs (kinematic) | `AFFE_CHAR_CINE` | `MECA_IMPO` — preferred for pure Dirichlet (no Lagrange multipliers) | — |
| Functions | `DEFI_FONCTION`, `DEFI_CONSTANTE` | `NOM_PARA`, `VALE`, `PROL_DROITE/GAUCHE`, `INTERPOL` — needed for hydrostatic pressure and temperature tables | — |
| Solve | `MECA_STATIQUE` | `MODELE`, `CHAM_MATER`, `CARA_ELEM`, `EXCIT` (`CHARGE`, `FONC_MULT`), `SOLVEUR` (`METHODE` ∈ {`MUMPS`, `MULT_FRONT`}, `RESI_RELA`), `OPTION` | — |
| Post fields | `CALC_CHAMP` | `CONTRAINTE` (`SIGM_ELNO`, `SIGM_NOEU`, `SIEF_ELNO`), `CRITERES` (`SIEQ_ELNO`, `SIEQ_NOEU`), `DEFORMATION` (`EPSI_ELNO`, `EPSI_NOEU`), `FORCE` (`REAC_NODA`, `FORC_NODA`), `ENERGIE` | — |
| Post extract | `POST_RELEVE_T` | `ACTION` × (`OPERATION='EXTRACTION'`, `INTITULE`, `RESULTAT`, `NOM_CHAM`, `GROUP_NO`, `RESULTANTE`, `MOMENT`, `POINT`) — reactions and resultants | — |
| Post elem | `POST_ELEM` | `MASS_INER`, `VOLUMOGRAMME` (later) | — |
| Field ops | `CREA_CHAMP` | `OPERATION` ∈ {`EXTR`, `AFFE`, `ASSE`}, `TYPE_CHAM` — used for initial/temperature fields and result assembly | — |
| Output | `IMPR_RESU` | `FORMAT='MED'`, `RESU` × (`RESULTAT`, `NOM_CHAM`, `GROUP_MA`), `UNITE` | — |
| Output tables | `IMPR_TABLE` | `TABLE`, `FORMAT` (`TABLEAU`, `ASTER`), `SEPARATEUR`, `UNITE` | — |
| Verification | `TEST_RESU` | `RESU` × (`VALE_CALC`, `VALE_REFE`, `REFERENCE`, `PRECISION`) — used in fixtures only | — |
| Cut lines | `MACR_LIGN_COUPE` | `LIGN_COUPE` (`TYPE='SEGMENT'`, `COOR_ORIG`, `COOR_EXTR`, `NB_POINTS`) — stress classification lines later; include early because pressure-vessel users need it | — |
| Linearisation | `POST_RCCM` *(or current equivalent)* | `TYPE_RESU_MECA`, `OPTION='PM_PB'` — stress linearisation per ASME-style membrane/bending; **verify name in pinned version** | — |

### Tier 1 message families (verify names in Phase 0; translate first, review after fixtures)

Likely: `SUPERVIS`, `JEVEUX`, `MODELISA`, `CALCULEL`, `MECASTATIQUE` or `MECANONLINE`, `ALGELINE`, `FACTOR`, `MATERIAL`, `CHARGES`, `POSTRELE`, `PREPOST`, `MED`, `UTILITAI`, `ELEMENTS`, `COMPOR`, `DVP`. The astest-index (1.4) and the fixture `.mess` logs (4.2) refine this list.

## Tier 2 — post-alpha: modal, extra loads, bonded assemblies (≈ 10 commands)

| Function | Command | Key keywords | Status |
|---|---|---|---|
| Modal | `CALC_MODES` | `OPTION` (`PLUS_PETITE`, `BANDE`, `CENTRE`), `CALC_FREQ` (`NMAX_FREQ`, `FREQ`), `SOLVEUR_MODAL`, `MATR_RIGI`/`MATR_MASS` or `MODELE`+`CHAM_MATER` form | — |
| Modal matrices | `ASSEMBLAGE` (or `CALC_MATR_ELEM`+`NUME_DDL`+`ASSE_MATRICE`) | `MATR_ASSE` (`RIGI_MECA`, `MASS_MECA`), `CHARGE` | — |
| Modal post | `NORM_MODE`, `EXTR_MODE`, `POST_ELEM MASS_INER` | `NORME`, `FILTRE_MODE` (`CRIT_EXTR='MASS_EFFE_UN'`, `SEUIL`) — effective mass table for the report | — |
| Remote load | `AFFE_CHAR_MECA` / `LIAISON_RBE3`, `LIAISON_SOLIDE` | `GROUP_NO_MAIT`, `GROUP_NO_ESCL`, `DDL_MAIT`, `COEF_ESCL` | — |
| Bonded contact | `AFFE_CHAR_MECA` / `LIAISON_MAIL` | `GROUP_MA_MAIT`, `GROUP_MA_ESCL`, `TYPE_RACCORD` | — |
| Springs | `AFFE_CARA_ELEM` / `DISCRET` + `AFFE_MODELE DIS_T`/`DIS_TR` | `CARA` (`K_T_D_N`, `K_TR_D_N`), `VALE`, `REPERE` | — |
| Temperature load | `AFFE_MATERIAU` / `AFFE_VARC` + `CREA_CHAMP` | `NOM_VARC='TEMP'`, `VALE_REF`, `CHAM_GD` | — |
| Thermal (steady) | `THER_LINEAIRE`, `AFFE_CHAR_THER` | `TEMP_IMPO`, `FLUX_REP`, `ECHANGE`, `SOURCE` | — |
| Hydrostatic | `DEFI_FONCTION` + `AFFE_CHAR_MECA PRES_REP` with `FONC_MULT` / `AFFE_CHAR_MECA_F` | spatial function of `Z` | — |

## Tier 3 — later (nonlinear, contact, buckling, transient)

`STAT_NON_LINE`, `DEFI_CONTACT`, `DEFI_LIST_INST`, `DEFI_LIST_REEL`, `CALC_EUROPLEXUS` (no), `DYNA_VIBRA`, `MODE_NON_LINE` (no), `CALC_FATIGUE`, `POST_CHAMP`, `CALC_G` (fracture, no). Not before ClearFEA asks.

## Explicitly out of scope

Everything else: fluid-structure, acoustics, soil, XFEM, damage models, `*_ENDO_*`, `HHO`, `MISS3D`, `IFS`, EDF-internal workflows. The catalog is still extracted for all commands (cheap, needed for diffing), but no `.md` is written.

## Notes for authors

- A reference must say **what the keyword does to the model**, not re-state its type. "`ORIE_PEAU` reorients the 2D boundary elements of a group so their normal points outward from the solid; required before applying `PRES_REP`, otherwise pressure acts inward and the run silently gives the wrong sign" is the standard.
- Prefer the kinematic form (`AFFE_CHAR_CINE`) for fixings and say why (no dualisation, faster, no reaction via Lagrange — reactions then come from `REAC_NODA`).
- Shell notes must cover normal orientation, `COQUE_NCOU` layers for stress recovery, and that `SIEQ` on shells is per layer/position (`SUP`/`INF`/`MOY`).
- Cite the test case(s) you read while writing. If none exist for a keyword combination, say so.
