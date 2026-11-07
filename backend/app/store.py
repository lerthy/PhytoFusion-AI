"""Storage layer: a thin REST client for Supabase (PostgREST + Storage) and an in-memory twin.

Everything above this module talks to the `Store` protocol only, so moving to another Postgres host
later (see docs/STACK.md) means writing one new class here, not touching the engines or routes.
"""

from __future__ import annotations

import math
import os
import re
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

import httpx

Row = dict[str, Any]
PAGE = 1000  # Supabase caps a single response at 1000 rows by default
# Temporary failures worth retrying: rate limit, server errors and Cloudflare timeouts (520-524).
TRANSIENT = {429, 500, 502, 503, 504, 520, 521, 522, 523, 524}


class StoreError(RuntimeError):
    """The database rejected or failed a request."""


class NotConfigured(StoreError):
    """Required environment variables are missing."""


class Store(Protocol):
    def select(
        self,
        table: str,
        *,
        eq: dict[str, Any] | None = None,
        ilike: dict[str, str] | None = None,
        in_: dict[str, list[Any]] | None = None,
        columns: str = "*",
        order: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Row]: ...

    def insert(self, table: str, rows: list[Row]) -> list[Row]: ...

    def upsert(self, table: str, rows: list[Row], on_conflict: str) -> list[Row]: ...

    def rpc(self, fn: str, args: dict[str, Any]) -> list[Row]: ...

    def count(self, table: str) -> int: ...


def load_env_file(path: str | Path) -> None:
    """Load KEY=VALUE lines into os.environ without overriding variables already set."""
    file = Path(path)
    if not file.is_file():
        return
    for raw in file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _filter_value(value: Any) -> str:
    if value is None:
        return "is.null"
    if isinstance(value, bool):
        return f"eq.{str(value).lower()}"
    return f"eq.{value}"


