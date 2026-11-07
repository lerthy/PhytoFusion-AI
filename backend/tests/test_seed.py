from pathlib import Path

import pytest

from app.comparison import read_fasta_records
from app.ingestion import seed
from app.repository import Repository
from app.store import InMemoryStore

DATA = Path(__file__).parent / "data"


def test_match_proteins_exact_and_isoform():
    genes = {"G1", "G2"}
    records = {"G1": "MK", "G2.t1": "MAAA", "G2.t2": "MAAAAA", "X": "M"}
    exact, unmatched = seed.match_proteins(genes, records)
    assert exact == {"G1": "MK"} and unmatched == 3
    iso, unmatched = seed.match_proteins(genes, records, strip_isoform=True)
    assert iso == {"G1": "MK", "G2": "MAAAAA"} and unmatched == 1  # longest isoform kept


def test_read_families(tmp_path):
    f = tmp_path / "f.csv"
    f.write_text("gene_id,family\nSbaiKPS1,KPS\n,ignored\n")
    assert seed.read_families(f) == {"SbaiKPS1": "KPS"}
    f.write_text("a,b\n1,2\n")
    with pytest.raises(ValueError, match="gene_id,family"):
        seed.read_families(f)


def test_build_plan_summary_and_validation(tmp_path):
    plan = seed.build_plan("Host sp.", "host", "ACC", "test", DATA / "sample.gff3")
    assert len(plan.genes) == 2 and plan.lengths == {"Chr1": 50000, "Chr2": 30000}
    assert "2 genes, 2 chromosomes" in plan.summary()
    empty = tmp_path / "empty.gff3"
    empty.write_text("##gff-version 3\n")
    with pytest.raises(ValueError, match="no gene"):
        seed.build_plan("x", "host", "A", "s", empty)


def test_apply_is_idempotent(seeded):
    before = seeded.stats()
    plan = seed.build_plan("Host sp.", "host", "ACC-H", "test", DATA / "sample.gff3")
    seed.apply_plan(seeded, plan)
    assert seeded.stats() == before
    assert before["species"] == 2 and before["genes"] == 4 and before["chromosomes"] == 3


def test_apply_stores_proteins_families_and_chromosome_links(repo, tmp_path):
    fam = tmp_path / "fam.csv"
    fam.write_text("gene_id,family\nSbaiKPS1,KPS\n")
    prot = tmp_path / "p.faa"
    prot.write_text(">SbaiKPS1\nMKV\n")
    plan = seed.build_plan("Host sp.", "host", "ACC", "t", DATA / "sample.gff3", prot, fam)
    seed.apply_plan(repo, plan)
    sid = repo.species_id("Host sp.")
    kps = repo.find_gene("SbaiKPS1", sid)
    assert kps["family"] == "KPS" and kps["protein_sequence"] == "MKV" and kps["chromosome_id"]
    assert repo.find_gene("SbaiCHS1", sid)["family"] is None  # never inferred


def test_usable_names_avoid_collisions():
    # two sequences share an alias, and one alias equals another sequence's id
    names = seed.usable_names(
        ["A", "B", "C", "D", "E"], {"A": "same", "B": "same", "C": "E", "D": "ok"}
    )
    assert names == {"D": "ok"}


def test_plan_reads_friendly_names_from_the_file():
    plan = seed.build_plan("S", "host", "ACC", "t", DATA / "aliased.gff3")
    assert plan.names == {"ACC0001": "Sbai1", "ACC0002": "Sbai2", "ACC0003": "utg9"}
    assert "3 sequences with friendlier names" in plan.summary()


