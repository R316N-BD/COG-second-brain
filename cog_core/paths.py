"""Centralized data location and conservative vault path validation."""
from pathlib import Path, PurePosixPath
import os
import re

ROOT = Path(__file__).resolve().parents[1]
VAULT_FOLDERS = ("00-inbox", "01-daily", "02-personal", "03-professional",
                 "04-projects", "05-knowledge", "06-templates")
DATA_FOLDERS = ("vault", "memory", "logs", "config", "backups", "runtime", "jobs", "agents")

def default_data_dir():
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local") / "COG"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "cog"

def inside(path, parent):
    return path == parent or parent in path.parents

def redirected(path):
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()

def private_path(path, root=ROOT):
    target = Path(path).expanduser().resolve()
    if inside(target, root.resolve()) or inside(root.resolve(), target):
        raise ValueError("Data directory must be separate from framework checkout.")
    if any((p / ".git").exists() for p in (target, *target.parents)):
        raise ValueError("Data directory must not be inside a Git working tree.")
    return target

def checked_child(root, relative):
    root = Path(root).resolve()
    candidate = root
    for part in PurePosixPath(relative).parts:
        if part in ("", ".", "..", "/") or not re.fullmatch(r"[^\\/:*?\"<>|\x00-\x1f]+", part):
            raise ValueError("Unsafe relative path.")
        if part.endswith((" ", ".")) or part.split(".")[0].upper() in {
            "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1,10)),
            *(f"LPT{i}" for i in range(1,10))}:
            raise ValueError("Unsafe Windows path.")
        candidate = candidate / part
        if redirected(candidate) or candidate.resolve() != candidate:
            raise ValueError("Redirected path is not allowed.")
    if not inside(candidate, root) or candidate == root:
        raise ValueError("Unsafe relative path.")
    return candidate

def note_path(data_dir, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Expected a vault-relative Markdown path.")
    parts = relative.split("/")
    if len(parts) < 2 or parts[0] not in VAULT_FOLDERS or any(
        not p or p.startswith(".") for p in parts
    ) or not relative.lower().endswith(".md"):
        raise ValueError("Expected a Markdown note inside a known vault scope.")
    root = private_path(data_dir)
    vault = checked_child(root, "vault")
    return checked_child(vault, relative)
