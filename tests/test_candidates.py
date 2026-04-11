# -*- coding: utf-8 -*-
"""Tests for evidence-ledger candidate planning."""

import json

import pytest

from agent_reach.candidates import CandidatePlanError, build_candidates_payload
from agent_reach.ledger import build_ledger_record
from agent_reach.results import build_item, build_result


def _result(channel="web", operation="read", items=None, input_value="query"):
    return build_result(
        ok=True,
        channel=channel,
        operation=operation,
        items=items or [],
        raw={"ok": True},
        meta={"input": input_value},
        error=None,
    )


def _item(item_id, url, title, source="web"):
    return build_item(
        item_id=item_id,
        kind="page",
        title=title,
        url=url,
        text=None,
        author=None,
        published_at=None,
        source=source,
    )


def _write_jsonl(path, records):
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def test_candidates_dedupe_by_canonical_url(tmp_path):
    path = tmp_path / "evidence.jsonl"
    first = _result(
        channel="exa_search",
        operation="search",
        items=[_item("exa-1", "HTTPS://Example.com/post/#section", "First", source="exa_search")],
    )
    second = _result(
        channel="web",
        operation="read",
        items=[_item("web-1", "https://example.com/post", "Second", source="web")],
    )
    _write_jsonl(
        path,
        [
            build_ledger_record(first, run_id="run-1", input_value="topic"),
            build_ledger_record(second, run_id="run-1", input_value="https://example.com/post"),
        ],
    )

    payload = build_candidates_payload(path, by="url", limit=20)

    assert payload["summary"]["candidate_count"] == 1
    assert payload["candidates"][0]["title"] == "First"
    assert payload["candidates"][0]["extras"]["seen_in"] == [
        {
            "run_id": "run-1",
            "channel": "exa_search",
            "operation": "search",
            "input": "topic",
            "item_id": "exa-1",
            "url": "HTTPS://Example.com/post/#section",
        },
        {
            "run_id": "run-1",
            "channel": "web",
            "operation": "read",
            "input": "https://example.com/post",
            "item_id": "web-1",
            "url": "https://example.com/post",
        },
    ]


def test_candidates_fallback_dedupe_by_source_and_id(tmp_path):
    path = tmp_path / "evidence.jsonl"
    first = _result(
        channel="github",
        operation="read",
        items=[_item("openai/openai-python", None, "OpenAI Python", source="github")],
    )
    second = _result(
        channel="github",
        operation="read",
        items=[_item("openai/openai-python", None, "Duplicate", source="github")],
    )
    third = _result(
        channel="rss",
        operation="read",
        items=[_item("openai/openai-python", None, "Different source", source="rss")],
    )
    _write_jsonl(
        path,
        [
            build_ledger_record(first, run_id="run-1"),
            build_ledger_record(second, run_id="run-2"),
            build_ledger_record(third, run_id="run-3"),
        ],
    )

    payload = build_candidates_payload(path, by="url", limit=20)

    assert payload["summary"]["candidate_count"] == 2
    assert payload["candidates"][0]["title"] == "OpenAI Python"
    assert len(payload["candidates"][0]["extras"]["seen_in"]) == 2
    assert payload["candidates"][1]["title"] == "Different source"


def test_candidates_limit_keeps_first_seen_order(tmp_path):
    path = tmp_path / "evidence.jsonl"
    result = _result(
        items=[
            _item("1", "https://example.com/1", "One"),
            _item("2", "https://example.com/2", "Two"),
            _item("3", "https://example.com/3", "Three"),
        ],
    )
    _write_jsonl(path, [build_ledger_record(result, run_id="run-1")])

    payload = build_candidates_payload(path, by="url", limit=2)

    assert payload["summary"]["candidate_count"] == 3
    assert payload["summary"]["returned"] == 2
    assert [candidate["title"] for candidate in payload["candidates"]] == ["One", "Two"]


def test_candidates_invalid_jsonl_reports_error(tmp_path):
    path = tmp_path / "evidence.jsonl"
    path.write_text("{broken\n", encoding="utf-8")

    with pytest.raises(CandidatePlanError):
        build_candidates_payload(path)


def test_candidates_handles_unicode_line_separator_in_record(tmp_path):
    path = tmp_path / "evidence.jsonl"
    item = _item("1", "https://example.com/1", "One")
    item["text"] = "alpha\u2028beta"
    result = _result(items=[item])
    _write_jsonl(path, [build_ledger_record(result, run_id="run-1")])

    payload = build_candidates_payload(path, by="url", limit=20)

    assert payload["summary"]["candidate_count"] == 1
    assert payload["candidates"][0]["text"] == "alpha\u2028beta"


def test_candidates_accept_raw_collection_result_jsonl(tmp_path):
    path = tmp_path / "raw-results.jsonl"
    result = _result(items=[_item("raw-1", "https://example.com/raw", "Raw")])
    _write_jsonl(path, [{"record_type": "other"}, result])

    payload = build_candidates_payload(path, by="url", limit=20)

    assert payload["summary"]["records"] == 2
    assert payload["summary"]["collection_results"] == 1
    assert payload["summary"]["skipped_records"] == 1
    assert payload["candidates"][0]["title"] == "Raw"
    assert payload["candidates"][0]["extras"]["seen_in"][0]["run_id"] is None


def test_candidates_summary_only_omits_candidate_bodies(tmp_path):
    path = tmp_path / "evidence.jsonl"
    result = _result(items=[_item("1", "https://example.com/1", "One")])
    _write_jsonl(path, [build_ledger_record(result, run_id="run-1")])

    payload = build_candidates_payload(path, by="url", limit=20, summary_only=True)

    assert payload["summary_only"] is True
    assert payload["summary"]["candidate_count"] == 1
    assert payload["candidates"] == []


