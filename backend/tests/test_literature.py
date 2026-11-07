import httpx
import pytest

from app.literature import EMBEDDING_DIM, HttpEmbedder, chunk_text, embedder_from_env
from app.store import NotConfigured, StoreError


def test_chunk_text_respects_size_and_overlaps():
    text = " ".join(f"w{i}" for i in range(400))
    chunks = chunk_text(text, max_chars=200, overlap=40)
    assert len(chunks) > 3 and all(len(c) <= 200 for c in chunks)
    assert chunks[0].split()[-1] in chunks[1].split()  # overlap carries words forward
    assert set(" ".join(chunks).split()) == set(text.split())


def test_chunk_text_edge_cases():
    assert chunk_text("") == [] and chunk_text("short text") == ["short text"]
    with pytest.raises(ValueError):
        chunk_text("x", max_chars=10, overlap=10)


def embedder(handler, dims=3):
    return HttpEmbedder(
        "https://e/api", "k", "m", httpx.Client(transport=httpx.MockTransport(handler)), dims
    )


def test_embed_orders_by_index_and_sends_model():
    def handler(request):
        import json

        body = json.loads(request.content)
        assert body == {"model": "m", "input": ["a", "b"]}
        return httpx.Response(
            200,
            json={
                "data": [{"index": 1, "embedding": [0, 1, 0]}, {"index": 0, "embedding": [1, 0, 0]}]
            },
        )

    assert embedder(handler).embed(["a", "b"]) == [[1, 0, 0], [0, 1, 0]]


def test_embed_empty_makes_no_request():
    def handler(request):
        raise AssertionError("no request expected")

    assert embedder(handler).embed([]) == []


def test_embed_rejects_wrong_dimension_count_and_http_errors():
    ok = lambda r: httpx.Response(200, json={"data": [{"index": 0, "embedding": [1, 2]}]})  # noqa: E731
    with pytest.raises(StoreError, match="dimensions"):
        embedder(ok).embed(["a"])
    short = lambda r: httpx.Response(200, json={"data": []})  # noqa: E731
    with pytest.raises(StoreError, match="wrong number"):
        embedder(short).embed(["a"])
    with pytest.raises(StoreError, match="401"):
        embedder(lambda r: httpx.Response(401, text="no")).embed(["a"])


def test_embed_network_failure():
    def handler(request):
        raise httpx.ConnectError("down")

    with pytest.raises(StoreError):
        embedder(handler).embed(["a"])


def test_embedder_from_env(monkeypatch):
    for k in ("EMBEDDING_API_URL", "EMBEDDING_API_KEY", "EMBEDDING_MODEL"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(NotConfigured):
        embedder_from_env()
    monkeypatch.setenv("EMBEDDING_API_URL", "https://e")
    monkeypatch.setenv("EMBEDDING_API_KEY", "k")
    monkeypatch.setenv("EMBEDDING_MODEL", "m")
    assert embedder_from_env().dimensions == EMBEDDING_DIM
