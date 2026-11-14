"""Durable proposals, job registry and audit events. No automatic execution."""
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import uuid
from .paths import checked_child, private_path, note_path

def now():
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def store(data_dir):
    root = private_path(data_dir)
    db = checked_child(root, "runtime/operations.sqlite3")
    with closing(sqlite3.connect(db, timeout=10)) as conn, conn:
        conn.row_factory = sqlite3.Row
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            raise ValueError("Unsupported operations database schema.")
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS proposals(
            id TEXT PRIMARY KEY, agent TEXT NOT NULL, path TEXT NOT NULL,
            body TEXT NOT NULL, digest TEXT NOT NULL, status TEXT NOT NULL,
            created TEXT NOT NULL, decided TEXT);
        CREATE TABLE IF NOT EXISTS jobs(
            id TEXT PRIMARY KEY, title TEXT NOT NULL, agent TEXT NOT NULL,
            status TEXT NOT NULL, created TEXT NOT NULL, updated TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(
            id INTEGER PRIMARY KEY, time TEXT NOT NULL, actor TEXT NOT NULL,
            action TEXT NOT NULL, target TEXT NOT NULL, outcome TEXT NOT NULL);
        PRAGMA user_version=1;
        """)
        yield conn

def _audit(conn, actor, action, target, outcome):
    conn.execute("INSERT INTO audit(time,actor,action,target,outcome) VALUES(?,?,?,?,?)",
                 (now(), actor, action, target, outcome))

def record(data_dir, actor, action, target, outcome):
    with store(data_dir) as conn:
        _audit(conn, actor, action, target, outcome)

def propose(data_dir, profile, relative, body):
    profile.require("propose", relative.split("/")[0])
    note_path(data_dir, relative)
    if not isinstance(body, str) or not body.strip() or len(body.encode("utf-8")) > 128 * 1024:
        raise ValueError("Proposal must contain 1–131072 UTF-8 bytes.")
    ident = uuid.uuid4().hex
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    with store(data_dir) as conn:
        conn.execute("INSERT INTO proposals VALUES(?,?,?,?,?,?,?,NULL)",
                     (ident, profile.name, relative, body, digest, "pending", now()))
        _audit(conn, profile.name, "propose", ident, "pending")
    return {"id": ident, "status": "pending", "sha256": digest}

def proposals(data_dir, ident=None):
    with store(data_dir) as conn:
        if ident:
            row = conn.execute("SELECT * FROM proposals WHERE id=?", (ident,)).fetchone()
            if row is None:
                raise ValueError("Unknown proposal.")
            return dict(row)
        return [dict(row) for row in conn.execute(
            "SELECT id,agent,path,digest,status,created,decided FROM proposals ORDER BY created DESC LIMIT 200")]

def decide(data_dir, ident, digest, approve):
    # Local operator only. This records a decision, never writes a note.
    with store(data_dir) as conn:
        status = "approved" if approve else "rejected"
        cur = conn.execute("UPDATE proposals SET status=?,decided=? WHERE id=? AND digest=? AND status='pending'",
                           (status, now(), ident, digest))
        if cur.rowcount != 1:
            raise ValueError("Proposal missing, already decided, or digest mismatch.")
        _audit(conn, "local-operator", "decide", ident, status)
    return {"id": ident, "status": status, "note": "No file mutation performed."}

def create_job(data_dir, title, agent):
    if not title.strip() or len(title) > 300 or not agent.strip() or len(agent) > 64:
        raise ValueError("Invalid job title or agent.")
    ident = uuid.uuid4().hex
    with store(data_dir) as conn:
        stamp = now()
        conn.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?)", (ident, title, agent, "queued", stamp, stamp))
        _audit(conn, "local-operator", "job-create", ident, "queued")
    return {"id": ident, "status": "queued"}

def list_jobs(data_dir):
    with store(data_dir) as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM jobs ORDER BY created DESC LIMIT 200")]

def job_transition(data_dir, ident, status):
    transitions = {"queued": {"running", "cancelled"}, "running": {"completed", "failed", "cancelled"},
                   "failed": {"queued"}}
    with store(data_dir) as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT status FROM jobs WHERE id=?", (ident,)).fetchone()
        if row is None or status not in transitions.get(row["status"], set()):
            raise ValueError("Invalid job transition.")
        conn.execute("UPDATE jobs SET status=?,updated=? WHERE id=?", (status, now(), ident))
        _audit(conn, "local-operator", "job-transition", ident, status)
    return {"id": ident, "status": status}

def audit_events(data_dir):
    with store(data_dir) as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 200")]
