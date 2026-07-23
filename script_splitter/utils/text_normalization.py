"""Text normalization utilities."""
import re

def collapse_spaces(text: str) -> str:
    return " ".join(text.split())

def light_normalize_subject(text: str) -> str:
    return " ".join(text.upper().split())

def normalize_temporal_relation(raw: str | None) -> str | None:
    if raw is None:
        return None
    upper = raw.upper().strip()
    mapping = {
        "LATER": "temporal_continuation",
        "CONTINUOUS": "parallel_or_overlapping",
        "MOMENTS LATER": "temporal_continuation",
        "SAME TIME": "parallel_or_overlapping",
        "SIMULTANEOUS": "parallel_or_overlapping",
    }
    return mapping.get(upper)

def strip_parentheticals(text: str) -> str:
    return re.sub(r"\([^)]*\)", "", text).strip()

