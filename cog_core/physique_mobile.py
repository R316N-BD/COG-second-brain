"""Encrypted, read-only mobile snapshot. No network server, sync or plaintext export."""
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from .paths import private_path, ROOT
from .physique import validate_state, _crypto
from .physique_training import date

ITERATIONS=600_000
AAD=b"cog-physique-mobile-v1"
MAX_BYTES=1_500_000
TEMPLATE=ROOT/"preview"/"physique-mobile.html"

def snapshot(state, days=90, feedback=(), today=None):
    state=validate_state(state)
    if type(days) is not int or not 1<=days<=365:
        raise ValueError("Choose 1–365 days.")
    today=today or dt.date.today()
    start=today-dt.timedelta(days=days-1)
    def recent(rows):
        return sorted((dict(r) for r in rows if start<=date(r["date"])<=today),key=lambda r:r["date"],reverse=True)
    feedback=list(feedback)
    if len(feedback)>40 or any(not isinstance(r,dict) or set(r)!={"role","feedback","review_note"} or
                              not all(isinstance(v,str) and len(v.encode("utf-8"))<=24000 for v in r.values())
                              for r in feedback):
        raise ValueError("Invalid review feedback.")
    return {"version":1,"exported":today.isoformat(),"period_days":days,
            "target_date":state["target_date"],"records":recent(state["records"]),
            "sets":recent(state["sets"]),"milestones":[dict(r) for r in state["milestones"]],
            "feedback":feedback}

def encode_snapshot(data,password):
    if not isinstance(password,str) or not 12<=len(password)<=1024:
        raise ValueError("Choose a separate mobile passphrase of at least 12 characters.")
    payload=json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(",",":")).encode("utf-8")
    if len(payload)>MAX_BYTES:raise ValueError("Snapshot is too large; choose fewer days.")
    salt=os.urandom(16);nonce=os.urandom(12)
    key=hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"),salt,ITERATIONS,dklen=32)
    AESGCM,_,_=_crypto()
    ciphertext=AESGCM(key).encrypt(nonce,payload,AAD)
    return base64.b64encode(salt+nonce+ciphertext).decode("ascii")

def write_snapshot(destination,data,password):
    path=private_path(Path(destination))
    if path.suffix.lower()!=".html":raise ValueError("Choose an HTML file.")
    if not path.parent.is_dir():raise ValueError("Destination folder does not exist.")
    template=TEMPLATE.read_text(encoding="utf-8")
    if template.count("__COG_ENCRYPTED_PAYLOAD__")!=1:raise ValueError("Invalid mobile viewer template.")
    content=template.replace("__COG_ENCRYPTED_PAYLOAD__",encode_snapshot(data,password))
    # Exclusive creation: never overwrite existing files or follow a symlink to an existing file.
    with path.open("x",encoding="utf-8") as handle:
        handle.write(content)
    return path
