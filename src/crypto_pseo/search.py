from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


JsonDict = dict[str, Any]


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str

    def as_dict(self) -> JsonDict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
        }


def search_evidence(query: str, provider: str = "mock", *, timeout_seconds: int = 10) -> JsonDict:
    if provider == "none":
        return _empty_evidence(provider, query, "skipped", "Search enrichment disabled.")
    if provider == "mock":
        return _mock_evidence(query)
    if provider == "google_cse":
        return _google_cse_evidence(query, timeout_seconds)
    return _empty_evidence(provider, query, "error", f"Unknown search provider: {provider}")


def _mock_evidence(query: str) -> JsonDict:
    results = [
        SearchResult(
            title="Brazil Pix onboarding checks remain important for crypto users",
            url="https://example.com/mock/brazil-pix-crypto-context",
            snippet="Mock evidence note: Pix can reduce funding friction, but CPF/CNPJ and KYC matching still matter.",
            source="mock",
        ),
        SearchResult(
            title="Crypto bonus headline amounts should be checked against tier requirements",
            url="https://example.com/mock/crypto-bonus-requirements",
            snippet="Mock evidence note: advertised maximum rewards often require higher deposits or trading volume.",
            source="mock",
        ),
    ]
    return {
        "provider": "mock",
        "query": query,
        "status": "ok",
        "checked_at": date.today().isoformat(),
        "note": "Offline deterministic evidence for tests. Do not treat mock results as factual sources.",
        "results": [result.as_dict() for result in results],
    }


def _google_cse_evidence(query: str, timeout_seconds: int) -> JsonDict:
    api_key = os.environ.get("GOOGLE_API_KEY")
    cse_id = os.environ.get("GOOGLE_CSE_ID")
    if not api_key or not cse_id:
        return _empty_evidence(
            "google_cse",
            query,
            "skipped",
            "GOOGLE_API_KEY and GOOGLE_CSE_ID are required for Google CSE enrichment.",
        )

    params = urlencode({"key": api_key, "cx": cse_id, "q": query, "num": 5})
    url = f"https://www.googleapis.com/customsearch/v1?{params}"
    try:
        with urlopen(url, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - depends on network/API credentials.
        return _empty_evidence("google_cse", query, "error", f"Google CSE request failed: {exc}")

    results = [
        SearchResult(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
            source="google_cse",
        ).as_dict()
        for item in payload.get("items", [])
    ]
    return {
        "provider": "google_cse",
        "query": query,
        "status": "ok",
        "checked_at": date.today().isoformat(),
        "note": "Evidence notes only. Do not overwrite campaign claims automatically.",
        "results": results,
    }


def _empty_evidence(provider: str, query: str, status: str, note: str) -> JsonDict:
    return {
        "provider": provider,
        "query": query,
        "status": status,
        "checked_at": date.today().isoformat(),
        "note": note,
        "results": [],
    }
