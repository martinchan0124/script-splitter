"""Location schemas. Uses 1+n topology with integer IDs for global assets."""
from pydantic import BaseModel, ConfigDict, Field

class GlobalLocationAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location_id: int
    location_class_id: str
    primary_location_raw: str
    date_or_period_raw: str | None = None
    background_context_raw: str | None = None
    source_scene_ids: list[str] = Field(default_factory=list)
    semantic_attributes: dict = Field(default_factory=dict)
    requires_human_review: bool = False

class LocationClassRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location_class_id: str
    ai3d_generation_class: str
    class_name: str
    default_workflow_profile_id: str | None = None
    supports_background_panorama: bool = False
    requires_background_panorama_by_default: bool = False
    requires_human_review: bool = False

class SceneLocationInstance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene_location_instance_id: str
    scene_id: str
    global_location_asset_id: int
    location_class_id: str
    time_of_day_raw: str | None = None
    classification_confidence: float = 0.0
    requires_human_review: bool = False

