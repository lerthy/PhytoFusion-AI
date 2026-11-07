import { describe, expect, it } from "vitest";
import { chromosomeLengths, normalizeGeneId, parseAttributes, parseGff3 } from "./gff3";

const row = (o: Partial<Record<string, string>> = {}) =>
  [
    o.seqid ?? "Chr1",
    "src",
    o.type ?? "gene",
    o.start ?? "1",
    o.end ?? "10",
    ".",
    o.strand ?? "+",
    ".",
    o.attrs ?? "ID=g1",
  ].join("\t");

const SAMPLE = [
  "##gff-version 3",
  "##sequence-region\tChr1\t1\t50000",
  row({ start: "1000", end: "2500", attrs: "ID=gene:SbaiKPS1;Name=KPS1;Note=Kaurene%20synthase-like" }),
  row({ type: "mRNA", attrs: "ID=t1;Parent=gene:SbaiKPS1" }),
  "",
  row({ seqid: "Chr2", start: "5000", end: "7000", strand: "-", attrs: "ID=SbaiCHS1" }),
].join("\n");

describe("gff3", () => {
  it("normalises ids and preserves case", () => {
    expect(normalizeGeneId(" gene:SbaiKPS1 ")).toBe("SbaiKPS1");
    expect(normalizeGeneId("gene-X")).toBe("X");
    expect(() => normalizeGeneId("gene:")).toThrow();
  });

  it("decodes attributes and rejects malformed ones", () => {
    expect(parseAttributes("ID=a;Note=x%20y;;")).toEqual({ ID: "a", Note: "x y" });
    expect(() => parseAttributes("ID=a;oops")).toThrow(/malformed/);
  });

  it("parses genes only, with lengths", () => {
    const parsed = parseGff3(SAMPLE);
    expect(parsed.genes.map((g) => g.geneId)).toEqual(["SbaiKPS1", "SbaiCHS1"]);
    expect(parsed.genes[0]).toMatchObject({ chromosome: "Chr1", start: 1000, end: 2500, name: "KPS1" });
    expect(parsed.genes[0].description).toBe("Kaurene synthase-like");
    expect(parsed.genes[1].strand).toBe("-");
    expect(parsed.lengths).toEqual({ Chr1: 50000 });
  });

  it("falls back to furthest gene end when no directive exists", () => {
    expect(chromosomeLengths(parseGff3(SAMPLE))).toEqual({ Chr1: 50000, Chr2: 7000 });
  });

  it("reports the line number on bad input", () => {
    expect(() => parseGff3([row(), "a\tb"].join("\n"))).toThrow(/line 2/);
  });

  it.each([
    row({ start: "x" }),
    row({ start: "0" }),
    row({ start: "20", end: "10" }),
    row({ strand: "*" }),
    row({ attrs: "Name=nope" }),
  ])("rejects invalid gene row %#", (bad) => {
    expect(() => parseGff3(bad)).toThrow();
  });

  it("rejects a malformed sequence-region", () => {
    expect(() => parseGff3("##sequence-region Chr1 1")).toThrow(/line 1/);
  });

  it("reads friendly sequence names from #OriSeqID comments", () => {
    const text = [
      "##gff-version 3",
      "#OriSeqID=Sbai1\tAccession=GWHAOTO00000001",
      row({ seqid: "GWHAOTO00000001" }),
      "#OriSeqID=Sbai1\tAccession=GWHAOTO00000001",
      "#OriSeqID=utg9\tAccession=GWHAOTO00000020",
    ].join("\n");
    expect(parseGff3(text).aliases).toEqual({ GWHAOTO00000001: "Sbai1", GWHAOTO00000020: "utg9" });
  });

  it("ignores malformed #OriSeqID comments instead of failing", () => {
    expect(parseGff3(["#OriSeqID=onlyname", row()].join("\n")).aliases).toEqual({});
  });
});
