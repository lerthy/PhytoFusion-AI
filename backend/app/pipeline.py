"""Engine 2 -> GeneBridge glue: compare donor candidates against a host proteome.

Only the sequence dimension can be derived from BLAST. The other four stay at conservative
"unknown" defaults unless the caller supplies evidence-backed overrides, so the pipeline can never
make a candidate look better supported than the data allows.
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from .comparison import (
    BlastHit,
    best_hits,
    classify_sequence_relationship,
    reciprocal_best_hits,
    run_blastp,
)
from .genebridge import AssessmentInput, SequenceRelationship

BlastFn = Callable[[Path, Path], list[BlastHit]]

CONSERVATIVE_DEFAULTS = {
    "functional": "predicted",
    "pathway": "unknown",
    "expression": "unavailable",
    "context": "uncertain",
}


@dataclass(frozen=True)
class PairResult:
    donor_id: str
    host_id: str | None
    hit: BlastHit | None
    reciprocal: bool
    sequence_relationship: SequenceRelationship


def write_fasta(path: Path, sequences: dict[str, str]) -> None:
    with path.open("w") as handle:
        for name, seq in sequences.items():
            handle.write(f">{name}\n{seq.rstrip('*')}\n")


def compare_proteomes(
    host: dict[str, str],
    donor: dict[str, str],
    candidates: Iterable[str] | None = None,
    blast: BlastFn = run_blastp,
) -> list[PairResult]:
    """Best host hit for each donor candidate, flagged when the pair is a reciprocal best hit."""
    wanted = list(candidates) if candidates is not None else list(donor)
    missing = [c for c in wanted if c not in donor]
    if missing:
        raise KeyError(f"candidates without a protein sequence: {', '.join(missing)}")
    if not host:
        raise ValueError("host proteome is empty")

    # Searching one proteome against the other in full (tens of thousands of proteins each way)
    # takes hours. Only the candidates are queries, and the reciprocal check queries only their
    # best host hits, which gives the same answer for these genes in seconds.
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        host_fa, donor_fa = folder / "host.fa", folder / "donor.fa"
        write_fasta(host_fa, host)
        write_fasta(donor_fa, donor)

        candidates_fa = folder / "query_donor.fa"
        write_fasta(candidates_fa, {c: donor[c] for c in wanted})
        donor_vs_host = blast(candidates_fa, host_fa)

        best_host_ids = sorted({h.subject for h in best_hits(donor_vs_host).values()})
        host_vs_donor: list[BlastHit] = []
        if best_host_ids:
            hits_fa = folder / "query_host.fa"
            write_fasta(hits_fa, {h: host[h] for h in best_host_ids})
            host_vs_donor = blast(hits_fa, donor_fa)

    best = best_hits(donor_vs_host)
    mutual = set(reciprocal_best_hits(donor_vs_host, host_vs_donor))
    results = []
    for donor_id in wanted:
        hit = best.get(donor_id)
        results.append(
            PairResult(
                donor_id=donor_id,
                host_id=hit.subject if hit else None,
                hit=hit,
                reciprocal=bool(hit and (donor_id, hit.subject) in mutual),
                sequence_relationship=classify_sequence_relationship(hit),
            )
        )
    return results


def assessment_for(pair: PairResult, overrides: dict[str, str] | None = None) -> AssessmentInput:
    """GeneBridge input: sequence from BLAST, the rest conservative unless overridden."""
    values = {**CONSERVATIVE_DEFAULTS, **(overrides or {})}
    return AssessmentInput(sequence=pair.sequence_relationship, **values)  # type: ignore[arg-type]
