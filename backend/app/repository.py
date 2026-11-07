"""Persistence for PhytoFusion AI: one place that knows the table layout."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from typing import Any

from .crispr import ScenarioResult, render_report_markdown
from .evidence import LEVELS
from .genebridge import Assessment, AssessmentInput
from .ingestion.gff3 import GeneRecord
from .literature import Embedder, chunk_text
from .pathway import validate_elements
from .store import PAGE, Row, Store

STAT_TABLES = (
    "species",
    "genome_assemblies",
    "chromosomes",
    "genes",
    "evidence",
    "literature_chunks",
    "gene_comparisons",
    "pathways",
    "crispr_scenarios",
)


class Repository:
    def __init__(self, store: Store) -> None:
        self.store = store

    # ---- helpers -------------------------------------------------------------------------
    def _all(self, table: str, **kwargs: Any) -> list[Row]:
        rows: list[Row] = []
        offset = 0
        while True:
            page = self.store.select(table, limit=PAGE, offset=offset, **kwargs)
            rows += page
            if len(page) < PAGE:
                return rows
            offset += PAGE

    def species_id(self, name: str) -> str:
        rows = self.store.select("species", eq={"scientific_name": name}, limit=1)
        if not rows:
            raise LookupError(f"species {name!r} is not in the database; ingest its genome first")
        return rows[0]["id"]

    def find_gene(self, gene_id: str, species_id: str) -> Row:
        assemblies = self.store.select("genome_assemblies", eq={"species_id": species_id})
        genes = self.store.select(
            "genes",
            eq={"gene_id": gene_id},
            in_={"assembly_id": [a["id"] for a in assemblies]},
            limit=1,
        )
        if not genes:
            raise LookupError(f"gene {gene_id!r} was not found for this species; ingest it first")
        return genes[0]

    def gene_lookup(self, species_name: str, gene_id: str) -> dict[str, Any]:
        """Where a gene sits: its sequence, position, strand and the sequence's length."""
        gene = self.find_gene(gene_id, self.species_id(species_name))
        chromosome = self.store.select("chromosomes", eq={"id": gene["chromosome_id"]}, limit=1)
        chrom = chromosome[0] if chromosome else {}
        return {
            "gene_id": gene["gene_id"],
            "chromosome": chrom.get("name"),
            "chromosome_length": chrom.get("length_bp"),
            "start_bp": gene["start_bp"],
            "end_bp": gene["end_bp"],
            "strand": gene["strand"],
            "annotation": gene.get("annotation"),
            "family": gene.get("family"),
        }

    def stats(self) -> dict[str, int]:
        return {t: self.store.count(t) for t in STAT_TABLES}

    # ---- genomes -------------------------------------------------------------------------
    def upsert_species(
        self,
        scientific_name: str,
        role: str,
        common_name: str | None = None,
        notes: str | None = None,
    ) -> Row:
        if role not in ("host", "donor"):
            raise ValueError("role must be 'host' or 'donor'")
        row = {
            "scientific_name": scientific_name,
            "role": role,
            "common_name": common_name,
            "notes": notes,
        }
        return self.store.upsert("species", [row], "scientific_name")[0]

    def upsert_assembly(
        self,
        species_id: str,
        accession: str,
        source: str,
        chromosome_count: int | None = None,
        storage_path: str | None = None,
        source_url: str | None = None,
    ) -> Row:
        row = {
            "species_id": species_id,
            "accession": accession,
            "source": source,
            "chromosome_count": chromosome_count,
            "storage_path": storage_path,
            "source_url": source_url,
        }
        return self.store.upsert("genome_assemblies", [row], "accession")[0]

    def upsert_chromosomes(
        self, assembly_id: str, lengths: dict[str, int], names: dict[str, str] | None = None
    ) -> dict[str, str]:
        """Store sequences. `names` maps the file's sequence id to a display name; the id itself is
        kept as `accession`. Returns {sequence id: row id}, whatever the display names are."""
        names = names or {}
        rows = [
            {
                "assembly_id": assembly_id,
                "name": names.get(seq, seq),
                "accession": seq,
                "length_bp": size,
            }
            for seq, size in lengths.items()
        ]
        stored = self.store.upsert("chromosomes", rows, "assembly_id,name")
        return {r["accession"]: r["id"] for r in stored}

    def upsert_genes(
        self,
        assembly_id: str,
        genes: Iterable[GeneRecord],
        chromosome_ids: dict[str, str],
        proteins: dict[str, str] | None = None,
        families: dict[str, str] | None = None,
    ) -> int:
        proteins, families = proteins or {}, families or {}
        rows = [
            {
                "assembly_id": assembly_id,
                "chromosome_id": chromosome_ids.get(g.chromosome),
                "gene_id": g.gene_id,
                "family": families.get(g.gene_id),
                "start_bp": g.start,
                "end_bp": g.end,
                "strand": g.strand,
                "annotation": g.description or g.name,
                "protein_sequence": proteins.get(g.gene_id),
            }
            for g in genes
        ]
        return len(self.store.upsert("genes", rows, "assembly_id,gene_id"))

    def list_species(self) -> list[Row]:
        return self.store.select("species", order="scientific_name")

    def genome(self, species_id: str) -> dict[str, Any]:
        species = self.store.select("species", eq={"id": species_id}, limit=1)
        if not species:
            raise LookupError("species not found")
        accessions, chromosomes, genes = [], [], []
        for assembly in self.store.select("genome_assemblies", eq={"species_id": species_id}):
            accessions.append(assembly["accession"])
            chroms = self._all("chromosomes", eq={"assembly_id": assembly["id"]})
            names = {c["id"]: c["name"] for c in chroms}
            chromosomes += [
                {"name": c["name"], "accession": c.get("accession"), "length_bp": c["length_bp"]}
                for c in chroms
            ]
            for g in self._all(
                "genes",
                eq={"assembly_id": assembly["id"]},
                columns="gene_id,chromosome_id,family,start_bp,end_bp,strand,annotation",
            ):
                genes.append(
                    {
                        "gene_id": g["gene_id"],
                        "chromosome": names.get(g["chromosome_id"]),
                        "family": g["family"],
                        "start_bp": g["start_bp"],
                        "end_bp": g["end_bp"],
                        "strand": g["strand"],
                        "annotation": g["annotation"],
                    }
                )
        return {
            "species": species[0],
            "accessions": accessions,
            "chromosomes": chromosomes,
            "genes": genes,
        }

    def proteins(self, species_id: str) -> dict[str, str]:
        """gene_id -> protein sequence for every gene of the species that has one."""
        out: dict[str, str] = {}
        for assembly in self.store.select("genome_assemblies", eq={"species_id": species_id}):
            for g in self._all(
                "genes", eq={"assembly_id": assembly["id"]}, columns="gene_id,protein_sequence"
            ):
                if g["protein_sequence"]:
                    out[g["gene_id"]] = g["protein_sequence"]
        return out

    # ---- evidence and literature -----------------------------------------------------------
    def add_evidence(
        self,
        finding: str,
        level: str,
        pmid: str | None = None,
        doi: str | None = None,
        title: str | None = None,
    ) -> Row:
        pmid, doi = (pmid or "").strip() or None, (doi or "").strip() or None
        if not pmid and not doi:
            raise ValueError("evidence needs a PMID or a DOI")
        if level not in LEVELS:
            raise ValueError(f"level must be one of {LEVELS}")
        if not finding.strip():
            raise ValueError("finding text is required")
        for column, value in (("pmid", pmid), ("doi", doi)):
            if value:
                existing = self.store.select("evidence", eq={column: value}, limit=1)
                if existing:
                    return existing[0]
        row = {"pmid": pmid, "doi": doi, "title": title, "finding": finding.strip(), "level": level}
        return self.store.insert("evidence", [row])[0]

    def list_evidence(self, limit: int = 200) -> list[Row]:
        return self.store.select("evidence", order="title", limit=limit)

    def add_literature(self, evidence_id: str, text: str, embedder: Embedder) -> int:
        if not self.store.select("evidence", eq={"id": evidence_id}, limit=1):
            raise LookupError("evidence row not found; add the PMID/DOI first")
        chunks = chunk_text(text)
        vectors = embedder.embed(chunks)
        rows = [
            {"evidence_id": evidence_id, "content": c, "embedding": v}
            for c, v in zip(chunks, vectors, strict=True)
        ]
        return len(self.store.insert("literature_chunks", rows))

    def search_literature(self, query: str, embedder: Embedder, k: int = 5) -> list[dict[str, Any]]:
        vector = embedder.embed([query])[0]
        hits = self.store.rpc("match_literature", {"query_embedding": vector, "match_count": k})
        results = []
        for hit in hits:
            source = self.store.select("evidence", eq={"id": hit["evidence_id"]}, limit=1)
            ev = source[0] if source else {}
            results.append(
                {
                    "content": hit["content"],
                    "similarity": hit["similarity"],
                    "pmid": ev.get("pmid"),
                    "doi": ev.get("doi"),
                    "title": ev.get("title"),
                }
            )
        return results

    # ---- comparisons -----------------------------------------------------------------------
    def save_comparison(
        self,
        host_gene_row: str,
        donor_gene_row: str,
        data: AssessmentInput,
        result: Assessment,
        percent_identity: float | None = None,
    ) -> Row:
        row = {
            "host_gene_id": host_gene_row,
            "donor_gene_id": donor_gene_row,
            "sequence_relationship": data.sequence,
            "percent_identity": percent_identity,
            "functional_evidence": data.functional,
            "pathway_completeness": data.pathway,
            "expression_compatibility": data.expression,
            "genomic_context": data.context,
            "overall_level": result.level,
            "explanation": result.explanation,
        }
        return self.store.upsert("gene_comparisons", [row], "host_gene_id,donor_gene_id")[0]

    def list_comparisons(self) -> list[dict[str, Any]]:
        rows = self._all("gene_comparisons")
        ids = list({r[k] for r in rows for k in ("host_gene_id", "donor_gene_id")})
        names = {
            g["id"]: g["gene_id"]
            for g in self.store.select("genes", in_={"id": ids}, columns="id,gene_id")
        }
        return [
            {
                **r,
                "host_gene": names.get(r["host_gene_id"]),
                "donor_gene": names.get(r["donor_gene_id"]),
            }
            for r in rows
        ]

    # ---- pathways --------------------------------------------------------------------------
    def save_pathway(self, name: str, elements: Any, description: str | None = None) -> Row:
        if not name.strip():
            raise ValueError("pathway name is required")
        graph = validate_elements(elements)
        row = {"name": name.strip(), "description": description, "graph": graph}
        return self.store.upsert("pathways", [row], "name")[0]

    def list_pathways(self) -> list[Row]:
        return self.store.select("pathways", columns="id,name,description", order="name")

    def get_pathway(self, pathway_id: str) -> Row:
        rows = self.store.select("pathways", eq={"id": pathway_id}, limit=1)
        if not rows:
            raise LookupError("pathway not found")
        return rows[0]

    # ---- scenarios -------------------------------------------------------------------------
    def save_scenario(self, result: ScenarioResult, assessment: dict[str, str] | None = None) -> Row:
        host_id = self.species_id(result.host_species)
        if result.type == "donor_integration":
            if not result.donor_species:
                raise ValueError("donor_integration requires donor_species")
            gene = self.find_gene(result.target_gene_id, self.species_id(result.donor_species))
            donor_id: str | None = self.species_id(result.donor_species)
        else:
            gene = self.find_gene(result.target_gene_id, host_id)
            donor_id = None
        scenario = self.store.insert(
            "crispr_scenarios",
            [
                {
                    "type": result.type,
                    "host_species_id": host_id,
                    "donor_species_id": donor_id,
                    "target_gene_id": gene["id"],
                    "description": result.scenario,
                }
            ],
        )[0]
        report = render_report_markdown(result)
        self.store.insert(
            "scenario_results",
            [
                {
                    "scenario_id": scenario["id"],
                    "predicted_consequences": "\n".join(result.predicted_consequences),
                    "compatibility_issues": "\n".join(result.compatibility_issues),
                    "missing_pathway_components": "\n".join(result.missing_information),
                    "limitations": "\n".join(result.limitations),
                    "evidence_level": result.evidence_level,
                    "report_markdown": report,
                    "result": {**asdict(result), "assessment": assessment},
                }
            ],
        )
        return scenario

    def get_scenario(self, scenario_id: str) -> dict[str, Any]:
        rows = self.store.select("scenario_results", eq={"scenario_id": scenario_id}, limit=1)
        if not rows:
            raise LookupError("scenario not found")
        return {
            **rows[0]["result"],
            "report_markdown": rows[0]["report_markdown"],
            "id": scenario_id,
        }

    def list_scenarios(self) -> list[dict[str, Any]]:
        results = self._all("scenario_results", order="created_at.desc")
        return [
            {
                "id": r["scenario_id"],
                "created_at": r.get("created_at"),
                "type": r["result"]["type"],
                "target_gene_id": r["result"]["target_gene_id"],
                "scenario": r["result"]["scenario"],
                "evidence_level": r["evidence_level"],
            }
            for r in results
        ]
