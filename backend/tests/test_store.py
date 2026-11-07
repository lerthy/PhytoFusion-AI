import json

import httpx
import pytest

from app.store import InMemoryStore, NotConfigured, StoreError, SupabaseStore, load_env_file


def make(handler):
    return SupabaseStore(
        "https://x.supabase.co/",
        "KEY",
        httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _seconds: None,  # never really wait in tests
    )


def test_from_env_requires_both_variables(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "k")
    with pytest.raises(NotConfigured):
        SupabaseStore.from_env()
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    assert SupabaseStore.from_env().url == "https://x.supabase.co"


def test_select_builds_postgrest_query_and_auth_headers():
    seen = {}

    def handler(request):
        seen["url"], seen["headers"] = request.url, request.headers
        return httpx.Response(200, json=[{"id": "1"}])

    rows = make(handler).select(
        "genes",
        eq={"gene_id": "KPS1", "flag": True, "x": None},
        ilike={"annotation": "syn"},
        in_={"assembly_id": ["a", "b"]},
        columns="id",
        order="gene_id.desc",
        limit=5,
        offset=10,
    )
    assert rows == [{"id": "1"}]
    q = dict(seen["url"].params)
    assert seen["url"].path == "/rest/v1/genes"
    assert q["gene_id"] == "eq.KPS1" and q["flag"] == "eq.true" and q["x"] == "is.null"
    assert q["annotation"] == "ilike.*syn*" and q["assembly_id"] == 'in.("a","b")'
    assert q["order"] == "gene_id.desc" and q["limit"] == "5" and q["offset"] == "10"
    assert seen["headers"]["apikey"] == "KEY" and seen["headers"]["authorization"] == "Bearer KEY"


def test_upsert_sends_on_conflict_and_merge_preference():
    seen = {}

    def handler(request):
        seen["params"], seen["prefer"] = dict(request.url.params), request.headers["prefer"]
        return httpx.Response(201, json=json.loads(request.content))

    out = make(handler).upsert("species", [{"scientific_name": "A"}], "scientific_name")
    assert out == [{"scientific_name": "A"}]
    assert seen["params"]["on_conflict"] == "scientific_name"
    assert "merge-duplicates" in seen["prefer"]


def test_insert_and_upsert_are_chunked_and_empty_is_a_noop():
    calls = []

    def handler(request):
        body = json.loads(request.content)
        calls.append(len(body))
        return httpx.Response(201, json=body)

    store = make(handler)
    assert store.insert("t", []) == [] and store.upsert("t", [], "id") == []
    assert len(store.insert("t", [{"n": i} for i in range(1200)])) == 1200
    assert calls == [500, 500, 200]


def test_count_reads_content_range():
    def handler(request):
        assert request.headers["prefer"] == "count=exact"
        return httpx.Response(206, json=[], headers={"content-range": "0-0/42"})

    assert make(handler).count("genes") == 42


def test_count_defaults_to_zero_without_header():
    assert make(lambda r: httpx.Response(200, json=[])).count("genes") == 0


def test_rpc_posts_arguments():
    def handler(request):
        assert request.url.path == "/rest/v1/rpc/match_literature"
        assert json.loads(request.content) == {"match_count": 2}
        return httpx.Response(200, json=[{"content": "c"}])

    assert make(handler).rpc("match_literature", {"match_count": 2}) == [{"content": "c"}]


def test_http_errors_become_store_errors():
    with pytest.raises(StoreError, match="400"):
        make(lambda r: httpx.Response(400, text="bad column")).select("genes")


def test_network_failures_become_store_errors():
    def handler(request):
        raise httpx.ConnectError("down")

    with pytest.raises(StoreError, match="failed"):
        make(handler).select("genes")


def test_upload_file_sets_upsert_header():
    seen = {}

    def handler(request):
        seen["path"], seen["upsert"] = request.url.path, request.headers["x-upsert"]
        return httpx.Response(200, json={})

    make(handler).upload_file("genomes", "a/b.gff3", b"data", "text/plain")
    assert seen == {"path": "/storage/v1/object/genomes/a/b.gff3", "upsert": "true"}


