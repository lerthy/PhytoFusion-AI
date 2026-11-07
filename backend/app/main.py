"""FastAPI entrypoint."""

from __future__ import annotations

import os
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import __version__
from .comparison import BlastHit, classify_sequence_relationship
from .crispr import ScenarioInput, ScenarioResult, render_report_markdown, simulate
from .genebridge import Assessment, AssessmentInput, assess
from .routes import router, store_error_handler
from .store import StoreError

app = FastAPI(title="PhytoFusion AI", version=__version__)
app.include_router(router)
app.add_exception_handler(StoreError, store_error_handler)


def cors_origins(raw: str) -> list[str]:
    """Split CORS_ORIGINS, tolerating spaces, quotes and trailing slashes."""
    origins = (part.strip().strip("\"'").rstrip("/") for part in raw.split(","))
    return [o for o in origins if o]


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(os.environ.get("CORS_ORIGINS", "http://localhost:5173")),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

Sequence = Literal["related", "weakly_related", "unknown"]
Level = Literal["strong", "moderate", "limited"]


class AssessRequest(BaseModel):
    sequence: Sequence
    functional: Literal["characterized", "predicted"]
    pathway: Literal["supported", "incomplete", "unknown"]
    expression: Literal["supporting", "conflicting", "unavailable"]
    context: Literal["characterized", "uncertain"]


class AssessResponse(BaseModel):
    level: Level
    deserves_investigation: bool
    missing_information: list[str]
    concerns: list[str]
    explanation: str


class ClassifyRequest(BaseModel):
    pident: float = Field(ge=0, le=100)
    evalue: float = Field(ge=0)


class ClassifyResponse(BaseModel):
    sequence_relationship: Sequence


class SimulateRequest(BaseModel):
    type: Literal["host_modification", "donor_integration"]
    host_species: str
    target_gene_id: str
    donor_species: str | None = None
    chromosome: str | None = None
    documented_function: str | None = None
    pathway: str | None = None
    references: list[str] = []
    assessment: AssessRequest


class SimulateResponse(BaseModel):
    type: Literal["host_modification", "donor_integration"]
    host_species: str
    donor_species: str | None
    target_gene_id: str
    chromosome: str | None
    documented_function: str | None
    pathway: str | None
    scenario: str
    predicted_consequences: list[str]
    compatibility_issues: list[str]
    missing_information: list[str]
    limitations: list[str]
    evidence_level: Level
    references: list[str]
    assessment: dict[str, str] | None = None
    report_markdown: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post("/api/genebridge/assess", response_model=AssessResponse)
def genebridge_assess(req: AssessRequest) -> Assessment:
    return assess(AssessmentInput(**req.model_dump()))


@app.post("/api/comparison/classify", response_model=ClassifyResponse)
def comparison_classify(req: ClassifyRequest) -> dict[str, str]:
    hit = BlastHit("q", "s", req.pident, 0, req.evalue, 0.0)
    return {"sequence_relationship": classify_sequence_relationship(hit)}


@app.post("/api/scenarios/simulate", response_model=SimulateResponse)
def scenarios_simulate(req: SimulateRequest) -> dict:
    data = req.model_dump()
    assessment_input = data.pop("assessment")
    assessment = assess(AssessmentInput(**assessment_input))
    data["references"] = tuple(data["references"])
    try:
        result: ScenarioResult = simulate(ScenarioInput(assessment=assessment, **data))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        **result.__dict__,
        "assessment": assessment_input,
        "report_markdown": render_report_markdown(result),
    }
