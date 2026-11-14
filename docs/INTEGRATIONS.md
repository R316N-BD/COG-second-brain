# COG integrations and local recall

After initialization, create Markdown notes in your separate vault (not the framework checkout). Then run these from the framework directory:

    py -3.12 -m cog_core memory-index
    py -3.12 -m cog_core recall "Hermes gateway" --scope 04-projects
    py -3.12 -m cog_core integrations

On macOS/Linux substitute python3. The SQLite FTS5 database is a rebuildable local index, not a source of truth. It contains full indexed note text and is not encrypted. Keep it private and do not sync it across devices. Rebuild after deleting or editing notes; old bytes may remain in the SQLite file. Rebuilding is explicit, not automatic. Files over 2 MiB, non-UTF-8 files, hidden paths and symbolic links are excluded. Search uses literal keywords, not semantic embeddings. Scope is a filter, not an access control mechanism.

## Integration plan

| Layer | Integration | Proposed next step |
|---|---|---|
| Knowledge | Obsidian | Open separate vault directly; explicit index rebuild |
| Agents | Hermes / OpenClaw | Scoped read-only MCP tools; per-agent identity |
| Models | Ollama | Opt-in local inference endpoint |
| Coding | GitHub / Codex / Claude Code | Read-only project status, review-gated writes |
| Security | AEGIS | Read-only event ingestion, redact sensitive fields |
| Messaging | Telegram | Existing Hermes gateway; authenticated commands |
| Scheduling | Windows Task Scheduler | Explicitly opt-in local recurring jobs |
| Network | Tailscale | Private authenticated workers; no public listener |
| Sync | Syncthing | Markdown only; resolve conflicts before indexing |
| Automation | n8n / Home Assistant | Approved actions with narrow permissions |
| Productivity | Email / calendar | Read-only retrieval before draft and write approval |

See integrations/hermes/COG-RECALL.md for a manual local recall recipe. Nothing is auto-connected by discovery. Native permissions, authentication, actual MCP server, durable approvals, automated scheduling and desktop UI are future work.
