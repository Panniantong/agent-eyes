# Contributing to Agent Reach

Thank you for contributing. This fork is intentionally narrow: Windows-first, Codex-friendly, and focused on external integration surfaces that other projects can depend on.

## Local setup

```powershell
git clone https://github.com/YOUR_USERNAME/Agent-Reach.git
cd Agent-Reach
uv sync --extra dev
```

If you prefer editable installs:

```powershell
uv pip install -e ".[dev]"
```

## Validation commands

Run these before submitting changes:

```powershell
python -m pytest -q
uvx ruff check agent_reach tests
uvx mypy agent_reach
uvx --from build pyproject-build --wheel --sdist
```

If dependencies changed, refresh the lock file too:

```powershell
uv lock
```

## Project direction

Keep contributions aligned with the current fork goals:

- Windows-native install and diagnostics
- machine-readable registry and readiness output
- thin read-only collection via `AgentReachClient` and `agent-reach collect --json`
- downstream integration support for Codex and similar hosts

Avoid reintroducing:

- removed legacy channels
- shell-specific Linux or Bash-first automation
- interactive prompts inside the collection path
- docs that claim this repo owns scheduling, ranking, or publishing

## Adding or changing channels

When you change channel support, update all of the following together:

1. `agent_reach/channels/` metadata and health checks
2. `agent_reach/adapters/` collection implementation
3. tests for channel contract, adapter behavior, and CLI output
4. docs and skill references

Every channel contract must include:

- `name`
- `description`
- `tier`
- `backends`
- `auth_kind`
- `entrypoint_kind`
- `operations`
- `required_commands`
- `host_patterns`
- `example_invocations`
- `supports_probe`
- `install_hints`

## Updating the local install

```powershell
git pull --ff-only
uv tool install . --reinstall
agent-reach doctor --json
```

## Pull requests

- Prefer small, focused changes
- Include tests for new behavior
- Update docs when the public surface changes
- Keep machine-readable outputs stable unless a schema change is deliberate
