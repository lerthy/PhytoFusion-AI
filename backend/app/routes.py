"""Persistence-backed API routes. All of them need Supabase; they answer 503 when it is not set."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from .crispr import ScenarioInput, simulate
from .explain import (
    KINDS,
    Backend,
    ExplainRefused,
    ExplainUnavailable,
    RateLimiter,
    backend_from_env,
    explain,
)
from .genebridge import AssessmentInput, assess
from .literature import Embedder, embedder_from_env
from .pipeline import assessment_for, compare_proteomes
from .repository import Repository
from .store import NotConfigured, Store, StoreError, SupabaseStore

router = APIRouter(prefix="/api")

Level = Literal["strong", "moderate", "limited"]


@lru_cache(maxsize=1)
def _cached_store() -> SupabaseStore:
    return SupabaseStore.from_env()


def get_store() -> Store:
    try:
        return _cached_store()
    except NotConfigured as exc:
        raise HTTPException(503, f"Database not configured: {exc}") from exc


def get_repo(store: Store = Depends(get_store)) -> Repository:
    return Repository(store)


def get_embedder() -> Embedder:
    try:
        return embedder_from_env()
    except NotConfigured as exc:
        raise HTTPException(503, f"Embeddings not configured: {exc}") from exc


def get_ai_backend() -> Backend:
    try:
        return backend_from_env()
    except NotConfigured as exc:
        raise HTTPException(503, f"AI explanations are not configured: {exc}") from exc


_explain_limiter = RateLimiter()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _not_found(exc: LookupError) -> HTTPException:
    return HTTPException(404, str(exc.args[0]))


# ---- genomes -----------------------------------------------------------------------------
@router.get("/stats")
def stats(repo: Repository = Depends(get_repo)) -> dict[str, int]:
    return repo.stats()


@router.get("/species")
def species(repo: Repository = Depends(get_repo)) -> list[dict[str, Any]]:
    return repo.list_species()


@router.get("/genome/{species_id}")
def genome(species_id: str, repo: Repository = Depends(get_repo)) -> dict[str, Any]:
    try:
        return repo.genome(species_id)
    except LookupError as exc:
        raise _not_found(exc) from exc


@router.get("/genes/lookup")
def gene_lookup(species: str, gene: str, repo: Repository = Depends(get_repo)) -> dict[str, Any]:
    try:
        return repo.gene_lookup(species, gene)
    except LookupError as exc:
        raise _not_found(exc) from exc


# ---- evidence and literature ---------------------------------------------------------------
class EvidenceIn(BaseModel):
    finding: str = Field(min_length=1)
    level: Level
    pmid: str | None = None
    doi: str | None = None
    title: str | None = None


@router.post("/evidence")
def add_evidence(body: EvidenceIn, repo: Repository = Depends(get_repo)) -> dict[str, Any]:
    try:
        return repo.add_evidence(body.finding, body.level, body.pmid, body.doi, body.title)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/evidence")
def list_evidence(repo: Repository = Depends(get_repo)) -> list[dict[str, Any]]:
    return repo.list_evidence()


class LiteratureIn(BaseModel):
    evidence_id: str
    text: str = Field(min_length=1)


@router.post("/literature")
def add_literature(
    body: LiteratureIn,
    repo: Repository = Depends(get_repo),
    embedder: Embedder = Depends(get_embedder),
) -> dict[str, int]:
    try:
        return {"chunks": repo.add_literature(body.evidence_id, body.text, embedder)}
    except LookupError as exc:
        raise _not_found(exc) from exc


@router.get("/literature/search")
def search_literature(
    q: str,
    k: int = 5,
    repo: Repository = Depends(get_repo),
    embedder: Embedder = Depends(get_embedder),
) -> list[dict[str, Any]]:
    """Retrieval only: passages are returned verbatim with their PMID/DOI, nothing is generated."""
    return repo.search_literature(q, embedder, max(1, min(k, 20)))


# ---- comparison pipeline ---------------------------------------------------------------------
class CompareRequest(BaseModel):
    host_species_id: str
    donor_species_id: str
    candidate_gene_ids: list[str] = Field(min_length=1)
    persist: bool = False


@router.post("/pipeline/compare")
def pipeline_compare(body: CompareRequest, repo: Repository = Depends(get_repo)) -> list[dict]:
    """BLAST donor candidates against the host proteome; sequence relationship only."""
    host, donor = repo.proteins(body.host_species_id), repo.proteins(body.donor_species_id)
    try:
        pairs = compare_proteomes(host, donor, body.candidate_gene_ids)
    except (KeyError, ValueError) as exc:
        raise HTTPException(422, str(exc.args[0])) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc

    out = []
    for pair in pairs:
        item: dict[str, Any] = {
            "donor_gene": pair.donor_id,
            "host_gene": pair.host_id,
            "percent_identity": pair.hit.pident if pair.hit else None,
            "evalue": pair.hit.evalue if pair.hit else None,
            "reciprocal_best_hit": pair.reciprocal,
            "sequence_relationship": pair.sequence_relationship,
        }
        if body.persist and pair.host_id:
            data = assessment_for(pair)
            saved = repo.save_comparison(
                repo.find_gene(pair.host_id, body.host_species_id)["id"],
                repo.find_gene(pair.donor_id, body.donor_species_id)["id"],
                data,
                assess(data),
                pair.hit.pident if pair.hit else None,
            )
            item["comparison_id"] = saved["id"]
        out.append(item)
    return out


class AssessIn(BaseModel):
    sequence: Literal["related", "weakly_related", "unknown"]
    functional: Literal["characterized", "predicted"]
    pathway: Literal["supported", "incomplete", "unknown"]
    expression: Literal["supporting", "conflicting", "unavailable"]
    context: Literal["characterized", "uncertain"]


class ComparisonIn(BaseModel):
    host_species_id: str
    donor_species_id: str
    host_gene: str
    donor_gene: str
    percent_identity: float | None = Field(default=None, ge=0, le=100)
    assessment: AssessIn


@router.post("/comparisons")
def save_comparison(body: ComparisonIn, repo: Repository = Depends(get_repo)) -> dict[str, Any]:
    data = AssessmentInput(**body.assessment.model_dump())
    try:
        return repo.save_comparison(
            repo.find_gene(body.host_gene, body.host_species_id)["id"],
            repo.find_gene(body.donor_gene, body.donor_species_id)["id"],
            data,
            assess(data),
            body.percent_identity,
        )
    except LookupError as exc:
        raise HTTPException(422, str(exc.args[0])) from exc


@router.get("/comparisons")
def list_comparisons(repo: Repository = Depends(get_repo)) -> list[dict[str, Any]]:
    return repo.list_comparisons()


# ---- pathways ----------------------------------------------------------------------------
class PathwayIn(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    elements: list[dict[str, Any]]


@router.post("/pathways")
def save_pathway(body: PathwayIn, repo: Repository = Depends(get_repo)) -> dict[str, Any]:
    try:
        row = repo.save_pathway(body.name, body.elements, body.description)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"id": row["id"], "name": row["name"]}


@router.get("/pathways")
def list_pathways(repo: Repository = Depends(get_repo)) -> list[dict[str, Any]]:
    return repo.list_pathways()


@router.get("/pathways/{pathway_id}")
def get_pathway(pathway_id: str, repo: Repository = Depends(get_repo)) -> dict[str, Any]:
    try:
        return repo.get_pathway(pathway_id)
    except LookupError as exc:
        raise _not_found(exc) from exc


# ---- scenarios ---------------------------------------------------------------------------
class ScenarioIn(BaseModel):
    type: Literal["host_modification", "donor_integration"]
    host_species: str
    target_gene_id: str
    donor_species: str | None = None
    chromosome: str | None = None
    documented_function: str | None = None
    pathway: str | None = None
    references: list[str] = []
    assessment: AssessIn


@router.post("/scenarios")
def save_scenario(body: ScenarioIn, repo: Repository = Depends(get_repo)) -> dict[str, Any]:
    """Simulate and store. The target gene and species must already be in the database."""
    data = body.model_dump()
    assessment_input = data.pop("assessment")
    assessment = assess(AssessmentInput(**assessment_input))
    data["references"] = tuple(data["references"])
    try:
        result = simulate(ScenarioInput(assessment=assessment, **data))
        scenario = repo.save_scenario(result, assessment_input)
    except LookupError as exc:
        raise HTTPException(422, str(exc.args[0])) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return repo.get_scenario(scenario["id"])


@router.get("/scenarios")
def list_scenarios(repo: Repository = Depends(get_repo)) -> list[dict[str, Any]]:
    return repo.list_scenarios()


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str, repo: Repository = Depends(get_repo)) -> dict[str, Any]:
    try:
        return repo.get_scenario(scenario_id)
    except LookupError as exc:
        raise _not_found(exc) from exc


def store_error_handler(_request: Any, exc: StoreError) -> Any:
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=502, content={"detail": str(exc)})


# ---- AI explanation (optional; needs ANTHROPIC_API_KEY) -------------------------------------
class ExplainRequest(BaseModel):
    kind: Literal["comparison", "report"]
    facts: dict[str, Any]


@router.post("/explain")
def explain_result(
    body: ExplainRequest, request: Request, backend: Backend = Depends(get_ai_backend)
) -> dict[str, str]:
    """A short plain-language explanation of facts the app already computed. Written by Claude."""
    if body.kind not in KINDS:
        raise HTTPException(422, "Unknown kind")
    if not _explain_limiter.allow(_client_ip(request)):
        raise HTTPException(429, "Too many explanations requested. Try again later.")
    try:
        text = explain(body.kind, body.facts, backend)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except ExplainUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except ExplainRefused as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"text": text, "model": backend.model}
