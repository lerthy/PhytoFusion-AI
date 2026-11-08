"""Plain-language explanations written by Claude from facts the app already computed.

Design rules (see docs/SCIENTIFIC_GUIDELINES.md):
- The model only restates the facts it is given. It is told not to add biology, numbers or sources.
- The explanation is shown beside those facts and labelled as AI-written, so a reader can check it.
- Evidence classes and gene matching stay rule-based and deterministic. AI never decides them.
"""

from __future__ import annotations

import json
import os
import time
from collections import deque
from collections.abc import Callable
from typing import Any, Protocol

import httpx

from .store import NotConfigured

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_OPENAI_MODEL = "openai/gpt-oss-120b"
KINDS = ("comparison", "report")
MAX_FACTS_CHARS = 6000
MAX_OUTPUT_TOKENS = 700

SYSTEM_PROMPT = (
    "You explain results from PhytoFusion AI, a computational tool that compares genes of two "
    "medicinal plants and explores a hypothetical gene transfer on paper.\n\n"
    "You are given a JSON object of facts that the tool already computed. Write a short "
    "plain-language explanation for a reader who is not a specialist.\n\n"
    "Rules:\n"
    "- Use only the facts in the JSON. Add no biology, gene functions, pathways, publications or "
    "numbers that are not in it.\n"
    "- If something is missing or unknown, say it is unknown. Never fill the gap.\n"
    "- Keep any source (PMID or DOI) attached to the statement it supports.\n"
    "- Say the scenario is hypothetical and computational. Never state that an engineered plant "
    "exists, and never say a gene transfer would work.\n"
    "- Evidence levels (strong, moderate, limited) are classes, not chances. Never turn them into "
    "scores or probabilities. Only quote percentage values that appear in the facts.\n"
    "- Never claim a compound treats or helps any disease.\n"
    "- At most 120 words. No headings.\n"
)

USER_TEMPLATE = "Kind of result: {kind}\n\nFacts (JSON):\n{facts}"


class ExplainUnavailable(Exception):
    """The AI service cannot be used right now (no key, rejected key, busy, or unreachable)."""


class ExplainRefused(Exception):
    """The model declined to answer, or returned nothing usable."""


def build_prompt(kind: str, facts: dict[str, Any]) -> str:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    text = json.dumps(facts, sort_keys=True, ensure_ascii=False)
    if len(text) > MAX_FACTS_CHARS:
        raise ValueError("facts are too large to explain")
    return USER_TEMPLATE.format(kind=kind, facts=text)


class Backend(Protocol):
    """Anything that can turn (system prompt, user prompt) into text."""

    model: str

    def complete(self, system: str, prompt: str) -> str: ...


