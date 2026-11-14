"""Owner-managed profile policy. No caller-supplied identity in MCP tools."""
import json
import re
from dataclasses import dataclass
from .paths import VAULT_FOLDERS, checked_child, private_path

CAPABILITIES = frozenset({"search", "read", "propose", "projects", "skills", "health", "jobs"})
DEFAULT_PROFILES = {
    "hermes-research": {"scopes": ["05-knowledge"], "capabilities": ["search", "read", "propose", "skills"]},
    "hermes-developer": {"scopes": ["04-projects"], "capabilities": ["search", "read", "propose", "projects", "skills"]},
    "verifier": {"scopes": ["04-projects"], "capabilities": ["search", "read", "projects"]},
}

@dataclass(frozen=True)
class Profile:
    name: str
    scopes: frozenset
    capabilities: frozenset

    def require(self, capability, scope=None):
        if capability not in self.capabilities or (scope is not None and scope not in self.scopes):
            raise PermissionError("Action or vault scope not authorized.")

def init_profiles(data_dir):
    root = private_path(data_dir)
    path = checked_child(root, "config/agents.json")
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump({"schema_version": 1, "profiles": DEFAULT_PROFILES}, handle, indent=2)
    except FileExistsError:
        pass
    return path

def load_profile(data_dir, name):
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        raise PermissionError("Unknown agent profile.")
    path = checked_child(private_path(data_dir), "config/agents.json")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema_version") != 1:
        raise ValueError("Unsupported profile schema.")
    raw = doc.get("profiles", {}).get(name)
    if not isinstance(raw, dict):
        raise PermissionError("Unknown agent profile.")
    scopes, caps = raw.get("scopes"), raw.get("capabilities")
    if not isinstance(scopes, list) or not isinstance(caps, list) or not all(
        isinstance(s, str) for s in scopes + caps
    ) or not set(scopes) <= set(VAULT_FOLDERS) or not set(caps) <= CAPABILITIES:
        raise ValueError("Invalid agent profile.")
    return Profile(name, frozenset(scopes), frozenset(caps))
