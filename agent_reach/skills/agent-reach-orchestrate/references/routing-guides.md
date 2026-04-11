# Routing Guides

Choose routing hints that match the task. Do not hard-code unavailable channels; check the live contract first and then start collection in-session.

## Latest-Info Research

- Prefer official announcements, official docs, release notes, vendor blogs, and recent primary-source pages.
- Use community channels only as supporting signals.
- Require concrete dates in the final answer.
- If a channel supports date bounds such as `since` or `until`, choose them from the live contract instead of assuming they exist.

## OSS Or Repository Research

- Start with `github` for repository facts and code search.
- Use `web` for official docs, release notes, and maintainer blog posts.
- Use `hacker_news`, `reddit`, or `bluesky` only when community adoption or reaction is relevant.
- Bias toward repository activity, release cadence, issue or PR patterns, and maintainer-authored material.

## Company Or Product Comparison

- Start with official docs, pricing pages, release notes, and official announcements for each compared item.
- Use `web` for official sites and `github` when a public repo is part of the product story.
- Add community channels only when the user wants market reaction, practitioner feedback, or known pain points.

## Community Reaction Collection

- Use `bluesky`, `reddit`, `hacker_news`, and `twitter` when the request is about public reaction and the configured runtime supports them.
- Pair reaction collection with the relevant official announcement or product page so community discussion has an anchor.
- Ask for `doctor --json --probe` only if the requested reaction channel is operationally important and its readiness is uncertain.

## Documentation Research

- Prefer `web` for docs and release notes.
- Prefer `rss` when the source exposes a feed and the task is about recent updates.
- Keep the run narrow unless the user explicitly wants wide coverage.

## Japanese And English Cross-Market Research

- Default to Japanese output.
- Use both Japanese and English queries for global topics.
- Keep region-specific source preferences explicit in the prompt.
- If the request is local-only, do not add bilingual discovery automatically.

## Broad Research

- Only describe evidence-ledger fan-out when the user explicitly opts into broad or provenance-heavy research.
- In that case:
- start with 2-4 small discovery queries
- save raw envelopes with `--save .agent-reach/evidence.jsonl`
- run `agent-reach plan candidates --input .agent-reach/evidence.jsonl --by url --limit 20 --json`
- deep-read only selected URLs
- use `batch --validate-only` before any saved batch plan execution
