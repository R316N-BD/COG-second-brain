"""COG Nexus desktop companion. Hermes owns sessions; COG owns private memory."""
import json
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from . import cli, memory
from .nexus_gateway import HermesClient, GatewayError
from .nexus_browser import DedicatedBrowser
from .nexus_rich import parse, INSTRUCTIONS

def run(data_dir):
    data=cli.init_vault(data_dir)
    root=tk.Tk()
    root.title("COG NEXUS | Hermes Operations")
    root.geometry("1180x760")
    root.minsize(800,550)
    root.configure(bg="#0b1220")
    style=ttk.Style(root)
    style.theme_use("clam")
    for name in ("TFrame","TLabel","TCheckbutton"):
        style.configure(name,background="#0b1220",foreground="#e5e7eb")
    style.configure("TButton",padding=7)
    style.configure("Treeview",background="#111c2d",fieldbackground="#111c2d",foreground="#e5e7eb",rowheight=28)
    commands=queue.Queue(maxsize=12)
    inbox=queue.Queue(maxsize=1000)
    stop=threading.Event()
    browser=DedicatedBrowser(data)
    state={"online":False,"busy":False,"pending":False,"uncertain":False,"session":None,"owner":None,
           "reply":"","attached":None}
    status=tk.StringVar(value="Offline — connect Hermes dashboard")
    base=tk.StringVar(value="http://127.0.0.1:9119")
    token=tk.StringVar(value=os.environ.get("HERMES_DASHBOARD_SESSION_TOKEN",""))
    if token.get().startswith("file:"):
        token.set("")
    profile=tk.StringVar()
    rich=tk.BooleanVar(value=True)
    body=ttk.Frame(root,padding=14)
    body.pack(fill="both",expand=True)
    ttk.Label(body,text="COG // NEXUS",font=("Segoe UI",24,"bold")).pack(anchor="w")
    ttk.Label(body,textvariable=status).pack(anchor="w",pady=(0,8))
    connection=ttk.Frame(body)
    connection.pack(fill="x")
    ttk.Entry(connection,textvariable=base,width=28).pack(side="left")
    ttk.Label(connection,text="Dashboard token").pack(side="left",padx=5)
    ttk.Entry(connection,textvariable=token,show="*",width=25).pack(side="left")
    tabs=ttk.Notebook(body)
    tabs.pack(fill="both",expand=True,pady=10)
    chat,team,visual,browse,knowledge=[ttk.Frame(tabs,padding=10) for _ in range(5)]
    for page,title in zip((chat,team,visual,browse,knowledge),("Command","Workforce","Visual replies","Browser","COG memory")):
        tabs.add(page,text=title)
    bar=ttk.Frame(chat)
    bar.pack(fill="x")
    ttk.Label(bar,text="Hermes profile").pack(side="left")
    picker=ttk.Combobox(bar,textvariable=profile,state="readonly",width=26)
    picker.pack(side="left",padx=6)
    ttk.Checkbutton(bar,text="Visual replies",variable=rich).pack(side="left")
    def text(parent,height=None):
        kw={"height":height} if height else {}
        return tk.Text(parent,bg="#111c2d",fg="#dbeafe",insertbackground="white",wrap="word",font=("Segoe UI",11),padx=10,pady=8,**kw)
    transcript=text(chat)
    transcript.pack(fill="both",expand=True,pady=8)
    transcript.configure(state="disabled")
    composer=text(chat,4)
    composer.pack(fill="x")
    actions=ttk.Frame(chat)
    actions.pack(fill="x",pady=4)
    def table(parent,columns):
        view=ttk.Treeview(parent,columns=columns,show="headings",height=7)
        for col in columns:
            view.heading(col,text=col.title())
            view.column(col,width=150)
        view.pack(fill="both",expand=True)
        return view
    office=tk.Canvas(team,bg="#111c2d",height=135,highlightthickness=0)
    office.pack(fill="x",pady=(0,8))
    roster=table(team,("profile","name","model","provider"))
    ttk.Label(team,text="Live sessions for selected profile").pack(anchor="w",pady=(8,2))
    sessions=table(team,("title","status","model","source"))
    rich_text=text(visual)
    rich_text.pack(fill="both",expand=True)
    rich_text.configure(state="disabled")
    chart=tk.Canvas(visual,bg="#111c2d",height=190,highlightthickness=0)
    chart.pack(fill="x",pady=5)
    browser_label=tk.StringVar(value="Not attached")
    ttk.Label(browse,text="Shared visible browser",font=("Segoe UI",16,"bold")).pack(anchor="w")
    ttk.Label(browse,text="Fresh isolated browser profile; do not sign into sensitive accounts. Hermes controls browser actions through its own tools.",wraplength=760).pack(anchor="w",pady=10)
    ttk.Label(browse,textvariable=browser_label,wraplength=760).pack(anchor="w")
    browser_bar=ttk.Frame(browse)
    browser_bar.pack(anchor="w",pady=8)
    ttk.Label(browse,text="After attachment, send a browser task to that profile in Command. Watch the separate browser window.").pack(anchor="w")
    search=tk.StringVar()
    scope=tk.StringVar(value="04-projects")
    kbar=ttk.Frame(knowledge)
    kbar.pack(fill="x")
    ttk.Entry(kbar,textvariable=search,width=35).pack(side="left")
    ttk.Combobox(kbar,textvariable=scope,values=cli.VAULT_FOLDERS,state="readonly",width=19).pack(side="left",padx=5)
    notes=text(knowledge)
    notes.pack(fill="both",expand=True,pady=8)
    notes.configure(state="disabled")
    panel=tk.Toplevel(root)
    panel.title("COG Quick Command")
    panel.geometry(f"370x320+{max(0,root.winfo_screenwidth()-410)}+100")
    panel.attributes("-topmost",True)
    panel.withdraw()
    panel.protocol("WM_DELETE_WINDOW",panel.withdraw)
    mini=ttk.Frame(panel,padding=10)
    mini.pack(fill="both",expand=True)
    ttk.Label(mini,text="COG // QUICK COMMAND",font=("Segoe UI",14,"bold")).pack(anchor="w")
    ttk.Label(mini,textvariable=profile).pack(anchor="w")
    ttk.Label(mini,textvariable=status,wraplength=340).pack(anchor="w",pady=6)
    quick=text(mini,5)
    quick.pack(fill="both",expand=True)
    mini_bar=ttk.Frame(mini)
    mini_bar.pack(fill="x",pady=5)

    def write(widget,value,clear=False):
        widget.configure(state="normal")
        if clear:
            widget.delete("1.0","end")
        widget.insert("end",value)
        widget.see("end")
        widget.configure(state="disabled")

    def emit(kind,value):
        while not stop.is_set():
            try:
                inbox.put((kind,value),timeout=.2)
                return
            except queue.Full:
                pass

    def put(action,*args):
        if state["pending"] or (state["busy"] and action!="interrupt"):
            return False
        try:
            commands.put_nowait((action,args))
        except queue.Full:
            return False
        state["pending"]=True
        return True

    def connect():
        if state["attached"]:
            if state["online"]:
                messagebox.showwarning("COG","Detach the current browser before reconnecting.")
                return
            if not messagebox.askyesno("COG","Close the dedicated browser and disconnect its profile in Hermes first. Have you done that?"):
                return
            state["attached"]=None
            browser_label.set("Attachment unknown; verify in Hermes.")
        if state["uncertain"] and not messagebox.askyesno("COG","Check the previous turn in Hermes before reconnecting. Continue?"):
            return
        if put("connect",base.get(),token.get()):
            status.set("Connecting…")

    def refresh():
        if state["online"] and not state["busy"] and profile.get():
            put("refresh",profile.get())

    def send(widget):
        if not state["online"] or state["busy"] or state["pending"] or state["uncertain"] or not profile.get():
            messagebox.showwarning("COG","Connect and select an idle profile. Inspect uncertain turns in Hermes before retrying.")
            return
        content=widget.get("1.0","end-1c").strip()
        payload=content+("\n\n"+INSTRUCTIONS if rich.get() else "")
        if not content or len(payload.encode("utf-8"))>32768:
            return
        sid=state["session"] if state["owner"]==profile.get() else None
        if put("send",profile.get(),sid,payload):
            state["busy"]=True
            state["reply"]=""
            status.set("Submitting to "+profile.get())
            write(transcript,"\nYOU ["+profile.get()+"]\n"+content+"\n\nHERMES\n")
            widget.delete("1.0","end")

    def interrupt():
        if state["online"] and state["busy"] and state["session"] and not state["pending"]:
            if messagebox.askyesno("Interrupt turn","Ask Hermes to interrupt the current turn?"):
                put("interrupt",state["owner"],state["session"])

    def new():
        if state["busy"] or state["pending"]:
            return
        if state["uncertain"] and not messagebox.askyesno("COG","Have you checked the prior turn in Hermes? Start a new session?"):
            return
        state.update(session=None,owner=None,uncertain=False)
        write(transcript,"",True)
        status.set("Ready — next message starts a new session")

    def attach():
        if not state["online"] or not profile.get() or state["attached"]:
            return
        if messagebox.askyesno("Attach browser","Attach a dedicated browser to "+profile.get()+"? This replaces its existing browser connection. Use a trusted profile; do not sign in to sensitive accounts."):
            put("attach",profile.get())

    def detach():
        if state["online"] and state["attached"] and messagebox.askyesno("Detach","Disconnect the browser from "+state["attached"]+"?"):
            put("detach",state["attached"])

    def button(parent,label,action,side="left"):
        ttk.Button(parent,text=label,command=action).pack(side=side,padx=4)

    button(connection,"Connect",connect)
    button(connection,"Refresh",refresh)
    button(connection,"Quick panel",panel.deiconify,"right")
    button(actions,"Send",lambda:send(composer),"right")
    button(actions,"New session",new)
    button(actions,"Interrupt",interrupt)
    button(mini_bar,"Send",lambda:send(quick),"right")
    button(mini_bar,"Open workspace",root.deiconify)
    button(browser_bar,"Launch + attach",attach)
    button(browser_bar,"Detach",detach)
    button(kbar,"Recall",lambda:put("recall",search.get(),scope.get()))
    button(kbar,"Refresh index",lambda:put("index"))
    picker.bind("<<ComboboxSelected>>",lambda _:refresh())

    def worker():
        client=None
        while not stop.is_set():
            try:
                action,args=commands.get(timeout=.1)
            except queue.Empty:
                if client:
                    try:
                        client.poll()
                    except GatewayError:
                        client.close()
                        client=None
                        emit("offline","Disconnected — inspect Hermes before resending.")
                continue
            try:
                if action=="connect":
                    if client:
                        client.close()
                    client=HermesClient(*args,event=lambda e:emit("event",e))
                    client.connect()
                    emit("connected",client.profiles())
                elif action=="refresh" and client:
                    emit("profiles",client.profiles())
                    emit("sessions",(args[0],client.active(args[0])))
                elif action=="send" and client:
                    owner,sid,payload=args
                    sid=sid or client.new_session(owner)
                    emit("session",(owner,sid))
                    emit("receipt",client.submit(owner,sid,payload)["status"])
                elif action=="interrupt" and client:
                    client.request("session.interrupt",{"profile":args[0],"session_id":args[1]})
                    emit("interrupt","Interrupt requested — wait for Hermes to confirm the turn ended.")
                elif action=="attach" and client:
                    port=browser.launch()
                    result=client.browser(args[0],"connect",port)
                    if result.get("connected") is not True:
                        raise GatewayError("Browser attachment unconfirmed.")
                    emit("browser",(args[0],port))
                elif action=="detach" and client:
                    result=client.browser(args[0],"disconnect")
                    if result.get("connected") is not False:
                        raise GatewayError("Browser detach unconfirmed.")
                    emit("browser",(None,None))
                elif action=="recall":
                    emit("notes",memory.search(data,args[0],scope=args[1]))
                elif action=="index":
                    emit("notes",memory.rebuild(data,incremental=True))
                else:
                    raise GatewayError("Connect Hermes first.")
            except Exception as exc:
                msg=str(exc) if isinstance(exc,GatewayError) else "Operation failed; inspect configuration and runtime."
                if action=="connect":
                    if client:
                        client.close()
                    client=None
                    emit("offline",msg)
                elif action=="send":
                    emit("uncertain",msg)
                else:
                    emit("error",msg)
            finally:
                emit("done",None)
        if client:
            client.close()

    def render(reply):
        blocks=parse(reply)
        write(rich_text,"",True)
        chart.delete("all")
        bars=None
        for block in blocks:
            write(rich_text,block["title"]+"\n")
            if block["type"]=="table":
                write(rich_text," | ".join(block["columns"])+"\n")
                for row in block["rows"]:
                    write(rich_text," | ".join(row)+"\n")
            else:
                for row in block["rows"]:
                    value=row["value"]
                    if block["type"]=="checklist":
                        value="[x]" if value else "[ ]"
                    write(rich_text,f'{row["label"]}: {value}\n')
                if block["type"]=="bar" and bars is None:
                    bars=block["rows"][:6]
            write(rich_text,"\n")
        if not blocks:
            write(rich_text,"No valid visual blocks in this reply.")
        if bars:
            maximum=max(r["value"] for r in bars) or 1
            width=max(chart.winfo_width()-200,100)
            for i,row in enumerate(bars):
                y=8+i*28
                chart.create_text(5,y+10,text=row["label"][:20],anchor="w",fill="#dbeafe")
                end=125+width*row["value"]/maximum
                chart.create_rectangle(125,y,end,y+18,fill="#38bdf8",outline="")
                chart.create_text(end+5,y+10,text=str(row["value"]),anchor="w",fill="#dbeafe")

    def draw_office(rows):
        office.delete("all")
        width=max(office.winfo_width(),760)
        center=width/2
        office.create_rectangle(center-90,6,center+90,36,fill="#1d4ed8",outline="")
        office.create_text(center,21,text="HERMES RUNTIME",fill="white",font=("Segoe UI",10,"bold"))
        shown=rows[:5]
        for i,row in enumerate(shown):
            x=(i+1)*width/(len(shown)+1)
            office.create_line(center,36,x,68,fill="#64748b")
            office.create_rectangle(x-65,68,x+65,111,fill="#263449",outline="#38bdf8")
            office.create_text(x,82,text=row["title"][:20],fill="white")
            office.create_text(x,99,text="Profile reported",fill="#93c5fd",font=("Segoe UI",8))
        if len(rows)>5:
            office.create_text(center,125,text=f"+{len(rows)-5} more in roster",fill="#94a3b8")
        if not rows:
            office.create_text(center,88,text="No profiles reported",fill="#94a3b8")

    def profiles(rows):
        draw_office(rows)
        names=[r["name"] for r in rows]
        picker["values"]=names
        if profile.get() not in names:
            profile.set(names[0] if names else "")
        roster.delete(*roster.get_children())
        for row in rows:
            roster.insert("","end",values=(row["name"],row["title"],row["model"] or "-",row["provider"] or "-"))

    def event(e):
        kind=e.get("type")
        payload=e.get("payload") or {}
        if not isinstance(payload,dict):
            return
        if kind=="nexus.attention":
            status.set("Unsupported Hermes request — not approved")
            return
        if (e.get("session_id") or payload.get("session_id"))!=state["session"] or not state["session"] or not state["busy"]:
            return
        if kind=="message.delta" and isinstance(payload.get("text"),str):
            part=payload["text"][:max(0,262144-len(state["reply"]))]
            state["reply"]+=part
            write(transcript,part)
        elif kind=="message.complete":
            final=payload.get("text")
            if isinstance(final,str) and final:
                if not state["reply"]:
                    write(transcript,final[:262144])
                elif final[:262144]!=state["reply"]:
                    write(transcript,"\n\nFINAL REPLY\n"+final[:262144])
                state["reply"]=final[:262144]
            render(state["reply"])
            state["busy"]=False
            status.set("Turn ended — "+str(payload.get("status") or "review result"))
        elif kind in {"tool.start","tool.complete","browser.progress","approval.request","clarify.request"}:
            status.set("Hermes: "+kind+" "+str(payload.get("name",""))[:80])

    def drain():
        for _ in range(100):
            try:
                kind,value=inbox.get_nowait()
            except queue.Empty:
                break
            if kind=="done":
                state["pending"]=False
            elif kind=="connected":
                state.update(online=True,busy=False,uncertain=False,session=None,owner=None)
                profiles(value)
                status.set("Connected — choose a profile")
            elif kind=="profiles":
                profiles(value)
            elif kind=="sessions":
                if value[0]==profile.get():
                    sessions.delete(*sessions.get_children())
                    for row in value[1]:
                        sessions.insert("","end",values=tuple(row.get(k) for k in ("title","status","model","source")))
            elif kind=="session":
                state["owner"],state["session"]=value
            elif kind=="receipt":
                if state["busy"]:
                    status.set("Hermes "+value)
            elif kind=="event":
                event(value)
            elif kind=="interrupt":
                status.set(value)
            elif kind=="offline":
                state.update(online=False,busy=False,uncertain=True)
                status.set(value)
            elif kind=="uncertain":
                state.update(busy=False,uncertain=True)
                status.set(value)
            elif kind=="browser":
                state["attached"]=value[0]
                browser_label.set(f"Attached to {value[0]} on loopback port {value[1]} — watch separate window." if value[0] else "Detached. Close the dedicated window.")
            elif kind=="notes":
                write(notes,json.dumps(value,indent=2,ensure_ascii=False),True)
            elif kind=="error":
                status.set(value)
        if not stop.is_set():
            root.after(100,drain)

    def tick():
        refresh()
        if not stop.is_set():
            root.after(10000,tick)

    def close():
        if (state["busy"] or state["attached"]) and not messagebox.askyesno("COG","A turn or browser may still be active in Hermes. Closing Nexus will not cancel or detach it. Close anyway?"):
            return
        stop.set()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW",close)
    threading.Thread(target=worker,daemon=True).start()
    root.after(100,drain)
    root.after(1000,tick)
    root.mainloop()
