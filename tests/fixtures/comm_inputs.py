"""The fixtures' ``input/run.comm`` files, written with the English builder (task 6.1).

``tests/test_comm.py`` checks that each function returns the committed ``run.comm`` byte for
byte. To change a fixture command file, change it here and run
``python tests/fixtures/comm_inputs.py`` from the repository root, which rewrites the three
files (the committed solver outputs refer to their line numbers, so rerun the fixtures too).
"""

from __future__ import annotations

import sys
from pathlib import Path

from codeaster_en.comm import Builder, Restraint, ResultCheck, Spring, literal

FIXTURES = Path(__file__).resolve().parent


def solid_static() -> str:
    b = Builder()
    b.header(
        "solid_static -- cylindrical shell with a radial nozzle under internal pressure.\n"
        "codeaster-en test fixture (task 4.1). Units: mm, N, MPa.\n"
        "Geometry: shell Ri=100 Ro=120 H=300 (axis Z); nozzle ri=25 ro=35 on +X at Z=150, "
        "open end at X=220.\n"
        "Base (Z=0) fully fixed; internal pressure P on the shell inner wall and the nozzle "
        "bore.\n"
        "Check: the reaction sum at the base balances the applied pressure resultant. With an "
        "open\n"
        "nozzle end the resultant is P * (area of the bore opening) along -X; see run.json "
        '"checks".\n'
        "Modelled on astest forma01a (LIRE_MAILLAGE MED, ORIE_PEAU, PRES_REP, CALC_CHAMP "
        "SIEQ_NOEU)\n"
        "and zzzz341b (POST_RELEVE_T RESULTANTE on REAC_NODA).\n"
        "VALE_CALC values are the solver's own results from the first run (task 4.2, "
        "code_aster\n"
        "17.4.22 image, see ADR-011); TEST_RESU checks them at the default TOLE_MACHINE."
    )
    b.start(language=None, testing=True, alarms_as_errors=True)
    p = b.param("P", 2.0, note="internal pressure [MPa]")
    mesh = b.read_mesh()
    b.node_groups(mesh, from_groups="BASE")
    b.orient_skin(mesh, ["P_SHELL", "P_NOZZLE"])
    b.comment(
        'TOUT="OUI" so the pressure faces (TRIA3 skin cells) get boundary elements, as in forma01a.'
    )
    model = b.model(mesh, "solid")
    steel = b.material("ACIER", E=210000.0, nu=0.3)
    mate = b.assign_materials(mesh, {"SOLID": steel})
    fixed = b.fix(model, "BASE")
    press = b.pressure(model, ["P_SHELL", "P_NOZZLE"], p)
    resu = b.linear_static(model, mate, [fixed, press])
    b.compute_fields(
        resu,
        stress=("SIGM_ELNO", "SIGM_NOEU"),
        criteria=("SIEQ_ELNO", "SIEQ_NOEU"),
        forces="REAC_NODA",
    )
    reac = b.resultant(resu, "BASE", title="REAC_BASE")
    b.print_table(reac, unit=30)
    b.write_med(resu, ("DEPL", "SIGM_NOEU", "SIEQ_NOEU", "REAC_NODA"))
    b.comment(
        "Reaction sum over the whole REAC_NODA field (non-zero only on the fixed base nodes).\n"
        "TYPE_TEST sums the whole field; GROUP_NO is not combined with it (see "
        "bibfor/test/trresu.F90).\n"
        "The reference is signed: REAC_NODA is the support reaction, so its sum is +X, "
        "opposite to the\n"
        "applied resultant along -X. Confirmed by the first run (task 4.2): DX sum = +3891.64 N."
    )
    b.test_results(
        [
            ResultCheck(
                resu,
                field="REAC_NODA",
                component="DX",
                sum=True,
                reference=3891.64,
                computed=3891.6428187786923,
                tolerance=literal("1.0e-3"),
                label="REAC_DX_SUM",
            )
        ]
    )
    return b.text()


