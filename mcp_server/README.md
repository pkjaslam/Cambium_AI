# Cambium MCP server

Exposes Cambium's tools to any MCP client (Claude Desktop / Claude Code / Cursor) so the AI can call them
as native tools: `cambium_plan`, `cambium_provision`, `cambium_agents`, `cambium_doctor`, `cambium_grade`,
`cambium_validate`, `cambium_dispatch`, `cambium_fidelity`, `cambium_recall`, `cambium_graph`.

## Install & run
```
pip install "mcp[cli]" PyYAML        # SDK + dep
python -m cambium_mcp.server         # stdio server (from the mcp_server/ dir, or after `pip install -e mcp_server/`)
```
Or packaged: `uvx --from git+https://github.com/pkjaslam/Cambium_AI#subdirectory=mcp_server cambium-mcp`

## Register in Claude (claude_desktop_config.json → mcpServers)
```json
{
  "mcpServers": {
    "cambium": { "command": "python", "args": ["-m", "cambium_mcp.server"] }
  }
}
```
uvx form:
```json
{ "mcpServers": { "cambium": { "command": "uvx", "args": ["cambium-mcp"] } } }
```

## Tools
| Tool | Does |
|---|---|
| `cambium_plan(task)` | which councils/agents + gate plan for any task |
| `cambium_provision(task)` | recommended existing tools/packages (reuse-beats-rebuild) |
| `cambium_agents()` | the live roster |
| `cambium_doctor()` | repo health |
| `cambium_grade()` | self-grade A–F + risk scan |
| `cambium_validate(ledger_csv)` | evidence-ledger check (blocks fake claims) |
| `cambium_dispatch(task)` | literal, copy-ready dispatch script for the routed plan (agents per phase + stop-at-gate lines) |
| `cambium_fidelity(task)` | close-out scorecard: routed vs actually-dispatched agents, phases, gate, learning (advisory) |
| `cambium_recall(query, k)` | semantic recall over Cambium's own curated findings and gate decisions |
| `cambium_graph(query, hops)` | multi-hop concept-graph query (supports/contradicts edges flagged, never auto-resolved) |
