"""Tests for the paginator using a mock JiraClient."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from jira_extractor.extractor.paginator import paginate


def _mock_client(pages: list[list[dict]]) -> MagicMock:
    """Return a mock client whose search_issues returns successive pages."""
    client = MagicMock()
    total = sum(len(p) for p in pages)
    responses = [{"total": total, "issues": page} for page in pages]
    client.search_issues.side_effect = responses
    return client


def test_single_page():
    issues = [{"id": str(i)} for i in range(5)]
    client = _mock_client([issues])
    result = list(paginate(client, "project = X", page_size=100))
    assert result == [issues]
    assert client.search_issues.call_count == 1


def test_multiple_pages():
    page1 = [{"id": str(i)} for i in range(3)]
    page2 = [{"id": str(i)} for i in range(3, 5)]
    client = _mock_client([page1, page2])
    result = list(paginate(client, "project = X", page_size=3))
    assert result == [page1, page2]
    assert client.search_issues.call_count == 2


def test_empty_result():
    client = _mock_client([[]])
    result = list(paginate(client, "project = X"))
    assert result == []


def test_start_at_increments_correctly():
    page1 = [{"id": "1"}, {"id": "2"}]
    page2 = [{"id": "3"}]
    client = _mock_client([page1, page2])
    list(paginate(client, "project = X", page_size=2))
    calls = client.search_issues.call_args_list
    assert calls[0].kwargs["start_at"] == 0
    assert calls[1].kwargs["start_at"] == 2
