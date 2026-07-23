 # Data Schema
 
 Script Splitter uses a **1+n topology**:
 
 ## 1. Global Registry (1)
 Stored as JSONL files in `data/`:
 - `global_characters.jsonl` — Character definitions with integer IDs (1001+)
 - `global_location_assets.jsonl` — Location definitions with integer IDs (3001+)
 - `global_visual_elements.jsonl` — Visual element definitions with integer IDs (5001+)
 
 ## n. Scene Data (n)
 Each scene has:
 - `scenes/Sxxx.md` — Human-readable scene with shot timeline
 - `data/scenes.jsonl` — Scene records with entity relationships
 - `data/shots.jsonl` — Shot-level timeline
 
 Entity relationships follow AI3Dstoryboard conventions:
 - `scene_character_instances.scene_id → scenes.scene_id`
 - `scene_character_instances.global_character_id → global_characters.character_id`
 - `scene_location_instances.global_location_asset_id → global_location_assets.location_id`
 + 
