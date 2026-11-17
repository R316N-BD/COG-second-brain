"""Local, opt-in COG Physique workspace. No network, indexing or agent access."""
import argparse
import datetime as dt
import getpass
import json
import math
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .paths import checked_child, default_data_dir, private_path
from . import physique_training as training

MAX_BYTES = 2_000_000
MAGIC = b"COGPHYS1"
AAD = b"cog-physique-v1"
FIELDS = {"date", "weight_kg", "sleep_hours", "training_minutes", "adherence_pct"}

def _crypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
        from cryptography.exceptions import InvalidTag
    except ImportError as exc:
        raise ValueError("Install requirements-physique.txt before opening the vault.") from exc
    return AESGCM, Scrypt, InvalidTag

def _key(password, salt):
    if not isinstance(password, str) or not 12 <= len(password) <= 1024:
        raise ValueError("Use a passphrase of at least 12 characters.")
    _, Scrypt, _ = _crypto()
    return Scrypt(salt=salt, length=32, n=2**15, r=8, p=1).derive(password.encode("utf-8"))

def _date(value):
    if not isinstance(value, str):
        raise ValueError("Date must be YYYY-MM-DD.")
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError:
        raise ValueError("Date must be YYYY-MM-DD.") from None
    if parsed.isoformat() != value:
        raise ValueError("Date must be YYYY-MM-DD.")
    return parsed

def validate_record(record):
    if not isinstance(record, dict) or set(record) != FIELDS:
        raise ValueError("Expected date, weight_kg, sleep_hours, training_minutes, adherence_pct.")
    _date(record["date"])
    for name, low, high in (("weight_kg", 20, 500), ("sleep_hours", 0, 24),
                            ("training_minutes", 0, 1440), ("adherence_pct", 0, 100)):
        value = record[name]
        if value is None:
            continue
        if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError("Invalid " + name)
    if all(record[key] is None for key in FIELDS - {"date"}):
        raise ValueError("Enter at least one observation.")
    return dict(record)

def validate_state(state):
    if not isinstance(state, dict):
        raise ValueError("Unsupported physique vault.")
    if state.get("version")==1 and set(state)=={"version","target_date","records"}:
        state=dict(state,version=2,sets=[],milestones=[])
    if state.get("version")!=2 or set(state)!={"version","target_date","records","sets","milestones"}:
        raise ValueError("Unsupported physique vault.")
    training.validate_collections(state)
    if state["target_date"] is not None:
        _date(state["target_date"])
    records = state["records"]
    if not isinstance(records, list) or len(records) > 10000:
        raise ValueError("Invalid record collection.")
    dates = set()
    for row in records:
        validate_record(row)
        if row["date"] in dates:
            raise ValueError("Duplicate date.")
        dates.add(row["date"])
    return state

def summary(state, today=None):
    state = validate_state(state)
    today = today or dt.date.today()
    rows = sorted(state["records"], key=lambda r:r["date"])
    def average(field, start, end):
        values = [r[field] for r in rows if start <= _date(r["date"]) <= end and r[field] is not None]
        return {"mean": round(sum(values)/len(values), 2) if values else None, "count": len(values)}
    current, previous = today-dt.timedelta(days=6), today-dt.timedelta(days=13)
    metrics = {}
    for field in sorted(FIELDS-{"date"}):
        a = average(field, current, today)
        b = average(field, previous, current-dt.timedelta(days=1))
        metrics[field] = {"last_7_days":a, "prior_7_days":b,
                          "change":round(a["mean"]-b["mean"],2) if a["mean"] is not None and b["mean"] is not None else None}
    target = state["target_date"]
    return {"records":len(rows), "days_until_target":(_date(target)-today).days if target else None,
            "metrics":metrics, "note":"Descriptive observations only; not medical or training prescriptions."}

