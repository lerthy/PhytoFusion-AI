import { describe, expect, it } from "vitest";
import { validateElements } from "./pathway";

const node = (id: string) => ({ data: { id, kind: "compound", label: id } });
const edge = (extra: Record<string, unknown> = {}) => ({
  data: { source: "a", target: "b", relation: "r", reference: "PMID:1", evidence_level: "strong", ...extra },
});

describe("validateElements", () => {
  it("accepts nodes and fully referenced edges", () => {
    expect(validateElements([node("a"), node("b"), edge()])).toHaveLength(3);
  });

  it("rejects non-arrays", () => {
    expect(() => validateElements({})).toThrow(/array/);
  });

  it.each([{ reference: "" }, { reference: "   " }, { reference: undefined }])(
    "rejects an edge without a reference (%j)",
    (extra) => {
      expect(() => validateElements([edge(extra)])).toThrow(/reference/);
    },
  );

  it("rejects an invalid evidence level", () => {
    expect(() => validateElements([edge({ evidence_level: "certain" })])).toThrow(/evidence_level/);
  });

  it("rejects a node without an id and an element without data", () => {
    expect(() => validateElements([{ data: {} }])).toThrow(/missing id/);
    expect(() => validateElements([{}])).toThrow(/missing data/);
  });
});
