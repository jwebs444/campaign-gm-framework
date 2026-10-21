"""Explicit setup and maintenance helpers; no fictional outcomes are generated."""
import json
from pathlib import Path
import re

from .bootstrap import write_json
from .store import Campaign, digest, read_json, section
from .workflow import connect


def identifier(value):
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,70}", value):
        raise ValueError("ID must use lowercase letters, digits and hyphens")
    return value


def add_character(root, key, name, controller="gm", importance="significant", player=None, sources=(), history=()):
    identifier(key)
    c = Campaign(root)
    identities = {label.casefold() for entity_id, e in c.entities.items()
                  for label in [entity_id, e["name"], *e.get("aliases", [])]}
    if key.casefold() in identities or name.casefold() in identities:
        raise ValueError("Character identity already exists; edit its owner instead")
    if not name.strip() or "\n" in name or "\r" in name:
        raise ValueError("Character name must be a nonempty single line")
    if controller == "player" and not player:
        raise ValueError("Player-controlled characters need --player")
    for ref in [*sources, *history]:
        c.read(ref)
    ref_id = key + "-profile"
    path = f"records/characters/{key}.md"
    if ref_id in c.refs or c.path(path).exists():
        raise ValueError("Profile path/reference already exists")
    body = f"# Character profile\n\nIdentity: {name}\nController: {controller}\n\n"
    body += "This is an unfilled profile scaffold, not established biography. Replace prompts with supported characterization before portrayal.\n\n"
    for heading, prompt in [
        ("Identity and voice", "Enduring identity, background, habits, manner of speaking, values and contradictions."),
        ("Relationships and independent life", "Individual relationships with other people, obligations, family, independent interests and projects; not just a relationship to the protagonist."),
        ("Knowledge and beliefs", "Observed facts, received testimony and its source, inference, suspicion, uncertainty and things not known. No shared group omniscience."),
        ("Present pressures", "Current goals, competing emotions, commitments and constraints. Current position/resources remain checkpoint-owned."),
        ("Causal development", "Experienced event and locator -> prior outlook/meaning -> supported present change or tension -> behavioral implication -> evidence that could reinforce or challenge it. Separate expressed evidence, GM interpretation and prospective behavior."),
        ("Accepted history anchors", "Precise accepted-scene references for formative and recent experiences, including contrary influences and meaningful small moments. Register them in this entity's history links."),
        ("Source portrayal and unresolved gaps", "Defining source/home chapter/faction links, adopted overrides, and genuinely unestablished details. Missing reading is not character ignorance."),
    ]:
        body += f"## {heading}\n\n{prompt}\n\n"
    c.path(path).parent.mkdir(parents=True, exist_ok=True)
    c.path(path).write_text(body, encoding="utf-8")
    c.refs[ref_id] = {"path": path, "dependencies": [{"ref": r, "required": True, "why": "Defining source portrayal"} for r in sources]}
    c.entities[key] = {"name": name, "kind": "character", "controller": controller, "importance": importance,
        "profile": ref_id, "history": list(history), "required": [ref_id, "corrections"],
        "topics": {"core": [], "relationship": list(history), "development": ["development"], "strategy": []}}
    if controller == "player":
        matches = [p for p in c.config["players"] if p["name"] == player]
        if not matches:
            c.config["players"].append({"name": player, "characters": [key]})
        else:
            matches[0]["characters"].append(key)
    write_json(c.root / "campaign.json", c.config)
    return {"entity": key, "profile": path, "notice": "Profile scaffold created. No character arrival, knowledge, party membership, or fictional event established."}


def link_source(root, source_id, entity, topic="core", heading=None, key=None, required=False, start=None, end=None):
    c = Campaign(root)
    entity = c.resolve(entity)
    ref = c.refs[source_id]
    if ref.get("status") != "source":
        raise ValueError("Use a registered original/supplement source reference")
    target = source_id
    if heading and start:
        raise ValueError("Use an exact heading or literal boundaries, not both")
    if end is not None and start is None:
        raise ValueError("An end marker requires a start marker")
    if heading or start:
        if not key:
            raise ValueError("A section link needs --ref-id")
        identifier(key)
        if key in c.refs:
            raise ValueError("Reference ID already exists")
        target = key
        c.refs[key] = dict(ref, view="text")
        if heading:
            c.refs[key]["section"] = heading
        else:
            c.refs[key].update({"start": start, "end": end})
        c.read(key)  # Exact complete section and source hash must validate first.
    else:
        if ref.get("format") != "visual":
            c.read(target)
    selected = c.entities[entity].setdefault("required", []) if required else c.entities[entity]["topics"].setdefault(topic, [])
    if target not in selected:
        selected.append(target)
    write_json(c.root / "campaign.json", c.config)
    return {"ref": target, "entity": entity, "topic": topic, "required": required,
            "notice": "Retrieval link only; no source adoption or character knowledge established."}


def upgrade(root, apply=False):
    c = Campaign(root)
    templates = Path(__file__).with_name("templates")
    legacy = read_json(Path(__file__).with_name("legacy_templates.json"))
    changes, conflicts = [], []
    for path in sorted(templates.rglob("*.md")):
        relative = path.relative_to(templates).as_posix()
        destination = c.path(relative)
        new = path.read_text(encoding="utf-8")
        old = destination.read_text(encoding="utf-8") if destination.exists() else ""
        if old == new:
            continue
        if old and digest(old) not in legacy.get(relative, []):
            conflicts.append(relative)
        else:
            changes.append((relative, new))
    if conflicts:
        return {"applied": False, "conflicts": conflicts,
                "notice": "Customized templates preserved. Merge the published procedures into these owners, then rerun; no partial upgrade performed."}
    config = connect(c.config)
    commitment_ref = c.refs[config["commitments_ref"]]
    scene_path, scene = None, None
    if commitment_ref.get("path") == "records/SCENE.md" and commitment_ref.get("section") == "Commitments":
        scene_path = c.path(commitment_ref["path"])
        scene = scene_path.read_text(encoding="utf-8")
        if not re.search(r"(?m)^## Commitments\s*$", scene):
            scene += "\n\n## Commitments\n\nReview accepted promises not yet promoted to operations; no new commitments inferred by upgrade.\n"
    else:
        try:
            c.read(config["commitments_ref"])
        except (ValueError, KeyError, OSError) as exc:
            return {"applied": False, "conflicts": [config["commitments_ref"]],
                    "notice": f"Custom commitment owner needs reconciliation; no partial upgrade performed: {exc}"}
    if apply:
        for relative, body in changes:
            c.path(relative).parent.mkdir(parents=True, exist_ok=True)
            c.path(relative).write_text(body, encoding="utf-8")
        if scene_path is not None:
            scene_path.write_text(scene, encoding="utf-8")
        write_json(c.root / "campaign.json", config)
    return {"applied": apply, "workflow_revision": 2, "templates": [p for p, _ in changes],
            "notice": "Configuration/procedure upgrade only. No time, resources, history, or scene outcomes changed. Use --apply after reviewing this preview."}
