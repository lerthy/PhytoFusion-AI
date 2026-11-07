import type { GeneRecord } from "./gff3";

/** A clean step (1, 2, 5 x 10^n) that gives roughly `target` ticks across `max`. */
export function niceStep(max: number, target = 5): number {
  if (!(max > 0)) return 1;
  const raw = max / target;
  const pow = 10 ** Math.floor(Math.log10(raw));
  const f = raw / pow;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * pow;
}

/** 25_000_000 -> "25 Mb", 500_000 -> "500 kb", 0 -> "0". */
export function formatBp(bp: number): string {
  if (bp === 0) return "0";
  if (bp >= 1_000_000) return `${+(bp / 1_000_000).toFixed(2)} Mb`;
  if (bp >= 1_000) return `${+(bp / 1_000).toFixed(1)} kb`;
  return `${bp} bp`;
}

export interface AxisTick { bp: number; label: string }

export function axisTicks(maxBp: number, target = 5): AxisTick[] {
  const step = niceStep(maxBp, target);
  const ticks: AxisTick[] = [];
  for (let bp = 0; bp <= maxBp; bp += step) ticks.push({ bp, label: formatBp(bp) });
  return ticks;
}

/** Nearest gene (by start) within `maxDistance` bp of `bp`. `genes` must be sorted by start. */
export function nearestGene(genes: GeneRecord[], bp: number, maxDistance: number): GeneRecord | null {
  let lo = 0, hi = genes.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (genes[mid].start < bp) lo = mid + 1; else hi = mid;
  }
  let best: GeneRecord | null = null, bestDist = Infinity;
  for (const i of [lo - 1, lo, lo + 1]) {
    const g = genes[i];
    if (!g) continue;
    const dist = bp >= g.start && bp <= g.end ? 0 : Math.min(Math.abs(g.start - bp), Math.abs(g.end - bp));
    if (dist < bestDist) { best = g; bestDist = dist; }
  }
  return bestDist <= maxDistance ? best : null;
}

/** Group by chromosome, each list sorted by start, ready for nearestGene. */
export function groupByChromosome(genes: GeneRecord[]): Map<string, GeneRecord[]> {
  const map = new Map<string, GeneRecord[]>();
  for (const g of genes) (map.get(g.chromosome) ?? map.set(g.chromosome, []).get(g.chromosome)!).push(g);
  for (const list of map.values()) list.sort((a, b) => a.start - b.start);
  return map;
}

/**
 * Separate chromosome-sized sequences from small unplaced scaffolds. A sequence is "main" when it is
 * at least `fraction` of the longest one. At least one is always kept, and input order is preserved.
 */
export function mainSequences(lengths: Record<string, number>, fraction = 0.1): { main: string[]; hidden: string[] } {
  const entries = Object.entries(lengths);
  const longest = Math.max(0, ...entries.map(([, v]) => v));
  const main: string[] = [], hidden: string[] = [];
  for (const [name, length] of entries) (length >= longest * fraction ? main : hidden).push(name);
  return { main, hidden };
}

/** Genes per window along a sequence: `bins` equal windows across `maxBp` (genes bucketed by start). */
export function binCounts(genes: GeneRecord[], maxBp: number, bins: number): number[] {
  const counts = new Array<number>(bins).fill(0);
  if (!(maxBp > 0)) return counts;
  for (const g of genes) counts[Math.min(bins - 1, Math.max(0, Math.floor((g.start / maxBp) * bins)))]++;
  return counts;
}

/** Above this many genes on one sequence, individual marks merge into solid bars: show density instead. */
export const DENSE_GENES_PER_SEQUENCE = 150;
