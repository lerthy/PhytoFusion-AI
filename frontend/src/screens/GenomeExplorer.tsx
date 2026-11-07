import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { getGenome, listSpecies } from "../api";
import { ChromosomeMap } from "../components/ChromosomeMap";
import { ErrorNote } from "../components/ErrorNote";
import { FileLoader } from "../components/FileLoader";
import { Alert, Button, Card, EmptyState, Field, PageHead, Skeleton, TableWrap } from "../components/ui";
import { defaultSpeciesId, genomeFromApi } from "../genome";
import { chromosomeLengths, parseGff3, type ParsedGenome } from "../gff3";
import { useAsync } from "../hooks";
import type { Species } from "../types";

// Loaded on demand so the 3D library is only downloaded when someone opens the 3D view.
const Genome3D = lazy(() => import("../components/Genome3D"));

const plural = (n: number, word: string) => `${n.toLocaleString()} ${word}${n === 1 ? "" : "s"}`;

interface SlotProps {
  title: string;
  role: "host" | "donor";
  genome: ParsedGenome | null;
  setGenome: (g: ParsedGenome | null) => void;
  species: Species[] | null;
  /** Tells the page which saved species this slot loaded (null for a file or nothing). */
  onSource: (speciesId: string | null) => void;
}

function Slot({ title, role, genome, setGenome, species, onSource }: SlotProps) {
  const [useFile, setUseFile] = useState(false);
  const [speciesId, setSpeciesId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [label, setLabel] = useState("");
  const [filter, setFilter] = useState("");
  const [shown, setShown] = useState(25);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [view, setView] = useState<"map" | "3d">("map");

  const hasDb = !!species && species.length > 0;
  useEffect(() => {
    if (!speciesId) setSpeciesId(defaultSpeciesId(species, role));
  }, [species, role, speciesId]);
  const noneForRole = hasDb && defaultSpeciesId(species, role) === "";

  const lengths = useMemo(() => (genome ? chromosomeLengths(genome) : {}), [genome]);
  const matches = useMemo(() => {
    if (!genome) return [];
    const q = filter.trim().toLowerCase();
    return genome.genes.filter((g) => !q || g.geneId.toLowerCase().includes(q) || (g.family ?? "").toLowerCase().includes(q) || (g.description ?? "").toLowerCase().includes(q));
  }, [genome, filter]);
  const hits = useMemo(() => new Set(filter ? matches.map((g) => g.geneId) : []), [matches, filter]);

  const loadFromDb = async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await getGenome(speciesId);
      setGenome(genomeFromApi(data));
      onSource(speciesId);
      setLabel(data.species.scientific_name);
      setShown(25);
    } catch (e) {
      setError(e as Error);
    } finally {
      setBusy(false);
    }
  };

  const showFile = useFile || !hasDb;

  return (
    <Card title={title} icon="dna">
      {showFile ? (
        <>
          <FileLoader label="Open a GFF3 annotation file" accept=".gff,.gff3,.txt" hint="Read in your browser only. A malformed row stops the load and names its line."
            onText={(text, name) => {
              try { setError(null); setGenome(parseGff3(text)); onSource(null); setLabel(name); setShown(25); } catch (e) { setGenome(null); onSource(null); setError(e as Error); }
            }} />
          {hasDb && <button className="btn small secondary" onClick={() => setUseFile(false)}>Use a saved species instead</button>}
        </>
      ) : (
        <>
          <div className="row" style={{ alignItems: "flex-end" }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <Field label="Species">
                {(a) => (
                  <select {...a} value={speciesId} onChange={(e) => setSpeciesId(e.target.value)}>
                    <option value="">Choose…</option>
                    {species?.map((s) => <option key={s.id} value={s.id}>{s.scientific_name} · {s.role}</option>)}
                  </select>
                )}
              </Field>
            </div>
            <div style={{ marginBottom: 12 }}><Button onClick={loadFromDb} busy={busy} disabled={!speciesId}>Load</Button></div>
          </div>
          {noneForRole && !genome && <p className="muted" style={{ margin: "0 0 8px" }}>No {role} plant is saved yet. Choose one, or open its GFF3 file.</p>}
          <button className="btn small secondary" onClick={() => setUseFile(true)}>Open a file instead</button>
        </>
      )}
      <div style={{ marginTop: 12 }}><ErrorNote error={error} /></div>

      {!genome && !error && <EmptyState icon="dna" title="Nothing loaded yet" />}
      {genome && (
        <>
          <p style={{ marginTop: 12 }}><strong>{label}</strong> <span className="muted">· {plural(genome.genes.length, "gene")} · {plural(Object.keys(lengths).length, "sequence")}</span></p>
          <div className="seg" role="group" aria-label="View">
            <button type="button" aria-pressed={view === "map"} onClick={() => setView("map")}>Map</button>
            <button type="button" aria-pressed={view === "3d"} onClick={() => setView("3d")}>3D</button>
          </div>
          {view === "map" ? (
            <ChromosomeMap label={title} lengths={lengths} genes={genome.genes} hits={hits} activeId={activeId} names={genome.aliases} />
          ) : (
            <Suspense fallback={<Skeleton lines={5} />}>
              <Genome3D label={title} lengths={lengths} genes={genome.genes} hits={hits} names={genome.aliases} />
            </Suspense>
          )}
          <Field label="Find a gene" hint={filter ? `${matches.length} found, highlighted on the map` : undefined}>
            {(a) => <input {...a} type="search" value={filter} onChange={(e) => { setFilter(e.target.value); setShown(25); }} placeholder="Gene name, family or note" />}
          </Field>
          {matches.length === 0 ? <EmptyState icon="search" title="No genes match" /> : (
            <TableWrap label={`${title} genes`}>
              <table>
                <thead><tr><th>Gene</th><th>Location</th><th>Notes</th></tr></thead>
                <tbody>
                  {matches.slice(0, shown).map((g) => (
                    <tr key={g.geneId} tabIndex={0} className={activeId === g.geneId ? "is-active" : undefined}
                      onMouseEnter={() => setActiveId(g.geneId)} onMouseLeave={() => setActiveId(null)}
                      onFocus={() => setActiveId(g.geneId)} onBlur={() => setActiveId(null)}>
                      <td className="mono">{g.geneId}</td>
                      <td>{genome.aliases?.[g.chromosome] ?? g.chromosome}: {g.start.toLocaleString()}–{g.end.toLocaleString()}</td>
                      <td>{[g.family, g.description].filter(Boolean).join(" · ") || "–"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableWrap>
          )}
          {matches.length > shown && <div style={{ marginTop: 8 }}><Button variant="secondary" small onClick={() => setShown(shown + 100)}>Show more ({matches.length - shown} left)</Button></div>}
        </>
      )}
    </Card>
  );
}

interface Props {
  host: ParsedGenome | null;
  donor: ParsedGenome | null;
  setHost: (g: ParsedGenome | null) => void;
  setDonor: (g: ParsedGenome | null) => void;
}

export function GenomeExplorer({ host, donor, setHost, setDonor }: Props) {
  const species = useAsync(listSpecies);
  const [hostSource, setHostSource] = useState<string | null>(null);
  const [donorSource, setDonorSource] = useState<string | null>(null);
  const samePlant = !!hostSource && hostSource === donorSource;
  return (
    <>
      <PageHead title="Genomes">Open the host plant (the one that would receive a gene) and the donor plant (the one the gene comes from).</PageHead>
      <ErrorNote error={species.error} quiet />
      {samePlant && <Alert kind="warn" title="Host and donor are the same plant">A gene transfer needs two different plants. Choose a different species or open a different file for one of them.</Alert>}
      <div className="cols-2">
        <Slot title="Host plant" role="host" genome={host} setGenome={setHost} species={species.data} onSource={setHostSource} />
        <Slot title="Donor plant" role="donor" genome={donor} setGenome={setDonor} species={species.data} onSource={setDonorSource} />
      </div>
    </>
  );
}
