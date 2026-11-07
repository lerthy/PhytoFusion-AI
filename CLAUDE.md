# Guidance for AI coding assistants

Read [Context.md](Context.md) for the project plan and [docs/SCIENTIFIC_GUIDELINES.md](docs/SCIENTIFIC_GUIDELINES.md) before changing anything scientific.

## Non-negotiable rules
1. **No invented biology.** Gene functions, pathways and results must come from a cited source (PMID/DOI). If unknown, say unknown.
2. **No numeric compatibility, success or efficacy claims.** Use the categorical values in `app/genebridge.py`. CI greps for violations.
3. **Say "hypothetical" and "computational".** Never write that a plant "has been engineered" or that a compound "cures" anything.
4. **Every pathway edge and finding needs a source and an evidence level.** The code and schema enforce this; do not weaken it.
5. **Evidence levels are classes, not probabilities.**

## Engineering conventions
- Backend: Python 3.11+, FastAPI, ruff (line length 100). Run `ruff check . && ruff format . && pytest` from `backend/` before finishing.
- Coverage gate is 85%. Add tests with every change; table-driven `pytest.mark.parametrize` is preferred.
- Database: Supabase Postgres. Add a **new** migration in `supabase/migrations/` (numbered, never edit applied ones) and extend `supabase/tests/schema_test.sql`.
- No AWS-specific code. Keep database access behind a thin data layer so the later AWS move stays easy (see docs/STACK.md).
- Secrets: never commit `.env`. The Supabase service-role key is backend-only.

## UI
Follow [docs/DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md): use the semantic tokens in `frontend/src/styles.css`, never raw hex in components; never convey meaning by colour alone; every input needs a visible label and field-level errors; every data view needs loading, empty and error states.

## Scope discipline
One deep case study (S. barbata → S. baicalensis, KPS family). Do not build a generic chatbot, train new models, or process raw sequencing data.
