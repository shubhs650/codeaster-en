---
command: AFFE_MODELE
upstream: 17.4.26
status: machine
---

# AFFE_MODELE — assign a finite-element model to a mesh

Test fixture. Assigns a modeling type to each element group. The word MODELISATION in capitals
is the keyword, and `cell` in code is not prose.

## Keywords

| Keyword | Type / cardinality | Default | Meaning and when to use |
|---|---|---|---|
| `MAILLAGE` | mesh, required | — | The mesh. |
| `AFFE` | factor keyword, 1..n | — | One block per region. |
| `AFFE / TOUT`, `AFFE / GROUP_MA` | `'OUI'` / groups | — | Where the block applies. |
| `AFFE / MODELISATION` | enum, required | — | Element formulation. |

```python
# cell and frame inside code are not checked
MODE = AFFE_MODELE(MAILLAGE=MAIL, AFFE=_F(TOUT='OUI', PHENOMENE='MECANIQUE', MODELISATION='3D'))
```

The keyword table above is the frame of this page. <!-- caen-allow: frame -->
