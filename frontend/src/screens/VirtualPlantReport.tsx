import { useState } from "react";
import { getScenario, listScenarios } from "../api";
import { ErrorNote } from "../components/ErrorNote";
import { EvidenceBadge } from "../components/EvidenceBadge";
import { Icon } from "../components/Icon";
import { ScenarioVisual } from "../components/ScenarioVisual";
import { Button, EmptyState, More, PageHead } from "../components/ui";
import { useAsync } from "../hooks";
import type { SimulateResult } from "../types";

const cap = (t: string) => t.charAt(0).toUpperCase() + t.slice(1);

function List({ items, empty }: { items: string[]; empty: string }) {
  return items.length ? <ul className="report-list">{items.map((i) => <li key={i}>{i}</li>)}</ul> : <p className="muted">{empty}</p>;
}

function Section({ title, icon, items, empty, tone }: { title: string; icon: "check" | "info" | "alert"; items: string[]; empty: string; tone?: "limits" }) {
  return (
    <section className={`rsec ${tone ?? ""}`}>
      <h3><Icon name={icon} />{title}</h3>
      {items.length ? <ul className="report-list">{items.map((i) => <li key={i}>{cap(i)}</li>)}</ul> : <p className="muted">{empty}</p>}
    </section>
  );
}

interface Props {
  result: SimulateResult | null;
  onOpen: (r: SimulateResult) => void;
  goToScenario: () => void;
}

export function VirtualPlantReport({ result, onOpen, goToScenario }: Props) {
  const saved = useAsync(listScenarios);
  const [error, setError] = useState<Error | null>(null);
  const count = saved.data?.length ?? 0;

  const download = () => {
    if (!result) return;
    const url = URL.createObjectURL(new Blob([result.report_markdown], { type: "text/markdown" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `report-${result.target_gene_id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <PageHead title="Report" />
      {result ? (
        <>
          <div className="banner"><Icon name="alert" /><div><strong>Hypothetical.</strong> Nothing has been edited or built, and this says nothing about how well a medicine would work.</div></div>
          <section className="rhero">
            <p className="eyebrow">Scenario</p>
            <h3>{result.scenario}</h3>
            <p className="row">
              <span>Gene <strong className="mono">{result.target_gene_id}</strong></span>
              {result.chromosome && <span className="muted">on {result.chromosome}</span>}
              <EvidenceBadge level={result.evidence_level} />
            </p>
            <div className="row">
              <Button variant="secondary" small onClick={goToScenario}>Change the scenario</Button>
              <Button variant="secondary" small onClick={download}><Icon name="download" size={16} />Download</Button>
            </div>
          </section>
          <ScenarioVisual result={result} />
          <Section title="What this could mean" icon="check" items={result.predicted_consequences} empty="Nothing can be said from the information given." />
          <Section title="What we don’t know" icon="info" items={[...result.compatibility_issues, ...result.missing_information]} empty="No gaps were identified from the information given." />
          <Section title="Limits of this scenario" icon="alert" items={result.limitations} empty="" tone="limits" />
          <More summary={`Sources (${result.references.length})`}><List items={result.references} empty="No sources were given." /></More>
        </>
      ) : (
        <EmptyState icon="report" title="No report yet">
          <Button onClick={goToScenario}>Start a scenario</Button>
        </EmptyState>
      )}

      {(saved.loading || count > 0 || saved.error) && (
        <More summary={`Saved scenarios${count ? ` (${count})` : ""}`}>
          {saved.error ? <ErrorNote error={saved.error} quiet /> : (
            <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
              {saved.data?.map((s) => (
                <li key={s.id} className="row between">
                  <span><strong className="mono">{s.target_gene_id}</strong> · {s.scenario}</span>
                  <span className="row"><EvidenceBadge level={s.evidence_level} />
                    <Button variant="secondary" small onClick={async () => { setError(null); try { onOpen(await getScenario(s.id)); } catch (e) { setError(e as Error); } }}>Open</Button>
                  </span>
                </li>
              ))}
            </ul>
          )}
          <ErrorNote error={error} />
        </More>
      )}
    </>
  );
}
