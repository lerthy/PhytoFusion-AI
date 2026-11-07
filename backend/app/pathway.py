"""Pathway graph: gene -> enzyme -> reaction -> compound.

Every edge must carry a source reference and an evidence level (traceability rule).
"""

from __future__ import annotations

from typing import Any

import networkx as nx

from .evidence import LEVELS

NODE_KINDS = ("gene", "enzyme", "reaction", "compound")


class PathwayGraph:
    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()

    def add_node(self, node_id: str, kind: str, label: str | None = None) -> None:
        if kind not in NODE_KINDS:
            raise ValueError(f"unknown node kind {kind!r}; expected one of {NODE_KINDS}")
        self.graph.add_node(node_id, kind=kind, label=label or node_id)

    def add_step(
        self, source: str, target: str, relation: str, evidence_level: str, reference: str
    ) -> None:
        for node in (source, target):
            if node not in self.graph:
                raise KeyError(f"node {node!r} not in graph")
        if evidence_level not in LEVELS:
            raise ValueError(f"invalid evidence level {evidence_level!r}")
        if not (reference or "").strip():
            raise ValueError("every pathway edge needs a PMID/DOI reference")
        self.graph.add_edge(
            source,
            target,
            relation=relation,
            evidence_level=evidence_level,
            reference=reference.strip(),
        )

    def downstream(self, node_id: str) -> set[str]:
        return set(nx.descendants(self.graph, node_id))

    def shared_precursors(self, compound_a: str, compound_b: str) -> set[str]:
        """Compounds that sit upstream of both targets (shared precursor metabolism)."""
        common = nx.ancestors(self.graph, compound_a) & nx.ancestors(self.graph, compound_b)
        return {n for n in common if self.graph.nodes[n]["kind"] == "compound"}

    def to_cytoscape(self) -> list[dict[str, Any]]:
        elements: list[dict[str, Any]] = [
            {"data": {"id": n, **attrs}} for n, attrs in self.graph.nodes(data=True)
        ]
        elements += [
            {"data": {"source": s, "target": t, **attrs}}
            for s, t, attrs in self.graph.edges(data=True)
        ]
        return elements


def validate_elements(raw: Any) -> list[dict[str, Any]]:
    """Validate Cytoscape-style elements before storing them (same rule as the frontend).

    Every edge needs a PMID/DOI reference and a valid evidence level; every node needs an id.
    """
    if not isinstance(raw, list):
        raise ValueError("expected a list of Cytoscape elements")
    for index, element in enumerate(raw):
        data = element.get("data") if isinstance(element, dict) else None
        if not isinstance(data, dict):
            raise ValueError(f"element {index}: missing data")
        if "source" in data:
            reference = data.get("reference")
            if not isinstance(reference, str) or not reference.strip():
                raise ValueError(f"edge {index}: missing PMID/DOI reference")
            if data.get("evidence_level") not in LEVELS:
                raise ValueError(f"edge {index}: evidence_level must be one of {LEVELS}")
        elif not isinstance(data.get("id"), str):
            raise ValueError(f"node {index}: missing id")
    return raw
