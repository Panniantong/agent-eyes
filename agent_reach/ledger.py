# -*- coding: utf-8 -*-
"""Evidence ledger helpers for collection runs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, TypedDict, cast

from agent_reach.results import CollectionResult
from agent_reach.schemas import SCHEMA_VERSION, utc_timestamp


class EvidenceLedgerRecord(TypedDict):
    """A JSONL record preserving one collection result envelope."""

    schema_version: str
    record_type: str
    run_id: str
    created_at: str
    channel: str
    operation: str
    input: str | None
    ok: bool
    count: int
    item_ids: list[str]
    urls: list[str]
    error_code: str | None
    intent: str | None
    query_id: str | None
    source_role: str | None
    result: CollectionResult


_LEDGER_GLOB = "*.jsonl"
_SHARD_CHOICES = {"channel", "operation", "channel-operation"}
_LARGE_TEXT_CHARS = 10_000
_DIAGNOSTIC_LIMIT = 50


def default_run_id() -> str:
    """Return the run ID for this command invocation."""

    configured = os.environ.get("AGENT_REACH_RUN_ID")
    if configured:
        return configured
    return f"run-{utc_timestamp().replace(':', '').replace('-', '')}"


def build_ledger_record(
    result: CollectionResult,
    *,
    run_id: str,
    input_value: str | None = None,
    intent: str | None = None,
    query_id: str | None = None,
    source_role: str | None = None,
) -> EvidenceLedgerRecord:
    """Build a compact ledger record around a full collection result."""

    items = result.get("items") or []
    error = result.get("error")
    meta = result.get("meta") or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "collection_result",
        "run_id": run_id,
        "created_at": utc_timestamp(),
        "channel": result["channel"],
        "operation": result["operation"],
        "input": input_value if input_value is not None else meta.get("input"),
        "ok": bool(result["ok"]),
        "count": int(meta.get("count", len(items)) or 0),
        "item_ids": [str(item.get("id")) for item in items if item.get("id")],
        "urls": [str(item.get("url")) for item in items if item.get("url")],
        "error_code": error["code"] if error else None,
        "intent": intent if intent is not None else meta.get("intent"),
        "query_id": query_id if query_id is not None else meta.get("query_id"),
        "source_role": source_role if source_role is not None else meta.get("source_role"),
        "result": result,
    }


def append_ledger_record(path: str | Path, record: EvidenceLedgerRecord) -> None:
    """Append a ledger record as JSON Lines, creating parent directories."""

    ledger_path = Path(path)
    _ensure_parent_dir(ledger_path)
    with ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False))
        handle.write("\n")


def save_collection_result(
    path: str | Path,
    result: CollectionResult,
    *,
    run_id: str,
    input_value: str | None = None,
    intent: str | None = None,
    query_id: str | None = None,
    source_role: str | None = None,
) -> EvidenceLedgerRecord:
    """Build and append a collection result ledger record."""

    record = build_ledger_record(
        result,
        run_id=run_id,
        input_value=input_value,
        intent=intent,
        query_id=query_id,
        source_role=source_role,
    )
    append_ledger_record(path, record)
    return record


def ledger_input_paths(
    path: str | Path,
    *,
    allow_missing: bool = False,
    exclude: str | Path | None = None,
) -> list[Path]:
    """Resolve a ledger file or directory into concrete JSONL input paths."""

    target = Path(path)
    if not target.exists():
        if allow_missing:
            return []
        raise FileNotFoundError(f"Ledger input does not exist: {target}")

    excluded_path = _resolved_path(exclude) if exclude is not None else None
    if target.is_dir():
        paths = [
            candidate
            for candidate in sorted(target.rglob(_LEDGER_GLOB), key=lambda item: str(item).lower())
            if candidate.is_file() and _resolved_path(candidate) != excluded_path
        ]
        if paths or allow_missing:
            return paths
        raise FileNotFoundError(f"No ledger JSONL files were found under: {target}")

    if excluded_path is not None and _resolved_path(target) == excluded_path:
        if allow_missing:
            return []
        raise ValueError("Ledger input and output paths must differ")
    return [target]


def iter_ledger_records(path: str | Path, *, allow_missing: bool = False) -> Iterable[dict[str, Any]]:
    """Yield parsed JSON records from one ledger file or a ledger directory."""

    for ledger_path in ledger_input_paths(path, allow_missing=allow_missing):
        for line in ledger_path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                yield record


def shard_ledger_path(
    base_dir: str | Path,
    *,
    channel: str,
    operation: str,
    shard_by: str = "channel",
) -> Path:
    """Return the target shard path for one collection result."""

    if shard_by not in _SHARD_CHOICES:
        choices = ", ".join(sorted(_SHARD_CHOICES))
        raise ValueError(f"Unsupported shard_by value: {shard_by}. Expected one of: {choices}")

    root = Path(base_dir)
    if shard_by == "channel":
        filename = f"{channel}.jsonl"
    elif shard_by == "operation":
        filename = f"{operation}.jsonl"
    else:
        filename = f"{channel}__{operation}.jsonl"
    return root / filename


def save_collection_result_sharded(
    base_dir: str | Path,
    result: CollectionResult,
    *,
    run_id: str,
    shard_by: str = "channel",
    input_value: str | None = None,
    intent: str | None = None,
    query_id: str | None = None,
    source_role: str | None = None,
) -> tuple[EvidenceLedgerRecord, Path]:
    """Save a collection result into a sharded ledger directory."""

    record = build_ledger_record(
        result,
        run_id=run_id,
        input_value=input_value,
        intent=intent,
        query_id=query_id,
        source_role=source_role,
    )
    shard_path = shard_ledger_path(
        base_dir,
        channel=record["channel"],
        operation=record["operation"],
        shard_by=shard_by,
    )
    append_ledger_record(shard_path, record)
    return record, shard_path


def merge_ledger_inputs(
    input_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    """Merge one ledger file or a directory of ledger shards into one JSONL output."""

    source = Path(input_path)
    destination = Path(output_path)
    if _resolved_path(source) == _resolved_path(destination):
        raise ValueError("Ledger input and output paths must differ")

    inputs = ledger_input_paths(source, exclude=destination)
    _ensure_parent_dir(destination)

    records_written = 0
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for ledger_path in inputs:
            for line in ledger_path.read_text(encoding="utf-8-sig").splitlines():
                if not line.strip():
                    continue
                handle.write(line.rstrip("\n"))
                handle.write("\n")
                records_written += 1

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "command": "ledger merge",
        "input": str(source),
        "output": str(destination),
        "files_merged": len(inputs),
        "records_written": records_written,
        "inputs": [str(path) for path in inputs],
    }


def validate_ledger_input(input_path: str | Path) -> dict[str, Any]:
    """Validate one evidence ledger file or a directory of ledger shards."""

    source = Path(input_path)
    inputs = ledger_input_paths(source)
    records = 0
    collection_results = 0
    items_seen = 0
    empty_lines = 0
    invalid_line_count = 0
    invalid_record_count = 0
    invalid_lines: list[dict[str, Any]] = []
    invalid_records: list[dict[str, Any]] = []
    large_text_fields: list[dict[str, Any]] = []

    for ledger_path in inputs:
        for line_number, line in enumerate(ledger_path.read_text(encoding="utf-8-sig").splitlines(), start=1):
            if not line.strip():
                empty_lines += 1
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                invalid_line_count += 1
                if len(invalid_lines) < _DIAGNOSTIC_LIMIT:
                    invalid_lines.append(
                        {
                            "file": str(ledger_path),
                            "line": line_number,
                            "error": exc.msg,
                        }
                    )
                continue
            records += 1
            if not isinstance(record, dict):
                invalid_record_count += 1
                if len(invalid_records) < _DIAGNOSTIC_LIMIT:
                    invalid_records.append(
                        {
                            "file": str(ledger_path),
                            "line": line_number,
                            "error": "record must be a JSON object",
                        }
                    )
                continue
            result_payload = record.get("result")
            if record.get("record_type") != "collection_result" or not _is_collection_result(result_payload):
                invalid_record_count += 1
                if len(invalid_records) < _DIAGNOSTIC_LIMIT:
                    invalid_records.append(
                        {
                            "file": str(ledger_path),
                            "line": line_number,
                            "error": "record must be a collection_result with a valid result envelope",
                        }
                    )
                continue
            result = cast(dict[str, Any], result_payload)
            collection_results += 1
            items = result.get("items") or []
            items_seen += len(items)
            for item in items:
                if not isinstance(item, dict):
                    continue
                text = item.get("text")
                if isinstance(text, str) and len(text) > _LARGE_TEXT_CHARS:
                    large_text_fields.append(
                        {
                            "file": str(ledger_path),
                            "line": line_number,
                            "item_id": item.get("id"),
                            "text_length": len(text),
                        }
                    )

    valid = invalid_line_count == 0 and invalid_record_count == 0
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "command": "ledger validate",
        "input": str(source),
        "valid": valid,
        "files_checked": len(inputs),
        "records": records,
        "collection_results": collection_results,
        "items_seen": items_seen,
        "empty_lines": empty_lines,
        "invalid_lines": invalid_line_count,
        "invalid_line_samples": invalid_lines,
        "invalid_records": invalid_record_count,
        "invalid_record_samples": invalid_records,
        "large_text_threshold": _LARGE_TEXT_CHARS,
        "large_text_fields": large_text_fields,
    }


def append_result_json(
    input_path: str | Path,
    output_path: str | Path,
    *,
    run_id: str,
    intent: str | None = None,
    query_id: str | None = None,
    source_role: str | None = None,
) -> dict[str, Any]:
    """Append an already-saved CollectionResult JSON file to an evidence ledger."""

    source = Path(input_path)
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(f"CollectionResult input does not exist: {source}")
    try:
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"CollectionResult input is not valid JSON: {exc.msg}") from exc
    if not _is_collection_result(payload):
        raise ValueError("Input JSON must be a CollectionResult envelope")

    record = save_collection_result(
        output_path,
        payload,
        run_id=run_id,
        intent=intent,
        query_id=query_id,
        source_role=source_role,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "command": "ledger append",
        "input": str(source),
        "output": str(output_path),
        "record_type": record["record_type"],
        "run_id": record["run_id"],
        "channel": record["channel"],
        "operation": record["operation"],
        "ok": record["ok"],
        "count": record["count"],
        "item_ids": record["item_ids"],
        "urls": record["urls"],
        "intent": record["intent"],
        "query_id": record["query_id"],
        "source_role": record["source_role"],
    }


def _is_collection_result(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if not isinstance(value.get("channel"), str):
        return False
    if not isinstance(value.get("operation"), str):
        return False
    if not isinstance(value.get("ok"), bool):
        return False
    if not isinstance(value.get("items"), list):
        return False
    if not isinstance(value.get("meta"), dict):
        return False
    if "error" not in value:
        return False
    return True


def _ensure_parent_dir(path: Path) -> None:
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)


def _resolved_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    return Path(path).resolve()
