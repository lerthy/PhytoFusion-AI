# PhytoFusion AI

**Cross-species genetic engineering intelligence.** A computational platform that evaluates, in silico, whether a genetic trait from one medicinal plant could theoretically be integrated into another using CRISPR. Built for EthnoHack, Track 2.

> This is a computational simulation. It does not perform genetic engineering, does not claim an engineered organism exists, and does not claim improved medicinal efficacy.

## The case study

*Scutellaria barbata* (donor, clerodane diterpenoids) → *Scutellaria baicalensis* (host, flavonoids). We compare the KPS diterpene synthase family, assess compatibility with explainable evidence classes, and simulate hypothetical CRISPR scenarios.

Full scientific and technical plan: [Context.md](Context.md).

## Docs

| Doc | Purpose |
|---|---|
| [Context.md](Context.md) | Original project plan (science + technical) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | The five engines and how they connect |
| [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) | File-by-file reference for the code that exists |
| [docs/SCIENTIFIC_GUIDELINES.md](docs/SCIENTIFIC_GUIDELINES.md) | Rules that keep the science honest |
| [docs/STACK.md](docs/STACK.md) | Supabase stack and the future AWS plan |
| [docs/SOURCES.md](docs/SOURCES.md) | Papers, genome records and the KPS gene matching, with links |
| [docs/DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md) | UI style, palette, accessibility checks |
| [docs/VALIDATION.md](docs/VALIDATION.md) | How the gene matching was checked, with numbers, and what is not validated |
| [docs/DEMO.md](docs/DEMO.md) | A click-by-click script for recording the demo |
| [docs/TESTING.md](docs/TESTING.md) | Test strategy and how to run tests |
| [docs/CICD.md](docs/CICD.md) | CI/CD pipelines and required secrets |
| [docs/DEVPOST.md](docs/DEVPOST.md) | Devpost submission text, field by field, plus a checklist against the challenge requirements |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Hosting: Netlify (frontend) and Render (backend), step by step |
| [docs/ROADMAP.md](docs/ROADMAP.md) | What is built, what is next |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | Biology and project terms |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Workflow for the team |
| [CLAUDE.md](CLAUDE.md) | Guidance for AI coding assistants |

## Quick start

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                       # unit tests + 85% coverage gate
ruff check . && ruff format --check .
uvicorn app.main:app --reload --env-file ../.env   # http://localhost:8000/docs
```

Seed a genome (dry run by default; add `--apply` to write to Supabase):
```bash
cd backend
python -m app.ingestion.seed --species "Scutellaria baicalensis" --role host \
  --accession <ACCESSION> --source "Genome Warehouse" --gff host.gff3 --proteins host.faa
```

Frontend (separate terminal):
```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173 (set VITE_API_URL to change the backend)
npm test                     # vitest
```

Database: apply `supabase/migrations/*.sql` to a Supabase project (or `supabase start` locally), then run `supabase/tests/schema_test.sql`. See [docs/STACK.md](docs/STACK.md).

## Repository layout

```
backend/            FastAPI app, engines, unit tests
  app/evidence.py     evidence classification (strong / moderate / limited)
  app/genebridge.py   categorical gene compatibility assessment
  app/pathway.py      gene -> enzyme -> reaction -> compound graph
  app/ingestion/      GFF3 parsing and gene ID normalisation
  app/comparison.py   FASTA/BLAST parsing, reciprocal best hits, blastp wrapper
  app/crispr.py       hypothetical scenario simulator and report
  app/store.py        Supabase REST client + in-memory twin for tests
  app/repository.py   all table reads and writes
  app/routes.py       persistence-backed API routes
  app/pipeline.py     BLAST donor candidates against the host proteome
  app/literature.py   chunking + embeddings for citation-only literature search
  app/ingestion/seed.py  load a genome into the database
supabase/           migrations and SQL schema tests
frontend/           React + TypeScript: About page + app (4 steps, 7 views), vitest tests
docs/               project documentation
.github/workflows/  CI and deploy pipelines
```
