"""Merge heading blocks into SceneRecords with shot-level timeline.
Combines AI3Dstoryboard's scene merge logic with Prism's shot splitting."""
from dataclasses import dataclass, field
import re
from .scene_splitter import HeadingBlock
from .constants import TEMPORAL_CONTINUATION_MARKERS
from ..schemas.scene import SceneRecord, SourceInfo, ShotRecord
from ..schemas.scene import SceneHeading
from ..utils.ids import scene_id, shot_id
from ..utils.text_normalization import light_normalize_subject, normalize_temporal_relation

def merge_heading_blocks(blocks: list[HeadingBlock], source_file: str, md_text: str = "") -> list[SceneRecord]:
    """Create SceneRecords from heading blocks, with shot-level timeline."""
    scenes = []
    for order, block in enumerate(blocks, start=1):
        sid = scene_id(order)
        original_text = block.original_text

        # Split into shots using Prism-style sentence + dialogue boundary splitting
        shots = _create_shots(sid, original_text)

        # Parse heading from text
        heading = block.heading

        scenes.append(SceneRecord(
            scene_id=sid,
            scene_order=order,
            heading=heading,
            source=SourceInfo(source_file=source_file, page_start=None, page_end=None),
            original_text=original_text,
            shots=shots,
        ))
    return scenes


import re as _re
def _merge_action_lines(lines):
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]; stripped = line.strip()
        if not stripped:
            i += 1; continue  # skip empty lines
        
        # Merge consecutive > lines (with gap-tolerant scan)
        if stripped.startswith(">"):
            merged = stripped
            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if not nxt:
                    j += 1; continue  # skip empty lines between > blocks
                if nxt.startswith(">"):
                    merged += " " + nxt.lstrip("> ")
                    j += 1
                else:
                    break
            merged = _re.sub(r'\s+', ' ', merged)
            result.append(merged)
            i = j; continue
            
        if stripped.startswith("#"):
            result.append(line); i += 1; continue
        merged = stripped
        while i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt.startswith("#") or nxt.startswith(">"): break
            if not merged.rstrip().endswith((".","!","?")) or (nxt and nxt[0].islower()):
                merged += " " + nxt; i += 1
            else: break
        merged = _re.sub(r'\s+', ' ', merged)
        result.append(merged); i += 1
    return result

def _last_speaker(shots):
    for s in reversed(shots):
        if ":" in s.content: return s.content.split(":")[0].strip()
    return None

def _create_shots(scene_id_str, text):
    from .scene_heading_detector import is_scene_heading_line
    import re as _re
    merged = _merge_action_lines(text.splitlines())
    shots = []; shot_order = 0; pending = None; heading_seen = False
    for fl in merged:
        s = fl.strip()
        if not s: continue
        if not heading_seen and is_scene_heading_line(s): heading_seen = True; continue
        if s.startswith("### "): pending = s[4:].strip(); continue
        if s.startswith("(") and s.endswith(")"):
            shot_order += 1; shots.append(ShotRecord(shot_id=shot_id(scene_id_str, shot_order), scene_id=scene_id_str, shot_order=shot_order, content=s))
            continue
        if s.startswith(">"):
            tc = s.lstrip("> "); sp = pending if pending else _last_speaker(shots); pending = None
            # Parenthetical continuation: merge with previous shot instead of new shot
            if tc.startswith("(") and shots:
                prev = shots[-1]
                prev.content += " " + tc
                continue
            if sp:
                shot_order += 1; shots.append(ShotRecord(shot_id=shot_id(scene_id_str, shot_order), scene_id=scene_id_str, shot_order=shot_order, content=_re.sub(r'\s+', ' ', f"{sp}: {tc}")))
            else:
                shot_order += 1; shots.append(ShotRecord(shot_id=shot_id(scene_id_str, shot_order), scene_id=scene_id_str, shot_order=shot_order, content=_re.sub(r'\s+', ' ', tc)))
            continue
        for sentence in _re.split(r"(?<=[.!?])\s+", s):
            sentence = sentence.strip()
            if sentence:
                shot_order += 1; shots.append(ShotRecord(shot_id=shot_id(scene_id_str, shot_order), scene_id=scene_id_str, shot_order=shot_order, content=_re.sub(r'\s+', ' ', sentence)))
    return shots
