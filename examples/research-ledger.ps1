# Collect raw evidence and produce a no-model candidate plan.

param(
  [string]$Topic = "AI agent tooling",
  [string]$EvidencePath = ".agent-reach/evidence.jsonl",
  [int]$Limit = 5,
  [string]$RunId = ("research-" + [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ"))
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$EvidenceDir = Split-Path -Parent $EvidencePath
if ($EvidenceDir) {
  New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
}

agent-reach collect --json --save $EvidencePath --run-id $RunId --intent discovery --query-id exa-topic --source-role web_search --channel exa_search --operation search --input $Topic --limit $Limit
agent-reach ledger summarize --input $EvidencePath --json
agent-reach plan candidates --input $EvidencePath --by normalized_url --limit 20 --json
