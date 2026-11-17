"""Pure validation and analytics for Physique v2. No network or prescriptions."""
import datetime as dt
import math
import re
import uuid

def date(value):
    if not isinstance(value,str):
        raise ValueError("Use YYYY-MM-DD.")
    try:
        parsed=dt.date.fromisoformat(value)
    except ValueError:
        raise ValueError("Use YYYY-MM-DD.") from None
    if parsed.isoformat()!=value:
        raise ValueError("Use YYYY-MM-DD.")
    return parsed

def label(value):
    if not isinstance(value,str) or not 1<=len(value.strip())<=80 or any(ord(c)<32 for c in value):
        raise ValueError("Enter a short label (1–80 characters).")
    return value.strip()

def number(value, low, high):
    if type(value) not in (float,int) or not math.isfinite(value) or not low<=value<=high:
        raise ValueError("Number outside allowed range.")
    return value

def ident(value):
    if not isinstance(value,str) or not re.fullmatch(r"[0-9a-f]{32}",value):
        raise ValueError("Invalid record ID.")
    return value

def validate_set(row):
    if not isinstance(row,dict) or set(row)!={"id","date","exercise","reps","weight_kg","rpe"}:
        raise ValueError("Invalid training set.")
    ident(row["id"]); date(row["date"]); label(row["exercise"])
    if type(row["reps"]) is not int or not 1<=row["reps"]<=500:
        raise ValueError("Reps must be an integer between 1 and 500.")
    number(row["weight_kg"],0,1500)
    if row["rpe"] is not None:
        number(row["rpe"],1,10)
    return row

def new_set(day,exercise,reps,weight,rpe=None):
    return validate_set(dict(id=uuid.uuid4().hex,date=day,exercise=label(exercise),
                             reps=reps,weight_kg=weight,rpe=rpe))

def validate_milestone(row):
    if not isinstance(row,dict) or set(row)!={"id","date","title","done"}:
        raise ValueError("Invalid milestone.")
    ident(row["id"]); date(row["date"]); label(row["title"])
    if type(row["done"]) is not bool:
        raise ValueError("Invalid milestone status.")
    return row

def new_milestone(day,title):
    return validate_milestone(dict(id=uuid.uuid4().hex,date=day,title=label(title),done=False))

def validate_collections(state):
    for key,validator,limit in (("sets",validate_set,10000),("milestones",validate_milestone,1000)):
        rows=state[key]
        if not isinstance(rows,list) or len(rows)>limit:
            raise ValueError("Collection exceeds limit.")
        seen=set()
        for row in rows:
            validator(row)
            if row["id"] in seen:
                raise ValueError("Duplicate record ID.")
            seen.add(row["id"])

def analytics(state,today=None):
    today=today or dt.date.today()
    sets=[r for r in state.get("sets",[]) if date(r["date"])<=today]
    def window(start,end):
        rows=[r for r in sets if start<=date(r["date"])<=end]
        return dict(sessions=len({r["date"] for r in rows}),sets=len(rows),
                    reps=sum(r["reps"] for r in rows),
                    volume_kg=round(sum(r["reps"]*r["weight_kg"] for r in rows),2))
    current=window(today-dt.timedelta(days=6),today)
    prior=window(today-dt.timedelta(days=13),today-dt.timedelta(days=7))
    best={}
    for row in sets:
        key=row["exercise"].strip().casefold()
        old=best.get(key)
        if old is None or (row["weight_kg"],row["reps"])>(old["weight_kg"],old["reps"]):
            best[key]=row
    milestones=sorted(state.get("milestones",[]),key=lambda r:(r["date"],r["id"]))
    return {"current":current,"prior":prior,
            "best_sets":sorted(best.values(),key=lambda r:r["exercise"].casefold()),
            "milestones":milestones,
            "overdue":sum(not r["done"] and date(r["date"])<today for r in milestones)}
