"""Seed a genome into the database.

    python -m app.ingestion.seed --species "Scutellaria baicalensis" --role host \
        --accession GWHAOTO00000000 --source "Genome Warehouse" \
        --gff host.gff3 [--proteins host.faa]

Without --apply this only prints what would be written (dry run). Re-running with --apply is
safe: all writes are upserts keyed on stable identifiers.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from ..comparison import FastaRecord, read_fasta_records
from ..repository import Repository
from ..store import SupabaseStore, load_env_file
from .gff3 import (
    GeneRecord,
    parse_chromosome_lengths,
    parse_gff3_genes,
    parse_sequence_aliases,
)

ISOFORM_SUFFIX = re.compile(r"\.(t)?\d+$")
ORI_GENE = re.compile(r"OriGeneID=(\S+)")  # Genome Warehouse protein headers name the gene this way


@dataclass
class SeedPlan:
    species: str
    role: str
    accession: str
    source: str
    source_url: str | None
    genes: list[GeneRecord]
    lengths: dict[str, int]
    proteins: dict[str, str]
    families: dict[str, str]
    unmatched_proteins: int
    names: dict[str, str] = field(default_factory=dict)  # sequence id -> display name

    def summary(self) -> str:
        return (
            f"{self.species} ({self.role}), assembly {self.accession}: "
            f"{len(self.genes)} genes, {len(self.lengths)} chromosomes, "
            f"{len(self.proteins)} proteins matched ({self.unmatched_proteins} protein records "
            f"matched no gene), {len(self.families)} family labels, "
            f"{len(self.names)} sequences with friendlier names"
        )


def match_proteins(
    gene_ids: set[str], records: dict[str, str], strip_isoform: bool = False
) -> tuple[dict[str, str], int]:
    """Map protein records to gene ids. Exact id match; optionally strip isoform suffixes and keep
    the longest isoform. Returns (gene_id -> sequence, number of unmatched records)."""
    matched: dict[str, str] = {}
    unmatched = 0
    for name, seq in records.items():
        gene = name if name in gene_ids else None
        if gene is None and strip_isoform:
            base = ISOFORM_SUFFIX.sub("", name)
            gene = base if base in gene_ids else None
        if gene is None:
            unmatched += 1
        elif len(seq) > len(matched.get(gene, "")):
            matched[gene] = seq
    return matched, unmatched


def match_protein_records(
    gene_ids: set[str], records: list[FastaRecord], strip_isoform: bool = False
) -> tuple[dict[str, str], int]:
    """Attach each protein to a gene. A record is tried by its OriGeneID= note (Genome Warehouse
    files), then its own id, then optionally its id without an isoform suffix. The longest protein
    per gene is kept. Returns (gene_id -> sequence, number of records that matched no gene)."""
    matched: dict[str, str] = {}
    unmatched = 0
    for record in records:
        candidates = []
        note = ORI_GENE.search(record.description)
        if note:
            candidates.append(note.group(1))
        candidates.append(record.id)
        if strip_isoform:
            candidates.append(ISOFORM_SUFFIX.sub("", record.id))
        gene = next((c for c in candidates if c in gene_ids), None)
        if gene is None:
            unmatched += 1
        elif len(record.sequence) > len(matched.get(gene, "")):
            matched[gene] = record.sequence
    return matched, unmatched


def read_families(path: Path) -> dict[str, str]:
    """CSV with columns gene_id,family (supplied by the science team, never inferred)."""
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not {"gene_id", "family"} <= set(reader.fieldnames):
            raise ValueError("families CSV needs the columns gene_id,family")
        return {
            row["gene_id"].strip(): row["family"].strip()
            for row in reader
            if row["gene_id"].strip()
        }


def usable_names(sequences: Iterable[str], aliases: dict[str, str]) -> dict[str, str]:
    """Display names for sequences, keeping the sequence id wherever an alias would collide.

    Names must be unique within an assembly. If two sequences would share a name, or an alias equals
    another sequence's id, neither uses it, so nothing is silently merged.
    """
    ids = list(sequences)
    wanted = {seq: aliases[seq] for seq in ids if seq in aliases and aliases[seq] != seq}
    taken = Counter([*wanted.values(), *(s for s in ids if s not in wanted)])
    return {seq: name for seq, name in wanted.items() if taken[name] == 1}


def build_plan(
    species: str,
    role: str,
    accession: str,
    source: str,
    gff: Path,
    proteins: Path | None = None,
    families: Path | None = None,
    source_url: str | None = None,
    strip_isoform: bool = False,
) -> SeedPlan:
    lines = gff.read_text().splitlines()
    genes = parse_gff3_genes(lines)
    if not genes:
        raise ValueError(f"{gff} contains no gene features")
    lengths = parse_chromosome_lengths(lines)
    for gene in genes:  # fall back to the furthest gene end when no directive exists
        lengths[gene.chromosome] = max(lengths.get(gene.chromosome, 0), gene.end)
    names = usable_names(lengths, parse_sequence_aliases(lines))
    matched, unmatched = {}, 0
    if proteins:
        matched, unmatched = match_protein_records(
            {g.gene_id for g in genes},
            read_fasta_records(proteins.read_text().splitlines()),
            strip_isoform,
        )
    fam = read_families(families) if families else {}
    return SeedPlan(
        species, role, accession, source, source_url, genes, lengths, matched, fam, unmatched, names
    )


def apply_plan(repo: Repository, plan: SeedPlan) -> dict[str, int]:
    species = repo.upsert_species(plan.species, plan.role)
    assembly = repo.upsert_assembly(
        species["id"], plan.accession, plan.source, len(plan.lengths), source_url=plan.source_url
    )
    chromosome_ids = repo.upsert_chromosomes(assembly["id"], plan.lengths, plan.names)
    written = repo.upsert_genes(
        assembly["id"], plan.genes, chromosome_ids, plan.proteins, plan.families
    )
    return {"chromosomes": len(chromosome_ids), "genes": written}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--species", required=True)
    ap.add_argument("--role", required=True, choices=["host", "donor"])
    ap.add_argument("--accession", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--source-url")
    ap.add_argument("--gff", required=True, type=Path)
    ap.add_argument("--proteins", type=Path)
    ap.add_argument("--families", type=Path, help="CSV gene_id,family")
    ap.add_argument(
        "--strip-isoform", action="store_true", help="match protein ids like G1.t1 to G1"
    )
    ap.add_argument("--env-file", default="../.env")
    ap.add_argument("--apply", action="store_true", help="write to the database (default: dry run)")
    args = ap.parse_args(argv)

    plan = build_plan(
        args.species,
        args.role,
        args.accession,
        args.source,
        args.gff,
        args.proteins,
        args.families,
        args.source_url,
        args.strip_isoform,
    )
    print(plan.summary())
    if not args.apply:
        print("Dry run. Nothing was written. Re-run with --apply to write to the database.")
        return 0
    load_env_file(args.env_file)
    counts = apply_plan(Repository(SupabaseStore.from_env()), plan)
    print(f"Wrote {counts['genes']} genes and {counts['chromosomes']} chromosomes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
