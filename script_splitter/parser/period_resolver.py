"""Period/date inheritance resolver."""

def resolve_effective_periods(scenes: list["SceneRecord"]) -> dict[str, str | None]:
    periods: dict[str, str | None] = {}
    last_period = None
    for scene in sorted(scenes, key=lambda s: s.scene_order):
        sp = scene.heading.date_or_period_raw
        if sp:
            last_period = sp
        periods[scene.scene_id] = last_period
    return periods

