"""Read-only BodyParts3D 4.0 ZIP importer. No extraction, execution or network."""
import csv
import hashlib
import io
import math
import re
import stat
import zipfile
from pathlib import Path

SOURCE="https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html"
ATTRIBUTION="BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International"
LICENSE="https://creativecommons.org/licenses/by/4.0/"
# Exact bilateral concept IDs from the official IS-A 4.0 names table.
PRESETS={
 "Upper pectorals":("FMA34690","FMA34691"),
 "Sternocostal pectorals":("FMA79979","FMA79980"),
 "Anterior deltoids":("FMA34680","FMA34681"),
 "Middle deltoids":("FMA34682","FMA34683"),
 "Posterior deltoids":("FMA34684","FMA34685"),
 "Biceps brachii":("FMA37684","FMA37685","FMA37686","FMA37687"),
 "Brachialis":("FMA37668","FMA37669"),
 "Triceps":("FMA37695","FMA37696","FMA37697","FMA37698","FMA37699","FMA37700"),
 "Rectus femoris":("FMA38928","FMA38929"),
 "Vastus lateralis":("FMA38930","FMA38931"),
 "Vastus medialis":("FMA38932","FMA38933"),
 "Vastus intermedius":("FMA38934","FMA38935"),
 "Biceps femoris":("FMA45888","FMA45889","FMA45891","FMA45892"),
 "Upper trapezius":("FMA33586","FMA33587"),
 "Middle trapezius":("FMA33584","FMA33585"),
 "Lower trapezius":("FMA33581","FMA33583"),
 "Rhomboids":("FMA13381","FMA13382","FMA13383","FMA13384"),
 "Serratus anterior":("FMA13398","FMA13399"),
 "External obliques":("FMA13336","FMA13337"),
 "Gluteus maximus":("FMA22328","FMA22329"),
 "Gluteus medius":("FMA22330","FMA22331"),
 "Gluteus minimus":("FMA22332","FMA22333"),
 "Medial hamstrings":("FMA22358","FMA22359","FMA22448","FMA22449"),
 "Hip adductors":("FMA22452","FMA22454","FMA22456","FMA22457","FMA22459","FMA22460"),
 "Gastrocnemius":("FMA45957","FMA45958","FMA45960","FMA45961"),
 "Soleus":("FMA22558","FMA22559"),
 "Tibialis anterior":("FMA22544","FMA22545"),
 "Scapula and humerus":("FMA13395","FMA13396","FMA23130","FMA23131"),
 "Knee bones":("FMA24474","FMA24475","FMA24477","FMA24478","FMA24486","FMA24487"),
 "Forearm bones":("FMA23464","FMA23465","FMA23467","FMA23468"),
}
MAX_META=8_000_000
MAX_MEMBER=12_000_000
MAX_TOTAL=24_000_000
MAX_FACES=24_000

def read_metadata(path):
    with Path(path).open("rb") as f:raw=f.read(MAX_META+1)
    if len(raw)>MAX_META:raise ValueError("Metadata exceeds size limit.")
    reader=csv.reader(io.StringIO(raw.decode("utf-8-sig")),delimiter="\t")
    header=next(reader,[])
    if header!=["concept id","name","element file id"]:
        raise ValueError("Select official isa_element_parts.txt.")
    concepts={}
    for line in reader:
        if len(line)!=3:raise ValueError("Unexpected metadata row.")
        fma,name,element=line
        if not re.fullmatch(r"FMA\d+",fma) or not re.fullmatch(r"FJ\d+",element):continue
        item=concepts.setdefault(fma,{"name":name,"elements":set()})
        if item["name"]!=name:raise ValueError("Inconsistent concept names.")
        item["elements"].add(element)
    return concepts,hashlib.sha256(raw).hexdigest()

