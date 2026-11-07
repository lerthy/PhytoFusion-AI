export type Level = "strong" | "moderate" | "limited";

export const OPTIONS = {
  sequence: ["related", "weakly_related", "unknown"],
  functional: ["characterized", "predicted"],
  pathway: ["supported", "incomplete", "unknown"],
  expression: ["supporting", "conflicting", "unavailable"],
  context: ["characterized", "uncertain"],
} as const;

export type AssessInput = {
  [K in keyof typeof OPTIONS]: (typeof OPTIONS)[K][number];
};

export const DEFAULT_ASSESS: AssessInput = {
  sequence: "unknown",
  functional: "predicted",
  pathway: "unknown",
  expression: "unavailable",
  context: "uncertain",
};

export interface AssessResult {
  level: Level;
  deserves_investigation: boolean;
  missing_information: string[];
  concerns: string[];
  explanation: string;
}

export type ScenarioType = "host_modification" | "donor_integration";

export interface SimulateRequest {
  type: ScenarioType;
  host_species: string;
  target_gene_id: string;
  donor_species: string | null;
  chromosome: string | null;
  documented_function: string | null;
  pathway: string | null;
  references: string[];
  assessment: AssessInput;
}

export interface SimulateResult {
  type: ScenarioType;
  host_species: string;
  donor_species: string | null;
  target_gene_id: string;
  chromosome: string | null;
  documented_function: string | null;
  pathway: string | null;
  scenario: string;
  predicted_consequences: string[];
  compatibility_issues: string[];
  missing_information: string[];
  limitations: string[];
  evidence_level: Level;
  references: string[];
  assessment?: AssessInput | null;
  report_markdown: string;
}

// ---- persisted data (GET/POST /api/...) ----------------------------------------------------
export interface Stats {
  species: number; genome_assemblies: number; chromosomes: number; genes: number; evidence: number;
  literature_chunks: number; gene_comparisons: number; pathways: number; crispr_scenarios: number;
}
export interface Species { id: string; scientific_name: string; role: "host" | "donor"; common_name: string | null }
export interface GenomeResponse {
  species: Species;
  accessions: string[];
  chromosomes: { name: string; accession?: string | null; length_bp: number | null }[];
  genes: { gene_id: string; chromosome: string | null; family: string | null; start_bp: number; end_bp: number; strand: string; annotation: string | null }[];
}
export interface EvidenceRow { id: string; pmid: string | null; doi: string | null; title: string | null; finding: string; level: Level }
export interface LiteratureHit { content: string; similarity: number; pmid: string | null; doi: string | null; title: string | null }
export interface PipelineRow {
  donor_gene: string; host_gene: string | null; percent_identity: number | null; evalue: number | null;
  reciprocal_best_hit: boolean; sequence_relationship: AssessInput["sequence"]; comparison_id?: string;
}
export interface ComparisonRow {
  id: string; host_gene: string | null; donor_gene: string | null; percent_identity: number | null;
  sequence_relationship: string; functional_evidence: string; overall_level: Level;
}
export interface PathwayItem { id: string; name: string; description: string | null }
export interface ScenarioItem { id: string; created_at?: string; type: ScenarioType; target_gene_id: string; scenario: string; evidence_level: Level }
