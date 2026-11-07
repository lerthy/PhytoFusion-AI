import { useState } from "react";
import { listSpecies, saveScenario, simulate } from "../api";
import { AssessmentFields } from "../components/AssessmentFields";
import { ErrorNote } from "../components/ErrorNote";
import { Button, Card, Field, More, PageHead } from "../components/ui";
import type { ParsedGenome } from "../gff3";
import { useAsync } from "../hooks";
import { DEFAULT_ASSESS, type AssessInput, type ScenarioType, type SimulateResult } from "../types";

interface Props {
  host: ParsedGenome | null;
  donor: ParsedGenome | null;
  onResult: (r: SimulateResult) => void;
  goToReport: () => void;
}

const orNull = (s: string) => (s.trim() ? s.trim() : null);

export function CrisprStudio({ host, donor, onResult, goToReport }: Props) {
  const species = useAsync(listSpecies);
  const [type, setType] = useState<ScenarioType>("donor_integration");
  const [hostSpecies, setHostSpecies] = useState("");
  const [donorSpecies, setDonorSpecies] = useState("");
  const [geneId, setGeneId] = useState("");
  const [chromosome, setChromosome] = useState("");
  const [fn, setFn] = useState("");
  const [pathway, setPathway] = useState("");
  const [refs, setRefs] = useState("");
  const [assessment, setAssessment] = useState<AssessInput>(DEFAULT_ASSESS);
  const [save, setSave] = useState(false);
  const [tried, setTried] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [busy, setBusy] = useState(false);

  const integration = type === "donor_integration";
  const source = integration ? donor : host;
  const problems = {
    host: !hostSpecies.trim() ? "Enter the host plant." : null,
    donor: integration && !donorSpecies.trim() ? "Enter the donor plant." : null,
    gene: !geneId.trim() ? "Enter the gene." : null,
  };
  const invalid = Object.values(problems).some(Boolean);

  const onGene = (id: string) => {
    setGeneId(id);
    const found = source?.genes.find((g) => g.geneId === id);
    if (found) setChromosome(found.chromosome);
  };

  const run = async (e: React.FormEvent) => {
    e.preventDefault();
    setTried(true);
    if (invalid) return;
    setBusy(true);
    setError(null);
    const body = {
      type, host_species: hostSpecies.trim(), donor_species: integration ? orNull(donorSpecies) : null,
      target_gene_id: geneId.trim(), chromosome: orNull(chromosome), documented_function: orNull(fn),
      pathway: orNull(pathway), references: refs.split(",").map((r) => r.trim()).filter(Boolean), assessment,
    };
    try {
      onResult(save ? await saveScenario(body) : await simulate(body));
      goToReport();
    } catch (err) {
      setError(err as Error);
    } finally {
      setBusy(false);
    }
  };

  const names = species.data?.map((s) => s.scientific_name) ?? []; // optional suggestions; a missing database is fine

  return (
    <>
      <PageHead title="New scenario">Pick a gene and see what moving it into another plant could mean, and what is still unknown.</PageHead>
      <form onSubmit={run} noValidate>
        <Card>
          <div className="seg" role="group" aria-label="Scenario type">
            <button type="button" aria-pressed={integration} onClick={() => setType("donor_integration")}>Add a gene from another plant</button>
            <button type="button" aria-pressed={!integration} onClick={() => setType("host_modification")}>Change a gene in the host</button>
          </div>
          <div className="grid">
            <Field label="Host plant" error={tried ? problems.host : null} hint="The plant that would receive the change.">
              {(a) => <input {...a} list="species-names" value={hostSpecies} onChange={(e) => setHostSpecies(e.target.value)} />}
            </Field>
            {integration && (
              <Field label="Donor plant" error={tried ? problems.donor : null} hint="Where the gene comes from.">
                {(a) => <input {...a} list="species-names" value={donorSpecies} onChange={(e) => setDonorSpecies(e.target.value)} />}
              </Field>
            )}
            <Field label="Gene" error={tried ? problems.gene : null} hint={source ? "Suggestions come from the genome you opened." : undefined}>
              {(a) => <input {...a} list="gene-ids" value={geneId} onChange={(e) => onGene(e.target.value)} />}
            </Field>
          </div>
          <datalist id="species-names">{names.map((n) => <option key={n} value={n} />)}</datalist>
          <datalist id="gene-ids">{source?.genes.slice(0, 500).map((g) => <option key={g.geneId} value={g.geneId} />)}</datalist>
        </Card>

        <More summary="Add what you know (optional, makes the result more useful)">
          <p className="muted">Copy facts from the paper. Anything left blank is listed as unknown in the report; nothing is made up.</p>
          <Field label="What the gene does (from the paper)">{(a) => <textarea {...a} rows={3} value={fn} onChange={(e) => setFn(e.target.value)} />}</Field>
          <div className="grid">
            <Field label="Pathway">{(a) => <input {...a} value={pathway} onChange={(e) => setPathway(e.target.value)} />}</Field>
            <Field label="Sources" hint="PMIDs or DOIs, separated by commas.">{(a) => <input {...a} value={refs} onChange={(e) => setRefs(e.target.value)} />}</Field>
            <Field label="Chromosome">{(a) => <input {...a} value={chromosome} onChange={(e) => setChromosome(e.target.value)} />}</Field>
          </div>
          <h4 style={{ margin: "8px 0" }}>How well is it supported?</h4>
          <AssessmentFields value={assessment} onChange={setAssessment} />
          <label className="check"><input type="checkbox" checked={save} onChange={(e) => setSave(e.target.checked)} />Save this scenario (the gene and plants must already be in the database)</label>
        </More>

        <ErrorNote error={error} />
        <Button type="submit" busy={busy}>{busy ? "Working…" : "Show me what this could mean"}</Button>
        {tried && invalid && <p className="muted" role="status" style={{ marginTop: 8 }}>Fill in the highlighted fields to continue.</p>}
      </form>
    </>
  );
}
