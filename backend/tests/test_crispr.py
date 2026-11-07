import re

import pytest

from app.crispr import ScenarioInput, render_report_markdown, simulate
from app.genebridge import AssessmentInput, assess

GOOD = assess(
    AssessmentInput("related", "characterized", "supported", "supporting", "characterized")
)
WEAK = assess(AssessmentInput("unknown", "predicted", "unknown", "unavailable", "uncertain"))
INCOMPLETE = assess(
    AssessmentInput("related", "characterized", "incomplete", "supporting", "characterized")
)


def make(**kw):
    base = dict(
        type="donor_integration",
        host_species="Host sp.",
        donor_species="Donor sp.",
        target_gene_id="GENE1",
        assessment=GOOD,
        documented_function="Published function text",
        pathway="Example pathway",
        references=("PMID:1",),
    )
    base.update(kw)
    return ScenarioInput(**base)


def test_donor_integration_basics():
    r = simulate(make())
    assert "Donor sp." in r.scenario and "Host sp." in r.scenario
    assert any("Published function text" in c for c in r.predicted_consequences)
    assert any("technically challenging" in lim for lim in r.limitations)
    assert r.evidence_level == "strong"


def test_host_modification_has_no_integration_limitation():
    r = simulate(make(type="host_modification", donor_species=None))
    assert "modification" in r.scenario
    assert not any("large donor DNA" in lim for lim in r.limitations)
    assert any("cannot be predicted" in c for c in r.predicted_consequences)


def test_donor_integration_requires_donor():
    with pytest.raises(ValueError, match="donor_species"):
        simulate(make(donor_species=None))


@pytest.mark.parametrize("field", ["host_species", "target_gene_id"])
def test_required_fields(field):
    with pytest.raises(ValueError):
        simulate(make(**{field: "  "}))


def test_missing_function_is_reported_not_invented():
    r = simulate(make(documented_function=None))
    assert "documented function of GENE1" in r.missing_information
    assert any("No documented function" in c for c in r.predicted_consequences)


def test_missing_pathway_on_integration_is_reported():
    assert "pathway context for the donor gene" in simulate(make(pathway=None)).missing_information


def test_no_references_forces_limited():
    r = simulate(make(references=("", "  ")))
    assert r.evidence_level == "limited"
    assert any("No literature references" in lim for lim in r.limitations)


def test_limited_assessment_adds_exploratory_limitation():
    r = simulate(make(assessment=WEAK))
    assert any("exploratory" in lim for lim in r.limitations)


def test_concerns_are_passed_through():
    assert any(
        "pathway components" in c
        for c in simulate(make(assessment=INCOMPLETE)).compatibility_issues
    )


def test_missing_information_is_deduplicated():
    r = simulate(make(assessment=WEAK, documented_function=None))
    assert len(r.missing_information) == len(set(r.missing_information))


def test_limitations_are_never_empty():
    assert len(simulate(make()).limitations) >= 3


def test_report_is_hypothetical_and_free_of_forbidden_claims():
    text = render_report_markdown(simulate(make(chromosome="Chr3")))
    assert "hypothetical" in text.lower()
    assert "chromosome Chr3" in text
    assert "## Limitations" in text and "PMID:1" in text
    assert not re.search(r"\d+ ?%", text)
    assert not re.search(r"has been (genetically )?engineered|\bcures?\b|proven", text)


def test_report_handles_empty_sections():
    text = render_report_markdown(simulate(make(assessment=GOOD, references=(), pathway="P")))
    assert "none supplied" in text
