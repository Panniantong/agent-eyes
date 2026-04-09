# GitHub

Use `gh` for repository discovery, metadata, and code search.

```powershell
agent-reach collect --channel github --operation read --input "owner/repo" --json
agent-reach collect --channel github --operation search --input "agent framework" --limit 10 --json
```

Direct `gh` commands are still useful for debugging:

```powershell
gh repo view owner/repo
gh search repos "agent framework" --sort stars --limit 10
gh search code "useEffectEvent repo:facebook/react"
gh issue list --repo owner/repo --limit 20
```

If `gh auth status` fails, tell the user to run:

```powershell
gh auth login
```
