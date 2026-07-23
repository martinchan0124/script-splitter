"""Location classification. Adapted from AI3Dstoryboard with hybrid ID support."""
from .constants import VEHICLE_TERMS, LOCATION_CLASS_IDS
from ..schemas.location import GlobalLocationAsset, SceneLocationInstance
from ..schemas.scene import SceneRecord
from ..utils.ids import next_location_id

def classify_locations(scenes: list[SceneRecord], effective_periods: dict[str, str | None] = None) -> tuple[list[GlobalLocationAsset], list[SceneLocationInstance]]:
    effective_periods = effective_periods or {}
    location_registry: dict[tuple, GlobalLocationAsset] = {}
    instances: list[SceneLocationInstance] = []

    for scene in scenes:
        heading = scene.heading
        gen_class, matched_rules, conf = _classify_scene(scene)
        loc_class_id = LOCATION_CLASS_IDS.get(gen_class, "LC_UNKNOWN")
        effective_period = effective_periods.get(scene.scene_id, heading.date_or_period_raw)

        asset_key = (loc_class_id, heading.primary_location_raw, effective_period, heading.background_context_raw)
        asset = location_registry.get(asset_key)
        if asset is None:
            asset = GlobalLocationAsset(
                location_id=next_location_id(),
                location_class_id=loc_class_id,
                primary_location_raw=heading.primary_location_raw,
                date_or_period_raw=effective_period,
                background_context_raw=heading.background_context_raw,
                source_scene_ids=[scene.scene_id],
            )
            location_registry[asset_key] = asset
        elif scene.scene_id not in asset.source_scene_ids:
            asset.source_scene_ids.append(scene.scene_id)

        instances.append(SceneLocationInstance(
            scene_location_instance_id=f"SLI_{scene.scene_id}_001",
            scene_id=scene.scene_id,
            global_location_asset_id=asset.location_id,
            location_class_id=loc_class_id,
            time_of_day_raw=heading.time_of_day_raw,
            classification_confidence=conf,
        ))

    return list(location_registry.values()), instances

def _classify_scene(scene: SceneRecord) -> tuple[str, list[str], float]:
    heading = scene.heading
    primary_upper = heading.primary_location_raw.upper()

    if any(term in primary_upper for term in VEHICLE_TERMS):
        if heading.background_context_raw or "/" in heading.int_ext:
            return "vehicle_on_road_scene", ["LOC_RULE_VEHICLE_ON_ROAD"], 0.9
        return "vehicle_interior", ["LOC_RULE_VEHICLE_INTERIOR"], 0.86

    if heading.int_ext.startswith("INT") and "/" not in heading.int_ext:
        if len(heading.location_chunks) > 1:
            return "interior_connected_rooms", ["LOC_RULE_INTERIOR_CONNECTED_CHUNKS"], 0.76
        return "interior_single_room", ["LOC_RULE_INTERIOR_SINGLE_ROOM"], 0.82

    if heading.int_ext.startswith("EXT") and "/" not in heading.int_ext:
        if any(tok in primary_upper for tok in ("STREET", "AVENUE", "ROAD", "STATION")):
            return "outdoor_street_depth_10_20m", ["LOC_RULE_OUTDOOR_STREET"], 0.8
        return "outdoor_small_area_under_10m", ["LOC_RULE_OUTDOOR_SMALL_AREA"], 0.72

    return "hybrid_or_uncertain", ["LOC_RULE_HYBRID_OR_UNCERTAIN"], 0.55

def resolve_effective_periods(scenes: list[SceneRecord]) -> dict[str, str | None]:
    """Resolve period inheritance for scenes."""
    periods: dict[str, str | None] = {}
    last_period = None
    for scene in sorted(scenes, key=lambda s: s.scene_order):
        if scene.heading.date_or_period_raw:
            last_period = scene.heading.date_or_period_raw
        periods[scene.scene_id] = last_period
    return periods

