import { useMemo, useRef, useState } from "react";
import type { GeneRecord } from "../gff3";
import { axisTicks, binCounts, DENSE_GENES_PER_SEQUENCE, formatBp, groupByChromosome, mainSequences, nearestGene } from "../mapScale";

interface Props {
  lengths: Record<string, number>;
  genes: GeneRecord[];
  /** Genes that match the current search, drawn in the second colour. */
  hits: Set<string>;
  /** Gene highlighted from the table below (hover or keyboard focus). */
  activeId: string | null;
  label: string;
  /** Optional friendlier sequence names (id -> name). */
  names?: Record<string, string>;
}

const W = 1000; // drawing width; x is scaled to the track, strokes stay a constant pixel width
const HIT_PX = 8;
const BINS = 240; // windows across the track in density view
const TIP_HALF = 125; // half the tooltip's max width, so it never hangs outside the card

/**
 * Chromosome map. One thin mark per gene on a to-scale track, a Mb axis, and a hover readout.
 * The table next to it carries every value, so nothing depends on the pointer.
 */
export function ChromosomeMap({ lengths, genes, hits, activeId, label, names = {} }: Props) {
  const wrap = useRef<HTMLDivElement>(null);
  const [tip, setTip] = useState<{ gene: GeneRecord; x: number; y: number } | null>(null);
  const [showAll, setShowAll] = useState(false);
  const { main, hidden } = useMemo(() => mainSequences(lengths), [lengths]);
  const visible = showAll ? Object.keys(lengths) : main;
  const nameOf = (id: string) => names[id] ?? id;

  const maxLength = Math.max(1, ...Object.values(lengths));
  const byChr = useMemo(() => groupByChromosome(genes), [genes]);
  const ticks = useMemo(() => axisTicks(maxLength), [maxLength]);
  const x = (bp: number) => (bp / maxLength) * W;
  const path = (list: GeneRecord[], h = 22, y0 = 1) => list.map((g) => `M${x(g.start).toFixed(1)} ${y0}v${h}`).join("");
  const activeGene = activeId ? genes.find((g) => g.geneId === activeId) : null;

  const onMove = (chr: string, e: React.PointerEvent<HTMLDivElement>) => {
    const box = e.currentTarget.getBoundingClientRect();
    const bp = ((e.clientX - box.left) / box.width) * maxLength;
    const slack = (HIT_PX / box.width) * maxLength;
    const gene = nearestGene(byChr.get(chr) ?? [], bp, slack);
    const parent = wrap.current!.getBoundingClientRect();
    setTip(gene ? { gene, x: Math.min(Math.max(e.clientX - parent.left, TIP_HALF), Math.max(TIP_HALF, parent.width - TIP_HALF)), y: box.top - parent.top } : null);
  };

  // Many genes per sequence: draw gene density (one hue, light to dark) instead of one mark per gene.
  const dense = useMemo(() => Math.max(0, ...visible.map((c) => byChr.get(c)?.length ?? 0)) > DENSE_GENES_PER_SEQUENCE, [visible, byChr]);
  const density = useMemo(() => {
    if (!dense) return null;
    const perChr = new Map(visible.map((c) => [c, binCounts(byChr.get(c) ?? [], maxLength, BINS)]));
    const top = Math.max(1, ...[...perChr.values()].flat());
    return { perChr, top };
  }, [dense, visible, byChr, maxLength]);
  const anyHits = hits.size > 0;
  return (
    <div className="map" ref={wrap} role="group" aria-label={`${label} chromosome map. The table below lists the same genes.`}>
      <div className="map-axis" aria-hidden="true">
        <span />
        <div className="map-scale">
          {ticks.map((t, i) => (
            <span key={t.bp} className={i === ticks.length - 1 && t.bp / maxLength > 0.96 ? "last" : ""} style={{ left: `${(t.bp / maxLength) * 100}%` }}>{t.label}</span>
          ))}
          {ticks.map((t) => <i key={`i${t.bp}`} style={{ left: `${(t.bp / maxLength) * 100}%` }} />)}
        </div>
      </div>
      {visible.map((chr) => {
        const length = lengths[chr];
        const list = byChr.get(chr) ?? [];
        return (
          <div key={chr} className="map-row">
            <span className="map-name" title={nameOf(chr) === chr ? chr : `${nameOf(chr)} (${chr})`}>{nameOf(chr)}</span>
            <div className="map-track" onPointerMove={(e) => onMove(chr, e)} onPointerLeave={() => setTip(null)}>
              <div className="bar" style={{ width: `${(length / maxLength) * 100}%` }} />
              <svg viewBox={`0 0 ${W} 24`} preserveAspectRatio="none" aria-hidden="true">
                {density ? (
                  <g aria-hidden="true">
                    {density.perChr.get(chr)!.map((n, i) => n > 0 && (
                      <rect key={i} className="dens" x={(i * W) / BINS} y={5} width={W / BINS + 0.6} height={14} style={{ opacity: 0.18 + 0.82 * (n / density.top) }} />
                    ))}
                  </g>
                ) : (
                  <path className="tick" d={path(list.filter((g) => !hits.has(g.geneId)), 14, 5)} />
                )}
                <path className="hit" d={path(list.filter((g) => hits.has(g.geneId)))} />
                {activeGene?.chromosome === chr && <path className="active" d={path([activeGene], 24, 0)} />}
              </svg>
            </div>
          </div>
        );
      })}
      {tip && (
        <div className="map-tip" style={{ left: tip.x, top: tip.y - 6 }}>
          <strong>{tip.gene.geneId}</strong>
          <span>{nameOf(tip.gene.chromosome)}: {tip.gene.start.toLocaleString()}–{tip.gene.end.toLocaleString()}</span>
          {(tip.gene.family || tip.gene.description) && <span> · {[tip.gene.family, tip.gene.description].filter(Boolean).join(" · ")}</span>}
        </div>
      )}
      <div className="map-legend" aria-hidden="true">
        {density ? (
          <span><i className="ramp" />Gene density, few to many per {formatBp(maxLength / BINS)} window ({density.top} at most)</span>
        ) : (
          <span><i style={{ background: "var(--viz-1)" }} />Gene</span>
        )}
        {anyHits && <span><i style={{ background: "var(--viz-2)" }} />Matches your search</span>}
        <span>Bars show length to scale</span>
      </div>
      {hidden.length > 0 && (
        <p className="map-more">
          {showAll ? `Showing all ${Object.keys(lengths).length} sequences.` : `Showing the ${main.length} largest sequences. ${hidden.length} small unplaced scaffolds are hidden.`}{" "}
          <button type="button" className="linkish" onClick={() => setShowAll(!showAll)}>{showAll ? "Show only the largest" : "Show all"}</button>
        </p>
      )}
      {/* the active gene is also announced for screen readers when chosen from the table */}
      <span className="sr-only" aria-live="polite">{activeGene ? `${activeGene.geneId}, ${activeGene.chromosome}` : ""}</span>
      <span className="sr-only">{`${genes.length} genes on ${Object.keys(lengths).length} chromosomes`}</span>
    </div>
  );
}
