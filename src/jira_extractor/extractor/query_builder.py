"""Build a JQL query string from structured configuration."""
from __future__ import annotations

import hashlib

from jira_extractor.config.schema import JiraConfig, TimeRangeConfig


def build_jql(jira: JiraConfig, time_range: TimeRangeConfig) -> str:
    """Return a JQL string derived from the given config objects."""
    clauses: list[str] = []

    if jira.projects:
        projects = ", ".join(f'"{p}"' for p in jira.projects)
        clauses.append(f"project in ({projects})")

    if jira.issue_types:
        types = ", ".join(f'"{t}"' for t in jira.issue_types)
        clauses.append(f"issuetype in ({types})")

    if jira.statuses:
        statuses = ", ".join(f'"{s}"' for s in jira.statuses)
        clauses.append(f"status in ({statuses})")

    if jira.labels:
        labels = ", ".join(f'"{lb}"' for lb in jira.labels)
        clauses.append(f"labels in ({labels})")

    if time_range.updated_after:
        clauses.append(f'updated >= "{time_range.updated_after}"')

    if time_range.updated_before:
        clauses.append(f'updated <= "{time_range.updated_before}"')

    jql = " AND ".join(clauses) if clauses else "ORDER BY updated DESC"
    if clauses:
        jql += " ORDER BY updated DESC"

    return jql


def jql_hash(jql: str) -> str:
    """Return an 8-char hex digest of the JQL string — used in output filenames."""
    return hashlib.sha256(jql.encode()).hexdigest()[:8]
