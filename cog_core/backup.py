"""Bounded encrypted Markdown snapshot; restore only into a fresh directory."""
from contextlib import closing
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import zipfile

from . import memory
from .paths import private_path, note_path, checked_child, VAULT_FOLDERS

MAGIC = b"COGBACKUP1"
MAX_TOTAL = 64 * 1024 * 1024
MAX_FILES = 5000

def _key(password, salt):
    if len(password) < 12:
        raise ValueError("Use a backup passphrase of at least 12 characters.")
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**15, r=8, p=1,
                          maxmem=64*1024*1024, dklen=32)

def _encrypt(data, password):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt, nonce = secrets.token_bytes(16), secrets.token_bytes(12)
    header = MAGIC + salt + nonce
    return header + AESGCM(_key(password, salt)).encrypt(nonce, data, header)

def _decrypt(data, password):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.exceptions import InvalidTag
    if not data.startswith(MAGIC) or len(data) < len(MAGIC) + 44:
        raise ValueError("Not a COG backup.")
    offset = len(MAGIC)
    salt, nonce = data[offset:offset+16], data[offset+16:offset+28]
    header = data[:offset+28]
    try:
        return AESGCM(_key(password, salt)).decrypt(nonce, data[offset+28:], header)
    except InvalidTag:
        raise ValueError("Incorrect passphrase or corrupted backup.") from None

def create(data_dir, password):
    root = private_path(data_dir)
    vault, _ = memory._paths(root)
    buf, hashes, total = io.BytesIO(), {}, 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in memory._notes(vault):
            rel = path.relative_to(vault).as_posix()
            # Only well-formed vault Markdown paths are eligible.
            if note_path(root, rel) != path:
                raise ValueError("Invalid vault note.")
            with path.open("rb") as handle:
                raw = handle.read(memory.MAX_BYTES+1)
            total += len(raw)
            if len(raw) > memory.MAX_BYTES or total > MAX_TOTAL or len(hashes) >= MAX_FILES:
                raise ValueError("Backup size limit exceeded; no backup written.")
            hashes[rel] = hashlib.sha256(raw).hexdigest()
            archive.writestr("vault/" + rel, raw)
        archive.writestr("manifest.json", json.dumps({"schema": 1, "hashes": hashes}))
    encrypted = _encrypt(buf.getvalue(), password)
    target = checked_child(root, "backups/" + secrets.token_hex(16) + ".cogbackup")
    with target.open("xb") as handle:
        handle.write(encrypted)
    return {"backup": str(target), "notes": len(hashes), "encrypted": True}

def restore(archive_path, destination, password):
    from .cli import init_vault
    target = private_path(destination)
    if target.exists():
        raise ValueError("Restore destination must not exist; existing data is never overwritten.")
    with Path(archive_path).open("rb") as handle:
        encrypted = handle.read(MAX_TOTAL+4*1024*1024+1)
    if len(encrypted) > MAX_TOTAL+4*1024*1024:
        raise ValueError("Backup exceeds archive limit.")
    contents = _decrypt(encrypted, password)
    with zipfile.ZipFile(io.BytesIO(contents)) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_FILES+1 or sum(e.file_size for e in entries) > MAX_TOTAL+2*1024*1024:
            raise ValueError("Backup extraction budget exceeded.")
        manifest = json.loads(archive.read("manifest.json"))
        hashes = manifest.get("hashes")
        if manifest.get("schema") != 1 or not isinstance(hashes, dict):
            raise ValueError("Invalid backup manifest.")
        if len(entries) != len(hashes)+1 or set(archive.namelist()) != {"manifest.json", *("vault/"+p for p in hashes)}:
            raise ValueError("Unexpected archive entries.")
        validated = []
        for rel, digest in hashes.items():
            path = note_path(target, rel)
            info = archive.getinfo("vault/" + rel)
            if info.file_size > memory.MAX_BYTES:
                raise ValueError("Oversized note.")
            raw = archive.read(info)
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError("Backup integrity check failed.")
            validated.append((path, raw))
    # All archive entries are validated before any restore writes.
    target.mkdir(mode=0o700, parents=True, exist_ok=False)
    init_vault(target)
    for path, raw in validated:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(raw)
    return {"restored": len(validated), "data_dir": str(target),
            "notice": "Only Markdown notes restored; rebuild the index."}
