---
command: AFFE_CHAR_CINE
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/affe_char_cine.py:48
doc_fr: U4.44.03
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 2.3c)
examples: [gcpc002c, ssls106a, ssnp123f, zzzz144a, ssla200a, ttnl101e]
---

# AFFE_CHAR_CINE — assign kinematic BCs

> **Assisted reference.** Written in session from the pinned catalog, the command's Python
> implementation, the solver source it calls, the message catalog, upstream test cases and the
> committed fixture runs. Every behavior claim cites its source. Not reviewed by an engineer.

`AFFE_CHAR_CINE` imposes known values of degrees of freedom (DOFs) on nodes, the condition
U = U0, and produces a kinematic load (`char_cine_meca` for `MECA_IMPO`). The analysis
eliminates those DOFs from the system of equations instead of adding a Lagrange multiplier per
condition, which is what `AFFE_CHAR_MECA/DDL_IMPO` does (catalog: «pour un traitement sans
dualisation», "without Lagrange-multiplier enforcement"). It needs only the model. The
analysis takes it in `EXCIT` like any other load, and it can be mixed there with
`AFFE_CHAR_MECA` loads (`upstream/astest/ssls106a.comm:53`). The decision it encodes is the
same as `DDL_IMPO`: which DOFs of which nodes are fixed, and at what value. COMMAND-SET
prefers this form for plain supports: the system has no Lagrange unknowns, and the support
reactions still come from `CALC_CHAMP(FORCE='REAC_NODA')` (`upstream/astest/ssla200a.comm:1149`).
It only imposes values: relations between DOFs (`LIAISON_*`) still need `AFFE_CHAR_MECA`.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Affectation de conditions aux limites cinématiques (U=U0) pour un traitement sans dualisation» |
| Kind | `OPER` |
| Result | `char_cine_meca`, `char_cine_ther`, `char_cine_acou` (depends on the keywords given) |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.44.03 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 1 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `MECA_IMPO` |

## Keywords

