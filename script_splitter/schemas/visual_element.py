"""Visual element schemas with global registry."""
from pydantic import BaseModel, ConfigDict, Field
from .character import RawEvidence

class GlobalVisualElement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    element_id: int
    name_raw: str
    visual_element_type: str
    source_scene_ids: list[str] = Field(default_factory=list)
    semantic_attributes: dict = Field(default_factory=dict)
    requires_human_review: bool = False

class SceneVisualElement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene_visual_element_id: str
    scene_id: str
    global_visual_element_id: int
    name_raw: str
    visual_element_type: str
    raw_evidence: list[RawEvidence] = Field(default_factory=list)

class CharacterEquipmentInstance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    character_equipment_instance_id: str
    scene_id: str
    character_label_raw: str
    equipment_name_raw: str
    raw_evidence: list[RawEvidence] = Field(default_factory=list)
    attachment_default: dict = Field(default_factory=dict)

class ScenePropInteraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prop_interaction_id: str
    scene_id: str
    character_label_raw: str
    scene_character_instance_id: str | None = None
    scene_visual_element_id: str | None = None
    interaction_type: str
    raw_evidence: list[RawEvidence] = Field(default_factory=list)

