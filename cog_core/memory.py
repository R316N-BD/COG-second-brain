"""Local, rebuildable full-text index of explicitly initialized vault Markdown."""
from contextlib import closing
import hashlib
from pathlib import Path
import re
import sqlite3

MAX_BYTES = 2 * 1024 * 1024
MAX_FILES = 20000
MAX_TOTAL_BYTES = 256 * 1024 * 1024

def _redirected(path):
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()

def _paths(data_dir):
    # Callers validate data_dir with private_path first.
    target = data_dir.resolve()
    vault, memory = target / "vault", target / "memory"
    if not (target / "config/cog.json").is_file():
        raise ValueError("Initialize COG first.")
    for path in (vault, memory):
        if _redirected(path) or path.resolve() != path or not path.is_dir():
            raise ValueError(f"Unsafe or missing data directory: {path}")
    db = memory / "search.sqlite3"
    if _redirected(db) or db.resolve() != db:
        raise ValueError("Refusing redirected search index.")
    return vault, db

def _notes(vault):
    count = 0
    stack = [vault]
    while stack:
        directory = stack.pop()
        for path in sorted(directory.iterdir()):
            if path.name.startswith(".") or _redirected(path):
                continue
            if path.resolve() != path:
                continue
            if path.is_dir():
                stack.append(path)
            elif path.is_file() and path.suffix.lower() == ".md":
                count += 1
                if count > MAX_FILES:
                    raise ValueError(f"Vault exceeds {MAX_FILES} Markdown files; index unchanged.")
                yield path

def rebuild(data_dir, incremental=False):
    vault, db = _paths(data_dir)
    indexed = 0
    unchanged = 0
    removed = 0
    total_bytes = 0
    seen = set()
    skipped = []
    # On error, rollback preserves the previous index.
    with closing(sqlite3.connect(db, timeout=10)) as conn, conn:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS notes USING fts5(path UNINDEXED, sha256 UNINDEXED, title, body)")
        conn.execute("BEGIN")
        existing = dict(conn.execute("SELECT path, sha256 FROM notes")) if incremental else {}
        if not incremental:
            conn.execute("DELETE FROM notes")
        for path in _notes(vault):
            rel = path.relative_to(vault).as_posix()
            with path.open("rb") as handle:
                raw = handle.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                skipped.append({"path": rel, "reason": "too large"})
                continue
            try:
                body = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                skipped.append({"path": rel, "reason": "not UTF-8"})
                continue
            total_bytes += len(raw)
            if total_bytes > MAX_TOTAL_BYTES:
                raise ValueError("Vault exceeds index byte budget; previous index preserved.")
            digest = hashlib.sha256(raw).hexdigest()
            seen.add(rel)
            if existing.get(rel) == digest:
                unchanged += 1
                continue
            if incremental:
                conn.execute("DELETE FROM notes WHERE path=?", (rel,))
            title = next((line[2:].strip() for line in body.splitlines() if line.startswith("# ")), path.stem)
            conn.execute("INSERT INTO notes(path,sha256,title,body) VALUES (?,?,?,?)",
                         (rel, digest, title[:300], body))
            indexed += 1
        for rel in existing.keys() - seen:
            conn.execute("DELETE FROM notes WHERE path=?", (rel,))
            removed += 1
    return {"indexed": indexed, "unchanged": unchanged, "removed": removed,
            "skipped": skipped, "database": str(db)}

def search(data_dir, query, limit=10, scope=None):
    _, db = _paths(data_dir)
    if not db.is_file():
        raise ValueError("No index. Run memory-index first.")
    if not 1 <= limit <= 50:
        raise ValueError("Limit must be between 1 and 50.")
    if len(query) > 500:
        raise ValueError("Query must be at most 500 characters.")
    tokens = re.findall(r"[^\W_]+", query, re.UNICODE)
    if not tokens:
        raise ValueError("Enter at least one search word.")
    # Treat user input as literal words rather than exposing FTS query syntax.
    expression = " AND ".join('"' + token + '"' for token in tokens[:30])
    where = "notes MATCH ?"
    params = [expression]
    if scope:
        if scope not in ("00-inbox", "01-daily", "02-personal", "03-professional",
                         "04-projects", "05-knowledge", "06-templates"):
            raise ValueError("Unknown vault scope.")
        where += " AND substr(path,1,?) = ?"
        prefix = scope + "/"
        params.extend([len(prefix), prefix])
    params.append(limit)
    # No write access to the index from search.
    uri = db.as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, timeout=10)) as conn:
        rows = conn.execute(
            "SELECT path, sha256, title, snippet(notes,3,'[',']','...',24) "
            f"FROM notes WHERE {where} ORDER BY bm25(notes) LIMIT ?", params).fetchall()
    return {"query": query, "scope": scope, "results": [
        {"path": path, "sha256": sha, "title": title, "snippet": snippet}
        for path, sha, title, snippet in rows],
        "notice": "Local indexed snapshots, not verified facts. Rebuild after editing or deleting notes."}
