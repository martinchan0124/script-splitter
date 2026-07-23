"""Tests for Stage 1: scene heading detection and shot splitting."""
from pathlib import Path
from script_splitter.parser.scene_splitter import split_heading_blocks_from_md
from script_splitter.parser.scene_merger import merge_heading_blocks
from script_splitter.parser.scene_heading_detector import is_scene_heading_line


def test_is_scene_heading_line():
   assert is_scene_heading_line("INT. ROOM - DAY")
   assert is_scene_heading_line("EXT. STREET - NIGHT")
   assert is_scene_heading_line("INT./EXT. BUILDING - DAY")
   assert not is_scene_heading_line("## JACK")
   assert not is_scene_heading_line("A dark figure approaches.")


def test_split_from_clarified_md():
   md = "# INT. ROOM - DAY\n\nThe room is dark.\n\n### JACK\n\n> I don't like this.\n\nHe moves to the window.\n\n# EXT. STREET - NIGHT\n\nRain falls.\n\n### JILL\n\n> Let's go.\n"
   blocks = split_heading_blocks_from_md(md)
   assert len(blocks) == 2
   assert blocks[0].heading.scene_heading_subject_raw.startswith("INT.")
   assert blocks[1].heading.scene_heading_subject_raw.startswith("EXT.")


def test_merge_with_shots():
   md = "# INT. ROOM - DAY\n\n### JACK\n\n> Hello.\n\nJack enters.\n\n# EXT. STREET - NIGHT\n\nRain.\n"
   blocks = split_heading_blocks_from_md(md)
   scenes = merge_heading_blocks(blocks, "test.script", md)
   assert len(scenes) == 2
   assert len(scenes[0].shots) >= 2
   assert scenes[0].shots[0].content.startswith("JACK:")


def test_shot_content():
   md = "# INT. ROOM - DAY\n\nJack walks in. He looks around. The door closes.\n\n### JACK\n\n> Anyone here?\n"
   blocks = split_heading_blocks_from_md(md)
   scenes = merge_heading_blocks(blocks, "test.script", md)
   assert len(scenes) == 1
   assert len(scenes[0].shots) >= 3
   assert any("Jack walks in" in s.content for s in scenes[0].shots)
   assert any("Anyone here" in s.content for s in scenes[0].shots)


def test_smoke_fountain():
   fixture = Path(__file__).parent / "fixtures" / "vp1_smoke.fountain"
   text = fixture.read_text(encoding="utf-8")
   lines = text.splitlines()
   md_lines = []
   for line in lines:
       s = line.strip()
       if s.startswith("="):
           continue
       if s.startswith("INT.") or s.startswith("EXT.") or s.startswith("INT./EXT."):
           md_lines.append(f"# {s}")
       elif s.isupper() and len(s) < 40 and ":" in s:
           char, _, dialogue = s.partition(":")
           md_lines.append(f"### {char.strip()}")
           md_lines.append(f"> {dialogue.strip()}")
       elif s.isupper() and len(s) < 40:
           md_lines.append(f"### {s}")
       elif not s.startswith("="):
           md_lines.append(s)
   md_text = "\n".join(md_lines)
   blocks = split_heading_blocks_from_md(md_text)
   assert len(blocks) == 3, f"Expected 3 headings, got {len(blocks)}"
