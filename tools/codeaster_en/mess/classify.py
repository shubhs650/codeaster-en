"""Failure classification of a run (docs/CLEARFEA-INTEGRATION.md §5).

ClearFEA bills or refunds a failed run by its class: ``user-model`` (the model or command file
is wrong), ``user-resources`` (time or memory limit), ``platform`` (our side: image, launch,
I/O) and ``unknown`` (no rule yet; charged provisionally and flagged for review).

Rules are keyed by message ID first, then by ``run_aster``'s diagnostic. Every rule names its
evidence: a broken-run fixture under ``tests/fixtures/`` that produced it, or the upstream file
it was read from when no fixture exercises it yet (``TODO(verify)`` until one does).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from codeaster_en.mess.log import ParsedLog


class FailureClass(StrEnum):
    USER_MODEL = "user-model"
    USER_RESOURCES = "user-resources"
    PLATFORM = "platform"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Rule:
    failure_class: FailureClass
    reason: str
    evidence: str


# Message ID of the first error diagnostic -> class.
MESSAGE_RULES: dict[str, Rule] = {
    "MODELISA7_77": Rule(
        FailureClass.USER_MODEL,
        "a group named in the command file does not exist in the mesh",
        "tests/fixtures/broken_missing_group",
    ),
    "FACTOR_11": Rule(
        FailureClass.USER_MODEL,
        "the stiffness matrix is singular (rigid-body motion not restrained, or redundant "
        "conditions)",
        "tests/fixtures/broken_singular_matrix",
    ),
    "SUPERVIS_4": Rule(
        FailureClass.USER_MODEL,
        "a command does not follow its catalog (bad or missing keyword)",
        "tests/fixtures/broken_bad_keyword",
    ),
}

# run_aster diagnostic (run_aster/status.py StateOptions.name) -> class, when no message rule
# applied.
DIAGNOSTIC_RULES: dict[str, Rule] = {
    "<F>_SYNTAX_ERROR": Rule(
        FailureClass.USER_MODEL,
        "the command file is not valid Python",
        "tests/fixtures/broken_python_syntax",
    ),
    "<S>_CPU_LIMIT": Rule(
        FailureClass.USER_RESOURCES,
        "the time limit of the job was reached",
        "upstream run_aster/status.py (TimeLimitError, exit code -9); TODO(verify) with a run",
    ),
    "<S>_MEMORY_ERROR": Rule(
        FailureClass.USER_RESOURCES,
        "the memory limit of the job was reached",
        "upstream run_aster/status.py (MEMOIRE INSUFFISANTE POUR ALLOUER); TODO(verify) with a run",
    ),
    "<F>_ABNORMAL_ABORT": Rule(
        FailureClass.PLATFORM,
        "the solver stopped without a code_aster diagnostic (crash, kill or launch failure)",
        "upstream run_aster/status.py (no error found in the output); TODO(verify) with a run",
    ),
}

SUCCESS_DIAGNOSTICS = ("OK", "<A>_ALARM")


@dataclass(frozen=True)
class Classification:
    failure_class: FailureClass | None  # None: the run succeeded
    reason: str
    message_id: str | None = None
    diagnostic_job: str | None = None
    evidence: str | None = None

    @property
    def failed(self) -> bool:
        return self.failure_class is not None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["failure_class"] = str(self.failure_class) if self.failure_class else None
        return data


def classify(log: ParsedLog | None, exit_code: int | None = None) -> Classification:
    """Class of the run's failure, or ``failure_class=None`` when it succeeded.

    ``log`` is ``None`` when there is no ``.mess`` at all (the job never started), which is a
    platform failure. ``exit_code`` overrides the one found in the log.
    """
    if log is None or not log.events:
        return Classification(
            FailureClass.PLATFORM,
            "no solver log was written",
            evidence="docs/CLEARFEA-INTEGRATION.md §5 (image missing, launch failure)",
        )
    summary = log.summary()
    diag = summary["diagnostic_job"]
    rc = exit_code if exit_code is not None else summary["exit_code"]
    if rc == 0 and (diag is None or diag in SUCCESS_DIAGNOSTICS):
        return Classification(None, "the run ended normally", diagnostic_job=diag)
    first = next(iter(log.errors), None)
    if first is not None and first.message_id in MESSAGE_RULES:
        rule = MESSAGE_RULES[first.message_id]
        return Classification(
            rule.failure_class, rule.reason, first.message_id, diag, rule.evidence
        )
    if diag in DIAGNOSTIC_RULES:
        rule = DIAGNOSTIC_RULES[diag]
        mid = first.message_id if first else None
        return Classification(rule.failure_class, rule.reason, mid, diag, rule.evidence)
    return Classification(
        FailureClass.UNKNOWN,
        "no classification rule matches this failure yet",
        first.message_id if first else None,
        diag,
    )
