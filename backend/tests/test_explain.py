from types import SimpleNamespace

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

from app import routes
from app.explain import (
    DEFAULT_MODEL,
    DEFAULT_OPENAI_BASE_URL,
    DEFAULT_OPENAI_MODEL,
    MAX_FACTS_CHARS,
    SYSTEM_PROMPT,
    AnthropicBackend,
    ExplainRefused,
    ExplainUnavailable,
    OpenAICompatBackend,
    RateLimiter,
    backend_from_env,
    build_prompt,
    explain,
)
from app.main import app
from app.store import NotConfigured

FACTS = {"donor_gene": "G1", "host_gene": "H1", "sequence_relationship": "related"}
ENV = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL",
    "AI_API_KEY",
    "GROQ_API_KEY",
    "AI_BASE_URL",
    "AI_MODEL",
    "AI_PROVIDER",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV:
        monkeypatch.delenv(name, raising=False)


class FakeBackend:
    model = "fake-model"

    def __init__(self, text="G1 and H1 are related.", error=None):
        self.text, self.error, self.calls = text, error, []

    def complete(self, system, prompt):
        self.calls.append((system, prompt))
        if self.error:
            raise self.error
        return self.text


# ---- prompt ---------------------------------------------------------------------------------
def test_prompt_contains_only_the_supplied_facts():
    prompt = build_prompt("comparison", FACTS)
    assert '"donor_gene": "G1"' in prompt and "comparison" in prompt


@pytest.mark.parametrize(
    "kind, facts",
    [("poem", FACTS), ("report", {"text": "x" * (MAX_FACTS_CHARS + 1)})],
)
def test_prompt_rejects_bad_input(kind, facts):
    with pytest.raises(ValueError):
        build_prompt(kind, facts)


def test_explain_sends_the_grounding_rules_with_the_facts():
    backend = FakeBackend()
    assert explain("comparison", FACTS, backend) == "G1 and H1 are related."
    system, prompt = backend.calls[0]
    assert system == SYSTEM_PROMPT and "Use only the facts" in system and "hypothetical" in system
    assert '"host_gene": "H1"' in prompt


# ---- Claude backend -------------------------------------------------------------------------
def reply(text="Fine.", stop_reason="end_turn", blocks=None):
    content = blocks if blocks is not None else [SimpleNamespace(type="text", text=text)]
    return SimpleNamespace(stop_reason=stop_reason, content=content)


class FakeSdk:
    def __init__(self, response=None, error=None):
        self.calls, self._response, self._error = [], response or reply(), error
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        return self._response


def api_error(cls, status):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls(message="x", response=httpx.Response(status, request=request), body=None)


