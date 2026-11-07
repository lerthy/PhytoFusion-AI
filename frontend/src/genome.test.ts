import { describe, expect, it } from "vitest";
import { defaultSpeciesId, genomeFromApi } from "./genome";
import type { GenomeResponse } from "./types";

const gene = (id: string, chromosome: string | null) => ({
  gene_id: id, chromosome, family: id === "G1" ? "KPS" : null, start_bp: 10, end_bp: 20, strand: "+", annotation: null,
});

describe("genomeFromApi", () => {
  const data: GenomeResponse = {
    species: { id: "s", scientific_name: "X y", role: "host", common_name: null },
    accessions: ["A"],
    chromosomes: [{ name: "Chr1", length_bp: 1000 }, { name: "Chr2", length_bp: null }],
    genes: [gene("G1", "Chr1"), gene("G2", null)],
  };

  it("keeps lengths that exist and maps gene fields", () => {
    const g = genomeFromApi(data);
    expect(g.lengths).toEqual({ Chr1: 1000 });
    expect(g.genes).toEqual([{ geneId: "G1", chromosome: "Chr1", start: 10, end: 20, strand: "+", description: undefined, family: "KPS" }]);
  });

  it("drops genes that are not placed on a chromosome instead of inventing a position", () => {
    expect(genomeFromApi(data).genes.map((x) => x.geneId)).toEqual(["G1"]);
  });
});

describe("defaultSpeciesId", () => {
  const host = { id: "h", role: "host" };
  const donor = { id: "d", role: "donor" };
  it("preselects the species with the slot's own role", () => {
    expect(defaultSpeciesId([host, donor], "host")).toBe("h");
    expect(defaultSpeciesId([host, donor], "donor")).toBe("d");
  });
  it("never falls back to another role: with only a host saved, the donor slot stays empty", () => {
    expect(defaultSpeciesId([host], "donor")).toBe("");
  });
  it("copes with no data", () => {
    expect(defaultSpeciesId(null, "host")).toBe("");
    expect(defaultSpeciesId([], "donor")).toBe("");
  });
});
