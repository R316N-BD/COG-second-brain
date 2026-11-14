# COG gateway (development)

Run from the framework checkout:

    py -3.12 -m cog_core init
    py -3.12 -m cog_core memory-index
    py -3.12 -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements-mcp.txt

The optional MCP server exposes search, read-note, memory proposal, project listing and skill listing over stdio. The operator chooses a profile when launching it. No network listener or credentials are installed.

Example Hermes MCP configuration (merge manually; use your actual absolute paths and the installed Hermes version's configuration format):

    mcp_servers:
      cog:
        command: 'C:\Projects\COG-second-brain\.venv\Scripts\python.exe'
        args:
          - '-m'
          - 'cog_core.mcp_server'
          - '--profile'
          - 'hermes-research'
        cwd: 'C:\Projects\COG-second-brain'

If the client does not support cwd, launch through a trusted wrapper that changes to the framework checkout first. The default data path is LOCALAPPDATA\COG. A custom path can be supplied with --data-dir before --profile.

Profiles live in config/agents.json under the separate data directory. Existing profiles are preserved. The defaults permit research to read 05-knowledge, developers to read 04-projects, and verifiers to read 04-projects. Calls enforce the selected profile's capability and scope, reload policies each time, and suppress stale search snapshots. A process running under the same OS account with unrestricted shell/filesystem access can bypass these application checks; this is not an OS sandbox or remote authentication. Do not give restricted agents unrestricted shell access or access to the database or profile configuration.

Proposals are durable, hashed, and reviewable locally:

    py -3.12 -m cog_core proposals
    py -3.12 -m cog_core proposal-show ID
    py -3.12 -m cog_core proposal-decide ID SHA256 approve

Approval records a decision only; it does not write notes. Job commands maintain a durable registry and explicit status transitions, not an automatic executor:

    py -3.12 -m cog_core job-create "Review project" --agent hermes-developer
    py -3.12 -m cog_core jobs
    py -3.12 -m cog_core audit

Audit events are local and editable by the OS account, not tamper-proof. Proposal bodies and search indexes are private but unencrypted. Legacy skills remain unmodified; their routing still requires explicit adaptation.
