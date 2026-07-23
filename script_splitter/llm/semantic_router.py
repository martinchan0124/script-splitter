"""Semantic router: LLM-based routing that maps shot content to pre-registered
entity IDs. Adapted from Prism's PrismSemanticEngine with AI3Dstoryboard's
cache and fallback patterns."""
import json
import logging
from typing import Any
from .deepseek_client import DeepSeekClient
from .cache_manager import LlmCacheManager

logger = logging.getLogger(__name__)

class SemanticRouter:
    def __init__(self, client: DeepSeekClient | None = None, cache_mgr: LlmCacheManager | None = None):
        self.client = client or DeepSeekClient.from_env()
        self.cache = cache_mgr

    def route_shot(self, smjs_registry: dict, scene_id: str, shot_id: str, shot_content: str,
                   context_shots: list[dict] | None = None, use_cache: bool = True) -> dict[str, Any]:
        """Route a single shot through LLM, returning semantic updates."""
        if use_cache and self.cache:
            cached = self.cache.read_cache(scene_id, f"{shot_id}_routed.json", stage="shots")
            if cached:
                return cached

        try:
            prompt = self._build_prompt(smjs_registry, scene_id, shot_id, shot_content, context_shots or [])
            result = self.client.complete_json(prompt, temperature=0.0, max_tokens=1024)

            if use_cache and self.cache:
                self.cache.write_cache(scene_id, f"{shot_id}_routed.json", result, stage="shots")
            return result
        except Exception as e:
            logger.warning("Semantic router failed for %s: %s", shot_id, e)
            return {"sdjs_updates": [], "smjs_updates": [], "error": str(e)}

    def _build_prompt(self, registry: dict, scene_id: str, shot_id: str,
                      content: str, context: list[dict]) -> list[dict[str, str]]:
        registry_str = json.dumps(registry, indent=2, ensure_ascii=False)
        context_str = "\n".join(
            f"[{c.get('shot_id', '?')}] {c.get('content', '')}" for c in context[-4:]
        )

        system = (
            "You are a rigid JSON routing API. Output ONLY valid JSON with keys "
            "'sdjs_updates' and 'smjs_updates'."
        )
        user = f"""[ENTITY REGISTRY - ID BOUNDARY]
You MUST only use these pre-registered integer IDs:
{registry_str}

[CONTEXT]
{context_str}

[TARGET SHOT: {shot_id}]
{content}

[RULES]
1. DO NOT invent IDs.
2. sdjs_updates.target_path = ["script_scenes", "{scene_id}_shots", "{shot_id}", "spatial_path"]
   payload = [location_id] as list of ints
3. sdjs_updates.target_path for characters = ["script_scenes", "{scene_id}_shots", "{shot_id}", "characters"]
   payload = list of character int IDs
4. smjs_updates.target_path for character attributes = ["elements_registry", "characters", "<ID>", "semantic_attributes"]
   payload = {{"mood": "...", "action": "...", "physical_state": "..."}}

Return: {{"sdjs_updates": [...], "smjs_updates": [...]}}
"""
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

