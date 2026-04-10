"""Tests for CSVWriter."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from jira_extractor.output.writers import CSVWriter


FIELDS = [
    "key",
    "category",
    "issuetype",
    "status",
    "resolution_date",
    "sprint_name",
    "assignee_name",
    "assignee_email",
    "creator_name",
    "creator_email",
    "story_points",
    "ai_assisted_effort",
    "ai_usage_level",
]

ISSUES = [
    {
        "key": "PROJ-1",
        "category": "Engineering",
        "issuetype": "Bug",
        "status": "In Progress",
        "resolution_date": "2024-03-01T10:00:00.000+0000",
        "sprint_name": "Sprint 5",
        "assignee_name": "Alice Smith",
        "assignee_email": "alice@example.com",
        "creator_name": "Bob Jones",
        "creator_email": "bob@example.com",
        "story_points": "3",
        "ai_assisted_effort": "Medium",
        "ai_usage_level": "High",
        "extra": "ignored",
    },
    {
        "key": "PROJ-2",
        "category": "Platform",
        "issuetype": "Story",
        "status": "Done",
        "resolution_date": "",
        "sprint_name": "Sprint 6",
        "assignee_name": "Carol White",
        "assignee_email": "carol@example.com",
        "creator_name": "Dave Green",
        "creator_email": "dave@example.com",
        "story_points": "5",
        "ai_assisted_effort": "Low",
        "ai_usage_level": "None",
    },
]


def test_csv_writer_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    with CSVWriter(path=out, fields=FIELDS) as w:
        w.write_batch(ISSUES)
    assert out.exists()


def test_csv_writer_header_and_rows(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    with CSVWriter(path=out, fields=FIELDS) as w:
        w.write_batch(ISSUES)

    with open(out, newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    assert reader.fieldnames == FIELDS
    assert rows[0]["key"] == "PROJ-1"
    assert rows[0]["status"] == "In Progress"
    assert rows[0]["assignee_email"] == "alice@example.com"
    assert rows[0]["ai_usage_level"] == "High"
    assert rows[1]["story_points"] == "5"
    # Extra field not in FIELDS should be absent
    assert "extra" not in rows[0]


def test_csv_writer_multiple_batches(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    with CSVWriter(path=out, fields=FIELDS) as w:
        w.write_batch(ISSUES[:1])
        w.write_batch(ISSUES[1:])

    with open(out, newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 2
