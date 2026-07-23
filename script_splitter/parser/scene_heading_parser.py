"""Parse raw scene heading text into structured SceneHeading."""
import re
from .constants import SCENE_HEADING_PREFIXES, PERIOD_MARKERS, VEHICLE_TERMS
from .constants import TEMPORAL_CONTINUATION_MARKERS, TIME_OF_DAY_MARKERS
from ..schemas.scene import SceneHeading
from ..utils.text_normalization import collapse_spaces

def parse_scene_heading(raw_heading: str, heading_id: str) -> SceneHeading:
    raw = raw_heading.strip()
    int_ext = _extract_prefix(raw)
    body = raw[len(int_ext):].strip()
    # Split by both '.' and ' - ' separators
    parts = []
    for chunk in body.split(" - "):
        sub_parts = [collapse_spaces(p) for p in chunk.split(".") if collapse_spaces(p)]
        parts.extend(sub_parts)

    temporal_modifier_raw = _pop_terminal_marker(parts, TEMPORAL_CONTINUATION_MARKERS)
    time_of_day_raw = None
    if temporal_modifier_raw is None:
        time_of_day_raw = _pop_terminal_marker(parts, TIME_OF_DAY_MARKERS)
    else:
        time_of_day_raw = _pop_terminal_marker(parts, TIME_OF_DAY_MARKERS)

    subject_chunks = list(parts)
    date_or_period_raw = _extract_date_or_period(parts)
    location_chunks = list(subject_chunks)
    location_raw = ". ".join(location_chunks)
    primary_location_raw = ". ".join(parts)
    primary_location_raw, background_context_raw = _split_vehicle_context(primary_location_raw)

    subject_parts = [int_ext] + subject_chunks
    scene_heading_subject_raw = _format_subject(subject_parts)

    return SceneHeading(
        heading_id=heading_id,
        raw=raw,
        scene_heading_subject_raw=scene_heading_subject_raw,
        int_ext=int_ext,
        location_raw=location_raw,
        location_chunks=location_chunks,
        primary_location_raw=primary_location_raw,
        background_context_raw=background_context_raw,
        date_or_period_raw=date_or_period_raw,
        time_of_day_raw=time_of_day_raw,
        temporal_modifier_raw=temporal_modifier_raw,
    )

def _extract_prefix(raw: str) -> str:
    upper = raw.upper()
    for prefix in sorted(SCENE_HEADING_PREFIXES, key=len, reverse=True):
        if upper.startswith(prefix):
            return raw[:len(prefix)]
    raise ValueError(f"Not a standard scene heading: {raw}")

def _pop_terminal_marker(parts: list[str], markers: set[str]) -> str | None:
    if not parts:
        return None
    candidate = parts[-1].upper()
    if candidate in markers:
        return parts.pop()
    return None

def _extract_date_or_period(parts: list[str]) -> str | None:
    if len(parts) < 2:
        return None
    period_chunks = []
    while len(parts) > 1 and _is_period_marker(parts[-1].upper()):
        period_chunks.insert(0, parts.pop())
    return ". ".join(period_chunks) if period_chunks else None

def _is_period_marker(upper: str) -> bool:
    if upper in PERIOD_MARKERS:
        return True
    if re.search(r"\b\d{3,4}S?\b", upper):
        return True
    if re.search(r"\b(?:ONE|TWO|THREE|... |TEN|TWENTY|\d+)\s+YEARS?\s+(?:AGO|EARLIER|LATER)\b", upper):
        return True
    months = "APRIL|JANUARY|FEBRUARY|MARCH|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER"
    if re.search(rf"\b(?:{months})\b", upper):
        return True
    return False

def _split_vehicle_context(location_raw: str) -> tuple[str, str | None]:
    upper = location_raw.upper()
    for term in sorted(VEHICLE_TERMS, key=len, reverse=True):
        if upper.endswith(term) and upper != term:
            prefix = location_raw[:-len(term)].strip()
            if prefix:
                return location_raw[-len(term):].strip(), prefix
    return location_raw, None

def _format_subject(parts: list[str]) -> str:
    clean = [p.strip() for p in parts if p.strip()]
    if not clean:
        return ""
    prefix = clean[0]
    rest = ". ".join(clean[1:])
    return f"{prefix} {rest}." if rest else prefix

