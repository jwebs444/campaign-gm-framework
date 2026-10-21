"""Original synthetic examples for learning and evaluation, not adventure imports."""
from pathlib import Path

from .bootstrap import initialize, write_json
from .store import read_json


def build_demo(destination, setting="marsh"):
    settings = {
        "marsh": ("Lantern Marsh", "Ari", "Tamsin", "Custom dice-pool fantasy", "wetland exploration", "Mira", "pump house", "water pump"),
        "orbital": ("Quiet Orbit", "Bo", "Nera", "Custom percentile science fiction", "orbital rescue", "Ori", "docking bay", "air recycler"),
    }
    title, player, hero, rules, genre, companion, place, machine = settings[setting]
    root = initialize(destination, title, player, hero, rules, genre)
    config = read_json(root / "campaign.json")
    config["entities"]["ally"] = {"name": companion, "kind": "character", "controller": "gm", "aliases": ["specialist"],
        "profile": "ally-profile", "history": ["accepted-visit"], "required": ["ally-profile", "corrections"],
        "topics": {"core": [], "work": ["work-site"], "relationship": ["accepted-visit"]},
        "related": [{"entity": "pc", "why": "Shared repair expedition; separate knowledge"}]}
    config["entities"]["site"] = {"name": place, "kind": "location", "required": ["work-site"],
        "topics": {"core": [], "repair": ["repair-rule"], "approach": ["site-map"]}}
    config["refs"].update({
        "ally-profile": {"path": "records/CHARACTERS.md", "section": "Specialist"},
        "work-site": {"path": "records/PLACES.md", "section": "Work site", "dependencies": [
            {"ref": "source-site", "required": True, "why": "Defining original location key"},
            {"ref": "regional-context", "required": True, "why": "Parent access and communications"},
            {"ref": "repair-rule", "topics": ["repair", "work"], "why": "Adopted repair constraint"}]},
        "source-site": {"path": "sources/original.md", "section": "Location key", "status": "source", "authority": "original"},
        "repair-rule": {"path": "records/MECHANICS.md", "section": "Repair", "dependencies": [
            {"ref": "supplement", "required": True, "why": "Supplement adapted by this ruling"}]},
        "supplement": {"path": "sources/supplement.md", "status": "source", "authority": "supplement"},
        "regional-context": {"path": "records/PLACES.md", "section": "Region"},
        "site-map": {"format": "visual", "status": "source", "locator": {"provider": "roll20", "page": "SYNTHETIC-NOT-A-LIVE-ID"}},
        "accepted-visit": {"path": "history/ACCEPTED.md", "section": "First visit"},
    })
    for path, text in {
        "records/SCENE.md": f"# Scene preparation\n\n## Current scene\n\nAt the {place}, {hero} and {companion} are discussing the unfinished repair. The specialist awaits a decision about inspecting the test station.\n\n## Commitments\n\nThe player delivered the seal. Remaining fitting, testing and reporting are owned by operation repair; no outcome has been promised as complete.\n\n## Rolling preparation\n\nA test, a conversation with the apprentice, or departure are possible. None is chosen.\n",
        "records/CHARACTERS.md": f"# Characters\n\n## Player character\n\n{hero} is controlled by {player}. Their inner life is not supplied by the GM.\n\n## Specialist\n\n{companion} repairs equipment but also draws unfamiliar birds, keeps letters from a distant sibling, and dislikes waste. Their humor is dry. They prefer evidence to promises but will spend scarce time helping an anxious apprentice.\n\n### Relationships\n\n{hero} kept a promise to bring parts. Trust increased because the delivery cost them a detour; this is not general obedience.\n\n### Knowledge\n\nThey know the old seal leaked. They have not received the test result and cannot report the repair complete.\n\n### Independent development\n\nAfter the apprentice identified a fault they missed, they began asking for observations before giving instructions. This is a supported change in teaching, not a new external event.\n",
        "records/PLACES.md": f"# Places\n\n## Region\n\nMessages require a runner; there is no assumed instant communication.\n\n## Work site\n\nThe {place} contains the {machine}. Access through the maintenance entrance was granted during the accepted first visit. Geometry is not established by this text.\n",
        "records/MECHANICS.md": "# Adopted mechanics\n\n## Repair\n\nA fitted replacement must be pressure-tested before safe operation. The supplement's automatic success rule is not adopted. Use the configured rules for uncertain work.\n",
        "history/ACCEPTED.md": f"# Accepted history\n\n## First visit\n\nAt tick 420, {hero} delivered the promised seal. {companion} said, 'You came back. I kept a place for your tools.' The apprentice helped locate the leak. No repair outcome or test result was established.\n",
        "sources/original.md": f"# Original synthetic source\n\n## Location key\n\nThe {machine} is reached from a maintenance entrance. A supervisor keeps the access ledger. Original example written for this repository; not copied from a published adventure.\n",
        "sources/supplement.md": "# Synthetic supplement\n\nProposed variant: an installed seal always works. The campaign does not adopt this provision; its mechanics owner requires a test.\n",
    }.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    write_json(root / "campaign.json", config)
    state = read_json(root / "records/state.json")
    state.update({"hold": True, "time": {"tick": 480, "label": "First workday, 08:00"}, "party": ["pc", "ally"],
                  "scene": {"location": "site", "participants": ["pc", "ally"], "last_exchange": "The specialist is waiting for the player's next instruction."},
                  "pending_player_input": "Decide whether to inspect the test station", "reviews": {"through_tick": 360, "partial": None}})
    write_json(root / "records/state.json", state)
    write_json(root / "records/operations.json", [{"id": "repair", "actors": ["ally"], "purpose": f"Restore the {machine}",
        "means": "Tools and replacement seal are present", "cadence": "ACTIVE", "status": "in-progress",
        "last_step": "Old seal removed", "next_tick": 540, "before": ["site", "repair-report"],
        "condition": "Resolve actual fitting and testing before a dependent report", "blocker": None,
        "delivery": "Report to the supervisor in person; no result has been sent"}])
    write_json(root / "records/sources.json", [
        {"id": "source-site", "provider": "synthetic", "path": "sources/original.md", "completeness": "complete-example", "adoption": "context only"},
        {"id": "supplement", "provider": "synthetic", "path": "sources/supplement.md", "completeness": "complete-example", "adoption": "modified; see repair-rule"}])
    return root
