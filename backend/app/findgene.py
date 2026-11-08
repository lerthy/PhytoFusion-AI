"""Find which genes of a plant match a protein sequence.

The answer comes from BLAST+ (`blastp`) against the proteins stored for that plant. No AI model is
involved and nothing is guessed: a gene is listed only if BLAST found it. The query can be an NCBI
protein accession (fetched from NCBI), a FASTA record, or a bare protein sequence.
"""

from __future__ import annotations

import re
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import httpx

from .comparison import BlastHit, classify_sequence_relationship, read_fasta_records, run_blastp
from .pipeline import write_fasta

MIN_RESIDUES = 30
MAX_RESIDUES = 5000
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
ACCESSION = re.compile(r"^[A-Za-z]{2,3}_?\d{5,9}(\.\d{1,3})?$")
DNA_LETTERS = set("ACGTUN")

BlastFn = Callable[[Path, Path], list[BlastHit]]
FetchFn = Callable[[str], str]


class QueryError(ValueError):
    """The query is not something we can search with (the message is shown to the person)."""


class FetchError(RuntimeError):
    """NCBI could not be reached or did not return a protein for the accession."""


@dataclass(frozen=True)
class Query:
    kind: str  # "accession", "fasta" or "sequence"
    name: str
    sequence: str


@dataclass(frozen=True)
class GeneHit:
    gene_id: str
    percent_identity: float
    aligned_aa: int
    evalue: float
    bitscore: float
    kind: str  # "same_protein", "related" or "weakly_related"


def clean_sequence(raw: str) -> str:
    seq = re.sub(r"[\s\d]", "", raw).upper().rstrip("*")
    if not seq.isalpha():
        raise QueryError("The sequence has characters that are not amino acid letters.")
    if len(seq) < MIN_RESIDUES:
        raise QueryError(f"The sequence is too short. Use at least {MIN_RESIDUES} amino acids.")
    if len(seq) > MAX_RESIDUES:
        raise QueryError(f"The sequence is too long. Use at most {MAX_RESIDUES} amino acids.")
    if sum(c in DNA_LETTERS for c in seq) / len(seq) >= 0.9:
        raise QueryError(
            "This looks like DNA. Paste a protein sequence, or an NCBI protein accession."
        )
    return seq


def fetch_ncbi_protein(accession: str, client: httpx.Client | None = None) -> str:
    """The FASTA text of one NCBI protein record."""
    params = {"db": "protein", "id": accession, "rettype": "fasta", "retmode": "text"}
    try:
        http = client or httpx.Client(timeout=20.0)
        response = http.get(NCBI_EFETCH, params=params)
    except httpx.HTTPError as exc:
        raise FetchError("NCBI could not be reached. Try again, or paste the sequence.") from exc
    text = response.text.strip()
    if response.status_code != 200 or not text.startswith(">"):
        raise FetchError(f"NCBI has no protein record for “{accession}”. Check the accession.")
    return text


def resolve_query(text: str, fetch: FetchFn = fetch_ncbi_protein) -> Query:
    """Turn what was typed into a protein sequence."""
    text = text.strip()
    if not text:
        raise QueryError("Enter a protein sequence or an NCBI protein accession.")
    if ACCESSION.match(text):
        try:
            records = read_fasta_records(fetch(text).splitlines())
        except ValueError as exc:
            raise FetchError(
                f"NCBI returned a record for “{text}” that could not be read."
            ) from exc
        if not records:
            raise FetchError(f"NCBI returned no sequence for “{text}”.")
        return Query("accession", text, clean_sequence(records[0].sequence))
    if text.startswith(">"):
        try:
            records = read_fasta_records(text.splitlines())
        except ValueError as exc:
            raise QueryError(f"The FASTA text could not be read: {exc}") from exc
        if not records:
            raise QueryError("The FASTA text has no sequence.")
        return Query("fasta", records[0].id, clean_sequence(records[0].sequence))
    return Query("sequence", "pasted sequence", clean_sequence(text))


def _kind(hit: BlastHit, query_length: int) -> str:
    if hit.pident >= 99.5 and hit.length >= 0.95 * query_length:
        return "same_protein"
    return (
        "weakly_related" if classify_sequence_relationship(hit) == "weakly_related" else "related"
    )


def find_genes(
    sequence: str, proteome: dict[str, str], *, blast: BlastFn = run_blastp, top: int = 5
) -> list[GeneHit]:
    """The best-matching genes for `sequence`, best first. `proteome` maps gene id to protein."""
    if not proteome:
        raise ValueError("this plant has no protein sequences")
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        query_fa, subject_fa = folder / "query.fa", folder / "proteins.fa"
        write_fasta(query_fa, {"query": sequence})
        write_fasta(subject_fa, proteome)
        hits = blast(query_fa, subject_fa)
    ranked = sorted(hits, key=lambda h: (-h.bitscore, h.evalue, h.subject))
    seen: set[str] = set()
    out: list[GeneHit] = []
    for h in ranked:
        if h.subject in seen:
            continue
        seen.add(h.subject)
        out.append(
            GeneHit(h.subject, h.pident, h.length, h.evalue, h.bitscore, _kind(h, len(sequence)))
        )
        if len(out) == top:
            break
    return out
