# Examples

## Example 1: Narrow Latest-Info Ask

User ask:

```text
Check the latest OpenAI agent-related releases.
```

Good behavior:

- do not use a subagent
- inspect live contracts only as needed
- run a narrow collection path
- report concrete dates in the final answer

## Example 2: Ambiguous Comparison Ask

User ask:

```text
Compare the recent agent features from major labs.
```

Good behavior:

- decide whether the missing comparison scope changes the route
- if delegation is available and helpful, use one intake-only subagent to shape the brief
- integrate that brief immediately
- keep execution on the main agent

## Example 3: OSS Investigation

User ask:

```text
Investigate this GitHub repo properly.
```

Good behavior:

- start with `github` and official docs
- keep the run narrow unless the user explicitly asks for broad coverage
- inspect `operation_contracts` before using pagination
- start collection in-session instead of building a handoff prompt

## Example 4: Broad Research With Provenance

User ask:

```text
Research this broadly and keep an evidence trail I can review later.
```

Good behavior:

- explicitly mark this as a broad run
- include `agent-reach collect --json --save .agent-reach/evidence.jsonl`
- include `agent-reach ledger summarize --input .agent-reach/evidence.jsonl --json`
- include `agent-reach plan candidates --input .agent-reach/evidence.jsonl --by normalized_url --limit 20 --json`
- mention `agent-reach batch --plan PLAN.json --validate-only --json` before any saved batch execution
- still deep-read only selected URLs