def parse_obj(raw):
    if len(raw)>MAX_MEMBER:raise ValueError("OBJ too large.")
    vertices=[];triangles=[]
    for line in raw.decode("utf-8-sig").splitlines():
        line=line.partition("#")[0].strip()
        if not line:continue
        words=line.split()
        if words[0]=="v":
            if len(words) not in (4,5):raise ValueError("Invalid vertex.")
            p=tuple(float(x) for x in words[1:4])
            if not all(math.isfinite(x) and abs(x)<1e7 for x in p):raise ValueError("Invalid coordinate.")
            if len(words)==5 and float(words[4])!=1:raise ValueError("Non-unit homogeneous vertex.")
            vertices.append(p)
            if len(vertices)>MAX_FACES*4:raise ValueError("Too many vertices.")
        elif words[0]=="f":
            if not 4<=len(words)<=65:raise ValueError("Unsupported face size.")
            ids=[]
            for token in words[1:]:
                idx=int(token.split("/")[0])
                if idx==0:raise ValueError("Invalid face index.")
                idx=idx-1 if idx>0 else len(vertices)+idx
                if not 0<=idx<len(vertices):raise ValueError("Face index out of bounds.")
                ids.append(idx)
            for j in range(1,len(ids)-1):
                tri=tuple(vertices[k] for k in (ids[0],ids[j],ids[j+1]))
                if len(set(tri))!=3:continue
                triangles.append(tri)
                if len(triangles)>MAX_FACES:raise ValueError("Triangle budget exceeded.")
        # Texture, material, normals, groups and other directives are ignored.
    if not triangles:raise ValueError("No supported geometry.")
    return triangles

def load_region(archive,metadata,concept_ids):
    if not concept_ids or len(concept_ids)>20:raise ValueError("Select a small concept group.")
    concepts,meta_hash=read_metadata(metadata)
    if any(k not in concepts for k in concept_ids):raise ValueError("Concept absent in supplied metadata.")
    elements=sorted({v for k in concept_ids for v in concepts[k]["elements"]})
    if len(elements)>80:raise ValueError("Choose fewer anatomical elements.")
    meshes=[];total=0;faces=0
    with zipfile.ZipFile(archive) as z:
        if len(z.infolist())>30000:raise ValueError("Archive index exceeds limit.")
        entries={}
        for info in z.infolist():
            name=Path(info.filename).name
            if not re.fullmatch(r"FJ\d+\.obj",name,re.I):continue
            key=name[:-4].upper()
            if key not in elements:continue
            if key in entries:raise ValueError("Duplicate element in archive.")
            if stat.S_ISLNK(info.external_attr>>16) or info.file_size>MAX_MEMBER or info.flag_bits&1:
                raise ValueError("Unsafe or oversized OBJ member.")
            entries[key]=info
        if set(entries)!=set(elements):
            raise ValueError("Archive does not contain all selected element IDs. Use matching IS-A 4.0 files.")
        for key in elements:
            info=entries[key];total+=info.file_size
            if total>MAX_TOTAL:raise ValueError("Import byte budget exceeded.")
            with z.open(info) as handle:raw=handle.read(MAX_MEMBER+1)
            tris=parse_obj(raw);faces+=len(tris)
            if faces>MAX_FACES:raise ValueError("Group exceeds viewer triangle budget; choose fewer concepts.")
            meshes.append({"element":key,"sha256":hashlib.sha256(raw).hexdigest(),"triangles":tris})
    return {"names":[concepts[k]["name"] for k in concept_ids],"concepts":list(concept_ids),
            "metadata_sha256":meta_hash,"meshes":meshes,"triangle_count":faces,
            "attribution":ATTRIBUTION,"source":SOURCE,"license":LICENSE}

def normalize_mesh(meshes,up="z",front_sign=-1):
    """Shared fit across all selected elements; preserves relative positions and proportions."""
    if up not in ("z","y") or front_sign not in (-1,1):raise ValueError("Invalid axis convention.")
    def transform(p):
        x,y,z=p
        return (x,-z,front_sign*y) if up=="z" else (x,-y,front_sign*z)
    mapped=[(m["element"],[tuple(transform(p) for p in t) for t in m["triangles"]]) for m in meshes]
    pts=[p for _,ts in mapped for t in ts for p in t]
    if not pts:raise ValueError("No geometry.")
    lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
    center=[(a+b)/2 for a,b in zip(lo,hi)];span=max(b-a for a,b in zip(lo,hi))
    if span<=1e-12:raise ValueError("Degenerate mesh.")
    return [(key,[tuple(tuple((p[i]-center[i])/span for i in range(3)) for p in t) for t in ts]) for key,ts in mapped]
