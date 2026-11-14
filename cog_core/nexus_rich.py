"""Inert COG UI v1 blocks. No generated HTML, scripts or commands."""
import json
import math
import re

MARK=chr(96)*3
FENCE=re.compile(r"(?:^|\n)"+MARK+r"cog-ui\s*\n(.*?)\n"+MARK+r"(?=\n|$)",re.S)
KINDS={"metrics","table","bar","checklist"}

def _text(value,limit=200):
    if not isinstance(value,str) or len(value)>limit:
        raise ValueError("Invalid text.")
    return value

def validate(doc):
    if not isinstance(doc,dict) or doc.get("version")!=1 or doc.get("type") not in KINDS:
        raise ValueError("Unsupported COG UI block.")
    kind=doc["type"]
    rows=doc.get("rows")
    if not isinstance(rows,list) or len(rows)>30:
        raise ValueError("Invalid row count.")
    result={"version":1,"type":kind,"title":_text(doc.get("title",""),100),"rows":[]}
    if kind=="table":
        cols=doc.get("columns")
        if not isinstance(cols,list) or not 1<=len(cols)<=8:
            raise ValueError("Invalid columns.")
        result["columns"]=[_text(c,80) for c in cols]
        for row in rows:
            if not isinstance(row,list) or len(row)!=len(cols) or not all(isinstance(v,(str,int,float,bool)) for v in row):
                raise ValueError("Invalid table row.")
            result["rows"].append([_text(str(v),300) for v in row])
    else:
        for row in rows:
            if not isinstance(row,dict):
                raise ValueError("Invalid row.")
            label=_text(row.get("label"),100)
            value=row.get("value")
            if kind=="bar":
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=1e12:
                    raise ValueError("Invalid bar value.")
            elif kind=="checklist":
                if not isinstance(value,bool):
                    raise ValueError("Invalid checklist.")
            elif not isinstance(value,(str,int,float,bool)):
                raise ValueError("Invalid metric.")
            else:
                value=_text(str(value),100)
            result["rows"].append({"label":label,"value":value})
    return result

def parse(text):
    blocks=[]
    for match in FENCE.finditer(text[:262144]):
        if len(blocks)>=5:
            break
        try:
            if len(match.group(1))<=32768:
                blocks.append(validate(json.loads(match.group(1))))
        except (ValueError,TypeError,OverflowError):
            pass
    return blocks

INSTRUCTIONS=("If a visual summary is useful append a fenced cog-ui JSON block. "
              "Use version 1; types metrics, table, bar or checklist. Example:\n"+
              MARK+'cog-ui\n{"version":1,"type":"bar","title":"Tasks","rows":[{"label":"Done","value":3}]}\n'+MARK+
              "\nTables use columns and rows of arrays; metrics/checklists use label/value pairs; checklist values are booleans. Use factual data only. No scripts or HTML.")
