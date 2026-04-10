"""Tests for JQL query builder."""
import pytest

from jira_extractor.config.schema import JiraConfig, TimeRangeConfig
from jira_extractor.extractor.query_builder import build_jql, jql_hash


def _jira(**kwargs) -> JiraConfig:
    return JiraConfig(token="test-token", **kwargs)


def test_empty_config_returns_order_by_only():
    jql = build_jql(_jira(), TimeRangeConfig())
    assert jql == "ORDER BY updated DESC"


def test_single_project():
    jql = build_jql(_jira(projects=["PROJ"]), TimeRangeConfig())
    assert 'project in ("PROJ")' in jql


def test_multiple_projects():
    jql = build_jql(_jira(projects=["A", "B"]), TimeRangeConfig())
    assert 'project in ("A", "B")' in jql


def test_issue_types():
    jql = build_jql(_jira(issue_types=["Bug", "Task"]), TimeRangeConfig())
    assert 'issuetype in ("Bug", "Task")' in jql


def test_statuses():
    jql = build_jql(_jira(statuses=["Done"]), TimeRangeConfig())
    assert 'status in ("Done")' in jql


def test_time_range_after_only():
    jql = build_jql(_jira(), TimeRangeConfig(updated_after="2024-01-01"))
    assert 'updated >= "2024-01-01"' in jql
    assert "updated <=" not in jql


def test_time_range_both_bounds():
    jql = build_jql(
        _jira(),
        TimeRangeConfig(updated_after="2024-01-01", updated_before="2024-12-31"),
    )
    assert 'updated >= "2024-01-01"' in jql
    assert 'updated <= "2024-12-31"' in jql


def test_combined_criteria():
    jql = build_jql(
        _jira(projects=["PROJ"], statuses=["Open"]),
        TimeRangeConfig(updated_after="2024-06-01"),
    )
    assert "project" in jql
    assert "status" in jql
    assert "updated >=" in jql
    assert "ORDER BY updated DESC" in jql


def test_jql_hash_is_deterministic():
    jql = 'project in ("PROJ") ORDER BY updated DESC'
    assert jql_hash(jql) == jql_hash(jql)


def test_jql_hash_length():
    assert len(jql_hash("anything")) == 8
