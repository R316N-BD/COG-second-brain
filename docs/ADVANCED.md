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
