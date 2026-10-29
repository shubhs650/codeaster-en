"""English API that writes a French ``.comm`` file (task 6.1, ARCHITECTURE §4.8).

Method and argument names are English; every command and keyword written to the file is the
solver's French name, unchanged (CLAUDE.md §2.2), and every call is checked against the pinned
catalog before it is added (:class:`codeaster_en.comm.CommandFile`). Values the solver names
itself (field names such as ``SIEQ_NOEU``, components such as ``DX``, group names) are passed
through as given.

Coverage is COMMAND-SET Tier 1 linear static on solids and shells plus the Tier 2 modal path:
the three fixtures in ``tests/fixtures/`` are written by this API
(``tests/fixtures/comm_inputs.py``). Modeling defaults per body kind are ADR-013's; a model has
one modeling family.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from codeaster_en.comm import catalog
from codeaster_en.comm.document import CommandFile
from codeaster_en.comm.syntax import Commented, CommSyntaxError, Concept, Number, Param

# ADR-013: default MODELISATION per body kind, and the modelings a kind may ask for instead.
BODY_KINDS: dict[str, tuple[str, tuple[str, ...]]] = {
    "solid": ("3D", ("3D", "3D_SI")),
    "thin_shell": ("DKT", ("DKT", "DST", "COQUE_3D")),
    "thick_shell": ("DST", ("DST", "DKT", "COQUE_3D")),
    "curved_shell": ("COQUE_3D", ("COQUE_3D", "DKT", "DST")),
    "plane_stress": ("C_PLAN", ("C_PLAN",)),
    "plane_strain": ("D_PLAN", ("D_PLAN",)),
    "axisymmetric": ("AXIS", ("AXIS",)),
}

# Degrees of freedom a clamp fixes, per modeling (translations; rotations on shells).
_CLAMP_DOFS: dict[str, tuple[str, ...]] = {
    "3D": ("DX", "DY", "DZ"),
    "3D_SI": ("DX", "DY", "DZ"),
    "DKT": ("DX", "DY", "DZ", "DRX", "DRY", "DRZ"),
    "DST": ("DX", "DY", "DZ", "DRX", "DRY", "DRZ"),
    "COQUE_3D": ("DX", "DY", "DZ", "DRX", "DRY", "DRZ"),
    "C_PLAN": ("DX", "DY"),
    "D_PLAN": ("DX", "DY"),
    "AXIS": ("DX", "DY"),
}
_SHELLS = {"DKT", "DST", "COQUE_3D"}

# Modal parameters CALC_MODES stores (bibfor/algeline/vpstor.F90), as the modal fixture and
# the results reader's modal table use them.
MODAL_PARAMETERS = (
    "FREQ",
    "MASS_GENE",
    "MASS_EFFE_DX",
    "MASS_EFFE_DY",
    "MASS_EFFE_DZ",
    "MASS_EFFE_UN_DX",
    "MASS_EFFE_UN_DY",
    "MASS_EFFE_UN_DZ",
)

Real = float | int | Number | Param
Groups = str | Sequence[str]


def literal(text: str) -> Number:
    """A number written exactly as ``text`` (``literal("1.0e-3")``)."""
    return Number(float(text), text)


def _real(value: Real) -> float | Number | Param:
    if isinstance(value, Number | Param):
        return value
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise CommSyntaxError(f"expected a number, got {value!r}")
    return float(value)


def _groups(groups: Groups) -> str | tuple[str, ...]:
    """One group as a string, several as a tuple (the form upstream test cases use)."""
    if isinstance(groups, str):
        return groups
    names = tuple(groups)
    if not names:
        raise CommSyntaxError("empty group list")
    return names[0] if len(names) == 1 else names


def _one_or_many(occurrences: list[Any]) -> Any:
    return occurrences[0] if len(occurrences) == 1 else tuple(occurrences)


@dataclass
class Model:
    """A model (``AFFE_MODELE`` result) and the modeling it was given."""

    concept: Concept
    mesh: Concept
    modelisation: str

    @property
    def is_shell(self) -> bool:
        return self.modelisation in _SHELLS


@dataclass
class Restraint:
    """Imposed displacements on element groups (``GROUP_MA``) or node groups (``GROUP_NO``).

    ``dofs`` maps component names (``DX``, ``DRZ``...) to imposed values.
    """

    dofs: Mapping[str, Real]
    groups: Groups | None = None
    node_groups: Groups | None = None

    def keywords(self) -> dict[str, Any]:
        if (self.groups is None) == (self.node_groups is None):
            raise CommSyntaxError("a restraint needs groups or node_groups (one of them)")
        where = (
            {"GROUP_MA": _groups(self.groups)}
            if self.groups is not None
            else {"GROUP_NO": _groups(self.node_groups)}  # type: ignore[arg-type]
        )
        if not self.dofs:
            raise CommSyntaxError("a restraint needs at least one degree of freedom")
        return {**where, **{dof: _real(v) for dof, v in self.dofs.items()}}


@dataclass
class ResultCheck:
    """One ``TEST_RESU`` ``RESU`` occurrence: a computed value checked against a reference.

    Give ``field`` and ``component`` (with ``node_group``, or ``sum=True`` for the sum over the
    whole field, ``TYPE_TEST='SOMM'``), or ``parameter`` (``FREQ``...). Used by fixtures.
    """

    result: Concept
    computed: Real
    reference: Real
    tolerance: Real
    label: str
    step: int = 1
    field: str | None = None
    component: str | None = None
    parameter: str | None = None
    node_group: str | None = None
    sum: bool = False
    reference_type: str = "ANALYTIQUE"
    comment: str | None = None

    def keywords(self) -> dict[str, Any]:
        kw: dict[str, Any] = {"NUME_ORDRE": self.step}
        if self.parameter is not None:
            kw["PARA"] = self.parameter
        kw["RESULTAT"] = self.result
        if self.field is not None:
            kw["NOM_CHAM"] = self.field
        if self.node_group is not None:
            kw["GROUP_NO"] = self.node_group
        if self.component is not None:
            kw["NOM_CMP"] = self.component
        if self.sum:
            kw["TYPE_TEST"] = "SOMM"
        kw["REFERENCE"] = self.reference_type
        kw["VALE_REFE"] = _real(self.reference)
        kw["VALE_CALC"] = _real(self.computed)
        kw["PRECISION"] = _real(self.tolerance)
        kw["LEGENDE"] = self.label
        return kw


@dataclass
class ModalMatrices:
    """Concepts written by :meth:`Builder.modal`."""

    stiffness_elements: Concept
    mass_elements: Concept
    numbering: Concept
    stiffness: Concept
    mass: Concept
    modes: Concept


@dataclass
class Builder:
    """Write a ``.comm`` file with English method names.

    Concept names default to the ones upstream test cases and our fixtures use (``MAIL``,
    ``MODE``, ``MATE``, ``RESU``...); a taken default gets a number (``FIXE2``).
    """

    commands_dir: Path = catalog.DEFAULT_COMMANDS_DIR
    file: CommandFile = field(init=False)
    _started: bool = field(default=False, init=False)
    _ended: bool = field(default=False, init=False)
    _models: dict[str, Model] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.file = CommandFile(self.commands_dir)

    # -- naming and comments -----------------------------------------------------------------

    def _name(self, name: str | None, default: str) -> str:
        if name is not None:
            return name
        taken = self.file._names
        if default not in taken:
            return default
        n = 2
        while f"{default}{n}" in taken:
            n += 1
        return f"{default}{n}"

    def header(self, text: str) -> None:
        """Comment block at the top of the file (call again for a second block)."""
        self.file.add_header(text)

    def comment(self, text: str) -> None:
        """Comment lines above the next statement."""
        self.file.add_comment(text)

    def _call(self, command: str, result: str | Concept | None = None, **kw: Any) -> Any:
        if self._ended:
            raise CommSyntaxError("the file is already ended (FIN)")
        if not self._started and command != "DEBUT":
            self.start()
        return self.file.call(command, result, **kw)

    # -- session -----------------------------------------------------------------------------

    def start(
        self,
        *,
        language: str | None = "EN",
        testing: bool = False,
        alarms_as_errors: bool = False,
        ignore_alarms: Sequence[str] = (),
    ) -> None:
        """``DEBUT``. ``language='EN'`` loads the English message catalog (ADR-004, ADR-018);
        ``testing`` is ``CODE='OUI'`` (test-case mode); ``alarms_as_errors`` turns every alarm
        into an error (``ERREUR=_F(ALARME='EXCEPTION')``); ``ignore_alarms`` lists message IDs
        whose alarms are not shown.
        """
        if self._started:
            raise CommSyntaxError("DEBUT is already written")
        if alarms_as_errors and ignore_alarms:
            # Utmess raises the alarm as an error before IGNORE_ALARM is consulted (task 4.2).
            raise CommSyntaxError("ignore_alarms has no effect with alarms_as_errors")
        kw: dict[str, Any] = {}
        if testing:
            kw["CODE"] = "OUI"
        if alarms_as_errors:
            kw["ERREUR"] = {"ALARME": "EXCEPTION"}
        if ignore_alarms:
            kw["IGNORE_ALARM"] = tuple(ignore_alarms)
        if language is not None:
            kw["LANG"] = language
        self._started = True
        self._call("DEBUT", **kw)

    def param(self, name: str, value: Any, note: str | None = None) -> Param:
        """A named constant (``P = 2.0  # note``) to pass as a value to later calls."""
        if not self._started:
            raise CommSyntaxError("call start() before defining constants")
        return self.file.param(name, value, note)

    def end(self) -> None:
        """``FIN``."""
        self._call("FIN")
        self._ended = True

    def text(self) -> str:
        """The file as text; ``FIN()`` is added if :meth:`end` was not called."""
        if not self._ended:
            self.end()
        return self.file.text()

    def write(self, path: str | Path) -> str:
        """Write the file to ``path`` and return its text."""
        text = self.text()
        Path(path).write_text(text, encoding="utf-8")
        return text

    # -- mesh --------------------------------------------------------------------------------

    def read_mesh(self, *, unit: int = 20, name: str | None = None) -> Concept:
        """``LIRE_MAILLAGE`` from a MED file on logical unit ``unit`` (the ``.export`` maps it)."""
        return self._call(
            "LIRE_MAILLAGE",
            self._name(name, "MAIL"),
            result_type="maillage_sdaster",
            FORMAT="MED",
            UNITE=unit,
        )

    def node_groups(
        self, mesh: Concept, *, from_groups: Groups | None = None, from_all_groups: bool = False
    ) -> Concept:
        """``DEFI_GROUP`` ``CREA_GROUP_NO``: node groups named after element groups."""
        if (from_groups is None) == (not from_all_groups):
            raise CommSyntaxError("give from_groups or from_all_groups=True (one of them)")
        occ = (
            {"TOUT_GROUP_MA": "OUI"} if from_all_groups else {"GROUP_MA": _groups(from_groups)}  # type: ignore[arg-type]
        )
        return self._call("DEFI_GROUP", mesh, reuse=True, MAILLAGE=mesh, CREA_GROUP_NO=occ)

    def orient_skin(self, mesh: Concept, groups: Groups) -> Concept:
        """``MODI_MAILLAGE`` ``ORIE_PEAU``: skin elements' normals point out of the solid.

        Needed before a pressure on those faces, or its sign depends on the mesher.
        """
        return self._call(
            "MODI_MAILLAGE",
            mesh,
            reuse=True,
            MAILLAGE=mesh,
            ORIE_PEAU={"GROUP_MA_PEAU": _groups(groups)},
        )

    def orient_shell_normals(
        self, mesh: Concept, group: Groups, *, normal: Sequence[Real], at_node_group: str
    ) -> Concept:
        """``MODI_MAILLAGE`` ``ORIE_NORM_COQUE``: shell normals made consistent with ``normal``
        at the node of ``at_node_group``."""
        return self._call(
            "MODI_MAILLAGE",
            mesh,
            reuse=True,
            MAILLAGE=mesh,
            ORIE_NORM_COQUE={
                "GROUP_MA": _groups(group),
                "GROUP_NO": at_node_group,
                "VECT_NORM": tuple(_real(v) for v in normal),
            },
        )

    # -- model, materials, element properties ------------------------------------------------

    def model(
        self,
        mesh: Concept,
        kind: str,
        *,
        groups: Groups | None = None,
        modelisation: str | None = None,
        name: str | None = None,
    ) -> Model:
        """``AFFE_MODELE`` with one modeling family (ADR-013).

        ``kind`` is a key of :data:`BODY_KINDS`; its default modeling is used unless
        ``modelisation`` names another one of the same family. ``groups=None`` models every
        element of the mesh (``TOUT='OUI'``), which also gives the skin faces of a solid the
        boundary elements a pressure needs.
        """
        if kind not in BODY_KINDS:
            raise CommSyntaxError(f"unknown body kind {kind!r} (one of {', '.join(BODY_KINDS)})")
        default, allowed = BODY_KINDS[kind]
        chosen = modelisation or default
        if chosen not in allowed:
            raise CommSyntaxError(
                f"{chosen} is not a {kind} modeling (one of {', '.join(allowed)}); "
                "a model mixes no modeling families (ADR-013)"
            )
        where = {"TOUT": "OUI"} if groups is None else {"GROUP_MA": _groups(groups)}
        concept = self._call(
            "AFFE_MODELE",
            self._name(name, "MODE"),
            MAILLAGE=mesh,
            AFFE={**where, "PHENOMENE": "MECANIQUE", "MODELISATION": chosen},
        )
        model = Model(concept, mesh, chosen)
        self._models[concept.name] = model
        return model

    def material(
        self,
        name: str,
        *,
        E: Real,
        nu: Real,
        rho: Real | None = None,
        alpha: Real | None = None,
    ) -> Concept:
        """``DEFI_MATERIAU`` ``ELAS``: Young's modulus, Poisson's ratio, density, expansion."""
        elas: dict[str, Any] = {"E": _real(E), "NU": _real(nu)}
        if rho is not None:
            elas["RHO"] = _real(rho)
        if alpha is not None:
            elas["ALPHA"] = _real(alpha)
        return self._call("DEFI_MATERIAU", name, ELAS=elas)

    def assign_materials(
        self, mesh: Concept, materials: Mapping[str, Concept], *, name: str | None = None
    ) -> Concept:
        """``AFFE_MATERIAU``: material per element group (``"*"`` for every element)."""
        if not materials:
            raise CommSyntaxError("no material assigned")
        occ = [
            {"TOUT": "OUI", "MATER": m} if group == "*" else {"GROUP_MA": group, "MATER": m}
            for group, m in materials.items()
        ]
        return self._call(
            "AFFE_MATERIAU", self._name(name, "MATE"), MAILLAGE=mesh, AFFE=_one_or_many(occ)
        )

    def shell_properties(
        self,
        model: Model,
        thickness: Mapping[str, Real],
        *,
        reference_angles: tuple[Real, Real] | None = None,
        name: str | None = None,
    ) -> Concept:
        """``AFFE_CARA_ELEM`` ``COQUE``: thickness per shell group; ``reference_angles`` is
        ``ANGL_REP`` (the in-plane reference direction for stresses and forces)."""
        if not model.is_shell:
            raise CommSyntaxError(f"shell properties on a {model.modelisation} model")
        occ = []
        for group, t in thickness.items():
            o: dict[str, Any] = {"GROUP_MA": group, "EPAIS": _real(t)}
            if reference_angles is not None:
                o["ANGL_REP"] = tuple(_real(a) for a in reference_angles)
            occ.append(o)
        return self._call(
            "AFFE_CARA_ELEM",
            self._name(name, "CARA"),
            MODELE=model.concept,
            COQUE=_one_or_many(occ),
        )

    # -- loads and boundary conditions -------------------------------------------------------

    def fix(
        self, model: Model, groups: Groups, *, kinematic: bool = False, name: str | None = None
    ) -> Concept:
        """Clamp element groups: every translation (and rotation on shells) set to zero.

        ``AFFE_CHAR_MECA`` ``DDL_IMPO``, or with ``kinematic=True`` ``AFFE_CHAR_CINE``
        ``MECA_IMPO`` (eliminated, no Lagrange multipliers; static analysis only).
        """
        dofs = dict.fromkeys(_CLAMP_DOFS[model.modelisation], 0.0)
        return self.restrain(
            model, [Restraint(dofs, groups=groups)], kinematic=kinematic, name=name
        )

    def restrain(
        self,
        model: Model,
        restraints: Sequence[Restraint],
        *,
        kinematic: bool = False,
        name: str | None = None,
    ) -> Concept:
        """Imposed displacements, one ``DDL_IMPO`` (or ``MECA_IMPO``) occurrence each."""
        if not restraints:
            raise CommSyntaxError("no restraint given")
        occ = _one_or_many([r.keywords() for r in restraints])
        if kinematic:
            return self._call(
                "AFFE_CHAR_CINE", self._name(name, "FIXE"), MODELE=model.concept, MECA_IMPO=occ
            )
        return self._call(
            "AFFE_CHAR_MECA", self._name(name, "FIXE"), MODELE=model.concept, DDL_IMPO=occ
        )

    def pressure(
        self, model: Model, groups: Groups, value: Real, *, name: str | None = None
    ) -> Concept:
        """``AFFE_CHAR_MECA`` ``PRES_REP``: positive pressure acts against the face normal."""
        return self._call(
            "AFFE_CHAR_MECA",
            self._name(name, "PRESS"),
            MODELE=model.concept,
            PRES_REP={"GROUP_MA": _groups(groups), "PRES": _real(value)},
        )

    # -- analyses ----------------------------------------------------------------------------

    def linear_static(
        self,
        model: Model,
        materials: Concept,
        loads: Sequence[Concept],
        *,
        elements: Concept | None = None,
        solver: str | None = "MUMPS",
        name: str | None = None,
    ) -> Concept:
        """``MECA_STATIQUE`` with the given loads and boundary conditions (``EXCIT``)."""
        if not loads:
            raise CommSyntaxError("a static analysis needs loads")
        kw: dict[str, Any] = {"MODELE": model.concept, "CHAM_MATER": materials}
        if elements is not None:
            kw["CARA_ELEM"] = elements
        kw["EXCIT"] = _one_or_many([{"CHARGE": load} for load in loads])
        if solver is not None:
            kw["SOLVEUR"] = {"METHODE": solver}
        return self._call("MECA_STATIQUE", self._name(name, "RESU"), **kw)

    def compute_fields(
        self,
        result: Concept,
        *,
        stress: str | Sequence[str] | None = None,
        criteria: str | Sequence[str] | None = None,
        strain: str | Sequence[str] | None = None,
        forces: str | Sequence[str] | None = None,
        energy: str | Sequence[str] | None = None,
    ) -> Concept:
        """``CALC_CHAMP`` on ``result`` in place: stress (``CONTRAINTE``), equivalent stress
        criteria (``CRITERES``), strain (``DEFORMATION``), nodal forces and reactions
        (``FORCE``), energy (``ENERGIE``). Field names are the solver's (``SIEQ_NOEU``)."""
        groups = {
            "CONTRAINTE": stress,
            "CRITERES": criteria,
            "DEFORMATION": strain,
            "FORCE": forces,
            "ENERGIE": energy,
        }
        kw = {
            key: v if isinstance(v, str) else tuple(v) for key, v in groups.items() if v is not None
        }
        if not kw:
            raise CommSyntaxError("no field requested")
        return self._call("CALC_CHAMP", result, reuse=True, RESULTAT=result, **kw)

    def modal(
        self,
        model: Model,
        materials: Concept,
        loads: Sequence[Concept],
        *,
        count: int,
        elements: Concept | None = None,
        name: str | None = None,
    ) -> ModalMatrices:
        """Lowest ``count`` natural modes: element matrices (``CALC_MATR_ELEM``), numbering
        (``NUME_DDL``), assembly (``ASSE_MATRICE``) and ``CALC_MODES``
        ``OPTION='PLUS_PETITE'``. ``loads`` are the boundary conditions (``AFFE_CHAR_MECA``)."""
        if not loads:
            raise CommSyntaxError("a modal analysis needs its boundary conditions")
        common: dict[str, Any] = {"MODELE": model.concept, "CHAM_MATER": materials}
        if elements is not None:
            common["CARA_ELEM"] = elements
        common["CHARGE"] = loads[0] if len(loads) == 1 else tuple(loads)
        rigi_el = self._call(
            "CALC_MATR_ELEM",
            self._name(None, "RIGI_EL"),
            result_type="matr_elem_depl_r",
            **common,
            OPTION="RIGI_MECA",
        )
        mass_el = self._call(
            "CALC_MATR_ELEM",
            self._name(None, "MASS_EL"),
            result_type="matr_elem_depl_r",
            **common,
            OPTION="MASS_MECA",
        )
        nume = self._call("NUME_DDL", self._name(None, "NUME"), MATR_RIGI=rigi_el)
        rigi = self._call(
            "ASSE_MATRICE",
            self._name(None, "RIGI"),
            result_type="matr_asse_depl_r",
            MATR_ELEM=rigi_el,
            NUME_DDL=nume,
        )
        mass = self._call(
            "ASSE_MATRICE",
            self._name(None, "MASS"),
            result_type="matr_asse_depl_r",
            MATR_ELEM=mass_el,
            NUME_DDL=nume,
        )
        modes = self._call(
            "CALC_MODES",
            self._name(name, "MODES"),
            result_type="mode_meca",
            MATR_RIGI=rigi,
            MATR_MASS=mass,
            OPTION="PLUS_PETITE",
            CALC_FREQ={"NMAX_FREQ": count},
        )
        return ModalMatrices(rigi_el, mass_el, nume, rigi, mass, modes)

    # -- post-processing and output ----------------------------------------------------------

    def resultant(
        self,
        result: Concept,
        node_groups: Groups,
        *,
        title: str,
        field: str = "REAC_NODA",
        components: Sequence[str] = ("DX", "DY", "DZ"),
        name: str | None = None,
    ) -> Concept:
        """``POST_RELEVE_T`` ``RESULTANTE``: sum of ``field`` over node groups, as a table."""
        return self._call(
            "POST_RELEVE_T",
            self._name(name, "REAC"),
            ACTION={
                "OPERATION": "EXTRACTION",
                "INTITULE": title,
                "RESULTAT": result,
                "NOM_CHAM": field,
                "GROUP_NO": _groups(node_groups),
                "RESULTANTE": tuple(components),
            },
        )

    def mass_properties(
        self,
        model: Model,
        materials: Concept,
        *,
        elements: Concept | None = None,
        name: str | None = None,
    ) -> Concept:
        """``POST_ELEM`` ``MASS_INER``: mass, center of gravity and inertia of the model."""
        kw: dict[str, Any] = {"MODELE": model.concept, "CHAM_MATER": materials}
        if elements is not None:
            kw["CARA_ELEM"] = elements
        return self._call(
            "POST_ELEM",
            self._name(name, "MASSE"),
            result_type="table_sdaster",
            **kw,
            MASS_INER={"TOUT": "OUI"},
        )

    def modal_parameters(
        self,
        modes: Concept,
        *,
        parameters: Sequence[str] = MODAL_PARAMETERS,
        name: str | None = None,
    ) -> Concept:
        """``RECU_TABLE``: frequency, generalized and effective masses of each mode."""
        return self._call(
            "RECU_TABLE", self._name(name, "PARA"), CO=modes, NOM_PARA=tuple(parameters)
        )

    def print_table(self, table: Concept, *, unit: int, separator: str = ",") -> None:
        """``IMPR_TABLE`` ``FORMAT='TABLEAU'`` to logical unit ``unit``."""
        self._call("IMPR_TABLE", TABLE=table, FORMAT="TABLEAU", SEPARATEUR=separator, UNITE=unit)

    def write_med(
        self,
        result: Concept,
        fields: str | Sequence[str],
        *,
        unit: int = 80,
        elements: Concept | None = None,
    ) -> None:
        """``IMPR_RESU`` ``FORMAT='MED'``: the given fields of ``result`` to logical unit
        ``unit``. Pass the shell ``elements`` so shell fields are written in their layers."""
        resu: dict[str, Any] = {"RESULTAT": result}
        if elements is not None:
            resu["CARA_ELEM"] = elements
        resu["NOM_CHAM"] = fields if isinstance(fields, str) else tuple(fields)
        self._call("IMPR_RESU", FORMAT="MED", UNITE=unit, RESU=resu)

    def test_results(self, checks: Sequence[ResultCheck]) -> None:
        """``TEST_RESU`` (fixtures only): one ``RESU`` occurrence per check."""
        if not checks:
            raise CommSyntaxError("no check given")
        occ = [Commented(c.keywords(), c.comment) if c.comment else c.keywords() for c in checks]
        self._call("TEST_RESU", RESU=tuple(occ))
