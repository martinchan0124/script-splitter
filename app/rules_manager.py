"""Rules Manager — simple YAML text editor. Rock solid."""
import tkinter as tk
from tkinter import ttk, messagebox
import yaml, os
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "rules.yaml"

def load_raw():
    return RULES_PATH.read_text(encoding="utf-8")

def save_raw(text):
    # Validate YAML before writing
    try:
        yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}")
    RULES_PATH.write_text(text, encoding="utf-8")

class RulesManager:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Rules Manager — rules.yaml")
        self.win.geometry("760x620")
        self.win.minsize(600, 400)

        top = ttk.Frame(self.win, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="📋 rules.yaml", font=("Helvetica", 14, "bold")).pack(side="left")
        ttk.Button(top, text="↩ Reload from Disk", command=self.reload).pack(side="right", padx=(4, 0))
        ttk.Button(top, text="💾 Save", command=self.save).pack(side="right")

        # Text editor
        text_frame = ttk.Frame(self.win, padding=(10, 0, 10, 10))
        text_frame.pack(fill="both", expand=True)
        self.text = tk.Text(text_frame, font=("Menlo", 10), wrap="none",
                            bg="#fafafa", fg="#222", bd=1, relief="solid",
                            undo=True)  # built-in undo!
        self.text.pack(fill="both", expand=True)

        # Scrollbars
        sy = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        sy.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=sy.set)
        sx = ttk.Scrollbar(self.win, orient="horizontal", command=self.text.xview)
        sx.pack(fill="x", padx=10)
        self.text.configure(xscrollcommand=sx.set)

        # Footer
        foot = ttk.Frame(self.win, padding=(10, 0, 10, 6))
        foot.pack(fill="x")
        self.status = ttk.Label(foot, text="", foreground="gray")
        self.status.pack(side="left")
        ttk.Label(foot, text="⌘Z undo | Edit freely, then Save", foreground="gray").pack(side="right")

        # Load
        self.load_content()

    def load_content(self):
        try:
            content = load_raw()
            self.text.delete("1.0", "end")
            self.text.insert("1.0", content)
            self.status.config(text=f"Loaded ({len(content)} chars)")
        except Exception as e:
            self.status.config(text=f"Load error: {e}")

    def reload(self):
        if messagebox.askyesno("Reload", "Discard unsaved changes and reload from disk?", parent=self.win):
            self.load_content()

    def save(self):
        content = self.text.get("1.0", "end-1c")
        try:
            save_raw(content)
            self.status.config(text="✅ Saved")
        except ValueError as e:
            messagebox.showerror("YAML Error", str(e), parent=self.win)
            self.status.config(text="❌ Invalid YAML")
        except Exception as e:
            messagebox.showerror("Error", f"Write failed: {e}", parent=self.win)
            self.status.config(text="❌ Write error")