The DOF names are the components of the displacement quantity `DEPL_R`; their meanings below
come from the catalog comment of that quantity (`upstream/catalo/cataelem/Commons/physical_quantities.py:856`).
A component can be imposed only on nodes that carry it, which depends on the modeling of the
elements around the node: solid (`3D`) nodes carry `DX`, `DY`, `DZ`; shell nodes (`DKT`,
`COQUE_3D`) also carry `DRX`, `DRY`, `DRZ`.

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MODELE` | `modele_sdaster`, required | — | *model*. The model whose DOFs are imposed. |
| `MECA_IMPO` | factor keyword, optional, repeatable | — | *imposed DOF (kinematic)*. One set of nodes and the values of their mechanical DOFs. Repeat it for each support (`upstream/astest/ssls106a.comm:44`). Where occurrences overlap on a node and DOF, the last value given wins: each occurrence overwrites the same slot of the imposed-value field (`upstream/bibfor/modelisa/charci.F90:297`). |
| `MECA_IMPO / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Every node of the mesh. For a DOF that must be zero everywhere, such as `DZ` in a plane model run as 3D (`upstream/astest/ssnp123f.comm:80`). |
| `MECA_IMPO / GROUP_MA` | element group, optional, list | — | *element group*. The nodes of these elements: the usual way to fix a face or an edge (`upstream/astest/ssls106a.comm:46`). |
| `MECA_IMPO / GROUP_NO` | node group, optional, list | — | *node group*. These nodes: for points and node sets (`upstream/astest/gcpc002c.comm:36`). |
| `MECA_IMPO / DX` | real, optional | — | Displacement along global X imposed on every node of the occurrence, in the length unit of the mesh. `DX=0.0` fixes the node in X. |
| `MECA_IMPO / DY` | real, optional | — | Displacement along global Y. |
| `MECA_IMPO / DZ` | real, optional | — | Displacement along global Z. |
| `MECA_IMPO / DRX` | real, optional | — | Rotation about global X, in radians. Exists only on nodes with rotational DOFs (shells, beams, discrete `DIS_TR`). |
| `MECA_IMPO / DRY` | real, optional | — | Rotation about global Y, in radians. |
| `MECA_IMPO / DRZ` | real, optional | — | Rotation about global Z, in radians. |
| `MECA_IMPO / GRX` | real, optional | — | A beam DOF not described in the catalog comment. TODO(verify) its meaning (cross-section warping of the `POU_D_TG` beam) against U4.44.01. Not used in Tier 1. |
| `MECA_IMPO / PRES` | real, optional | — | A pressure DOF; not described in the catalog comment. TODO(verify) which modelings carry it (fluid, incompressible formulations) against U4.44.01. Not used in Tier 1. |
| `MECA_IMPO / PHI` | real, optional | — | Depending on the modeling, a fluid displacement potential, a crack angle or a shear angle of the `PLAQ_MITC` plate (catalog comment). Not used in Tier 1. |
| `MECA_IMPO / PSI` | real, optional | — | Fluid velocity potential (catalog comment). Not used in Tier 1. |
| `MECA_IMPO / TEMP` | real, optional | — | *temperature*. A temperature DOF of the mechanical quantity (catalog comment «DDL de temperature»), carried by coupled modelings such as THM; not the temperature of a thermal model: to impose a temperature in a thermal analysis use `THER_IMPO`. Not used in Tier 1. |
| `MECA_IMPO / PRE1` | real, optional | — | First pressure DOF of coupled hydro-mechanical (THM) modelings (catalog comment: «DDL de pression»). Out of scope. |
| `MECA_IMPO / PRE2` | real, optional | — | Second pressure DOF of THM modelings. Out of scope. |
| `MECA_IMPO / GONF` | real, optional | — | Not described in the catalog comment. TODO(verify) its meaning (swelling DOF of incompressible formulations) against U4.44.01. Out of scope. |
| `MECA_IMPO / GLIS` | real, optional | — | Relative tangential displacement (slip), in a local basis (catalog comment). Out of scope. |
| `MECA_IMPO / LAG_GV` | real, optional | — | A Lagrange multiplier of some formulations (catalog comment: «méthode plaq_mitc»). Out of scope. |
| `MECA_IMPO / LH1` | real, optional | — | Lagrange multiplier of the pressure across a crack in HM-XFEM (catalog comment). Out of scope (XFEM). |
| `MECA_IMPO / UI2`, `MECA_IMPO / UI3`, `MECA_IMPO / UI4`, `MECA_IMPO / UI5`, `MECA_IMPO / UI6`, `MECA_IMPO / UO2`, `MECA_IMPO / UO3`, `MECA_IMPO / UO4`, `MECA_IMPO / UO5`, `MECA_IMPO / UO6`, `MECA_IMPO / VI2`, `MECA_IMPO / VI3`, `MECA_IMPO / VI4`, `MECA_IMPO / VI5`, `MECA_IMPO / VI6`, `MECA_IMPO / VO2`, `MECA_IMPO / VO3`, `MECA_IMPO / VO4`, `MECA_IMPO / VO5`, `MECA_IMPO / VO6`, `MECA_IMPO / WI2`, `MECA_IMPO / WI3`, `MECA_IMPO / WI4`, `MECA_IMPO / WI5`, `MECA_IMPO / WI6`, `MECA_IMPO / WO2`, `MECA_IMPO / WO3`, `MECA_IMPO / WO4`, `MECA_IMPO / WO5`, `MECA_IMPO / WO6`, `MECA_IMPO / WO`, `MECA_IMPO / WI1`, `MECA_IMPO / WO1` | real, optional | — | DOFs of the pipe elements (`TUYAU_*` modelings, catalog comment «DDL des elements de tube»): the Fourier terms of the cross-section deformation. Out of scope. |
| `MECA_IMPO / H1X`, `MECA_IMPO / H1Y`, `MECA_IMPO / H1Z`, `MECA_IMPO / H1PRE1`, `MECA_IMPO / K1`, `MECA_IMPO / K2`, `MECA_IMPO / K3` | real, optional | — | XFEM enrichment DOFs: Heaviside (`H1*`) and crack-tip (`K*`) (catalog comment). Out of scope (XFEM). |
| `MECA_IMPO / V11`, `MECA_IMPO / V12`, `MECA_IMPO / V13`, `MECA_IMPO / V21`, `MECA_IMPO / V22`, `MECA_IMPO / V23`, `MECA_IMPO / V31`, `MECA_IMPO / V32`, `MECA_IMPO / V33`, `MECA_IMPO / PRES11`, `MECA_IMPO / PRES12`, `MECA_IMPO / PRES13`, `MECA_IMPO / PRES21`, `MECA_IMPO / PRES22`, `MECA_IMPO / PRES23`, `MECA_IMPO / PRES31`, `MECA_IMPO / PRES32`, `MECA_IMPO / PRES33` | real, optional | — | DOFs of the mixed second-gradient modeling: `Vij` = ∂ui/∂xj, `PRESij` the multiplier that enforces it (catalog comment). Out of scope. |
| `THER_IMPO` | factor keyword, optional, repeatable | — | Imposed temperature for a thermal model (result `char_cine_ther`, for the thermal analyses). Tier 2 (steady thermal). Same node selection as `MECA_IMPO` (`upstream/astest/ttnl101e.comm:69`). |
| `THER_IMPO / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. |
| `THER_IMPO / GROUP_MA` | element group, optional, list | — | *element group*. |
| `THER_IMPO / GROUP_NO` | node group, optional, list | — | *node group*. |
| `THER_IMPO / TEMP` | real, optional | — | *temperature*. The imposed temperature, in the temperature unit of the material data. |
| `THER_IMPO / TEMP_MIL` | real, optional | — | Temperature of the mid-surface of a thermal shell (catalog comment of `TEMP_R`, `upstream/catalo/cataelem/Commons/physical_quantities.py:3740`). |
| `THER_IMPO / TEMP_SUP` | real, optional | — | Temperature of the upper face of a thermal shell (same source). |
| `THER_IMPO / TEMP_INF` | real, optional | — | Temperature of the lower face of a thermal shell (same source; `upstream/astest/tpls101a.comm:759`). |
| `ACOU_IMPO` | factor keyword, optional, repeatable | — | Imposed acoustic pressure for an acoustic model (result `char_cine_acou`). Out of scope. |
| `ACOU_IMPO / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. |
| `ACOU_IMPO / GROUP_MA` | element group, optional, list | — | *element group*. |
| `ACOU_IMPO / GROUP_NO` | node group, optional, list | — | *node group*. |
| `ACOU_IMPO / PRES` | complex, required | — | The complex acoustic pressure. |
| `EVOL_IMPO` | `evol_noli` or `evol_elas` or `evol_ther`, optional | — | *imposed result*. Imposes the DOFs of an evol_xxx result: every DOF present in the first field of the result is imposed, at each time, with the value of the result at that time (`upstream/bibfor/modelisa/charci.F90:141`; message `CALCULEL_2`). Used to drive a sub-model with the displacements of a global run. Not used in Tier 1. |
| `NOM_CMP` | text, optional, list | — | *component name*. Only when `exists("EVOL_IMPO")`. Impose only these components of `EVOL_IMPO` (default: all, catalog comment). |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `2` prints the field of imposed DOFs (`upstream/bibfor/modelisa/charci.F90:350`). |

