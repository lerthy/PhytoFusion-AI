"""Literature intelligence (RAG, retrieval only).

This module retrieves and cites; it never generates text. A retrieved passage always travels with
its PMID/DOI, so a gene function can only be stated if a source says it.
"""

from __future__ import annotations

import os
from typing import Protocol

import httpx

from .store import NotConfigured, StoreError

EMBEDDING_DIM = 1536  # must match vector(1536) in the schema


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks, preferring to break at whitespace."""
    if max_chars <= overlap:
        raise ValueError("max_chars must be greater than overlap")
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    length = 0
    for word in words:
        if current and length + len(word) + 1 > max_chars:
            chunks.append(" ".join(current))
            tail: list[str] = []
            size = 0
            for w in reversed(current):
                if size + len(w) + 1 > overlap:
                    break
                tail.insert(0, w)
                size += len(w) + 1
            current, length = tail, size
        current.append(word)
        length += len(word) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks


class HttpEmbedder:
    """Client for an OpenAI-compatible `/embeddings` endpoint."""

    def __init__(
        self,
        url: str,
        api_key: str,
        model: str,
        client: httpx.Client | None = None,
        dimensions: int = EMBEDDING_DIM,
    ) -> None:
        self.url, self.api_key, self.model = url, api_key, model
        self.client = client or httpx.Client(timeout=60)
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self.client.post(
                self.url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": texts},
            )
        except httpx.HTTPError as exc:
            raise StoreError(f"embedding request failed: {exc}") from exc
        if response.status_code >= 400:
            raise StoreError(f"embedding API {response.status_code}: {response.text[:200]}")
        data = sorted(response.json()["data"], key=lambda d: d["index"])
        vectors = [d["embedding"] for d in data]
        if len(vectors) != len(texts):
            raise StoreError("embedding API returned the wrong number of vectors")
        for vector in vectors:
            if len(vector) != self.dimensions:
                raise StoreError(
                    f"embedding has {len(vector)} dimensions but the database expects "
                    f"{self.dimensions}; change the model or the vector(...) column"
                )
        return vectors


def embedder_from_env() -> HttpEmbedder:
    url = os.environ.get("EMBEDDING_API_URL", "").strip()
    key = os.environ.get("EMBEDDING_API_KEY", "").strip()
    model = os.environ.get("EMBEDDING_MODEL", "").strip()
    if not (url and key and model):
        raise NotConfigured("EMBEDDING_API_URL, EMBEDDING_API_KEY and EMBEDDING_MODEL must be set")
    return HttpEmbedder(url, key, model)
