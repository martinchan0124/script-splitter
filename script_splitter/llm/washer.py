"""LLM Script Washer — uses YAML rules + LLM to produce clean instance DB."""
import json, logging, time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _summarize_rules(rule_db) -> dict:
    data = rule_db.load()
    locs = []
    for c in data.get("location_classes", []):
        locs.append(f"  {c['class_id']}: {c.get('description', '')}")
    ves = []
    for v in data.get("visual_element_patterns", []):
        tw = v.get("trigger_words", [])
        verbs = v.get("interaction_verbs", [])
        ves.append(f"  {v['id']} ({v['type']}): triggers={tw[:4]} verbs={verbs[:3]}")
    return {
        "location_classes": "\n".join(locs),
        "visual_elements": "\n".join(ves[:20]),
        "background_population": data.get("background_population", [])[:10],
        "bit_part_chars": data.get("bit_part_characters", [])[:10],
    }


class ScriptWasher:
    def __init__(self, rule_db, llm_client, cache_dir=None):
        self.db = rule_db
        self.llm = llm_client
        self.cache = None
        if cache_dir:
            from ..llm.cache_manager import LlmCacheManager
            self.cache = LlmCacheManager(cache_dir)
        self._rule_summary = _summarize_rules(rule_db)

    def wash_script(self, scenes):
        results = []
        proposals = []
        for idx, scene in enumerate(scenes, start=1):
            logger.info(f"[washer] Scene {idx}/{len(scenes)} {scene.scene_id}")
            try:
                result = self._wash_one(scene, idx, len(scenes))
                results.append(result)
                for p in result.get("new_pattern_proposals", []):
                    proposals.append(p)
            except Exception as e:
                logger.warning(f"[washer] {scene.scene_id} failed: {e}")
                results.append({"scene_id": scene.scene_id, "error": str(e)})
        if proposals:
            self._register_proposals(proposals)
        return results

    def _wash_one(self, scene, idx, total):
        if self.cache:
            cached = self.cache.read_cache(scene.scene_id, "washed.json", stage="washer")
            if cached:
                return cached
        prompt = self._build_prompt(scene, idx, total)
        response = self.llm.complete_json(prompt, temperature=0.1, max_tokens=2000)
        result = self._parse_response(response, scene)
        if self.cache:
            self.cache.write_cache(scene.scene_id, "washed.json", result, stage="washer")
        return result

    def _build_prompt(self, scene, idx, total):
        rs = self._rule_summary
        system = f"""You are a screenplay analysis engine.

Use this rule database to identify entities in each scene:

LOCATION CLASSES:
{rs['location_classes']}

VISUAL ELEMENT PATTERNS:
{rs['visual_elements']}

BACKGROUND POPULATION: {rs['background_population']}
BIT PART CHARACTERS: {rs['bit_part_chars']}

Rules:
- Match scene content to the rule database EXACTLY
- Do NOT invent location classes or element types not in the rules
- If you find something that should be a rule but isn't, propose it

Return JSON:
{{"scene_id":"...",
  "location": {{"class_id":"...","confidence":0.9}},
  "characters": [{{"name":"...","is_speaking":true}}],
  "visual_elements": [{{"type":"...","name":"...","interaction":"...","rule_id":"..."}}],
  "background_population": ["..."],
  "new_pattern_proposals": [{{"section":"...","suggestion":{{...}}}}]}}"""

        user = f"""Scene {idx}/{total}

Heading: {scene.heading.raw}
INT/EXT: {scene.heading.int_ext}
Location: {scene.heading.primary_location_raw}
Time: {scene.heading.time_of_day_raw or '—'}
Period: {scene.heading.date_or_period_raw or '—'}

Text:
{scene.original_text}"""

        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def _parse_response(self, response, scene):
        return {
            "scene_id": scene.scene_id,
            "location": response.get("location", {}),
            "characters": response.get("characters", []),
            "visual_elements": response.get("visual_elements", []),
            "background_population": response.get("background_population", []),
            "new_pattern_proposals": response.get("new_pattern_proposals", []),
        }

    def _register_proposals(self, proposals):
        reg = 0
        for prop in proposals:
            section = prop.get("section")
            sug = prop.get("suggestion")
            if section and sug:
                try:
                    self.db.ai_register(section, sug)
                    reg += 1
                except Exception as e:
                    logger.warning(f"[washer] register failed: {e}")
        if reg:
            logger.info(f"[washer] registered {reg} new pattern(s)")

