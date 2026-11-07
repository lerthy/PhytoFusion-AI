# Architecture

```
Scientific sources (Genome Warehouse, NCBI, PubMed, PubChem)
        │
 [1] Ingestion ──► Supabase Postgres + Storage
        │
 [2] Comparative genomics (BLAST, chromosome mapping)
        │
 [3] Pathway intelligence (NetworkX graph)
        │
 [4] GeneBridge (assessment + literature RAG)
        │
 [5] CRISPR scenario simulator
        │
 FastAPI ──► React app (6 screens)
```

## Engines

| # | Engine | Status | Code |
|---|---|---|---|
| 1 | Data ingestion | GFF3 parsing done; FASTA/protein loading and DB writes next | `app/ingestion/` |
| 2 | Comparative genomics | FASTA and BLAST parsing, reciprocal best hits, categorical classification, gene mapping, injectable `blastp` wrapper | `app/comparison.py` |
| 3 | Pathway intelligence | Graph model with enforced evidence, Cytoscape export | `app/pathway.py` |
| 4 | GeneBridge | Categorical assessment done; RAG next | `app/genebridge.py`, `app/evidence.py` |
| 5 | CRISPR simulator | Both scenario types, qualitative output, mandatory limitations, Markdown report | `app/crispr.py` |

## Data flow rules
- Engines pass structured data, not free text. The simulator may not add biological facts that GeneBridge did not supply.
- Each finding stored in Postgres links to an `evidence` row (`finding_evidence`).
- Literature is chunked into `literature_chunks` with embeddings. The `match_literature()` SQL function does vector search, and the RAG layer returns the chunk's PMID/DOI with every answer.

## API (current)
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/api/genebridge/assess` | Categorical compatibility assessment |
| POST | `/api/comparison/classify` | BLAST hit (identity, e-value) to a categorical sequence relationship |
| POST | `/api/scenarios/simulate` | Hypothetical scenario result plus Markdown report |

## Planned API
`/api/species`, `/api/genes`, `/api/comparisons`, `/api/pathways/{id}/graph`, `/api/scenarios`, `/api/reports/{scenario_id}`.

## Frontend screens
All six are implemented in `frontend/src/screens/`: Dashboard, Genome Explorer, GeneBridge, Pathway Explorer, CRISPR Studio, Virtual Plant Report (details in Context.md). Genome and pathway data are loaded from the team's own files in the browser, so the app ships no invented biology.