4 hidden keyword(s) (`statut='c'`, set by the code, not by users) are not listed.

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: exactly one of `MECA_IMPO`, `THER_IMPO`, `ACOU_IMPO`, `EVOL_IMPO` must be given (`UN_PARMI`).
- `MECA_IMPO`: exactly one of `TOUT`, `GROUP_MA`, `GROUP_NO`, `NOEUD` must be given (`UN_PARMI`).
- `MECA_IMPO`: at least one of `DX`, `DY`, `DZ`, `DRX`, `DRY`, `DRZ`, `GRX`, `PRES`, `PHI`, `TEMP`, `PRE1`, `PRE2`, `UI2`, `UI3`, `VI2`, `VI3`, `WI2`, `WI3`, `UO2`, `UO3`, `VO2`, `VO3`, `WO2`, `WO3`, `UI4`, `UI5`, `VI4`, `VI5`, `WI4`, `WI5`, `UO4`, `UO5`, `VO4`, `VO5`, `WO4`, `WO5`, `UI6`, `UO6`, `VI6`, `VO6`, `WI6`, `WO6`, `WO`, `WI1`, `WO1`, `GONF`, `H1X`, `H1Y`, `H1Z`, `H1PRE1`, `K1`, `K2`, `K3`, `V11`, `V12`, `V13`, `V21`, `V22`, `V23`, `V31`, `V32`, `V33`, `PRES11`, `PRES12`, `PRES13`, `PRES21`, `PRES22`, `PRES23`, `PRES31`, `PRES32`, `PRES33`, `LH1`, `GLIS`, `PSI`, `LAG_GV` must be given (`AU_MOINS_UN`).
- `THER_IMPO`: exactly one of `TOUT`, `GROUP_MA`, `GROUP_NO` must be given (`UN_PARMI`).
- `THER_IMPO`: at least one of `TEMP`, `TEMP_MIL`, `TEMP_INF`, `TEMP_SUP` must be given (`AU_MOINS_UN`).
- `ACOU_IMPO`: exactly one of `TOUT`, `GROUP_MA`, `GROUP_NO` must be given (`UN_PARMI`).

