"""Orchestrate the extraction: build JQL -> paginate -> write output."""
from __future__ import annotations

import logging
import re
import time
from typing import Any

from jira_extractor.client.jira_client import JiraClient
from jira_extractor.client.rate_limiter import RateLimiter
from jira_extractor.config.schema import AppConfig, CustomFieldsConfig
from jira_extractor.extractor.paginator import paginate
from jira_extractor.extractor.query_builder import build_jql, jql_hash
from jira_extractor.output.factory import make_writer

logger = logging.getLogger(__name__)

# Regex to extract the sprint name from the legacy Jira Server sprint string,
# e.g. "com.atlassian.greenhopper...Sprint@xxx[...,name=Sprint 1,...]"
_SPRINT_NAME_RE = re.compile(r"name=([^,\]]+)")


def run_extraction(cfg: AppConfig) -> int:
    """Execute one full extraction run. Returns the total number of issues written."""
    jql = build_jql(cfg.jira, cfg.time_range)
    query_hash = jql_hash(jql)
    logger.info("JQL: %s", jql)
    logger.info("Query hash: %s", query_hash)

    rate_limiter = RateLimiter(
        delay_seconds=cfg.jira.request_delay_seconds,
    )

    writer = make_writer(cfg, query_hash)

    total_written = 0
    start = time.monotonic()

    with JiraClient(
        base_url=cfg.jira.base_url,
        token=cfg.jira.token.get_secret_value(),
        rate_limiter=rate_limiter,
    ) as client:
        with writer:
            for page in paginate(
                client,
                jql,
                page_size=cfg.jira.max_results,
            ):
                flat_issues = [_flatten_issue(issue, cfg.custom_fields) for issue in page]
                writer.write_batch(flat_issues)
                total_written += len(flat_issues)

    elapsed = time.monotonic() - start
    logger.info(
        "Extraction complete: %d issues written in %.1f seconds",
        total_written,
        elapsed,
    )
    return total_written


def _flatten_issue(issue: dict[str, Any], cf: CustomFieldsConfig) -> dict[str, Any]:
    """Flatten a Jira issue JSON into the target field set."""
    fields: dict[str, Any] = issue.get("fields", {})

    def _str(val: Any) -> str:
        if val is None:
            return ""
        if isinstance(val, dict):
            return val.get("displayName") or val.get("name") or val.get("value") or ""
        return str(val)

    def _email(person: Any) -> str:
        if not isinstance(person, dict):
            return ""
        return person.get("emailAddress") or ""

    def _sprint_name(sprint_field: Any) -> str:
        """Extract the active/latest sprint name from either object or legacy string format."""
        if not sprint_field:
            return ""
        sprints = sprint_field if isinstance(sprint_field, list) else [sprint_field]
        # Prefer the active sprint; fall back to the last one in the list.
        for sprint in reversed(sprints):
            if isinstance(sprint, dict):
                if sprint.get("state", "").lower() == "active":
                    return sprint.get("name", "")
            elif isinstance(sprint, str):
                match = _SPRINT_NAME_RE.search(sprint)
                if match:
                    return match.group(1)
        # No active sprint found — return the name of the last sprint.
        last = sprints[-1]
        if isinstance(last, dict):
            return last.get("name", "")
        if isinstance(last, str):
            match = _SPRINT_NAME_RE.search(last)
            return match.group(1) if match else ""
        return ""

    assignee = fields.get("assignee")
    creator = fields.get("creator")

    return {
        "key": issue.get("key", ""),
        "category": _str(fields.get("project", {}).get("projectCategory")),
        "issuetype": _str(fields.get("issuetype")),
        "status": _str(fields.get("status")),
        "resolution_date": fields.get("resolutiondate") or "",
        "sprint_name": _sprint_name(fields.get(cf.sprint)),
        "assignee_name": _str(assignee),
        "assignee_email": _email(assignee),
        "creator_name": _str(creator),
        "creator_email": _email(creator),
        "story_points": fields.get(cf.story_points) or "",
        "ai_assisted_effort": _str(fields.get(cf.ai_assisted_effort)),
        "ai_usage_level": _str(fields.get(cf.ai_usage_level)),
    }
