import { useState } from "react";
import { addEvidence, addLiterature, listEvidence, searchLiterature } from "../api";
import { ErrorNote } from "../components/ErrorNote";
import { EvidenceBadge } from "../components/EvidenceBadge";
import { Button, Card, EmptyState, Field, More, PageHead, Skeleton, TableWrap } from "../components/ui";
import { useAsync } from "../hooks";
import type { EvidenceRow, Level, LiteratureHit } from "../types";

const LEVELS: { value: Level; label: string }[] = [
  { value: "strong", label: "Strong: several studies, at least one experimental" },
  { value: "moderate", label: "Moderate: one experimental study, or several computational" },
  { value: "limited", label: "Limited: mostly predictions or missing information" },
];

// The paper behind the case study. Text follows the abstract in docs/SOURCES.md; nothing is added to it.
const KEY_PAPER = {
  pmid: "37395679",
  doi: "10.1111/tpj.16377",
  title: "Tandem duplication and sub-functionalization of clerodane diterpene synthase originate the blooming of clerodane diterpenoids in Scutellaria barbata",
  finding: "SbarKPS1 is a monofunctional (-)-kolavenyl diphosphate synthase. SbarKPS2 and SbaiKPS1 mainly produce neo-cleroda-4(18),13E-dienyl diphosphate with a small amount of (-)-kolavenyl diphosphate. SbarKPS1 and SbarKPS2 are a tandem gene pair with high sequence identity.",
  level: "moderate" as Level,
};

function AddEvidence({ onAdded }: { onAdded: () => void }) {
  const [form, setForm] = useState({ finding: "", level: "moderate" as Level, pmid: "", doi: "", title: "" });
  const [tried, setTried] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm({ ...form, [k]: e.target.value });
  const noSource = !form.pmid.trim() && !form.doi.trim();
  const noFinding = !form.finding.trim();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTried(true);
    if (noSource || noFinding) return;
    setBusy(true);
    setError(null);
    try {
      await addEvidence({ finding: form.finding, level: form.level, pmid: form.pmid || undefined, doi: form.doi || undefined, title: form.title || undefined });
      setForm({ finding: "", level: "moderate", pmid: "", doi: "", title: "" });
      setTried(false);
      onAdded();
    } catch (err) {
      setError(err as Error);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} noValidate>
      <p className="row" style={{ marginTop: 0 }}>
        <Button type="button" variant="secondary" small onClick={() => setForm({ ...KEY_PAPER })}>Fill in the key paper</Button>
        <span className="muted">Qiu et al., The Plant Journal 2023: the KPS enzymes in both plants. Check it, then press Add.</span>
      </p>
      <div className="grid">
        <Field label="PMID" error={tried && noSource ? "Enter a PMID or a DOI." : null}>{(a) => <input {...a} value={form.pmid} onChange={set("pmid")} />}</Field>
        <Field label="DOI">{(a) => <input {...a} value={form.doi} onChange={set("doi")} placeholder="10.xxxx/xxxxx" />}</Field>
      </div>
      <Field label="What the paper found" error={tried && noFinding ? "Describe the finding." : null}>{(a) => <textarea {...a} value={form.finding} onChange={set("finding")} />}</Field>
      <Field label="How well supported is it?">
        {(a) => <select {...a} value={form.level} onChange={set("level")}>{LEVELS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}</select>}
      </Field>
      <Field label="Title (optional)">{(a) => <input {...a} value={form.title} onChange={set("title")} />}</Field>
      <ErrorNote error={error} />
      <Button type="submit" busy={busy}>Add</Button>
    </form>
  );
}

function Papers({ evidence }: { evidence: EvidenceRow[] }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<LiteratureHit[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [evId, setEvId] = useState("");
  const [text, setText] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  const search = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!q.trim()) return;
    setBusy(true);
    setError(null);
    try { setHits(await searchLiterature(q)); } catch (err) { setError(err as Error); setHits(null); } finally { setBusy(false); }
  };

  return (
    <>
      <p className="muted">Search returns passages exactly as written, with their source. Nothing is summarised or generated.</p>
      <form onSubmit={search} className="row" style={{ alignItems: "flex-end" }}>
        <div style={{ flex: 1, minWidth: 200 }}><Field label="Search">{(a) => <input {...a} type="search" value={q} onChange={(e) => setQ(e.target.value)} />}</Field></div>
        <div style={{ marginBottom: 12 }}><Button type="submit" busy={busy} disabled={!q.trim()}>Search</Button></div>
      </form>
      <ErrorNote error={error} />
      {hits && hits.length === 0 && <EmptyState icon="search" title="No passages found" />}
      {hits?.map((h, i) => (
        <blockquote key={i} style={{ margin: "0 0 12px", paddingLeft: 12, borderLeft: "3px solid var(--border-strong)" }}>
          <p>{h.content}</p>
          <footer className="muted">{h.title ?? "Untitled"} · {h.pmid ? `PMID ${h.pmid}` : `DOI ${h.doi}`}</footer>
        </blockquote>
      ))}
      <h4 style={{ margin: "16px 0 8px" }}>Add paper text to search</h4>
      <form onSubmit={async (e) => {
        e.preventDefault(); setError(null); setMsg(null);
        try { const r = await addLiterature(evId, text); setMsg(`Added ${r.chunks} passage${r.chunks === 1 ? "" : "s"}.`); setText(""); } catch (err) { setError(err as Error); }
      }}>
        <Field label="Which paper?">
          {(a) => (
            <select {...a} value={evId} onChange={(e) => setEvId(e.target.value)}>
              <option value="">Choose…</option>
              {evidence.map((ev) => <option key={ev.id} value={ev.id}>{ev.title ?? ev.pmid ?? ev.doi}</option>)}
            </select>
          )}
        </Field>
        <Field label="Text" hint="Only paste text you have the right to use.">{(a) => <textarea {...a} value={text} onChange={(e) => setText(e.target.value)} />}</Field>
        {msg && <p role="status">{msg}</p>}
        <Button type="submit" disabled={!evId || !text.trim()}>Add text</Button>
      </form>
    </>
  );
}

export function Evidence() {
  const list = useAsync(listEvidence);
  const empty = !list.loading && !list.error && list.data?.length === 0;
  return (
    <>
      <PageHead title="Evidence">The papers behind every claim in this app, and how well supported each finding is.</PageHead>
      <Card title="Recorded evidence" icon="book">
        {list.loading ? <Skeleton lines={4} /> : list.error ? <ErrorNote error={list.error} /> : empty ? (
          <EmptyState icon="book" title="No evidence yet">Add the first finding below.</EmptyState>
        ) : (
          <TableWrap label="Evidence">
            <table>
              <thead><tr><th>Source</th><th>Support</th><th>Finding</th></tr></thead>
              <tbody>
                {list.data?.map((ev) => (
                  <tr key={ev.id}>
                    <td className="wrap"><strong>{ev.title ?? "Untitled"}</strong><br /><span className="mono muted">{ev.pmid ? `PMID ${ev.pmid}` : `DOI ${ev.doi}`}</span></td>
                    <td><EvidenceBadge level={ev.level} /></td>
                    <td className="wrap">{ev.finding}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableWrap>
        )}
      </Card>
      <More summary="Add a finding" open={empty}><AddEvidence onAdded={list.reload} /></More>
      <More summary="Search papers"><Papers evidence={list.data ?? []} /></More>
    </>
  );
}
