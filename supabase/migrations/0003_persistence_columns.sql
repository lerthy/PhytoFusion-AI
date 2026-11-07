-- Columns the application layer needs on top of the initial schema.

-- Validated Cytoscape elements for a pathway (every edge carries a reference and evidence level;
-- the API enforces this before storing).
alter table pathways add column if not exists graph jsonb;

-- Saved scenario output, so a report can be re-opened exactly as generated.
alter table scenario_results add column if not exists report_markdown text;
alter table scenario_results add column if not exists result jsonb;

-- One row per publication. Multiple NULLs are allowed, so PMID-only or DOI-only rows are fine.
alter table evidence add constraint evidence_pmid_key unique (pmid);
alter table evidence add constraint evidence_doi_key unique (doi);
