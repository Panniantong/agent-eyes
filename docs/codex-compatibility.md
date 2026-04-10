# Codex Compatibility

Agent Reach currently optimizes for Windows-based Codex setups.

| Surface | Status | Notes |
| --- | --- | --- |
| Native Windows PowerShell | Supported | Primary target |
| Codex skill install | Supported | Uses `CODEX_HOME/skills` or `~/.codex/skills` |
| Codex plugin manifest | Supported | Repo-local in checkouts, inline export in tool installs |
| MCP wiring for Exa | Supported | Repo-local in checkouts, inline export in tool installs |
| Python SDK | Supported | `AgentReachClient` works after install into the caller project environment |
| Read-only collect CLI | Supported | `agent-reach collect --json` |
| macOS/Linux installer automation | Not first-class | Use `install --safe` for guidance only |
| Full workflow orchestration | Deferred | Scheduling, ranking, and publishing stay downstream |
| Additional channels beyond current nine | Deferred | Planned for later phases |
