# Codex Compatibility

Agent Reach currently optimizes for Windows-based Codex setups.

| Surface | Status | Notes |
| --- | --- | --- |
| Native Windows PowerShell | Supported | Primary target |
| Codex skill install | Supported | Uses `CODEX_HOME/skills` or `~/.codex/skills` |
| Codex plugin manifest | Supported | Repo-local `.codex-plugin/plugin.json` |
| MCP wiring for Exa | Supported | Repo-local `.mcp.json` |
| Python SDK | Supported | `AgentReachClient` is the primary external API |
| Read-only collect CLI | Supported | `agent-reach collect --json` |
| macOS/Linux installer automation | Not first-class | Use `install --safe` for guidance only |
| Full workflow orchestration | Deferred | Scheduling, ranking, and publishing stay downstream |
| Additional channels beyond current six | Deferred | Planned for later phases |
