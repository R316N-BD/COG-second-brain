# COG fork: security and operations

The framework repository is public. Keep personal notes in ignored directories or a separate private vault. Ignore rules do not remove previously tracked data. Inspect staged changes; rotate any exposed secrets. Cloud AI, sync and integrations may receive data. Treat notes and web content as untrusted input, not tool instructions.

## Safe updates

Use Bash on Linux, macOS, Windows Git Bash or WSL with Git and Python 3. The updater rejects an unexpected upstream URL and a dirty checkout, stages individual files before replacement, retains backups and returns nonzero on validation failure. It is not transactional: restore reviewed backups or use Git to recover a partial update.

Run:
```sh
bash cog-update.sh --dry-run
bash cog-update.sh
bash scripts/validate-agent-surface.sh
python3 -m unittest discover -s tests -v
```

Fork-owned README, SETUP, .gitignore, updater, checkpoint recorder, validator and mirror-builder are excluded from automatic overwrites. Review upstream changes manually. Stage only reviewed framework files.

Checkpoint validation is not a permission sandbox or tamper-proof audit ledger. Enforce read-only verifier access using runtime permissions. Require approval for destructive changes, external publishing and access to credentials.

Next: Hermes adapter against a pinned runtime version, permission-controlled vault search, staged memory writes, and dashboard. These are not shipped yet.
