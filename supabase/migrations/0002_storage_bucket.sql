-- Private bucket for genome assemblies, annotations and protein files.
-- Private: no public read policy is created, so only the service-role key (backend) can access it.
insert into storage.buckets (id, name, public)
values ('genomes', 'genomes', false)
on conflict (id) do nothing;
