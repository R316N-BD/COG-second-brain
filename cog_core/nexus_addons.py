"""Owner-invoked Hermes-first utilities; no new agent runtime or remote listener.

The functions are intentionally separate from the MCP server. They do not grant
restricted agents an execution channel, automatically route private data to the
cloud, or claim to enforce AEGIS policy.
"""
from __future__ import annotations
import argparse
from collections import Counter
from getpass import getpass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
from urllib.parse import urlsplit

MAX_EVENTS = 10000
MAX_JSON = 8 * 1024 * 1024
ENTITY = re.compile(r"[a-z][a-z0-9_]*\.[a-z0-9_]+")
KNOWN_EVENTS = {"network-connection", "tool-call", "file-access", "configuration-change", "process-start", "policy-denial", "approval", "agent-start", "agent-stop", "error"}
KNOWN_SEVERITIES = {"critical", "high", "medium", "low", "info", "warning", "unknown"}
WINDOWS_APPS = {"calculator": "calc.exe", "notepad": "notepad.exe"}


def recommendation(privacy: str, local_ready: bool, offline: bool = False) -> dict:
    if privacy not in {"public", "private", "restricted"}:
        raise ValueError("Unknown privacy class.")
    if offline or privacy != "public":
        route = "local-only" if local_ready else "blocked"
    else:
        route = "hermes-configured-provider"
    return {"route": route, "privacy": privacy, "local_ready": local_ready,
            "automatic_switch": False, "automatic_cloud_fallback": False,
            "notice": "Recommendation only. Hermes owns the actual provider and its settings."}


def summarize_aegis(path: Path) -> dict:
    """Aggregate a bounded local export without returning messages, paths or secrets."""
    with Path(path).open("rb") as handle:
        raw = handle.read(MAX_JSON + 1)
    if len(raw) > MAX_JSON:
        raise ValueError("Audit export exceeds 8 MiB.")
    doc = json.loads(raw)
    rows = doc if isinstance(doc, list) else doc.get("events") if isinstance(doc, dict) else None
    if not isinstance(rows, list) or len(rows) > MAX_EVENTS:
        raise ValueError("Expected a JSON event array (or events member), at most 10,000 entries.")
    types, levels = Counter(), Counter()
    invalid = 0
    for row in rows:
        if not isinstance(row, dict):
            invalid += 1
            continue
        kind, level = row.get("type"), row.get("severity")
        kind = kind.lower() if isinstance(kind, str) else "unknown"
        level = level.lower() if isinstance(level, str) else "unknown"
        types[kind if kind in KNOWN_EVENTS else "other"] += 1
        levels[level if level in KNOWN_SEVERITIES else "unknown"] += 1
    return {"events": len(rows), "invalid": invalid, "types": dict(types), "severity": dict(levels),
            "notice": "Offline aggregate only; not live AEGIS monitoring, threat detection or enforcement."}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def home_state(base: str, entity: str, token: str, *, opener=None) -> dict:
    """Read one entity through an explicitly configured loopback HA endpoint/tunnel."""
    url = urlsplit(base)
    if (url.scheme not in {"http", "https"} or url.hostname != "127.0.0.1"
            or url.username or url.password or url.query or url.fragment
            or url.path not in ("", "/") or not url.port):
        raise ValueError("Use an explicit loopback Home Assistant URL or local tunnel.")
    if not ENTITY.fullmatch(entity) or len(entity) > 160:
        raise ValueError("Invalid entity ID.")
    if not token or len(token) > 4096 or any(c.isspace() for c in token):
        raise ValueError("A valid access token is required.")
    opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    req = urllib.request.Request(f"{url.scheme}://127.0.0.1:{url.port}/api/states/{entity}",
                                 headers={"Authorization": "Bearer " + token, "Accept": "application/json"}, method="GET")
    try:
        with opener.open(req, timeout=5) as response:
            raw = response.read(65537)
    except Exception:
        raise ValueError("Home Assistant read failed; check the configured local endpoint and credentials.") from None
    if len(raw) > 65536:
        raise ValueError("Home Assistant response exceeds limit.")
    doc = json.loads(raw)
    if not isinstance(doc, dict) or doc.get("entity_id") != entity or not isinstance(doc.get("state"), str):
        raise ValueError("Unexpected Home Assistant response.")
    return {"entity_id": entity, "state": doc["state"][:200], "read_only": True}


