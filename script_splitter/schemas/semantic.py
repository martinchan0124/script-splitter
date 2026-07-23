"""Semantic analysis schemas for scene intentions and beats."""
from pydantic import BaseModel, ConfigDict, Field

class SourceTextSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_line: int | None = None
    end_line: int | None = None
    text: str = ""

class SemanticValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str | None = None
    source_type: str = "unresolved"
    raw_evidence: list[dict] = Field(default_factory=list)
    confidence: float = 0.0

class SceneIntentionAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene_id: str
    primary_active_character_id: str | None = None
    primary_intention: SemanticValue = Field(default_factory=SemanticValue)
    opposing_force_or_obstacle: SemanticValue = Field(default_factory=SemanticValue)
    requires_human_review: bool = False
    parse_warnings: list[str] = Field(default_factory=list)

class SceneBeat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    beat_id: str
    scene_id: str
    beat_order: int
    tactic_verb_phrase: str | None = None
    active_character_id: str | None = None
    character_name: str | None = None
    character_motivation: str | None = None
    beat_trigger: str | None = None
    source_excerpt: str | None = None
    source_text_span: SourceTextSpan = Field(default_factory=SourceTextSpan)
    confidence: float = 0.0
    requires_human_review: bool = False

