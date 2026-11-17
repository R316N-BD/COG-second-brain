"""Rotatable schematic muscle explorer, not an anatomical mesh or medical model."""
import math
import tkinter as tk
from tkinter import ttk
from .physique_anatomy import MUSCLES,muscle_history

# Ellipsoids in normalized 3D coordinates: label,x,y,z,rx,ry,rz.
PARTS=[("",0,0.48,0,.16,.17,.14),("",0,.83,0,.22,.27,.13),
       ("",0,1.17,0,.18,.19,.13)]
for s in (-1,1):
    PARTS += [
        ("chest",s*.11,.78,.10,.12,.10,.065),
        ("delts",s*.25,.73,0,.10,.12,.12),
        ("lats",s*.16,.95,-.10,.10,.19,.06),
        ("upper_back",s*.09,.77,-.12,.10,.14,.06),
        ("biceps",s*.31,.94,.07,.068,.14,.06),
        ("triceps",s*.31,.94,-.07,.075,.14,.065),
        ("",s*.36,1.19,0,.065,.14,.07),
        ("",s*.39,1.37,0,.045,.08,.04),
        ("abs",s*.055,1.03,.12,.06,.19,.04),
        ("glutes",s*.10,1.24,-.10,.105,.12,.08),
        ("quads",s*.11,1.52,.07,.095,.23,.08),
        ("hamstrings",s*.11,1.52,-.07,.09,.23,.08),
        ("",s*.11,1.79,0,.06,.09,.06),
        ("calves",s*.11,1.98,-.035,.073,.19,.08),
        ("",s*.11,2.19,.06,.075,.06,.12)]
def mount_anatomy(page):
    style="Physique.TLabel"
    ttk.Label(page,text="BODY INTELLIGENCE • Rotatable 3D schematic",style=style,font=("Segoe UI",16,"bold")).pack(anchor="w")
    ttk.Label(page,text="Select a region, rotate the model, or inspect the last 30 days of recognized exercise history. Not a clinical anatomy model.",style=style,wraplength=900).pack(anchor="w")
    top=ttk.Frame(page,style="Physique.TFrame");top.pack(fill="x",pady=8)
    muscle=tk.StringVar(value="chest")
    picker=ttk.Combobox(top,textvariable=muscle,values=tuple(MUSCLES),state="readonly",width=18);picker.pack(side="left")
    angle=tk.DoubleVar(value=0)
    ttk.Label(top,text="Rotate",style=style).pack(side="left",padx=8)
    slider=ttk.Scale(top,from_=0,to=360,variable=angle,orient="horizontal");slider.pack(side="left",fill="x",expand=True)
    split=ttk.Panedwindow(page,orient="horizontal");split.pack(fill="both",expand=True)
    left=ttk.Frame(split,style="Physique.TFrame");right=ttk.Frame(split,style="Physique.TFrame")
    split.add(left,weight=2);split.add(right,weight=3)
    canvas=tk.Canvas(left,bg="#101c2b",highlightthickness=0,width=360,height=420);canvas.pack(fill="both",expand=True)
    info=tk.StringVar();ttk.Label(right,textvariable=info,style=style,wraplength=540,justify="left").pack(anchor="w")
    tree=ttk.Treeview(right,columns=("date","exercise","reps","kg","role"),show="headings",style="Physique.Treeview")
    for key,width in (("date",95),("exercise",155),("reps",45),("kg",55),("role",85)):
        tree.heading(key,text=key.title());tree.column(key,width=width,minwidth=35)
    tree.pack(fill="both",expand=True,pady=8)
    state={"sets":[],"unlocked":False}
    def draw(*_):
        canvas.delete("all")
        w=max(canvas.winfo_width(),160);h=max(canvas.winfo_height(),200)
        scale=min(w/1.05,h/2.05);origin=h*.08-.30*scale
        theta=math.radians(angle.get());c=math.cos(theta);s=math.sin(theta)
        shapes=[]
        for key,x,y,z,rx,ry,rz in PARTS:
            xx=x*c+z*s;depth=-x*s+z*c
            radius=math.sqrt((rx*c)**2+(rz*s)**2)
            shapes.append((depth,key,xx,y,radius,ry))
        for depth,key,x,y,rx,ry in sorted(shapes):
            cx=w/2+x*scale;cy=origin+y*scale
            color="#36ddc7" if key==muscle.get() else "#46617b" if key else "#28384c"
            item=canvas.create_oval(cx-rx*scale,cy-ry*scale,cx+rx*scale,cy+ry*scale,fill=color,outline="#0b1320",width=2)
            if key:canvas.tag_bind(item,"<Button-1>",lambda event,k=key:muscle.set(k))
        canvas.create_text(w/2,h-12,text=f"Rotation {angle.get():.0f}° · illustrative model",fill="#9db2ca")
    def refresh(*_):
        key=muscle.get();name,description=MUSCLES[key]
        report=muscle_history(state["sets"],key)
        history=(f"30-day history: {report['primary']} primary / {report['secondary']} secondary sets; "
                 f"{report['unclassified']} unclassified sets across all exercises.") if state["unlocked"] else "Unlock Physique to view your history."
        info.set(name+"\n"+description+"\n\n"+history+"\n\nRecognized exercises: "+", ".join(report["exercises"]))
        tree.delete(*tree.get_children())
        for row in report["rows"]:tree.insert("","end",values=row)
        draw()
    muscle.trace_add("write",refresh);angle.trace_add("write",draw);canvas.bind("<Configure>",draw)
    def load(rows):
        state["sets"]=list(rows) if rows is not None else []
        state["unlocked"]=rows is not None
        refresh()
    refresh()
    return load
