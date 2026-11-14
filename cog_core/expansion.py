"""Hermes-first expansion: catalog and bounded owner-only local workflows."""
from contextlib import closing
import json
import sqlite3
import time
import uuid
from pathlib import Path
from .paths import private_path, checked_child
from . import memory, graph, integrations, adapters

CATALOG = Path(__file__).with_name("expansion_catalog.json")
# No arbitrary shell, URLs, model prompts, or device mutations.
ACTIONS = {"index", "graph", "discover", "ollama-models"}

def catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))

def validate_workflow(doc):
    if not isinstance(doc, dict) or set(doc) != {"name", "nodes"}:
        raise ValueError("Expected name and nodes.")
    name, nodes = doc["name"], doc["nodes"]
    if not isinstance(name, str) or not 1 <= len(name) <= 120 or not isinstance(nodes, list) or not 1 <= len(nodes) <= 20:
        raise ValueError("Invalid workflow size.")
    by_id = {}
    for node in nodes:
        if not isinstance(node, dict) or set(node) != {"id","action","after"}:
            raise ValueError("Invalid node.")
        ident, action, deps = node["id"], node["action"], node["after"]
        if not isinstance(ident,str) or not ident.isascii() or not ident.replace("-","").isalnum() or len(ident)>40 or ident in by_id:
            raise ValueError("Invalid or duplicate node id.")
        if not isinstance(action,str) or action not in ACTIONS or not isinstance(deps,list) or not all(isinstance(d,str) for d in deps) or len(set(deps))!=len(deps):
            raise ValueError("Invalid action or dependency.")
        by_id[ident]=node
    ordered=[]
    remaining=set(by_id)
    while remaining:
        ready=sorted(i for i in remaining if set(by_id[i]["after"]) <= set(ordered))
        if not ready:
            raise ValueError("Cycle or unknown dependency.")
        ordered.extend(ready)
        remaining.difference_update(ready)
    return [by_id[i] for i in ordered]

def _db(data):
    root=private_path(data)
    if not checked_child(root,"config/cog.json").is_file():
        raise ValueError("Initialize COG first.")
    db=checked_child(root,"runtime/expansion.sqlite3")
    conn=sqlite3.connect(db,timeout=10)
    conn.row_factory=sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, name TEXT, status TEXT, created REAL, updated REAL, definition TEXT, results TEXT)")
    conn.commit()
    return conn

def run_workflow(data,doc):
    """Explicit local operator run. No agent identities or network server exposed."""
    ordered=validate_workflow(doc)
    root=private_path(data)
    ident=uuid.uuid4().hex
    results=[]
    with closing(_db(root)) as conn:
        # Refuse overlap, including unresolved interrupted runs.
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute("SELECT 1 FROM runs WHERE status='running'").fetchone():
            conn.rollback()
            raise ValueError("Another run is active or needs manual recovery.")
        conn.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?)",
                     (ident,doc["name"],"running",time.time(),time.time(),json.dumps(doc),"[]"))
        conn.commit()
        try:
            for node in ordered:
                action=node["action"]
                if action=="index":
                    result=memory.rebuild(root,incremental=True)
                    summary={k:result[k] for k in ("indexed","unchanged","removed")}
                elif action=="graph":
                    result=graph.build(root)
                    summary={k:len(result[k]) for k in ("nodes","edges","unresolved")}
                elif action=="discover":
                    summary={"count":len(integrations.discover()["integrations"])}
                else:
                    summary={"count":len(adapters.ollama_models()["models"])}
                results.append({"id":node["id"],"action":action,"status":"completed","summary":summary})
                conn.execute("UPDATE runs SET results=?,updated=? WHERE id=?",(json.dumps(results),time.time(),ident))
                conn.commit()
        except Exception:
            conn.execute("UPDATE runs SET status='failed',updated=? WHERE id=?",(time.time(),ident))
            conn.commit()
            raise
        conn.execute("UPDATE runs SET status='completed',updated=? WHERE id=?",(time.time(),ident))
        conn.commit()
    return {"id":ident,"status":"completed","results":results}

def history(data):
    with closing(_db(data)) as conn:
        return [dict(row) for row in conn.execute("SELECT id,name,status,created,updated,results FROM runs ORDER BY created DESC LIMIT 100")]
