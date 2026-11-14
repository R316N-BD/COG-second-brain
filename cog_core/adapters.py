"""Explicitly invoked read-only integration adapters."""
import json
import re
import shutil
import subprocess
import urllib.request

def ollama_models():
    # No remote fallback; bypass proxy settings and reject redirects.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open("http://127.0.0.1:11434/api/tags", timeout=3) as response:
        raw = response.read(1024*1024+1)
    if len(raw) > 1024*1024:
        raise ValueError("Ollama response exceeds limit.")
    models = json.loads(raw).get("models", [])
    return {"connected": True, "models": [
        {"name": item.get("name"), "size": item.get("size")}
        for item in models[:200] if isinstance(item, dict)]}

def github_status(repository):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or any(
        part in (".", "..") or part.startswith("-") for part in repository.split("/")
    ):
        raise ValueError("Use a GitHub owner/repository name.")
    executable = shutil.which("gh")
    if not executable:
        raise ValueError("GitHub CLI (gh) is not available.")
    # No shell, no token extraction, and only a fixed read-only command.
    result = subprocess.run([executable, "repo", "view", repository, "--json",
                             "nameWithOwner,description,defaultBranchRef,url,isPrivate,pushedAt"],
                            capture_output=True, text=True, timeout=20, check=True)
    return json.loads(result.stdout)
