# Changelog

All notable changes to this fork are documented here.

## Unreleased

### Added

- `AgentReachClient` as the primary external Python SDK
- `agent-reach collect --json` as the thin read-only CLI collection surface
- normalized `CollectionResult` and `NormalizedItem` envelopes with backend-native `raw` payloads
- dedicated collection adapters for `web`, `exa_search`, `github`, `youtube`, `rss`, and `twitter`
- Python SDK documentation and external usage examples for bots and CI jobs

### Changed

- positioned the fork around external integration, diagnostics, and read-only collection
- updated Codex integration exports and plugin metadata to include collection guidance
- aligned docs, skill references, and machine-readable channel metadata around supported operations

### Removed

- legacy `watch` command
- legacy Bash-first helper scripts and outdated docs
- legacy skill root discovery for `.claude` and `.openclaw`

## [1.4.0] - 2026-04-10

### Added

- machine-readable channel contracts through `agent-reach channels --json`
- machine-readable diagnostics through `agent-reach doctor --json`
- lightweight live checks through `agent-reach doctor --json --probe`
- non-mutating integration export through `agent-reach export-integration --client codex`
- JSON install preview through `agent-reach install --dry-run --json`
- repo-local `.codex-plugin/plugin.json` and `.mcp.json`

### Changed

- narrowed the supported surface to `web`, `exa_search`, `github`, `youtube`, `rss`, and optional `twitter`
- rewrote the Windows/Codex docs around bootstrap, registry, readiness, and integration flows
