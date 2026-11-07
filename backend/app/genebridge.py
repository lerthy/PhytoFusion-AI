"""GeneBridge: explainable, categorical gene compatibility assessment.

Design rules (see docs/SCIENTIFIC_GUIDELINES.md):
- No percentages or numeric "compatibility scores". Output is categorical.
- Unknown stays unknown. Missing information is reported, never guessed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .evidence import EvidenceLevel

SequenceRelationship = Literal["related", "weakly_related", "unknown"]
FunctionalEvidence = Literal["characterized", "predicted"]
PathwayCompleteness = Literal["supported", "incomplete", "unknown"]
ExpressionCompatibility = Literal["supporting", "conflicting", "unavailable"]
GenomicContext = Literal["characterized", "uncertain"]


@dataclass(frozen=True)
class AssessmentInput:
    sequence: SequenceRelationship
    functional: FunctionalEvidence
    pathway: PathwayCompleteness
    expression: ExpressionCompatibility
    context: GenomicContext


@dataclass(frozen=True)
class Assessment:
    level: EvidenceLevel
    deserves_investigation: bool
    missing_information: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    explanation: str = ""


def assess(data: AssessmentInput) -> Assessment:
    missing: list[str] = []
    concerns: list[str] = []

    if data.sequence == "unknown":
        missing.append("sequence relationship between host and donor gene")
    if data.functional == "predicted":
        missing.append("experimental characterisation of gene function")
    if data.pathway == "unknown":
        missing.append("host pathway completeness")
    if data.expression == "unavailable":
        missing.append("expression data")
    if data.context == "uncertain":
        missing.append("genomic context (location, clusters, duplications)")

    if data.sequence == "weakly_related":
        concerns.append("host and donor genes are only weakly related")
    if data.pathway == "incomplete":
        concerns.append("host lacks pathway components needed by the donor enzyme")
    if data.expression == "conflicting":
        concerns.append("expression evidence conflicts between host and donor")

    all_favourable = (
        data.sequence == "related"
        and data.functional == "characterized"
        and data.pathway == "supported"
        and data.expression == "supporting"
        and data.context == "characterized"
    )

    if all_favourable:
        level: EvidenceLevel = "strong"
    elif data.sequence == "unknown" or data.functional == "predicted":
        level = "limited"
    else:
        level = "moderate"

    deserves = level != "limited" and data.pathway != "incomplete"
    explanation = _explain(level, missing, concerns)
    return Assessment(level, deserves, missing, concerns, explanation)


def _explain(level: EvidenceLevel, missing: list[str], concerns: list[str]) -> str:
    parts = [f"Evidence level: {level}. This is an evidence class, not a success probability."]
    if concerns:
        parts.append("Concerns: " + "; ".join(concerns) + ".")
    if missing:
        parts.append("Missing information: " + "; ".join(missing) + ".")
    if not concerns and not missing:
        parts.append("All five evidence dimensions are supported by available data.")
    return " ".join(parts)
