from pydantic import BaseModel, ConfigDict, Field

class ScriptInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    warnings: list[str] = Field(default_factory=list)
    page_by_line: list[int | None] | None = None
    source_path: str = ""

