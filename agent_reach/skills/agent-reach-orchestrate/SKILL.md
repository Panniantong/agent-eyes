---
name: agent-reach-orchestrate
description: Run one-shot in-session research orchestration with Agent Reach. Use when Codex should take a rough or structured research ask, decide whether one intake-only subagent is actually worth using, normalize the ask into an executable brief when needed, inspect live Agent Reach channel and readiness contracts, and begin collection in the same session instead of generating an external prompt.
---

# Agent Reach Orchestrate

Take a rough or structured research ask and move it to actual Agent Reach collection start in the same session.

## Workflow

1. Read [references/intake-and-handoff.md](references/intake-and-handoff.md) to decide whether the ask is already executable.
2. Read [references/subagent-policy.md](references/subagent-policy.md) before spawning any subagent.
3. If intake ambiguity would materially change freshness, sources, geography, or deliverable shape, normalize the ask to the fixed brief contract first.
4. Use [references/orchestration-flow.md](references/orchestration-flow.md) to choose the execution path.
5. Use [references/routing-guides.md](references/routing-guides.md) for source and channel hints that match the task type.
6. Start actual Agent Reach checks and collection in-session. Do not stop at a prompt.

## Execution Rules

- Default to Japanese.
- Keep subagent usage conservative. Use at most one intake-only subagent per user request, and only when delegation is available and the ambiguity would materially change the research route.
- Keep `channels --json`, `doctor --json`, channel choice, collection start, and final synthesis on the main agent.
- Keep lightweight asks lightweight. Default to `agent-reach collect --json`.
- When you name channels in commands or handoffs, use the exact stable names from `agent-reach channels --json`. Do not shorten names such as `exa_search`, `hatena_bookmark`, or `hacker_news`.
- Use pagination or time-window controls only after checking live `operation_contracts`.
- Use evidence ledgers, candidate planning, `batch`, or `scout` only when the user explicitly asks for broad or provenance-heavy research.
- When the request is freshness-sensitive, confirm concrete dates and use absolute dates in the final answer.

## References

- Intake decision and brief handoff: [references/intake-and-handoff.md](references/intake-and-handoff.md)
- Orchestration flow and collection-start rules: [references/orchestration-flow.md](references/orchestration-flow.md)
- Subagent decision policy: [references/subagent-policy.md](references/subagent-policy.md)
- Task-type routing guidance: [references/routing-guides.md](references/routing-guides.md)
- Example runs and edge cases: [references/examples.md](references/examples.md)
