"""Native Coach Command panel. Prompts and replies are held only in process memory."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from .physique_coach import CoachQueue, ROLES

def mount_coach(page, stage=None):
    queue=CoachQueue()
    root=page.winfo_toplevel()
    style="Physique.TLabel"
    frame_style="Physique.TFrame"
    ttk.Label(page,text="AI COACH COMMAND",style=style,font=("Segoe UI",17,"bold")).pack(anchor="w")
    ttk.Label(page,text="Specialists prepare drafts; you decide what to share and approve. No automatic vault access or execution.",style=style,wraplength=900).pack(anchor="w",pady=(3,8))
    top=ttk.Frame(page,style=frame_style);top.pack(fill="x")
    role=tk.StringVar(value="commander")
    ttk.Combobox(top,textvariable=role,values=tuple(ROLES),state="readonly",width=17).pack(side="left")
    scope=tk.StringVar()
    def show_scope(*_):
        scope.set(ROLES[role.get()][0]+" • "+ROLES[role.get()][1])
    role.trace_add("write",show_scope);show_scope()
    ttk.Label(top,textvariable=scope,style=style,wraplength=680).pack(side="left",padx=10)
    ttk.Label(page,text="Mission topic (do not include identifiers, private records or credentials)",style=style).pack(anchor="w",pady=(7,1))
    task=tk.Text(page,height=3,wrap="word",bg="#152336",fg="#e5eef9",insertbackground="white")
    task.pack(fill="x")
    controls=ttk.Frame(page,style=frame_style);controls.pack(fill="x",pady=5)
    split=ttk.Panedwindow(page,orient="horizontal")
    split.pack(fill="both",expand=True)
    left=ttk.Frame(split,style=frame_style);right=ttk.Frame(split,style=frame_style)
    split.add(left,weight=1);split.add(right,weight=3)
    tree=ttk.Treeview(left,columns=("role","status"),show="headings",selectmode="browse",style="Physique.Treeview",height=8)
    for key,width in (("role",120),("status",120)):
        tree.heading(key,text=key.title());tree.column(key,width=width,minwidth=85)
    tree.pack(fill="both",expand=True)
    detail=ttk.Notebook(right);detail.pack(fill="both",expand=True)
    prompt_page=ttk.Frame(detail);response_page=ttk.Frame(detail)
    detail.add(prompt_page,text="Exact prompt");detail.add(response_page,text="Returned draft")
    def text_box(parent,readonly=False):
        box=tk.Text(parent,wrap="word",bg="#152336",fg="#e5eef9",insertbackground="white",height=10)
        scroll=ttk.Scrollbar(parent,orient="vertical",command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right",fill="y");box.pack(fill="both",expand=True)
        if readonly:box.configure(state="disabled")
        return box
    prompt=text_box(prompt_page,True);reply=text_box(response_page)
    status=tk.StringVar(value="Local session queue • no messages sent")
    ttk.Label(page,textvariable=status,style=style,wraplength=900).pack(anchor="w",pady=5)
    actions=ttk.Frame(page,style=frame_style);actions.pack(fill="x")
    def chosen():
        rows=tree.selection()
        if len(rows)!=1:raise ValueError("Select a mission first.")
        return queue.get(rows[0])
    def replace(widget,value,readonly=False):
        widget.configure(state="normal")
        widget.delete("1.0","end");widget.insert("1.0",value)
        if readonly:widget.configure(state="disabled")
    def display(event=None):
        try:m=chosen()
        except ValueError:return
        replace(prompt,m.prompt,True);replace(reply,m.response)
        status.set(m.state.replace("_"," ").upper()+(" • "+m.review if m.review else " • "+ROLES[m.role][0]))
    def update(m):
        if tree.exists(m.id):tree.item(m.id,values=(m.role,m.state))
        else:tree.insert("","end",iid=m.id,values=(m.role,m.state))
        tree.selection_set(m.id);tree.focus(m.id);display()
    tree.bind("<<TreeviewSelect>>",display)
    def safe(action):
        try:action()
        except (ValueError,RuntimeError) as exc:messagebox.showerror("Coach Command",str(exc),parent=root)
    def create():
        m=queue.create(role.get(),task.get("1.0","end-1c"))
        update(m);detail.select(prompt_page)
        task.delete("1.0","end")
    def team():
        for m in queue.create_team(task.get("1.0","end-1c")):update(m)
        task.delete("1.0","end");detail.select(prompt_page)
    def synthesize(role):
        if not messagebox.askyesno("Review handoff","Build a new mission from the accepted reports in this team? Inspect its full contents before sending to Hermes.",parent=root):return
        update(queue.synthesize(chosen().id,role));detail.select(prompt_page)
    def handoff():
        m=chosen()
        if m.state!="draft":raise ValueError("Create a new mission to stage again.")
        if stage is None:
            raise ValueError("Open Physique from Nexus to stage a prompt, or manually select and copy this exact prompt.")
        if not messagebox.askyesno("Stage for Hermes","Stage the displayed prompt in the Nexus composer? This does not send it. Check the selected profile, model provider and exact contents before pressing Send.",parent=root):return
        if stage(m.prompt):
            update(queue.staged(m.id))
    def save_reply():
        m=chosen()
        update(queue.attach_response(m.id,reply.get("1.0","end-1c")))
        detail.select(response_page)
    def decide(decision):
        m=chosen()
        note=simpledialog.askstring("Review note","Why accept or reject this draft? Acceptance records review only, not execution.",parent=root)
        if note is None:return
        update(queue.decide(m.id,decision,note))
    def clear():
        queue.clear();tree.delete(*tree.get_children())
        task.delete("1.0","end");replace(prompt,"",True);replace(reply,"")
        status.set("Local session queue cleared • previously staged or sent messages are not recalled")
    def confirm_clear():
        if messagebox.askyesno("Clear session","Remove all local missions and drafts? This cannot recall messages in Nexus or Hermes.",parent=root):clear()
    for parent,label,action in ((controls,"Create mission",create),(controls,"Create 4-agent team",team),(controls,"Stage in Nexus",handoff),(controls,"Clear queue",confirm_clear),
                                (actions,"Save pasted reply",save_reply),(actions,"Accept reviewed draft",lambda:decide("accepted")),
                                (actions,"Reject draft",lambda:decide("rejected")),(actions,"Safety review",lambda:synthesize("safety")),(actions,"Commander synthesis",lambda:synthesize("commander"))):
        ttk.Button(parent,text=label,command=lambda f=action:safe(f),style="Physique.TButton").pack(side="left",padx=3)
    ttk.Label(page,text="Paste the Hermes reply into Returned draft, then Save pasted reply. Review is not clinical approval. No queue persistence; switching missions discards unsaved reply edits.",style=style,wraplength=900).pack(anchor="w",pady=3)
    return clear, queue.accepted_feedback
