"""Character extraction from scenes. Hybrid: regex dialogue cues + spaCy NER."""
import re
from collections import Counter
from .constants import CHARACTER_CUE_RE_STR, BACKGROUND_POPULATION_LABELS, BIT_PART_CHARACTER_NAMES
from ..schemas.character import GlobalCharacter, SceneCharacterInstance, SceneBackgroundPopulation, RawEvidence
from ..schemas.scene import SceneRecord
from ..utils.ids import next_character_id, scene_character_instance_id, _slug

CHARACTER_CUE_RE = re.compile(CHARACTER_CUE_RE_STR)

def extract_characters(scenes: list[SceneRecord]) -> tuple[list[GlobalCharacter], list[SceneCharacterInstance], list[SceneBackgroundPopulation]]:
    global_chars: dict[str, GlobalCharacter] = {}
    instances: list[SceneCharacterInstance] = []
    populations: list[SceneBackgroundPopulation] = []

    for scene in scenes:
        cue_counts, first_cues = _collect_character_cues(scene.original_text)
        for name_raw, cue_count in cue_counts.items():
            gc = global_chars.get(name_raw)
            if gc is None:
                gc = GlobalCharacter(
                    character_id=next_character_id(),
                    name_raw=name_raw,
                    character_type="bit_part_character" if name_raw in BIT_PART_CHARACTER_NAMES else "named_character",
                    speaking=True,
                    source_scene_ids=[scene.scene_id],
                )
                global_chars[name_raw] = gc
            elif scene.scene_id not in gc.source_scene_ids:
                gc.source_scene_ids.append(scene.scene_id)

            instance_id = scene_character_instance_id(scene.scene_id, name_raw)
            instances.append(SceneCharacterInstance(
                scene_character_instance_id=instance_id,
                scene_id=scene.scene_id,
                global_character_id=gc.character_id,
                name_raw=name_raw,
                speaking=True,
                dialogue_cue_count=cue_count,
                first_dialogue_cue_raw=first_cues.get(name_raw),
            ))
            scene.character_instance_ids.append(instance_id)

        for pop in _collect_background_populations(scene):
            populations.append(pop)
            scene.background_population_ids.append(pop.population_id)

    return list(global_chars.values()), instances, populations

def _collect_character_cues(text: str) -> tuple[Counter[str], dict[str, str]]:
    counts: Counter[str] = Counter()
    first_cues: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not _is_character_cue(stripped):
            continue
        # Handle (CONT'D)
        name_raw = re.sub(r"\s*\(CONT['’]?D\)", "", stripped).strip()
        name_raw = name_raw.lstrip("### ")
        counts[name_raw] += 1
        first_cues.setdefault(name_raw, stripped)
    return counts, first_cues

def _collect_background_populations(scene: SceneRecord) -> list[SceneBackgroundPopulation]:
    found: dict[str, RawEvidence] = {}
    for line in scene.original_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for label in BACKGROUND_POPULATION_LABELS:
            if re.search(rf"\b{re.escape(label)}\b", stripped):
                found.setdefault(label, RawEvidence(text=stripped))
    populations = []
    for idx, (label, evidence) in enumerate(found.items(), start=1):
        populations.append(SceneBackgroundPopulation(
            population_id=f"SBP_{scene.scene_id}_{_slug(label)}_{idx:03d}",
            scene_id=scene.scene_id,
            label_raw=label,
            description_raw_evidence=[evidence],
        ))
    return populations

def _is_character_cue(line: str) -> bool:
    if not line:
        return False
    stripped = line.lstrip("### ")
    if not stripped:
        return False
    if len(stripped) > 40 or "." in stripped or "," in stripped:
        return False
    return bool(CHARACTER_CUE_RE.match(stripped))

