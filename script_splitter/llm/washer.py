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

    def wash_script(self, scenes, instance_db=None):
        results = []
        proposals = []
        if instance_db:
            self._instance_context = instance_db.get_context()
        for idx, scene in enumerate(scenes, start=1):
            logger.info(f"[washer] Scene {idx}/{len(scenes)} {scene.scene_id}")
            try:
                result = self._wash_one(scene, idx, len(scenes))
                results.append(result)
                if instance_db:
                    instance_db.update_from_wash(scene.scene_id, result)
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

        ctx_str = ""
        ctx = self._instance_context if hasattr(self, "_instance_context") else {}
        if ctx.get("known_characters"):
            ctx_str = f"\nKnown entities: {ctx.get('known_characters', [])}\n"
        user = f"""Scene {idx}/{total}

{ctx_str}
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

    SECTION_ALIASES = {
        "visual_element_patterns": ["visual_element_patterns", "visual elements", "visual_element_pattern",
                                     "visual_elements", "visual element patterns",
                                     "VISUAL_ELEMENT_PATTERNS", "VISUAL ELEMENT PATTERNS"],
        "location_classes": ["location_classes", "location class", "LOCATION CLASSES"],
        "location_matchers": ["location_matchers", "location matcher", "LOCATION MATCHERS"],
        "background_population": ["background_population", "background population", "BACKGROUND POPULATION"],
        "bit_part_characters": ["bit_part_characters", "bit part characters", "BIT PART CHARACTERS"],
    }
    KNOWN_SECTIONS = set(SECTION_ALIASES.keys())

    @staticmethod
    def _normalize_section(raw):
        raw_lower = raw.lower().replace(" ", "_")
        for canonical, aliases in ScriptWasher.SECTION_ALIASES.items():
            if raw_lower in [a.lower().replace(" ", "_") for a in aliases] or raw_lower == canonical:
                return canonical
        return raw

    def _register_proposals(self, proposals):
        reg = 0
        for prop in proposals:
            section = self._normalize_section(prop.get("section", ""))
            if section not in self.KNOWN_SECTIONS:
                logger.warning(f"[washer] skipping unknown section '{section}' from proposal")
                continue
            sug = prop.get("suggestion")
            if section and sug:
                try:
                    self.db.ai_register(section, sug)
                    reg += 1
                except Exception as e:
                    logger.warning(f"[washer] register failed: {e}")
        if reg:
            logger.info(f"[washer] registered {reg} new pattern(s)")

