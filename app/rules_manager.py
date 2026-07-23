"""Rules Manager — table-based GUI for rules.yaml + ai_rules.yaml."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from script_splitter.rules_db import RuleDB

db = RuleDB()

# ── Helpers ────────────────────────────────────────────────────────────
def _simple_list_tab(parent, section):
    """Build a single-column treeview for list-type sections."""
    frame = ttk.Frame(parent, padding=8)
    tree = ttk.Treeview(frame, columns=("item", "source"), show="headings", height=14)
    tree.heading("item", text="Item")
    tree.heading("source", text="Source")
    tree.column("item", width=300)
    tree.column("source", width=80)
    tree.pack(fill="both", expand=True)

    entry = ttk.Entry(frame)
    entry.pack(fill="x", pady=(6, 0))

    btnf = ttk.Frame(frame)
    btnf.pack(fill="x", pady=(4, 0))
    ttk.Button(btnf, text="+ Add", command=lambda: _add_simple(tree, entry, section)).pack(side="left", padx=(0, 4))
    ttk.Button(btnf, text="✕ Delete", command=lambda: _del_simple(tree, section)).pack(side="left")
    ttk.Button(btnf, text="Update Selected", command=lambda: _update_simple(tree, entry, section)).pack(side="left", padx=(8, 0))
    ttk.Label(btnf, text="Click item → edit → Update", foreground="gray").pack(side="right")

    def on_select(e):
        sel = tree.selection()
        if sel:
            entry.delete(0, "end")
            entry.insert(0, tree.item(sel[0], "values")[0])

    tree.bind("<<TreeviewSelect>>", on_select)
    _refresh_simple(tree, section)
    return frame

def _refresh_simple(tree, section):
    tree.delete(*tree.get_children())
    data = db.load()
    items = data.get(section, [])
    for item in items:
        is_ai = db.is_ai_rule(section, item)
        tag = "ai" if is_ai else "human"
        src = "🤖 AI" if is_ai else "human"
        tree.insert("", "end", values=(item, src), tags=(tag,))
    tree.tag_configure("ai", foreground="gray", font=("", 9, "italic"))
    tree.tag_configure("human", foreground="black")

def _add_simple(tree, entry, section):
    val = entry.get().strip().upper()
    if not val:
        messagebox.showwarning("Add", "Enter a value first.")
        return
    data = db.load()
    data.setdefault(section, [])
    if val in data[section]:
        messagebox.showinfo("Exists", f"{val} already in list.")
        return
    data[section].append(val)
    db.save_human(data)
    entry.delete(0, "end")
    _refresh_simple(tree, section)

def _del_simple(tree, section):
    sel = tree.selection()
    if not sel: return
    vals = tree.item(sel[0], "values")
    if db.is_ai_rule(section, vals[0]):
        messagebox.showerror("Read Only", "AI rules cannot be deleted from this editor.")
        return
    if not messagebox.askyesno("Delete", f"Remove '{vals[0]}'?"):
        return
    data = db.load()
    data[section] = [i for i in data[section] if i != vals[0]]
    db.save_human(data)
    _refresh_simple(tree, section)

def _update_simple(tree, entry, section):
    sel = tree.selection()
    if not sel: return
    old_val = tree.item(sel[0], "values")[0]
    if db.is_ai_rule(section, old_val):
        messagebox.showerror("Read Only", "AI rules cannot be edited.")
        return
    new_val = entry.get().strip().upper()
    if not new_val:
        return
    data = db.load()
    idx = data[section].index(old_val)
    data[section][idx] = new_val
    db.save_human(data)
    entry.delete(0, "end")
    _refresh_simple(tree, section)

# ── Structured Tab (Visual Elements / Matchers) ───────────────────────
def _struct_tab(parent, section):
    """Build a tree+form editor for structured rule sections."""
    from script_splitter.rules_db import _id_key, _load_yaml, HUMAN_PATH

    frame = ttk.Frame(parent, padding=8)
    paned = ttk.PanedWindow(frame, orient="horizontal")
    paned.pack(fill="both", expand=True)

    # Left: tree
    left = ttk.Frame(paned)
    paned.add(left, weight=1)
    id_k = _id_key(section) or "id"
    tree = ttk.Treeview(left, columns=(id_k, "source"), show="headings", height=14)
    tree.heading(id_k, text=id_k)
    tree.heading("source", text="Source")
    tree.column(id_k, width=160)
    tree.column("source", width=70)
    tree.pack(fill="both", expand=True)
    bf = ttk.Frame(left)
    bf.pack(fill="x", pady=(4, 0))
    ttk.Button(bf, text="+ Add", command=lambda: _add_struct(tree, section)).pack(side="left", padx=(0, 4))
    ttk.Button(bf, text="✕ Delete", command=lambda: _del_struct(tree, section)).pack(side="left")

    # Right: form
    right = ttk.Frame(paned, padding=(10, 0, 0, 0))
    paned.add(right, weight=2)
    form = ttk.LabelFrame(right, text="Edit", padding=8)
    form.pack(fill="both", expand=True)
    fields_frame = ttk.Frame(form)
    fields_frame.pack(fill="both", expand=True)

    # We'll store form widgets in a dict
    form_widgets = {}

    def build_fields(data_item=None):
        """Rebuild/edit the form based on selected item's keys."""
        for w in fields_frame.winfo_children():
            w.destroy()
        form_widgets.clear()

        if not data_item:
            ttk.Label(fields_frame, text="Select an item to edit", foreground="gray").pack()
            return

        # Text fields
        for k, v in data_item.items():
            if isinstance(v, list):
                # Lists: show as mini treeview
                lf = ttk.LabelFrame(fields_frame, text=k, padding=4)
                lf.pack(fill="x", pady=2)
                lt = tk.Listbox(lf, height=min(len(v), 5), font=("Menlo", 9))
                lt.pack(fill="x")
                for item in v:
                    lt.insert("end", str(item))
                ef = ttk.Frame(lf)
                ef.pack(fill="x", pady=(2, 0))
                e_entry = ttk.Entry(ef)
                e_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
                ttk.Button(ef, text="+", width=3, command=lambda lb=lt, ee=e_entry: _list_add(lb, ee, k)).pack(side="left", padx=(0, 2))
                ttk.Button(ef, text="−", width=3, command=lambda lb=lt: _list_del(lb, k)).pack(side="left")
                form_widgets[k] = lt
            elif isinstance(v, bool):
                r = ttk.Frame(fields_frame)
                r.pack(fill="x", pady=1)
                ttk.Label(r, text=k, width=18, anchor="w").pack(side="left")
                var = tk.BooleanVar(value=v)
                cb = ttk.Checkbutton(r, variable=var)
                cb.pack(side="left")
                form_widgets[k] = var
            else:
                r = ttk.Frame(fields_frame)
                r.pack(fill="x", pady=1)
                ttk.Label(r, text=k, width=18, anchor="w").pack(side="left")
                var = tk.StringVar(value=str(v) if v is not None else "")
                ent = ttk.Entry(r, textvariable=var)
                ent.pack(side="left", fill="x", expand=True)
                form_widgets[k] = var

    def on_select(e):
        sel = tree.selection()
        if not sel:
            build_fields(None)
            return
        vals = tree.item(sel[0], "values")
        data = db.load()
        for item in data.get(section, []):
            if isinstance(item, dict) and str(item.get(id_k, "")) == str(vals[0]):
                build_fields(item)
                return
        build_fields(None)

    ttk.Button(form, text="Apply", command=lambda: _apply_struct(tree, section, form_widgets, id_k)).pack(anchor="w", pady=(4, 0))

    tree.bind("<<TreeviewSelect>>", on_select)
    _refresh_struct(tree, section)

    # Apply button below tree
    return frame

