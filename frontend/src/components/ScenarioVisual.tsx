import { useEffect, useState } from "react";
import { lookupGene, type GeneLocation } from "../api";
import { geneT } from "../helix";
import { formatBp } from "../mapScale";
import type { AssessInput, SimulateResult } from "../types";
import { Icon } from "./Icon";

type Status = "good" | "partial" | "bad" | "unknown";

/** How well each of the five parts is known, in the same words as the assessment form. */
const MEANING: { key: keyof AssessInput; label: string; states: Record<string, [Status, string]> }[] = [
  { key: "sequence", label: "Sequence match", states: { related: ["good", "related"], weakly_related: ["partial", "weak"], unknown: ["unknown", "unknown"] } },
  { key: "functional", label: "Gene function", states: { characterized: ["good", "tested"], predicted: ["partial", "predicted"] } },
  { key: "pathway", label: "Host pathway", states: { supported: ["good", "supported"], incomplete: ["bad", "incomplete"], unknown: ["unknown", "unknown"] } },
  { key: "expression", label: "Expression", states: { supporting: ["good", "supports"], conflicting: ["bad", "conflicts"], unavailable: ["unknown", "no data"] } },
  { key: "context", label: "Genome context", states: { characterized: ["good", "known"], uncertain: ["unknown", "unclear"] } },
];
const BADGE: Record<Status, { cls: string; icon: "check" | "minus" | "alert" }> = {
  good: { cls: "strong", icon: "check" },
  partial: { cls: "moderate", icon: "minus" },
  bad: { cls: "limited", icon: "alert" },
  unknown: { cls: "neutral", icon: "minus" },
};

const W = 760, BAR_Y = 92, BAR_H = 16, LEFT = 24, RIGHT = 440, BAR_W = 296;

/**
 * The scenario as one picture: the gene on its real chromosome, a dashed arrow that says
 * "hypothetical", and an insertion site that is honestly left open. Below it, how well each part is known.
 */
export function ScenarioVisual({ result }: { result: SimulateResult }) {
  const donor = result.type === "donor_integration";
  const sourceSpecies = donor ? (result.donor_species ?? "") : result.host_species;
  const [where, setWhere] = useState<GeneLocation | null>(null);

  useEffect(() => {
    let live = true;
    setWhere(null);
    lookupGene(sourceSpecies, result.target_gene_id).then((w) => live && setWhere(w), () => live && setWhere(null));
    return () => { live = false; };
  }, [sourceSpecies, result.target_gene_id]);

  const t = where?.chromosome_length ? geneT({ start: where.start_bp, end: where.end_bp }, where.chromosome_length) : null;
  const markerX = t === null ? LEFT + BAR_W / 2 : LEFT + t * BAR_W;
  const place = where?.chromosome ? `${where.chromosome} · ${formatBp(where.start_bp)}` : "position not available";
  const a = result.assessment;

  return (
    <section className="visual" aria-label="Scenario at a glance">
      <svg viewBox={`0 0 ${W} 190`} role="img" aria-label={`${result.target_gene_id} would move from ${sourceSpecies}${donor ? ` into ${result.host_species}` : ""}. This is hypothetical. The insertion site is not chosen.`}>
        <text className="fig-role" x={LEFT} y="26">{donor ? "DONOR" : "HOST"}</text>
        <text className="fig-label" x={LEFT} y="48"><tspan fontStyle="italic">{sourceSpecies}</tspan></text>

        <rect className="fig-bar" x={LEFT} y={BAR_Y} width={BAR_W} height={BAR_H} rx={8} />
        <rect className="fig-gene" x={markerX - 3} y={BAR_Y - 14} width={6} height={BAR_H + 28} rx={3} />
        <text className="fig-gene-label" x={Math.min(Math.max(markerX, LEFT + 70), LEFT + BAR_W - 70)} y={BAR_Y - 22} textAnchor="middle">{result.target_gene_id}</text>
        <text className="fig-label" x={LEFT} y={BAR_Y + 50}>{place}</text>

        {donor ? (
          <>
            <path className="fig-arrow dashed" d={`M${LEFT + BAR_W + 22} ${BAR_Y + 8}H${RIGHT - 22}`} />
            <path className="fig-arrow" d={`M${RIGHT - 30} ${BAR_Y + 1}L${RIGHT - 21} ${BAR_Y + 8}L${RIGHT - 30} ${BAR_Y + 15}`} />
            <text className="fig-label" x={(LEFT + BAR_W + RIGHT) / 2} y={BAR_Y - 6} textAnchor="middle">hypothetical</text>
            <text className="fig-label" x={(LEFT + BAR_W + RIGHT) / 2} y={BAR_Y + 30} textAnchor="middle">not performed</text>

            <text className="fig-role" x={RIGHT + BAR_W} y="26" textAnchor="end">HOST</text>
            <text className="fig-label" x={RIGHT + BAR_W} y="48" textAnchor="end"><tspan fontStyle="italic">{result.host_species}</tspan></text>
            <rect className="fig-bar" x={RIGHT} y={BAR_Y} width={BAR_W} height={BAR_H} rx={8} />
            <rect className="fig-slot" x={RIGHT + BAR_W / 2 - 14} y={BAR_Y - 12} width={28} height={BAR_H + 24} rx={5} />
            <text className="fig-gene-label" x={RIGHT + BAR_W / 2} y={BAR_Y + 12} textAnchor="middle">?</text>
            <text className="fig-label" x={RIGHT} y={BAR_Y + 50}>insertion site: not chosen</text>
          </>
        ) : (
          <text className="fig-label" x={RIGHT} y={BAR_Y + 12}>hypothetical edit of this gene in place</text>
        )}
      </svg>

      {a && (
        <>
          <h3 className="visual-title">How well is each part known?</h3>
          <ul className="meter">
            {MEANING.map(({ key, label, states }) => {
              const [status, word] = states[a[key]] ?? ["unknown", String(a[key])];
              const b = BADGE[status];
              return (
                <li key={key}>
                  <span className="meter-label">{label}</span>
                  <span className={`badge ${b.cls}`}><Icon name={b.icon} size={14} />{word}</span>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </section>
  );
}
