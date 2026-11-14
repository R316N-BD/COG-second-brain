"""Discovery and planning only; never authenticate or launch third-party services."""
import shutil

CATALOG = (
    ("hermes", "Hermes Agent", "hermes", "agent runtime", "scoped search adapter"),
    ("ollama", "Ollama", "ollama", "local model runtime", "local inference adapter"),
    ("git", "Git", "git", "version control", "native update preview"),
    ("github", "GitHub CLI", "gh", "repository intelligence", "read-only project summaries"),
    ("codex", "Codex", "codex", "coding agent", "review and coding workflow"),
    ("claude", "Claude Code", "claude", "coding agent", "review and coding workflow"),
    ("obsidian", "Obsidian", "obsidian", "knowledge editor", "open the separate vault manually"),
    ("mcp", "MCP", None, "tool protocol", "scoped authenticated server"),
    ("telegram", "Telegram", None, "remote messaging", "Hermes gateway adapter"),
    ("aegis", "AEGIS", None, "security monitoring", "read-only audit event adapter"),
    ("tailscale", "Tailscale", "tailscale", "private network", "authenticated remote workers"),
    ("syncthing", "Syncthing", "syncthing", "file synchronization", "vault only; never live SQLite"),
    ("openclaw", "OpenClaw", "openclaw", "agent runtime", "scoped search adapter"),
    ("n8n", "n8n", "n8n", "workflow automation", "approved workflow adapter"),
    ("home-assistant", "Home Assistant", None, "smart home", "explicitly approved control"),
    ("calendar", "Calendar", None, "scheduling", "read-only events first"),
    ("email", "Email", None, "communications", "read-only and draft-first"),
)

def discover():
    result = []
    for key, name, executable, role, next_step in CATALOG:
        path = shutil.which(executable) if executable else None
        result.append({"id": key, "name": name, "role": role,
                       "executable": path, "status": ("detected" if path else
                       "not_on_path" if executable else "manual_configuration"),
                       "connected": False, "next_step": next_step})
    return {"integrations": result,
            "notice": "Executable discovery only. No service has been connected or authenticated."}