class Vault:
    """Encrypted file; only the local owner can open it with a passphrase."""
    def __init__(self, data_dir):
        root = private_path(data_dir)
        if not checked_child(root, "config/cog.json").is_file():
            raise ValueError("Initialize COG first.")
        folder = checked_child(root, "physique")
        folder.mkdir(mode=0o700, exist_ok=True)
        self.path = checked_child(root, "physique/records.enc")
        self.lock = checked_child(root, "physique/write.lock")

    @contextmanager
    def exclusive(self):
        try:
            fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise ValueError("Vault is busy or needs manual lock recovery.") from None
        os.close(fd)
        try:
            yield
        finally:
            self.lock.unlink()

    def read(self, password):
        if not self.path.is_file():
            raise ValueError("Create the Physique vault first.")
        with self.path.open("rb") as handle:
            blob = handle.read(MAX_BYTES+1)
        if len(blob)>MAX_BYTES or len(blob)<52 or not blob.startswith(MAGIC):
            raise ValueError("Invalid vault file.")
        salt, nonce = blob[8:24], blob[24:36]
        AESGCM, _, InvalidTag = _crypto()
        try:
            payload = AESGCM(_key(password, salt)).decrypt(nonce, blob[36:], AAD)
            return validate_state(json.loads(payload))
        except (InvalidTag, UnicodeError, json.JSONDecodeError):
            raise ValueError("Incorrect passphrase or damaged vault.") from None

    def _write(self, password, state):
        state = validate_state(state)
        AESGCM, _, _ = _crypto()
        salt, nonce = os.urandom(16), os.urandom(12)
        payload = json.dumps(state, separators=(",", ":"), allow_nan=False).encode()
        blob = MAGIC + salt + nonce + AESGCM(_key(password, salt)).encrypt(nonce, payload, AAD)
        if len(blob)>MAX_BYTES:
            raise ValueError("Vault size limit reached.")
        fd, temporary = tempfile.mkstemp(prefix=".physique-", dir=self.path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(blob)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def initialize(self, password):
        with self.exclusive():
            if self.path.exists():
                raise ValueError("Vault already exists.")
            self._write(password, {"version":2,"target_date":None,"records":[],"sets":[],"milestones":[]})

    def add(self, password, record):
        record = validate_record(record)
        with self.exclusive():
            state = self.read(password)
            if any(row["date"]==record["date"] for row in state["records"]):
                raise ValueError("A record already exists for this date. Use replace explicitly.")
            state["records"].append(record)
            self._write(password, state)

    def replace(self, password, record):
        record = validate_record(record)
        with self.exclusive():
            state = self.read(password)
            if not any(r["date"]==record["date"] for r in state["records"]):
                raise ValueError("No record for this date.")
            state["records"] = [record if r["date"]==record["date"] else r for r in state["records"]]
            self._write(password, state)

    def delete(self, password, date):
        _date(date)
        with self.exclusive():
            state = self.read(password)
            rows = [r for r in state["records"] if r["date"]!=date]
            if len(rows)==len(state["records"]):
                raise ValueError("No record for this date.")
            state["records"] = rows
            self._write(password, state)

    def set_target(self, password, date):
        if date is not None:
            _date(date)
        with self.exclusive():
            state = self.read(password)
            state["target_date"] = date
            self._write(password, state)

    def add_set(self,password,row):
        training.validate_set(row)
        with self.exclusive():
            state=self.read(password)
            state["sets"].append(row)
            self._write(password,state)

    def add_milestone(self,password,row):
        training.validate_milestone(row)
        with self.exclusive():
            state=self.read(password)
            state["milestones"].append(row)
            self._write(password,state)

    def change_item(self,password,collection,ident,action):
        training.ident(ident)
        if collection not in ("sets","milestones") or action not in ("delete","toggle"):
            raise ValueError("Unsupported change.")
        if action=="toggle" and collection!="milestones":
            raise ValueError("Only milestones can be toggled.")
        with self.exclusive():
            state=self.read(password)
            rows=state[collection]
            row=next((r for r in rows if r["id"]==ident),None)
            if row is None:
                raise ValueError("Record no longer exists.")
            if action=="delete":
                state[collection]=[r for r in rows if r["id"]!=ident]
            else:
                row["done"]=not row["done"]
            self._write(password,state)

def run(data_dir, parent=None, coach_stage=None):
    """Owner-operated dashboard; no agent access."""
    from .physique_ui import open_workspace
    return open_workspace(Vault(data_dir),parent,coach_stage=coach_stage)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir",type=Path,default=default_data_dir())
    parser.add_argument("action",choices=["desktop","init","summary","add","replace","delete","target"])
    parser.add_argument("--date")
    args=parser.parse_args()
    try:
        if args.action=="desktop":
            run(args.data_dir)
            return
        vault=Vault(args.data_dir)
        password=getpass.getpass("Local vault passphrase: ")
        if args.action=="init":
            if password!=getpass.getpass("Repeat passphrase: "):
                raise ValueError("Passphrases do not match.")
            vault.initialize(password)
        elif args.action in ("add","replace"):
            row={"date":args.date or dt.date.today().isoformat()}
            for key in sorted(FIELDS-{"date"}):
                value=input(key+" (blank = missing): ").strip()
                row[key]=float(value) if value else None
            (vault.add if args.action=="add" else vault.replace)(password,row)
        elif args.action=="delete":
            vault.delete(password,args.date)
        elif args.action=="target":
            vault.set_target(password,args.date)
        print(json.dumps(summary(vault.read(password)),indent=2))
    except (ValueError,OSError) as exc:
        parser.exit(1,str(exc)+"\n")

if __name__=="__main__":
    main()
