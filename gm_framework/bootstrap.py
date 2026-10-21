"""Create a private campaign, without a preselected story or character."""
import json
from pathlib import Path
import shutil


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def initialize(destination, title, player, character, rules, genre):
    root = Path(destination).resolve()
    if root.exists():
        raise ValueError("Destination already exists; initialization never overwrites a campaign")
    root.mkdir(parents=True)
    templates = Path(__file__).with_name("templates")
    for path in templates.rglob("*.md"):
        target = root / path.relative_to(templates)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    owners = {"state": "records/state.json", "operations": "records/operations.json",
              "sources": "records/sources.json", "development": "records/development.json"}
    refs = {
        "checkpoint": {"path": owners["state"]},
        "operations": {"path": owners["operations"]},
        "development": {"path": owners["development"]},
        "foundation": {"path": "FOUNDATION.md"},
        "workflow": {"path": "DM_WORKFLOW.md"},
        "mechanics": {"path": "records/MECHANICS.md"},
        "scene": {"path": "records/SCENE.md"},
        "player-profile": {"path": "records/CHARACTERS.md", "section": "Player character"},
        "corrections": {"path": "records/CORRECTIONS.md"},
        "history": {"path": "history/ACCEPTED.md"},
    }
    config = {"version": 1, "title": title, "rules_system": rules, "genre": genre,
              "players": [{"name": player, "characters": ["pc"]}],
              "source_provider": "roll20", "owners": owners,
              "calendar": {"tick_unit": "minute", "period": 1440, "review_offsets": [360, 1080]},
              "excluded": ["rejected", "evaluations", "handoffs", "receipts"],
              "discovery_paths": ["records/**/*.md", "history/**/*.md", "sources/**/*.html"],
              "checkpoint_ref": "checkpoint", "refs": refs,
              "entities": {"pc": {"name": character, "kind": "character", "controller": "player",
                                  "profile": "player-profile", "required": ["player-profile", "corrections"],
                                  "topics": {"core": [], "development": ["development"], "mechanics": ["mechanics"]}}},
              "recovery": {"context": ["workflow", "foundation", "checkpoint", "scene", "operations", "development", "mechanics", "corrections"],
                           "fresh": ["workflow", "foundation", "checkpoint", "scene", "operations", "development", "mechanics", "corrections", "history"],
                           "review": ["workflow", "foundation", "checkpoint", "scene", "operations", "development", "corrections"]},
              "procedures": {name: {"path": f"procedures/{name.upper()}.md"}
                             for name in ["play", "world", "records", "spatial", "tools", "handoff"]}}
    from .workflow import connect
    connect(config)
    write_json(root / "campaign.json", config)
    write_json(root / owners["state"], {"time": {"tick": 0, "label": "Not started"}, "hold": True,
        "party": ["pc"], "scene": {"location": "Unestablished", "participants": ["pc"], "last_exchange": "Campaign setup pending"},
        "pending_player_input": "Confirm campaign, characters, boundaries, and opening situation", "resources": {}, "effects": [],
        "reviews": {"through_tick": 0, "partial": None}})
    for owner in ["operations", "sources", "development"]:
        write_json(root / owners[owner], [])
    for path, text in {
        "records/CHARACTERS.md": "# Characters\n\n## Player character\n\nIdentity and choices belong to the player. See campaign.json for their name and controller.\n\n### Accepted background\n\nNot established. Do not invent memories or internal commitments.\n\n### Relationships and development\n\nNot established. Record player-declared changes here.\n",
        "records/MECHANICS.md": "# Adopted mechanics\n\nVerify the configured rules and actual character sheets before adjudicating. No homebrew or edition is presumed.\n",
        "records/SCENE.md": "# Scene preparation\n\n## Current scene\n\nNo opening scene is adopted. Establish actual participants, individual stakes, access, knowledge, pending exchanges, and relevant opportunities.\n\n## Commitments\n\nNo accepted commitments yet. Preserve unpromoted promises here with speaker, recipient, terms, and actual next opportunity; promote consequential work into operations without duplicating its status.\n\n## Rolling preparation\n\nPrepare the current scene and a few plausible next scenes, including source events, parent routes, and choices. Do not choose the players' itinerary.\n",
        "records/CORRECTIONS.md": "# Accepted correction index\n\nNo corrections. Add compact affected-owner pointers and accepted replacements; rejected scene text stays outside ordinary retrieval.\n",
        "history/ACCEPTED.md": "# Accepted history\n\nNo play has occurred. Keep meaningful dialogue and emotional moments here once, linked from relevant owners.\n",
        ".gitignore": "# This is private campaign data, not a public framework checkout.\n*\n!.gitignore\n",
    }.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return root