def test_candidates_summary_includes_channel_and_source_role_counts(tmp_path):
    path = tmp_path / "evidence.jsonl"
    exa_result = _result(
        channel="exa_search",
        operation="search",
        items=[_item("exa-1", "https://example.com/post", "Post", source="exa_search")],
        input_value="topic",
    )
    web_result = _result(
        channel="web",
        operation="read",
        items=[_item("web-1", "https://example.com/post", "Post", source="web")],
        input_value="https://example.com/post",
    )
    github_result = _result(
        channel="github",
        operation="read",
        items=[_item("repo-1", None, "Repo", source="github")],
        input_value="owner/repo",
    )
    _write_jsonl(
        path,
        [
            build_ledger_record(
                exa_result,
                run_id="run-1",
                intent="official_docs",
                query_id="q01",
                source_role="article_discovery",
            ),
            build_ledger_record(
                web_result,
                run_id="run-1",
                intent="followup_read",
                query_id="q02",
                source_role="followup_read",
            ),
            build_ledger_record(
                github_result,
                run_id="run-1",
                intent="oss_candidates",
                query_id="q03",
                source_role="repo_discovery",
            ),
        ],
    )

    payload = build_candidates_payload(path, by="url", limit=20, summary_only=True)

    assert payload["summary"]["candidate_count"] == 2
    assert payload["summary"]["channel_counts"] == {
        "exa_search": 1,
        "github": 1,
        "web": 1,
    }
    assert payload["summary"]["source_role_counts"] == {
        "article_discovery": 1,
        "followup_read": 1,
        "repo_discovery": 1,
    }
    assert payload["summary"]["intent_counts"] == {
        "followup_read": 1,
        "official_docs": 1,
        "oss_candidates": 1,
    }


def test_candidates_fields_filter_and_relevance_metadata(tmp_path):
    path = tmp_path / "evidence.jsonl"
    result = _result(items=[_item("1", "https://example.com/1", "One")])
    _write_jsonl(
        path,
        [
            build_ledger_record(
                result,
                run_id="run-1",
                input_value="topic",
                intent="official_docs",
                query_id="q01",
                source_role="web_discovery",
            )
        ],
    )

    payload = build_candidates_payload(
        path,
        by="url",
        limit=20,
        fields="title,url,intent,query_id,source_role",
    )

    assert payload["fields"] == ["title", "url", "intent", "query_id", "source_role"]
    assert payload["candidates"] == [
        {
            "title": "One",
            "url": "https://example.com/1",
            "intent": "official_docs",
            "query_id": "q01",
            "source_role": "web_discovery",
        }
    ]


def test_candidates_unknown_field_reports_error(tmp_path):
    path = tmp_path / "evidence.jsonl"
    _write_jsonl(path, [build_ledger_record(_result(), run_id="run-1")])

    with pytest.raises(CandidatePlanError):
        build_candidates_payload(path, fields="title,nope")


def test_candidates_records_alternate_urls_for_duplicate(tmp_path):
    path = tmp_path / "evidence.jsonl"
    first = _result(
        items=[_item("1", "https://example.com/post/", "One")],
    )
    second = _result(
        items=[_item("2", "https://example.com/post#section", "Two")],
    )
    _write_jsonl(
        path,
        [
            build_ledger_record(first, run_id="run-1"),
            build_ledger_record(second, run_id="run-1"),
        ],
    )

    payload = build_candidates_payload(path, by="url", limit=20)

    assert payload["summary"]["candidate_count"] == 1
    assert payload["candidates"][0]["extras"]["candidate_key"] == "url:https://example.com/post"
    assert payload["candidates"][0]["extras"]["alternate_urls"] == [
        "https://example.com/post#section"
    ]


def test_candidates_supports_neutral_identifier_dedupe_modes(tmp_path):
    path = tmp_path / "evidence.jsonl"
    github_item = build_item(
        item_id="repo-api-id",
        kind="repository",
        title="Agent Reach",
        url="https://github.com/iwachacha/Agent-Reach",
        text=None,
        author="iwachacha",
        published_at=None,
        source="github",
        extras={"repo_full_name": "iwachacha/Agent-Reach", "stars": 10},
        source_item_id="iwachacha/Agent-Reach",
    )
    web_item = _item("web-1", "https://example.com/post#intro", "Post")
    _write_jsonl(
        path,
        [
            build_ledger_record(_result(channel="github", operation="read", items=[github_item]), run_id="run-1"),
            build_ledger_record(_result(channel="web", operation="read", items=[web_item]), run_id="run-1"),
        ],
    )

    by_repo = build_candidates_payload(path, by="repo", limit=20)
    by_domain = build_candidates_payload(path, by="domain", limit=20)
    by_source_item_id = build_candidates_payload(path, by="source_item_id", limit=20)
    by_normalized_url = build_candidates_payload(path, by="normalized_url", limit=20)

    assert by_repo["summary"]["candidate_count"] == 1
    assert by_repo["candidates"][0]["extras"]["candidate_key"] == "repo:iwachacha/Agent-Reach"
    assert by_domain["summary"]["candidate_count"] == 2
    assert by_source_item_id["candidates"][0]["extras"]["candidate_key"] == "source_item_id:github:iwachacha/Agent-Reach"
    assert by_source_item_id["candidates"][0]["engagement"] == {"stars": 10}
    assert by_normalized_url["candidates"][1]["extras"]["candidate_key"] == "normalized_url:https://example.com/post"
