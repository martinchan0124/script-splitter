"""LLM cache manager. Adapted from AI3Dstoryboard's per-scene cache structure."""
import json
from pathlib import Path
from typing import Any

class LlmCacheManager:
    def __init__(self, cache_dir: str | Path):
        self.base = Path(cache_dir)

    def scene_path(self, scene_id: str, stage: str = "stage3") -> Path:
        p = self.base / stage / scene_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def read_cache(self, scene_id: str, filename: str, stage: str = "stage3") -> dict[str, Any] | None:
        path = self.scene_path(scene_id, stage) / filename
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def write_cache(self, scene_id: str, filename: str, data: dict[str, Any], stage: str = "stage3") -> None:
        path = self.scene_path(scene_id, stage) / filename
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def has_normalized(self, scene_id: str, stage: str = "stage3") -> bool:
        return self.read_cache(scene_id, "normalized.json", stage) is not None

    def read_normalized(self, scene_id: str, stage: str = "stage3") -> dict[str, Any] | None:
        return self.read_cache(scene_id, "normalized.json", stage)

    def write_error(self, scene_id: str, error_type: str, message: str, stage: str = "stage3") -> None:
        self.write_cache(scene_id, "error.json", {"scene_id": scene_id, "error_type": error_type, "message": str(message)}, stage)

