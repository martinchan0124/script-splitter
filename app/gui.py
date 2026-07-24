"""Script Splitter Web GUI — Flask-based UI for screenplay parsing pipeline."""
import json, os, shutil, sys, threading, time, uuid
from datetime import datetime
from pathlib import Path

import flask

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from script_splitter.pipeline import run_pipeline

app = flask.Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "script-splitter-dev"

UPLOAD_DIR = ROOT / "output" / "web_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# In-memory run state
_run_state: dict = {
    "current_output": None,
    "running": False,
    "progress": [],
    "error": None,
}


# ── Helpers ────────────────────────────────────────────────────────────────

def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().strip().splitlines() if line.strip()]


def _load_output_dir(path: Path) -> dict:
    """Load all structured data from an output directory."""
    data_dir = path / "data"
    scenes_dir = path / "scenes"
    result = {
        "report": {},
        "scenes": [],
        "shots": [],
        "global_characters": [],
        "global_location_assets": [],
        "global_visual_elements": [],
        "scene_character_instances": [],
        "scene_location_instances": [],
        "scene_visual_elements": [],
        "scene_markdowns": [],
        "instance_db": {},
    }
    # Report
    report_path = data_dir / "parse_report.json"
    if report_path.exists():
        result["report"] = json.loads(report_path.read_text())

    # Scene records + shots
    scenes = _load_jsonl(data_dir / "scenes.jsonl")
    result["scenes"] = scenes
    shots = _load_jsonl(data_dir / "shots.jsonl")
    result["shots"] = shots

    # Entity data
    result["global_characters"] = _load_jsonl(data_dir / "global_characters.jsonl")
    result["global_location_assets"] = _load_jsonl(data_dir / "global_location_assets.jsonl")
    result["global_visual_elements"] = _load_jsonl(data_dir / "global_visual_elements.jsonl")
    result["scene_character_instances"] = _load_jsonl(data_dir / "scene_character_instances.jsonl")
    result["scene_location_instances"] = _load_jsonl(data_dir / "scene_location_instances.jsonl")
    result["scene_visual_elements"] = _load_jsonl(data_dir / "scene_visual_elements.jsonl")

    # Scene markdowns
    if scenes_dir.exists():
        result["scene_markdowns"] = sorted(
            [f.name for f in scenes_dir.iterdir() if f.suffix == ".md"]
        )

    # Instance DB
    inst_path = path / "instance_db.json"
    if inst_path.exists():
        result["instance_db"] = json.loads(inst_path.read_text())

    # Build scene-to-data mapping
    scene_map = {}
    for s in scenes:
        sid = s.get("scene_id", "")
        heading = s.get("heading", {})
        if isinstance(heading, dict):
            raw = heading.get("raw", "")
        else:
            raw = str(heading)
        scene_map[sid] = {
            "order": s.get("scene_order", 0),
            "heading": raw,
            "shots": [sh for sh in shots if sh.get("scene_id") == sid],
            "characters": [c for c in result["scene_character_instances"] if c.get("scene_id") == sid],
            "locations": [l for l in result["scene_location_instances"] if l.get("scene_id") == sid],
            "visual_elements": [v for v in result["scene_visual_elements"] if v.get("scene_id") == sid],
        }
    result["scene_map"] = scene_map

    return result


# ── Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return flask.render_template("index.html", state=_run_state)


@app.route("/run", methods=["POST"])
def run():
    if _run_state["running"]:
        return flask.jsonify({"error": "Already running"}), 400

    file = flask.request.files.get("script")
    if not file or not file.filename:
        return flask.jsonify({"error": "No file uploaded"}), 400

    stage = int(flask.request.form.get("stage", 2))
    use_llm = flask.request.form.get("use_llm", "on") == "on"
    use_wash = flask.request.form.get("use_wash", "off") == "on"
    use_nlp = flask.request.form.get("use_nlp", "on") == "on"

    # Save upload
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    upload_path = UPLOAD_DIR / run_id / file.filename
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    file.save(str(upload_path))

    output_dir = UPLOAD_DIR / run_id / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    _run_state["running"] = True
    _run_state["progress"] = []
    _run_state["error"] = None
    _run_state["current_output"] = None

    def _progress(msg):
        _run_state["progress"].append(msg)

    def _run():
        try:
            run_pipeline(
                str(upload_path),
                stage=stage,
                use_llm=use_llm,
                use_wash=use_wash,
                use_nlp=use_nlp,
                output_dir=str(output_dir),
                progress=_progress,
                llm_cache_dir=str(output_dir / "llm_cache") if stage >= 3 and use_llm else None,
            )
            _run_state["current_output"] = str(output_dir)
        except Exception as e:
            _run_state["error"] = str(e)
        finally:
            _run_state["running"] = False

    threading.Thread(target=_run, daemon=True).start()
    return flask.jsonify({"status": "started"})


@app.route("/progress")
def progress():
    return flask.jsonify({
        "running": _run_state["running"],
        "progress": _run_state["progress"],
        "error": _run_state["error"],
        "current_output": _run_state["current_output"],
    })


@app.route("/results")
def results():
    out = _run_state.get("current_output")
    if not out:
        return flask.redirect("/")
    data = _load_output_dir(Path(out))
    return flask.render_template("results.html", data=data)


@app.route("/results/<scene_id>")
def scene_detail(scene_id):
    out = _run_state.get("current_output")
    if not out:
        return flask.redirect("/")
    data = _load_output_dir(Path(out))
    scene = data.get("scene_map", {}).get(scene_id, {})
    return flask.render_template("scene_detail.html", scene=scene, scene_id=scene_id)


@app.route("/entities")
def entities():
    out = _run_state.get("current_output")
    if not out:
        return flask.redirect("/")
    data = _load_output_dir(Path(out))
    return flask.render_template("entities.html", data=data)


@app.route("/rules")
def rules_view():
    """View rules.yaml and ai_rules.yaml"""
    rules_path = ROOT / "rules" / "rules.yaml"
    ai_rules_path = ROOT / "rules" / "ai_rules.yaml"
    rules_text = rules_path.read_text() if rules_path.exists() else ""
    ai_rules_text = ai_rules_path.read_text() if ai_rules_path.exists() else ""
    return flask.render_template("rules.html", rules_text=rules_text, ai_rules_text=ai_rules_text)


@app.route("/instance-db")
def instance_db_view():
    out = _run_state.get("current_output")
    if not out:
        return flask.redirect("/")
    data = _load_output_dir(Path(out))
    idb = data.get("instance_db", {})
    return flask.render_template("instance_db.html", idb=idb)


@app.route("/api/data")
def api_data():
    out = _run_state.get("current_output")
    if not out:
        return flask.jsonify({})
    return flask.jsonify(_load_output_dir(Path(out)))


# ── Entry point ─────────────────────────────────────────────────────────

def main():
    import webbrowser
    url = "http://127.0.0.1:5001"
    print(f"  Script Splitter Web GUI → {url}")
    webbrowser.open(url)
    app.run(host="127.0.0.1", port=5001, debug=False)


if __name__ == "__main__":
    main()