def _refresh_struct(tree, section):
    from script_splitter.rules_db import _id_key
    tree.delete(*tree.get_children())
    data = db.load()
    id_k = _id_key(section) or "id"
    for item in data.get(section, []):
        if isinstance(item, dict):
            val = item.get(id_k, "?")
            is_ai = db.is_ai_rule(section, val)
            src = "🤖 AI" if is_ai else "human"
            tag = "ai" if is_ai else "human"
            tree.insert("", "end", values=(val, src), tags=(tag,))
    tree.tag_configure("ai", foreground="gray", font=("", 9, "italic"))
    tree.tag_configure("human", foreground="black")

def _add_struct(tree, section):
    from script_splitter.rules_db import _id_key
    id_k = _id_key(section) or "id"
    val = simpledialog.askstring("Add", f"{id_k}:")
    if not val:
        return
    data = db.load()
    data.setdefault(section, [])
    data[section].append({id_k: val})
    db.save_human(data)
    _refresh_struct(tree, section)

def _del_struct(tree, section):
    sel = tree.selection()
    if not sel: return
    from script_splitter.rules_db import _id_key
    id_k = _id_key(section) or "id"
    vals = tree.item(sel[0], "values")
    if db.is_ai_rule(section, vals[0]):
        messagebox.showerror("Read Only", "AI rules cannot be deleted.")
        return
    if not messagebox.askyesno("Delete", f"Delete '{vals[0]}'?"):
        return
    data = db.load()
    data[section] = [i for i in data.get(section, []) if not (isinstance(i, dict) and i.get(id_k) == vals[0])]
    db.save_human(data)
    _refresh_struct(tree, section)

