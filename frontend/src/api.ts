import type {
  AssessInput, AssessResult, ComparisonRow, EvidenceRow, GenomeResponse, Level, LiteratureHit, PathwayItem,
  PipelineRow, ScenarioItem, SimulateRequest, SimulateResult, Species, Stats,
} from "./types";

export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
  /** 503 means the server is up but Supabase (or the embeddings endpoint) is not configured. */
  get notConfigured() { return this.status === 503; }
}

async function request<T>(path: string, init?: RequestInit, timeoutMs?: number): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json" },
      signal: timeoutMs ? AbortSignal.timeout(timeoutMs) : undefined,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "TimeoutError") {
      throw new ApiError(0, `This took longer than ${Math.round((timeoutMs ?? 0) / 1000)} seconds, so it was stopped. Try fewer genes, or check that the backend is not busy.`);
    }
    throw new ApiError(0, `Cannot reach the backend at ${API_URL}. Is it running?`);
  }
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch { /* keep statusText */ }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

const post = <T>(path: string, body: unknown, timeoutMs?: number) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) }, timeoutMs);

export const getHealth = () => request<{ status: string; version: string }>("/health");
export const assess = (input: AssessInput) => post<AssessResult>("/api/genebridge/assess", input);
export const classify = (pident: number, evalue: number) =>
  post<{ sequence_relationship: AssessInput["sequence"] }>("/api/comparison/classify", { pident, evalue });
export const simulate = (req: SimulateRequest) => post<SimulateResult>("/api/scenarios/simulate", req);

export interface GeneLocation {
  gene_id: string;
  chromosome: string | null;
  chromosome_length: number | null;
  start_bp: number;
  end_bp: number;
  strand: string;
  annotation: string | null;
  family: string | null;
}
export const lookupGene = (species: string, gene: string) =>
  request<GeneLocation>(`/api/genes/lookup?species=${encodeURIComponent(species)}&gene=${encodeURIComponent(gene)}`);

export const explainResult = (kind: "comparison" | "report", facts: Record<string, unknown>) =>
  request<{ text: string; model: string }>("/api/explain", { method: "POST", body: JSON.stringify({ kind, facts }) }, 90_000);

export const getStats = () => request<Stats>("/api/stats");
export const listSpecies = () => request<Species[]>("/api/species");
export const getGenome = (id: string) => request<GenomeResponse>(`/api/genome/${encodeURIComponent(id)}`);

export const listEvidence = () => request<EvidenceRow[]>("/api/evidence");
export const addEvidence = (body: { finding: string; level: Level; pmid?: string; doi?: string; title?: string }) =>
  post<EvidenceRow>("/api/evidence", body);
export const addLiterature = (evidence_id: string, text: string) => post<{ chunks: number }>("/api/literature", { evidence_id, text });
export const searchLiterature = (q: string) => request<LiteratureHit[]>(`/api/literature/search?q=${encodeURIComponent(q)}`);

export const compareCandidates = (body: { host_species_id: string; donor_species_id: string; candidate_gene_ids: string[]; persist: boolean }) =>
  post<PipelineRow[]>("/api/pipeline/compare", body, 180_000);
export const listComparisons = () => request<ComparisonRow[]>("/api/comparisons");

export const listPathways = () => request<PathwayItem[]>("/api/pathways");
export const getPathway = (id: string) => request<{ id: string; name: string; graph: { data: Record<string, unknown> }[] }>(`/api/pathways/${encodeURIComponent(id)}`);
export const savePathway = (name: string, elements: unknown[]) => post<{ id: string; name: string }>("/api/pathways", { name, elements });

export const saveScenario = (req: SimulateRequest) => post<SimulateResult & { id: string }>("/api/scenarios", req);
export const listScenarios = () => request<ScenarioItem[]>("/api/scenarios");
export const getScenario = (id: string) => request<SimulateResult & { id: string }>(`/api/scenarios/${encodeURIComponent(id)}`);
