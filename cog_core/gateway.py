"""Scoped local gateway, shared by MCP tools and tests."""
import hashlib
from . import memory, operations, policy
from .paths import note_path, private_path, ROOT

class Gateway:
    def __init__(self, data_dir, profile_name):
        self.data = private_path(data_dir)
        self.name = profile_name
        policy.load_profile(self.data, self.name)

    def _profile(self, cap, scope=None):
        # Reload owner-managed policy on every call, including revocations.
        profile = policy.load_profile(self.data, self.name)
        try:
            profile.require(cap, scope)
        except PermissionError:
            operations.record(self.data, self.name, cap, scope or "-", "denied")
            raise
        return profile

    def search(self, query, scope, limit=10):
        self._profile("search", scope)
        if not scope:
            raise PermissionError("Explicit authorized scope required.")
        result = memory.search(self.data, query, limit, scope)
        # Filter stale snapshots before any note contents leave the gateway.
        fresh = []
        for item in result["results"]:
            try:
                path = note_path(self.data, item["path"])
                with path.open("rb") as handle:
                    raw = handle.read(memory.MAX_BYTES + 1)
                if hashlib.sha256(raw).hexdigest() == item["sha256"]:
                    fresh.append(item)
            except (OSError, ValueError):
                continue
        result["results"] = fresh
        operations.record(self.data, self.name, "search", scope, "ok")
        return result

    def read(self, relative):
        self._profile("read", relative.split("/")[0])
        path = note_path(self.data, relative)
        with path.open("rb") as handle:
            raw = handle.read(memory.MAX_BYTES + 1)
        if len(raw) > memory.MAX_BYTES:
            raise ValueError("Note exceeds read limit.")
        result = {"path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                  "content": raw.decode("utf-8-sig")}
        operations.record(self.data, self.name, "read", relative.split("/")[0], "ok")
        return result

    def propose(self, relative, body):
        profile = self._profile("propose", relative.split("/")[0])
        return operations.propose(self.data, profile, relative, body)

    def projects(self):
        self._profile("projects", "04-projects")
        from .paths import checked_child
        root = checked_child(self.data, "vault/04-projects")
        return {"projects": sorted(p.name for p in root.iterdir()
                                    if p.is_dir() and not p.name.startswith(".")
                                    and not p.is_symlink() and p.resolve() == p)[:200]}

    def skills(self):
        self._profile("skills")
        import json
        doc = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        return {"skills": [{"name": s["name"], "description": s.get("description", "")} for s in doc["skills"]]}
