"""Rules Manager — visual editor for rules.yaml. User-friendly."""
import tkinter as tk
from tkinter import ttk, messagebox
import yaml
from pathlib import Path
import copy

RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "rules.yaml"
_UNDO = []  # stack of (description, data_snapshot)

def load_rules():
    with open(RULES_PATH) as f:
        return yaml.safe_load(f)

def save_rules(data):
    with open(RULES_PATH, "w") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def _snapshot(data):
    return copy.deepcopy(data)

def _push_undo(desc, data):
    _UNDO.append((desc, _snapshot(data)))

def _pop_undo():
    if _UNDO:
        return _UNDO.pop()
    return None

class RulesManager:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Rules Manager")
        self.win.geometry("860+300")
        self.data = load_rules()

        # Top bar
        top = ttk.Frame(self.win, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="📋 Rules Manager", font=("Helvetica", 14, "bold")).pack(side="left")
        ttk.Button(top, text="↩ Undo", command=self.undo, width=8).pack(side="right", padx=(4, 0))
        ttk.Button(top, text="💾 Save All", command=self.save).pack(side="right")

        self.undo_label = ttk.Label(top, text="", foreground="gray")
        self.undo_label.pack(side="right", padx=(8, 8))

        nb = ttk.Notebook(self.win, padding=4)
        nb.pack(fill="both", expand=True, padx=10, pady=(0, 10))


        # Tab 1: Simple list editor (reused for background pop & bit part chars)
        self._build_simple_tab(nb, "Background Pop.",
                               "background_population",
                               "Labels like COMMUTERS, CROWD, EXTRAS")
        self._build_simple_tab(nb, "Bit Part Chars",
                               "bit_part_characters",
                               "Names like BARTENDER, WAITER, NURSE")

        # Tab 2: Visual Elements (form-based)
        self._build_ve_tab(nb, "Visual Elements", "visual_element_patterns")

        # Tab 3: Location Classes + Matchers (combined section)
        self._build_lc_tab(nb, "Locations", "location_classes")
        self._build_lc_tab(nb, "Matchers", "location_matchers")

    # ── Undo ────────────────────────────────────────────────────────────
    def undo(self):
        item = _pop_undo()
        if item:
            desc, snap = item
            self.data = snap
            self.undo_label.config(text=f"↩ {desc}")
            self.win.after(3000, lambda: self.undo_label.config(text=""))
            messagebox.showinfo("Undo", f"Reverted: {desc}", parent=self.win)
        else:
            messagebox.showinfo("Undo", "Nothing to undo.", parent=self.win)

    # ── Simple List Tab (editable text area) ────────────────────────────
    def _build_simple_tab(self, nb, label, key, hint):
        f = ttk.Frame(nb, padding=8)
        nb.add(f, text=label)
        ttk.Label(f, text=hint, foreground="gray").pack(anchor="w")
        text_w = tk.Text(f, height=12, font=("Menlo", 10), wrap="none")
        text_w.pack(fill="both", expand=True, pady=(6, 6))
        # Load data
        items = self.data.get(key, [])
        text_w.insert("1.0", "\n".join(items))
        btnf = ttk.Frame(f)
        btnf.pack(fill="x")
        ttk.Button(btnf, text="+ Add Line", command=lambda: text_w.insert("end", "\n")).pack(side="left", padx=(0, 4))
        ttk.Button(btnf, text="− Delete Selected", command=lambda: self._del_lines(text_w)).pack(side="left")
        ttk.Label(btnf, text="Edit freely, Save writes back.", foreground="gray").pack(side="right")
        # Store reference
        setattr(self, f"_text_{key}", text_w)

    def _del_lines(self, text_w):
        try:
            sel = text_w.tag_ranges("sel")
            if sel:
                text_w.delete(sel[0], sel[1])
            else:
                # Delete current line
                idx = text_w.index("insert")
                line_start = f"{idx.split('.')[0]}.0"
                line_end = f"{idx.split('.')[0]}.end+1c"
                text_w.delete(line_start, line_end)
        except: pass

    # ── Form-Based Tab (Visual Elements) ────────────────────────────────
    def _build_ve_tab(self, nb, label, key):
        f = ttk.Frame(nb, padding=8)
        nb.add(f, text=label)

        paned = ttk.PanedWindow(f, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Left: tree list
        left = ttk.Frame(paned)
        paned.add(left, weight=1)
        self._ve_tree = ttk.Treeview(left, columns=("id", "type"), show="headings", height=12, selectmode="browse")
        self._ve_tree.heading("id", text="ID")
        self._ve_tree.heading("type", text="Type")
        self._ve_tree.column("id", width=140)
        self._ve_tree.column("type", width=120)
        self._ve_tree.pack(fill="both", expand=True)
        btnf = ttk.Frame(left)
        btnf.pack(fill="x", pady=(4, 0))
        ttk.Button(btnf, text="+ Add", command=lambda: self._ve_add()).pack(side="left", padx=(0, 4))
        ttk.Button(btnf, text="✕ Delete", command=lambda: self._ve_del()).pack(side="left")

        # Right: edit form
        right = ttk.Frame(paned, padding=(10, 0, 0, 0))
        paned.add(right, weight=2)
        self._ve_form = ttk.LabelFrame(right, text="Edit Pattern", padding=10)
        self._ve_form.pack(fill="both", expand=True)
        self._ve_vars = {}
        fields = [("id", 20), ("type", 20), ("description", 30)]
        for k, w in fields:
            r = ttk.Frame(self._ve_form)
            r.pack(fill="x", pady=2)
            ttk.Label(r, text=k, width=16, anchor="w").pack(side="left")
            var = tk.StringVar()
            ttk.Entry(r, textvariable=var, width=w).pack(side="left", fill="x", expand=True)
            self._ve_vars[k] = var
        # Multi-line for trigger words
        ttk.Label(self._ve_form, text="trigger words\n(one per line)", anchor="w").pack(anchor="w", pady=(8, 2))
        self._ve_trig = tk.Text(self._ve_form, height=5, font=("Menlo", 9))
        self._ve_trig.pack(fill="x", pady=(0, 4))
        ttk.Label(self._ve_form, text="interaction verbs (one per line)", anchor="w").pack(anchor="w", pady=(2, 2))
        self._ve_verb = tk.Text(self._ve_form, height=4, font=("Menlo", 9))
        self._ve_verb.pack(fill="x")

        btnf2 = ttk.Frame(self._ve_form)
        btnf2.pack(fill="x", pady=(8, 0))
        ttk.Button(btnf2, text="Apply", command=lambda: self._ve_apply()).pack(side="left", padx=(0, 4))
        ttk.Label(btnf2, text="Apply writes to in-memory data. Save to persist.", foreground="gray").pack(side="right")

        self._ve_tree.bind("<<TreeviewSelect>>", lambda e: self._ve_load())
        self._ve_refresh()

    def _ve_refresh(self):
        self._ve_tree.delete(*self._ve_tree.get_children())
        for v in self.data.get("visual_element_patterns", []):
            self._ve_tree.insert("", "end", values=(v.get("id", "?"), v.get("type", "?")))

    def _ve_load(self):
        sel = self._ve_tree.selection()
        if not sel: return
        vals = self._ve_tree.item(sel[0], "values")
        for v in self.data.get("visual_element_patterns", []):
            if v.get("id") == vals[0]:
                for k in self._ve_vars:
                    self._ve_vars[k].set(str(v.get(k, "")))
                trig = v.get("trigger_words", [])
                self._ve_trig.delete("1.0", "end")
                self._ve_trig.insert("1.0", "\n".join(trig) if isinstance(trig, list) else str(trig))
                verbs = v.get("interaction_verbs", [])
                self._ve_verb.delete("1.0", "end")
                self._ve_verb.insert("1.0", "\n".join(verbs) if isinstance(verbs, list) else str(verbs))
                return

    def _ve_add(self):
        _push_undo("Add Visual Element", self.data)
        d = {"id": "VE_NEW", "type": "container", "description": "",
             "trigger_words": [], "interaction_verbs": []}
        self.data.setdefault("visual_element_patterns", []).append(d)
        self._ve_refresh()

    def _ve_del(self):
        sel = self._ve_tree.selection()
        if not sel: return
        vals = self._ve_tree.item(sel[0], "values")
        if not messagebox.askyesno("Delete", f"Delete {vals[0]}?", parent=self.win):
            return
        _push_undo(f"Delete {vals[0]}", self.data)
        self.data["visual_element_patterns"] = [
            v for v in self.data.get("visual_element_patterns", []) if v.get("id") != vals[0]
        ]
        self._ve_refresh()

    def _ve_apply(self):
        sel = self._ve_tree.selection()
        if not sel: return
        vals = self._ve_tree.item(sel[0], "values")
        _push_undo(f"Edit {vals[0]}", self.data)
        for v in self.data.get("visual_element_patterns", []):
            if v.get("id") == vals[0]:
                for k in self._ve_vars:
                    v[k] = self._ve_vars[k].get()
                trig = self._ve_trig.get("1.0", "end").strip().split("\n")
                v["trigger_words"] = [t.strip() for t in trig if t.strip()]
                verbs = self._ve_verb.get("1.0", "end").strip().split("\n")
                v["interaction_verbs"] = [t.strip() for t in verbs if t.strip()]
                self._ve_refresh()
                messagebox.showinfo("Applied", f"{vals[0]} updated in memory.", parent=self.win)
                return

    # ── Form Tab: Location Classes / Matchers ──────────────────────────
    def _build_lc_tab(self, nb, label, key):
        f = ttk.Frame(nb, padding=8)
        nb.add(f, text=label)

        paned = ttk.PanedWindow(f, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned)
        paned.add(left, weight=1)
        cols = ("id",)
        tree = ttk.Treeview(left, columns=cols, show="headings", height=12, selectmode="browse")
        tree.heading("id", text="ID")
        tree.column("id", width=180)
        tree.pack(fill="both", expand=True)
        btnf = ttk.Frame(left)
        btnf.pack(fill="x", pady=(4, 0))
        ttk.Button(btnf, text="+ Add", command=lambda: self._lc_add(tree, key)).pack(side="left", padx=(0, 4))
        ttk.Button(btnf, text="✕ Delete", command=lambda: self._lc_del(tree, key)).pack(side="left")

        right = ttk.Frame(paned, padding=(10, 0, 0, 0))
        paned.add(right, weight=2)
        form = ttk.LabelFrame(right, text="Edit", padding=10)
        form.pack(fill="both", expand=True)
        vars_dict = {}
        rows = ttk.Frame(form)
        rows.pack(fill="both", expand=True)
        # Dynamic fields based on first item
        sample = self.data.get(key, [{}])[0]
        self._lc_fields = {}
        for k in sample:
            if k in ("keywords_any", "interaction_verbs", "trigger_words", "note"):
                continue
            r = ttk.Frame(rows)
            r.pack(fill="x", pady=1)
            ttk.Label(r, text=k, width=22, anchor="w").pack(side="left")
            var = tk.StringVar()
            if isinstance(sample[k], bool):
                cb = ttk.Checkbutton(r, variable=tk.BooleanVar())
                cb.pack(side="left")
                self._lc_fields[k] = ("check", cb)
            else:
                ent = ttk.Entry(r, textvariable=var)
                ent.pack(side="left", fill="x", expand=True)
                self._lc_fields[k] = ("entry", var, ent)
        btnf2 = ttk.Frame(form)
        btnf2.pack(fill="x", pady=(6, 0))
        ttk.Button(btnf2, text="Apply", command=lambda: self._lc_apply(tree, key)).pack(side="left", padx=(0, 4))
        ttk.Label(btnf2, text="Apply → memory. Save → disk.", foreground="gray").pack(side="right")

        # Stash refs
        setattr(self, f"_lc_tree_{key}", tree)
        setattr(self, f"_lc_form_{key}", rows)
        tree.bind("<<TreeviewSelect>>", lambda e: self._lc_load(tree, key))
        self._lc_refresh(tree, key)

    def _lc_refresh(self, tree, key):
        tree.delete(*tree.get_children())
        for item in self.data.get(key, []):
            tree.insert("", "end", values=(item.get(list(item.keys())[0], "?"),))

    def _lc_load(self, tree, key):
        sel = tree.selection()
        if not sel: return
        vals = tree.item(sel[0], "values")
        first_key = list(self.data.get(key, [{}])[0].keys())[0]
        for item in self.data.get(key, []):
            if str(item.get(first_key, "")) == str(vals[0]):
                for k, spec in self._lc_fields.items():
                    v = item.get(k, "")
                    if spec[0] == "entry":
                        _, var, ent = spec
                        ent.delete(0, "end")
                        ent.insert(0, str(v) if v is not None else "")
                    elif spec[0] == "check":
                        _, cb = spec
                        cb.invoke() if v else None  # toggle to match
                return

    def _lc_add(self, tree, key):
        _push_undo(f"Add to {key}", self.data)
        first_key = list(self.data.get(key, [{}])[0].keys())[0] if self.data.get(key) else "id"
        d = {first_key: f"NEW_{key.upper()}"}
        for k in self._lc_fields:
            if k != first_key:
                d[k] = "" if self._lc_fields[k][0] == "entry" else False
        self.data.setdefault(key, []).append(d)
        self._lc_refresh(tree, key)

    def _lc_del(self, tree, key):
        sel = tree.selection()
        if not sel: return
        vals = tree.item(sel[0], "values")
        first_key = list(self.data.get(key, [{}])[0].keys())[0]
        if not messagebox.askyesno("Delete", f"Delete {vals[0]}?", parent=self.win):
            return
        _push_undo(f"Delete {vals[0]} from {key}", self.data)
        self.data[key] = [item for item in self.data.get(key, []) if str(item.get(first_key, "")) != str(vals[0])]
        self._lc_refresh(tree, key)

    def _lc_apply(self, tree, key):
        sel = tree.selection()
        if not sel: return
        vals = tree.item(sel[0], "values")
        first_key = list(self.data.get(key, [{}])[0].keys())[0]
        _push_undo(f"Edit {vals[0]} in {key}", self.data)
        for item in self.data.get(key, []):
            if str(item.get(first_key, "")) == str(vals[0]):
                for k, spec in self._lc_fields.items():
                    if spec[0] == "entry":
                        _, var, ent = spec
                        item[k] = var.get()
                    elif spec[0] == "check":
                        _, cb = spec
                        item[k] = bool(cb.var.get()) if hasattr(cb, 'var') else False
                self._lc_refresh(tree, key)
                messagebox.showinfo("Applied", f"{vals[0]} updated.", parent=self.win)
                return

    # ── Save ────────────────────────────────────────────────────────────
    def save(self):
        # Read simple list tabs
        for key in ("background_population", "bit_part_characters"):
            tw = getattr(self, f"_text_{key}", None)
            if tw:
                raw = tw.get("1.0", "end").strip()
                self.data[key] = [l.strip() for l in raw.split("\n") if l.strip()]
        save_rules(self.data)
        _UNDO.clear()
        messagebox.showinfo("Saved", "rules.yaml written to disk.", parent=self.win)
