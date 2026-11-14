"""Dependency-free COG CLI. Python 3.10+; no Bash required."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import sqlite3
from . import memory, integrations

from .paths import ROOT, VAULT_FOLDERS, DATA_FOLDERS, default_data_dir, private_path, inside
from . import policy, operations
UPSTREAM = "https://github.com/huytieu/COG-second-brain.git"

def init_vault(data_dir, root=ROOT):
    target = private_path(data_dir, root)
    directories = [target / name for name in DATA_FOLDERS]
    directories += [target / "vault" / name for name in VAULT_FOLDERS]
    for path in directories:
        if not inside(path.resolve(), target):
            raise ValueError(f"Refusing redirected data directory: {path}")
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    for path in directories:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Exclusive creation preserves an existing configuration.
    config = target / "config" / "cog.json"
    if config.is_symlink() or not inside(config.resolve(), target):
        raise ValueError("Refusing redirected config file.")
    try:
        with config.open("x", encoding="utf-8") as out:
            json.dump({"schema_version": 1, "vault": str(target / "vault"),
                       "framework": str(root.resolve()), "hermes": {"enabled": False}},
                      out, indent=2)
            out.write("\n")
    except FileExistsError:
        pass
    policy.init_profiles(target)
    return target

def validate(root=ROOT):
    errors, warnings = [], []
    try:
        manifest = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        standard = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
        market = json.loads((root / "marketplace-entry.json").read_text(encoding="utf-8"))
        version = (root / "COG-VERSION").read_text(encoding="utf-8").strip()
        if not version or any(obj.get("version") != version for obj in (manifest, standard, market)):
            errors.append("Version mismatch across manifests.")
        if standard.get("name") != "cog-second-brain" or standard.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
            errors.append("Invalid standard plugin manifest.")
        canonical = root / ".claude/skills"
        mirror = root / "skills"
        def contents(directory):
            return {p.relative_to(directory).as_posix(): p.read_bytes()
                    for p in directory.rglob("*") if p.is_file()}
        if not canonical.is_dir() or not mirror.is_dir() or contents(canonical) != contents(mirror):
            errors.append("Skill mirror differs from canonical skills.")
        shipped = {p.relative_to(root).as_posix() for p in canonical.rglob("SKILL.md")}
        items = manifest["skills"]
        declared = {item["path"] for item in items}
        names = {item["name"] for item in items}
        if shipped != declared or len(items) != len(declared) or len(items) != len(names):
            errors.append("Skill paths or names do not match shipped skills.")
        commands = set(re.findall(r"^### /([^\s]+)", (root / "AGENTS.md").read_text(encoding="utf-8"), re.M))
        for name in sorted(names - commands):
            errors.append(f"Missing command documentation: {name}")
        for item in items:
            if item["path"] != f'.claude/skills/{item["name"]}/SKILL.md':
                errors.append(f'Unexpected manifest path: {item["path"]}')
        for doc in ("README.md", "SETUP.md", "CONTRIBUTING.md", ".github/MARKETPLACE.md"):
            if "agents.md" in (root / doc).read_text(encoding="utf-8"):
                errors.append(f"Incorrect AGENTS.md casing: {doc}")
        for folder, pattern in ((".kiro/powers", "POWER.md"), (".gemini/commands", "*"), (".gemini/skills", "*")):
            count = sum(p.is_file() for p in (root / folder).rglob(pattern))
            if count != 7:
                warnings.append(f"{folder}: expected 7 files, found {count}")
        if not (root / "docs/AGENT-SUPPORT.md").is_file():
            errors.append("Missing docs/AGENT-SUPPORT.md.")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append(f"Cannot validate framework: {exc}")
        version, names = None, set()
    return {"ok": not errors, "version": version, "skills": len(names),
            "errors": errors, "warnings": warnings}

def doctor(data_dir, root=ROOT):
    target = private_path(data_dir, root)
    validation = validate(root)
    return {"platform": platform.platform(), "python": platform.python_version(),
            "git": shutil.which("git"), "hermes": shutil.which("hermes"),
            "ollama": shutil.which("ollama"), "framework": str(root),
            "data_dir": str(target), "vault_initialized": (target / "config/cog.json").is_file(),
            "validation": validation}

def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True, timeout=30).stdout.strip()

def update_preview(root=ROOT, offline=False):
    local = git(root, "rev-parse", "HEAD")
    cached = None
    try:
        cached = git(root, "rev-parse", "--verify", "refs/remotes/cog-upstream/main")
    except subprocess.CalledProcessError:
        pass
    upstream = None
    if not offline:
        result = git(root, "ls-remote", "--exit-code", UPSTREAM, "refs/heads/main")
        upstream = result.split()[0]
        if not re.fullmatch(r"[0-9a-f]{40,64}", upstream):
            raise ValueError("Unexpected upstream response.")
    # A fork's HEAD can differ without having an available update.
    return {"local_head": local, "cached_upstream_head": cached,
            "remote_upstream_head": upstream, "offline": offline,
            "note": "Commit preview only; no files, Git refs or remotes modified. Different heads do not prove an update is available."}

def main(argv=None):
    parser = argparse.ArgumentParser(prog="cog", description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=default_data_dir())
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("init", help="Initialize a separate private data directory.")
    subs.add_parser("doctor", help="Read-only environment and skill diagnostics.")
    subs.add_parser("validate", help="Validate manifests and skill mirror.")
    preview = subs.add_parser("update-preview", help="Read-only upstream commit preview.")
    preview.add_argument("--offline", action="store_true")
    subs.add_parser("memory-index", help="Rebuild local Markdown full-text index.")
    recall = subs.add_parser("recall", help="Search indexed vault notes locally.")
    recall.add_argument("query")
    recall.add_argument("--limit", type=int, default=10)
    recall.add_argument("--scope", choices=VAULT_FOLDERS)
    subs.add_parser("integrations", help="Discover integration executables without connecting.")
    subs.add_parser("vault-path", help="Print private vault location.")
    subs.add_parser("proposals", help="List proposals awaiting review.")
    inspect = subs.add_parser("proposal-show")
    inspect.add_argument("id")
    decision = subs.add_parser("proposal-decide")
    decision.add_argument("id")
    decision.add_argument("sha256")
    decision.add_argument("decision", choices=["approve", "reject"])
    job = subs.add_parser("job-create")
    job.add_argument("title")
    job.add_argument("--agent", required=True)
    subs.add_parser("jobs")
    transition = subs.add_parser("job-transition")
    transition.add_argument("id")
    transition.add_argument("status", choices=["queued", "running", "completed", "failed", "cancelled"])
    subs.add_parser("audit")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = {"data_dir": str(init_vault(args.data_dir)), "initialized": True}
        elif args.command == "doctor":
            result = doctor(args.data_dir)
        elif args.command == "validate":
            result = validate()
        elif args.command == "memory-index":
            result = memory.rebuild(private_path(args.data_dir))
        elif args.command == "recall":
            result = memory.search(private_path(args.data_dir), args.query, args.limit, args.scope)
        elif args.command == "integrations":
            result = integrations.discover()
        elif args.command == "vault-path":
            result = {"vault": str(private_path(args.data_dir) / "vault")}
        elif args.command == "proposals":
            result = {"proposals": operations.proposals(args.data_dir)}
        elif args.command == "proposal-show":
            result = operations.proposals(args.data_dir, args.id)
        elif args.command == "proposal-decide":
            result = operations.decide(args.data_dir, args.id, args.sha256, args.decision == "approve")
        elif args.command == "job-create":
            policy.load_profile(args.data_dir, args.agent)
            result = operations.create_job(args.data_dir, args.title, args.agent)
        elif args.command == "jobs":
            result = {"jobs": operations.list_jobs(args.data_dir)}
        elif args.command == "job-transition":
            result = operations.job_transition(args.data_dir, args.id, args.status)
        elif args.command == "audit":
            result = {"events": operations.audit_events(args.data_dir)}
        else:
            result = update_preview(offline=args.offline)
        print(json.dumps(result, indent=2))
        return 1 if result.get("ok") is False or result.get("validation", {}).get("ok") is False else 0
    except (OSError, ValueError, subprocess.SubprocessError, sqlite3.Error) as exc:
        print(f"COG: {exc}", file=sys.stderr)
        return 1
