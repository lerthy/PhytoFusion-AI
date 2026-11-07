import { describe, expect, it } from "vitest";
import { bpPerDisplayedTurn, geneT, helixPoint, turnsFor } from "./helix";

const shape = { height: 10, turns: 4, radius: 1 };

describe("helixPoint", () => {
  it("runs along the axis from one end to the other, to scale", () => {
    expect(helixPoint(0, 0, shape)[0]).toBeCloseTo(-5);
    expect(helixPoint(0.5, 0, shape)[0]).toBeCloseTo(0);
    expect(helixPoint(1, 0, shape)[0]).toBeCloseTo(5);
  });
  it("keeps every point on the cylinder of the given radius", () => {
    for (const t of [0, 0.13, 0.5, 0.77, 1]) {
      const [, y, z] = helixPoint(t, 0, shape);
      expect(Math.hypot(y, z)).toBeCloseTo(1);
    }
  });
  it("places the second strand on the opposite side at the same position", () => {
    const a = helixPoint(0.3, 0, shape), b = helixPoint(0.3, 1, shape);
    expect(b[0]).toBeCloseTo(a[0]);
    expect(b[1]).toBeCloseTo(-a[1]);
    expect(b[2]).toBeCloseTo(-a[2]);
  });
  it("completes one turn per 1/turns of the axis", () => {
    const start = helixPoint(0, 0, shape), oneTurn = helixPoint(1 / shape.turns, 0, shape);
    expect(oneTurn[1]).toBeCloseTo(start[1]);
    expect(oneTurn[2]).toBeCloseTo(start[2]);
  });
});

describe("turnsFor", () => {
  it.each([[1_000_000, 4], [60_000_000, 12], [30_000_000, 6], [500_000_000, 12]])("%d bp -> %d turns", (bp, turns) => {
    expect(turnsFor(bp)).toBe(turns);
  });
});

describe("geneT", () => {
  it("is the gene midpoint as a fraction of the chromosome", () => {
    expect(geneT({ start: 100, end: 300 }, 1000)).toBeCloseTo(0.2);
  });
  it("clamps genes that run past the end and copes with an unknown length", () => {
    expect(geneT({ start: 900, end: 1500 }, 1000)).toBe(1);
    expect(geneT({ start: 10, end: 20 }, 0)).toBe(0);
  });
});

describe("bpPerDisplayedTurn", () => {
  it("is length divided by turns", () => expect(bpPerDisplayedTurn(40_000_000, 20)).toBe(2_000_000));
});
