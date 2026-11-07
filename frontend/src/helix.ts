import type { GeneRecord } from "./gff3";

export interface HelixShape {
  /** Length of the axis in scene units. */
  height: number;
  /** Number of full turns over the whole chromosome. */
  turns: number;
  radius: number;
}

export type Vec3 = [number, number, number];

/**
 * Point on one strand of the helix at position t (0 to 1 along the chromosome).
 * The axis is x; strand 1 sits half a turn behind strand 0.
 * Position along the axis is real (linear in base pairs). The twist is decorative.
 */
export function helixPoint(t: number, strand: 0 | 1, shape: HelixShape): Vec3 {
  const angle = t * shape.turns * 2 * Math.PI + (strand === 1 ? Math.PI : 0);
  return [(t - 0.5) * shape.height, Math.cos(angle) * shape.radius, Math.sin(angle) * shape.radius];
}

/** Keep the twist readable: roughly `bpPerTurn` per turn, but never fewer than 4 or more than 12 turns. */
export function turnsFor(lengthBp: number, bpPerTurn = 5_000_000): number {
  return Math.min(12, Math.max(4, Math.round(lengthBp / bpPerTurn)));
}

/** Position of a gene along its chromosome as a fraction 0..1 (by its midpoint). */
export function geneT(gene: Pick<GeneRecord, "start" | "end">, lengthBp: number): number {
  if (!(lengthBp > 0)) return 0;
  return Math.min(1, Math.max(0, (gene.start + gene.end) / 2 / lengthBp));
}

/** Base pairs represented by one decorative turn, for the caption. */
export function bpPerDisplayedTurn(lengthBp: number, turns: number): number {
  return lengthBp / turns;
}
