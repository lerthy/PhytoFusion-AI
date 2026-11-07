import pytest

from app.pathway import PathwayGraph


@pytest.fixture
def graph():
    g = PathwayGraph()
    g.add_node("GGPP", "compound")
    g.add_node("SbarKPS1", "gene")
    g.add_node("clerodane", "compound")
    g.add_node("SbaiCHS1", "gene")
    g.add_node("baicalein", "compound")
    g.add_node("precursor", "compound")
    g.add_step("precursor", "GGPP", "converted_to", "moderate", "PMID:1")
    g.add_step("precursor", "baicalein", "converted_to", "moderate", "PMID:2")
    g.add_step("GGPP", "clerodane", "converted_to", "strong", "PMID:3")
    return g


def test_unknown_node_kind_rejected():
    with pytest.raises(ValueError):
        PathwayGraph().add_node("x", "protein-ish")


def test_label_defaults_to_id():
    g = PathwayGraph()
    g.add_node("x", "gene")
    assert g.graph.nodes["x"]["label"] == "x"


def test_edge_requires_existing_nodes():
    g = PathwayGraph()
    g.add_node("a", "gene")
    with pytest.raises(KeyError):
        g.add_step("a", "missing", "r", "strong", "PMID:1")


@pytest.mark.parametrize("ref", ["", "   "])
def test_edge_requires_reference(ref):
    g = PathwayGraph()
    g.add_node("a", "gene")
    g.add_node("b", "compound")
    with pytest.raises(ValueError, match="reference"):
        g.add_step("a", "b", "r", "strong", ref)


def test_edge_requires_valid_evidence_level():
    g = PathwayGraph()
    g.add_node("a", "gene")
    g.add_node("b", "compound")
    with pytest.raises(ValueError, match="evidence level"):
        g.add_step("a", "b", "r", "certain", "PMID:1")


def test_downstream(graph):
    assert graph.downstream("precursor") == {"GGPP", "clerodane", "baicalein"}


def test_shared_precursors(graph):
    assert graph.shared_precursors("clerodane", "baicalein") == {"precursor"}


def test_shared_precursors_excludes_non_compounds(graph):
    graph.add_step("SbarKPS1", "GGPP", "catalyses", "strong", "PMID:4")
    assert "SbarKPS1" not in graph.shared_precursors("clerodane", "baicalein")


def test_cytoscape_export_carries_evidence(graph):
    elements = graph.to_cytoscape()
    edges = [e["data"] for e in elements if "source" in e["data"]]
    nodes = [e["data"] for e in elements if "source" not in e["data"]]
    assert len(nodes) == 6
    assert len(edges) == 3
    assert all(e["reference"] and e["evidence_level"] for e in edges)


def test_validate_elements_python_mirror():
    from app.pathway import validate_elements

    node = {"data": {"id": "a"}}
    edge = {
        "data": {"source": "a", "target": "b", "reference": "PMID:1", "evidence_level": "strong"}
    }
    assert validate_elements([node, edge]) == [node, edge]
    bad = [
        ({}, "list"),
        ([{}], "missing data"),
        ([{"data": {}}], "missing id"),
        ([{"data": {"source": "a", "reference": "  ", "evidence_level": "strong"}}], "reference"),
        (
            [{"data": {"source": "a", "reference": "PMID:1", "evidence_level": "certain"}}],
            "evidence_level",
        ),
    ]
    for raw, message in bad:
        with pytest.raises(ValueError, match=message):
            validate_elements(raw)
