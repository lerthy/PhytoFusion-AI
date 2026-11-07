export interface GeneRecord {
  geneId: string;
  chromosome: string;
  start: number;
  end: number;
  strand: string;
  name?: string;
  description?: string;
  family?: string;
}

export interface ParsedGenome {
  genes: GeneRecord[];
  lengths: Record<string, number>;
  /** Sequence id -> friendlier original name, when the file provides one (#OriSeqID comments). */
  aliases?: Record<string, string>;
}

const ID_PREFIX = /^gene[:-]/i;

export function normalizeGeneId(raw: string): string {
  const id = raw.trim().replace(ID_PREFIX, "");
  if (!id) throw new Error("empty gene identifier");
  return id;
}

export function parseAttributes(attr: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const part of attr.split(";")) {
    const piece = part.trim();
    if (!piece) continue;
    const eq = piece.indexOf("=");
    if (eq < 0) throw new Error(`malformed attribute: ${piece}`);
    out[piece.slice(0, eq).trim()] = decodeURIComponent(piece.slice(eq + 1).trim());
  }
  return out;
}

/** Mirrors backend/app/ingestion/gff3.py: strict, and errors carry the 1-based line number. */
export function parseGff3(text: string): ParsedGenome {
  const genes: GeneRecord[] = [];
  const lengths: Record<string, number> = {};
  const aliases: Record<string, string> = {};
  text.split(/\r?\n/).forEach((line, index) => {
    const number = index + 1;
    if (!line.trim()) return;
    if (line.startsWith("##sequence-region")) {
      const parts = line.trim().split(/\s+/);
      if (parts.length !== 4) throw new Error(`line ${number}: malformed sequence-region`);
      lengths[parts[1]] = Number(parts[3]) - Number(parts[2]) + 1;
      return;
    }
    if (line.startsWith("#")) {
      if (line.startsWith("#OriSeqID=")) {
        const parts = line.slice(1).split("\t");
        const original = parts[0].slice("OriSeqID=".length).trim();
        const accession = parts.find((p) => p.startsWith("Accession="))?.slice("Accession=".length).trim();
        if (original && accession) aliases[accession] = original;
      }
      return;
    }
    const cols = line.split("\t");
    if (cols.length !== 9) throw new Error(`line ${number}: expected 9 columns, got ${cols.length}`);
    const [seqid, , type, startRaw, endRaw, , strand, , attrs] = cols;
    if (type !== "gene") return;
    const start = Number(startRaw);
    const end = Number(endRaw);
    if (!Number.isInteger(start) || !Number.isInteger(end)) {
      throw new Error(`line ${number}: non-integer coordinates`);
    }
    if (start < 1 || start > end) throw new Error(`line ${number}: invalid coordinates`);
    if (!["+", "-", ".", "?"].includes(strand)) throw new Error(`line ${number}: invalid strand`);
    const attributes = parseAttributes(attrs);
    if (!("ID" in attributes)) throw new Error(`line ${number}: gene without ID attribute`);
    genes.push({
      geneId: normalizeGeneId(attributes.ID),
      chromosome: seqid,
      start,
      end,
      strand,
      name: attributes.Name,
      description: attributes.Note ?? attributes.description,
    });
  });
  return { genes, lengths, aliases };
}

/** Chromosome length from the directive when present, otherwise the furthest gene end. */
export function chromosomeLengths(genome: ParsedGenome): Record<string, number> {
  const result: Record<string, number> = { ...genome.lengths };
  for (const gene of genome.genes) {
    result[gene.chromosome] = Math.max(result[gene.chromosome] ?? 0, gene.end);
  }
  return result;
}
