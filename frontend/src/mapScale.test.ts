import { describe, expect, it } from "vitest";
import type { GeneRecord } from "./gff3";
import { axisTicks, formatBp, binCounts, groupByChromosome, mainSequences, nearestGene, niceStep } from "./mapScale";

const gene = (id: string, start: number, end: number, chromosome = "Chr1"): GeneRecord => ({ geneId: id, chromosome, start, end, strand: "+" });

describe("niceStep", () => {
  it.each([[60_000_000, 20_000_000], [48_000_000, 10_000_000], [22_000_000, 5_000_000], [900, 200], [0, 1]])("%d -> %d", (max, step) => {
    expect(niceStep(max)).toBe(step);
  });
  it("always returns a 1, 2 or 5 times a power of ten", () => {
    for (const max of [7, 130, 4_100_000, 98_765_432]) {
      const step = niceStep(max);
      expect([1, 2, 5]).toContain(+(step / 10 ** Math.floor(Math.log10(step))).toFixed(6));
    }
  });
});

describe("formatBp", () => {
  it.each([[0, "0"], [999, "999 bp"], [1500, "1.5 kb"], [25_000_000, "25 Mb"], [1_250_000, "1.25 Mb"]])("%d -> %s", (bp, text) => {
    expect(formatBp(bp)).toBe(text);
  });
});

describe("axisTicks", () => {
  it("starts at zero, stays within the length and is evenly spaced", () => {
    const ticks = axisTicks(62_000_000);
    expect(ticks[0]).toEqual({ bp: 0, label: "0" });
    expect(ticks.at(-1)!.bp).toBeLessThanOrEqual(62_000_000);
    const gaps = new Set(ticks.slice(1).map((t, i) => t.bp - ticks[i].bp));
    expect(gaps.size).toBe(1);
  });
});

describe("nearestGene", () => {
  const genes = [gene("A", 100, 200), gene("B", 1000, 1100), gene("C", 5000, 5200)];
  it("finds the gene under the pointer", () => expect(nearestGene(genes, 1050, 10)?.geneId).toBe("B"));
  it("snaps to the closest gene within range", () => expect(nearestGene(genes, 4980, 50)?.geneId).toBe("C"));
  it("returns nothing when no gene is close enough", () => expect(nearestGene(genes, 3000, 50)).toBeNull());
  it("handles empty and one-gene lists", () => {
    expect(nearestGene([], 5, 100)).toBeNull();
    expect(nearestGene([gene("A", 10, 20)], 15, 0)?.geneId).toBe("A");
  });
});

describe("groupByChromosome", () => {
  it("groups and sorts by start", () => {
    const m = groupByChromosome([gene("B", 50, 60), gene("A", 10, 20), gene("C", 5, 9, "Chr2")]);
    expect(m.get("Chr1")!.map((g) => g.geneId)).toEqual(["A", "B"]);
    expect(m.get("Chr2")!.map((g) => g.geneId)).toEqual(["C"]);
  });
});

describe("mainSequences", () => {
  it("separates chromosome-sized sequences from small scaffolds, keeping order", () => {
    const r = mainSequences({ chr1: 69_000_000, small1: 400_000, chr2: 26_000_000, small2: 300_000 });
    expect(r.main).toEqual(["chr1", "chr2"]);
    expect(r.hidden).toEqual(["small1", "small2"]);
  });
  it("hides nothing when all sequences are comparable", () => {
    expect(mainSequences({ a: 50, b: 40, c: 30 }).hidden).toEqual([]);
  });
  it("always keeps the longest sequence, and copes with empty input", () => {
    expect(mainSequences({ only: 5 }).main).toEqual(["only"]);
    expect(mainSequences({})).toEqual({ main: [], hidden: [] });
  });
});

describe("binCounts", () => {
  const g = (start: number): GeneRecord => ({ geneId: `g${start}`, chromosome: "c", start, end: start + 1, strand: "+" });
  it("buckets genes by start into equal windows", () => {
    expect(binCounts([g(0), g(10), g(55), g(99)], 100, 10)).toEqual([1, 1, 0, 0, 0, 1, 0, 0, 0, 1]);
  });
  it("keeps every gene, even one at or beyond the end", () => {
    const counts = binCounts([g(100), g(250)], 100, 4);
    expect(counts.reduce((a, b) => a + b, 0)).toBe(2);
    expect(counts[3]).toBe(2);
  });
  it("handles an empty or zero-length sequence", () => {
    expect(binCounts([], 100, 3)).toEqual([0, 0, 0]);
    expect(binCounts([g(5)], 0, 3)).toEqual([0, 0, 0]);
  });
});
