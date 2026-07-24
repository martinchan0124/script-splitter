"""InstanceDB Browser — step-by-step entity change viewer.

Locations tab, richer detail, per-entity IDs."""
import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path

class InstanceDBBrowser:
    def __init__(self, parent, json_path):
        self.win = tk.Toplevel(parent)
        self.win.title("InstanceDB Browser")
        self.win.geometry("880x600")
        self.json_path = json_path
        data = json.loads(Path(json_path).read_text())
        self.history = data.get("changes_history", [])
        self.chars = data.get("characters", {})
        self.ves = data.get("visual_elements", {})
        self.locs = data.get("locations", {})

        top = ttk.Frame(self.win, padding=10)
        top.pack(fill="x")
        meta = data.get("metadata", {})
        ttk.Label(top, text="InstanceDB Browser", font=("Helvetica", 14, "bold")).pack(side="left")
        ttk.Label(top,
                  text=f"{meta.get('scenes_processed',0)} scenes | {len(self.chars)} chars | {len(self.locs)} locs | {len(self.ves)} VEs",
                  foreground="gray").pack(side="left", padx=(12, 0))
        ttk.Label(top, text=Path(json_path).name,
                  foreground="gray").pack(side="left", padx=(4, 0))

        paned = ttk.PanedWindow(self.win, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        left = ttk.Frame(paned)
        paned.add(left, weight=1)
        self.tree = ttk.Treeview(left, columns=("changes",), show="tree", height=20)
        self.tree.heading("#0", text="Scene")
        self.tree.column("#0", width=130)
        self.tree.pack(fill="both", expand=True)

        right = ttk.Frame(paned, padding=(10, 0, 0, 0))
        paned.add(right, weight=2)
        nb = ttk.Notebook(right)
        nb.pack(fill="both", expand=True)
        self.summary = tk.Text(nb, wrap="word", font=("Menlo", 9))
        nb.add(self.summary, text="Summary")
        self.loc_t = tk.Text(nb, wrap="word", font=("Menlo", 9))
        nb.add(self.loc_t, text="Locations")
        self.char_t = tk.Text(nb, wrap="word", font=("Menlo", 9))
        nb.add(self.char_t, text="Characters")
        self.ve_t = tk.Text(nb, wrap="word", font=("Menlo", 9))
        nb.add(self.ve_t, text="Visual Elements")

        for h in self.history:
            sid = h.get("scene_id", "?")
            n = sum(len(h.get(k, [])) for k in ("new_characters", "new_visual_elements", "new_locations"))
            self.tree.insert("", "end", iid=sid, text=f"{sid} ({n})" if n else sid)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        if not self.history:
            self.summary.insert("end", "No history. Run --wash first.")

    def _on_select(self, e):
        sel = self.tree.selection()
        if not sel:
            return
        sid = sel[0]
        for w in (self.summary, self.char_t, self.ve_t, self.loc_t):
            w.delete("1.0", "end")
        h = next((x for x in self.history if x.get("scene_id") == sid), None)
        if not h:
            return
        nc = h.get("new_characters", [])
        nu = h.get("updated_characters", [])
        nv = h.get("new_visual_elements", [])
        nl = h.get("new_locations", [])

        # Summary tab
        summary_lines = [f"=== {sid} ==="]
        if nc:
            summary_lines.append(f"\n[+] Characters: {len(nc)}")
            for c in nc:
                summary_lines.append(f"    {c['name']}  (id: {c['character_id']})")
        if nu:
            summary_lines.append(f"\n[~] Updated characters: {len(nu)}")
            for c in nu:
                summary_lines.append(f"    {c['name']}  (id: {c['character_id']})")
        if nl:
            summary_lines.append(f"\n[+] Locations: {len(nl)}")
            for l in nl:
                summary_lines.append(f"    {l.get('class_id', '?')}  (id: {l.get('location_id', '?')})")
        if nv:
            summary_lines.append(f"\n[+] Visual Elements: {len(nv)}")
            for v in nv:
                summary_lines.append(f"    {v['name']} ({v.get('type', '?')})  [id: {v.get('element_id', '?')}]")
        if not any([nc, nu, nv, nl]):
            summary_lines.append("No entity changes for this scene.")
        self.summary.insert("end", "\n".join(summary_lines))

        # Locations tab
        for l in nl:
            self.loc_t.insert("end",
                f"[NEW] class: {l.get('class_id', '?')}\n"
                f"      location_id: {l.get('location_id', '?')}\n\n")
        if not nl:
            self.loc_t.insert("end", "No location changes.")

        # Characters tab
        for c in nc:
            self.char_t.insert("end", f"[NEW] {c['name']}  (id: {c['character_id']})\n")
        for c in nu:
            self.char_t.insert("end", f"[UPD] {c['name']}  (id: {c['character_id']})\n")
        if not nc and not nu:
            self.char_t.insert("end", "No character changes.")

        # Visual Elements tab
        for v in nv:
            self.ve_t.insert("end",
                f"[NEW] {v['name']}\n"
                f"      type: {v.get('type', '?')}\n"
                f"      element_id: {v.get('element_id', '?')}\n\n")
        if not nv:
            self.ve_t.insert("end", "No visual element changes.")