import { getHealth, getStats } from "../api";
import { ErrorNote } from "../components/ErrorNote";
import { Icon } from "../components/Icon";
import { Alert, PageHead } from "../components/ui";
import { useAsync } from "../hooks";
import type { ParsedGenome } from "../gff3";
import type { RouteId } from "../router";

interface Props {
  host: ParsedGenome | null;
  donor: ParsedGenome | null;
  goTo: (id: RouteId) => void;
}

const plural = (n: number, one: string, many = `${one}s`) => `${n.toLocaleString()} ${n === 1 ? one : many}`;

export function Dashboard({ host, donor, goTo }: Props) {
  const health = useAsync(getHealth);
  const stats = useAsync(getStats);
  const s = stats.data;
  const offline = !!health.error;

  const hasGenomes = (!!s && s.genes > 0) || !!host || !!donor;
  const steps = [
    {
      n: 1, to: "genome" as const, title: "Look at the genomes", cta: "Open genomes",
      text: "See the two plants’ chromosomes and find the genes you care about.",
      done: hasGenomes,
      detail: s && s.genes > 0 ? `${plural(s.species, "plant")} and ${plural(s.genes, "gene")} ready` : host || donor ? "Opened from a file" : "Nothing loaded yet",
    },
    {
      n: 2, to: "genebridge" as const, title: "Compare genes", cta: "Compare genes",
      text: "Find the closest match for a donor gene in the host plant, and see how well supported it is.",
      done: !!s && s.gene_comparisons > 0,
      detail: s ? `${plural(s.gene_comparisons, "saved comparison")}` : "",
    },
    {
      n: 3, to: "crispr" as const, title: "Try a scenario", cta: "Start a scenario",
      text: "Explore a hypothetical gene transfer and read what it could mean and what is still unknown.",
      done: !!s && s.crispr_scenarios > 0,
      detail: s ? `${plural(s.crispr_scenarios, "saved scenario")}` : "",
    },
  ];
  // One main action: the first step that is not done yet. The others stay available but quieter.
  const nextIndex = steps.findIndex((x) => !x.done);

  return (
    <>
      <PageHead title="Explore what a gene transfer between two medicinal plants could mean">
        Compare genes, check the evidence, and try a hypothetical CRISPR scenario. Nothing is edited or built: it is a thinking tool.
      </PageHead>

      {offline && <Alert kind="error" title="The backend is not running">{health.error?.message}</Alert>}
      {!offline && <ErrorNote error={stats.error} quiet />}

      <div className="workspace">
        <ol className="journey" aria-label="The three steps">
          {steps.map((step, i) => {
            const state = step.done ? "done" : i === nextIndex ? "next" : "later";
            return (
              <li key={step.n} className={state}>
                <span className="mark" aria-hidden="true">{step.done ? <Icon name="check" size={20} /> : step.n}</span>
                <div>
                  <p className="state">
                    {state === "done" && <><Icon name="check" size={14} />Done</>}
                    {state === "next" && "Next"}
                    {state === "later" && "Later"}
                    {step.detail && <span className="muted" style={{ fontWeight: 400 }}>&nbsp;·&nbsp;{step.detail}</span>}
                  </p>
                  <h3>{step.title}</h3>
                  <p>{step.text}</p>
                  <button className={`btn ${state === "next" ? "accent" : "secondary"}`} onClick={() => goTo(step.to)}>{step.cta}</button>
                </div>
              </li>
            );
          })}
        </ol>

        <aside className="datapanel" aria-label="What is loaded">
          <h3>Your data</h3>
          {s ? (
            <dl>
              <dt>Plants</dt><dd>{s.species}</dd>
              <dt>Genes</dt><dd>{s.genes.toLocaleString()}</dd>
              <dt>Chromosomes</dt><dd>{s.chromosomes.toLocaleString()}</dd>
              <dt>Evidence entries</dt><dd>{s.evidence}</dd>
              <dt>Pathways</dt><dd>{s.pathways}</dd>
              <dt>Saved comparisons</dt><dd>{s.gene_comparisons}</dd>
              <dt>Saved scenarios</dt><dd>{s.crispr_scenarios}</dd>
            </dl>
          ) : (
            <p className="muted" style={{ margin: 0 }}>
              {stats.loading ? "Checking the database…" : "Saved data is off until the database is connected. You can still open files and try everything else."}
            </p>
          )}
          <div className="health" aria-live="polite">
            <span className={`badge ${offline ? "limited" : health.data ? "strong" : "neutral"}`}>
              <Icon name={offline ? "alert" : "check"} size={14} />Backend {offline ? "offline" : health.data ? "online" : "checking"}
            </span>
            <span className={`badge ${s ? "strong" : stats.loading ? "neutral" : "moderate"}`}>
              <Icon name={s ? "check" : "minus"} size={14} />Database {s ? "connected" : stats.loading ? "checking" : "not connected"}
            </span>
          </div>
        </aside>
      </div>
    </>
  );
}
