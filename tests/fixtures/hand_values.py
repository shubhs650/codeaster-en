"""Hand-calculated reference values for the solver fixtures (task 4.1).

Each fixture's ``run.comm`` tests its results with ``TEST_RESU`` against the values computed
here, and ``input/run.json`` records them under ``checks``. ``tests/test_fixtures.py`` asserts
that the three stay in agreement. Run this file to print the values::

    python tests/fixtures/hand_values.py

Only numpy and h5py are needed (the MED mesh is read as plain HDF5).
"""

from __future__ import annotations

import math
from pathlib import Path

import h5py
import numpy as np

FIXTURES = Path(__file__).resolve().parent

# Eigenvalue roots lambda_n of the clamped-free beam, cos(l) cosh(l) = -1.
CANTILEVER_ROOTS = (1.875104068712, 4.694091132974, 7.854757438238, 10.995540734875)


def navier_square_plate(nu: float, terms: int = 400) -> tuple[float, float]:
    """Simply supported square plate, uniform load: centre coefficients (alpha, beta).

    w_max = alpha q a^4 / D and M_x = M_y = beta q a^2 at the centre (Navier double series,
    Timoshenko & Woinowsky-Krieger, Theory of Plates and Shells, sec. 30).
    """
    sw = sm = 0.0
    for m in range(1, terms, 2):
        for n in range(1, terms, 2):
            sign = (-1) ** ((m + n) // 2 - 1)
            den = m * n * (m * m + n * n) ** 2
            sw += sign / den
            sm += sign * (m * m + nu * n * n) / den
    return 16.0 / math.pi**6 * sw, 16.0 / math.pi**4 * sm


def plate_rigidity(e: float, nu: float, t: float) -> float:
    """Flexural rigidity D = E t^3 / (12 (1 - nu^2))."""
    return e * t**3 / (12.0 * (1.0 - nu**2))


def cantilever_frequencies(
    e: float, rho: float, length: float, b: float, h: float, count: int
) -> list[tuple[float, str, int]]:
    """Lowest Euler-Bernoulli bending frequencies of a rectangular cantilever, both planes.

    Returns ``(f [Hz], plane, n)`` sorted by frequency; plane "Z" bends about the width b
    (I = b h^3 / 12), plane "Y" about the depth h (I = h b^3 / 12).
    """
    area = b * h
    out = []
    for plane, inertia in (("Z", b * h**3 / 12.0), ("Y", h * b**3 / 12.0)):
        for n, lam in enumerate(CANTILEVER_ROOTS, start=1):
            f = lam**2 / (2.0 * math.pi * length**2) * math.sqrt(e * inertia / (rho * area))
            out.append((f, plane, n))
    return sorted(out)[:count]


def med_group_names(path: Path) -> set[str]:
    """Names of all groups (on cells or nodes) stored in a MED file."""
    names: set[str] = set()
    with h5py.File(path, "r") as f:

        def visit(name: str, obj: object) -> None:
            if name.endswith("GRO/NOM") and isinstance(obj, h5py.Dataset):
                for row in obj[()]:
                    names.add(bytes(row).decode("ascii").rstrip("\x00 "))

        f["FAS"].visititems(visit)
    return names


def _cell_groups(path: Path) -> dict[int, list[str]]:
    families: dict[int, list[str]] = {}
    with h5py.File(path, "r") as f:
        (fas,) = f["FAS"].values()
        for fam in fas.get("ELEME", {}).values():
            names = [bytes(r).decode("ascii").rstrip("\x00 ") for r in fam["GRO/NOM"][()]]
            families[int(fam.attrs["NUM"])] = names
    return families


def _cells(step: h5py.Group, kind: str, nnod: int) -> tuple[np.ndarray, np.ndarray]:
    grp = step["MAI"][kind]
    conn = grp["NOD"][()].reshape(nnod, -1).T - 1  # MED stores connectivity non-interlaced
    return conn, grp["FAM"][()]


def pressure_resultant(path: Path, groups: tuple[str, ...], pressure: float) -> np.ndarray:
    """Resultant force of a uniform pressure on triangle skin groups of a linear tet mesh.

    The pressure pushes into the solid, against the outward normal of each skin face (the
    orientation ``MODI_MAILLAGE/ORIE_PEAU`` gives). Exact for the faceted mesh, so the
    reaction sum of a converged linear solve must match it to solver precision.
    """
    families = _cell_groups(path)
    with h5py.File(path, "r") as f:
        (mesh,) = f["ENS_MAA"].values()
        (step,) = mesh.values()
        coords = step["NOE/COO"][()].reshape(3, -1).T
        tets, _ = _cells(step, "TE4", 4)
        tris, tri_fam = _cells(step, "TR3", 3)
    owner: dict[tuple[int, ...], int] = {}
    for tet in tets:
        for k in range(4):
            face = tuple(sorted(np.delete(tet, k)))
            owner[face] = tet[k]  # the node opposite this face, inside the solid
    force = np.zeros(3)
    for tri, fam in zip(tris, tri_fam, strict=True):
        if not set(families.get(int(fam), [])) & set(groups):
            continue
        a, b, c = coords[tri]
        normal = 0.5 * np.cross(b - a, c - a)
        inside = coords[owner[tuple(sorted(tri))]]
        if normal @ (inside - a) > 0:
            normal = -normal  # make it outward
        force -= pressure * normal
    return force


def solid_static() -> dict[str, float]:
    """Reaction sum at the base = minus the applied pressure resultant (P = 2 MPa)."""
    mesh = FIXTURES / "solid_static" / "input" / "mesh.med"
    force = pressure_resultant(mesh, ("P_SHELL", "P_NOZZLE"), 2.0)
    return {
        "REAC_DX_SUM": float(abs(force[0])),
        "applied_FX": float(force[0]),
        "applied_FY": float(force[1]),
        "applied_FZ": float(force[2]),
        "analytic_P_pi_ri2": 2.0 * math.pi * 25.0**2,
    }


def shell_static() -> dict[str, float]:
    """Plate a=1000 mm, t=10 mm, E=210000 MPa, nu=0.3, q=0.01 MPa."""
    a, t, e, nu, q = 1000.0, 10.0, 210000.0, 0.3, 0.01
    alpha, beta = navier_square_plate(nu)
    return {
        "W_CENTER": -alpha * q * a**4 / plate_rigidity(e, nu, t),
        "MXX_CENTER": beta * q * a**2,
        "REAC_DZ_SUM": q * a**2,
        "alpha": alpha,
        "beta": beta,
    }


def torsion_constant(b: float, h: float, terms: int = 50) -> float:
    """Saint-Venant torsion constant J of a b x h rectangle (b >= h), series solution.

    J = b h^3 / 3 * (1 - 192 h / (pi^5 b) * sum_{n odd} tanh(n pi b / (2 h)) / n^5)
    (Timoshenko & Goodier, Theory of Elasticity, sec. 109).
    """
    s = sum(math.tanh(n * math.pi * b / (2.0 * h)) / n**5 for n in range(1, terms, 2))
    return b * h**3 / 3.0 * (1.0 - 192.0 * h / (math.pi**5 * b) * s)


def cantilever_torsion_frequency(
    e: float, nu: float, rho: float, length: float, b: float, h: float
) -> float:
    """First torsional frequency of a clamped-free bar, warping ignored.

    f = 1 / (4 L) * sqrt(G J / (rho I_p)), I_p = b h (b^2 + h^2) / 12.
    """
    g = e / (2.0 * (1.0 + nu))
    polar = b * h * (b**2 + h**2) / 12.0
    return math.sqrt(g * torsion_constant(b, h) / (rho * polar)) / (4.0 * length)


def cantilever_axial_frequency(e: float, rho: float, length: float) -> float:
    """First axial frequency of a clamped-free bar, f = sqrt(E / rho) / (4 L)."""
    return math.sqrt(e / rho) / (4.0 * length)


def modal() -> dict[str, float]:
    """Cantilever L=400 mm, b=20 mm (Y), h=10 mm (Z), steel: modes 1-5 bend, mode 6 twists."""
    e, nu, rho, length, b, h = 210000.0, 0.3, 7.85e-9, 400.0, 20.0, 10.0
    bending = cantilever_frequencies(e, rho, length, b, h, 5)
    out = {f"F{i}_BENDING_{plane}{n}": f for i, (f, plane, n) in enumerate(bending, start=1)}
    out["F6_TORSION_1"] = cantilever_torsion_frequency(e, nu, rho, length, b, h)
    out["next_bending"] = cantilever_frequencies(e, rho, length, b, h, 6)[5][0]
    out["axial_1"] = cantilever_axial_frequency(e, rho, length)
    out["mass"] = rho * length * b * h
    return out


ALL = {"solid_static": solid_static, "shell_static": shell_static, "modal": modal}

if __name__ == "__main__":
    for case, func in ALL.items():
        print(case)
        for key, value in func().items():
            print(f"  {key:20s} {value:.6g}")