def shell_static() -> str:
    b = Builder()
    b.header(
        "shell_static -- simply supported square plate under uniform pressure (DKT, QUAD4 -> "
        "DKQ).\n"
        "codeaster-en test fixture (task 4.1). Units: mm, N, MPa.\n"
        "Plate a=1000, thickness t=10, E=210000, NU=0.3, pressure q=0.01 on the whole plate.\n"
        "Edges: DZ=0 (hard simple support, rotations free); two corners restrain in-plane "
        "rigid motion.\n"
        "Reference: Navier double series (Timoshenko & Woinowsky-Krieger, Theory of Plates "
        "and\n"
        "Shells, 2nd ed., sec. 30 and table 8): w_max = alpha q a^4 / D, M_x = beta q a^2 at "
        "the centre.\n"
        "Modelled on astest ssls101n (DKT, ORIE_NORM_COQUE, PRES_REP, TEST_RESU on DEPL DZ).\n"
        "VALE_CALC values are the solver's own results from the first run (task 4.2, "
        "code_aster\n"
        "17.4.22 image, see ADR-011); TEST_RESU checks them at the default TOLE_MACHINE."
    )
    b.comment(
        "The Gmsh mesh stores the point groups (CENTER, CORNER_A, CORNER_B) as POI1 cells on "
        "plate\n"
        'nodes, which the LIRE_MAILLAGE mesh check reports as alarm MODELISA8_14 ("POI1 cell '
        "included\n"
        'in another"). That is intended, so the alarm is ignored. ERREUR=_F(ALARME="EXCEPTION")'
        " cannot\n"
        "be kept with it: Utmess.py turns the alarm into an error before IGNORE_ALARM is "
        "consulted\n"
        "(seen in the first run, task 4.2). Any other alarm still shows in run.mess as <A> and "
        "makes\n"
        "the job diagnostic <A>_ALARM instead of OK, which tests/test_fixture_outputs.py rejects."
    )
    b.start(language=None, testing=True, ignore_alarms=["MODELISA8_14"])
    q = b.param("Q", 0.01, note="uniform pressure [MPa]")
    t = b.param("T", 10.0, note="thickness [mm]")
    mesh = b.read_mesh()
    b.node_groups(mesh, from_all_groups=True)
    b.comment("Mesh normals already point to +Z; this makes the orientation explicit and checked.")
    b.orient_shell_normals(mesh, "PLATE", normal=(0.0, 0.0, 1.0), at_node_group="CENTER")
    model = b.model(mesh, "thin_shell", groups="PLATE")
    cara = b.shell_properties(model, {"PLATE": t}, reference_angles=(0.0, 0.0))
    steel = b.material("ACIER", E=210000.0, nu=0.3)
    mate = b.assign_materials(mesh, {"PLATE": steel})
    supports = b.restrain(
        model,
        [
            Restraint({"DZ": 0.0}, groups="EDGES"),
            Restraint({"DX": 0.0, "DY": 0.0}, node_groups="CORNER_A"),
            Restraint({"DY": 0.0}, node_groups="CORNER_B"),
        ],
        name="APPUI",
    )
    b.comment("Positive PRES acts against the element normal (+Z), i.e. downward (as in ssls101n).")
    press = b.pressure(model, "PLATE", q)
    resu = b.linear_static(model, mate, [supports, press], elements=cara)
    b.compute_fields(resu, stress=("EFGE_ELNO", "EFGE_NOEU"), forces="REAC_NODA")
    reac = b.resultant(resu, "EDGES", title="REAC_EDGES")
    b.print_table(reac, unit=30)
    b.write_med(resu, ("DEPL", "EFGE_NOEU", "REAC_NODA"), elements=cara)
    b.test_results(
        [
            ResultCheck(
                resu,
                field="DEPL",
                node_group="CENTER",
                component="DZ",
                reference=-2.11242,
                computed=-2.112263828055923,
                tolerance=literal("1.0e-2"),
                label="W_CENTER",
                comment="Centre deflection: w = alpha q a^4 / D, alpha = 0.00406235 (NU=0.3), "
                "D = E t^3/(12(1-NU^2)).",
            ),
            ResultCheck(
                resu,
                field="EFGE_NOEU",
                node_group="CENTER",
                component="MXX",
                reference=-478.864,
                computed=-479.645314641979,
                tolerance=literal("3.0e-2"),
                label="MXX_CENTER",
                comment="Centre bending moment per unit length: M_x = -beta q a^2, beta = "
                "0.0478864 (NU=0.3).\n"
                "Negative: in the first run (task 4.2) EFGE_NOEU MXX = MYY < 0 at the centre "
                "while the\n"
                "plate sags (DZ < 0), so the sagging moment is negative in code_aster's "
                "convention.",
            ),
            ResultCheck(
                resu,
                field="REAC_NODA",
                component="DZ",
                sum=True,
                reference=10000.0,
                computed=9999.999999999982,
                tolerance=literal("1.0e-3"),
                label="REAC_DZ_SUM",
                comment="Reaction sum = +q a^2 (whole REAC_NODA field; only supported nodes "
                "carry reactions).\n"
                "Positive: REAC_NODA is the support reaction, opposite to the -Z load (first "
                "run, 4.2).",
            ),
        ]
    )
    return b.text()


