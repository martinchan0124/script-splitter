"""ID generation utilities. Hybrid approach: uses integer IDs for the global
1+n topology (borrowed from Prism) and scene-level string IDs for backward
compatibility with the AI3Dstoryboard review system."""
import re
from collections.abc import Iterator

_char_counter: Iterator[int] = iter(range(1001, 998001))
_loc_counter: Iterator[int] = iter(range(3001, 998001))
_element_counter: Iterator[int] = iter(range(5001, 998001))

def next_character_id() -> int:
    return next(_char_counter)

def next_location_id() -> int:
    return next(_loc_counter)

def next_visual_element_id() -> int:
    return next(_element_counter)

def scene_id(order: int) -> str:
    return f"S{order:03d}"

def heading_id(index: int) -> str:
    return f"H{index:03d}"

def shot_id(scene_id: str, shot_order: int) -> str:
    return f"{scene_id}-SHOT-{shot_order:03d}"

def scene_character_instance_id(scene_id: str, name: str) -> str:
    slug = _slug(name)
    return f"SCI_{scene_id}_{slug}_001"

def _slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_") or "UNKNOWN"

