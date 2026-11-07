import type { GeneRecord, ParsedGenome } from "./gff3";
import type { GenomeResponse } from "./types";

/** Convert the API's genome payload into the shape the explorer already renders. */
export function genomeFromApi(data: GenomeResponse): ParsedGenome {
  const lengths: Record<string, number> = {};
  for (const c of data.chromosomes) if (c.length_bp) lengths[c.name] = c.length_bp;
  const genes: GeneRecord[] = data.genes
    .filter((g) => g.chromosome)
    .map((g) => ({
      geneId: g.gene_id,
      chromosome: g.chromosome as string,
      start: g.start_bp,
      end: g.end_bp,
      strand: g.strand,
      description: g.annotation ?? undefined,
      family: g.family ?? undefined,
    }));
  return { genes, lengths };
}

/** Which saved species a slot should preselect: only one with the slot's own role, never a fallback.
 *  Falling back to "the first species" made the donor slot show the host plant. */
export function defaultSpeciesId(species: { id: string; role: string }[] | null, role: "host" | "donor"): string {
  return species?.find((s) => s.role === role)?.id ?? "";
}