def test_claude_call_uses_low_effort_and_refusal_fallback():
    sdk = FakeSdk()
    assert AnthropicBackend(sdk).complete("sys", "hi") == "Fine."
    call = sdk.calls[0]
    assert call["model"] == DEFAULT_MODEL and call["system"] == "sys"
    assert call["output_config"] == {"effort": "low"} and call["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in call["betas"]


@pytest.mark.parametrize(
    "response",
    [
        reply(stop_reason="refusal"),
        reply(blocks=[]),
        reply(blocks=[SimpleNamespace(type="thinking")]),
    ],
)
def test_claude_refusal_or_empty_reply_is_reported(response):
    with pytest.raises(ExplainRefused):
        AnthropicBackend(FakeSdk(response=response)).complete("s", "p")


@pytest.mark.parametrize(
    "cls, status",
    [
        (anthropic.AuthenticationError, 401),
        (anthropic.RateLimitError, 429),
        (anthropic.InternalServerError, 500),
    ],
)
def test_claude_service_errors_become_unavailable(cls, status):
    with pytest.raises(ExplainUnavailable):
        AnthropicBackend(FakeSdk(error=api_error(cls, status))).complete("s", "p")


# ---- OpenAI-style backend (Groq, Gemini, OpenRouter) ------------------------------------------
def compat(handler):
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenAICompatBackend("key-123", "https://example.test/v1/", "m1", http=http)


def chat(text="Plain words.", finish="stop"):
    return {"choices": [{"message": {"content": text}, "finish_reason": finish}]}


def test_openai_style_request_shape_and_reply():
    seen = {}

    def handler(request):
        seen["url"], seen["auth"] = str(request.url), request.headers["authorization"]
        seen["body"] = __import__("json").loads(request.content)
        return httpx.Response(200, json=chat())

    assert compat(handler).complete("sys", "hi") == "Plain words."
    assert seen["url"] == "https://example.test/v1/chat/completions"
    assert seen["auth"] == "Bearer key-123"
    assert seen["body"]["model"] == "m1"
    assert [m["role"] for m in seen["body"]["messages"]] == ["system", "user"]


@pytest.mark.parametrize(
    "response, error",
    [
        (httpx.Response(401, json={}), ExplainUnavailable),
        (httpx.Response(429, json={}), ExplainUnavailable),
        (httpx.Response(500, json={}), ExplainUnavailable),
        (httpx.Response(200, text="not json"), ExplainUnavailable),
        (httpx.Response(200, json={"choices": []}), ExplainUnavailable),
        (httpx.Response(200, json=chat(finish="content_filter")), ExplainRefused),
        (httpx.Response(200, json=chat(text="")), ExplainRefused),
    ],
)
def test_openai_style_errors(response, error):
    with pytest.raises(error):
        compat(lambda _request: response).complete("s", "p")


def test_openai_style_connection_error():
    def handler(request):
        raise httpx.ConnectError("down", request=request)

    with pytest.raises(ExplainUnavailable):
        compat(handler).complete("s", "p")


# ---- choosing a backend from the environment -----------------------------------------------
def test_nothing_configured(monkeypatch):
    with pytest.raises(NotConfigured):
        backend_from_env()


def test_groq_is_the_default_for_ai_api_key(monkeypatch):
    monkeypatch.setenv("AI_API_KEY", "k")
    backend = backend_from_env()
    assert isinstance(backend, OpenAICompatBackend)
    assert backend.base_url == DEFAULT_OPENAI_BASE_URL and backend.model == DEFAULT_OPENAI_MODEL


def test_groq_api_key_alias_and_overrides(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setenv("AI_MODEL", "other")
    monkeypatch.setenv("AI_BASE_URL", "https://x.test/v1")
    backend = backend_from_env()
    assert backend.model == "other" and backend.base_url == "https://x.test/v1"


def test_anthropic_key_selects_claude(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    backend = backend_from_env()
    assert isinstance(backend, AnthropicBackend) and backend.model == "claude-sonnet-5-5"


def test_provider_can_force_the_other_one(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("AI_API_KEY", "k2")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    assert isinstance(backend_from_env(), OpenAICompatBackend)


@pytest.mark.parametrize("provider", ["anthropic", "mistral"])
def test_provider_errors(monkeypatch, provider):
    monkeypatch.setenv("AI_API_KEY", "k")
    monkeypatch.setenv("AI_PROVIDER", provider)
    with pytest.raises(NotConfigured):
        backend_from_env()


# ---- rate limiter and route --------------------------------------------------------------------
def test_rate_limiter_per_ip_and_per_day():
    now = [0.0]
    limiter = RateLimiter(per_ip_per_hour=2, per_day=3, clock=lambda: now[0])
    assert limiter.allow("a") and limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")
    assert not limiter.allow("c")
    now[0] = 3601
    assert not limiter.allow("a")
    now[0] = 90000
    assert limiter.allow("a")


@pytest.fixture
def api(monkeypatch):
    backend = FakeBackend()
    app.dependency_overrides[routes.get_ai_backend] = lambda: backend
    monkeypatch.setattr(routes, "_explain_limiter", RateLimiter())
    yield TestClient(app), backend
    app.dependency_overrides.clear()


def test_route_returns_text_and_model(api):
    client, _ = api
    body = client.post("/api/explain", json={"kind": "comparison", "facts": FACTS}).json()
    assert body == {"text": "G1 and H1 are related.", "model": "fake-model"}


def test_route_rate_limits(api, monkeypatch):
    client, _ = api
    monkeypatch.setattr(routes, "_explain_limiter", RateLimiter(per_ip_per_hour=1))
    payload = {"kind": "report", "facts": FACTS}
    assert client.post("/api/explain", json=payload).status_code == 200
    assert client.post("/api/explain", json=payload).status_code == 429


def test_route_rejects_oversized_facts(api):
    client, _ = api
    big = {"t": "x" * (MAX_FACTS_CHARS + 1)}
    assert client.post("/api/explain", json={"kind": "report", "facts": big}).status_code == 422


@pytest.mark.parametrize(
    "error, status", [(ExplainRefused("no"), 502), (ExplainUnavailable("down"), 503)]
)
def test_route_maps_ai_errors(error, status):
    app.dependency_overrides[routes.get_ai_backend] = lambda: FakeBackend(error=error)
    try:
        response = TestClient(app).post("/api/explain", json={"kind": "report", "facts": FACTS})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == status


def test_route_says_not_configured_without_a_key():
    response = TestClient(app).post("/api/explain", json={"kind": "report", "facts": FACTS})
    assert response.status_code == 503 and "not configured" in response.json()["detail"]
