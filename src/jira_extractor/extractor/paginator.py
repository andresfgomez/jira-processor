"""Paginate through Jira Server search results using startAt / maxResults."""
from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

from jira_extractor.client.jira_client import JiraClient

logger = logging.getLogger(__name__)


def paginate(
    client: JiraClient,
    jql: str,
    page_size: int = 100,
    fields: list[str] | None = None,
) -> Generator[list[dict[str, Any]], None, None]:
    """Yield successive pages of issue dicts until all results are fetched."""
    start_at = 0
    total: int | None = None
    page_num = 0

    while total is None or start_at < total:
        page_num += 1
        data = client.search_issues(jql, start_at=start_at, max_results=page_size, fields=fields)

        if total is None:
            total = data.get("total", 0)
            logger.info("JQL matched %d issues total (page size: %d)", total, page_size)

        issues: list[dict[str, Any]] = data.get("issues", [])
        if not issues:
            break

        logger.info("Fetched page %d: issues %d–%d", page_num, start_at + 1, start_at + len(issues))
        yield issues
        start_at += len(issues)