class AnthropicBackend:
    """Claude through the official SDK."""

    def __init__(self, client: Any, model: str = DEFAULT_MODEL) -> None:
        self.client, self.model = client, model

    def complete(self, system: str, prompt: str) -> str:
        import anthropic

        try:
            # Server-side fallback: if a safety filter declines a gene-editing topic, the API
            # retries on a fallback model inside the same call instead of failing.
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=MAX_OUTPUT_TOKENS,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                output_config={"effort": "low"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.AuthenticationError as exc:
            raise ExplainUnavailable("The AI service rejected the API key.") from exc
        except anthropic.RateLimitError as exc:
            raise ExplainUnavailable("The AI service is busy. Try again in a minute.") from exc
        except (anthropic.APIConnectionError, anthropic.APIStatusError) as exc:
            raise ExplainUnavailable("The AI service could not be reached.") from exc
        if response.stop_reason == "refusal":
            raise ExplainRefused("The model declined to explain this result.")
        text = " ".join(b.text for b in response.content if b.type == "text").strip()
        if not text:
            raise ExplainRefused("The model returned no text.")
        return text


class OpenAICompatBackend:
    """Any service with an OpenAI-style /chat/completions endpoint (Groq, Gemini, OpenRouter)."""

    def __init__(
        self, api_key: str, base_url: str, model: str, http: httpx.Client | None = None
    ) -> None:
        self.api_key, self.base_url, self.model = api_key, base_url.rstrip("/"), model
        self.http = http or httpx.Client(timeout=45.0)

    def complete(self, system: str, prompt: str) -> str:
        try:
            body: dict[str, Any] = {
                "model": self.model,
                "max_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            }
            if "gpt-oss" in self.model:
                # Reasoning models spend output tokens thinking first; keep that short.
                body["reasoning_effort"] = "low"
            response = self.http.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=body,
            )
        except httpx.HTTPError as exc:
            raise ExplainUnavailable("The AI service could not be reached.") from exc
        if response.status_code in (401, 403):
            raise ExplainUnavailable("The AI service rejected the API key.")
        if response.status_code == 429:
            raise ExplainUnavailable("The AI service is busy. Try again in a minute.")
        if response.status_code >= 400:
            raise ExplainUnavailable(
                f"The AI service answered with an error ({response.status_code})."
            )
        try:
            choice = response.json()["choices"][0]
            text = (choice["message"]["content"] or "").strip()
            finish = choice.get("finish_reason")
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ExplainUnavailable("The AI service sent an unexpected reply.") from exc
        if finish == "content_filter" or not text:
            raise ExplainRefused("The model declined to explain this result.")
        return text


def backend_from_env() -> Backend:
    """Pick a backend from the environment, or raise NotConfigured when none is set.

    - ANTHROPIC_API_KEY (and optional ANTHROPIC_MODEL): Claude.
    - AI_API_KEY or GROQ_API_KEY, with optional AI_BASE_URL and AI_MODEL: any OpenAI-style service.
      The defaults point at Groq.
    AI_PROVIDER=anthropic or openai forces one when both are set.
    """
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    other_key = (
        os.environ.get("AI_API_KEY", "").strip() or os.environ.get("GROQ_API_KEY", "").strip()
    )
    provider = os.environ.get("AI_PROVIDER", "").strip().lower()
    if provider not in ("", "anthropic", "openai"):
        raise NotConfigured("AI_PROVIDER must be 'anthropic' or 'openai'")
    use_anthropic = provider == "anthropic" or (provider == "" and anthropic_key)
    if use_anthropic:
        if not anthropic_key:
            raise NotConfigured("ANTHROPIC_API_KEY is not set")
        import anthropic

        model = os.environ.get("ANTHROPIC_MODEL", "").strip() or DEFAULT_MODEL
        return AnthropicBackend(
            anthropic.Anthropic(api_key=anthropic_key, timeout=45.0, max_retries=1), model
        )
    if not other_key:
        raise NotConfigured("set AI_API_KEY (or ANTHROPIC_API_KEY)")
    return OpenAICompatBackend(
        other_key,
        os.environ.get("AI_BASE_URL", "").strip() or DEFAULT_OPENAI_BASE_URL,
        os.environ.get("AI_MODEL", "").strip() or DEFAULT_OPENAI_MODEL,
    )


def explain(kind: str, facts: dict[str, Any], backend: Backend) -> str:
    """Explain `facts` briefly. Raises ValueError, ExplainRefused or ExplainUnavailable."""
    return backend.complete(SYSTEM_PROMPT, build_prompt(kind, facts))


class RateLimiter:
    """In-memory limits, so a public demo cannot run up the bill. One process only."""

    def __init__(
        self,
        per_ip_per_hour: int = 12,
        per_day: int = 150,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.per_ip_per_hour = per_ip_per_hour
        self.per_day = per_day
        self._clock = clock
        self._ip: dict[str, deque[float]] = {}
        self._day: deque[float] = deque()

    def allow(self, ip: str) -> bool:
        now = self._clock()
        while self._day and now - self._day[0] > 86400:
            self._day.popleft()
        hits = self._ip.setdefault(ip, deque())
        while hits and now - hits[0] > 3600:
            hits.popleft()
        if len(hits) >= self.per_ip_per_hour or len(self._day) >= self.per_day:
            return False
        hits.append(now)
        self._day.append(now)
        return True
