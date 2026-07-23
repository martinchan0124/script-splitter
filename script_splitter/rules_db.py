"""Rules Database — human/AI decoupled rule management.

rules.yaml        ← human territory, fully editable
ai_rules.yaml     ← AI territory, append-only via register_rule()
                   human can view/approve/reject in Rules Manager

Usage:
    db = RuleDB()
    merged = db.load()           # human + AI merged
    db.save_human(data)          # writes rules.yaml
    db.ai_register(section, item)  # appends to ai_rules.yaml
    db.is_ai_rule(section, id_idx)  # True if rule came from AI
"""
from pathlib import Path
import copy, yaml

ROOT = Path(__file__).resolve().parent.parent
HUMAN_PATH = ROOT / "rules" / "rules.yaml"
AI_PATH = ROOT / "rules" / "ai_rules.yaml"


def _ensure_ai_file():
    if not AI_PATH.exists():
        AI_PATH.write_text(yaml.dump({
            "location_classes": [],
            "location_matchers": [],
            "visual_element_patterns": [],
            "background_population": [],
            "bit_part_characters": [],
        }, allow_unicode=True, default_flow_style=False))


def _load_yaml(path):
    try:
        return yaml.safe_load(path.read_text()) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


def _id_key(section):
    """Return the primary ID key for a section."""
    mapping = {
        "location_classes": "class_id",
        "location_matchers": "rule_id",
        "visual_element_patterns": "id",
    }
    return mapping.get(section, None)


def _get_ids(items, id_key):
    """Extract IDs from a list of dicts."""
    return {item.get(id_key) for item in items if isinstance(item, dict)}


class RuleDB:
    """Human/AI decoupled rules database."""

    def load(self):
        """Return merged human + AI rules as a single dict.
        Human rules come first; AI rules are appended.
        For list sections (background_population, bit_part_characters),
        AI items are appended to the human list."""
        human = _load_yaml(HUMAN_PATH)
        ai = _load_yaml(AI_PATH)
        merged = copy.deepcopy(human)

        # Merge simple list sections
        for section in ("background_population", "bit_part_characters"):
            human_items = set(human.get(section, []))
            ai_items = [i for i in ai.get(section, []) if i not in human_items]
            merged[section] = list(human_items) + ai_items

        # Merge structured sections (avoid duplicate IDs)
        for section in ("location_classes", "location_matchers", "visual_element_patterns"):
            merged[section] = list(human.get(section, []))
            id_k = _id_key(section)
            if id_k:
                existing = _get_ids(human.get(section, []), id_k)
                for item in ai.get(section, []):
                    if isinstance(item, dict) and item.get(id_k) not in existing:
                        merged[section].append(item)

        return merged

    def save_human(self, data):
        """Write human rules to rules.yaml. Validates first."""
        yaml.dump(data, open(HUMAN_PATH, "w"),
                  allow_unicode=True, default_flow_style=False, sort_keys=False)

    def ai_register(self, section: str, item):
        """AI appends an item to ai_rules.yaml.
        AI CANNOT delete or modify existing entries—only append."""
        _ensure_ai_file()
        ai = _load_yaml(AI_PATH)
        ai.setdefault(section, [])

        # Prevent duplicate IDs for structured sections
        id_k = _id_key(section)
        if id_k and isinstance(item, dict):
            existing = _get_ids(ai.get(section, []), id_k)
            if item.get(id_k) in existing:
                return False  # already exists

        ai[section].append(item)
        yaml.dump(ai, open(AI_PATH, "w"),
                  allow_unicode=True, default_flow_style=False, sort_keys=False)
        return True

    def is_ai_rule(self, section: str, id_or_value):
        """Check if a rule originated from AI."""
        ai = _load_yaml(AI_PATH)
        items = ai.get(section, [])
        id_k = _id_key(section)
        if id_k:
            return any(item.get(id_k) == id_or_value for item in items if isinstance(item, dict))
        return id_or_value in items

    def get_human_ids(self, section):
        """Return set of IDs/values in human rules."""
        human = _load_yaml(HUMAN_PATH)
        items = human.get(section, [])
        id_k = _id_key(section)
        if id_k:
            return _get_ids(items, id_k)
        return set(items)

    def is_editable(self, section, id_or_value):
        """True if this rule is human-owned and can be edited."""
        return not self.is_ai_rule(section, id_or_value)
