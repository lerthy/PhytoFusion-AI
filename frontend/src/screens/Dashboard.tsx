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

export function Dashboard({ host, donor, goTo }: Props) {
  const health = useAsync(getHealth);
  const stats = useAsync(getStats);
  const s = stats.data;
  const offline = !!health.error;

  const genomeStatus = s && s.genes > 0
    ? `${s.species} species, ${s.genes.toLocaleString()} genes ready`
    : host || donor ? "Genome opened from a file" : "No genomes yet";
  const compareStatus = s ? `${s.gene_comparisons} saved comparison${s.gene_comparisons === 1 ? "" : "s"}` : "";
  const scenarioStatus = s ? `${s.crispr_scenarios} saved scenario${s.crispr_scenarios === 1 ? "" : "s"}` : "";

  const cards = [
    { n: 1, title: "Look at the genomes", text: "See the two plants' chromosomes and find the genes you care about.", status: genomeStatus, to: "genome" as const, cta: "Open genomes" },
    { n: 2, title: "Compare genes", text: "Find the closest match for a donor gene in the host plant, and see how well supported it is.", status: compareStatus, to: "genebridge" as const, cta: "Compare genes" },
    { n: 3, title: "Try a scenario", text: "Explore a hypothetical gene transfer and read what it could mean and what is still unknown.", status: scenarioStatus, to: "crispr" as const, cta: "Start a scenario" },
  ];

  return (
    <>
      <PageHead title="Explore what a gene transfer between two medicinal plants could mean">
        Compare genes, check the evidence, and try a hypothetical CRISPR scenario. Nothing is edited or built: it is a thinking tool.
      </PageHead>

      <div className="statusline" aria-live="polite">
        <span className={`badge ${offline ? "limited" : health.data ? "strong" : "neutral"}`}>
          <Icon name={offline ? "alert" : "check"} size={14} />Backend {offline ? "offline" : health.data ? "online" : "checking"}
        </span>
        <span className={`badge ${s ? "strong" : stats.loading ? "neutral" : "moderate"}`}>
          <Icon name={s ? "check" : "minus"} size={14} />Database {s ? "connected" : stats.loading ? "checking" : "not connected"}
        </span>
      </div>
      {offline && <Alert kind="error" title="The backend is not running">{health.error?.message}</Alert>}
      {!offline && <ErrorNote error={stats.error} quiet />}
      {!offline && !s && !stats.loading && <p className="muted">Saved data is off until the database is connected. You can still open files and try everything else.</p>}

      <div className="steps">
        {cards.map((c) => (
          <section key={c.n} className="step-card" aria-labelledby={`step-${c.n}`}>
            <span className="big" aria-hidden="true">{c.n}</span>
            <h3 id={`step-${c.n}`}>{c.title}</h3>
            <p>{c.text}</p>
            <p className="status">{c.status}</p>
            <div className="actions"><button className="btn" onClick={() => goTo(c.to)}>{c.cta}</button></div>
          </section>
        ))}
      </div>
    </>
  );
}
