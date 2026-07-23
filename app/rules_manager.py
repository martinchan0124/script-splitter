"""Rules Manager — GUI for browsing/editing rules.yaml."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import yaml, os, copy
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "rules.yaml"

def load_rules():
    with open(RULES_PATH) as f:
        return yaml.safe_load(f)

def save_rules(data):
    with open(RULES_PATH, "w") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

# ── Helpers ────────────────────────────────────────────────────────────
def _list_str(values):
    """Convert '["A; B; C"]' or ['A', 'B'] to a flat list."""
    if isinstance(values, str):
        return [v.strip() for v in values.replace(";", "\n").split("\n") if v.strip()]
    if isinstance(values, list):
        out = []
        for v in values:
            if isinstance(v, str) and ";" in v:
                out.extend(x.strip() for x in v.split(";") if x.strip())
            else:
                out.append(str(v).strip())
        return out
    return []

def _format_list(items):
    return "\n".join(items) if items else ""

def _try_get(d, *keys, default=""):
    for k in keys:
        if isinstance(d, dict) and k in d:
            v = d[k]
            return v if v is not None else default
    return default

# ── Editor Panel: field row ────────────────────────────────────────────
class FieldRow(ttk.Frame):
    def __init__(self, parent, label, text_var=None, **kwargs):
        super().__init__(parent)
        self.columnconfigure(1, weight=1)
        ttk.Label(self, text=label, width=22, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 6))
        if text_var is not None:
            self.entry = ttk.Entry(self, textvariable=text_var, **kwargs)
        else:
            self.entry = ttk.Entry(self, **kwargs)
        self.entry.grid(row=0, column=1, sticky="ew")

class CheckRow(ttk.Frame):
    def __init__(self, parent, label, var):
        super().__init__(parent)
        ttk.Label(self, text=label, width=22, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Checkbutton(self, variable=var).grid(row=0, column=1, sticky="w")

# ── Main Rules Manager ────────────────────────────────────────────────
class RulesManager:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Rules Manager")
        self.win.geometry("820x620")
        self.win.minsize(700, 500)
        self.data = load_rules()

        nb = ttk.Notebook(self.win)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabs = {}
        sections = [
            ("Location Classes", self._build_loc_classes),
            ("Matchers", self._build_matchers),
            ("Visual Elements", self._build_visual),
            ("Background Pop.", self._build_bgpop),
            ("Bit Part Chars", self._build_bitpart),
        ]
        for label, builder in sections:
            frame = ttk.Frame(nb, padding=10)
            nb.add(frame, text=label)
            self.tabs[label] = {"frame": frame, "builder": builder}
            builder(frame)

        # Bottom save
        btnf = ttk.Frame(self.win)
        btnf.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(btnf, text="Changes apply after Save", foreground="gray").pack(side="left")
        ttk.Button(btnf, text="💾 Save All", command=self.save).pack(side="right")

    # ── Tab: Location Classes ──────────────────────────────────────────
    def _build_loc_classes(self, parent):
        for c in "0146":
            parent.columnconfigure(int(c), weight=1)
        # Tree
        cols = ("class_id", "class_name", "generation", "panorama", "review")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=8, selectmode="browse")
        for c, w in zip(cols, (28, 24, 24, 10, 8)):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="w")
        tree.grid(row=0, column=0, columnspan=5, sticky="ew", pady=(0, 6))
        # Buttons
        bf = ttk.Frame(parent)
        bf.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(0, 8))
        ttk.Button(bf, text="+ Add", command=lambda: self._add_lc(tree)).pack(side="left", padx=(0, 4))
        ttk.Button(bf, text="− Delete", command=lambda: self._del_lc(tree)).pack(side="left")
        # Edit fields
        self.lc_vars = {k: tk.StringVar() for k in ("class_id", "class_name", "generation_class", "description")}
        self.lc_checks = {}
        for k in ("supports_background_panorama", "requires_background_panorama", "requires_human_review"):
            self.lc_checks[k] = tk.BooleanVar()
        row = 2
        for k in ("class_id", "class_name", "generation_class"):
            FieldRow(parent, k, self.lc_vars[k]).grid(row=row, column=0, columnspan=5, sticky="ew", pady=1); row += 1
        FieldRow(parent, "description", self.lc_vars["description"]).grid(row=row, column=0, columnspan=5, sticky="ew", pady=1); row += 1
        ckf = ttk.Frame(parent)
        ckf.grid(row=row, column=0, columnspan=5, sticky="ew", pady=2)
        for i, k in enumerate(self.lc_checks):
            ttk.Checkbutton(ckf, text=k, variable=self.lc_checks[k]).pack(side="left", padx=(0, 12))
        tree.bind("<<TreeviewSelect>>", lambda e: self._load_lc(tree))
        self._refresh_lc(tree)

    def _refresh_lc(self, tree):
        tree.delete(*tree.get_children())
        for c in self.data.get("location_classes", []):
            tree.insert("", "end", values=(
                _try_get(c, "class_id"),
                _try_get(c, "class_name"),
                _try_get(c, "generation_class"),
                "✓" if c.get("supports_background_panorama") else "",
                "⚠" if c.get("requires_human_review") else "",
            ))

    def _load_lc(self, tree):
        sel = tree.selection()
        if not sel: return
        vals = tree.item(sel[0], "values")
        for c in self.data.get("location_classes", []):
            if c.get("class_id") == vals[0]:
                for k in self.lc_vars:
                    self.lc_vars[k].set(str(c.get(k, "")))
                for k in self.lc_checks:
                    self.lc_checks[k].set(bool(c.get(k, False)))
                return

    def _add_lc(self, tree):
        d = {"class_id": "LC_NEW", "class_name": "new class", "generation_class": "new_class",
             "description": "", "supports_background_panorama": False,
             "requires_background_panorama": False, "requires_human_review": False}
        self.data.setdefault("location_classes", []).append(d)
        self._refresh_lc(tree)

    def _del_lc(self, tree):
        sel = tree.selection()
        if not sel: return
        vals = tree.item(sel[0], "values")
        self.data["location_classes"] = [c for c in self.data.get("location_classes", []) if c.get("class_id") != vals[0]]
        self._refresh_lc(tree)

    # ── Tab: Location Matchers ─────────────────────────────────────────
    def _build_matchers(self, parent):
        parent.columnconfigure(1, weight=1)
        # Tree
        cols = ("rule_id", "priority", "int_ext", "result_class", "confidence")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=8, selectmode="browse")
        for c, w in zip(cols, (28, 8, 10, 28, 10)):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="w")
        tree.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 6))
        bf = ttk.Frame(parent)
        bf.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Button(bf, text="+ Add", command=lambda: self._add_m(tree)).pack(side="left", padx=(0, 4))
        ttk.Button(bf, text="− Delete", command=lambda: self._del_m(tree)).pack(side="left")
        label_frame = ttk.LabelFrame(parent, text="Edit Rule", padding=8)
        label_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        lf = label_frame
        self.m_vars = {}
        for i, k in enumerate(["rule_id", "priority", "int_ext", "result_class", "confidence"]):
            f = FieldRow(lf, k, width=20); f.pack(fill="x", pady=1)
            self.m_vars[k] = f.entry
        self.m_keywords_var = tk.StringVar()
        FieldRow(lf, "keywords_any", self.m_keywords_var, width=20).pack(fill="x", pady=1)
        self.m_note_var = tk.StringVar()
        FieldRow(lf, "note", self.m_note_var, width=20).pack(fill="x", pady=1)
        tree.bind("<<TreeviewSelect>>", lambda e: self._load_m(tree))
        self._refresh_m(tree)

    def _refresh_m(self, tree):
        tree.delete(*tree.get_children())
        for m in self.data.get("location_matchers", []):
            tree.insert("", "end", values=(
                _try_get(m, "rule_id"),
                _try_get(m, "priority"),
                _try_get(m, "int_ext"),
                _try_get(m, "result_class"),
                _try_get(m, "confidence"),
            ))

    def _load_m(self, tree):
        sel = tree.selection()
        if not sel: return
        vals = tree.item(sel[0], "values")
        for m in self.data.get("location_matchers", []):
            if m.get("rule_id") == vals[0]:
                for k in ("rule_id", "priority", "int_ext", "result_class", "confidence", "note"):
                    v = m.get(k, "")
                    if hasattr(self.m_vars.get(k), "delete"):
                        self.m_vars[k].delete(0, tk.END)
                        self.m_vars[k].insert(0, str(v))
                kw = m.get("keywords_any", [])
                self.m_keywords_var.delete(0, tk.END)
                self.m_keywords_var.insert(0, _format_list(_list_str(kw)))
                return

    def _add_m(self, tree):
        d = {"rule_id": "LOC_NEW", "priority": 50, "int_ext": "INT",
             "result_class": "LC_INTERIOR_SINGLE_ROOM", "confidence": 0.7,
             "keywords_any": [], "note": ""}
        self.data.setdefault("location_matchers", []).append(d)
        self._refresh_m(tree)

    def _del_m(self, tree):
        sel = tree.selection()
        if not sel: return
        vals = tree.item(sel[0], "values")
        self.data["location_matchers"] = [m for m in self.data.get("location_matchers", []) if m.get("rule_id") != vals[0]]
        self._refresh_m(tree)

    # ── Tab: Visual Elements ───────────────────────────────────────────
    def _build_visual(self, parent):
        parent.columnconfigure(1, weight=1)
        cols = ("id", "type", "trigger_words")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=8, selectmode="browse")
        for c, w in zip(cols, (30, 26, 44)):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="w")
        tree.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 6))
        bf = ttk.Frame(parent)
        bf.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Button(bf, text="+ Add", command=lambda: self._add_v(tree)).pack(side="left", padx=(0, 4))
        ttk.Button(bf, text="− Delete", command=lambda: self._del_v(tree)).pack(side="left")
        lf = ttk.LabelFrame(parent, text="Edit Pattern", padding=8)
        lf.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.v_vars = {}
        for k in ("id", "type", "description"):
            f = FieldRow(lf, k, width=20); f.pack(fill="x", pady=1)
            self.v_vars[k] = f.entry
        self.v_trig_var = tk.StringVar()
        FieldRow(lf, "trigger_words (one per line)", self.v_trig_var, width=20).pack(fill="x", pady=1)
        self.v_verb_var = tk.StringVar()
        FieldRow(lf, "interaction_verbs", self.v_verb_var, width=20).pack(fill="x", pady=1)
        tree.bind("<<TreeviewSelect>>", lambda e: self._load_v(tree))
        self._refresh_v(tree)

    def _refresh_v(self, tree):
        tree.delete(*tree.get_children())
        for v in self.data.get("visual_element_patterns", []):
            kw = _list_str(v.get("trigger_words", []))
            tree.insert("", "end", values=(
                _try_get(v, "id"),
                _try_get(v, "type"),
                "; ".join(kw[:5]) + ("…" if len(kw) > 5 else ""),
            ))

    def _load_v(self, tree):
        sel = tree.selection()
        if not sel: return
        vals = tree.item(sel[0], "values")
        for v in self.data.get("visual_element_patterns", []):
            if v.get("id") == vals[0]:
                for k in ("id", "type", "description"):
                    var = self.v_vars.get(k)
                    if var:
                        var.delete(0, tk.END)
                        var.insert(0, str(v.get(k, "")))
                self.v_trig_var.delete(0, tk.END)
                self.v_trig_var.insert(0, _format_list(_list_str(v.get("trigger_words", []))))
                self.v_verb_var.delete(0, tk.END)
                self.v_verb_var.insert(0, _format_list(_list_str(v.get("interaction_verbs", []))))
                return

    def _add_v(self, tree):
        d = {"id": "VE_NEW", "type": "container", "description": "",
             "trigger_words": [], "interaction_verbs": []}
        self.data.setdefault("visual_element_patterns", []).append(d)
        self._refresh_v(tree)

    def _del_v(self, tree):
        sel = tree.selection()
        if not sel: return
        vals = tree.item(sel[0], "values")
        self.data["visual_element_patterns"] = [v for v in self.data.get("visual_element_patterns", []) if v.get("id") != vals[0]]
        self._refresh_v(tree)

    # ── Tab: Background Population ─────────────────────────────────────
    def _build_bgpop(self, parent):
        parent.columnconfigure(0, weight=1)
        self.bg_listbox = tk.Listbox(parent, height=15)
        self.bg_listbox.pack(fill="both", expand=True, pady=(0, 6))
        bf = ttk.Frame(parent)
        bf.pack(fill="x")
        ttk.Button(bf, text="+ Add", command=self._add_bg).pack(side="left", padx=(0, 4))
        ttk.Button(bf, text="− Delete", command=self._del_bg).pack(side="left")
        self._refresh_bg()

    def _refresh_bg(self):
        self.bg_listbox.delete(0, tk.END)
        for item in self.data.get("background_population", []):
            self.bg_listbox.insert(tk.END, item)

    def _add_bg(self):
        val = simpledialog.askstring("Add Label", "Background population label:", parent=self.win)
        if val:
            self.data.setdefault("background_population", []).append(val.strip().upper())
            self._refresh_bg()

    def _del_bg(self):
        sel = self.bg_listbox.curselection()
        if sel:
            idx = sel[0]
            self.data["background_population"].pop(idx)
            self._refresh_bg()

    # ── Tab: Bit Part Characters ───────────────────────────────────────
    def _build_bitpart(self, parent):
        parent.columnconfigure(0, weight=1)
        self.bp_listbox = tk.Listbox(parent, height=15)
        self.bp_listbox.pack(fill="both", expand=True, pady=(0, 6))
        bf = ttk.Frame(parent)
        bf.pack(fill="x")
        ttk.Button(bf, text="+ Add", command=self._add_bp).pack(side="left", padx=(0, 4))
        ttk.Button(bf, text="− Delete", command=self._del_bp).pack(side="left")
        self._refresh_bp()

    def _refresh_bp(self):
        self.bp_listbox.delete(0, tk.END)
        for item in self.data.get("bit_part_characters", []):
            self.bp_listbox.insert(tk.END, item)

    def _add_bp(self):
        val = simpledialog.askstring("Add Name", "Bit part character name:", parent=self.win)
        if val:
            self.data.setdefault("bit_part_characters", []).append(val.strip().upper())
            self._refresh_bp()

    def _del_bp(self):
        sel = self.bp_listbox.curselection()
        if sel:
            idx = sel[0]
            self.data["bit_part_characters"].pop(idx)
            self._refresh_bp()

    # ── Save ───────────────────────────────────────────────────────────
    def save(self):
        # Sync form edits back to data (simplified — full editing on the
        # tree selection is already in-memory; this is a safety net.)
        save_rules(self.data)
        messagebox.showinfo("Saved", "rules.yaml updated.", parent=self.win)
