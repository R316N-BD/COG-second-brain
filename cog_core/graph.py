"""Local wiki-link graph. Ambiguous links remain unresolved."""
import re
from collections import defaultdict
from pathlib import PurePosixPath
from . import memory
from .paths import private_path, note_path

def build(data_dir):
    root = private_path(data_dir)
    vault, _ = memory._paths(root)
    notes, names, edges, unresolved = {}, defaultdict(list), [], []
    total = 0
    for path in memory._notes(vault):
        rel = path.relative_to(vault).as_posix()
        try:
            note_path(root, rel)
            with path.open("rb") as handle:
                raw = handle.read(memory.MAX_BYTES+1)
            if len(raw) > memory.MAX_BYTES:
                continue
            total += len(raw)
            if total > memory.MAX_TOTAL_BYTES:
                raise ValueError("Graph byte budget exceeded.")
            body = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            continue
        notes[rel] = re.findall(r"\[\[([^\]\n]{1,300})\]\]", body)[:1000]
        names[PurePosixPath(rel).stem.casefold()].append(rel)
        names[rel[:-3].casefold()].append(rel)
    for src, links in notes.items():
        for raw in links:
            if len(edges) + len(unresolved) >= 100000:
                raise ValueError("Graph link budget exceeded.")
            name = raw.split("|",1)[0].split("#",1)[0].strip()
            if name.lower().endswith(".md"):
                name = name[:-3]
            candidates = sorted(set(names.get(name.casefold(), [])))
            if len(candidates) == 1:
                edges.append({"from": src, "to": candidates[0]})
            else:
                unresolved.append({"from": src, "link": raw, "reason": "ambiguous" if candidates else "missing"})
    return {"nodes": sorted(notes), "edges": edges, "unresolved": unresolved}
