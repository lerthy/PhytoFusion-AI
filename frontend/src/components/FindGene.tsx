import { useState } from "react";
import { findGenes } from "../api";
import type { GeneFindResult } from "../types";
import { ErrorNote } from "./ErrorNote";
import { Button, Field, More, TableWrap } from "./ui";

const KIND_WORDS = { same_protein: "Same protein", related: "Related", weakly_related: "Weakly related" } as const;
const EXAMPLE = "WJZ49120.1";

/**
 * "I do not know the gene ID": search a plant's proteins with a protein sequence or an NCBI accession.
 * The answer is computed by BLAST+ on the server. No AI is involved and nothing is guessed.
 */
export function FindGene({ speciesId, speciesName, onUse }: { speciesId: string; speciesName: string; onUse: (geneId: string) => void }) {
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<GeneFindResult | null>(null);
  const [used, setUsed] = useState<string[]>([]);

  const search = async () => {
    setBusy(true);
    setError(null);
    try {
      setResult(await findGenes(speciesId, query));
    } catch (e) {
      setError(e as Error);
      setResult(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <More summary="Don’t know the gene ID? Find it from a protein sequence">
      <p className="muted" style={{ marginTop: 0 }}>
        Paste a protein sequence or an NCBI protein accession. We search {speciesName ? <em>{speciesName}</em> : "the donor plant"}’s proteins with BLAST and list the closest genes.
        This is a computed search, not an AI guess.
      </p>
      <Field label="Protein sequence or NCBI accession" hint="For example WJZ49120.1, the SbarKPS2 protein from the 2023 paper (PMID 37395679).">
        {(a) => <textarea {...a} rows={3} value={query} onChange={(e) => setQuery(e.target.value)} placeholder="WJZ49120.1, or paste a sequence" />}
      </Field>
      <div className="row">
        <Button type="button" onClick={search} busy={busy} disabled={!speciesId || !query.trim()}>Find genes</Button>
        <Button type="button" variant="secondary" onClick={() => setQuery(EXAMPLE)}>Try the paper’s SbarKPS2 protein</Button>
        {!speciesId && <span className="muted">Choose the donor plant above first.</span>}
        {busy && <span className="muted" role="status">Searching. The first search can take about 20 seconds; later ones take a few.</span>}
      </div>
      <div style={{ marginTop: 12 }}><ErrorNote error={error} /></div>
      {result && (
        <div aria-live="polite">
          <p style={{ margin: "12px 0 8px" }}>
            Searched <strong>{result.query.name}</strong> ({result.query.length} amino acids). Closest genes:
          </p>
          {result.hits.length === 0 ? <p className="muted">No gene matched well enough.</p> : (
            <TableWrap label="Genes that match the sequence">
              <table>
                <thead><tr><th>Gene</th><th className="num">Identity</th><th className="num">Aligned</th><th>Where</th><th>Result</th><th><span className="sr-only">Action</span></th></tr></thead>
                <tbody>
                  {result.hits.map((h) => (
                    <tr key={h.gene_id}>
                      <td className="mono">{h.gene_id}</td>
                      <td className="num">
                        <span className="simbar-cell">
                          <span className={`simbar ${h.kind === "same_protein" ? "mutual" : ""}`} aria-hidden="true"><i style={{ width: `${Math.max(2, Math.min(100, h.percent_identity))}%` }} /></span>
                          {h.percent_identity.toFixed(1)}%
                        </span>
                      </td>
                      <td className="num">{h.aligned_aa} aa</td>
                      <td>{h.location ? `${h.location.chromosome ?? "?"}: ${h.location.start_bp.toLocaleString()}–${h.location.end_bp.toLocaleString()}` : "–"}</td>
                      <td>{KIND_WORDS[h.kind]}</td>
                      <td>
                        <Button type="button" variant="secondary" small onClick={() => { onUse(h.gene_id); setUsed((u) => [...u, h.gene_id]); }} disabled={used.includes(h.gene_id)}>
                          {used.includes(h.gene_id) ? "Added" : "Use this gene"}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableWrap>
          )}
          <p className="muted" style={{ marginTop: 8 }}>
            Found by {result.computed_by}, not by AI. Identity says how alike two proteins are; only “Same protein” means the gene is the one that was searched.
            It does not say the gene would work in another plant.
          </p>
        </div>
      )}
    </More>
  );
}
