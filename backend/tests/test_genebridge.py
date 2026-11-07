import dataclasses

import pytest

from app.genebridge import AssessmentInput, assess

BEST = AssessmentInput(
    sequence="related",
    functional="characterized",
    pathway="supported",
    expression="supporting",
    context="characterized",
)


def variant(**changes):
    return dataclasses.replace(BEST, **changes)


def test_all_favourable_is_strong():
    result = assess(BEST)
    assert result.level == "strong"
    assert result.deserves_investigation
    assert result.missing_information == []
    assert result.concerns == []


def test_predicted_function_caps_at_limited():
    result = assess(variant(functional="predicted"))
    assert result.level == "limited"
    assert not result.deserves_investigation
    assert "experimental characterisation of gene function" in result.missing_information


def test_unknown_sequence_is_limited():
    assert assess(variant(sequence="unknown")).level == "limited"


def test_weak_relationship_is_moderate_with_concern():
    result = assess(variant(sequence="weakly_related"))
    assert result.level == "moderate"
    assert any("weakly related" in c for c in result.concerns)


def test_incomplete_pathway_blocks_investigation():
    result = assess(variant(pathway="incomplete"))
    assert result.level == "moderate"
    assert not result.deserves_investigation
    assert any("pathway components" in c for c in result.concerns)


def test_conflicting_expression_is_a_concern():
    result = assess(variant(expression="conflicting"))
    assert any("conflicts" in c for c in result.concerns)


def test_unavailable_data_is_reported_as_missing():
    result = assess(variant(expression="unavailable", context="uncertain", pathway="unknown"))
    assert len(result.missing_information) == 3
    assert result.level == "moderate"


def test_explanation_never_claims_a_probability():
    text = assess(variant(functional="predicted")).explanation
    assert "%" not in text
    assert "not a success probability" in text


def test_strong_explanation_mentions_all_dimensions():
    assert "All five evidence dimensions" in assess(BEST).explanation


@pytest.mark.parametrize("field", ["sequence", "functional", "pathway", "expression", "context"])
def test_assessment_is_deterministic(field):
    data = variant(**{field: getattr(BEST, field)})
    assert assess(data) == assess(data)
