"""Tests for _flatten_issue field extraction."""
from __future__ import annotations

from jira_extractor.config.schema import CustomFieldsConfig
from jira_extractor.extractor.extractor import _flatten_issue

CF = CustomFieldsConfig(
    sprint="customfield_10020",
    story_points="customfield_10016",
    ai_assisted_effort="customfield_10100",
    ai_usage_level="customfield_10101",
)


def _issue(fields: dict) -> dict:
    return {"key": "PROJ-1", "fields": fields}


def test_basic_fields():
    flat = _flatten_issue(
        _issue({
            "issuetype": {"name": "Bug"},
            "status": {"name": "In Progress"},
            "resolutiondate": "2024-06-01T00:00:00.000+0000",
            "assignee": {"displayName": "Alice", "emailAddress": "alice@example.com"},
            "creator": {"displayName": "Bob", "emailAddress": "bob@example.com"},
            "customfield_10016": 5,
            "customfield_10100": {"value": "Medium"},
            "customfield_10101": {"value": "High"},
        }),
        CF,
    )
    assert flat["key"] == "PROJ-1"
    assert flat["issuetype"] == "Bug"
    assert flat["status"] == "In Progress"
    assert flat["resolution_date"] == "2024-06-01T00:00:00.000+0000"
    assert flat["assignee_name"] == "Alice"
    assert flat["assignee_email"] == "alice@example.com"
    assert flat["creator_name"] == "Bob"
    assert flat["creator_email"] == "bob@example.com"
    assert flat["story_points"] == 5
    assert flat["ai_assisted_effort"] == "Medium"
    assert flat["ai_usage_level"] == "High"


def test_category_from_project():
    flat = _flatten_issue(
        _issue({"project": {"projectCategory": {"name": "Engineering"}}}),
        CF,
    )
    assert flat["category"] == "Engineering"


def test_category_missing():
    flat = _flatten_issue(_issue({"project": {}}), CF)
    assert flat["category"] == ""


def test_sprint_object_active():
    sprints = [
        {"id": 1, "name": "Sprint 4", "state": "closed"},
        {"id": 2, "name": "Sprint 5", "state": "active"},
    ]
    flat = _flatten_issue(_issue({"customfield_10020": sprints}), CF)
    assert flat["sprint_name"] == "Sprint 5"


def test_sprint_object_no_active_returns_last():
    sprints = [
        {"id": 1, "name": "Sprint 3", "state": "closed"},
        {"id": 2, "name": "Sprint 4", "state": "closed"},
    ]
    flat = _flatten_issue(_issue({"customfield_10020": sprints}), CF)
    assert flat["sprint_name"] == "Sprint 4"


def test_sprint_legacy_string():
    sprint_str = (
        "com.atlassian.greenhopper.service.sprint.Sprint@abc123"
        "[id=10,rapidViewId=1,state=ACTIVE,name=Sprint 7,startDate=2024-01-01,"
        "endDate=2024-01-14,completeDate=<null>,sequence=10]"
    )
    flat = _flatten_issue(_issue({"customfield_10020": [sprint_str]}), CF)
    assert flat["sprint_name"] == "Sprint 7"


def test_sprint_missing():
    flat = _flatten_issue(_issue({}), CF)
    assert flat["sprint_name"] == ""


def test_null_assignee():
    flat = _flatten_issue(_issue({"assignee": None}), CF)
    assert flat["assignee_name"] == ""
    assert flat["assignee_email"] == ""


def test_null_resolution_date():
    flat = _flatten_issue(_issue({"resolutiondate": None}), CF)
    assert flat["resolution_date"] == ""