class SupabaseStore:
    def __init__(
        self,
        url: str,
        service_key: str,
        client: httpx.Client | None = None,
        *,
        attempts: int = 4,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.url = url.rstrip("/")
        self.client = client or httpx.Client(timeout=30)
        self.attempts, self._sleep = attempts, sleep
        self._headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        }

    @classmethod
    def from_env(cls) -> SupabaseStore:
        url = os.environ.get("SUPABASE_URL", "").strip()
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        if not url or not key:
            raise NotConfigured("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        return cls(url, key)

    def _send(
        self, method: str, path: str, *, retry: bool = False, **kwargs: Any
    ) -> httpx.Response:
        """One request. With `retry=True`, temporary failures are retried with a growing pause.

        Only pass `retry=True` for requests that are safe to repeat (reads and upserts). A plain
        insert is never retried, because a timeout does not tell us whether the rows were written.
        """
        headers = {**self._headers, **kwargs.pop("headers", {})}
        attempts = self.attempts if retry else 1
        for attempt in range(1, attempts + 1):
            last = attempt == attempts
            try:
                response = self.client.request(
                    method, f"{self.url}{path}", headers=headers, **kwargs
                )
            except httpx.HTTPError as exc:
                if last:
                    raise StoreError(f"request to Supabase failed: {exc}") from exc
            else:
                if response.status_code < 400:
                    return response
                if response.status_code not in TRANSIENT or last:
                    text = re.sub(r"\s+", " ", response.text)[:200]
                    raise StoreError(f"Supabase {response.status_code}: {text}")
            self._sleep(min(2 ** (attempt - 1), 8))
        raise AssertionError("unreachable")  # pragma: no cover

    def select(
        self,
        table: str,
        *,
        eq: dict[str, Any] | None = None,
        ilike: dict[str, str] | None = None,
        in_: dict[str, list[Any]] | None = None,
        columns: str = "*",
        order: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Row]:
        params: list[tuple[str, str]] = [("select", columns)]
        params += [(col, _filter_value(val)) for col, val in (eq or {}).items()]
        params += [(col, f"ilike.*{val}*") for col, val in (ilike or {}).items()]
        params += [
            (col, "in.(" + ",".join(f'"{v}"' for v in vals) + ")")
            for col, vals in (in_ or {}).items()
        ]
        if order:
            params.append(("order", order))
        if limit is not None:
            params.append(("limit", str(limit)))
        if offset:
            params.append(("offset", str(offset)))
        return self._send("GET", f"/rest/v1/{table}", params=params, retry=True).json()

    def insert(self, table: str, rows: list[Row]) -> list[Row]:
        if not rows:
            return []
        out: list[Row] = []
        for i in range(0, len(rows), 500):
            response = self._send(
                "POST",
                f"/rest/v1/{table}",
                json=rows[i : i + 500],
                headers={"Prefer": "return=representation"},
            )
            out += response.json()
        return out

    def upsert(self, table: str, rows: list[Row], on_conflict: str) -> list[Row]:
        if not rows:
            return []
        out: list[Row] = []
        for i in range(0, len(rows), 500):
            response = self._send(
                "POST",
                f"/rest/v1/{table}",
                params={"on_conflict": on_conflict},
                json=rows[i : i + 500],
                headers={"Prefer": "resolution=merge-duplicates,return=representation"},
                retry=True,
            )
            out += response.json()
        return out

    def rpc(self, fn: str, args: dict[str, Any]) -> list[Row]:
        return self._send("POST", f"/rest/v1/rpc/{fn}", json=args).json()

    def count(self, table: str) -> int:
        response = self._send(
            "GET",
            f"/rest/v1/{table}",
            params={"select": "*"},
            headers={"Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"},
            retry=True,
        )
        total = response.headers.get("content-range", "*/0").rsplit("/", 1)[-1]
        return int(total) if total.isdigit() else 0

    def upload_file(self, bucket: str, path: str, data: bytes, content_type: str) -> None:
        self._send(
            "POST",
            f"/storage/v1/object/{bucket}/{path}",
            content=data,
            headers={"Content-Type": content_type, "x-upsert": "true"},
            retry=True,
        )


class InMemoryStore:
    """Dictionary-backed Store used by tests and offline development."""

    def __init__(
        self, rpc_handlers: dict[str, Callable[[dict[str, Any]], list[Row]]] | None = None
    ):
        self.tables: dict[str, list[Row]] = {}
        self.rpc_handlers = rpc_handlers or {"match_literature": self._match_literature}

    def _rows(self, table: str) -> list[Row]:
        return self.tables.setdefault(table, [])

    def select(
        self,
        table: str,
        *,
        eq: dict[str, Any] | None = None,
        ilike: dict[str, str] | None = None,
        in_: dict[str, list[Any]] | None = None,
        columns: str = "*",
        order: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Row]:
        rows = [
            r
            for r in self._rows(table)
            if all(r.get(c) == v for c, v in (eq or {}).items())
            and all(v.lower() in str(r.get(c, "")).lower() for c, v in (ilike or {}).items())
            and all(r.get(c) in vals for c, vals in (in_ or {}).items())
        ]
        if order:
            column, _, direction = order.partition(".")
            rows.sort(
                key=lambda r: (r.get(column) is None, r.get(column)), reverse=direction == "desc"
            )
        end = None if limit is None else offset + limit
        rows = rows[offset:end]
        if columns != "*":
            wanted = [c.strip() for c in columns.split(",")]
            rows = [{c: r.get(c) for c in wanted} for r in rows]
        return [dict(r) for r in rows]

    def insert(self, table: str, rows: list[Row]) -> list[Row]:
        stored = []
        for row in rows:
            new = {"id": str(uuid.uuid4()), **row}
            self._rows(table).append(new)
            stored.append(dict(new))
        return stored

    def upsert(self, table: str, rows: list[Row], on_conflict: str) -> list[Row]:
        keys = [k.strip() for k in on_conflict.split(",")]
        # Index existing rows once per call, so a large batch is linear rather than quadratic.
        index = {tuple(r.get(k) for k in keys): r for r in self._rows(table)}
        out = []
        for row in rows:
            key = tuple(row.get(k) for k in keys)
            existing = index.get(key)
            if existing is None:
                stored = self.insert(table, [row])[0]
                index[key] = self._rows(table)[-1]
                out.append(stored)
            else:
                existing.update(row)
                out.append(dict(existing))
        return out

    def rpc(self, fn: str, args: dict[str, Any]) -> list[Row]:
        if fn not in self.rpc_handlers:
            raise StoreError(f"unknown rpc {fn!r}")
        return self.rpc_handlers[fn](args)

    def count(self, table: str) -> int:
        return len(self._rows(table))

    def _match_literature(self, args: dict[str, Any]) -> list[Row]:
        query = args["query_embedding"]

        def cosine(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b, strict=True))
            norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
            return dot / norm if norm else 0.0

        scored = [
            {
                "id": r["id"],
                "evidence_id": r["evidence_id"],
                "content": r["content"],
                "similarity": cosine(query, r["embedding"]),
            }
            for r in self._rows("literature_chunks")
        ]
        scored.sort(key=lambda r: r["similarity"], reverse=True)
        return scored[: args.get("match_count", 5)]