def test_apply_stores_friendly_name_and_keeps_the_accession(repo):
    seed.apply_plan(repo, seed.build_plan("S", "host", "ACC", "t", DATA / "aliased.gff3"))
    rows = repo.store.select("chromosomes", order="name")
    assert {(r["name"], r["accession"]) for r in rows} == {
        ("Sbai1", "ACC0001"),
        ("Sbai2", "ACC0002"),
        ("utg9", "ACC0003"),
    }
    genome = repo.genome(repo.species_id("S"))
    placed = {g["gene_id"]: g["chromosome"] for g in genome["genes"]}
    assert placed == {
        "G1": "Sbai1",
        "G2": "Sbai2",
        "G3": "utg9",
    }  # genes land on the right sequence
    assert {c["accession"] for c in genome["chromosomes"]} == {"ACC0001", "ACC0002", "ACC0003"}


def test_reseeding_with_names_is_still_idempotent(repo):
    plan = seed.build_plan("S", "host", "ACC", "t", DATA / "aliased.gff3")
    seed.apply_plan(repo, plan)
    before = repo.stats()
    seed.apply_plan(repo, plan)
    assert repo.stats() == before


def test_main_dry_run_writes_nothing(capsys, monkeypatch):
    def boom():
        raise AssertionError("must not connect")

    monkeypatch.setattr(seed.SupabaseStore, "from_env", boom)
    code = seed.main(
        [
            "--species",
            "S",
            "--role",
            "host",
            "--accession",
            "A",
            "--source",
            "x",
            "--gff",
            str(DATA / "sample.gff3"),
        ]
    )
    out = capsys.readouterr().out
    assert code == 0 and "Dry run" in out and "2 genes" in out


def test_main_apply_writes_through_store(monkeypatch, capsys, tmp_path):
    store = InMemoryStore()
    monkeypatch.setattr(seed.SupabaseStore, "from_env", classmethod(lambda cls: store))
    code = seed.main(
        [
            "--species",
            "S",
            "--role",
            "donor",
            "--accession",
            "A",
            "--source",
            "x",
            "--gff",
            str(DATA / "sample.gff3"),
            "--apply",
            "--env-file",
            str(tmp_path / "none"),
        ]
    )
    assert code == 0 and Repository(store).stats()["genes"] == 2
    assert "Wrote 2 genes" in capsys.readouterr().out


def test_proteins_match_through_origeneid_and_keep_the_longest():
    records = read_fasta_records((DATA / "proteins_gwh.faa").read_text().splitlines())
    matched, unmatched = seed.match_protein_records({"G1", "G2", "G3"}, records)
    assert matched == {"G1": "MKVLAAGGTTTT*", "G2": "MAAA*"}  # G1: the longer isoform wins
    assert unmatched == 1  # Z9 is not in the annotation


def test_origeneid_beats_a_non_matching_record_id_and_ids_still_work_without_it():
    records = [
        read_fasta_records([">ACC1 OriGeneID=G1", "MK"])[0],
        read_fasta_records([">G2", "MAA"])[0],  # no note: matched by its own id
        read_fasta_records([">G3.t1", "MAAA"])[0],  # only matches with isoform stripping
    ]
    ids = {"G1", "G2", "G3"}
    assert seed.match_protein_records(ids, records) == ({"G1": "MK", "G2": "MAA"}, 1)
    assert seed.match_protein_records(ids, records, strip_isoform=True)[0] == {
        "G1": "MK",
        "G2": "MAA",
        "G3": "MAAA",
    }


def test_plan_stores_proteins_for_genes_it_can_match(tmp_path):
    gff = tmp_path / "a.gff3"
    gff.write_text(
        "##gff-version 3\n"
        "ACC0001\tt\tgene\t100\t900\t.\t+\t.\tID=G1\n"
        "ACC0001\tt\tgene\t1000\t1500\t.\t+\t.\tID=G2\n"
    )
    plan = seed.build_plan("S", "host", "ACC", "t", gff, DATA / "proteins_gwh.faa")
    assert set(plan.proteins) == {"G1", "G2"} and plan.unmatched_proteins == 1
    assert "2 proteins matched (1 protein records matched no gene)" in plan.summary()
