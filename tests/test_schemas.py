"""Tests for Pydantic schemas."""
from script_splitter.schemas.scene import SceneRecord, ShotRecord, SceneHeading, SourceInfo
from script_splitter.schemas.character import GlobalCharacter
from script_splitter.schemas.location import GlobalLocationAsset
from script_splitter.utils.ids import scene_id, shot_id, next_character_id, next_location_id


def test_scene_record():
   heading = SceneHeading(
       heading_id="H001", raw="INT. ROOM - DAY",
       scene_heading_subject_raw="INT. ROOM - DAY",
       int_ext="INT.", location_raw="ROOM", location_chunks=["ROOM"],
       primary_location_raw="ROOM",
   )
   record = SceneRecord(
       scene_id=scene_id(1), scene_order=1,
       heading=heading, source=SourceInfo(source_file="test.txt"),
       original_text="",
   )
   assert record.scene_id == "S001"
   assert record.heading.int_ext == "INT."


def test_shot_record():
   shot = ShotRecord(
       shot_id=shot_id("S001", 1),
       scene_id="S001", shot_order=1,
       content="Jack enters.",
   )
   assert shot.shot_id == "S001-SHOT-001"


def test_global_character():
   char = GlobalCharacter(character_id=next_character_id(), name_raw="JACK", speaking=True)
   assert char.character_id == 1001
   assert char.name_raw == "JACK"


def test_global_location():
   loc = GlobalLocationAsset(
       location_id=next_location_id(), location_class_id="LC_INTERIOR_SINGLE_ROOM",
       primary_location_raw="ROOM",
   )
   assert loc.location_id == 3001


def test_id_generators():
   assert next_location_id() == 3002
   assert next_character_id() == 1002
   assert scene_id(5) == "S005"
   assert shot_id("S001", 3) == "S001-SHOT-003"
