import subprocess
from pathlib import Path

import pytest

from app.comparison import (
    BlastHit,
    best_hits,
    classify_sequence_relationship,
    map_genes_to_chromosomes,
    parse_blast_tabular,
    read_fasta,
    read_fasta_records,
    reciprocal_best_hits,
    run_blastp,
)
from app.ingestion.gff3 import GeneRecord


def hit(q, s, pident=90.0, evalue=1e-50, bits=200.0):
    return BlastHit(q, s, pident, 100, evalue, bits)


def test_read_fasta_joins_wrapped_lines_and_uses_first_token():
    seqs = read_fasta([">g1 description", "MKV", "LLA", "", ">g2", "MAA"])
    assert seqs == {"g1": "MKVLLA", "g2": "MAA"}


@pytest.mark.parametrize(
    "lines",
    [["MKV"], [">"], [">a", "M", ">a", "K"]],
    ids=["no-header", "empty-header", "duplicate"],
)
def test_read_fasta_rejects_bad_input(lines):
    with pytest.raises(ValueError):
        read_fasta(lines)


def test_parse_blast_tabular():
    hits = parse_blast_tabular(["# comment", "", "a\tb\t88.5\t300\t1e-80\t450.0"])
    assert hits == [BlastHit("a", "b", 88.5, 300, 1e-80, 450.0)]


@pytest.mark.parametrize("line", ["a\tb\t1", "a\tb\tx\t1\t1\t1"])
def test_parse_blast_rejects_malformed(line):
    with pytest.raises(ValueError):
        parse_blast_tabular([line])


def test_best_hits_prefers_bitscore_then_evalue_then_subject():
    hits = [
        hit("q", "s1", bits=100),
        hit("q", "s2", bits=300),
        hit("q", "s3", bits=300, evalue=1e-60),
    ]
    assert best_hits(hits)["q"].subject == "s3"
    tie = [hit("q", "sb"), hit("q", "sa")]
    assert best_hits(tie)["q"].subject == "sa"


def test_reciprocal_best_hits_only_mutual_pairs():
    a_vs_b = [hit("a1", "b1"), hit("a2", "b1", bits=100)]
    b_vs_a = [hit("b1", "a1")]
    assert reciprocal_best_hits(a_vs_b, b_vs_a) == [("a1", "b1")]


@pytest.mark.parametrize(
    "h,expected",
    [
        (None, "unknown"),
        (hit("q", "s", pident=60, evalue=1e-40), "related"),
        (hit("q", "s", pident=25, evalue=1e-20), "weakly_related"),
        (hit("q", "s", pident=60, evalue=1e-5), "weakly_related"),
        (hit("q", "s", pident=60, evalue=0.5), "unknown"),
    ],
)
def test_classify_sequence_relationship(h, expected):
    assert classify_sequence_relationship(h) == expected


def test_classify_thresholds_are_tunable():
    h = hit("q", "s", pident=35, evalue=1e-20)
    assert classify_sequence_relationship(h) == "weakly_related"
    assert classify_sequence_relationship(h, related_min_pident=30) == "related"


def test_map_genes_reports_missing_as_none():
    gene = GeneRecord("SbaiKPS1", "Chr1", 1, 100, "+")
    assert map_genes_to_chromosomes([gene], ["SbaiKPS1", "nope"]) == {
        "SbaiKPS1": gene,
        "nope": None,
    }


def test_run_blastp_requires_binary():
    with pytest.raises(RuntimeError, match="not found"):
        run_blastp(Path("q"), Path("s"), which=lambda _: None)


def test_run_blastp_parses_output_and_builds_command():
    calls = []

    def fake_runner(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="a\tb\t90\t100\t1e-30\t150\n", stderr="")

    hits = run_blastp(Path("q.fa"), Path("s.fa"), runner=fake_runner, which=lambda _: "/bin/blastp")
    assert hits[0].subject == "b"
    assert calls[0][:5] == ["blastp", "-query", "q.fa", "-subject", "s.fa"]


def test_run_blastp_surfaces_failures():
    def failing(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 2, stdout="", stderr="bad db")

    with pytest.raises(RuntimeError, match="bad db"):
        run_blastp(Path("q"), Path("s"), runner=failing, which=lambda _: "/bin/blastp")


def test_read_fasta_records_keeps_the_description():
    (a, b) = read_fasta_records([">p1 mRNA=m1\tOriGeneID=G1", "MK", "V", ">p2", "MA"])
    assert (a.id, a.description, a.sequence) == ("p1", "mRNA=m1\tOriGeneID=G1", "MKV")
    assert (b.id, b.description, b.sequence) == ("p2", "", "MA")


@pytest.mark.parametrize(
    "lines", [["MKV"], [">"], [">a", "M", ">a", "K"]], ids=["no-header", "empty", "duplicate"]
)
def test_read_fasta_records_rejects_bad_input(lines):
    with pytest.raises(ValueError):
        read_fasta_records(lines)


def test_run_blastp_uses_threads_and_a_timeout_and_reports_a_timeout_clearly():
    seen = {}

    def runner(cmd, **kwargs):
        seen["cmd"], seen["timeout"] = cmd, kwargs.get("timeout")
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    with pytest.raises(RuntimeError, match="took longer than 5 s"):
        run_blastp(
            Path("q"), Path("s"), timeout=5, threads=3, runner=runner, which=lambda _: "/bin/blastp"
        )
    assert seen["timeout"] == 5
    assert seen["cmd"][seen["cmd"].index("-num_threads") + 1] == "3"
    assert seen["cmd"][seen["cmd"].index("-max_target_seqs") + 1] == "5"
