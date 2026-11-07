"""Minimal GFF3 parsing for gene features and chromosome lengths."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import unquote

_ID_PREFIXES = ("gene:", "gene-")


@dataclass(frozen=True)
class GeneRecord:
    gene_id: str
    chromosome: str
    start: int
    end: int
    strand: str
    name: str | None = None
    description: str | None = None


def normalize_gene_id(raw: str) -> str:
    """Strip whitespace and common database prefixes. Case is preserved (e.g. SbaiKPS1)."""
    gene_id = (raw or "").strip()
    for prefix in _ID_PREFIXES:
        if gene_id.lower().startswith(prefix):
            gene_id = gene_id[len(prefix) :]
            break
    if not gene_id:
        raise ValueError("empty gene identifier")
    return gene_id


def parse_attributes(attr: str) -> dict[str, str]:
    """Parse the GFF3 column-9 attribute string into a dict."""
    result: dict[str, str] = {}
    for part in attr.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"malformed attribute: {part!r}")
        key, value = part.split("=", 1)
        result[key.strip()] = unquote(value.strip())
    return result


def parse_gff3_genes(lines: Iterable[str]) -> list[GeneRecord]:
    """Return all `gene` features. Raises ValueError (with line number) on malformed input."""
    genes: list[GeneRecord] = []
    for number, line in enumerate(lines, start=1):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) != 9:
            raise ValueError(f"line {number}: expected 9 columns, got {len(cols)}")
        seqid, _source, ftype, start, end, _score, strand, _phase, attrs = cols
        if ftype != "gene":
            continue
        try:
            start_i, end_i = int(start), int(end)
        except ValueError as exc:
            raise ValueError(f"line {number}: non-integer coordinates") from exc
        if start_i < 1 or start_i > end_i:
            raise ValueError(f"line {number}: invalid coordinates {start_i}-{end_i}")
        if strand not in {"+", "-", ".", "?"}:
            raise ValueError(f"line {number}: invalid strand {strand!r}")
        attributes = parse_attributes(attrs)
        if "ID" not in attributes:
            raise ValueError(f"line {number}: gene without ID attribute")
        genes.append(
            GeneRecord(
                gene_id=normalize_gene_id(attributes["ID"]),
                chromosome=seqid,
                start=start_i,
                end=end_i,
                strand=strand,
                name=attributes.get("Name"),
                description=attributes.get("Note") or attributes.get("description"),
            )
        )
    return genes


def parse_chromosome_lengths(lines: Iterable[str]) -> dict[str, int]:
    """Read `##sequence-region <id> <start> <end>` directives."""
    lengths: dict[str, int] = {}
    for line in lines:
        if not line.startswith("##sequence-region"):
            continue
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"malformed sequence-region: {line.strip()!r}")
        lengths[parts[1]] = int(parts[3]) - int(parts[2]) + 1
    return lengths


def parse_sequence_aliases(lines: Iterable[str]) -> dict[str, str]:
    """Friendlier sequence names from ``#OriSeqID=Sbai1<TAB>Accession=GWHAOTO00000001`` comments.

    Returns {accession: original name}. Malformed comments are skipped, never fatal.
    """
    aliases: dict[str, str] = {}
    for line in lines:
        if not line.startswith("#OriSeqID="):
            continue
        parts = line[1:].rstrip("\n").split("\t")
        original = parts[0][len("OriSeqID=") :].strip()
        accession = next(
            (p[len("Accession=") :].strip() for p in parts if p.startswith("Accession=")), ""
        )
        if original and accession:
            aliases[accession] = original
    return aliases
