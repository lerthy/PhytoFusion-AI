import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

GOOD = {
    "sequence": "related",
    "functional": "characterized",
    "pathway": "supported",
    "expression": "supporting",
    "context": "characterized",
}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_assess_strong():
    response = client.post("/api/genebridge/assess", json=GOOD)
    assert response.status_code == 200
    body = response.json()
    assert body["level"] == "strong"
    assert body["deserves_investigation"] is True


def test_assess_limited_reports_missing():
    response = client.post("/api/genebridge/assess", json={**GOOD, "functional": "predicted"})
    body = response.json()
    assert body["level"] == "limited"
    assert body["missing_information"]


@pytest.mark.parametrize("field", list(GOOD))
def test_missing_field_is_rejected(field):
    payload = {k: v for k, v in GOOD.items() if k != field}
    assert client.post("/api/genebridge/assess", json=payload).status_code == 422


def test_invalid_enum_is_rejected():
    assert (
        client.post("/api/genebridge/assess", json={**GOOD, "sequence": "95%"}).status_code == 422
    )


def test_response_has_no_numeric_score():
    body = client.post("/api/genebridge/assess", json=GOOD).json()
    assert not any(isinstance(v, int | float) and not isinstance(v, bool) for v in body.values())


SIM = {
    "type": "donor_integration",
    "host_species": "Host sp.",
    "donor_species": "Donor sp.",
    "target_gene_id": "GENE1",
    "documented_function": "Published function text",
    "pathway": "Example pathway",
    "references": ["PMID:1"],
    "assessment": GOOD,
}


def test_simulate_returns_report_with_limitations():
    response = client.post("/api/scenarios/simulate", json=SIM)
    assert response.status_code == 200
    body = response.json()
    assert body["limitations"]
    assert "Virtual plant report" in body["report_markdown"]
    assert body["evidence_level"] == "strong"


def test_simulate_invalid_scenario_returns_422():
    response = client.post("/api/scenarios/simulate", json={**SIM, "donor_species": None})
    assert response.status_code == 422
    assert "donor_species" in response.json()["detail"]


@pytest.mark.parametrize(
    "pident,evalue,expected",
    [(80, 1e-50, "related"), (20, 1e-5, "weakly_related"), (80, 1, "unknown")],
)
def test_classify_endpoint(pident, evalue, expected):
    response = client.post("/api/comparison/classify", json={"pident": pident, "evalue": evalue})
    assert response.json() == {"sequence_relationship": expected}


@pytest.mark.parametrize("payload", [{"pident": 101, "evalue": 1}, {"pident": 50, "evalue": -1}])
def test_classify_rejects_out_of_range(payload):
    assert client.post("/api/comparison/classify", json=payload).status_code == 422


def test_cors_allows_local_frontend():
    response = client.options(
        "/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