def _apply_struct(tree, section, widgets, id_k):
    """Write form values back to the selected rule."""
    sel = tree.selection()
    if not sel: return
    vals = tree.item(sel[0], "values")
    if db.is_ai_rule(section, vals[0]):
        messagebox.showerror("Read Only", "AI rules cannot be modified.")
        return
    data = db.load()
    for item in data.get(section, []):
        if isinstance(item, dict) and str(item.get(id_k, "")) == str(vals[0]):
            for k, w in widgets.items():
                if isinstance(w, tk.BooleanVar):
                    item[k] = w.get()
                elif isinstance(w, tk.Listbox):
                    item[k] = list(w.get(0, "end"))
                elif isinstance(w, tk.StringVar):
                    item[k] = w.get()
            db.save_human(data)
            messagebox.showinfo("Applied", f"{vals[0]} updated.")
            _refresh_struct(tree, section)
            return

def _list_add(lb, entry, key):
    val = entry.get().strip()
    if val:
        lb.insert("end", val)
        entry.delete(0, "end")

def _list_del(lb, key):
    sel = lb.curselection()
    if sel:
        lb.delete(sel[0])

# ── Main Window ────────────────────────────────────────────────────────
class RulesManager:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Rules Manager")
        self.win.geometry("820x560")

        top = ttk.Frame(self.win, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="📋 Rules Manager", font=("Helvetica", 14, "bold")).pack(side="left")
        ttk.Label(top, text="  Human rules: editable  |  🤖 AI rules: read-only",
                  foreground="gray").pack(side="left", padx=(12, 0))

        nb = ttk.Notebook(self.win, padding=4)
        nb.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        _simple_list_tab(nb, "background_population")
        nb.tab(len(nb.tabs()) - 1, text="Background Pop.")

        _simple_list_tab(nb, "bit_part_characters")
        nb.tab(len(nb.tabs()) - 1, text="Bit Part Chars")

        _struct_tab(nb, "visual_element_patterns")
        nb.tab(len(nb.tabs()) - 1, text="Visual Elements")

        _struct_tab(nb, "location_classes")
        nb.tab(len(nb.tabs()) - 1, text="Location Classes")

        _struct_tab(nb, "location_matchers")
        nb.tab(len(nb.tabs()) - 1, text="Matchers")

        # Footer
        foot = ttk.Frame(self.win, padding=(10, 0, 10, 6))
        foot.pack(fill="x")
        ttk.Label(foot, text="💾 All changes are saved immediately.",
                  foreground="gray").pack(side="right")
