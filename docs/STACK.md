# PhytoFusion AI: Stack (Supabase edition)

Supersedes the AWS deployment section of `Context.md`. Nothing here depends on AWS.

## Now (hackathon)

| Layer | Choice |
|---|---|
| Frontend | React + TypeScript + Tailwind, Cytoscape.js, Plotly |
| Backend | Python + FastAPI (Biopython, BLAST+, pandas, NetworkX, RDKit) |
| Database | Supabase Postgres (schema in `supabase/migrations/0001_init.sql`) |
| Vector search | pgvector in Supabase (`match_literature()` function), no FAISS needed |
| File storage | Supabase Storage, bucket `genomes` (FASTA, GFF3, protein files) |
| AI / RAG | LLM API + embeddings stored in `literature_chunks` |
| Local dev | `supabase start` (local stack via CLI) or a free hosted project |

### What Supabase covers
- All 9 tables from the plan, plus evidence linking and RAG chunks.
- Vector search, so no separate vector DB.
- Storage for genome files.
- We do not use Supabase Auth or Realtime. The app has no user accounts.

### What Supabase does not cover
- **Running FastAPI**, which is a Python server with BLAST+ installed. Run it locally or in Docker for the demo. If a public URL is needed, deploy the container to a simple host such as Render or Fly.io.
- **Hosting the frontend**: a static host such as Vercel or Netlify works.

### Setup
1. Create a Supabase project, or run `supabase start` locally.
2. Apply the schema with `supabase db push`.
3. Create a Storage bucket named `genomes`.
4. Put `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env`. Only the backend and ingestion scripts use the service key, and it must never reach the frontend.
5. The frontend may use the anon key for read-only queries. RLS allows public reads and no public writes.

### Notes
- Embedding dimension is set to 1536. Change `vector(1536)` in the migration if you pick a different embedding model.
- Keep the genome files small. Store only the assemblies and annotations you need, since the free tier has storage limits.
- Each finding must link to an `evidence` row with a PMID or DOI. The schema enforces this on `evidence`.

## Later: AWS migration plan (not started)

Do this only after the prototype works.

1. **Database:** move Supabase Postgres to RDS or Aurora PostgreSQL with the `pgvector` extension. Use `pg_dump` and `pg_restore`. The schema is plain Postgres plus pgvector, so it should port without changes.
2. **Files:** copy the `genomes` bucket to S3 and switch the storage client in the backend.
3. **Backend:** containerize FastAPI and run it on ECS Fargate behind an ALB.
4. **Frontend:** build the static app and serve it from S3 + CloudFront.
5. **Secrets and config:** move env vars to Secrets Manager or SSM Parameter Store.
6. **Cutover:** run both stacks in parallel, check results match, then change the frontend's API URL.

To keep this migration easy, access the database through a thin data layer in the backend and avoid Supabase-specific features. That way only the storage client and connection string change.