# (mode, reference frequency literal, computed frequency, tolerance literal, label)
_MODAL_CHECKS = (
    (1, "52.2198", 52.3396441683678, "2.0e-2", "F1_BENDING_Z1"),
    (2, "104.440", 104.42992528937033, "2.0e-2", "F2_BENDING_Y1"),
    (3, "327.256", 327.0652475459293, "2.0e-2", "F3_BENDING_Z2"),
    (4, "654.512", 646.9886423229167, "2.0e-2", "F4_BENDING_Y2"),
    (5, "916.326", 911.6795505473701, "3.0e-2", "F5_BENDING_Z3"),
    (6, "1485.22", 1497.0292704690783, "3.0e-2", "F6_TORSION_1"),
)


def modal() -> str:
    b = Builder()
    b.header(
        "modal -- 3D cantilever beam, first 6 natural frequencies (HEXA20).\n"
        "codeaster-en test fixture (task 4.1). Units: mm, N, MPa, tonne, s (density in "
        "t/mm3).\n"
        "Beam L=400 along X, section b=20 (Y) x h=10 (Z), steel E=210000, NU=0.3, "
        "RHO=7.85e-9.\n"
        "Face X=0 clamped. Reference: Euler-Bernoulli cantilever,\n"
        "  f_n = lambda_n^2 / (2 pi L^2) * sqrt(E I / (RHO A)),\n"
        "  lambda_n = 1.8751, 4.6941, 7.8548, 10.9955; I = b h^3/12 (bending in Z) or h b^3/12 "
        "(in Y).\n"
        "Mode 6 is the first torsion mode, f = 1/(4L) sqrt(G J / (RHO Ip)), Saint-Venant J "
        "(warping\n"
        "ignored). Expected order: Z1, Y1, Z2, Y2, Z3, T1 (Z4 ~ 1.80 kHz and axial ~ 3.2 kHz "
        "are higher).\n"
        "Modelled on astest sdlv100a (CALC_MATR_ELEM/NUME_DDL/ASSE_MATRICE, POST_ELEM "
        "MASS_INER,\n"
        'TEST_RESU on PARA="FREQ") and sdll05a (CALC_MODES OPTION="PLUS_PETITE", NMAX_FREQ).\n'
        "VALE_CALC values are the solver's own results from the first run (task 4.2, "
        "code_aster\n"
        "17.4.22 image, see ADR-011); TEST_RESU checks them at the default TOLE_MACHINE."
    )
    b.start(language=None, testing=True, alarms_as_errors=True)
    mesh = b.read_mesh()
    model = b.model(mesh, "solid", groups="BEAM")
    steel = b.material("ACIER", E=210000.0, nu=0.3, rho=literal("7.85e-9"))
    mate = b.assign_materials(mesh, {"BEAM": steel})
    clamp = b.fix(model, "CLAMP", name="ENCAS")
    b.comment("Mass and inertia of the model: mass = RHO * b * h * L = 6.28e-4 t.")
    mass = b.mass_properties(model, mate)
    b.print_table(mass, unit=30)
    modes = b.modal(model, mate, [clamp], count=6).modes
    b.comment(
        "CALC_MODES scales each shape to a largest component of 1 (bibfor/algeline/vppara.F90); "
        "NORM_MODE\n"
        "rescales them to a unit generalized mass, the usual form for modal superposition "
        "(task 6.4)."
    )
    b.normalize_modes(modes)
    b.write_med(modes, "DEPL")
    b.comment(
        "Modal parameters stored by CALC_MODES (bibfor/algeline/vpstor.F90), printed for the "
        "modal\n"
        "table of the results reader and the report (task 4.5): frequency, generalized mass "
        "and the\n"
        "effective masses per direction. RECU_TABLE with NOM_PARA as in astest zzzz399a."
    )
    para = b.modal_parameters(modes)
    b.print_table(para, unit=31)
    b.test_results(
        [
            ResultCheck(
                modes,
                step=mode,
                parameter="FREQ",
                reference=literal(ref),
                computed=calc,
                tolerance=literal(tol),
                label=label,
            )
            for mode, ref, calc, tol, label in _MODAL_CHECKS
        ]
        + [
            ResultCheck(
                modes,
                step=1,
                parameter="MASS_GENE",
                reference=1.0,
                computed=1.0,
                tolerance=literal("1.0e-6"),
                label="M1_MASS_GENE",
                comment="Generalized mass of mode 1 after NORM_MODE NORME='MASS_GENE'.",
            )
        ]
    )
    return b.text()


# (component, hand value, solver value from the first run); hand values from hand_values.py.
_LOADS_CHECKS = (
    ("DX", -828.0, -828.000000000001),
    ("DY", -500.39, -500.38999999999965),
    ("DZ", 654.017, 654.017),
)


