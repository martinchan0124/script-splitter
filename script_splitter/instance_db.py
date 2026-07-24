"""Instance Database — iterative entity registry built scene by scene."""
from __future__ import annotations
import json
from pathlib import Path

from script_splitter.utils.ids import next_character_id, next_location_id, next_visual_element_id


class InstanceDB:
   def __init__(self, known_names: list[str] | None = None):
       self.characters: dict[str, dict] = {}
       self.locations: dict[str, dict] = {}
       self.visual_elements: dict[str, dict] = {}
       self._scene_order: list[str] = []
       self._history: list[dict] = []
       if known_names:
           for name in known_names:
               self._ensure_character(name, source="prescan")

   def _ensure_character(self, name: str, source: str = "llm") -> int:
       nu = name.upper().strip()
       if nu not in self.characters:
           cid = next_character_id()
           self.characters[nu] = {
               "character_id": cid, "name_raw": nu, "source": source,
               "scenes": [], "type": "named_character", "speaking": False,
           }
       return self.characters[nu]["character_id"]

   def _ensure_location(self, raw_name: str, class_id: str) -> int:
       key = raw_name.upper().strip()
       if key not in self.locations:
           lid = next_location_id()
           self.locations[key] = {
               "location_id": lid, "primary_location_raw": raw_name,
               "location_class_id": class_id, "scenes": [],
           }
       return self.locations[key]["location_id"]

   def _ensure_visual_element(self, name: str, vtype: str, rule_id: str | None = None) -> int:
       key = f"{vtype}::{name.upper()}"
       if key not in self.visual_elements:
           eid = next_visual_element_id()
           self.visual_elements[key] = {
               "element_id": eid, "name_raw": name,
               "visual_element_type": vtype, "rule_id": rule_id, "scenes": [],
           }
       return self.visual_elements[key]["element_id"]

   def update_from_wash(self, scene_id: str, wash_result: dict):
       if scene_id not in self._scene_order:
           self._scene_order.append(scene_id)
       scene_changes = {
           "scene_id": scene_id,
           "new_characters": [],
           "new_locations": [],
           "new_visual_elements": [],
           "updated_characters": [],
       }
       for char in wash_result.get("characters", []):
           name = char.get("name", "")
           if not name:
               continue
           was_new = name.upper().strip() not in self.characters
           self._ensure_character(name)
           nu = name.upper().strip()
           if scene_id not in self.characters[nu]["scenes"]:
               self.characters[nu]["scenes"].append(scene_id)
           if char.get("is_speaking"):
               self.characters[nu]["speaking"] = True
           entry = {"name": name, "character_id": self.characters[nu]["character_id"]}
           if was_new:
               scene_changes["new_characters"].append(entry)
           else:
               scene_changes["updated_characters"].append(entry)
       loc = wash_result.get("location", {})
       if loc.get("class_id"):
           was_new = f"{scene_id}_{loc['class_id']}".upper().strip() not in self.locations
           raw_name = f"{scene_id}_{loc['class_id']}"
           self._ensure_location(raw_name, loc["class_id"])
           key = raw_name.upper().strip()
           if scene_id not in self.locations[key]["scenes"]:
               self.locations[key]["scenes"].append(scene_id)
           if was_new:
               scene_changes["new_locations"].append({
                   "class_id": loc["class_id"],
                   "location_id": self.locations[key]["location_id"],
               })
       for ve in wash_result.get("visual_elements", []):
           name = ve.get("name", "")
           vtype = ve.get("type", "")
           if not name or not vtype:
               continue
           was_new = f"{vtype}::{name.upper()}" not in self.visual_elements
           self._ensure_visual_element(name, vtype, ve.get("rule_id"))
           key = f"{vtype}::{name.upper()}"
           if scene_id not in self.visual_elements[key]["scenes"]:
               self.visual_elements[key]["scenes"].append(scene_id)
           if was_new:
               scene_changes["new_visual_elements"].append({
                   "name": name, "type": vtype,
                   "element_id": self.visual_elements[key]["element_id"],
               })
       self._history.append(scene_changes)

   def get_scene_entities(self, scene_id: str) -> dict:
       """Return characters, location, and visual elements for a given scene."""
       result = {
           "scene_id": scene_id,
           "characters": [],
           "location": None,
           "visual_elements": [],
       }
       for c in self.characters.values():
           if scene_id in c.get("scenes", []):
               result["characters"].append({
                   "name": c["name_raw"],
                   "character_id": c["character_id"],
                   "speaking": c.get("speaking", False),
               })
       for l in self.locations.values():
           if scene_id in l.get("scenes", []):
               result["location"] = {
                   "class_id": l["location_class_id"],
                   "location_id": l["location_id"],
                   "primary_location_raw": l.get("primary_location_raw", ""),
               }
       for v in self.visual_elements.values():
           if scene_id in v.get("scenes", []):
               result["visual_elements"].append({
                   "name": v["name_raw"],
                   "type": v["visual_element_type"],
                   "element_id": v["element_id"],
               })
       return result

   def get_context(self) -> dict:
       return {
           "known_characters": list(self.characters.keys()),
           "known_characters_count": len(self.characters),
           "known_locations": list(self.locations.keys()),
           "scenes_processed": len(self._scene_order),
       }

   def export(self) -> dict:
       return {
           "metadata": {
               "scenes_processed": len(self._scene_order),
               "scene_ids": self._scene_order,
                "total_changes": sum(len(h["new_characters"])+len(h["new_visual_elements"])+len(h["new_locations"]) for h in self._history),
           },
           "changes_history": self._history,
            "characters": {str(c["character_id"]): c for c in self.characters.values()},
           "locations": {str(l["location_id"]): l for l in self.locations.values()},
           "visual_elements": {str(e["element_id"]): e for e in self.visual_elements.values()},
       }

   def write(self, path: str | Path):
       Path(path).write_text(json.dumps(self.export(), indent=2, ensure_ascii=False), encoding="utf-8")

