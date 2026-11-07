"""Engine 2: comparative genomics.

Pure parsing and classification logic plus one thin BLAST+ wrapper. The thresholds below are
conventional starting defaults for protein similarity, NOT scientific claims about these species;
they are parameters so the science team can tune them and cite the choice.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from .genebridge import SequenceRelationship
from .ingestion.gff3 import GeneRecord

BLAST_FIELDS = "qseqid sseqid pident length evalue bitscore"


@dataclass(frozen=True)
class BlastHit:
    query: str
    subject: str
    pident: float
    length: int
    evalue: float
    bitscore: float


def read_fasta(lines: Iterable[str]) -> dict[str, str]:
    """Parse FASTA into {id: sequence}. The id is the first token of the header."""
    records: dict[str, list[str]] = {}
    current: str | None = None
    for number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            header = line[1:].split()
            if not header:
                raise ValueError(f"line {number}: empty FASTA header")
            current = header[0]
            if current in records:
                raise ValueError(f"line {number}: duplicate FASTA id {current!r}")
            records[current] = []
        else:
            if current is None:
                raise ValueError(f"line {number}: sequence before any header")
            records[current].append(line)
    return {k: "".join(v) for k, v in records.items()}


@dataclass(frozen=True)
class FastaRecord:
    id: str  # first token of the header
    description: str  # the rest of the header line (may hold key=value notes)
    sequence: str


def read_fasta_records(lines: Iterable[str]) -> list[FastaRecord]:
    """Like read_fasta, but keeps each header's description so notes such as OriGeneID= survive."""
    heads: dict[str, str] = {}
    parts: dict[str, list[str]] = {}
    current: str | None = None
    for number, line in enumerate(lines, start=1):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith(">"):
            header = line[1:].strip().split(None, 1)
            if not header:
                raise ValueError(f"line {number}: empty FASTA header")
            current = header[0]
            if current in parts:
                raise ValueError(f"line {number}: duplicate FASTA id {current!r}")
            heads[current] = header[1] if len(header) > 1 else ""
            parts[current] = []
        else:
            if current is None:
                raise ValueError(f"line {number}: sequence before any header")
            parts[current].append(line.strip())
    return [FastaRecord(k, heads[k], "".join(v)) for k, v in parts.items()]


def parse_blast_tabular(lines: Iterable[str]) -> list[BlastHit]:
    """Parse BLAST outfmt 6 produced with BLAST_FIELDS."""
    hits: list[BlastHit] = []
    for number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) != 6:
            raise ValueError(f"line {number}: expected 6 columns, got {len(cols)}")
        try:
            hits.append(
                BlastHit(
                    cols[0], cols[1], float(cols[2]), int(cols[3]), float(cols[4]), float(cols[5])
                )
            )
        except ValueError as exc:
            raise ValueError(f"line {number}: malformed numeric field") from exc
    return hits


def best_hits(hits: Iterable[BlastHit]) -> dict[str, BlastHit]:
    """Best hit per query: highest bitscore, ties broken by lower e-value then subject id."""
    best: dict[str, BlastHit] = {}
    for hit in hits:
        current = best.get(hit.query)
        if current is None or _rank(hit) < _rank(current):
            best[hit.query] = hit
    return best


def _rank(hit: BlastHit) -> tuple[float, float, str]:
    return (-hit.bitscore, hit.evalue, hit.subject)


def reciprocal_best_hits(
    a_vs_b: Iterable[BlastHit], b_vs_a: Iterable[BlastHit]
) -> list[tuple[str, str]]:
    """Pairs (a, b) where each is the other's best hit: candidate orthologs, sorted by id."""
    forward = best_hits(a_vs_b)
    reverse = best_hits(b_vs_a)
    pairs = [
        (a, hit.subject)
        for a, hit in forward.items()
        if reverse.get(hit.subject) and reverse[hit.subject].subject == a
    ]
    return sorted(pairs)


def classify_sequence_relationship(
    hit: BlastHit | None,
    *,
    related_min_pident: float = 40.0,
    related_max_evalue: float = 1e-10,
    weak_max_evalue: float = 1e-3,
) -> SequenceRelationship:
    """Map a BLAST hit to the categorical value used by GeneBridge. No hit means unknown."""
    if hit is None:
        return "unknown"
    if hit.pident >= related_min_pident and hit.evalue <= related_max_evalue:
        return "related"
    if hit.evalue <= weak_max_evalue:
        return "weakly_related"
    return "unknown"


def map_genes_to_chromosomes(
    genes: Sequence[GeneRecord], gene_ids: Iterable[str]
) -> dict[str, GeneRecord | None]:
    """Locate each requested gene id. A missing gene maps to None (reported, not guessed)."""
    index = {g.gene_id: g for g in genes}
    return {gid: index.get(gid) for gid in gene_ids}


Runner = Callable[..., subprocess.CompletedProcess]


def run_blastp(
    query_fasta: Path,
    subject_fasta: Path,
    *,
    evalue: float = 1e-3,
    threads: int | None = None,
    timeout: float = 600,
    runner: Runner = subprocess.run,
    which: Callable[[str], str | None] = shutil.which,
) -> list[BlastHit]:
    """Run `blastp -query ... -subject ...` and parse the result.

    `runner` and `which` are injectable so tests never need BLAST+ installed.
    """
    if which("blastp") is None:
        raise RuntimeError("blastp not found on PATH; install BLAST+ (it is in the Docker image)")
    cmd = [
        "blastp",
        "-query",
        str(query_fasta),
        "-subject",
        str(subject_fasta),
        "-evalue",
        str(evalue),
        "-num_threads",
        str(threads or min(os.cpu_count() or 1, 8)),
        "-max_target_seqs",
        "5",
        "-outfmt",
        f"6 {BLAST_FIELDS}",
    ]
    try:
        result = runner(cmd, capture_output=True, text=True, check=False, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"blastp took longer than {timeout:.0f} s and was stopped") from exc
    if result.returncode != 0:
        raise RuntimeError(f"blastp failed: {result.stderr.strip()}")
    return parse_blast_tabular(result.stdout.splitlines())