def solid_loads() -> str:
    b = Builder()
    b.header(
        "solid_loads -- steel block on its base under the Tier 2 loads (task 6.4).\n"
        "codeaster-en test fixture. Units: mm, N, MPa, tonne, s (density in t/mm3).\n"
        "Block 200 (X) x 100 (Y) x 100 (Z), HEXA8, steel E=210000, NU=0.3, RHO=7.85e-9; "
        "base Z=0 clamped.\n"
        "Loads: gravity 9810 mm/s2 along -Z; rotation 20 rad/s about Z through the origin; "
        "water\n"
        "(1e-9 t/mm3, free surface Z=1000) on the face Y=0; F=(200, 0, -500) N and "
        "M=(0, 0, 2.0e4) N.mm\n"
        "at the remote point MASTER (100, 50, 200), spread over the top face by RBE3; a "
        "1000 N/mm spring\n"
        "from (200, 50, 50) to a fixed ground node at (250, 50, 50).\n"
        "Check: the REAC_NODA sum over the whole field is minus the sum of the applied forces "
        "(see\n"
        'run.json "checks" and hand_values.py). Modelled on astest zzzz144a (DIS_TR point, '
        "LIAISON_RBE3,\n"
        "FORCE_NODALE), sdnv138c (pressure FORMULE), erreu01a (ROTATION) and forma01d "
        "(ENV_SPHERE).\n"
        "VALE_CALC values are the solver's own results from the first run (task 6.4c)."
    )
    b.start(language=None, testing=True, alarms_as_errors=True)
    mesh = b.read_mesh()
    b.node_groups(mesh, from_groups=("BASE", "TOP", "MASTER"))
    b.comment(
        "The free end of the spring is not a mesh group: a POI1 there would be included in "
        "the SEG2\n"
        "and raise alarm MODELISA8_14."
    )
    b.node_group_at(mesh, "GROUND", (250.0, 50.0, 50.0), tolerance=0.1)
    b.orient_skin(mesh, "WET")
    model = b.model(mesh, "solid", springs="SPRING", remote_points="MASTER")
    steel = b.material("ACIER", E=210000.0, nu=0.3, rho=literal("7.85e-9"))
    mate = b.assign_materials(mesh, {"BLOCK": steel})
    cara = b.element_properties(model, springs={"SPRING": Spring((1000.0, 1000.0, 1000.0))})
    fixed = b.fix(model, "BASE")
    ground = b.restrain(
        model, [Restraint({"DX": 0.0, "DY": 0.0, "DZ": 0.0}, node_groups="GROUND")], name="SOL"
    )
    remote = b.remote_load(
        model, "MASTER", "TOP", force=(200.0, 0.0, -500.0), moment=(0.0, 0.0, 2.0e4)
    )
    weight = b.gravity(model, acceleration=9810.0, groups="BLOCK")
    spin = b.rotation(model, speed=20.0, axis=(0.0, 0.0, 1.0), groups="BLOCK")
    b.comment("Water pressure rho g (h - Z) in MPa: rho = 1e-9 t/mm3, g = 9810 mm/s2, h = 1000 mm.")
    water = b.hydrostatic_pressure(
        model, "WET", density=literal("1.0e-9"), gravity=9810.0, free_surface=1000.0
    )
    resu = b.linear_static(model, mate, [fixed, ground, remote, weight, spin, water], elements=cara)
    b.compute_fields(resu, criteria="SIEQ_NOEU", forces="REAC_NODA")
    reac = b.resultant(resu, ("BASE", "GROUND"), title="REAC_SUPPORTS")
    b.print_table(reac, unit=30)
    b.comment(
        "Moment of the support reactions about the base center (100, 50, 0): minus the moment "
        "of the\n"
        "applied loads, including the remote moment MZ (hand_values.py; checked by "
        "tests/test_fixture_outputs.py)."
    )
    moment = b.resultant(
        resu,
        ("BASE", "GROUND"),
        title="MOMENT_SUPPORTS",
        moment_about=(100.0, 50.0, 0.0),
        name="MOMT",
    )
    b.print_table(moment, unit=32)
    mass = b.mass_properties(model, mate, elements=cara)
    b.print_table(mass, unit=31)
    b.write_med(resu, ("DEPL", "SIEQ_NOEU", "REAC_NODA"), elements=cara)
    b.comment(
        "Reaction sums over the whole REAC_NODA field: minus the applied force. The RBE3 "
        "relations\n"
        "pass forces between TOP and MASTER that cancel in the sum."
    )
    b.test_results(
        [
            ResultCheck(
                resu,
                field="REAC_NODA",
                component=comp,
                sum=True,
                reference=ref,
                computed=calc,
                tolerance=literal("1.0e-4"),
                label=f"REAC_{comp}_SUM",
            )
            for comp, ref, calc in _LOADS_CHECKS
        ]
    )
    return b.text()


CASES = {
    "solid_static": solid_static,
    "shell_static": shell_static,
    "modal": modal,
    "solid_loads": solid_loads,
}


def main() -> int:
    for case, build in CASES.items():
        path = FIXTURES / case / "input" / "run.comm"
        path.write_text(build(), encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
