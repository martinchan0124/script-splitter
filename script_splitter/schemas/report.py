"""Parse report and review tracking schemas."""
from pydantic import BaseModel, ConfigDict, Field

class WarningRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    warning_id: str
    record_type: str
    record_id: str
    scene_id: str = ""
    warning_code: str
    message: str
    severity: str = "low"

class ReviewRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    review_id: str
    record_type: str
    record_id: str
    scene_id: str = ""
    reason_code: str
    message: str = ""
    severity: str = "medium"

class ParseReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_file: str
    input_format: str
    stage: int
    heading_count: int = 0
    scene_count: int = 0
    shot_count: int = 0
    llm_used: bool = False
    character_count: int = 0
    location_asset_count: int = 0
    visual_element_count: int = 0
    intention_count: int = 0
    beat_count: int = 0
    intentions_requiring_review: int = 0
    beats_requiring_review: int = 0
    warnings: list[str] = Field(default_factory=list)
    review_count: int = 0

