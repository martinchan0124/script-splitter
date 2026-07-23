"""Split markdown text into scene heading blocks."""
from dataclasses import dataclass, field
from .scene_heading_detector import detect_scene_headings_from_md
from .scene_heading_parser import parse_scene_heading
from ..schemas.scene import SceneHeading
from ..utils.ids import heading_id

@dataclass
class HeadingBlock:
    heading: SceneHeading
    start_line: int
    end_line: int
    original_text: str

def split_heading_blocks_from_md(md_text: str) -> list[HeadingBlock]:
    lines = md_text.splitlines(keepends=True)
    candidates = detect_scene_headings_from_md(md_text)
    blocks = []
    for index, candidate in enumerate(candidates, start=1):
        next_candidate = candidates[index] if index < len(candidates) else None
        end_line = next_candidate.line_index if next_candidate else len(lines)
        heading = parse_scene_heading(candidate.raw, heading_id(index))
        original_text = "".join(lines[candidate.line_index:end_line])
        blocks.append(HeadingBlock(heading=heading, start_line=candidate.line_index, end_line=end_line, original_text=original_text))
    return blocks

