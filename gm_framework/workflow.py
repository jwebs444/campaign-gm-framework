"""Default retrieval connections for the existing workflow, not a second task queue."""

PHASES = ("orientation", "preparation", "world", "cleanup", "scene")
ACTIVITIES = ("arrival", "transition", "rest", "downtime", "resolution", "scene-close", "strategy", "combat")


def connect(config):
    """Add missing portable defaults. Never overwrite campaign-specific selections."""
    refs = config["refs"]
    defaults = {
        "commitments": {"path": "records/SCENE.md", "section": "Commitments"},
        "play-context": {"path": "procedures/PLAY.md", "section": "Scene and character refresh"},
        "play-development": {"path": "procedures/PLAY.md", "section": "Significant NPC inner development"},
        "play-rest": {"path": "procedures/PLAY.md", "section": "Companion preparation after rests"},
        "world-review": {"path": "procedures/WORLD.md", "section": "Broad review and rewards"},
        "world-catalogue": {"path": "procedures/WORLD.md", "section": "Recurring preparation catalogue"},
        "world-strategy": {"path": "procedures/WORLD.md", "section": "Important actor decisions"},
        "world-events": {"path": "procedures/WORLD.md", "section": "Source events and opportunities"},
        "world-work": {"path": "procedures/WORLD.md", "section": "Operations and checkpoints"},
        "records-cleanup": {"path": "procedures/RECORDS.md", "section": "Scheduled cleanup"},
        "records-integration": {"path": "procedures/RECORDS.md", "section": "Integrating a change"},
        "records-corrections": {"path": "procedures/RECORDS.md", "section": "Canon corrections"},
        "spatial-encounter": {"path": "procedures/SPATIAL.md", "section": "Combat and extended approaches"},
    }
    for key, ref in defaults.items():
        refs.setdefault(key, dict(ref, authority="campaign" if key == "commitments" else "procedure"))
    cleanup = refs["records-cleanup"]
    if cleanup.get("path") == defaults["records-cleanup"]["path"] and cleanup.get("section") == "Scheduled cleanup":
        dependencies = cleanup.setdefault("dependencies", [])
        if not any(d["ref"] == "records-integration" for d in dependencies):
            dependencies.append({"ref": "records-integration", "required": True,
                                 "why": "Integrate changed topics and repair selectors before disposing of scaffolding"})
    config.setdefault("scene_ref", "scene")
    config.setdefault("commitments_ref", "commitments")
    config.setdefault("review_actors", [])
    config.setdefault("focused_refresh", {})
    phases = config.setdefault("review_phases", {})
    for name, selected in {
        "orientation": ["foundation", "checkpoint", "scene", "corrections"],
        "preparation": ["checkpoint", "scene", "development", "commitments", "world-review", "world-catalogue", "world-events", "play-development"],
        "world": ["checkpoint", "operations", "commitments", "world-work", "world-strategy", "world-events"],
        "cleanup": ["checkpoint", "operations", "development", "corrections", "records-cleanup", "records-corrections"],
        "scene": ["checkpoint", "scene", "play-context"],
    }.items():
        phases.setdefault(name, selected)
    activities = config.setdefault("activities", {})
    for name, selected in {
        "arrival": ["scene", "commitments", "play-context", "world-work"],
        "transition": ["scene", "commitments", "world-work"],
        "rest": ["mechanics", "development", "commitments", "play-rest"],
        "downtime": ["development", "commitments", "world-work"],
        "resolution": ["development", "commitments", "play-development", "world-review", "world-events"],
        "scene-close": ["development", "commitments", "play-development", "world-review", "world-events", "records-cleanup"],
        "strategy": ["world-strategy", "world-events"],
        "combat": ["mechanics", "spatial-encounter"],
    }.items():
        activities.setdefault(name, selected)
    for mode in ["context", "fresh"]:
        for ref in ["commitments"]:
            if ref not in config["recovery"][mode]:
                config["recovery"][mode].append(ref)
    config["recovery"].setdefault("scene", ["checkpoint", "scene"])
    config["workflow_revision"] = 3
    return config
