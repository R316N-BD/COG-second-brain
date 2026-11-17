"""Native Physique dashboard. All private fields remain in the local process."""
import datetime as dt
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from .physique import FIELDS, summary
from . import physique_training as training

def open_workspace(vault, parent=None, coach_stage=None):
    win=tk.Toplevel(parent) if parent else tk.Tk()
    win.title("COG PHYSIQUE | Athlete command")
    win.geometry("1100x760")
    win.minsize(800,600)
    bg="#0b1320"; panel="#152336"; ink="#e5eef9"; accent="#38dbc5"; muted="#9db2ca"
    win.configure(bg=bg)
    style=ttk.Style(win)
    style.configure("Physique.TFrame",background=bg)
    style.configure("Physique.TLabel",background=bg,foreground=ink)
    style.configure("Physique.TButton",padding=7)
    style.configure("Physique.Treeview",background=panel,fieldbackground=panel,foreground=ink,rowheight=26)
    outer=ttk.Frame(win,style="Physique.TFrame",padding=18)
    outer.pack(fill="both",expand=True)
    title=ttk.Frame(outer,style="Physique.TFrame")
    title.pack(fill="x",pady=(0,12))
    ttk.Label(title,text="COG / PHYSIQUE",style="Physique.TLabel",font=("Segoe UI",20,"bold")).pack(side="left")
    status=tk.StringVar(value="LOCKED • Local vault")
    ttk.Label(title,textvariable=status,style="Physique.TLabel").pack(side="right")
    tabs=ttk.Notebook(outer)
    tabs.pack(fill="both",expand=True)
    pages={}
    for name in ("Command","Check-ins","Training log","Personal bests","Prep planner","AI Coach","Privacy"):
        page=ttk.Frame(tabs,style="Physique.TFrame",padding=16)
        tabs.add(page,text=name)
        pages[name]=page
    def button(parent,label,fn):
        return ttk.Button(parent,text=label,command=fn,style="Physique.TButton")
    def fields(parent,spec):
        form=ttk.Frame(parent,style="Physique.TFrame")
        form.pack(fill="x",pady=8)
        result={}
        for index,(key,label,initial) in enumerate(spec):
            col=(index%3)*2; row=index//3
            ttk.Label(form,text=label,style="Physique.TLabel").grid(row=row,column=col,padx=5,pady=6,sticky="w")
            field=ttk.Entry(form,width=18)
            field.grid(row=row,column=col+1,padx=5,pady=6,sticky="ew")
            field.insert(0,initial)
            result[key]=field
        return result
    def table(parent,columns,widths):
        wrap=ttk.Frame(parent,style="Physique.TFrame")
        wrap.pack(fill="both",expand=True,pady=8)
        tree=ttk.Treeview(wrap,columns=columns,show="headings",style="Physique.Treeview",selectmode="browse")
        for col,width in zip(columns,widths):
            tree.heading(col,text=col)
            tree.column(col,width=width,minwidth=65)
        scroll=ttk.Scrollbar(wrap,orient="vertical",command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        return tree
    def fill(tree,rows):
        tree.delete(*tree.get_children())
        for key,values in rows:
            tree.insert("","end",iid=key,values=values)
    def selected(tree):
        rows=tree.selection()
        if len(rows)!=1:
            raise ValueError("Select one record.")
        return rows[0]
    today=dt.date.today().isoformat()
    command=pages["Command"]
    cards=tk.Frame(command,bg=bg)
    cards.pack(fill="x",pady=6)
    values={}
    for i,(key,label) in enumerate([("target","CONTEST COUNTDOWN"),("weight","7-DAY WEIGHT AVG"),("sleep","7-DAY SLEEP AVG"),("sets","7-DAY LOGGED SETS")]):
        card=tk.Frame(cards,bg=panel,padx=16,pady=14)
        card.grid(row=0,column=i,sticky="nsew",padx=4)
        cards.columnconfigure(i,weight=1)
        tk.Label(card,text=label,bg=panel,fg=muted,font=("Segoe UI",10)).pack(anchor="w")
        value=tk.StringVar(value="—")
        tk.Label(card,textvariable=value,bg=panel,fg=accent,font=("Segoe UI",21,"bold")).pack(anchor="w")
        values[key]=value
    chart=tk.Canvas(command,bg=panel,height=230,highlightthickness=0)
    chart.pack(fill="x",pady=12)
    detail=tk.StringVar(value="Unlock to review your records.")
    ttk.Label(command,textvariable=detail,style="Physique.TLabel",justify="left",wraplength=900).pack(anchor="w",pady=6)
    check=pages["Check-ins"]
    cf=fields(check,[("date","Date",today),("weight_kg","Weight kg",""),("sleep_hours","Sleep hours",""),("training_minutes","Training minutes",""),("adherence_pct","Adherence %","")])
    cb=ttk.Frame(check,style="Physique.TFrame");cb.pack(fill="x")
    ct=table(check,("Date","Weight kg","Sleep h","Minutes","Adherence %"),(150,120,120,120,140))
    train=pages["Training log"]
    tf=fields(train,[("date","Date",today),("exercise","Exercise",""),("reps","Reps",""),("weight","Load kg",""),("rpe","RPE (optional)","")])
    tb=ttk.Frame(train,style="Physique.TFrame");tb.pack(fill="x")
    training_detail=tk.StringVar(value="Unlock to review training volume.")
    ttk.Label(train,textvariable=training_detail,style="Physique.TLabel",wraplength=900).pack(anchor="w",pady=5)
    tt=table(train,("Date","Exercise","Reps","Load kg","RPE"),(120,260,90,110,90))
    best=pages["Personal bests"]
    ttk.Label(best,text="Heaviest recorded set per exercise (ties: more reps). Not estimated 1RM.",style="Physique.TLabel",wraplength=850).pack(anchor="w",pady=5)
    bt=table(best,("Exercise","Load kg","Reps","Date"),(260,140,100,150))
    prep=pages["Prep planner"]
    pf=fields(prep,[("target","Contest target",""),("date","Milestone date",today),("title","Milestone","")])
    pb=ttk.Frame(prep,style="Physique.TFrame");pb.pack(fill="x")
    pt=table(prep,("Date","Milestone","Status"),(150,420,120))
    from .physique_coach_ui import mount_coach
    clear_coach=mount_coach(pages["AI Coach"],stage=coach_stage)
    privacy=pages["Privacy"]
    ttk.Label(privacy,text="Private by design",style="Physique.TLabel",font=("Segoe UI",18,"bold")).pack(anchor="w")
    ttk.Label(privacy,text="Encrypted at rest. No automatic upload, cloud analysis, MCP access or agent execution. Unlocking displays records locally; it is not protection against a compromised computer. Lock clears the displayed data and form fields. Passphrases are requested for every write and are not retained as a session credential. Keep a secure backup before upgrading; old versions cannot read a migrated v2 file.",style="Physique.TLabel",wraplength=800,justify="left").pack(anchor="w",pady=14)
    current={"rows":[]}
    def fmt(x):
        return "—" if x is None else str(x)
    def plot(rows):
        chart.delete("all")
        width=max(chart.winfo_width(),400); height=230
        chart.create_text(18,18,text="BODY WEIGHT • LAST 30 DAYS",fill=muted,anchor="w",font=("Segoe UI",10,"bold"))
        end=dt.date.today(); start=end-dt.timedelta(days=29)
        points=[(training.date(r["date"]),r["weight_kg"]) for r in rows if r["weight_kg"] is not None and start<=training.date(r["date"])<=end]
        if not points:
            chart.create_text(width/2,height/2,text="No recorded weights in this period",fill=muted)
            return
        low=min(y for _,y in points);high=max(y for _,y in points)
        pad=max((high-low)*0.15,0.5);low-=pad;high+=pad
        left=64;right=width-24;top=45;bottom=height-32
        for i in range(4):
            y=top+(bottom-top)*i/3
            v=high-(high-low)*i/3
            chart.create_line(left,y,right,y,fill="#2d4156")
            chart.create_text(left-8,y,text=f"{v:.1f}",anchor="e",fill=muted)
        coords=[]
        for day,value in points:
            x=left+(right-left)*(day-start).days/29
            y=bottom-(bottom-top)*(value-low)/(high-low)
            coords.extend([x,y])
        if len(coords)>2: chart.create_line(*coords,fill=accent,width=2)
        for x,y in zip(coords[::2],coords[1::2]):
            chart.create_oval(x-3,y-3,x+3,y+3,fill=accent,outline="")
        chart.create_text(left,bottom+17,text=start.isoformat(),anchor="w",fill=muted)
        chart.create_text(right,bottom+17,text=end.isoformat(),anchor="e",fill=muted)
    chart.bind("<Configure>",lambda e:plot(current["rows"]))
    def render(state):
        s=summary(state);a=training.analytics(state)
        current["rows"]=sorted(state["records"],key=lambda r:r["date"])
        days=s["days_until_target"]
        values["target"].set("—" if days is None else (f"{days} d" if days>=0 else f"{-days} d past"))
        for k,metric,unit in (("weight","weight_kg"," kg"),("sleep","sleep_hours"," h")):
            v=s["metrics"][metric]["last_7_days"]["mean"]
            values[k].set("—" if v is None else f"{v:.1f}"+unit)
        values["sets"].set(str(a["current"]["sets"]))
        detail.set("7-day comparison • change versus prior 7 days (no missing values counted as zero)\n"+
                   " | ".join(f"{k}: {fmt(v['change'])} (n={v['last_7_days']['count']})" for k,v in s["metrics"].items())+
                   f"\nPrep milestones overdue: {a['overdue']} • Descriptive, not prescriptive.")
        training_detail.set(f"Last 7 days: {a['current']['sessions']} sessions • {a['current']['sets']} sets • {a['current']['volume_kg']:,.1f} kg external-load volume | Prior 7 days: {a['prior']['volume_kg']:,.1f} kg")
        fill(ct,[(r["date"],[fmt(r[k]) for k in ("date","weight_kg","sleep_hours","training_minutes","adherence_pct")]) for r in reversed(current["rows"])])
        fill(tt,[(r["id"],[fmt(r[k]) for k in ("date","exercise","reps","weight_kg","rpe")]) for r in sorted(state["sets"],key=lambda r:r["date"],reverse=True)])
        fill(bt,[(r["id"],(r["exercise"],r["weight_kg"],r["reps"],r["date"])) for r in a["best_sets"]])
        fill(pt,[(r["id"],(r["date"],r["title"],"Complete" if r["done"] else "Open")) for r in a["milestones"]])
        pf["target"].delete(0,"end");pf["target"].insert(0,state["target_date"] or "")
        plot(current["rows"])
        status.set("DISPLAY UNLOCKED • Local only")
    def clear_fields():
        for form in (cf,tf,pf):
            for entry in form.values():
                entry.delete(0,"end")
            if "date" in form:form["date"].insert(0,today)
    def lock():
        clear_coach()
        current["rows"]=[]
        for v in values.values():v.set("—")
        for tree in (ct,tt,bt,pt):fill(tree,[])
        clear_fields();chart.delete("all")
        detail.set("Unlock to review your records.")
        training_detail.set("Unlock to review training volume.")
        status.set("LOCKED • Local vault")
    def perform(action):
        try:
            password=simpledialog.askstring("Physique vault","Local vault passphrase:",show="*",parent=win)
            if password is None:return
            if action=="init":
                confirm=simpledialog.askstring("Confirm","Repeat passphrase:",show="*",parent=win)
                if confirm!=password:raise ValueError("Passphrases do not match.")
                vault.initialize(password)
            elif action in ("add","replace"):
                row={"date":cf["date"].get()}
                for key in FIELDS-{"date"}:
                    raw=cf[key].get().strip();row[key]=float(raw) if raw else None
                (vault.add if action=="add" else vault.replace)(password,row)
            elif action=="delete":
                vault.delete(password,selected(ct))
            elif action=="set":
                raw=tf["rpe"].get().strip()
                row=training.new_set(tf["date"].get(),tf["exercise"].get(),int(tf["reps"].get()),float(tf["weight"].get()),float(raw) if raw else None)
                vault.add_set(password,row)
            elif action=="delete-set":vault.change_item(password,"sets",selected(tt),"delete")
            elif action=="target":vault.set_target(password,pf["target"].get().strip() or None)
            elif action=="milestone":vault.add_milestone(password,training.new_milestone(pf["date"].get(),pf["title"].get()))
            elif action=="toggle":vault.change_item(password,"milestones",selected(pt),"toggle")
            elif action=="delete-milestone":vault.change_item(password,"milestones",selected(pt),"delete")
            render(vault.read(password))
        except (ValueError,OSError) as exc:
            messagebox.showerror("Physique",str(exc),parent=win)
    def confirmed(action):
        if messagebox.askyesno("Confirm deletion","Permanently remove the selected item?",parent=win):perform(action)
    toolbar=ttk.Frame(outer,style="Physique.TFrame");toolbar.pack(fill="x",pady=8)
    for label,action in [("Create vault","init"),("Unlock / refresh","read")]:
        button(toolbar,label,lambda a=action:perform(a)).pack(side="left",padx=4)
    button(toolbar,"Lock display",lock).pack(side="right")
    for parent,actions in [(cb,[("Save new","add"),("Replace date","replace"),("Delete selected","delete")]),(tb,[("Log set","set"),("Delete set","delete-set")]),(pb,[("Save target","target"),("Add milestone","milestone"),("Toggle completion","toggle"),("Delete milestone","delete-milestone")])]:
        for label,action in actions:
            button(parent,label,lambda a=action:confirmed(a) if a.startswith("delete") else perform(a)).pack(side="left",padx=3)
    lock()
    if parent is None:win.mainloop()
    return win
