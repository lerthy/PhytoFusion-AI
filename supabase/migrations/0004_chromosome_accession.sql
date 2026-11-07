-- Keep the assembly's own sequence identifier (e.g. GWHAOTO00000001) next to the friendlier name
-- from the annotation file (e.g. Sbai1), so nothing is lost when the display name is used.
alter table chromosomes add column if not exists accession text;
