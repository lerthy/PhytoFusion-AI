from pathlib import Path

import pytest

from app.ingestion.gff3 import (
    normalize_gene_id,
    parse_attributes,
    parse_chromosome_lengths,
    parse_gff3_genes,
    parse_sequence_aliases,
)

SAMPLE = Path(__file__).parent / "data" / "sample.gff3"


def row(ftype="gene", start="1", end="10", strand="+", attrs="ID=g1", seqid="Chr1"):
    return "\t".join([seqid, "src", ftype, start, end, ".", strand, ".", attrs])


def test_normalize_strips_prefix_and_whitespace():
    assert normalize_gene_id("  gene:SbaiKPS1 ") == "SbaiKPS1"
    assert normalize_gene_id("gene-SbarKPS2") == "SbarKPS2"


def test_normalize_preserves_case():
    assert normalize_gene_id("SbaiKPS1") == "SbaiKPS1"


@pytest.mark.parametrize("raw", ["", "   ", "gene:"])
def test_normalize_rejects_empty(raw):
    with pytest.raises(ValueError):
        normalize_gene_id(raw)


def test_parse_attributes_decodes_and_ignores_blanks():
    assert parse_attributes("ID=a;Note=x%20y;;") == {"ID": "a", "Note": "x y"}


def test_parse_attributes_rejects_malformed():
    with pytest.raises(ValueError):
        parse_attributes("ID=a;oops")


def test_parse_sample_file_only_returns_genes():
    genes = parse_gff3_genes(SAMPLE.read_text().splitlines())
    assert [g.gene_id for g in genes] == ["SbaiKPS1", "SbaiCHS1"]
    kps = genes[0]
    assert (kps.chromosome, kps.start, kps.end, kps.strand) == ("Chr1", 1000, 2500, "+")
    assert kps.name == "KPS1"
    assert kps.description == "Kaurene synthase-like"
    assert genes[1].strand == "-"


def test_chromosome_lengths_from_sample():
    lengths = parse_chromosome_lengths(SAMPLE.read_text().splitlines())
    assert lengths == {"Chr1": 50000, "Chr2": 30000}


def test_malformed_sequence_region():
    with pytest.raises(ValueError):
        parse_chromosome_lengths(["##sequence-region Chr1 1"])


def test_wrong_column_count_reports_line_number():
    with pytest.raises(ValueError, match="line 2"):
        parse_gff3_genes([row(), "a\tb\tc"])


@pytest.mark.parametrize(
    "bad",
    [
        row(start="x"),
        row(start="0"),
        row(start="20", end="10"),
        row(strand="*"),
        row(attrs="Name=nope"),
    ],
)
def test_invalid_gene_rows_raise(bad):
    with pytest.raises(ValueError):
        parse_gff3_genes([bad])


def test_empty_input():
    assert parse_gff3_genes([]) == []


def test_sequence_aliases_from_oriseqid_comments():
    lines = [
        "##gff-version 3",
        "#OriSeqID=Sbai1\tAccession=GWHAOTO00000001",
        row(seqid="GWHAOTO00000001"),
        "#OriSeqID=Sbai1\tAccession=GWHAOTO00000001",  # repeated per gene in real files
        "#OriSeqID=utg9\tAccession=GWHAOTO00000020",
    ]
    assert parse_sequence_aliases(lines) == {
        "GWHAOTO00000001": "Sbai1",
        "GWHAOTO00000020": "utg9",
    }


@pytest.mark.parametrize(
    "line", ["#OriSeqID=onlyname", "#OriSeqID=\tAccession=X", "#OriSeqID=A\tAccession=", "# note"]
)
def test_malformed_aliases_are_skipped_not_fatal(line):
    assert parse_sequence_aliases([line]) == {}
