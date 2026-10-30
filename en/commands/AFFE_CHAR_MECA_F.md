---
command: AFFE_CHAR_MECA_F
upstream: 17.4.26
upstream_commit: 5d2a06d2a4afe589468f96617080e7aabac3e4f2
source: code_aster/Cata/Commands/affe_char_meca_f.py:28
doc_fr: U4.44.01
status: assisted
method: assisted
reviewed_by:
reviewed_on:
generated_by: caen translate command (draft), then authored in session (task 6.4)
examples: [zzzz219a, sslv07c, forma00a]
---

# AFFE_CHAR_MECA_F — assign mechanical loads and BCs (function-valued)

> **Assisted reference.** Written in session from the pinned catalog, the solver source it
> calls, the message catalog, upstream test cases and the committed fixture runs. Every behavior
> claim cites its source. Not reviewed by an engineer.

Assigns mechanical loads and boundary conditions that are functions of one or more parameters.

`AFFE_CHAR_MECA_F` is `AFFE_CHAR_MECA` with functions in place of numbers: each value
(pressure, force component, imposed displacement) is a `DEFI_FONCTION`, `DEFI_NAPPE` or
`FORMULE` of the coordinates `X`, `Y`, `Z` and of time `INST`, evaluated where the load acts. Its
Tier 2 use is a pressure that varies in space, above all hydrostatic pressure
p = ρ g (h − z) on a tank wall or a dam face (`upstream/astest/sdnv138c.comm:173`,
`upstream/astest/forma00a.comm:84`). This is the only way to get a spatially varying load:
`FONC_MULT` in `MECA_STATIQUE` `EXCIT` multiplies a whole load by a function of time only
(docs/OWNER-REVIEW-QUEUE.md, task 2.3c finding). The result is a `char_meca` that
`MECA_STATIQUE` takes in `EXCIT` like any other load. The keywords mirror those of
[AFFE_CHAR_MECA](AFFE_CHAR_MECA.md) (same factor keywords, same components, same checks), so
this reference details `PRES_REP` only.

| Fact | Value |
|---|---|
| Catalog description (fr) | «Affectation de charges et conditions aux limites mécaniques fonction d'un (ou plusieurs) paramètres» |
| Kind | `OPER` |
| Result | `char_meca` |
| Can reuse its input (`reuse=`) | no |
| French reference | U4.44.01 — from en/doc-ids.yaml (status: verified) |
| Scope tier | 2 (docs/COMMAND-SET.md) |
| Key keywords (COMMAND-SET) | `PRES_REP`, `FONC_MULT` |

## Keywords

