# -*- coding: utf-8 -*-
"""Tests for the external collection result schema helpers."""

from agent_reach.results import build_error, build_item, build_result


def test_build_item_and_result_shape():
    item = build_item(
        item_id="item-1",
        kind="page",
        title="Example",
        url="https://example.com",
        text="hello",
        author="alice",
        published_at="2026-04-10T00:00:00Z",
        source="web",
        extras={"reader_url": "https://r.jina.ai/https://example.com"},
    )
    payload = build_result(
        ok=True,
        channel="web",
        operation="read",
        items=[item],
        raw={"ok": True},
        meta={"input": "https://example.com"},
        error=None,
    )

    assert set(item) == {
        "id",
        "kind",
        "title",
        "url",
        "text",
        "author",
        "published_at",
        "source",
        "extras",
    }
    assert set(payload) == {"ok", "channel", "operation", "items", "raw", "meta", "error"}
    assert payload["meta"]["schema_version"]
    assert payload["meta"]["count"] == 1


def test_build_error_shape():
    error = build_error(code="invalid_input", message="bad input", details={"field": "input"})

    assert error == {
        "code": "invalid_input",
        "message": "bad input",
        "details": {"field": "input"},
    }
