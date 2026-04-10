"""Thin httpx wrapper for the Jira Server REST API."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from jira_extractor.client.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

_SEARCH_PATH = "/rest/api/2/search"
_MAX_RETRIES = 5


class JiraClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        rate_limiter: RateLimiter,
        timeout: float = 30.0,
    ) -> None:
        self._rate_limiter = rate_limiter
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    def search_issues(
        self,
        jql: str,
        start_at: int = 0,
        max_results: int = 100,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Call /rest/api/2/search and return the raw JSON response dict."""
        params: dict[str, Any] = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
        }
        if fields:
            params["fields"] = ",".join(fields)

        for attempt in range(_MAX_RETRIES):
            self._rate_limiter.wait()
            try:
                response = self._client.get(_SEARCH_PATH, params=params)
            except httpx.RequestError as exc:
                logger.error("HTTP request failed: %s", exc)
                raise

            if response.status_code in (429, 503):
                self._rate_limiter.backoff(attempt)
                continue

            response.raise_for_status()
            logger.debug(
                "GET %s startAt=%d -> %d issues (total=%s)",
                _SEARCH_PATH,
                start_at,
                len(response.json().get("issues", [])),
                response.json().get("total", "?"),
            )
            return response.json()  # type: ignore[no-any-return]

        raise RuntimeError(f"Exceeded {_MAX_RETRIES} retries for startAt={start_at}")

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "JiraClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