def windows_launch(app: str, confirmation: str) -> dict:
    """Fixed native applications only. No arbitrary path, arguments or shell."""
    if app not in WINDOWS_APPS or confirmation != f"LAUNCH {app}":
        raise ValueError("Exact owner confirmation is required.")
    if os.name != "nt":
        raise ValueError("This command requires Windows.")
    system = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    path = system / WINDOWS_APPS[app]
    if not path.is_file():
        raise ValueError("Requested Windows application is unavailable.")
    proc = subprocess.Popen([str(path)], shell=False)
    return {"requested": app, "pid": proc.pid, "notice": "Launch requested; no further computer control."}


def local_transcribe(audio: Path, model: Path) -> dict:
    """Explicit audio-file transcription; preinstalled model only, no auto download."""
    audio, model = Path(audio).resolve(strict=True), Path(model).resolve(strict=True)
    if not audio.is_file() or audio.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("Select an audio file up to 32 MiB.")
    if not model.is_dir() or not (model / "model.bin").is_file():
        raise ValueError("Select an already-installed local CTranslate2 Whisper model directory.")
    from faster_whisper import WhisperModel
    worker = WhisperModel(str(model), device="cpu", compute_type="int8", local_files_only=True)
    segments, _ = worker.transcribe(str(audio), beam_size=1, vad_filter=False)
    output = []
    count = 0
    for seg in segments:
        count += len(seg.text)
        if count > 20000 or seg.end > 600:
            raise ValueError("Transcript exceeds the 10-minute / 20,000-character limit.")
        output.append(seg.text.strip())
    return {"text": " ".join(output), "local": True, "notice": "Explicit file only; no microphone or wake-word listener."}


def speak_windows(text: str) -> dict:
    if os.name != "nt":
        raise ValueError("Windows speech requires Windows.")
    if not isinstance(text, str) or not 1 <= len(text) <= 1000:
        raise ValueError("Speech text must contain 1–1000 characters.")
    import win32com.client
    # SVSFIsNotXML prevents text from being interpreted as SAPI XML/markup.
    voice = win32com.client.Dispatch("SAPI.SpVoice")
    voice.Speak(text, 16)
    return {"spoken": True, "local": True}


def inventory() -> dict:
    from .paths import ROOT
    doc = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    return {"skills": [{"name": x["name"], "description": x.get("description", "")}
                        for x in doc["skills"]],
            "notice": "Source skill inventory. Use Hermes Bot Mode to manage live profiles and skills."}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="command", required=True)
    route = s.add_parser("model-route")
    route.add_argument("privacy", choices=("public", "private", "restricted"))
    route.add_argument("--local-ready", action="store_true")
    route.add_argument("--offline", action="store_true")
    audit = s.add_parser("aegis-summary")
    audit.add_argument("file", type=Path)
    ha = s.add_parser("home-state")
    ha.add_argument("entity")
    ha.add_argument("--url", default="http://127.0.0.1:8123")
    app = s.add_parser("windows-launch")
    app.add_argument("app", choices=tuple(WINDOWS_APPS))
    audio = s.add_parser("transcribe")
    audio.add_argument("file", type=Path)
    audio.add_argument("--model-dir", type=Path, required=True)
    voice = s.add_parser("speak")
    voice.add_argument("text")
    s.add_parser("skills")
    a = p.parse_args(argv)
    try:
        if a.command == "model-route":
            result = recommendation(a.privacy, a.local_ready, a.offline)
        elif a.command == "aegis-summary":
            result = summarize_aegis(a.file)
        elif a.command == "home-state":
            result = home_state(a.url, a.entity, getpass("Home Assistant token: "))
        elif a.command == "windows-launch":
            if not sys.stdin.isatty():
                raise ValueError("Run interactively as the local operator.")
            result = windows_launch(a.app, input(f"Type LAUNCH {a.app} to confirm: "))
        elif a.command == "transcribe":
            result = local_transcribe(a.file, a.model_dir)
        elif a.command == "speak":
            result = speak_windows(a.text)
        else:
            result = inventory()
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0
    except (ValueError, OSError, ImportError, subprocess.SubprocessError) as exc:
        print(f"Nexus add-on: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
