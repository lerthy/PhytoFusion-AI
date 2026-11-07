import pytest
from fastapi.testclient import TestClient

from app import routes
from app.main import app
from app.pipeline import compare_proteomes
from app.store import StoreError

ASSESS = {
    "sequence": "related",
    "functional": "characterized",
    "pathway": "supported",
    "expression": "supporting",
    "context": "characterized",
}


class FakeEmbedder:
    def embed(self, texts):
        return [[1.0, 0.0] if "terpene" in t else [0.0, 1.0] for t in texts]


@pytest.fixture
def client(seeded):
    app.dependency_overrides[routes.get_store] = lambda: seeded.store
    app.dependency_overrides[routes.get_embedder] = lambda: FakeEmbedder()
    yield TestClient(app)
    app.dependency_overrides.clear()


def species_ids(client):
    rows = {s["scientific_name"]: s["id"] for s in client.get("/api/species").json()}
    return rows["Host sp."], rows["Donor sp."]


def test_stats_species_and_genome(client):
    assert client.get("/api/stats").json()["genes"] == 4
    host, _ = species_ids(client)
    body = client.get(f"/api/genome/{host}").json()
    assert {g["gene_id"] for g in body["genes"]} == {"SbaiKPS1", "SbaiCHS1"}
    assert client.get("/api/genome/missing").status_code == 404


def test_evidence_endpoints_enforce_traceability(client):
    assert client.post("/api/evidence", json={"finding": "f", "level": "strong"}).status_code == 422
    assert (
        client.post(
            "/api/evidence", json={"finding": "f", "level": "certain", "pmid": "1"}
        ).status_code
        == 422
    )
    ok = client.post("/api/evidence", json={"finding": "f", "level": "strong", "pmid": "PMID:1"})
    assert ok.status_code == 200 and client.get("/api/evidence").json()[0]["pmid"] == "PMID:1"


def test_literature_add_and_search_returns_sources(client):
    ev = client.post(
        "/api/evidence", json={"finding": "f", "level": "strong", "pmid": "PMID:9"}
    ).json()
    added = client.post(
        "/api/literature", json={"evidence_id": ev["id"], "text": "A terpene synthase."}
    )
    assert added.json() == {"chunks": 1}
    hits = client.get("/api/literature/search", params={"q": "terpene", "k": 99}).json()
    assert hits[0]["pmid"] == "PMID:9"
    assert (
        client.post("/api/literature", json={"evidence_id": "nope", "text": "x"}).status_code == 404
    )


def test_pipeline_compare_with_persistence(client, monkeypatch):
    from app.comparison import BlastHit

    def blast(query, subject):
        if query.name == "query_donor.fa":
            return [BlastHit("SbarKPS1", "SbaiKPS1", 71.0, 100, 1e-50, 300.0)]
        return [BlastHit("SbaiKPS1", "SbarKPS1", 71.0, 100, 1e-50, 300.0)]

    monkeypatch.setattr(
        routes, "compare_proteomes", lambda h, d, c: compare_proteomes(h, d, c, blast=blast)
    )
    host, donor = species_ids(client)
    body = {
        "host_species_id": host,
        "donor_species_id": donor,
        "candidate_gene_ids": ["SbarKPS1"],
        "persist": True,
    }
    (item,) = client.post("/api/pipeline/compare", json=body).json()
    assert item["sequence_relationship"] == "related" and item["reciprocal_best_hit"] is True
    saved = client.get("/api/comparisons").json()[0]
    # only the sequence dimension is derived; the rest stays conservative
    assert saved["functional_evidence"] == "predicted" and saved["overall_level"] == "limited"
    bad = client.post("/api/pipeline/compare", json={**body, "candidate_gene_ids": ["GHOST"]})
    assert bad.status_code == 422


def test_pipeline_reports_missing_blast_as_503(client, monkeypatch):
    def missing(h, d, c):
        raise RuntimeError("blastp not found on PATH")

    monkeypatch.setattr(routes, "compare_proteomes", missing)
    host, donor = species_ids(client)
    r = client.post(
        "/api/pipeline/compare",
        json={
            "host_species_id": host,
            "donor_species_id": donor,
            "candidate_gene_ids": ["SbarKPS1"],
        },
    )
    assert r.status_code == 503 and "blastp" in r.json()["detail"]


def test_manual_comparison(client):
    host, donor = species_ids(client)
    body = {
        "host_species_id": host,
        "donor_species_id": donor,
        "host_gene": "SbaiKPS1",
        "donor_gene": "SbarKPS1",
        "percent_identity": 55.5,
        "assessment": ASSESS,
    }
    assert client.post("/api/comparisons", json=body).status_code == 200
    assert client.post("/api/comparisons", json={**body, "donor_gene": "GHOST"}).status_code == 422
    assert (
        client.post("/api/comparisons", json={**body, "percent_identity": 140}).status_code == 422
    )


def test_pathway_endpoints(client):
    elements = [
        {"data": {"id": "a"}},
        {"data": {"id": "b"}},
        {"data": {"source": "a", "target": "b", "reference": "PMID:1", "evidence_level": "strong"}},
    ]
    saved = client.post("/api/pathways", json={"name": "P", "elements": elements}).json()
    assert client.get("/api/pathways").json()[0]["name"] == "P"
    assert client.get(f"/api/pathways/{saved['id']}").json()["graph"] == elements
    assert client.get("/api/pathways/nope").status_code == 404
    no_ref = [{"data": {"source": "a", "target": "b", "reference": "", "evidence_level": "strong"}}]
    assert client.post("/api/pathways", json={"name": "Q", "elements": no_ref}).status_code == 422


def test_scenario_save_list_and_get(client):
    body = {
        "type": "donor_integration",
        "host_species": "Host sp.",
        "donor_species": "Donor sp.",
        "target_gene_id": "SbarKPS1",
        "references": ["PMID:1"],
        "assessment": ASSESS,
    }
    saved = client.post("/api/scenarios", json=body)
    assert saved.status_code == 200 and saved.json()["limitations"]
    sid = saved.json()["id"]
    assert client.get("/api/scenarios").json()[0]["id"] == sid
    assert "Virtual plant report" in client.get(f"/api/scenarios/{sid}").json()["report_markdown"]
    assert client.get("/api/scenarios/nope").status_code == 404
    assert (
        client.post("/api/scenarios", json={**body, "target_gene_id": "GHOST"}).status_code == 422
    )
    assert client.post("/api/scenarios", json={**body, "donor_species": None}).status_code == 422


def test_database_failures_surface_as_502(seeded):
    class Broken:
        def count(self, table):
            raise StoreError("db down")

    app.dependency_overrides[routes.get_store] = lambda: Broken()
    try:
        r = TestClient(app).get("/api/stats")
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 502 and "db down" in r.json()["detail"]


def test_endpoints_answer_503_when_not_configured(monkeypatch):
    for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "EMBEDDING_API_URL"):
        monkeypatch.delenv(k, raising=False)
    routes._cached_store.cache_clear()
    c = TestClient(app)
    assert c.get("/api/stats").status_code == 503
    assert c.get("/api/literature/search", params={"q": "x"}).status_code == 503
    assert c.get("/health").status_code == 200  # core endpoints keep working without a database
