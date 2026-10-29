"""Typed English builder that writes French ``.comm`` command files (task 6.1, ADR-008).

``Builder`` is the English API; ``CommandFile`` is the layer under it that takes French
command and keyword names and checks each call against the pinned catalog
(``en/commands/<CMD>.json``) as it is added.
"""

from codeaster_en.comm.builder import (
    BODY_KINDS,
    MODAL_PARAMETERS,
    Builder,
    ModalMatrices,
    Model,
    Restraint,
    ResultCheck,
    literal,
)
from codeaster_en.comm.catalog import CatalogError, CommandSpec, load_command
from codeaster_en.comm.document import CommandFile
from codeaster_en.comm.syntax import Commented, CommSyntaxError, Concept, Number, Param

__all__ = [
    "BODY_KINDS",
    "MODAL_PARAMETERS",
    "Builder",
    "CatalogError",
    "CommSyntaxError",
    "CommandFile",
    "CommandSpec",
    "Commented",
    "Concept",
    "ModalMatrices",
    "Model",
    "Number",
    "Param",
    "Restraint",
    "ResultCheck",
    "literal",
    "load_command",
]
