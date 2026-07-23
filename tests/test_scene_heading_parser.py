"""Tests for scene heading parsing."""
from script_splitter.parser.scene_heading_parser import parse_scene_heading
from script_splitter.utils.ids import heading_id


def test_parse_int_day():
   h = parse_scene_heading("INT. OFFICE - DAY", heading_id(1))
   assert h.int_ext == "INT."
   assert h.location_raw == "OFFICE"
   assert h.time_of_day_raw == "DAY"


def test_parse_ext_night():
   h = parse_scene_heading("EXT. MAIN STREET - NIGHT", heading_id(2))
   assert h.int_ext == "EXT."
   assert h.time_of_day_raw == "NIGHT"


def test_parse_vehicle():
   h = parse_scene_heading("INT. TAXI - DAY", heading_id(3))
   assert h.int_ext == "INT."
   assert h.primary_location_raw == "TAXI"


def test_parse_period():
   h = parse_scene_heading("INT. BAR - APRIL 1953 - NIGHT", heading_id(4))
   assert h.date_or_period_raw is not None
   assert "APRIL 1953" in h.date_or_period_raw


def test_parse_temporal_continuation():
   h = parse_scene_heading("INT. ROOM - LATER", heading_id(5))
   assert h.temporal_modifier_raw == "LATER"
   assert h.time_of_day_raw is None


def test_parse_hybrid():
   h = parse_scene_heading("EXT./INT. SUBWAY - NIGHT", heading_id(6))
   assert "/" in h.int_ext
