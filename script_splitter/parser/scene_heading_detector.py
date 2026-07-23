"""Scene heading detection. Adapted from AI3Dstoryboard.
Also handles the clarifier's Markdown format (#, ###, >)."""
import re
from dataclasses import dataclass, field
from .constants import SCENE_HEADING_PREFIXES, SPECIAL_MARKERS

@dataclass(frozen=True)
class HeadingCandidate:
    line_index: int
    raw: str

def is_scene_heading_line(line: str) -> bool:
    stripped = line.strip().lstrip("# ")
    upper = stripped.upper()
    return any(upper.startswith(p) for p in SCENE_HEADING_PREFIXES)

def detect_scene_headings_from_md(md_text: str) -> list[HeadingCandidate]:
    """Detect scene headings from clarifier Markdown."""
    lines = md_text.splitlines()
    candidates = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# ") and is_scene_heading_line(stripped):
            raw_heading = stripped[2:].strip()  # remove # prefix
            candidates.append(HeadingCandidate(line_index=i, raw=raw_heading))
    return candidates

def detect_scene_headings_from_raw(lines: list[str]) -> list[HeadingCandidate]:
    """Detect scene headings from raw script text (no clarifier)."""
    return [
        HeadingCandidate(line_index=i, raw=line.strip())
        for i, line in enumerate(lines)
        if is_scene_heading_line(line)
    ]

def detect_special_markers(lines: list[str]) -> list["SpecialMarkerCandidate"]:
    from dataclasses import dataclass
    @dataclass(frozen=True)
    class SpecialMarkerCandidate:
        line_index: int
        raw: str
    return [
        SpecialMarkerCandidate(line_index=i, raw=line.strip())
        for i, line in enumerate(lines)
        if line.strip().upper() in SPECIAL_MARKERS
    ]

