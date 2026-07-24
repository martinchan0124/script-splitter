"""InstanceDB Browser — step-by-step entity change viewer."""
import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path

class InstanceDBBrowser:
    def __init__(self, parent, json_path):
        self.win = tk.Toplevel(parent)
        self.win.title("InstanceDB Browser")
        self.win.geometry("820x560")
        data = json.loads(Path(json_path).read_text())
        self.history = data.get("changes_history", [])
        self.chars = data.get("characters", {})
        self.ves = data.get("visual_elements", {})

        top = ttk.Frame(self.win, padding=10)
        top.pack(fill="x")
        meta = data.get("metadata", {})
        ttk.Label(top, text="InstanceDB Browser", font=("Helvetica", 14, "bold")).pack(side="left")
        ttk.Label(top, text=f"{meta.get('scenes_processed',0)} scenes | {len(self.chars)} chars | {len(self.ves)} VEs",
                  foreground="gray").pack(side="left", padx=(12, 0))

        paned = ttk.PanedWindow(self.win, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        left = ttk.Frame(paned)
        paned.add(left, weight=1)
        self.tree = ttk.Treeview(left, columns=("changes",), show="tree", height=20)
        self.tree.heading("#0", text="Scene")
        self.tree.column("#0", width=80)
        self.tree.pack(fill="both", expand=True)

        right = ttk.Frame(paned, padding=(10, 0, 0, 0))
        paned.add(right, weight=2)
        nb = ttk.Notebook(right)
        nb.pack(fill="both", expand=True)
        self.summary = tk.Text(nb, wrap="word", font=("Menlo", 9))
        nb.add(self.summary, text="Summary")
        self.char_t = tk.Text(nb, wrap="word", font=("Menlo", 9))
        nb.add(self.char_t, text="Characters")
        self.ve_t = tk.Text(nb, wrap="word", font=("Menlo", 9))
        nb.add(self.ve_t, text="V. Elements")

        for h in self.history:
            sid = h.get("scene_id", "?")
            n = sum(len(h.get(k,[])) for k in ("new_characters","new_visual_elements","new_locations"))
            self.tree.insert("", "end", iid=sid, text=f"{sid} ({n})" if n else sid)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        if not self.history:
            self.summary.insert("end", "No history. Run --wash first.")

    def _on_select(self, e):
        sel = self.tree.selection()
        if not sel: return
        sid = sel[0]
        for w in (self.summary, self.char_t, self.ve_t):
            w.delete("1.0", "end")
        h = next((x for x in self.history if x.get("scene_id") == sid), None)
        if not h: return
        nc, nu = h.get("new_characters",[]), h.get("updated_characters",[])
        nv, nl = h.get("new_visual_elements",[]), h.get("new_locations",[])
        lines = [f"=== {sid} ==="]
        if nc: lines.append(f"+ {len(nc)} chars"); [lines.append(f"  + {c['name']}") for c in nc]
        if nu: lines.append(f"~ {len(nu)} updated"); [lines.append(f"  ~ {c['name']}") for c in nu]
        if nv: lines.append(f"+ {len(nv)} VEs"); [lines.append(f"  + {v['name']} ({v.get('type','?')})") for v in nv]
        if nl: lines.append(f"+ {len(nl)} locs"); [lines.append(f"  + {l.get('class_id','?')}") for l in nl]
        if not any([nc, nu, nv, nl]): lines.append("No changes")
        self.summary.insert("end", "\n".join(lines))
        for c in nc: self.char_t.insert("end", f"[NEW] {c['name']}\n")
        for c in nu: self.char_t.insert("end", f"[UPD] {c['name']}\n")
        for v in nv: self.ve_t.insert("end", f"[NEW] {v['name']} ({v.get('type','?')})\n")
        if not nc and not nu: self.char_t.insert("end", "No changes.")
        if not nv: self.ve_t.insert("end", "No changes.")
