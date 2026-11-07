# Contributing

## Workflow
1. Branch from `main`: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`.
2. Make a small change with tests.
3. Run locally from `backend/`: `ruff check . && ruff format --check . && pytest`.
4. Open a PR using the template. CI must pass (the `CI passed` check is the required gate).
5. Squash-merge into `main`.

## Rules
- Scientific claims need a PMID/DOI. See [docs/SCIENTIFIC_GUIDELINES.md](docs/SCIENTIFIC_GUIDELINES.md).
- Schema changes go in a new numbered migration, with matching tests in `supabase/tests/`.
- Do not commit `.env`, genome files or other large data. Use Supabase Storage.
- Commit messages: imperative, short subject (`Add KPS comparison endpoint`).

## Suggested team split
| Area | Owns |
|---|---|
| Science | Gene curation, evidence rows, limitations report |
| Bioinformatics | Ingestion, BLAST, chromosome mapping |
| AI / backend | GeneBridge, RAG, CRISPR simulator, API |
| Frontend | React screens, Cytoscape and Plotly views |
| Integration | Tests, CI, docs, pitch |

## Recommended branch protection (GitHub settings)
Require a PR, require the `CI passed` status check, and block force-pushes to `main`.
