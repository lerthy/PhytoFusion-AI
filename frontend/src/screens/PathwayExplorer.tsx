import cytoscape from "cytoscape";
import { useEffect, useRef, useState } from "react";
import { getPathway, listPathways, savePathway } from "../api";
import { ErrorNote } from "../components/ErrorNote";
import { EvidenceBadge } from "../components/EvidenceBadge";
import { FileLoader } from "../components/FileLoader";
import { Alert, Button, Card, EmptyState, Field, More, PageHead, TableWrap } from "../components/ui";
import { useAsync } from "../hooks";
import kpsExample from "../../../data/pathways/kps-clerodane.json";
import { validateElements, type Element } from "../pathway";
import type { Level } from "../types";

const css = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

export function PathwayExplorer() {
  const container = useRef<HTMLDivElement>(null);
  const saved = useAsync(listPathways);
  const [elements, setElements] = useState<Element[] | null>(null);
  const [title, setTitle] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<Error | null>(null);
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);
  const [pick, setPick] = useState("");
  const [name, setName] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!elements || !container.current) return;
    const text = css("--text"), border = css("--border-strong"), ok = css("--ok"), warn = css("--warn"), bad = css("--bad"), gene = css("--viz-1"), surface = css("--surface"), surface2 = css("--surface-2");
    const edge = (level: Level, color: string, style: "solid" | "dotted" | "dashed") => ({
      selector: `edge[evidence_level = '${level}']`,
      style: { "line-color": color, "target-arrow-color": color, "line-style": style },
    });
    const cy = cytoscape({
      container: container.current,
      elements: elements as cytoscape.ElementDefinition[],
      layout: { name: "breadthfirst", directed: true, padding: 24 },
      style: [
        { selector: "node", style: { label: "data(label)", "font-size": 12, color: text, "text-valign": "bottom", "text-margin-y": 6, "text-background-color": surface, "text-background-opacity": 0.92, "text-background-padding": "3px", "text-background-shape": "roundrectangle", width: 30, height: 30, "background-color": surface2, "border-width": 2, "border-color": border } },
        { selector: "node[kind = 'compound']", style: { shape: "round-rectangle" } },
        { selector: "node[kind = 'gene']", style: { shape: "diamond", "background-color": gene, "border-color": gene, width: 34, height: 34 } },
        { selector: "edge", style: { width: 2, "curve-style": "bezier", "target-arrow-shape": "triangle", "line-color": border, "target-arrow-color": border } },
        edge("strong", ok, "solid"), edge("moderate", warn, "dotted"), edge("limited", bad, "dashed"),
        { selector: ":selected", style: { "border-color": css("--ring"), "border-width": 4, "overlay-opacity": 0 } },
      ],
    });
    cy.on("tap", "node, edge", (evt) => setSelected(evt.target.data()));
    cy.on("tap", (evt) => evt.target === cy && setSelected(null));
    return () => cy.destroy();
  }, [elements]);

  const open = (els: Element[], label: string) => { setElements(els); setTitle(label); setSelected(null); setLoadError(null); };
  const edges = (elements ?? []).map((e) => e.data).filter((d) => "source" in d);
  const hasSaved = (saved.data?.length ?? 0) > 0;

  return (
    <>
      <PageHead title="Pathways">How genes, enzymes and compounds connect, with the evidence behind every step. Steps without a PMID or DOI are rejected.</PageHead>

      <Card title="Open a pathway" icon="network">
        {hasSaved && (
          <div className="row" style={{ alignItems: "flex-end" }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <Field label="Saved pathway">
                {(a) => (
                  <select {...a} value={pick} onChange={(e) => setPick(e.target.value)}>
                    <option value="">Choose…</option>
                    {saved.data?.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                )}
              </Field>
            </div>
            <div style={{ marginBottom: 12 }}>
              <Button disabled={!pick} onClick={async () => {
                setApiError(null);
                try { const p = await getPathway(pick); open(validateElements(p.graph), p.name); } catch (e) { setApiError(e as Error); }
              }}>Open</Button>
            </div>
          </div>
        )}
        <div className="row" style={{ marginBottom: 12 }}>
          <Button onClick={() => open(validateElements(kpsExample), "KPS enzymes (Qiu et al. 2023)")}>Try the KPS example</Button>
          <span className="muted">The case-study enzymes, with every step sourced (PMID 37395679).</span>
        </div>
        <FileLoader label={hasSaved ? "Or open a JSON file" : "Open a pathway JSON file"} accept=".json" hint="The format produced by the backend's to_cytoscape()."
          onText={(text, file) => { try { open(validateElements(JSON.parse(text)), file); } catch (e) { setElements(null); setLoadError((e as Error).message); } }} />
        {loadError && <Alert kind="error" title="Could not open this graph">{loadError}</Alert>}
        <ErrorNote error={saved.error} quiet />
        <ErrorNote error={apiError} />
      </Card>

      {!elements ? (
        <EmptyState icon="network" title="No pathway open">Choose “Try the KPS example” above to see how the genes and compounds connect.</EmptyState>
      ) : (
        <>
          <Card title={title || "Pathway"} icon="network">
            <div className="legend" aria-label="Legend">
              {([["strong", "var(--ok)", ""], ["moderate", "var(--warn)", "2 4"], ["limited", "var(--bad)", "6 4"]] as const).map(([l, c, d]) => (
                <span key={l}><svg width="34" height="10" aria-hidden="true"><line x1="0" y1="5" x2="34" y2="5" stroke={c} strokeWidth="2.5" strokeDasharray={d} /></svg>{l}</span>
              ))}
              <span><svg width="12" height="12" aria-hidden="true"><path d="M6 0 12 6 6 12 0 6Z" fill="var(--viz-1)" /></svg>gene</span><span><svg width="12" height="12" aria-hidden="true"><rect x="1" y="1" width="10" height="10" rx="3" fill="var(--surface-2)" stroke="var(--border-strong)" strokeWidth="1.5" /></svg>compound</span>
            </div>
            <div className={`pathway-wrap ${selected ? "has-side" : ""}`}>
              <div ref={container} className="pathway" role="img" aria-label={`Pathway graph with ${edges.length} steps. The table below lists every step.`} />
              {selected && (
                <aside className="card" style={{ margin: 0 }} aria-label="Selection details">
                  <h4>{String(selected.label ?? selected.relation ?? selected.id)}</h4>
                  <dl className="kv">{Object.entries(selected).map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{String(v)}</dd></div>)}</dl>
                </aside>
              )}
            </div>
          </Card>
          <More summary={`Show the ${edges.length} steps as a table`}>
            <TableWrap label="Pathway steps">
              <table>
                <thead><tr><th>From</th><th>To</th><th>Evidence</th><th>Source</th></tr></thead>
                <tbody>
                  {edges.map((d, i) => (
                    <tr key={i}>
                      <td className="mono">{String(d.source)}</td><td className="mono">{String(d.target)}</td>
                      <td><EvidenceBadge level={d.evidence_level as Level} /></td><td className="mono">{String(d.reference)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableWrap>
          </More>
          <More summary="Save this pathway">
            <Field label="Name">{(a) => <input {...a} value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Flavonoid biosynthesis" />}</Field>
            <Button disabled={!name.trim()} onClick={async () => {
              setApiError(null); setNotice(null);
              try { await savePathway(name.trim(), elements); setNotice(`Saved “${name.trim()}”.`); setName(""); saved.reload(); } catch (e) { setApiError(e as Error); }
            }}>Save</Button>
            {notice && <p role="status" style={{ marginTop: 8 }}>{notice}</p>}
          </More>
        </>
      )}
    </>
  );
}
