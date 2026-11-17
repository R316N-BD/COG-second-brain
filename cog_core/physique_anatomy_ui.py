"""Interactive shaded 3D body explorer with local, read-only training analytics."""
import tkinter as tk
from tkinter import ttk
from .physique_body_detail import REGIONS,body_counts,period_comparison
from .physique_body_mesh import scene

def mount_anatomy(page):
    style="Physique.TLabel"; frame_style="Physique.TFrame"
    ttk.Label(page,text="BODY INTELLIGENCE / 3D muscle atlas",style=style,font=("Segoe UI",16,"bold")).pack(anchor="w")
    ttk.Label(page,text="Original schematic geometry, not a clinical atlas. Counts describe recognized exercise relationships, not muscle activation or recovery.",style=style,wraplength=950).pack(anchor="w")
    top=ttk.Frame(page,style=frame_style);top.pack(fill="x",pady=5)
    names={v[1]:k for k,v in REGIONS.items()}
    region=tk.StringVar(value=REGIONS["upper_pec"][1])
    picker=ttk.Combobox(top,textvariable=region,values=tuple(names),state="readonly",width=27);picker.pack(side="left",padx=3)
    period=tk.StringVar(value="30")
    ttk.Combobox(top,textvariable=period,values=("7","14","30","90","365"),state="readonly",width=5).pack(side="left")
    ttk.Label(top,text="days",style=style).pack(side="left",padx=3)
    layer=tk.StringVar(value="surface")
    ttk.Combobox(top,textvariable=layer,values=("surface","deep","all"),state="readonly",width=8).pack(side="left",padx=4)
    mode=tk.StringVar(value="Anatomy")
    ttk.Combobox(top,textvariable=mode,values=("Anatomy","Primary sets","Secondary sets"),state="readonly",width=15).pack(side="left",padx=4)
    isolate=tk.BooleanVar(value=False)
    ttk.Checkbutton(top,text="Isolate",variable=isolate).pack(side="left",padx=4)
    controls=ttk.Frame(page,style=frame_style);controls.pack(fill="x")
    yaw=tk.DoubleVar(value=0);pitch=tk.DoubleVar(value=0);zoom=tk.DoubleVar(value=1)
    def orient(a,b=0):
        yaw.set(a);pitch.set(b)
    for text,a in (("Front",0),("Back",180),("Left",90),("Right",270)):
        ttk.Button(controls,text=text,command=lambda x=a:orient(x)).pack(side="left",padx=2)
    ttk.Button(controls,text="Reset",command=lambda:(orient(0),zoom.set(1))).pack(side="left",padx=2)
    ttk.Label(controls,text="Zoom",style=style).pack(side="left",padx=6)
    ttk.Scale(controls,from_=.65,to=1.8,variable=zoom).pack(side="left",fill="x",expand=True)
    split=ttk.Panedwindow(page,orient="horizontal");split.pack(fill="both",expand=True)
    left=ttk.Frame(split,style=frame_style);right=ttk.Frame(split,style=frame_style)
    split.add(left,weight=2);split.add(right,weight=3)
    canvas=tk.Canvas(left,bg="#101c2b",highlightthickness=0,width=360,height=440);canvas.pack(fill="both",expand=True)
    legend=tk.StringVar(value="Drag to rotate • click a region • mouse wheel to zoom")
    ttk.Label(left,textvariable=legend,style=style,wraplength=400).pack(anchor="w")
    info=tk.StringVar();ttk.Label(right,textvariable=info,style=style,wraplength=500,justify="left").pack(anchor="w",pady=5)
    detail=ttk.Notebook(right);detail.pack(fill="both",expand=True)
    history=ttk.Frame(detail);exercises=ttk.Frame(detail)
    detail.add(history,text="Training history");detail.add(exercises,text="Exercise relationships")
    def table(parent,columns):
        tree=ttk.Treeview(parent,columns=[k for k,_ in columns],show="headings",style="Physique.Treeview")
        for k,w in columns:tree.heading(k,text=k.title());tree.column(k,width=w,minwidth=40)
        scroll=ttk.Scrollbar(parent,orient="vertical",command=tree.yview)
        tree.configure(yscrollcommand=scroll.set);scroll.pack(side="right",fill="y");tree.pack(fill="both",expand=True)
        return tree
    ht=table(history,(("date",95),("exercise",140),("reps",45),("kg",55),("role",85)))
    et=table(exercises,(("exercise",220),("relationship",120)))
    state={"sets":[],"unlocked":False,"reports":{},"pending":False,"items":{},"drag":None}
    def selected():return names[region.get()]
    def color(key,light):
        if not key:base=(43,58,76)
        elif key==selected():base=(42,225,194)
        elif mode.get()!="Anatomy" and state["unlocked"]:
            metric="primary" if mode.get()=="Primary sets" else "secondary"
            maximum=max((r[metric] for r in state["reports"].values()),default=0)
            v=state["reports"].get(key,{}).get(metric,0)
            f=v/maximum if maximum else 0
            base=tuple(int(a+(b-a)*f) for a,b in zip((49,64,83),(246,155,66)))
        else:base=(160,84,81)
        factor=.48+.52*light
        return "#"+"".join(f"{int(v*factor):02x}" for v in base)
    def draw():
        state["pending"]=False
        canvas.delete("all");state["items"].clear()
        w=max(canvas.winfo_width(),160);h=max(canvas.winfo_height(),200)
        scale=min(w/1.02,(h-32)/2.05)*zoom.get()
        for _,key,side,light,points in scene(yaw.get(),pitch.get(),layer.get(),selected() if isolate.get() else None):
            coords=[v for x,y,z in points for v in (w/2+x*scale,(h-20)/2+y*scale)]
            item=canvas.create_polygon(*coords,fill=color(key,light),outline="")
            if key:state["items"][item]=(key,side)
        canvas.create_text(w/2,h-12,text=f"{yaw.get():.0f}° / tilt {pitch.get():.0f}° · schematic",fill="#9db2ca")
    def schedule(*_):
        if not state["pending"]:
            state["pending"]=True
            canvas.after_idle(draw)
    def show(*_):
        k=selected();group,name,description=REGIONS[k]
        report=state["reports"].get(k)
        if report is None:
            summary="Unlock Physique to see training history."
            from .physique_body_detail import region_history
            report=region_history([],k,int(period.get()))
        else:
            summary=(f"{period.get()} days: {report['primary']} primary / {report['secondary']} secondary sets"
                     f" • {report['sessions']} training dates\nLast recognized exposure: {report['last_date'] or 'none'}"
                     f" • Unclassified sets: {report['unclassified']}")
            comparison=period_comparison(state["sets"],k,int(period.get()))
            summary+=f"\nChange vs preceding equal period: {comparison['primary_change']:+d} primary / {comparison['secondary_change']:+d} secondary"
        info.set(name+" · "+group.replace("_"," ")+"\n"+description+"\n\n"+summary)
        ht.delete(*ht.get_children());et.delete(*et.get_children())
        for row in report["rows"]:ht.insert("","end",values=row)
        for k,title in (("primary_exercises","Primary"),("secondary_exercises","Secondary")):
            for ex in report[k]:et.insert("","end",values=(ex,title))
        legend.set("Drag to rotate • click a region • wheel to zoom" if mode.get()=="Anatomy" else
                   "Heatmap: gray = no mapped sets; amber = highest relative count; teal = selection" if state["unlocked"] else "Unlock to view heatmap")
        schedule()
    def recompute(*_):
        state["reports"]=body_counts(state["sets"],int(period.get())) if state["unlocked"] else {}
        show()
    def press(event):
        state["drag"]=(event.x,event.y,yaw.get(),pitch.get())
    def motion(event):
        d=state["drag"]
        if d:
            yaw.set((d[2]+(event.x-d[0])*.65)%360)
            pitch.set(max(-35,min(35,d[3]+(event.y-d[1])*.35)))
    def release(event):
        d=state["drag"];state["drag"]=None
        if d and abs(event.x-d[0])+abs(event.y-d[1])<5:
            hits=canvas.find_overlapping(event.x,event.y,event.x,event.y)
            if hits and hits[-1] in state["items"]:
                key,_=state["items"][hits[-1]];region.set(REGIONS[key][1])
    def wheel(event):
        direction=1 if getattr(event,"delta",0)>0 or getattr(event,"num",0)==4 else -1
        zoom.set(max(.65,min(1.8,zoom.get()+direction*.1)))
    canvas.bind("<ButtonPress-1>",press);canvas.bind("<B1-Motion>",motion);canvas.bind("<ButtonRelease-1>",release)
    canvas.bind("<MouseWheel>",wheel);canvas.bind("<Button-4>",wheel);canvas.bind("<Button-5>",wheel)
    canvas.bind("<Configure>",schedule)
    for var in (yaw,pitch,zoom,layer,isolate):var.trace_add("write",schedule)
    for var in (region,mode):var.trace_add("write",show)
    period.trace_add("write",recompute)
    def load(rows):
        state["sets"]=list(rows) if rows is not None else []
        state["unlocked"]=rows is not None
        recompute()
    recompute()
    return load
