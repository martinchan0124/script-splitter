"""Script Splitter GUI — for directors. Clean, native, no server."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, sys, os, json, threading, re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / ".gui_config.json"

def default_config():
    return {"stage": 2, "use_llm": False, "use_nlp": False,
            "output_dir": str(ROOT / "test"), "auto_open": True}

def load_config():
    try:
        if CONFIG_FILE.exists():
            cfg = json.loads(CONFIG_FILE.read_text())
            d = default_config()
            d.update(cfg)
            return d
    except: pass
    return default_config()

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def script_name(path):
    name = os.path.splitext(os.path.basename(path))[0]
    # clean
    name = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "_", name).strip("_").lower()
    if not name:
        name = "untitled"
    ts = datetime.now().strftime("%m%d_%H%M")
    return f"{name}_{ts}"

def run_pipeline(script_path, stage, use_llm, output_dir):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    cmd = [sys.executable, "-m", "app.main", "parse", script_path,
           "--stage", str(stage), "--output", output_dir]
    if not use_llm:
        cmd.append("--no-llm")
    cmd.append("--no-nlp")
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=ROOT)
    return proc.returncode == 0, proc.stdout + proc.stderr

# ─── Settings Dialog ────────────────────────────────────────────────────
class SettingsDialog:
    def __init__(self, parent, config, on_save):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("480x380")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.on_save = on_save
        self.config = dict(config)

        f = ttk.Frame(self.dialog, padding=24)
        f.pack(fill="both", expand=True)

        # Pipeline
        ttk.Label(f, text="Pipeline Stage", font=("Helvetica", 12, "bold")).pack(anchor="w")
        self.stage_var = tk.IntVar(value=config["stage"])
        for i, label in enumerate(["1 — Scene split only", "2 — + Entity extraction", "3 — + LLM routing"], 1):
            ttk.Radiobutton(f, text=label, variable=self.stage_var, value=i).pack(anchor="w", padx=10, pady=2)

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=15)

        # Options
        ttk.Label(f, text="Options", font=("Helvetica", 12, "bold")).pack(anchor="w")
        self.llm_var = tk.BooleanVar(value=config["use_llm"])
        ttk.Checkbutton(f, text="Enable LLM (requires .env with DEEPSEEK_API_KEY)",
                       variable=self.llm_var).pack(anchor="w", padx=10, pady=2)
        self.nlp_var = tk.BooleanVar(value=config["use_nlp"])
        ttk.Checkbutton(f, text="Enable spaCy NER pre-scan",
                       variable=self.nlp_var).pack(anchor="w", padx=10, pady=2)

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=15)

        # Output
        ttk.Label(f, text="Output Directory", font=("Helvetica", 12, "bold")).pack(anchor="w")
        orow = ttk.Frame(f)
        orow.pack(fill="x", padx=10, pady=5)
        self.out_var = tk.StringVar(value=config["output_dir"])
        ttk.Entry(orow, textvariable=self.out_var).pack(side="left", fill="x", expand=True)
        ttk.Button(orow, text="Browse…", command=self.browse_out).pack(side="right", padx=(8, 0))

        self.auto_var = tk.BooleanVar(value=config["auto_open"])
        ttk.Checkbutton(f, text="Open output folder after run",
                       variable=self.auto_var).pack(anchor="w", padx=10, pady=2)

        # Buttons
        bf = ttk.Frame(f)
        bf.pack(fill="x", pady=(20, 0))
        ttk.Button(bf, text="Cancel", command=self.dialog.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(bf, text="Save", command=self.save).pack(side="right")

    def browse_out(self):
        d = filedialog.askdirectory()
        if d:
            self.out_var.set(d)

    def save(self):
        self.config["stage"] = self.stage_var.get()
        self.config["use_llm"] = self.llm_var.get()
        self.config["use_nlp"] = self.nlp_var.get()
        self.config["output_dir"] = self.out_var.get()
        self.config["auto_open"] = self.auto_var.get()
        save_config(self.config)
        self.on_save(self.config)
        self.dialog.destroy()

# ─── Main App ──────────────────────────────────────────────────────────
class App:
    def __init__(self):
        self.cfg = load_config()
        self.output_path = None

        self.win = tk.Tk()
        self.win.title("Script Splitter ◬")
        self.win.geometry("680x560")
        self.win.minsize(520, 420)

        # ── Top bar ──
        top = ttk.Frame(self.win, padding=(20, 16, 20, 0))
        top.pack(fill="x")
        ttk.Label(top, text="Script Splitter ◬", font=("Helvetica", 20, "bold")).pack(side="left")
        ttk.Button(top, text="⚙", width=3, command=self.open_settings).pack(side="right")
        ttk.Label(top, text="Layout-aware screenplay parser", foreground="gray",
                  font=("Helvetica", 10)).pack(side="left", padx=(12, 0), pady=(6, 0))

        # ── Body ──
        body = ttk.Frame(self.win, padding=20)
        body.pack(fill="both", expand=True)

        # Drop zone
        self.drop_frame = tk.LabelFrame(body, text="", bd=2, relief="groove",
                                        bg="#fafafa", height=100)
        self.drop_frame.pack(fill="x")
        self.drop_frame.pack_propagate(False)

        drop_inner = tk.Frame(self.drop_frame, bg="#fafafa")
        drop_inner.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(drop_inner, text="📄  Drop screenplay here, or", bg="#fafafa",
                 font=("Helvetica", 13)).pack()
        self.browse_btn = tk.Button(drop_inner, text="Browse Files…",
                                    command=self.browse, cursor="hand2",
                                    font=("Helvetica", 11), relief="flat",
                                    bg="#e0e0e0", padx=12, pady=4)
        self.browse_btn.pack(pady=(6, 0))

        # File info row
        info = ttk.Frame(body)
        info.pack(fill="x", pady=(14, 0))
        self.file_label = ttk.Label(info, text="No file selected", foreground="gray")
        self.file_label.pack(side="left")
        self.run_btn = ttk.Button(info, text="▶  Run Pipeline", command=self.run, state="disabled")
        self.run_btn.pack(side="right")

        # Stage indicator
        self.stage_label = ttk.Label(body, text=f"Stage: {self.cfg['stage']}",
                                      foreground="gray", font=("Helvetica", 9))
        self.stage_label.pack(anchor="w", pady=(4, 0))

        # Log
        self.log = tk.Text(body, height=12, wrap="word", font=("Menlo", 9),
                           bg="#f8f8f8", fg="#222", bd=1, relief="solid")
        self.log.pack(fill="both", expand=True, pady=(8, 0))
        self.log.insert("end", "Select a screenplay and click Run.\n")

        # Output link
        self.out_link = ttk.Label(body, text="", foreground="blue", cursor="hand2")
        self.out_link.pack(anchor="w", pady=(6, 0))
        self.out_link.bind("<Button-1>", lambda e: self.open_output())

        self.selected_path = None
        self.win.mainloop()

    def browse(self):
        path = filedialog.askopenfilename(
            title="Select Screenplay",
            filetypes=[("Screenplay", "*.pdf *.docx *.txt *.fountain"),
                       ("PDF", "*.pdf"), ("Word", "*.docx"),
                       ("Text", "*.txt *.fountain")])
        if path:
            self.select_file(path)

    def select_file(self, path):
        self.selected_path = path
        self.file_label.config(text=f"📄  {os.path.basename(path)}", foreground="#333")
        self.run_btn.config(state="normal")

    def open_settings(self):
        SettingsDialog(self.win, self.cfg, self.on_settings_saved)

    def on_settings_saved(self, cfg):
        self.cfg = cfg
        self.stage_label.config(text=f"Stage: {cfg['stage']}")
        self.log_insert(f"Settings updated: stage={cfg['stage']}, llm={cfg['use_llm']}")

    def log_insert(self, msg):
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.win.update()

    def open_output(self):
        if self.output_path and os.path.exists(self.output_path):
            subprocess.run(["open", self.output_path])

    def run(self):
        if not self.selected_path or not os.path.exists(self.selected_path):
            messagebox.showerror("Error", "Please select a valid file.")
            return

        # Build output path: {output_dir}/{script_name}/
        name = script_name(self.selected_path)
        final_out = os.path.join(self.cfg["output_dir"], name)
        os.makedirs(final_out, exist_ok=True)

        self.run_btn.config(state="disabled")
        self.log.delete("1.0", "end")
        self.log_insert(f"Parsing: {os.path.basename(self.selected_path)}")
        self.log_insert(f"Stage:     {self.cfg['stage']}")
        self.log_insert(f"Output:    {final_out}")
        self.log_insert("─" * 40)

        def task():
            ok, output = run_pipeline(
                self.selected_path, self.cfg["stage"],
                self.cfg["use_llm"] and self.cfg["stage"] >= 3,
                final_out,
            )
            self.win.after(0, lambda: self._done(ok, output, final_out))

        threading.Thread(target=task, daemon=True).start()

    def _done(self, ok, output, out_path):
        self.run_btn.config(state="normal")
        for line in output.splitlines():
            self.log_insert(line)
        self.output_path = out_path
        if ok:
            # Parse stats from log
            for line in output.splitlines():
                if "Created" in line and "scenes" in line:
                    self.log_insert("")
                    self.log_insert("✅ Done.")
                    break
                if "Parsed" in line:
                    self.log_insert("")
                    self.log_insert("✅ Done. Open output to see results.")
                    break
            self.out_link.config(text=f"📂  {out_path}")
            if self.cfg["auto_open"]:
                subprocess.run(["open", out_path])
        else:
            self.log_insert("")
            self.log_insert("❌ Pipeline failed. Check the log above.")

if __name__ == "__main__":
    App()
