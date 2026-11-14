# COG Nexus — Hermes companion preview

An independent, Herm-inspired Windows-friendly interface. Hermes owns profiles, sessions and execution; COG owns its private Markdown knowledge and proposals.

## Run on Windows

From the development checkout:

    py -3.12 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements-nexus.txt -r requirements-mcp.txt
    .\.venv\Scripts\python.exe -m cog_core init
    .\.venv\Scripts\python.exe -m cog_core nexus

Alternatively run scripts/start-nexus.ps1 explicitly. Python must include Tkinter.

## Connect Hermes

Nexus connects to the authenticated Hermes dashboard WebSocket (/api/ws), not the Telegram messaging gateway. Use a compatible running dashboard on the same machine. Only explicit loopback HTTP endpoints and session-token authentication are supported; no token is written to disk.

If no compatible dashboard is running, and starting one will not interrupt existing work, use the documented command in a separate terminal:

    hermes dashboard --host 127.0.0.1 --port 9119 --no-open

Configure the deployment session token according to the official Hermes dashboard session-token documentation before starting. Do not paste a model API key into Nexus. Use the existing backend and token when available. Never publish the dashboard or CDP port.

Enter the actual URL and dashboard session token in Nexus; click Connect. Profiles are discovered with profiles.list. Live sessions are reported by session.active_list for the selected profile. Sending starts a fresh session with confirmed profile ownership or continues a session created by Nexus. Existing sessions are read-only in this preview. Streamed replies use message.delta and message.complete. Uncertain submissions are not retried automatically. Interrupt requests do not prove the turn stopped; wait for the terminal event. Unsupported server requests are refused, never approved automatically. Use a supported Hermes client for approvals and questions.

The floating panel is always on top and anchored near the right edge. Quick messages use the currently selected profile. The workforce diagram displays actual reported profiles, not invented bot activity; detailed live session status appears below.

## Shared browser

Choose a trusted Hermes profile and click Launch + attach. This opens a separate visible Edge/Chrome/Chromium window with a fresh user-data directory and random loopback DevTools port. The browser.manage RPC attaches that endpoint to the selected Hermes profile. Ask Hermes to use its browser tools from Command. Browser capabilities and action approvals remain Hermes-owned.

This is a separate visible browser window, not embedded video or cursor mirroring. It is not a network sandbox or isolated operating-system account. Do not sign into personal, financial, or sensitive accounts. Attach can replace an existing browser connection for the selected profile; confirm first. Detach explicitly and close the dedicated window when finished. A new attachment requires the previous browser process to be closed; Nexus will not reuse the same browser profile for a different bot. The browser profile may persist on disk; remove it manually after closing. Nexus does not auto-detach or auto-clean on exit.

## Connect COG memory

Initialize and index the private vault, then generate the exact MCP entry:

    .\.venv\Scripts\python.exe -m cog_core memory-index --incremental
    .\.venv\Scripts\python.exe -m cog_core hermes-config --profile hermes-research

Merge the generated mcp_servers entry into the appropriate Hermes profile's config.yaml (JSON is a YAML subset). The absolute launcher works without a specific working directory. The COG profile is separate from the Hermes profile. Enable and test cog_search from Hermes; do not grant unrestricted shell access to a restricted agent. COG notes are not automatically inserted into messages. Local memory search is available from the COG memory tab.

## Generative replies

The composer optionally requests version-1 cog-ui JSON blocks for metrics, tables, bar charts and checklists. Rendering is inert: no generated HTML, scripts, shell commands or automatic actions. Plain replies remain plain text. Only a bounded subset is supported.

## References

The public Hermes contracts and Herm design informed this implementation; no Swift source or branded assets were copied.

- https://github.com/chryzxc/herm/blob/main/ARCHITECTURE.md
- https://github.com/NousResearch/hermes-agent/blob/main/tui_gateway/contracts/sessions.py
- https://github.com/NousResearch/hermes-agent/blob/main/tui_gateway/contracts/tools_commands.py
- https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard
- https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp

Development preview: mock WebSocket tests do not establish live Hermes compatibility, real browser attachment or Windows GUI behavior. No remote gateway, automatic session recovery, existing-session messaging, embedded browser stream, 3D office or approval submission is shipped.
