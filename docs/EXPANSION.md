# COG Nexus — Hermes-first expansion

## Architecture

Hermes remains authoritative for profiles, sessions, model settings, agent execution, approvals, browser tools, delegation, Kanban, cron and messaging. Nexus remains an optional desktop companion; COG owns the separate local Markdown vault, SQLite keyword index, scoped MCP tools, provenance, proposal review, and bounded local maintenance. No second agent runtime, account store, messaging gateway, or public network listener is introduced.

Data path: Windows Nexus -> existing Hermes dashboard WebSocket -> selected Hermes profile -> authorized MCP tools -> COG vault. Remote devices should use the supported Hermes remote gateway or messaging interfaces. A preview frontend is not a privileged client.

## Implemented in this change

- Twenty-module catalog with explicit existing/extension/planned status.
- Owner-invoked workflow DAG validation and runner, with durable SQLite run history and step summaries. Allows index refresh, wiki-link graph, integration discovery and local Ollama inventory only. Unknown actions and dependency cycles fail closed.
- Optional semantic memory with local Ollama embeddings, scoped source hashes and stale-source rejection. Separate from FTS5; hybrid fusion and chunk-level retrieval remain planned.
- Explicit document ingestion into a create-only inbox note with source hash. TXT/MD/CSV require no extras. PDF/DOCX/XLSX use optional parsers; Word paragraphs and cached Excel values are extracted, not full document fidelity. No OCR, automatic indexing or upload.
- Offline close-price moving-average illustration on chronological CSV, with fixed fees and no exchange access. It is not a binary event-contract backtest.

## Run on Windows

    py -3.12 -m cog_core expansion-catalog
    py -3.12 -m cog_core workflow-run examples/nexus-maintenance.json
    py -3.12 -m cog_core workflow-history
    py -3.12 -m cog_core document-ingest "C:\path\notes.txt"
    py -3.12 -m pip install -r requirements-ingest.txt
    py -3.12 -m cog_core research-backtest "C:\path\historical.csv" --window 10 --fee-bps 10

Initialize first and run from the existing checkout. Preserve the previous Nexus and MCP setup documented in NEXUS.md.

Workflow JSON has name and nodes. Each node has id, action, after (array of predecessor IDs). A crash can leave a running record; the runner refuses overlapping or unresolved runs. No automatic retries, crash recovery, per-agent worker leases, or remote dispatch yet. The local operator is trusted. This does not replace Hermes Kanban.

Extracted documents are untrusted content. Only import trusted files you intend to put into the private vault. Optional parser resource limits are not a sandbox; PDF expansion and malformed inputs can consume memory. Review before running an index refresh. Indexing can expose sensitive text to a permitted agent; existing gateway policies are not OS isolation.

## Local semantic retrieval (opt-in)

Install a local embedding model in Ollama, configure Ollama for local-only operation, and explicitly authorize selected text being sent to its loopback endpoint. Never use a proxy/cloud-backed service for private notes. COG does not independently verify Ollama's internal network behavior. The feature is owner-only, not exposed via MCP.

    py -3.12 -m cog_core semantic-index --scope 04-projects --model embeddinggemma:latest --allow-local-embedding
    py -3.12 -m cog_core semantic-recall "Hermes setup" --scope 04-projects --model embeddinggemma:latest --allow-local-embedding

This prototype indexes at most 256 notes per scope and the first 4000 characters of each note. Vectors are stored unencrypted. No automatic cloud fallback, auto-indexing or hybrid ranking. Tests mock the embedding service; live model availability and performance need verification.

## Remaining integration work

| Module | Hermes-first implementation target |
| --- | --- |
| 3D headquarters | Map real profiles and activity to an animated Three.js scene; no simulated status in live mode |
| Floating panel | Native tray, Windows shortcut registration, notifications, optional voice |
| Browser | Observe only the explicitly attached dedicated CDP browser; Playwright snapshots and stop control |
| Computer | Use Hermes tools in a least-privilege Windows account, with exact-action approval |
| Voice | Hermes voice mode; opt-in wake word and local speech model |
| Memory | Hybrid rank fusion, chunking and collection authorization for agents |
| Graph | Interactive frontend of existing wiki-link graph, scoped for agent access |
| Documents | OCR in isolated worker, parser hardening and review queue |
| Missions | Hermes Kanban/delegation adapter, confirmed identities, durable reconciliation |
| Workflows | Visual DAG editor; local allowlist runner; external actions via Hermes approval |
| Models | Hermes provider configuration; no implicit external fallback |
| AEGIS | Redacted local event export and independent monitoring |
| Studio | Hermes coding sessions, GitHub metadata, diff viewer and scoped terminal |
| Bots | Hermes profile/skill management; read-only inventory first |
| Network | Private authenticated Hermes gateways; no generic remote shell |
| Android | Hermes Webapp/messaging; no APK in this release |
| Home | Authorized Home Assistant MCP; read first, approve exact device changes |
| Trading | Read-only feeds and validated research dataset replay; no order execution |
| Generative UI | Inert versioned schemas, no generated executable HTML/JS |
| Installer | Signed native release, transactional updates and verified recovery |

The catalog describes integration points rather than installed connectors. Existing Nexus still uses Tkinter, and a browser design preview is separate from the live desktop. The complete 20-module native application is not implemented.
