# Rules Database — Authoring Guide

Rules live in `rules/rules.yaml`. This file is loaded at runtime and requires
no code changes to add or modify rules.

## Quick Start

### Add a new location class
```yaml
location_classes:
  - class_id: "LC_MY_NEW_CLASS"
    class_name: "my new class name"
    generation_class: "my_new_class"
    supports_background_panorama: false
    requires_background_panorama: false
    requires_human_review: false
```

### Add a heading matcher to trigger it
```yaml
location_matchers:
  - rule_id: "LOC_MY_NEW_RULE"
    priority: 75
    int_ext: "INT"
    keywords_any:
      - KEYWORD1; KEYWORD2
    result_class: "LC_MY_NEW_CLASS"
    confidence: 0.85
```

### Add a visual element pattern
```yaml
visual_element_patterns:
  - id: "VE_PROP_MY_ITEM"
    type: "container"         # must match one of the valid types
    description: "describe the item"
    trigger_words:
      - keyword1; keyword2
    interaction_verbs:
      - verb1; verb2; verb3
```

## Match Logic

### Location matchers
- Rules are checked in **priority order** (highest first)
- First matching rule wins
- `int_ext` must match exactly (INT / EXT / BOTH)
- `keywords_any`: if ANY keyword appears in the heading → match
- `has_dot_or_slash`: heading contains `.` or `/` (for connected rooms)
- If no rule matches → `LC_UNKNOWN`

### Visual element patterns
- `trigger_words`: matched against action text lines
- If a trigger word is found → `SceneVisualElement` created
- `interaction_verbs`: if character performs this verb on the element → `ScenePropInteraction` created

## Valid Element Types
- `weapon_or_dangerous_object`
- `symbolic_object`
- `clothing_detail`
- `container`
- `communication_device`
- `document`
- `food_or_drink`
- `furniture`
- `equipment_mount`
- `carrier_gear`
