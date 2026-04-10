# -*- coding: utf-8 -*-
"""Candidate planning helpers for evidence ledgers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit, urlunsplit

from agent_reach.schemas import SCHEMA_VERSION, utc_timestamp


class CandidatePlanError(Exception):
    """Raised when candidate planning input cannot be read or parsed."""


ALLOWED_CANDIDATE_FIELDS = {
    "id",
    "kind",
    "title",
    "url",
    "text",
    "author",
    "published_at",
    "source",
    "intent",
    "query_id",
    "source_role",
    "extras",
}


def canonicalize_url(url: str | None) -> str | None:
    """Return a minimal canonical URL for dedupe."""

    if not url:
        return None
    text = str(url).strip()
    if not text:
        return None
    parts = urlsplit(text)
    path = parts.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            parts.query,
            "",
        )
    )


def build_candidates_payload(
    path: str | Path,
    *,
    by: str = "url",
    limit: int = 20,
    summary_only: bool = False,
    fields: Sequence[str] | str | None = None,
) -> dict[str, Any]:
    """Read evidence JSONL and return a deduped candidate payload."""

    if by not in {"url", "id"}:
        raise CandidatePlanError(f"Unsupported dedupe mode: {by}")
    if limit < 1:
        raise CandidatePlanError("limit must be greater than or equal to 1")
    selected_fields = _normalize_fields(fields)

    evidence_path = Path(path)
    records, skipped_records = _read_collection_records(evidence_path)
    candidates: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}
    items_seen = 0
    skipped_items = 0

    for record in records:
        result = record["result"]
        meta = result.get("meta") or {}
        for item in result.get("items") or []:
            if not isinstance(item, dict):
                skipped_items += 1
                continue
            items_seen += 1
            key = _dedupe_key(item, result, by=by)
            if key is None:
                skipped_items += 1
                continue
            intent = _metadata_value(record, result, item, "intent")
            query_id = _metadata_value(record, result, item, "query_id")
            source_role = _metadata_value(record, result, item, "source_role")

            sighting = {
                "run_id": record.get("run_id"),
                "channel": result.get("channel"),
                "operation": result.get("operation"),
                "input": record.get("input") if record.get("input") is not None else meta.get("input"),
                "item_id": item.get("id"),
                "url": item.get("url"),
            }
            _add_if_present(sighting, "intent", intent)
            _add_if_present(sighting, "query_id", query_id)
            _add_if_present(sighting, "source_role", source_role)

            if key in by_key:
                by_key[key]["extras"]["seen_in"].append(sighting)
                _fill_missing_candidate_metadata(by_key[key], intent, query_id, source_role)
                _append_alternate_url(by_key[key], item.get("url"))
                continue

            candidate = _candidate_from_item(item)
            candidate["intent"] = intent
            candidate["query_id"] = query_id
            candidate["source_role"] = source_role
            candidate["extras"]["seen_in"] = [sighting]
            candidate["extras"]["candidate_key"] = key
            candidate["extras"].setdefault("alternate_urls", [])
            by_key[key] = candidate
            candidates.append(candidate)

    returned = candidates[:limit]
    output_candidates = [] if summary_only else [_filter_candidate(candidate, selected_fields) for candidate in returned]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "command": "plan candidates",
        "input": str(evidence_path),
        "by": by,
        "limit": limit,
        "summary_only": summary_only,
        "fields": list(selected_fields) if selected_fields is not None else None,
        "summary": {
            "records": len(records) + skipped_records,
            "collection_results": len(records),
            "skipped_records": skipped_records,
            "items_seen": items_seen,
            "skipped_items": skipped_items,
            "candidate_count": len(candidates),
            "returned": len(returned),
        },
        "candidates": output_candidates,
    }


def render_candidates_text(payload: dict[str, Any]) -> str:
    """Render candidate planner output for humans."""

    summary = payload["summary"]
    lines = [
        "Agent Reach Candidate Plan",
        "========================================",
        f"Input: {payload['input']}",
        f"Mode: {payload['by']}",
        f"Candidates: {summary['returned']}/{summary['candidate_count']}",
    ]
    if summary.get("skipped_records"):
        lines.append(f"Skipped records: {summary['skipped_records']}")
    if summary.get("skipped_items"):
        lines.append(f"Skipped items: {summary['skipped_items']}")
    for candidate in payload["candidates"]:
        title = candidate.get("title") or candidate.get("id") or "(untitled)"
        url = candidate.get("url") or ""
        lines.append(f"  - {title} {url}".rstrip())
    return "\n".join(lines)


def _read_collection_records(path: Path) -> tuple[list[dict[str, Any]], int]:
    records: list[dict[str, Any]] = []
    skipped_records = 0
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise CandidatePlanError(f"Could not read evidence input: {exc}") from exc

    for line_number, line in enumerate(lines, start=1):
        text = line.strip()
        if not text:
            continue
        try:
            record = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CandidatePlanError(f"Invalid JSONL at line {line_number}: {exc.msg}") from exc
        collection_record = _collection_record_from_json(record)
        if collection_record is None:
            skipped_records += 1
            continue
        records.append(collection_record)
    return records, skipped_records


def _collection_record_from_json(record: Any) -> dict[str, Any] | None:
    if not isinstance(record, dict):
        return None

    if record.get("record_type") == "collection_result":
        result = record.get("result")
        if _is_collection_result(result):
            return {
                "run_id": record.get("run_id"),
                "input": record.get("input"),
                "intent": record.get("intent"),
                "query_id": record.get("query_id"),
                "source_role": record.get("source_role"),
                "result": result,
            }
        return None

    if _is_collection_result(record):
        meta = record.get("meta") or {}
        return {
            "run_id": record.get("run_id"),
            "input": meta.get("input"),
            "intent": meta.get("intent"),
            "query_id": meta.get("query_id"),
            "source_role": meta.get("source_role"),
            "result": record,
        }
    return None


def _is_collection_result(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    required = {"ok", "channel", "operation", "items", "meta", "error"}
    return required.issubset(value.keys()) and isinstance(value.get("items"), list)


def _candidate_from_item(item: dict[str, Any]) -> dict[str, Any]:
    raw_extras = item.get("extras")
    extras: dict[str, Any] = raw_extras if isinstance(raw_extras, dict) else {}
    return {
        "id": item.get("id"),
        "kind": item.get("kind"),
        "title": item.get("title"),
        "url": item.get("url"),
        "text": item.get("text"),
        "author": item.get("author"),
        "published_at": item.get("published_at"),
        "source": item.get("source"),
        "intent": extras.get("intent"),
        "query_id": extras.get("query_id"),
        "source_role": extras.get("source_role"),
        "extras": {**extras},
    }


def _metadata_value(
    record: dict[str, Any],
    result: dict[str, Any],
    item: dict[str, Any],
    name: str,
) -> Any:
    raw_meta = result.get("meta")
    raw_extras = item.get("extras")
    meta: dict[str, Any] = raw_meta if isinstance(raw_meta, dict) else {}
    extras: dict[str, Any] = raw_extras if isinstance(raw_extras, dict) else {}
    for source in (record, meta, extras):
        value = source.get(name)
        if value is not None:
            return value
    return None


def _add_if_present(target: dict[str, Any], name: str, value: Any) -> None:
    if value is not None:
        target[name] = value


def _fill_missing_candidate_metadata(
    candidate: dict[str, Any],
    intent: Any,
    query_id: Any,
    source_role: Any,
) -> None:
    if candidate.get("intent") is None and intent is not None:
        candidate["intent"] = intent
    if candidate.get("query_id") is None and query_id is not None:
        candidate["query_id"] = query_id
    if candidate.get("source_role") is None and source_role is not None:
        candidate["source_role"] = source_role


def _append_alternate_url(candidate: dict[str, Any], url: Any) -> None:
    if not url:
        return
    text = str(url)
    if not text or text == candidate.get("url"):
        return
    alternates = candidate.setdefault("extras", {}).setdefault("alternate_urls", [])
    if text not in alternates:
        alternates.append(text)


def _normalize_fields(fields: Sequence[str] | str | None) -> tuple[str, ...] | None:
    if fields is None:
        return None
    if isinstance(fields, str):
        values = tuple(item.strip() for item in fields.split(",") if item.strip())
    else:
        values = tuple(str(item).strip() for item in fields if str(item).strip())
    if not values:
        raise CandidatePlanError("fields must include at least one field name")
    unknown = sorted(set(values) - ALLOWED_CANDIDATE_FIELDS)
    if unknown:
        supported = ", ".join(sorted(ALLOWED_CANDIDATE_FIELDS))
        raise CandidatePlanError(
            f"Unsupported candidate field(s): {', '.join(unknown)}. Supported fields: {supported}"
        )
    return values


def _filter_candidate(
    candidate: dict[str, Any],
    fields: tuple[str, ...] | None,
) -> dict[str, Any]:
    if fields is None:
        return candidate
    return {field: candidate.get(field) for field in fields}


def _dedupe_key(
    item: dict[str, Any],
    result: dict[str, Any],
    *,
    by: str,
) -> str | None:
    source = item.get("source") or result.get("channel") or "unknown"
    item_id = item.get("id")
    url = canonicalize_url(item.get("url"))
    if by == "id":
        if item_id:
            return f"id:{source}:{item_id}"
        if url:
            return f"url:{url}"
    else:
        if url:
            return f"url:{url}"
        if item_id:
            return f"id:{source}:{item_id}"
    return None