Unlike `DDL_IMPO`, each `MECA_IMPO` occurrence takes exactly one of `TOUT`, `GROUP_MA`,
`GROUP_NO`: to fix an element group and a node group, write two occurrences.

## Patterns

### Supports for a static analysis, mixed with a force load

Symmetry planes `Syz` (DX = 0) and `Sxy` (DZ = 0) and one node in Y; the forces are in an
`AFFE_CHAR_MECA` load, and both go into `EXCIT`.

Source: `upstream/astest/ssls106a.comm:44`.

```python
kine = AFFE_CHAR_CINE(
    MECA_IMPO=(
        _F(DX=0.0, GROUP_MA=("Syz",)),
        _F(DZ=0.0, GROUP_MA=("Sxy",)),
        _F(DY=0.0, GROUP_NO=("nce",)),
    ),
    MODELE=model,
)

reslin = MECA_STATIQUE(
    CHAM_MATER=fieldmat,
    EXCIT=(_F(CHARGE=forcPonc), _F(CHARGE=kine)),
    MODELE=model,
    SOLVEUR=_F(POSTTRAITEMENTS="MINI"),
)
```

### Imposed displacement (non-zero value)

`CHARGE` is pulled by DX = −1 while `SUPZ` is held in Z.

Source: `upstream/astest/gcpc002c.comm:36`.

```python
CHA2 = AFFE_CHAR_CINE(
    MODELE=MO, MECA_IMPO=(_F(GROUP_NO="SUPZ", DZ=0.0), _F(GROUP_NO="CHARGE", DX=-1.0))
)
```

### Clamp a solid face

The usual fixed support of our solid fixtures, in kinematic form: every node of the face
`Encast` held in X, Y and Z.

Source: `upstream/astest/zzzz144a.comm:55`.

```python
CH2 = AFFE_CHAR_CINE(MODELE=MODM, MECA_IMPO=_F(GROUP_MA="Encast", DX=0.0, DY=0.0, DZ=0.0))
```

### One DOF fixed on the whole mesh

Source: `upstream/astest/ssnp123f.comm:80`.

```python
APPUI = AFFE_CHAR_CINE(MODELE=MO, MECA_IMPO=_F(TOUT="OUI", DZ=0.0))
```

