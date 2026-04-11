# Orchestration Flow

## Default Path

1. Determine whether the ask is already executable.
2. If not, shape it into the fixed brief.
3. If channel surface or option support is unclear, run `agent-reach channels --json`.
4. If readiness matters, run `agent-reach doctor --json`.
5. Use `agent-reach doctor --json --probe` only when a live operation check would change the route.
6. Start collection with one or a small number of `agent-reach collect --json` commands using exact stable channel names from `agent-reach channels --json`.
7. Synthesize results with source links and explicit uncertainty notes.

## Narrow Research

Use this for verification, focused lookups, or one clear topic.

- stay on `collect --json`
- avoid evidence ledgers unless the user explicitly wants saved provenance
- prefer one to a few targeted commands

## Broad Research

Use this only when the user explicitly asks for wider coverage or provenance-heavy work.

- start with 2-4 small discovery queries
- save raw envelopes with `--save .agent-reach/evidence.jsonl`
- run `agent-reach ledger summarize --input .agent-reach/evidence.jsonl --json` when downstream automation needs neutral artifact health counts
- run `agent-reach plan candidates --input .agent-reach/evidence.jsonl --by normalized_url --limit 20 --json`
- deep-read only selected URLs
- use `agent-reach batch --plan PLAN.json --validate-only --json` before any saved batch execution

## Collection-Start Guardrails

- inspect live `operation_contracts` before using `page_size`, `max_pages`, `cursor`, `page`, `since`, or `until`
- treat `engagement`, `media_references`, `identifiers`, `extras.source_hints`, `error.category`, social time-window warnings, and extraction hygiene as diagnostics only
- keep channel choice task-driven and live-contract-aware
