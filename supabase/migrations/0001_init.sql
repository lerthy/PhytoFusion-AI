-- PhytoFusion AI: initial schema (Supabase / Postgres)
-- Design rule: every scientific finding must be traceable to an evidence row.

create extension if not exists vector;

create type evidence_level as enum ('strong', 'moderate', 'limited');
create type gene_role as enum ('host', 'donor');
create type scenario_type as enum ('host_modification', 'donor_integration');

create table species (
  id uuid primary key default gen_random_uuid(),
  scientific_name text not null unique,
  common_name text,
  role gene_role not null,
  notes text
);

create table genome_assemblies (
  id uuid primary key default gen_random_uuid(),
  species_id uuid not null references species(id) on delete cascade,
  accession text not null unique,          -- e.g. GWHAOTO00000000
  source text not null,                    -- Genome Warehouse, NCBI, CoGe
  chromosome_count int,
  storage_path text,                       -- path in Supabase Storage bucket "genomes"
  source_url text
);

create table chromosomes (
  id uuid primary key default gen_random_uuid(),
  assembly_id uuid not null references genome_assemblies(id) on delete cascade,
  name text not null,
  length_bp bigint,
  unique (assembly_id, name)
);

create table genes (
  id uuid primary key default gen_random_uuid(),
  assembly_id uuid not null references genome_assemblies(id) on delete cascade,
  chromosome_id uuid references chromosomes(id) on delete set null,
  gene_id text not null,                   -- normalized ID, e.g. SbaiKPS1
  family text,                             -- PAL, CHS, 4CL, CHI, CYP82D, KPS
  category text check (category in ('biosynthetic', 'regulatory', 'enzyme')),
  start_bp bigint,
  end_bp bigint,
  strand char(1),
  annotation text,
  protein_sequence text,
  unique (assembly_id, gene_id)
);
create index on genes (family);

create table compounds (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  pubchem_cid bigint,
  smiles text,
  class text                               -- flavonoid, clerodane diterpenoid...
);

create table pathways (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  description text
);

-- Gene -> enzyme -> reaction -> compound edges of the pathway graph
create table pathway_edges (
  id uuid primary key default gen_random_uuid(),
  pathway_id uuid not null references pathways(id) on delete cascade,
  gene_id uuid references genes(id) on delete set null,
  compound_in uuid references compounds(id) on delete set null,
  compound_out uuid references compounds(id) on delete set null,
  reaction text,
  evidence_level evidence_level not null
);

create table evidence (
  id uuid primary key default gen_random_uuid(),
  pmid text,
  doi text,
  title text,
  finding text not null,
  level evidence_level not null,
  check (pmid is not null or doi is not null)
);

-- Literature chunks for RAG. Dimension 1536: change to match your embedding model.
create table literature_chunks (
  id uuid primary key default gen_random_uuid(),
  evidence_id uuid not null references evidence(id) on delete cascade,
  content text not null,
  embedding vector(1536)
);
create index on literature_chunks using hnsw (embedding vector_cosine_ops);

create table gene_comparisons (
  id uuid primary key default gen_random_uuid(),
  host_gene_id uuid not null references genes(id) on delete cascade,
  donor_gene_id uuid not null references genes(id) on delete cascade,
  sequence_relationship text check (sequence_relationship in ('related', 'weakly_related', 'unknown')),
  percent_identity numeric,                -- from BLAST, a measured value
  functional_evidence text check (functional_evidence in ('characterized', 'predicted')),
  pathway_completeness text check (pathway_completeness in ('supported', 'incomplete', 'unknown')),
  expression_compatibility text check (expression_compatibility in ('supporting', 'conflicting', 'unavailable')),
  genomic_context text check (genomic_context in ('characterized', 'uncertain')),
  overall_level evidence_level not null,
  explanation text,
  unique (host_gene_id, donor_gene_id)
);

-- Links any finding to its sources
create table finding_evidence (
  evidence_id uuid not null references evidence(id) on delete cascade,
  gene_id uuid references genes(id) on delete cascade,
  comparison_id uuid references gene_comparisons(id) on delete cascade,
  pathway_edge_id uuid references pathway_edges(id) on delete cascade
);

create table crispr_scenarios (
  id uuid primary key default gen_random_uuid(),
  type scenario_type not null,
  host_species_id uuid not null references species(id) on delete cascade,
  donor_species_id uuid references species(id) on delete set null,
  target_gene_id uuid not null references genes(id) on delete cascade,
  description text,
  created_at timestamptz not null default now()
);

create table scenario_results (
  id uuid primary key default gen_random_uuid(),
  scenario_id uuid not null references crispr_scenarios(id) on delete cascade,
  predicted_consequences text,             -- qualitative only
  compatibility_issues text,
  missing_pathway_components text,
  limitations text not null,
  evidence_level evidence_level not null,
  created_at timestamptz not null default now()
);

-- Public scientific reference data: readable by anyone, writable only by the
-- service role (the FastAPI backend / ingestion scripts).
do $$
declare t text;
begin
  foreach t in array array[
    'species','genome_assemblies','chromosomes','genes','compounds','pathways',
    'pathway_edges','evidence','literature_chunks','gene_comparisons',
    'finding_evidence','crispr_scenarios','scenario_results']
  loop
    execute format('alter table %I enable row level security', t);
    execute format('create policy "public read" on %I for select using (true)', t);
  end loop;
end $$;

-- Vector search helper used by the RAG engine
create or replace function match_literature(query_embedding vector(1536), match_count int default 5)
returns table (id uuid, evidence_id uuid, content text, similarity float)
language sql stable as $$
  select id, evidence_id, content, 1 - (embedding <=> query_embedding) as similarity
  from literature_chunks
  order by embedding <=> query_embedding
  limit match_count;
$$;
