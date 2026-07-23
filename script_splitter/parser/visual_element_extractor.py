"""Visual element extraction. Adapted from AI3Dstoryboard."""
import re
from ..schemas.character import RawEvidence, SceneCharacterInstance
from ..schemas.scene import SceneRecord
from ..schemas.visual_element import GlobalVisualElement, SceneVisualElement, CharacterEquipmentInstance, ScenePropInteraction
from ..utils.ids import next_visual_element_id, _slug

ACCESSORY_PATTERNS = [
    (re.compile(r"\bgreen silk scarf\b", re.IGNORECASE), "green silk scarf", "symbolic_object"),
]
WEAPON_PATTERNS = [
    (re.compile(r"\bpistol\b", re.IGNORECASE), "pistol"),
    (re.compile(r"\bgun\b", re.IGNORECASE), "gun"),
]
EQUIPMENT_RE = re.compile(r"\b(?P<char>[A-Z][A-Z ]+?)\s+stands\b.*\b(?P<equip>pistol|gun)\s+in\s+his\s+holster\b", re.IGNORECASE)
USED_WEAPON_RE = re.compile(r"\b(?P<char>[A-Z][A-Z ]+?)\s+(?P<action>draws|points|holds|aims)\s+(?:his|her|the)?\s*(?P<equip>pistol|gun)\b", re.IGNORECASE)

def extract_visual_elements(scenes: list[SceneRecord], char_instances: list[SceneCharacterInstance]) -> tuple[list[GlobalVisualElement], list[SceneVisualElement], list[CharacterEquipmentInstance], list[ScenePropInteraction]]:
    char_lookup = {(inst.scene_id, inst.name_raw): inst.scene_character_instance_id for inst in char_instances}
    global_elems: dict[str, GlobalVisualElement] = {}
    scene_elems: list[SceneVisualElement] = []
    equipments: list[CharacterEquipmentInstance] = []
    interactions: list[ScenePropInteraction] = []

    for scene in scenes:
        for line in _action_lines(scene.original_text):
            scene_elems.extend(_extract_accessories(scene, line, global_elems))
            equipments.extend(_extract_equipment(scene, line))
            used_elems, props = _extract_used_equipment(scene, line, global_elems, char_lookup)
            scene_elems.extend(used_elems)
            interactions.extend(props)

    return list(global_elems.values()), scene_elems, equipments, interactions

def _extract_accessories(scene: SceneRecord, line: str, global_elems: dict) -> list[SceneVisualElement]:
    elems = []
    for pattern, name_raw, etype in ACCESSORY_PATTERNS:
        if not pattern.search(line):
            continue
        ge = _get_global(global_elems, name_raw, etype, scene.scene_id)
        elems.append(SceneVisualElement(
            scene_visual_element_id=f"SVE_{scene.scene_id}_{_slug(name_raw)}_001",
            scene_id=scene.scene_id,
            global_visual_element_id=ge.element_id,
            name_raw=name_raw,
            visual_element_type=etype,
            raw_evidence=[RawEvidence(text=line)],
        ))
    return elems

def _extract_equipment(scene: SceneRecord, line: str) -> list[CharacterEquipmentInstance]:
    m = EQUIPMENT_RE.search(line)
    if not m:
        return []
    char_label = _norm(m.group("char"))
    equip_name = m.group("equip").lower()
    equip = CharacterEquipmentInstance(
        character_equipment_instance_id=f"CEI_{scene.scene_id}_{_slug(char_label)}_{_slug(equip_name)}_001",
        scene_id=scene.scene_id,
        character_label_raw=char_label,
        equipment_name_raw=equip_name,
        raw_evidence=[RawEvidence(text=line)],
        attachment_default={"attachment_point": "waist_belt_right", "mount_type": "holster", "requires_manual_binding": True},
    )
    scene.character_equipment_instance_ids.append(equip.character_equipment_instance_id)
    return [equip]

def _extract_used_equipment(scene: SceneRecord, line: str, global_elems: dict, lookup: dict) -> tuple[list[SceneVisualElement], list[ScenePropInteraction]]:
    m = USED_WEAPON_RE.search(line)
    if not m:
        return [], []
    char_label = _norm(m.group("char"))
    equip_name = m.group("equip").lower()
    action = m.group("action").lower()
    ge = _get_global(global_elems, equip_name, "weapon_or_dangerous_object", scene.scene_id)
    ve = SceneVisualElement(
        scene_visual_element_id=f"SVE_{scene.scene_id}_{_slug(equip_name)}_001",
        scene_id=scene.scene_id,
        global_visual_element_id=ge.element_id,
        name_raw=equip_name,
        visual_element_type="weapon_or_dangerous_object",
        raw_evidence=[RawEvidence(text=line)],
    )
    inter = ScenePropInteraction(
        prop_interaction_id=f"SPI_{scene.scene_id}_001",
        scene_id=scene.scene_id,
        character_label_raw=char_label,
        scene_character_instance_id=lookup.get((scene.scene_id, char_label)),
        scene_visual_element_id=ve.scene_visual_element_id,
        interaction_type=_inter_type(action),
        raw_evidence=[RawEvidence(text=line)],
    )
    return [ve], [inter]

def _get_global(global_elems: dict, name_raw: str, etype: str, scene_id: str) -> GlobalVisualElement:
    key = name_raw.lower()
    ge = global_elems.get(key)
    if ge is None:
        ge = GlobalVisualElement(
            element_id=next_visual_element_id(),
            name_raw=name_raw,
            visual_element_type=etype,
            source_scene_ids=[scene_id],
        )
        global_elems[key] = ge
    elif scene_id not in ge.source_scene_ids:
        ge.source_scene_ids.append(scene_id)
    return ge

def _action_lines(text: str) -> list[str]:
    return [l.strip() for l in text.splitlines() if l.strip()]

def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.upper()).strip()

def _inter_type(action: str) -> str:
    mapping = {"draws": "drawn", "points": "aimed", "aims": "aimed"}
    return mapping.get(action, "held")

