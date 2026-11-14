"""Opt-in owner-only semantic retrieval using a local Ollama embedding service.
No automatic network fallback, no agent-facing tool, no cloud model selection.
"""
from contextlib import closing
import hashlib
import json
import math
import re
import sqlite3
import urllib.request
from .paths import private_path, checked_child, note_path, VAULT_FOLDERS
from . import memory

MODELS={"embeddinggemma:latest","nomic-embed-text:latest"}
MAX_NOTES=256
MAX_CHARS=4000
MAX_RESPONSE=4*1024*1024

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

def _embed(model,inputs):
    if model not in MODELS:
        raise ValueError("Select a supported locally installed embedding model.")
    # The user must configure Ollama for local-only operation before opting in.
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    request=urllib.request.Request("http://127.0.0.1:11434/api/embed",
        data=json.dumps({"model":model,"input":inputs,"truncate":False}).encode(),
        headers={"Content-Type":"application/json"},method="POST")
    with opener.open(request,timeout=30) as response:
        raw=response.read(MAX_RESPONSE+1)
    if len(raw)>MAX_RESPONSE:
        raise ValueError("Embedding response exceeds limit.")
    vectors=json.loads(raw).get("embeddings")
    if not isinstance(vectors,list) or len(vectors)!=len(inputs):
        raise ValueError("Invalid embedding response.")
    return [_normalized(v) for v in vectors]

def _normalized(vector):
    if not isinstance(vector,list) or not 1<=len(vector)<=4096 or not all(
            isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) for v in vector):
        raise ValueError("Invalid vector.")
    magnitude=math.sqrt(sum(v*v for v in vector))
    if not math.isfinite(magnitude) or magnitude<=0:
        raise ValueError("Invalid vector magnitude.")
    return [v/magnitude for v in vector]

def _scope(scope):
    if scope not in VAULT_FOLDERS:
        raise ValueError("Explicit vault scope required.")

def _db(data):
    return checked_child(private_path(data),"memory/semantic.sqlite3")

def build(data,scope,model):
    _scope(scope)
    root=private_path(data)
    vault,_=memory._paths(root)
    records=[]
    # Only one requested collection; bounded first-chunk embeddings.
    directory=checked_child(vault,scope)
    for path in memory._notes(directory):
        rel=path.relative_to(vault).as_posix()
        note_path(root,rel)
        with path.open("rb") as handle:
            raw=handle.read(memory.MAX_BYTES+1)
        if len(raw)>memory.MAX_BYTES:
            continue
        try:
            text=raw.decode("utf-8-sig")[:MAX_CHARS]
        except UnicodeDecodeError:
            continue
        if not text.strip():
            continue
        if len(records)>=MAX_NOTES:
            raise ValueError("Scope exceeds 256 eligible notes; narrow the collection before indexing.")
        records.append((rel,hashlib.sha256(raw).hexdigest(),text))
    indexed=[]
    for i in range(0,len(records),8):
        batch=records[i:i+8]
        vectors=_embed(model,[r[2] for r in batch])
        indexed.extend((scope,model,rel,digest,json.dumps(vec)) for (rel,digest,_),vec in zip(batch,vectors))
    with closing(sqlite3.connect(_db(root),timeout=10)) as conn,conn:
        conn.execute("CREATE TABLE IF NOT EXISTS vectors(scope TEXT, model TEXT, path TEXT, sha TEXT, vector TEXT, PRIMARY KEY(scope,model,path))")
        conn.execute("DELETE FROM vectors WHERE scope=? AND model=?",(scope,model))
        conn.executemany("INSERT INTO vectors VALUES(?,?,?,?,?)",indexed)
    return {"scope":scope,"model":model,"indexed":len(indexed),"notice":"Only the first 4000 characters of each eligible note are embedded."}

def search(data,scope,model,query,limit=10):
    _scope(scope)
    if not 1<=limit<=20 or not isinstance(query,str) or not query.strip() or len(query)>1000:
        raise ValueError("Invalid search query or limit.")
    root=private_path(data)
    db=_db(root)
    if not db.is_file():
        raise ValueError("Build the semantic index first.")
    query_vector=_embed(model,[query])[0]
    with closing(sqlite3.connect(db.as_uri()+"?mode=ro",uri=True)) as conn:
        rows=conn.execute("SELECT path,sha,vector FROM vectors WHERE scope=? AND model=?",(scope,model)).fetchall()
    scores=[]
    for rel,digest,encoded in rows:
        try:
            path=note_path(root,rel)
            with path.open("rb") as handle:
                raw=handle.read(memory.MAX_BYTES+1)
            if len(raw)>memory.MAX_BYTES or hashlib.sha256(raw).hexdigest()!=digest:
                continue
            vector=_normalized(json.loads(encoded))
            if len(vector)!=len(query_vector):
                continue
            score=sum(a*b for a,b in zip(vector,query_vector))
            scores.append({"path":rel,"sha256":digest,"score":score})
        except (OSError,ValueError):
            continue
    return {"results":sorted(scores,key=lambda r:r["score"],reverse=True)[:limit],
            "notice":"Semantic similarity, not verified facts; stale notes excluded."}
