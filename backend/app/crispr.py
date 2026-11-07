"""Engine 5: CRISPR scenario simulator.

Hypothetical and qualitative. It consumes a GeneBridge `Assessment` plus facts supplied by the
caller (documented function, pathway, references) and never adds biological facts of its own.
Every result carries limitations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .evidence import EvidenceLevel
from .genebridge import Assessment

ScenarioType = Literal["host_modification", "donor_integration"]

BASE_LIMITATIONS = (
    "Computational scenario only: no genome editing was performed "
    "and no engineered organism exists.",
    "Qualitative output: outcomes are not quantified and success cannot be predicted.",
    "Therapeutic efficacy is not assessed and would require separate experimental evidence.",
)
INTEGRATION_LIMITATION = (
    "Introducing a large donor DNA sequence into a plant genome remains technically challenging."
)


@dataclass(frozen=True)
class ScenarioInput:
    type: ScenarioType
    host_species: str
    target_gene_id: str
    assessment: Assessment
    donor_species: str | None = None
    chromosome: str | None = None
    documented_function: str | None = None  # published description, supplied by the caller
    pathway: str | None = None
    references: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScenarioResult:
    type: ScenarioType
    host_species: str
    donor_species: str | None
    target_gene_id: str
    chromosome: str | None
    documented_function: str | None
    pathway: str | None
    scenario: str
    predicted_consequences: list[str]
    compatibility_issues: list[str]
    missing_information: list[str]
    limitations: list[str]
    evidence_level: EvidenceLevel
    references: list[str] = field(default_factory=list)


def simulate(data: ScenarioInput) -> ScenarioResult:
    if not data.host_species.strip() or not data.target_gene_id.strip():
        raise ValueError("host_species and target_gene_id are required")
    if data.type == "donor_integration" and not (data.donor_species or "").strip():
        raise ValueError("donor_integration requires donor_species")

    references = [r.strip() for r in data.references if r and r.strip()]
    function = data.documented_function.strip() if data.documented_function else None
    pathway = data.pathway.strip() if data.pathway else None

    consequences: list[str] = []
    missing = list(data.assessment.missing_information)

    if function:
        consequences.append(f"Documented function of {data.target_gene_id}: {function}")
    else:
        missing.append(f"documented function of {data.target_gene_id}")
        consequences.append("No documented function was supplied, so no consequence can be stated.")

    if data.type == "host_modification":
        scenario = (
            f"Hypothetical modification of host gene {data.target_gene_id} in {data.host_species}."
        )
        if pathway:
            consequences.append(
                f"The change could alter activity of the {pathway} pathway; "
                "the direction and size of the effect cannot be predicted from available data."
            )
    else:
        scenario = (
            f"Hypothetical introduction of donor gene {data.target_gene_id} from "
            f"{data.donor_species} into {data.host_species}."
        )
        consequences.append(
            "If expressed, the enzyme could add or increase this activity in the host; whether a "
            "product forms depends on precursor supply and downstream enzymes in the host."
        )
        if pathway is None:
            missing.append("pathway context for the donor gene")

    limitations = list(BASE_LIMITATIONS)
    if data.type == "donor_integration":
        limitations.append(INTEGRATION_LIMITATION)
    if data.assessment.level == "limited":
        limitations.append("Supporting evidence is limited; treat this scenario as exploratory.")

    level: EvidenceLevel = data.assessment.level if references else "limited"
    if not references:
        limitations.append("No literature references were supplied, so evidence is limited.")

    return ScenarioResult(
        type=data.type,
        host_species=data.host_species,
        donor_species=data.donor_species,
        target_gene_id=data.target_gene_id,
        chromosome=data.chromosome,
        documented_function=function,
        pathway=pathway,
        scenario=scenario,
        predicted_consequences=consequences,
        compatibility_issues=list(data.assessment.concerns),
        missing_information=_dedupe(missing),
        limitations=limitations,
        evidence_level=level,
        references=references,
    )


def render_report_markdown(result: ScenarioResult) -> str:
    """Virtual plant report: a hypothetical scenario with evidence and limitations."""

    def bullets(items: list[str], empty: str) -> str:
        return "\n".join(f"- {i}" for i in items) if items else f"- {empty}"

    location = f" (chromosome {result.chromosome})" if result.chromosome else ""
    return "\n".join(
        [
            "# Virtual plant report (hypothetical)",
            "",
            result.scenario,
            "",
            f"**Candidate gene:** {result.target_gene_id}{location}",
            f"**Evidence level:** {result.evidence_level} "
            "(an evidence class, not a success probability)",
            "",
            "## Predicted qualitative consequences",
            bullets(result.predicted_consequences, "none"),
            "",
            "## Compatibility issues",
            bullets(result.compatibility_issues, "none identified from supplied data"),
            "",
            "## Missing information",
            bullets(result.missing_information, "none"),
            "",
            "## Limitations",
            bullets(result.limitations, "none"),
            "",
            "## References",
            bullets(result.references, "none supplied"),
            "",
        ]
    )


def _dedupe(items: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for item in items:
        seen.setdefault(item, None)
    return list(seen)
