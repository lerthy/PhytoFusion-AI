import pytest

from app.evidence import Study, classify_evidence


def test_no_studies_is_limited():
    assert classify_evidence([]) == "limited"


def test_studies_without_reference_are_ignored():
    assert classify_evidence([Study("", True), Study("   ", True)]) == "limited"


def test_single_experimental_is_moderate():
    assert classify_evidence([Study("PMID:1", True)]) == "moderate"


def test_single_computational_is_limited():
    assert classify_evidence([Study("PMID:1", False)]) == "limited"


def test_two_computational_is_moderate():
    assert classify_evidence([Study("PMID:1", False), Study("PMID:2", False)]) == "moderate"


def test_two_refs_with_one_experimental_is_strong():
    assert classify_evidence([Study("PMID:1", True), Study("PMID:2", False)]) == "strong"


def test_duplicate_reference_counts_once():
    studies = [Study("PMID:1", True), Study("PMID:1", True)]
    assert classify_evidence(studies) == "moderate"


def test_duplicate_reference_experimental_wins():
    studies = [Study("PMID:1", False), Study("PMID:1", True), Study("PMID:2", False)]
    assert classify_evidence(studies) == "strong"


@pytest.mark.parametrize("n", [2, 5, 10])
def test_many_experimental_is_strong(n):
    assert classify_evidence([Study(f"PMID:{i}", True) for i in range(n)]) == "strong"
