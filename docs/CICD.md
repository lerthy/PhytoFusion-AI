# CI/CD

No AWS is used. Delivery targets Supabase. See [STACK.md](STACK.md) for the future AWS plan.

## CI: `.github/workflows/ci.yml`
Runs on every push to `main`, every PR, and when called by the deploy workflow.

| Job | What it checks |
|---|---|
| `backend-lint` | `ruff check` and `ruff format --check` |
| `backend-test` | pytest on Python 3.11 and 3.12, coverage gate 85%, coverage.xml artifact |
| `schema-test` | Applies all migrations to Postgres 16 + pgvector, runs `schema_test.sql`, then rebuilds from scratch to prove migrations apply cleanly |
| `docker-build` | Builds the backend image and hits `/health` in a running container |
| `frontend` | `npm ci`, lint, `tsc`, tests, build. Skips until `frontend/package.json` exists |
| `security` | `pip-audit` for vulnerable dependencies, gitleaks for committed secrets |
| `science-guardrails` | Fails on numeric compatibility claims or "has been engineered" style wording in app code |
| `ci-passed` | Single required check that fails if any job above failed |

## CD: `.github/workflows/deploy.yml`
Triggered manually (`workflow_dispatch`) or by pushing a tag like `v0.1.0`.
1. Re-runs the full CI.
2. Links the Supabase project and shows pending migrations (`supabase db push --dry-run`).
3. Applies them, but only on a tag push or when `dry_run` is set to false.

The job uses the GitHub environment `production`. Add required reviewers there to get a manual approval gate.

### Secrets to add (Settings, Secrets and variables, Actions)
| Secret | Where to get it |
|---|---|
| `SUPABASE_ACCESS_TOKEN` | Supabase dashboard, Account, Access Tokens |
| `SUPABASE_DB_PASSWORD` | Database password of the project |
| `SUPABASE_PROJECT_ID` | Project settings, Reference ID |

Gitleaks may also want `GITLEAKS_LICENSE` if the repository is under an organization.

## One-time GitHub setup
1. Create the `production` environment and add a reviewer.
2. Protect `main`: require PR and the `CI passed` check.
3. Dependabot is configured in `.github/dependabot.yml` (pip, npm, actions, docker).

## Not covered yet
- Backend hosting. Deploying the container (for example Render or Fly.io) is a later step. The image is already built and smoke-tested in CI.
- Frontend deployment (Vercel or Netlify) once the app exists.
- Neither CI file has been run on GitHub yet. Only the YAML syntax, backend tests and most of the schema tests were verified locally.
