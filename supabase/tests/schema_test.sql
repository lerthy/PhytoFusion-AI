-- Schema tests. Run after applying migrations:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f supabase/tests/schema_test.sql
-- Everything runs in one transaction that is rolled back, so it leaves no data behind.

begin;

create or replace function pg_temp.expect_error(stmt text, label text) returns void
language plpgsql as $$
begin
  begin
    execute stmt;
  exception when others then
    raise notice 'ok: % (rejected: %)', label, sqlerrm;
    return;
  end;
  raise exception 'FAIL: % was accepted but should have been rejected', label;
end $$;

-- 1. All expected tables exist
do $$
declare t text;
begin
  foreach t in array array[
    'species','genome_assemblies','chromosomes','genes','compounds','pathways',
    'pathway_edges','evidence','literature_chunks','gene_comparisons',
    'finding_evidence','crispr_scenarios','scenario_results']
  loop
    if to_regclass('public.' || t) is null then
      raise exception 'FAIL: table % is missing', t;
    end if;
    if not (select relrowsecurity from pg_class where oid = ('public.' || t)::regclass) then
      raise exception 'FAIL: row level security is not enabled on %', t;
    end if;
  end loop;
  raise notice 'ok: all tables exist with RLS enabled';
end $$;

-- 2. Traceability: evidence needs a PMID or DOI
select pg_temp.expect_error(
  $q$insert into evidence (finding, level) values ('no source', 'strong')$q$,
  'evidence without PMID/DOI');
insert into evidence (pmid, finding, level) values ('PMID:1', 'has a source', 'moderate');

-- 3. Enum values are enforced
select pg_temp.expect_error(
  $q$insert into evidence (pmid, finding, level) values ('PMID:2', 'x', 'certain')$q$,
  'invalid evidence level');

-- 4. Gene comparisons use categorical values only
do $$
declare s uuid; a uuid; g1 uuid; g2 uuid;
begin
  insert into species (scientific_name, role) values ('Scutellaria baicalensis', 'host') returning id into s;
  insert into genome_assemblies (species_id, accession, source) values (s, 'TEST-1', 'test') returning id into a;
  insert into genes (assembly_id, gene_id, family) values (a, 'SbaiKPS1', 'KPS') returning id into g1;
  insert into genes (assembly_id, gene_id, family) values (a, 'SbarKPS1', 'KPS') returning id into g2;

  perform pg_temp.expect_error(
    format($q$insert into gene_comparisons (host_gene_id, donor_gene_id, sequence_relationship, overall_level)
              values (%L, %L, '95_percent', 'strong')$q$, g1, g2),
    'free-form compatibility value');

  insert into gene_comparisons (host_gene_id, donor_gene_id, sequence_relationship, overall_level)
  values (g1, g2, 'related', 'moderate');

  perform pg_temp.expect_error(
    format($q$insert into gene_comparisons (host_gene_id, donor_gene_id, overall_level)
              values (%L, %L, 'limited')$q$, g1, g2),
    'duplicate host/donor comparison');

  perform pg_temp.expect_error(
    format($q$insert into genes (assembly_id, gene_id) values (%L, 'SbaiKPS1')$q$, a),
    'duplicate gene id within an assembly');
end $$;

-- 5. Vector search returns the nearest chunk first
do $$
declare ev uuid; top record; vec_a text; vec_b text;
begin
  select id into ev from evidence limit 1;
  vec_a := '[1' || repeat(',0', 1535) || ']';
  vec_b := '[0,1' || repeat(',0', 1534) || ']';
  insert into literature_chunks (evidence_id, content, embedding) values
    (ev, 'chunk A', vec_a::vector), (ev, 'chunk B', vec_b::vector);

  select * into top from match_literature(vec_b::vector, 1);
  if top.content <> 'chunk B' then
    raise exception 'FAIL: nearest chunk should be B, got %', top.content;
  end if;
  raise notice 'ok: vector search returns nearest chunk';
end $$;

-- 6. Deleting a species cascades to its assemblies
do $$
declare s uuid;
begin
  select id into s from species where scientific_name = 'Scutellaria baicalensis';
  delete from species where id = s;
  if exists (select 1 from genome_assemblies where accession = 'TEST-1') then
    raise exception 'FAIL: assembly survived species deletion';
  end if;
  raise notice 'ok: cascade delete works';
end $$;

-- 7. Migration 0003: application columns and one row per publication
do $$
declare ev uuid; pw uuid;
begin
  insert into pathways (name, graph) values ('P', '[{"data":{"id":"a"}}]'::jsonb) returning id into pw;
  if (select graph from pathways where id = pw) is null then
    raise exception 'FAIL: pathways.graph was not stored';
  end if;

  insert into evidence (pmid, finding, level) values ('PMID:UNIQ', 'first', 'strong') returning id into ev;
  perform pg_temp.expect_error(
    $q$insert into evidence (pmid, finding, level) values ('PMID:UNIQ', 'second', 'strong')$q$,
    'duplicate PMID');
  -- Several DOI-less rows are fine (NULLs do not collide)
  insert into evidence (pmid, finding, level) values ('PMID:A', 'x', 'limited'), ('PMID:B', 'y', 'limited');

  perform 1 from information_schema.columns
   where table_name = 'scenario_results' and column_name in ('report_markdown', 'result')
   having count(*) = 2;
  if not found then
    raise exception 'FAIL: scenario_results is missing report_markdown/result';
  end if;
  raise notice 'ok: migration 0003 columns and unique publications';
end $$;

-- 8. Migration 0004: chromosomes keep the assembly's own sequence identifier
do $$
declare sp uuid; a uuid;
begin
  insert into species (scientific_name, role) values ('Accession test', 'host') returning id into sp;
  insert into genome_assemblies (species_id, accession, source) values (sp, 'TEST-ACC', 't') returning id into a;
  insert into chromosomes (assembly_id, name, accession, length_bp) values (a, 'Sbai1', 'GWHAOTO00000001', 100);
  if (select accession from chromosomes where assembly_id = a and name = 'Sbai1') <> 'GWHAOTO00000001' then
    raise exception 'FAIL: chromosomes.accession was not stored';
  end if;
  raise notice 'ok: migration 0004 chromosome accession';
end $$;

rollback;
