"""Scene-level schemas.
Integrates AI3Dstoryboard's detailed SceneRecord with Prism's shot-level timeline.
Uses 1+n topology: each scene has a heading + a shot timeline.
"""
from pydantic import BaseModel, ConfigDict, Field

class SceneHeading(BaseModel):
    model_config = ConfigDict(extra="forbid")
    heading_id: str
    raw: str
    scene_heading_subject_raw: str
    int_ext: str
    location_raw: str
    location_chunks: list[str] = Field(default_factory=list)
    primary_location_raw: str
    background_context_raw: str | None = None
    date_or_period_raw: str | None = None
    time_of_day_raw: str | None = None
    temporal_modifier_raw: str | None = None
    special_context: list[str] = Field(default_factory=list)
    parse_warnings: list[str] = Field(default_factory=list)

class ShotRecord(BaseModel):
    """Prism-style shot: atomic scene fragment with layout-based routing."""
    model_config = ConfigDict(extra="forbid")
    shot_id: str
    scene_id: str
    shot_order: int
    content: str
    spatial_path: list[int] = Field(default_factory=list)
    character_ids: list[int] = Field(default_factory=list)
    element_ids: list[int] = Field(default_factory=list)
    environment_spatial: str = ""
    environment_temporal: str = ""
    semantic_attributes: dict = Field(default_factory=dict)
    confidence: float = 0.0
    requires_human_review: bool = False

class SourceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_file: str
    page_start: int | None = None
    page_end: int | None = None

class SceneRecord(BaseModel):
    """Scene record combining AI3Dstoryboard entity relationships with Prism shot timelines."""
    model_config = ConfigDict(extra="forbid")
    scene_id: str
    scene_order: int
    heading: SceneHeading
    source: SourceInfo
    original_text: str = Field(default="", exclude=True)
    shots: list[ShotRecord] = Field(default_factory=list)
    # entity relationships (borrowed from AI3Dstoryboard)
    character_instance_ids: list[str] = Field(default_factory=list)
    background_population_ids: list[str] = Field(default_factory=list)
    visual_element_instance_ids: list[str] = Field(default_factory=list)
    character_equipment_instance_ids: list[str] = Field(default_factory=list)
    prop_interaction_ids: list[str] = Field(default_factory=list)
    location_links: dict[str, str | None] = Field(default_factory=dict)
    requires_human_review: bool = False
    parse_warnings: list[str] = Field(default_factory=list)

