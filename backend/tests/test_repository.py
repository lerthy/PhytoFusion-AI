import pytest

from app.crispr import ScenarioInput, simulate
from app.genebridge import AssessmentInput, assess

GOOD = AssessmentInput("related", "characterized", "supported", "supporting", "characterized")


class FakeEmbedder:
    """Deterministic vectors: texts mentioning 'terpene' point one way, the rest another."""

    def embed(self, texts):
        return [[1.0, 0.0, 0.0] if "terpene" in t else [0.0, 1.0, 0.0] for t in texts]


def ids(repo):
    return repo.species_id("Host sp."), repo.species_id("Donor sp.")


def test_species_validation_and_lookup(repo):
    with pytest.raises(ValueError, match="role"):
        repo.upsert_species("X", "neither")
    with pytest.raises(LookupError, match="not in the database"):
        repo.species_id("Unknown")


def test_genome_resolves_chromosome_names_and_omits_proteins(seeded):
    host_id, _ = ids(seeded)
    genome = seeded.genome(host_id)
    assert genome["accessions"] == ["ACC-H"]
    assert {c["name"] for c in genome["chromosomes"]} == {"Chr1", "Chr2"}
    kps = next(g for g in genome["genes"] if g["gene_id"] == "SbaiKPS1")
    assert kps["chromosome"] == "Chr1" and kps["start_bp"] == 1000 and "protein_sequence" not in kps
    with pytest.raises(LookupError):
        seeded.genome("missing")


def test_proteins_only_for_genes_that_have_one(seeded):
    host_id, _ = ids(seeded)
    assert seeded.proteins(host_id) == {"SbaiKPS1": "MKVLAAGG", "SbaiCHS1": "MTTTT"}


def test_find_gene_is_scoped_to_species(seeded):
    host_id, donor_id = ids(seeded)
    assert seeded.find_gene("SbarKPS1", donor_id)["gene_id"] == "SbarKPS1"
    with pytest.raises(LookupError, match="not found"):
        seeded.find_gene("SbarKPS1", host_id)


def test_paging_collects_every_row(repo):
    repo.store.insert("chromosomes", [{"assembly_id": "a", "name": f"c{i}"} for i in range(2500)])
    assert len(repo._all("chromosomes", eq={"assembly_id": "a"})) == 2500


def test_evidence_requires_a_source_and_deduplicates(repo):
    with pytest.raises(ValueError, match="PMID or a DOI"):
        repo.add_evidence("finding", "strong")
    with pytest.raises(ValueError, match="level"):
        repo.add_evidence("finding", "certain", pmid="1")
    with pytest.raises(ValueError, match="finding"):
        repo.add_evidence("  ", "strong", pmid="1")
    first = repo.add_evidence("a finding", "moderate", pmid="PMID:1", title="T")
    again = repo.add_evidence("different text", "strong", pmid="PMID:1")
    by_doi = repo.add_evidence("via doi", "limited", doi="10.1/x")
    assert again["id"] == first["id"] and by_doi["id"] != first["id"]
    assert len(repo.list_evidence()) == 2


def test_literature_roundtrip_returns_source_with_every_passage(repo):
    ev = repo.add_evidence("KPS paper", "strong", pmid="PMID:7", title="Diterpene synthases")
    other = repo.add_evidence("other paper", "limited", doi="10.1/other", title="Other")
    assert (
        repo.add_literature(ev["id"], "This terpene synthase makes a product.", FakeEmbedder()) == 1
    )
    repo.add_literature(other["id"], "Unrelated flavonoid note.", FakeEmbedder())
    hits = repo.search_literature("which terpene?", FakeEmbedder(), k=1)
    assert (
        len(hits) == 1 and hits[0]["pmid"] == "PMID:7" and hits[0]["title"] == "Diterpene synthases"
    )
    assert "terpene synthase" in hits[0]["content"]
    with pytest.raises(LookupError):
        repo.add_literature("no-such-id", "text", FakeEmbedder())


def test_comparisons_are_upserted_and_named(seeded):
    host_id, donor_id = ids(seeded)
    h, d = seeded.find_gene("SbaiKPS1", host_id), seeded.find_gene("SbarKPS1", donor_id)
    first = seeded.save_comparison(h["id"], d["id"], GOOD, assess(GOOD), 71.5)
    second = seeded.save_comparison(h["id"], d["id"], GOOD, assess(GOOD), 72.0)
    assert first["id"] == second["id"]
    (row,) = seeded.list_comparisons()
    assert (row["host_gene"], row["donor_gene"], row["percent_identity"]) == (
        "SbaiKPS1",
        "SbarKPS1",
        72.0,
    )
    assert row["overall_level"] == "strong" and row["sequence_relationship"] == "related"


def good_edge(**extra):
    return {
        "data": {
            "source": "a",
            "target": "b",
            "reference": "PMID:1",
            "evidence_level": "strong",
            **extra,
        }
    }


def test_pathways_validate_before_saving(repo):
    elements = [{"data": {"id": "a"}}, {"data": {"id": "b"}}, good_edge()]
    saved = repo.save_pathway("Flavonoid", elements, "desc")
    assert repo.list_pathways()[0]["name"] == "Flavonoid"
    assert repo.get_pathway(saved["id"])["graph"] == elements
    with pytest.raises(ValueError, match="reference"):
        repo.save_pathway("Bad", [good_edge(reference="")])
    with pytest.raises(ValueError, match="name"):
        repo.save_pathway(" ", elements)
    with pytest.raises(LookupError):
        repo.get_pathway("missing")


def scenario(kind, **kw):
    base = {
        "type": kind,
        "host_species": "Host sp.",
        "target_gene_id": "SbarKPS1",
        "donor_species": "Donor sp.",
        "assessment": assess(GOOD),
        "references": ("PMID:1",),
    }
    return simulate(ScenarioInput(**{**base, **kw}))


def test_scenarios_persist_and_reload_exactly(seeded):
    saved = seeded.save_scenario(
        scenario("donor_integration", documented_function="Published text")
    )
    loaded = seeded.get_scenario(saved["id"])
    assert (
        loaded["target_gene_id"] == "SbarKPS1"
        and "Virtual plant report" in loaded["report_markdown"]
    )
    assert loaded["limitations"] and loaded["evidence_level"] == "strong"
    (item,) = seeded.list_scenarios()
    assert item["id"] == saved["id"] and item["type"] == "donor_integration"


def test_host_modification_targets_a_host_gene(seeded):
    result = scenario("host_modification", target_gene_id="SbaiKPS1", donor_species=None)
    saved = seeded.save_scenario(result)
    host_id, _ = ids(seeded)
    row = seeded.store.select("crispr_scenarios", eq={"id": saved["id"]})[0]
    assert row["target_gene_id"] == seeded.find_gene("SbaiKPS1", host_id)["id"]
    assert row["donor_species_id"] is None


def test_scenario_needs_known_species_and_genes(seeded):
    with pytest.raises(LookupError, match="Nowhere"):
        seeded.save_scenario(scenario("donor_integration", host_species="Nowhere"))
    with pytest.raises(LookupError, match="not found"):
        seeded.save_scenario(scenario("donor_integration", target_gene_id="GHOST"))
    with pytest.raises(LookupError):
        seeded.get_scenario("missing")


def test_stats_counts_every_table(seeded):
    stats = seeded.stats()
    assert stats["species"] == 2 and stats["evidence"] == 0 and set(stats) >= {"genes", "pathways"}