Top-level simple keywords and `PRES_REP` are expanded below; the other factor keywords are
listed under [Other keywords](#other-keywords).

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `VERI_NORM` | text, optional | `'OUI'` | *normal check*. One of `'OUI'`, `'NON'`. As in [AFFE_CHAR_MECA](AFFE_CHAR_MECA.md): check that the faces under `PRES_REP` have outward normals (`MODELISA8_56`); keep `'OUI'` and orient the skin with `MODI_MAILLAGE ORIE_PEAU` first. |
| `MODELE` | `modele_sdaster`, required | — | *model*. The model the load applies to. |
| `DOUBLE_LAGRANGE` | text, optional | `'OUI'` | *double Lagrange multipliers*. One of `'OUI'`, `'NON'`. As in [AFFE_CHAR_MECA](AFFE_CHAR_MECA.md): two Lagrange multipliers per imposed DOF or relation (`DDL_IMPO`, `LIAISON_*`). No effect on `PRES_REP`. |
| `PRES_REP` | factor keyword, optional, repeatable | — | *distributed pressure*. Applies a pressure to a 2D or 3D continuum domain, or to a domain of shells and pipes, whose imposed values (pressure and/or shear) are given by a function concept. A pressure given by a function on faces of solids (2D boundary elements of a 3D model, edges of a 2D model) or on shells. Positive pressure acts against the outward normal (into the solid), as with `AFFE_CHAR_MECA` `PRES_REP`. The function is evaluated at each Gauss point of each face, with the point's coordinates as `X`, `Y`, `Z` and the time as `INST` (`upstream/bibfor/load_elem/evalPressureSetFuncPara.F90:96`), so a linear variation is followed exactly within each face. Repeat it for faces with different functions (`upstream/astest/epicu03a.comm:1305`). |
| `PRES_REP / TOUT` | text, optional | — | *all (entire mesh)*. One of `'OUI'`. Every face of the model (boundary elements included in the model). Rarely what is wanted for a pressure; name the wetted faces with `GROUP_MA`. |
| `PRES_REP / GROUP_MA` | element group, optional, list | — | *element group*. The loaded faces: the wetted wall of a tank or the upstream face of a dam (`upstream/astest/sdnv138c.comm:188`). They must be modeled: `AFFE_MODELE` with `TOUT='OUI'`, or the skin groups listed. |
| `PRES_REP / FISSURE` | `fiss_xfem`, optional, list of up to 100 | — | An XFEM crack whose faces carry the pressure. Out of scope (XFEM). |
| `PRES_REP / PRES` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional | — | The pressure function, in the model's stress units (MPa in mm/N models). Hydrostatic pressure as a `FORMULE`: `FORMULE(VALE="max(RHO*G*(H-Z), 0.)", NOM_PARA="Z", RHO=..., G=..., H=...)`, with `max` so that the faces above the free surface carry none (`upstream/astest/sdnv138c.comm:173`, in `Y`). Or a piecewise-linear `DEFI_FONCTION` of `Z` (`upstream/astest/forma00a.comm:84`, in `Y`), with `PROL_GAUCHE`/`PROL_DROITE` set if faces lie outside its range. A constant (`DEFI_CONSTANTE`) also works (`upstream/astest/adls102a.comm:255`). |
| `PRES_REP / CISA_2D` | `fonction_sdaster` or `nappe_sdaster` or `formule`, optional | — | *in-plane shear*. In-plane shear on edges of a 2D model, as a function. Not used in Tier 2. |
| `INFO` | integer, optional | `1` | *verbosity*. One of `1`, `2`. `2` prints nothing more than `1` for `FORCE_FACE` in our 17.4 run (`docs/reference-checks/todo-verify/`). |

## Rules

From the catalog `regles` (meanings from `code_aster/Cata/Language/Rules.py`):

- command: at least one of `DDL_IMPO`, `FACE_IMPO`, `LIAISON_DDL`, `FORCE_NODALE`, `FORCE_FACE`, `FORCE_ARETE`, `FORCE_CONTOUR`, `FORCE_INTERNE`, `PRES_REP`, `FORCE_POUTRE`, `VITE_FACE`, `ONDE_PLANE`, `LIAISON_OBLIQUE`, `PRE_EPSI`, `LIAISON_GROUP`, `LIAISON_UNIF`, `FORCE_COQUE`, `LIAISON_COQUE`, `FORCE_TUYAU`, `EFFE_FOND`, `FLUX_THM_REP`, `ECHANGE_THM`, `ECHANGE_THM_HR` must be given (`AU_MOINS_UN`).
- `PRES_REP`: at least one of `TOUT`, `GROUP_MA`, `FISSURE` must be given (`AU_MOINS_UN`).
- `PRES_REP`: if `TOUT` is given, none of `GROUP_MA`, `FISSURE` may be given (`PRESENT_ABSENT`).
- `PRES_REP`: at least one of `PRES`, `CISA_2D` must be given (`AU_MOINS_UN`).

At least one load keyword must be given. Under `PRES_REP`, give the faces (`TOUT`, `GROUP_MA`
or `FISSURE`) and `PRES` or `CISA_2D`.

## Other keywords

The other factor keywords take the same sub-keywords as in [AFFE_CHAR_MECA](AFFE_CHAR_MECA.md), with function concepts as values (sub-keywords are in `en/commands/AFFE_CHAR_MECA_F.json`):

- `DDL_IMPO` — *imposed DOF*: Imposes on nodes one or more values of displacement (or of some associated quantities) given by a function concept.
- `ECHANGE_THM`: Applies to a 2D or 3D continuum domain an exchange condition whose coefficients are functions (hydraulic flux).
- `ECHANGE_THM_HR`: Applies to a 2D or 3D continuum domain an exchange condition in relative humidity whose coefficients are functions (hydraulic flux).
- `EFFE_FOND`: Computes the end effect on a pipe branch (3D modeling) under a pressure whose value is given by a function concept.
- `FACE_IMPO` — *imposed DOF on faces*: Imposes on all the nodes of a face one or more values of displacement (or of some associated quantities) given by a function concept.
- `FLUX_THM_REP`: Applies to a 2D or 3D continuum domain a heat flux and/or a fluid mass supply (hydraulic flux), with flux values given by a function concept.
- `FORCE_ARETE` — *force per unit length on edges*: Applies line forces on an edge of a volume or shell element, with component values given by a function concept.
- `FORCE_CONTOUR` — *force per unit length on 2D edges*: Applies line forces on the boundary of a 2D, AXIS or AXIS_FOURIER domain, with component values given by a function concept.
- `FORCE_COQUE` — *force per unit area on shells*: Applies surface forces on shell elements, with values given by a function concept.
- `FORCE_FACE` — *force per unit area on faces*: Applies surface forces on a face of a volume element, with component values given by a function concept.
- `FORCE_INTERNE`: Applies volume forces (2D or 3D) to a volume domain, with component values given by a function concept.
- `FORCE_NODALE` — *nodal force*: Applies nodal forces to nodes, with component values given by a function concept.
- `FORCE_POUTRE` — *force per unit length on beams*: Applies line forces on beam elements, with values given by a function concept.
- `FORCE_TUYAU`: Applies a pressure on TUYAU elements, with the value given by a function concept.
- `LIAISON_COQUE`: Models the connection between shell elements by linear relations.
- `LIAISON_DDL` — *linear DOF relation*: Defines a linear relation between degrees of freedom of two or more nodes; the values are given by a function concept.
- `LIAISON_GROUP`: Defines the same linear relation between some degrees of freedom of pairs of nodes; the values are given by function concepts.
- `LIAISON_OBLIQUE`: Applies to nodes the same displacement value, defined component by component in any oblique coordinate system; the values are given by a function concept.
- `LIAISON_UNIF` — *uniform DOF coupling*: Imposes the same (unknown) value on DOFs of a set of nodes.
- `ONDE_PLANE`: Imposes a seismic plane-wave load whose value is given by a function concept.
- `PRE_EPSI`: Applies an initial strain load to a 2D, 3D or structural element, with the components of the strain tensor given by a function concept.
- `VITE_FACE`: Imposes velocities on a face, with values given by a function concept.

## Patterns

### Hydrostatic pressure on a dam face, as a formula

Water level `niv_am` is itself a function of time; with a fixed level, replace `niv_am(INST)` by
a number and drop `INST`. The model's vertical axis is `Y`. Source:
`upstream/astest/sdnv138c.comm:173`.

```python
p_am = FORMULE(
    VALE="max(rho_e*ap*(niv_am(INST)-Y),0)",
    NOM_PARA=("Y", "INST"),
    rho_e=rho_e,
    ap=ap,
    niv_am=niv_am,
)
```

```python
PAMONT = AFFE_CHAR_MECA_F(MODELE=MO, PRES_REP=_F(GROUP_MA=("BAR_AMON",), PRES=p_am))
```

### Linear pressure as a tabulated function

200 kPa at y = 0 down to 0 at y = 4. Source: `upstream/astest/forma00a.comm:84`, `:91`.

```python
f_y = DEFI_FONCTION(NOM_PARA="Y", VALE=(0.0, 200000.0, 4.0, 0.0))
```

```python
charg = AFFE_CHAR_MECA_F(MODELE=modl, PRES_REP=_F(GROUP_MA=("LDA",), PRES=f_y))
```

### Body force and face force as functions

Source: `upstream/astest/sslv07c.comm:56`.

```python
CH2 = AFFE_CHAR_MECA_F(
    MODELE=MO, FORCE_INTERNE=_F(TOUT="OUI", FZ=POIDS), FORCE_FACE=_F(GROUP_MA="FACESUP", FZ=FZ)
)
```

### Imposed displacements as functions

Source: `upstream/astest/zzzz219a.comm:69`.

```python
CHMECF = AFFE_CHAR_MECA_F(
    MODELE=MO,
    INFO=2,
    FACE_IMPO=(
        _F(GROUP_MA="GXXXXXX_GAUCHE", SANS_GROUP_NO="N3", DX=DX1, DY=DY1),
        _F(GROUP_MA="GXXXXXX_BAS", SANS_GROUP_NO="N1", DNOR=DNOR1),
        _F(GROUP_MA="GXXXXXX_HAUT", SANS_GROUP_MA="GXXXXXX_GAUCHE", DNOR=DNOR2),
        _F(GROUP_MA="GXXXXXX_DROIT", SANS_GROUP_NO="GXXXXXX_N2N6", DX=DX2, DY=DY2),
    ),
    DDL_IMPO=(_F(GROUP_NO=("N3", "N6", "N2"), DX=DX3), _F(GROUP_NO="N3", DY=DY3)),
)
```

## Pitfalls

- **A function, not a number.** Every value must be a function concept (`DEFI_FONCTION`,
  `DEFI_CONSTANTE`, `FORMULE`, `DEFI_NAPPE`); a plain number is refused by the catalog type
  check. Use `AFFE_CHAR_MECA` for constant values.
- **Out-of-range evaluation stops the run.** A `DEFI_FONCTION` with the default
  `PROL_*='EXCLU'` evaluated at a coordinate outside its abscissas stops with `FONCT0_19` /
  `FONCT0_20` (see [DEFI_FONCTION](DEFI_FONCTION.md)). A `FORMULE` with `max(..., 0)` avoids
  this for faces above the free surface.
- **Parameter names are coordinates.** `NOM_PARA` must be `X`, `Y`, `Z` (and `INST`), the
  names the element routine passes (`evalPressureSetFuncPara.F90:96`); a formula of another
  name is not evaluated with the coordinate. With `NOM_PARA='W'` the solve prints "Evaluation
  failed with: {'X': …, 'INST': 0.0}" and stops on a Python `NameError`, no message ID (`docs/reference-checks/todo-verify/`).
- **Sign.** Positive `PRES` pushes into the solid, against the outward normal, as for
  `AFFE_CHAR_MECA`; water pressure on a wall is positive. Orient the faces (`ORIE_PEAU`) first.
- **`FONC_MULT` is not a spatial function.** The COMMAND-SET "Hydrostatic" row lists `PRES_REP`
  with `FONC_MULT`: `FONC_MULT` scales a load in time; a pressure that varies with depth needs
  this command.

## See also

- French reference: U4.44.01 (the `AFFE_CHAR_MECA` document; from en/doc-ids.yaml, status:
  proposed)
- Catalog: `en/commands/AFFE_CHAR_MECA_F.json` (generated from `upstream/code_aster/Cata/Commands/affe_char_meca_f.py:28`)
- Same keywords with numbers: [AFFE_CHAR_MECA](AFFE_CHAR_MECA.md)
- Before: [DEFI_FONCTION](DEFI_FONCTION.md), [DEFI_CONSTANTE](DEFI_CONSTANTE.md), `FORMULE`,
  [MODI_MAILLAGE](MODI_MAILLAGE.md) (`ORIE_PEAU`)
- Next steps: [MECA_STATIQUE](MECA_STATIQUE.md) (`EXCIT`)
- Example: `upstream/astest/sdnv138c.comm` (line 173)
- Example: `upstream/astest/forma00a.comm` (line 84)
- Example: `upstream/astest/sslv07c.comm` (line 56)
