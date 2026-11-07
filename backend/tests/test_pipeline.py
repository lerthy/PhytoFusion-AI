import pytest

from app.comparison import BlastHit
from app.pipeline import assessment_for, compare_proteomes, write_fasta

HOST = {"H1": "MKV*", "H2": "MAA"}
DONOR = {"D1": "MKV", "D2": "MCC"}


def hit(q, s, pident=70.0, evalue=1e-40, bits=200.0):
    return BlastHit(q, s, pident, 100, evalue, bits)


def fake_blast(query, subject):
    if query.name == "query_donor.fa":  # donor vs host
        return [hit("D1", "H1")]
    return [hit("H1", "D1"), hit("H2", "D1", bits=50.0)]  # host vs donor


def test_pairs_flag_reciprocal_hits_and_missing_hits():
    pairs = compare_proteomes(HOST, DONOR, blast=fake_blast)
    d1, d2 = pairs
    assert (d1.donor_id, d1.host_id, d1.reciprocal, d1.sequence_relationship) == (
        "D1",
        "H1",
        True,
        "related",
    )
    assert (d2.host_id, d2.hit, d2.reciprocal, d2.sequence_relationship) == (
        None,
        None,
        False,
        "unknown",
    )


def test_candidates_restrict_output_and_must_exist():
    assert [p.donor_id for p in compare_proteomes(HOST, DONOR, ["D2"], blast=fake_blast)] == ["D2"]
    with pytest.raises(KeyError, match="NOPE"):
        compare_proteomes(HOST, DONOR, ["NOPE"], blast=fake_blast)
    with pytest.raises(ValueError, match="empty"):
        compare_proteomes({}, DONOR, blast=fake_blast)


def test_non_reciprocal_hit_is_not_flagged():
    def one_way(query, subject):
        return [hit("D1", "H1")] if query.name == "query_donor.fa" else [hit("H1", "D2")]

    assert compare_proteomes(HOST, DONOR, ["D1"], blast=one_way)[0].reciprocal is False


def test_write_fasta_strips_stop_codon(tmp_path):
    write_fasta(tmp_path / "x.fa", {"a": "MKV*"})
    assert (tmp_path / "x.fa").read_text() == ">a\nMKV\n"


def test_assessment_only_derives_sequence_and_stays_conservative():
    pair = compare_proteomes(HOST, DONOR, ["D1"], blast=fake_blast)[0]
    data = assessment_for(pair)
    assert data.sequence == "related"
    assert (data.functional, data.pathway, data.expression, data.context) == (
        "predicted",
        "unknown",
        "unavailable",
        "uncertain",
    )
    assert assessment_for(pair, {"functional": "characterized"}).functional == "characterized"


def test_only_the_candidates_and_their_best_hits_are_searched():
    """The speed fix: never search whole proteomes against each other."""
    seen = []

    def spy(query, subject):
        seen.append((query.name, sorted(read_names(query)), subject.name))
        if query.name == "query_donor.fa":
            return [hit("D1", "H1")]
        return [hit("H1", "D1")]

    compare_proteomes(HOST, {**DONOR, "D3": "MQQ"}, ["D1"], blast=spy)
    assert seen == [
        ("query_donor.fa", ["D1"], "host.fa"),  # one candidate, not the whole donor proteome
        ("query_host.fa", ["H1"], "donor.fa"),  # one best hit, not the whole host proteome
    ]


def test_no_reverse_search_when_nothing_matched():
    calls = []

    def none_found(query, subject):
        calls.append(query.name)
        return []

    pairs = compare_proteomes(HOST, DONOR, ["D1"], blast=none_found)
    assert calls == ["query_donor.fa"] and pairs[0].host_id is None


def read_names(path):
    return [line[1:].strip() for line in path.read_text().splitlines() if line.startswith(">")]