### Imposed temperature for a thermal analysis

Source: `upstream/astest/ttnl101e.comm:69`.

```python
BND_TEMP = AFFE_CHAR_CINE(MODELE=MODEL, THER_IMPO=_F(GROUP_MA="END", TEMP=0))
```

## Pitfalls

- **A DOF that the nodes do not carry.** Components missing on some nodes of an occurrence are
  skipped there without a message (only nodes that carry the DOF are imposed,
  `upstream/bibfor/modelisa/chcsur.F90:130`). The command stops only if nothing at all is
  imposed (`CALCULEL_9`: "none of the DOFs to block belongs to the model",
  `upstream/bibfor/modelisa/chcsur.F90:154`). So `DRX=0.0` on the nodes of a solid face does
  nothing, silently: a shell-to-solid support that relies on it is not clamped in rotation.
  `AFFE_CHAR_MECA/DDL_IMPO` is stricter (`CHARGES2_45`).
- **Not every analysis option accepts it.** Kinematic loads cannot be follower loads
  (`CHARGES9_3`), cannot be driven by `PILOTAGE` (`CHARGES9_7`,
  `upstream/bibfor/listLoad/listLoad_module.F90:318`), are refused with
  `SOLVEUR/ELIM_LAGR='OUI'` (`ELIMLAGR_4`) and with `CALC_MODES` `OPTION='PLUS_GRANDE'`
  (`ALGELINE2_7`). In each case the message advises using `AFFE_CHAR_MECA` instead. The Tier 1
  path (`MECA_STATIQUE`) accepts it (catalog `EXCIT/CHARGE` type `char_cine_meca`,
  `upstream/code_aster/Cata/Commands/meca_statique.py:67`).
- **No relations.** `AFFE_CHAR_CINE` imposes values only. Rigid links, ties and equal-DOF
  conditions (`LIAISON_SOLIDE`, `LIAISON_MAIL`, `LIAISON_UNIF`, `LIAISON_DDL`) stay in
  `AFFE_CHAR_MECA`; the two kinds can be used together (`upstream/astest/zzzz144a.comm:55`).
- **Overlapping occurrences.** A node in two occurrences with different values for the same DOF
  takes the value of the last occurrence, without a message (`upstream/bibfor/modelisa/charci.F90:297`).
  Write each support once, or put the exceptions last on purpose.
- **Modal analyses need the same load on every matrix.** The matrices are assembled with the
  kinematic load, and the dynamic commands check that it is consistent across them
  (`DYNALINE2_4` to `DYNALINE2_10`). TODO(verify) the `CALC_MODES` path when task 2.3d/Tier 2
  covers it.

## See also

- French reference: U4.44.03 (French text: `en/docs/_src/U4.44.03.fr.md`; translation: `en/docs/U4.44.03.md` once task 5.2 lands)
- Catalog: `en/commands/AFFE_CHAR_CINE.json` (generated from `upstream/code_aster/Cata/Commands/affe_char_cine.py:48`)
- Implementation: `upstream/code_aster/CodeCommands/affe_char_cine.py`;
  `upstream/bibfor/op/op0101.F90`, `upstream/bibfor/modelisa/charci.F90`,
  `upstream/bibfor/modelisa/chcsur.F90`
- Lagrange-multiplier form, loads and relations: [AFFE_CHAR_MECA](AFFE_CHAR_MECA.md)
- Values that vary in time or space: `AFFE_CHAR_CINE_F` with [DEFI_FONCTION](DEFI_FONCTION.md)
  functions (`upstream/astest/ssla200a.comm:446`)
- Next steps: `MECA_STATIQUE` (`EXCIT`), then `CALC_CHAMP(FORCE='REAC_NODA')` for reactions
- Example: `upstream/astest/gcpc002c.comm` (line 36)
- Example: `upstream/astest/ssls106a.comm` (line 44)
- Example: `upstream/astest/ssls108j.comm` (line 38)
