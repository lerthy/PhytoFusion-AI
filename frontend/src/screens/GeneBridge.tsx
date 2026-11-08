import { useState } from "react";
import { assess, classify, compareCandidates, listComparisons, listSpecies } from "../api";
import { AssessmentFields } from "../components/AssessmentFields";
import { ApiError } from "../api";
import { ErrorNote } from "../components/ErrorNote";
import { EvidenceBadge } from "../components/EvidenceBadge";
import { ExplainButton } from "../components/ExplainButton";
import { Button, Card, EmptyState, Field, More, PageHead, Skeleton, TableWrap } from "../components/ui";
import { useAsync } from "../hooks";
import { DEFAULT_ASSESS, type AssessInput, type AssessResult, type PipelineRow } from "../types";

const MATCH_WORDS: Record<string, string> = { related: "Related", weakly_related: "Weakly related", unknown: "No clear match" };

function Screening({ onSaved }: { onSaved: () => void }) {
  const species = useAsync(listSpecies);
  const [hostId, setHostId] = useState("");
  const [donorId, setDonorId] = useState("");
  const [genes, setGenes] = useState("");
  const [persist, setPersist] = useState(false);
  const [rows, setRows] = useState<PipelineRow[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [tried, setTried] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const ids = genes.split(/[,\s]+/).filter(Boolean);
  const same = !!hostId && hostId === donorId;
  const invalid = !hostId || !donorId || same || ids.length === 0;

  const run = async (e: React.FormEvent) => {
    e.preventDefault();
    setTried(true);
    if (invalid) return;
    setBusy(true);
    setError(null);
    try {
      setRows(await compareCandidates({ host_species_id: hostId, donor_species_id: donorId, candidate_gene_ids: ids, persist }));
      if (persist) onSaved();
    } catch (err) {
      setError(err as Error);
      setRows(null);
    } finally {
      setBusy(false);
    }
  };

  const pick = (value: string, set: (v: string) => void) => (a: object) => (
    <select {...a} value={value} onChange={(e) => set(e.target.value)}>
      <option value="">Choose…</option>
      {species.data?.map((s) => <option key={s.id} value={s.id}>{s.scientific_name}</option>)}
    </select>
  );

  const unavailable = (species.error instanceof ApiError && species.error.notConfigured) || (species.data && species.data.length === 0);
  if (unavailable) {
    return (
      <Card title="Find the closest match in the host plant" icon="compare">
        <EmptyState icon="database" title="No genomes saved yet">
          Comparing genes uses the two genomes stored in the database. Load them with the seed script, then come back here.
          You can still rate a gene pair by hand below.
        </EmptyState>
      </Card>
    );
  }

  return (
    <Card title="Find the closest match in the host plant" icon="compare" sub="Enter one or more donor genes. We look for the most similar gene in the host plant.">
      <ErrorNote error={species.error} quiet />
      <form onSubmit={run} noValidate>
        <div className="grid">
          <Field label="Host plant" error={tried && !hostId ? "Choose the host plant." : null}>{pick(hostId, setHostId)}</Field>
          <Field label="Donor plant" error={tried && !donorId ? "Choose the donor plant." : tried && same ? "Host and donor must be different." : null}>{pick(donorId, setDonorId)}</Field>
        </div>
        <Field label="Donor genes" hint="Separate several with commas." error={tried && ids.length === 0 ? "Enter at least one gene." : null}>
          {(a) => <input {...a} value={genes} onChange={(e) => setGenes(e.target.value)} />}
        </Field>
        <label className="check"><input type="checkbox" checked={persist} onChange={(e) => setPersist(e.target.checked)} />Save the results</label>
        <Button type="submit" busy={busy}>Compare</Button>
        {busy && <p className="muted" role="status" style={{ marginTop: 8 }}>Searching the host plant’s genes. This usually takes under a minute.</p>}
      </form>
      <div style={{ marginTop: 12 }}><ErrorNote error={error} /></div>
      {rows && (
        <>
          <TableWrap label="Comparison results">
            <table>
              <thead><tr><th>Donor gene</th><th>Closest host gene</th><th className="num">Similarity</th><th>Result</th></tr></thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.donor_gene}>
                    <td className="mono">{r.donor_gene}</td>
                    <td className="mono">{r.host_gene ?? "none found"}</td>
                    <td className="num">{r.percent_identity != null ? `${r.percent_identity.toFixed(0)}%` : "–"}</td>
                    <td>{MATCH_WORDS[r.sequence_relationship]}{r.reciprocal_best_hit ? " · mutual best match" : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableWrap>
          <p className="muted" style={{ marginTop: 8 }}>Similarity is how alike the two proteins are. It does not say the gene would work in the host.</p>
          <ExplainButton
            key={JSON.stringify(rows)}
            kind="comparison"
            facts={{
              comparisons: rows.map((r) => ({
                donor_gene: r.donor_gene,
                closest_host_gene: r.host_gene,
                percent_identity: r.percent_identity,
                mutual_best_match: r.reciprocal_best_hit,
                sequence_relationship: r.sequence_relationship,
              })),
              note: "Similarity says how alike two proteins are. It does not say the gene would work in the host.",
            }}
          />
        </>
      )}
    </Card>
  );
}

function Manual() {
  const [input, setInput] = useState<AssessInput>(DEFAULT_ASSESS);
  const [result, setResult] = useState<AssessResult | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [pident, setPident] = useState("");
  const [evalue, setEvalue] = useState("");
  const [blastErr, setBlastErr] = useState<string | null>(null);

  const fromBlast = async () => {
    const p = Number(pident), ev = Number(evalue);
    if (pident.trim() === "" || evalue.trim() === "" || !(p >= 0 && p <= 100) || !(ev >= 0)) {
      setBlastErr("Identity must be 0–100 and the E-value a number such as 1e-30.");
      return;
    }
    setBlastErr(null);
    try { setInput({ ...input, sequence: (await classify(p, ev)).sequence_relationship }); } catch (e) { setError(e as Error); }
  };

  return (
    <>
      <p className="muted">Set what is known about a gene pair. “Unknown” is a valid answer. There is no score, only what is supported and what is missing.</p>
      <AssessmentFields value={input} onChange={setInput} />
      <details style={{ margin: "0 0 12px" }}>
        <summary>Fill “sequence relationship” from a BLAST result</summary>
        <div className="grid" style={{ marginTop: 8 }}>
          <Field label="% identity" error={blastErr}>{(a) => <input {...a} inputMode="decimal" value={pident} onChange={(e) => setPident(e.target.value)} />}</Field>
          <Field label="E-value">{(a) => <input {...a} value={evalue} onChange={(e) => setEvalue(e.target.value)} placeholder="1e-30" />}</Field>
        </div>
        <Button variant="secondary" small onClick={fromBlast}>Use this result</Button>
      </details>
      <Button onClick={async () => { setError(null); try { setResult(await assess(input)); } catch (e) { setError(e as Error); } }}>Assess</Button>
      <ErrorNote error={error} />
      {result && (
        <div aria-live="polite" style={{ marginTop: 12 }}>
          <p><EvidenceBadge level={result.level} /> <strong>{result.deserves_investigation ? "Worth investigating further." : "Not enough support to continue yet."}</strong></p>
          <p>{result.explanation}</p>
          {result.concerns.length > 0 && <><h4>Concerns</h4><ul>{result.concerns.map((c) => <li key={c}>{c}</li>)}</ul></>}
          {result.missing_information.length > 0 && <><h4>Still unknown</h4><ul>{result.missing_information.map((c) => <li key={c}>{c}</li>)}</ul></>}
        </div>
      )}
    </>
  );
}

export function GeneBridge() {
  const saved = useAsync(listComparisons);
  const count = saved.data?.length ?? 0;
  return (
    <>
      <PageHead title="Compare genes">Find which host gene is most like a donor gene, then judge how well supported the match is.</PageHead>
      <Screening onSaved={saved.reload} />
      <More summary="Rate a gene pair by hand (advanced)"><Manual /></More>
      {(saved.loading || count > 0 || saved.error) && (
        <More summary={`Saved comparisons${count ? ` (${count})` : ""}`}>
          {saved.loading ? <Skeleton lines={3} /> : saved.error ? <ErrorNote error={saved.error} quiet /> : count === 0 ? <EmptyState icon="info" title="Nothing saved yet" /> : (
            <TableWrap label="Saved comparisons">
              <table>
                <thead><tr><th>Donor gene</th><th>Host gene</th><th className="num">Similarity</th><th>Support</th></tr></thead>
                <tbody>
                  {saved.data?.map((c) => (
                    <tr key={c.id}>
                      <td className="mono">{c.donor_gene}</td><td className="mono">{c.host_gene}</td>
                      <td className="num">{c.percent_identity != null ? `${c.percent_identity.toFixed(0)}%` : "–"}</td>
                      <td><EvidenceBadge level={c.overall_level} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableWrap>
          )}
        </More>
      )}
    </>
  );
}
