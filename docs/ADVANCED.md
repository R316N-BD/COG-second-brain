# Advanced COG preview

## Incremental index

    py -3.12 -m cog_core memory-index --incremental

The refresh still scans and hashes Markdown files, but rewrites only changed entries, removes deleted/skipped entries, and applies a 256 MiB aggregate decoded source budget. This is not a live watcher or semantic vector engine.

## Encrypted note backup

    py -3.12 -m pip install -r requirements-backup.txt
    py -3.12 -m cog_core backup
    py -3.12 -m cog_core restore "C:\path\snapshot.cogbackup" "C:\path\new-cog-data"

Passphrases are prompted interactively. The archive uses AES-GCM with a scrypt-derived key, randomized salt and nonce, per-note hashes and size limits. It includes Markdown notes only, not configuration, agent profiles, credentials, job history, or databases. Restore requires a new data directory; validate restored content before replacing any active data. The restore is not a transactional replacement of an existing vault.

## Desktop preview

    py -3.12 -m cog_core desktop

Requires Python with Tkinter (standard Windows installer option). The local operator view provides scoped search, incremental indexing, system diagnostics, integration discovery, proposals, jobs and audit records. It is a prototype, not the final Tauri application or permission-isolated remote UI.

## Gateway

See GATEWAY.md for the optional MCP server. Existing skills still need explicit vault-routing adaptations. No third-party integration has been connected automatically. Durable job records do not execute jobs. No automatic scheduling, remote workers, vector embeddings or signed installer is shipped.


## Optional integrations and maintenance

    py -3.12 -m cog_core graph
    py -3.12 -m cog_core ollama-models
    py -3.12 -m cog_core github-status R316N-BD/COG-second-brain
    py -3.12 -m cog_core maintenance index-refresh

Graph output is a local Obsidian-style wiki-link graph, not semantic relationship extraction. Ollama model discovery queries only the loopback API, requires a running local Ollama service, and never sends vault content. GitHub status uses the existing GitHub CLI installation and its configured authentication; it only reads repository metadata. Neither service is installed or authenticated by COG.

Maintenance runs an allowlisted index refresh and records the job outcome. The PowerShell script scripts/run-maintenance.ps1 can be invoked by the local operator or configured manually in Windows Task Scheduler. Do not create multiple overlapping schedules. Crash recovery and persistent automatic scheduling are still planned.

After reviewing a proposal and approving its exact digest, the owner can explicitly create a new note:

    py -3.12 -m cog_core proposal-apply ID SHA256

This checks current agent policy and refuses to overwrite existing notes. Approval alone does not apply anything. A crash between file creation and database commit may require manual reconciliation. Rebuild the index after applying a proposal.
