"""Output package exporter. Writes structured JSONL, CSV, review files,
and scene markdowns to a directory."""
import json
import csv
import os
from pathlib import Path
from typing import Any
from ..schemas.scene import SceneRecord
from ..schemas.report import ParseReport

def export_output_package(
    scenes: list[SceneRecord],
    report: ParseReport,
    output_dir: str | Path,
    wash_results: dict[str, dict] | None = None,
    global_characters: list | None = None,
    global_location_assets: list | None = None,
    global_visual_elements: list | None = None,
    scene_character_instances: list | None = None,
    scene_location_instances: list | None = None,
    scene_visual_elements: list | None = None,
    character_equipment_instances: list | None = None,
    scene_prop_interactions: list | None = None,
    scene_intention_analyses: list | None = None,
    scene_beats: list | None = None,
    reviews: list | None = None,
    warnings: list | None = None,
) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "scenes").mkdir(exist_ok=True)
    (out / "data").mkdir(exist_ok=True)
    (out / "review").mkdir(exist_ok=True)

    # Scene markdowns
    for scene in scenes:
        lines = [
            f"# {scene.heading.raw}",
            f"**Scene ID:** {scene.scene_id}",
            f"**Order:** {scene.scene_order}",
            "",
            "## SHOTS",
        ]
        for shot in scene.shots:
            chars = ", ".join(str(c) for c in shot.character_ids) if shot.character_ids else "?"
            locs = ", ".join(str(l) for l in shot.spatial_path) if shot.spatial_path else "?"
            lines.append(f"- **{shot.shot_id}** [{locs} / {chars}]: {shot.content}")
        lines.append("")
        # Wash results write-back
        if wash_results and scene.scene_id in wash_results:
            wr = wash_results[scene.scene_id]
            lines.append("## RECOGNIZED ENTITIES")
            if wr.get("location"):
                loc = wr["location"]
                lines.append(f"**Location:** {loc.get('primary_location_raw', '?')} (class: {loc['class_id']}, id: {loc['location_id']})")
            chars = wr.get("characters", [])
            if chars:
                lines.append("**Characters:**")
                for c in chars:
                    sp = "🎤 " if c.get("speaking") else ""
                    lines.append(f"- {sp}{c['name']} (id: {c['character_id']})")
            ves = wr.get("visual_elements", [])
            if ves:
                lines.append("**Visual Elements:**")
                for v in ves:
                    lines.append(f"- {v['name']} ({v['type']}, id: {v['element_id']})")
            lines.append("")
        lines.append("## ORIGINAL SCRIPT TEXT - DO NOT MODIFY")
        lines.append(scene.original_text)
        (out / "scenes" / f"{scene.scene_id}.md").write_text("\n".join(lines), encoding="utf-8")

    # JSONL exports
    _write_jsonl(out / "data" / "scenes.jsonl", scenes)
    _write_jsonl(out / "data" / "shots.jsonl", [s for scene in scenes for s in scene.shots])
    if global_characters:
        _write_jsonl(out / "data" / "global_characters.jsonl", global_characters)
    if global_location_assets:
        _write_jsonl(out / "data" / "global_location_assets.jsonl", global_location_assets)
    if global_visual_elements:
        _write_jsonl(out / "data" / "global_visual_elements.jsonl", global_visual_elements)
    if scene_character_instances:
        _write_jsonl(out / "data" / "scene_character_instances.jsonl", scene_character_instances)
    if scene_location_instances:
        _write_jsonl(out / "data" / "scene_location_instances.jsonl", scene_location_instances)
    if scene_visual_elements:
        _write_jsonl(out / "data" / "scene_visual_elements.jsonl", scene_visual_elements)
    if scene_intention_analyses:
        _write_jsonl(out / "data" / "scene_intention_analysis.jsonl", scene_intention_analyses)
    if scene_beats:
        _write_jsonl(out / "data" / "scene_beats.jsonl", scene_beats)
    if character_equipment_instances:
        _write_jsonl(out / "data" / "character_equipment_instances.jsonl", character_equipment_instances)
    if scene_prop_interactions:
        _write_jsonl(out / "data" / "scene_prop_interactions.jsonl", scene_prop_interactions)

    # Report
    (out / "data" / "parse_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Reviews
    if reviews:
        _write_csv(out / "review" / "human_review_required.csv", reviews)
    if warnings:
        _write_csv(out / "review" / "extraction_warnings.csv", warnings)

def _write_jsonl(path: Path, records: list[Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            data = r.model_dump(mode="json") if hasattr(r, "model_dump") else r
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

def _write_csv(path: Path, records: list[Any]) -> None:
    if not records:
        return
    first = records[0]
    fieldnames = list(first.model_dump().keys()) if hasattr(first, "model_dump") else list(first.keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            data = r.model_dump(mode="json") if hasattr(r, "model_dump") else r
            writer.writerow(data)

