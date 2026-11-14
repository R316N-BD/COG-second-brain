"""Local Windows-friendly desktop prototype; no remote services or shell access."""
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from . import cli, memory, integrations, operations

def run(data_dir):
    data = cli.init_vault(data_dir)
    root = tk.Tk()
    root.title("COG Command — Local Preview")
    root.geometry("1120x720")
    root.minsize(800, 520)
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(bg="#111827")
    style.configure("TFrame", background="#111827")
    style.configure("TLabel", background="#111827", foreground="#e5e7eb")
    style.configure("TButton", padding=8)
    shell = ttk.Frame(root, padding=16)
    shell.pack(fill="both", expand=True)
    ttk.Label(shell, text="COG // COMMAND", font=("Segoe UI", 22, "bold")).pack(anchor="w")
    ttk.Label(shell, text=f"Local vault: {data / 'vault'}").pack(anchor="w", pady=(2,12))
    toolbar = ttk.Frame(shell)
    toolbar.pack(fill="x")
    query = tk.StringVar()
    scope = tk.StringVar(value="04-projects")
    ttk.Entry(toolbar, textvariable=query, width=42).pack(side="left", padx=(0,8))
    ttk.Combobox(toolbar, textvariable=scope, values=cli.VAULT_FOLDERS, state="readonly", width=20).pack(side="left")
    text = tk.Text(shell, background="#0b1220", foreground="#dbeafe", insertbackground="#ffffff",
                   font=("Consolas", 11), wrap="word", padx=14, pady=14)
    text.pack(fill="both", expand=True, pady=12)
    text.configure(state="disabled")
    status = tk.StringVar(value="Ready — local operator view")
    ttk.Label(shell, textvariable=status).pack(anchor="w")
    buttons = []
    def display(result):
        text.configure(state="normal")
        text.delete("1.0", "end")
        text.insert("1.0", json.dumps(result, indent=2, ensure_ascii=False))
        text.configure(state="disabled")
    def execute(action):
        for button in buttons:
            button.configure(state="disabled")
        status.set("Working…")
        def worker():
            try:
                result = action()
                root.after(0, lambda: finish(result))
            except Exception as exc:
                error = str(exc)
                root.after(0, lambda: finish({"error": error}))
        threading.Thread(target=worker, daemon=True).start()
    def finish(result):
        display(result)
        status.set("Ready")
        for button in buttons:
            button.configure(state="normal")
    def add_button(parent, label, action):
        button = ttk.Button(parent, text=label, command=action)
        button.pack(side="left", padx=4)
        buttons.append(button)
    def search():
        q, s = query.get(), scope.get()
        execute(lambda: memory.search(data, q, scope=s))
    add_button(toolbar, "Recall", search)
    add_button(toolbar, "Refresh index", lambda: execute(lambda: memory.rebuild(data, incremental=True)))
    nav = ttk.Frame(shell)
    nav.pack(fill="x", before=toolbar, pady=(0,8))
    for label, action in [
        ("System health", lambda: cli.doctor(data)),
        ("Integrations", integrations.discover),
        ("Jobs", lambda: operations.list_jobs(data)),
        ("Proposals", lambda: operations.proposals(data)),
        ("Audit", lambda: operations.audit_events(data))
    ]:
        add_button(nav, label, lambda fn=action: execute(fn))
    root.mainloop()
