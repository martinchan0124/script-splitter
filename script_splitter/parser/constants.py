"""Constants for screenplay parsing."""

SCENE_HEADING_PREFIXES = {
    "INT.", "EXT.", "INT./EXT.", "EXT./INT.",
    "I/E.", "INT/EXT", "EXT/INT",
}

SPECIAL_MARKERS = {
    "FADE IN:", "FADE OUT", "FADE TO BLACK",
    "DISSOLVE TO:", "CUT TO:", "SMASH CUT TO:",
    "MATCH CUT TO:", "JUMP CUT TO:",
    "CUT TO BLACK", "IRIS OUT",
    "THE END",
}

TEMPORAL_CONTINUATION_MARKERS = {
    "LATER", "CONTINUOUS", "MOMENTS LATER",
    "SAME TIME", "SIMULTANEOUS",
}

TIME_OF_DAY_MARKERS = {
    "DAWN", "MORNING", "DAY", "DUSK", "SUNSET",
    "EVENING", "NIGHT", "LATER", "CONTINUOUS",
    "MOMENTS LATER", "SAME TIME",
}

PERIOD_MARKERS = {
    "FLASHBACK", "DREAM", "NIGHTMARE", "FANTASY",
    "MONTAGE", "SEQUENCE", "TITLE",
}

VEHICLE_TERMS = {
    "TAXI", "CAR", "TRUCK", "BUS", "VAN", "SUV",
    "AMBULANCE", "POLICE CAR", "JEEP",
    "BOAT", "SHIP", "SUBMARINE", "PLANE", "HELICOPTER",
    "TRAIN", "SUBWAY", "MIR ONE",
}

CHARACTER_CUE_RE_STR = r"^[A-Z][A-Z0-9 '\-.]+(?:\s*\((?:CONT'D|CONT\u2019D)\))?$"

BACKGROUND_POPULATION_LABELS = {
    "COMMUTERS", "BUSINESSMEN", "CROWD", "CROWDS",
    "EXTRAS", "PEDESTRIANS", "TOURISTS",
    "PASSENGERS", "SHOPPERS",
}

BIT_PART_CHARACTER_NAMES = {
    "BARTENDER", "WAITER", "WAITRESS", "SECURITY GUARD",
    "HOTEL MANAGER", "POLICE OFFICER", "OFFICER", "DRIVER",
}

LOCATION_CLASS_IDS = {
    "interior_single_room": "LC_INTERIOR_SINGLE_ROOM",
    "interior_connected_rooms": "LC_INTERIOR_CONNECTED_ROOMS",
    "interior_corridor_or_stairwell": "LC_INTERIOR_CORRIDOR_OR_STAIRWELL",
    "outdoor_small_area_under_10m": "LC_OUTDOOR_SMALL_AREA_UNDER_10M",
    "outdoor_street_depth_10_20m": "LC_OUTDOOR_STREET_DEPTH_10_20M",
    "outdoor_long_street_over_20m": "LC_OUTDOOR_LONG_STREET_OVER_20M",
    "vehicle_interior": "LC_VEHICLE_INTERIOR",
    "vehicle_on_road_scene": "LC_VEHICLE_ON_ROAD_SCENE",
    "hybrid_or_uncertain": "LC_HYBRID_OR_UNCERTAIN",
    "unknown": "LC_UNKNOWN",
}

