# Testing

## Layers

| Layer | Tool | Location | Runs in CI job |
|---|---|---|---|
| Unit | pytest | `backend/tests/test_*.py` | `backend-test` (Python 3.11 and 3.12) |
| API | pytest + FastAPI TestClient | `backend/tests/test_api.py` | `backend-test` |
| Schema / DB | psql against Postgres + pgvector | `supabase/tests/schema_test.sql` | `schema-test` |
| Container smoke | docker run + `/health` | | `docker-build` |
| Frontend | `tsc`, vitest (GFF3, pathway validation, routing and navigation grouping, API errors, genome mapping), build | `frontend/src/*.test.ts` | `frontend` |
| Scientific guardrails | grep rules | `ci.yml` | `science-guardrails` |
| Security | pip-audit, gitleaks | | `security` |

## Run locally
```bash
cd backend
pip install -e ".[dev]"
pytest                          # fails if coverage < 85%
pytest tests/test_genebridge.py -k strong
ruff check . && ruff format --check .
```
Schema tests (needs Postgres with the pgvector extension):
```bash
for f in supabase/migrations/*.sql; do psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"; done
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f supabase/tests/schema_test.sql
```
The schema test runs in a transaction and rolls back.

## What the tests protect
- **Evidence rules**: boundaries between strong, moderate and limited; references are required and deduplicated.
- **GeneBridge**: deterministic, categorical output, missing data is reported as missing, no `%` in explanations, API returns no numeric scores.
- **GFF3 ingestion**: malformed rows fail loudly with a line number.
- **Pathway graph**: edges without evidence or with unknown nodes are rejected.
- **Schema**: traceability constraint, enums, uniqueness, cascades and vector search.

## Writing tests
- Use `pytest.mark.parametrize` for input matrices.
- For every bug fix, add a regression test first.
- Put fixture files in `backend/tests/data/`.
- Tests needing external services should be marked `@pytest.mark.integration`.

## Visual checks
Done by hand with headless Chrome driven from a throwaway script outside the repo (it is not part
of CI). See the verified list in [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md).

## Known gaps
- The vector search test (section 5 of `schema_test.sql`) only runs where pgvector is installed, which CI provides.
- No component or browser tests yet. The React screens are type-checked and built in CI but not rendered by a test. Add Playwright for that.
- `run_blastp` is tested with a stubbed runner; it has not been run against a real BLAST+ install.
