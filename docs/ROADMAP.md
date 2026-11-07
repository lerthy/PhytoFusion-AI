# Roadmap

Deadline: **8 November 2026, 10:00 GMT+1**.

## Done
- [x] Project plan (Context.md)
- [x] Supabase schema with traceability constraints and RLS
- [x] Evidence classification, GeneBridge assessment, pathway graph, GFF3 parser
- [x] FastAPI skeleton with `/health` and `/api/genebridge/assess`
- [x] Unit, API and schema tests; CI and deploy workflows
- [x] Engine 2 (comparison) and Engine 5 (CRISPR simulator) with API endpoints
- [x] Frontend with all six screens, GFF3 and pathway-JSON loaders
- [x] Supabase project created, migrations 0001-0002 applied, `genomes` bucket, `.env` set up
- [x] Persistence layer, seed script, BLAST pipeline, evidence and literature endpoints (backend)
- [x] UI redesign, then simplified to 4 steps with progressive disclosure (design system, database-wired views, deep links, a11y states)

## Must have for the demo (in priority order)
1. [ ] Curate the KPS candidate genes and their publications into `evidence` (science team; the code takes this as input)
2. [ ] Download the two assemblies' GFF3 and protein FASTA files
3. [ ] Run `run_blastp` on the KPS candidates and review the hits
4. [ ] Write the flavonoid vs diterpenoid pathway JSON with a PMID/DOI on every edge
5. [ ] Apply migrations 0003 and 0004 (`supabase db push --remote`), then seed both genomes with `app.ingestion.seed --apply` and wire the UI to the saved data
6. [ ] Browser walkthrough of the UI with the real files
7. [ ] README demo section, 10 slides, pitch video

## Nice to have
- RAG literature search over `literature_chunks`
- Deploy backend and frontend publicly
- Playwright end-to-end tests

## Later
- AWS migration (see STACK.md)