def test_load_env_file_does_not_override(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('# c\nA_NEW="one"\nA_SET=file\nbroken\n')
    monkeypatch.setenv("A_SET", "shell")
    monkeypatch.delenv("A_NEW", raising=False)
    load_env_file(env)
    load_env_file(tmp_path / "missing")
    import os

    assert os.environ["A_NEW"] == "one" and os.environ["A_SET"] == "shell"


def test_in_memory_store_basics():
    s = InMemoryStore()
    s.insert("t", [{"a": 1, "name": "Alpha"}, {"a": 2, "name": "beta"}, {"a": 3, "name": "ALPHA2"}])
    assert [r["a"] for r in s.select("t", ilike={"name": "alpha"})] == [1, 3]
    assert [r["a"] for r in s.select("t", in_={"a": [2, 3]}, order="a.desc")] == [3, 2]
    assert s.select("t", columns="a", limit=1, offset=1) == [{"a": 2}]
    s.upsert("t", [{"a": 1, "name": "changed"}], "a")
    assert s.count("t") == 3 and s.select("t", eq={"a": 1})[0]["name"] == "changed"
    with pytest.raises(StoreError):
        s.rpc("nope", {})


def flaky(statuses, calls):
    """A transport that answers with `statuses` in turn, then 200."""
    queue = list(statuses)

    def handler(request):
        calls.append(request.method)
        status = queue.pop(0) if queue else 200
        return httpx.Response(
            status,
            text="<html>timeout</html>" if status >= 400 else "[]",
            json=None if status >= 400 else [],
        )

    return handler


def retrying(handler, pauses):
    return SupabaseStore(
        "https://x.supabase.co",
        "KEY",
        httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=pauses.append,
    )


def test_upsert_retries_a_cloudflare_522_then_succeeds():
    calls, pauses = [], []
    store = retrying(flaky([522, 522], calls), pauses)
    assert store.upsert("species", [{"scientific_name": "A"}], "scientific_name") == []
    assert len(calls) == 3 and pauses == [1, 2]  # growing pause between attempts


def test_select_retries_server_errors_and_connection_failures():
    calls, pauses = [], []
    attempts = iter([httpx.ConnectError("down"), 503, 200])

    def handler(request):
        calls.append(1)
        step = next(attempts)
        if isinstance(step, Exception):
            raise step
        return (
            httpx.Response(200, json=[{"id": "1"}])
            if step == 200
            else httpx.Response(step, text="x")
        )

    assert retrying(handler, pauses).select("genes") == [{"id": "1"}]
    assert len(calls) == 3


def test_gives_up_after_the_last_attempt_with_a_short_message():
    calls, pauses = [], []
    store = retrying(flaky([522] * 10, calls), pauses)
    with pytest.raises(StoreError, match=r"522: <html>timeout</html>"):
        store.select("genes")
    assert len(calls) == 4 and len(pauses) == 3


def test_plain_insert_is_never_retried():
    calls, pauses = [], []
    store = retrying(flaky([522], calls), pauses)
    with pytest.raises(StoreError, match="522"):
        store.insert("evidence", [{"finding": "x"}])
    assert len(calls) == 1 and pauses == []  # a timeout does not say whether the rows were written


def test_client_errors_are_not_retried():
    calls, pauses = [], []
    with pytest.raises(StoreError, match="400"):
        retrying(flaky([400], calls), pauses).select("genes")
    assert len(calls) == 1 and pauses == []


def test_error_text_is_collapsed_and_truncated():
    big = "<!DOCTYPE html>\n" + ("<p>line</p>\n" * 200)
    store = retrying(lambda r: httpx.Response(404, text=big), [])
    with pytest.raises(StoreError) as err:
        store.select("genes")
    assert "\n" not in str(err.value) and len(str(err.value)) < 260
