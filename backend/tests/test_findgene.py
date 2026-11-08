import httpx
import pytest
from fastapi.testclient import TestClient

from app import routes
from app.comparison import BlastHit
from app.explain import RateLimiter
from app.findgene import (
    FetchError,
    QueryError,
    clean_sequence,
    fetch_ncbi_protein,
    find_genes,
    resolve_query,
)
from app.main import app

PROTEIN = "MAFAWQTTSLLSSPNRGCLPAALHIPATSSAACATIGAIPFWKLPITIMSLRQ"  # 54 aa


# ---- query parsing --------------------------------------------------------------------------
def test_clean_sequence_strips_spaces_numbers_and_stop():
    assert clean_sequence("mafawqttsllsspnrgclpaalhipatss\n1 aacatigaipf*") == (
        "MAFAWQTTSLLSSPNRGCLPAALHIPATSSAACATIGAIPF"
    )


@pytest.mark.parametrize(
    "raw, message",
    [
        ("MAFAW-QTTS" * 6, "amino acid letters"),
        ("MAFAW", "too short"),
        ("M" * 5001, "too long"),
        ("ACGTACGTAC" * 6, "DNA"),
    ],
)
def test_clean_sequence_rejects(raw, message):
    with pytest.raises(QueryError, match=message):
        clean_sequence(raw)


def test_resolve_pasted_sequence_and_fasta():
    assert resolve_query(PROTEIN).kind == "sequence"
    fasta = resolve_query(
        f">WJZ49120.1 KPS2 [Scutellaria barbata]\n{PROTEIN[:30]}\n{PROTEIN[30:]}\n"
    )
    assert (fasta.kind, fasta.name, fasta.sequence) == ("fasta", "WJZ49120.1", PROTEIN)


def test_resolve_accession_uses_the_fetcher():
    seen = []

    def fetch(accession):
        seen.append(accession)
        return f">{accession} test\n{PROTEIN}"

    query = resolve_query("WJZ49120.1", fetch=fetch)
    assert seen == ["WJZ49120.1"] and (query.kind, query.name, query.sequence) == (
        "accession",
        "WJZ49120.1",
        PROTEIN,
    )
    assert resolve_query("NP_001234.1", fetch=fetch).kind == "accession"


@pytest.mark.parametrize("text", ["", "   ", ">\nMAFAW", ">only-a-header"])
def test_resolve_rejects_unusable_text(text):
    with pytest.raises(QueryError):
        resolve_query(text)


def test_resolve_accession_with_no_sequence_is_a_fetch_error():
    with pytest.raises(FetchError):
        resolve_query("WJZ49120.1", fetch=lambda a: ">")


# ---- NCBI fetch -------------------------------------------------------------------------------
def client_for(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_ncbi_protein_returns_fasta():
    seen = {}

    def handler(request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, text=f">WJZ49120.1 x\n{PROTEIN}\n")

    text = fetch_ncbi_protein("WJZ49120.1", client_for(handler))
    assert text.startswith(">WJZ49120.1") and seen["params"]["db"] == "protein"
    assert seen["params"]["id"] == "WJZ49120.1"


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(400, text="bad"),
        httpx.Response(200, text="Error: nothing"),
        httpx.Response(200, text=""),
    ],
)
def test_fetch_ncbi_protein_errors(response):
    with pytest.raises(FetchError, match="no protein record"):
        fetch_ncbi_protein("XX000000", client_for(lambda r: response))


def test_fetch_ncbi_protein_connection_error():
    def handler(request):
        raise httpx.ConnectError("down", request=request)

    with pytest.raises(FetchError, match="could not be reached"):
        fetch_ncbi_protein("WJZ49120.1", client_for(handler))


# ---- BLAST ranking ----------------------------------------------------------------------------
def hit(subject, pident, length, evalue, bits):
    return BlastHit("query", subject, pident, length, evalue, bits)


def test_find_genes_ranks_labels_and_limits():
    qlen = len(PROTEIN)
    hits = [
        hit("G_far", 30.0, 40, 1e-5, 60.0),
        hit("G_same", 100.0, qlen, 0.0, 900.0),
        hit("G_rel", 62.0, qlen, 1e-60, 400.0),
        hit("G_rel", 55.0, qlen, 1e-30, 200.0),  # duplicate subject: only the best row counts
        hit("G_partial", 100.0, 20, 1e-9, 90.0),  # identical but covers a small part only
    ]
    got = find_genes(PROTEIN, {"G": "MKV"}, blast=lambda q, s: hits, top=4)
    assert [g.gene_id for g in got] == ["G_same", "G_rel", "G_partial", "G_far"]
    kinds = {g.gene_id: g.kind for g in got}
    assert kinds == {
        "G_same": "same_protein",
        "G_rel": "related",
        "G_partial": "weakly_related",
        "G_far": "weakly_related",
    }
    assert find_genes(PROTEIN, {"G": "MKV"}, blast=lambda q, s: hits, top=2)[1].gene_id == "G_rel"


