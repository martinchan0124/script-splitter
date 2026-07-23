# Data Schema

## 1+n Topology

Script Splitter uses a **1+n topology** borrowed from Prism:

```
1 — Global Registry (one file per entity type, integer IDs)
n — Scene Data (one file per scene, references global IDs)
```

## 1. Global Registry

Stored as JSONL files in `data/`:

| File | Entity | ID Range | Example |
|------|--------|----------|---------|
| `global_characters.jsonl` | Characters | 1001+ | `{"character_id": 1004, "name_raw": "CAROL", "character_type": "named_character"}` |
| `global_location_assets.jsonl` | Locations | 3001+ | `{"location_id": 3002, "location_class_id": "LC_INTERIOR_SINGLE_ROOM", "primary_location_raw": "INT. RITZ TOWER HOTEL. BAR/LOUNGE. NIGHT."}` |
| `global_visual_elements.jsonl` | Visual elements | 5001+ | `{"element_id": 5001, "name_raw": "pistol", "visual_element_type": "weapon_or_dangerous_object"}` |

## 2. Scene Data

Each scene has:

| File | Contents |
|------|----------|
| `scenes/S001.md` | Human-readable scene + shot timeline |
| `data/scenes.jsonl` | Scene records with entity relationships |
| `data/shots.jsonl` | Shot-level timeline with spatial_path and character_ids |

### Entity Relationships

```
scenes.scene_id
├── scene_character_instances.scene_id
│   └── scene_character_instances.global_character_id → global_characters.character_id
├── scene_location_instances.scene_id
│   └── scene_location_instances.global_location_asset_id → global_location_assets.location_id
├── scene_visual_elements.scene_id
│   └── scene_visual_elements.global_visual_element_id → global_visual_elements.element_id
├── scene_prop_interactions.scene_id
│   ├── scene_prop_interactions.scene_character_instance_id → scene_character_instances
│   └── scene_prop_interactions.scene_visual_element_id → scene_visual_elements
└── shots.scene_id
    └── shots.spatial_path → global_location_assets.location_id
    └── shots.character_ids → global_characters.character_id
```

## 3. Rules Database

Location classification and visual element patterns are defined in `rules/rules.yaml`.
See [RULES.md](RULES.md) for the full rule authoring guide.

```yaml
# Example: location matcher
- rule_id: "LOC_LARGE_ENVIRONMENT"
  priority: 70
  int_ext: "EXT"
  keywords_any:
    - OCEAN; SEA; DESERT; FOREST; MOUNTAIN
  result_class: "LC_OUTDOOR_LARGE"
  confidence: 0.82
```

```yaml
# Example: visual element pattern
- id: "VE_WEAPON_FIREARM"
  type: "weapon_or_dangerous_object"
  trigger_words:
    - pistol; gun; revolver
  interaction_verbs:
    - draw; point; hold; aim; fire
```

## 4. Location Classes

| Class ID | Description | Example |
|----------|-------------|---------|
| `LC_INTERIOR_SINGLE_ROOM` | Single room, INT | `INT. OFFICE - DAY` |
| `LC_INTERIOR_CONNECTED_ROOMS` | Multiple connected rooms | `INT. LIVING ROOM / KITCHEN` |
| `LC_VEHICLE_INTERIOR` | Vehicle interior | `INT. TAXI - NIGHT` |
| `LC_VEHICLE_ON_ROAD` | Vehicle exterior scene | `EXT./INT. SUBWAY - DAY` |
| `LC_OUTDOOR_SMALL_AREA` | Small outdoor space (<10m) | `EXT. BACKYARD - DAY` |
| `LC_OUTDOOR_STREET` | Street depth (10-20m) | `EXT. MAIN STREET - NIGHT` |
| `LC_OUTDOOR_LARGE` | Large open environment (20m+) | `EXT. THE BOTTOM OF THE SEA` |
| `LC_HYBRID_OR_UNCERTAIN` | Mixed or uncertain | `EXT./INT. BUILDING` |
| `LC_UNKNOWN` | No match | fallback |

## 5. Visual Element Types

| Type | Examples |
|------|----------|
| `weapon_or_dangerous_object` | pistol, knife, bat, bomb |
| `symbolic_object` | wedding ring, locket, mask |
| `clothing_detail` | coat, hat, sunglasses, tie |
| `container` | briefcase, box, bag, envelope |
| `communication_device` | phone, radio, walkie-talkie |
| `document` | letter, newspaper, map, photo |
| `food_or_drink` | glass, bottle, cigarette, coffee |
| `furniture` | chair, table, bed, piano |
| `equipment_mount` | holster, scabbard, sling |
| `carrier_gear` | harness, vest, oxygen tank |
