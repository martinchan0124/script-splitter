"""NLP engine for pre-scanning and registering entities.
Adapted from Prism's NLP_Scanner: uses spaCy NER + regex dialogue cues."""
import re
import logging

logger = logging.getLogger(__name__)

class PrismNLPEngine:
    def __init__(self, model_size: str = "en_core_web_sm"):
        self._model_size = model_size
        self._nlp = None

    def _ensure_loaded(self):
        if self._nlp is not None:
            return
        try:
            import spacy
            self._nlp = spacy.load(self._model_size)
        except OSError:
            logger.warning("spaCy model %s not found. Run: python -m spacy download %s", self._model_size, self._model_size)
            self._nlp = None

    def scan_and_register(self, md_text: str) -> dict:
        """Returns {characters: {name: id}, locations: {name: id}}."""
        self._ensure_loaded()
        found_persons = set()
        found_locations = set()

        # Extract locations from scene headings
        scene_pattern = re.compile(r"^#\s*(?:INT\.|EXT\.|INT\./EXT\.)\s+(.*?)(?:\.|\s+-)", re.MULTILINE)
        for match in scene_pattern.finditer(md_text):
            loc_name = match.group(1).strip()
            found_locations.add(self._normalize_name(loc_name))

        # Clean lines for character extraction
        clean_lines = [line for line in md_text.split("\n") if not line.strip().startswith("#")]
        safe_text = "\n".join(clean_lines)

        # Dialogue cue extraction
        dialogue_pattern = re.compile(r"^([A-Z\s]+):", re.MULTILINE)
        for match in dialogue_pattern.finditer(safe_text):
            found_persons.add(self._normalize_name(match.group(1)))

        # spaCy NER extraction
        if self._nlp:
            doc = self._nlp(safe_text)
            for ent in doc.ents:
                if (ent.label_ == "ORG" and ent.text.isupper()) or ent.label_ == "PERSON":
                    found_persons.add(self._normalize_name(ent.text))

        # Filter and resolve aliases
        blacklist = {"Man", "Woman", "Boy", "Girl", "Int", "Ext", "Day", "Night", "Continuous"}
        filtered = {n for n in found_persons if len(n) > 1 and n not in blacklist}
        final_persons = self._resolve_aliases(filtered)

        from script_splitter.utils.ids import next_character_id, next_location_id
        registry = {"characters": {}, "locations": {}}
        for name in final_persons:
            registry["characters"][name] = next_character_id()
        for loc in sorted(found_locations):
            registry["locations"][loc] = next_location_id()
        logger.info("NLP pre-scan: %d characters, %d locations", len(registry["characters"]), len(registry["locations"]))
        return registry

    def _normalize_name(self, name: str) -> str:
        return re.sub(r"[^A-Za-z0-9\s]", "", name).strip().title()

    def _resolve_aliases(self, name_set: set) -> list:
        sorted_names = sorted(list(name_set), key=len, reverse=True)
        unique = []
        for name in sorted_names:
            if not any(name in accepted.split() for accepted in unique):
                unique.append(name)
        return sorted(unique)

