"""Character schemas. Global registry via integer IDs + per-scene instances."""
from pydantic import BaseModel, ConfigDict, Field

class GlobalCharacter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    character_id: int  # integer ID (1+n topology)
    name_raw: str
    character_type: str = "named_character"  # named_character | bit_part_character
    speaking: bool = True
    semantic_attributes: dict = Field(default_factory=dict)
    source_scene_ids: list[str] = Field(default_factory=list)
    requires_human_review: bool = False

class SceneCharacterInstance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene_character_instance_id: str
    scene_id: str
    global_character_id: int
    name_raw: str
    speaking: bool = True
    dialogue_cue_count: int = 0
    first_dialogue_cue_raw: str | None = None

class RawEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str

class SceneBackgroundPopulation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    population_id: str
    scene_id: str
    label_raw: str
    description_raw_evidence: list[RawEvidence] = Field(default_factory=list)