def test_find_genes_writes_query_and_proteins_for_blast():
    seen = {}

    def blast(query, subject):
        seen["query"], seen["subject"] = query.read_text(), subject.read_text()
        return []

    assert find_genes(PROTEIN, {"G1": "MKVL*", "G2": "MAAA"}, blast=blast) == []
    assert f">query\n{PROTEIN}" in seen["query"]
    assert ">G1\nMKVL\n" in seen["subject"] and ">G2\nMAAA\n" in seen["subject"]


def test_find_genes_needs_proteins():
    with pytest.raises(ValueError):
        find_genes(PROTEIN, {})


# ---- the route --------------------------------------------------------------------------------
@pytest.fixture
def api(seeded, monkeypatch):
    app.dependency_overrides[routes.get_store] = lambda: seeded.store
    monkeypatch.setattr(routes, "_find_limiter", RateLimiter())
    routes._protein_cache.clear()
    client = TestClient(app)
    host = {s["scientific_name"]: s["id"] for s in client.get("/api/species").json()}["Host sp."]
    yield client, host
    routes._protein_cache.clear()
    app.dependency_overrides.clear()


def blast_ok(query, subject):
    return [BlastHit("query", "SbaiKPS1", 100.0, len(PROTEIN), 0.0, 900.0)]


def test_route_returns_hits_with_location_and_caches_proteins(api, monkeypatch):
    client, host = api
    monkeypatch.setattr(
        routes, "find_genes", lambda seq, prot: find_genes(seq, prot, blast=blast_ok)
    )
    body = client.post("/api/genes/find", json={"species_id": host, "query": PROTEIN}).json()
    assert body["computed_by"] == "BLAST+ (blastp)"
    assert body["query"] == {"kind": "sequence", "name": "pasted sequence", "length": len(PROTEIN)}
    (top,) = body["hits"]
    assert (top["gene_id"], top["kind"], top["percent_identity"]) == (
        "SbaiKPS1",
        "same_protein",
        100.0,
    )
    assert top["location"]["start_bp"] == 1000 and top["location"]["strand"] == "+"
    assert host in routes._protein_cache  # a second search reuses it


def test_route_hit_for_an_unsaved_gene_has_no_location(api, monkeypatch):
    client, host = api

    def blast(q, s):
        return [BlastHit("query", "orphan", 70.0, 50, 1e-30, 200.0)]

    monkeypatch.setattr(routes, "find_genes", lambda seq, prot: find_genes(seq, prot, blast=blast))
    # "orphan" has a protein but no gene row in the annotation
    body = client.post("/api/genes/find", json={"species_id": host, "query": PROTEIN}).json()
    assert body["hits"][0]["location"] is None


@pytest.mark.parametrize(
    "query, error, status",
    [("MAFAW", QueryError("short"), 422), ("WJZ49120.1", FetchError("no record"), 502)],
)
def test_route_query_errors(api, monkeypatch, query, error, status):
    client, host = api

    def boom(text):
        raise error

    monkeypatch.setattr(routes, "resolve_query", boom)
    assert (
        client.post("/api/genes/find", json={"species_id": host, "query": query}).status_code
        == status
    )


def test_route_unknown_plant_and_empty_query(api):
    client, _ = api
    r = client.post("/api/genes/find", json={"species_id": "nope", "query": PROTEIN})
    assert r.status_code == 404 and "No protein sequences" in r.json()["detail"]
    assert client.post("/api/genes/find", json={"species_id": "x", "query": ""}).status_code == 422


def test_route_missing_blast_is_503(api, monkeypatch):
    client, host = api

    def missing(seq, prot):
        raise RuntimeError("blastp not found on PATH")

    monkeypatch.setattr(routes, "find_genes", missing)
    r = client.post("/api/genes/find", json={"species_id": host, "query": PROTEIN})
    assert r.status_code == 503 and "blastp" in r.json()["detail"]


def test_route_rate_limits(api, monkeypatch):
    client, host = api
    monkeypatch.setattr(routes, "_find_limiter", RateLimiter(per_ip_per_hour=1))
    monkeypatch.setattr(routes, "find_genes", lambda seq, prot: [])
    payload = {"species_id": host, "query": PROTEIN}
    assert client.post("/api/genes/find", json=payload).status_code == 200
    assert client.post("/api/genes/find", json=payload).status_code == 429
