# Deploying

Two pieces, both free for a demo:

| Piece | Host | Why |
|---|---|---|
| Frontend (React/Vite, static) | **Netlify** | Static files, instant deploys |
| Backend (FastAPI + BLAST+) | **Render** (Docker, free plan) | Runs the `backend/Dockerfile`, which installs BLAST+ |
| Database | **Supabase** (already set up) | No change |

Configuration lives in the repo: [`netlify.toml`](../netlify.toml) and [`render.yaml`](../render.yaml).

## 1. Backend on Render

1. Sign in at <https://render.com> with GitHub.
2. **New > Blueprint**, pick this repository. Render reads `render.yaml` and proposes the service `phytofusion-api`.
3. Fill the three secrets it asks for:
   - `SUPABASE_URL`: `https://<project-ref>.supabase.co`
   - `SUPABASE_SERVICE_ROLE_KEY`: Supabase dashboard > Project Settings > API (backend only, never in the frontend)
   - `CORS_ORIGINS`: your Netlify address, for example `https://phytofusion.netlify.app` (no trailing slash). Several origins are separated by commas. Put a placeholder first and update it after step 2.
4. Deploy. When it is live, open `https://<service>.onrender.com/health`. It should answer `ok`.

The first build takes a few minutes because it installs BLAST+.

## 2. Frontend on Netlify

1. Sign in at <https://app.netlify.com> with GitHub, then **Add new site > Import an existing project**, pick this repository, and branch `main`.
2. The build settings come from `netlify.toml` (base `frontend`, publish `dist`). Leave them.
3. **Site configuration > Environment variables**: add `VITE_API_URL` = `https://<service>.onrender.com`.
4. Deploy, then copy the site address into Render's `CORS_ORIGINS` and redeploy the backend.

Routes use `#/...` addresses, so no redirect rules are needed.

## Free-plan behaviour to know about

- **Sleeping.** Render's free service sleeps after about 15 minutes idle. The first request afterwards takes 30 to 60 seconds. Open `/health` a minute before a demo.
- **Memory.** 512 MB. The comparison only searches the candidate genes, so it fits; searching two whole proteomes against each other would not.
- **Short disk.** Nothing is stored on the server. All data is in Supabase.

## Before going public

- The API has **no login**. Anyone who finds the address can call it and write to the database. Fine for a hackathon demo with public data; do not store anything private.
- Protein sequences must already be in Supabase for Compare to work. Run the seed with `--proteins ... --apply` once (see `docs/SOURCES.md`).
- Merging to `main` does not deploy the database. Migrations are applied with the Deploy workflow (see `docs/CICD.md`).

## Updating

Both hosts redeploy when `main` changes. The flow is: push to `dev`, open a PR, wait for `ci-passed`, merge.
