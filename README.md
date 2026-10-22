# Campaign GM Framework

A reusable, model-independent framework for running a persistent tabletop campaign with an AI-assisted GM and source material in Roll20.

The package combines GM operating instructions, focused evidence retrieval, character and world-state templates, a source importer, and an optional Roll20 inspection Mod. **It is a workflow and toolset, not a trained model, adventure, rules engine, or autonomous game server.** Bring your preferred assistant with local file/command tools and authorized Roll20 browser access.

No player, protagonist, companion, setting, rules edition, character-sheet schema, genre, or ending is built into the engine. You can configure multiple human players, player characters, and independent companions. The examples are original synthetic fiction.

## What it does

- Keeps facts in authoritative owners rather than competing summaries.
- Retrieves complete relevant sections, full participant profiles, and required source dependencies.
- Distinguishes original sources, adopted canon, proposals, character knowledge, and accepted history.
- Surfaces due work before dependent arrivals and decisions, as well as configurable morning/evening reviews.
- Preserves character depth, individual agency, meaningful dialogue, and NPC development.
- Supports correction impact checks, accepted-record discovery, scoped byte reuse, and guarded owner updates.
- Reads supported Roll20 handouts, character fields, maps' object metadata, and sheet attributes through an optional GM-only Mod.
- Keeps actual world decisions, source interpretation, visual inspection, and narration with the GM.

## Quick start

Requirements: Python 3.10+ for local tools. Node.js is needed only to run the bridge's local tests. There are no Python runtime dependencies, model API keys, or cloud database requirements.

```sh
git clone https://github.com/jwebs444/campaign-gm-framework.git
cd campaign-gm-framework
python -m pip install .

campaign-gm init ../my-private-campaign --title "Your campaign" --player "Your name" --character "Your character" --rules "Your system and edition" --genre "Your chosen genre"
campaign-gm --root ../my-private-campaign audit
campaign-gm --root ../my-private-campaign recover --mode fresh --list-parts
campaign-gm --root ../my-private-campaign recover --mode fresh --part 1
```

Read all required recovery parts, not only part 1. Initialization starts on HOLD with source intake incomplete. It does not invent an opening adventure. `python -m gm_framework` works in place of `campaign-gm` from a checkout or installed environment.

1. Open the private campaign directory in your assistant's workspace. Have it read the generated `AGENTS.md` and complete recovery.
2. Complete `FOUNDATION.md`, verify the rules and sheets, and add the actual cast. See [configuration](docs/CONFIGURATION.md).
3. Inventory your Roll20 sources, inspect the relevant material, and connect original keys/maps and adopted overrides. See [Roll20 setup](roll20/README.md).
4. Establish the actual opening boundary with the players, then remove HOLD deliberately. Use [the operating workflow](gm_framework/templates/DM_WORKFLOW.md).

The generated `.gitignore` excludes the private campaign by default. Do not put licensed sources or private play records into this public repository. This repository's MIT license covers its code and original documentation, **not** a publisher's adventure or your players' data.

## Try it without a live game

```sh
campaign-gm demo ../marsh-demo --setting marsh
campaign-gm demo ../orbital-demo --setting orbital
campaign-gm --root ../marsh-demo prepare specialist --topic work --actor specialist --destination site --until 500
campaign-gm --root ../orbital-demo prepare site --topic repair
campaign-gm --root ../orbital-demo attention --until 1100
campaign-gm --root ../orbital-demo discover "promise"
```

These examples use different characters, genres, and nominal rules systems. They illustrate retrieval and duties; neither supplies a playable ruleset. A map dependency intentionally remains unresolved until visual inspection. An unfinished repair is due before a return even when its nominal deadline is later. Source text proposing automatic success does not override the adopted requirement to test it.

## Documentation

| Read this | For |
|---|---|
| [Operating workflow](gm_framework/templates/DM_WORKFLOW.md) | Each response, recovery, time and review phases |
| [Architecture](docs/ARCHITECTURE.md) | Owners, selectors, dependency selection, discovery and reuse |
| [Configuration](docs/CONFIGURATION.md) | Add characters, topics, source links, operations and calendars |
| [Optional rulings](docs/OPTIONAL_RULINGS.md) | Reusable table variants; none are applied by default |
| [Roll20 bridge](roll20/README.md) | Install, inspect, capture sources, limits and permissions |
| [Evaluation guide](docs/EVALUATION.md) | Test real outcomes and unfamiliar questions |
| [Export coverage](docs/EXPORT_COVERAGE.md) | What was generalized, retained, replaced or intentionally excluded |
| [Parity audit](docs/PARITY_AUDIT.md) | Losses found in the initial export, restored capabilities and remaining limits |
| [Contributing](CONTRIBUTING.md) | Changes, tests, privacy and issue reports |

The campaign procedures cover [portrayal](gm_framework/templates/procedures/PLAY.md), [living world](gm_framework/templates/procedures/WORLD.md), [records](gm_framework/templates/procedures/RECORDS.md), [space and encounters](gm_framework/templates/procedures/SPATIAL.md), [tools](gm_framework/templates/procedures/TOOLS.md), and [handoffs](gm_framework/templates/procedures/HANDOFF.md). They are triggered detail, not six extra checklists for every turn.

Existing v0.1 or v0.2 campaigns: install the new version, preview `campaign-gm --root PATH upgrade`, then use `upgrade --apply` if no customized-template conflict is reported. See the [upgrade procedure](docs/CONFIGURATION.md#upgrade-an-existing-v01-campaign). v0.3 adds coherent topic integration, source refresh in place, stronger obsolete-record and source-discovery boundaries, and publication scanning of staged files and reachable history. It preserves v0.2's activity triggers, review phases and causal-history joins.

## Roll20 and model limitations

The optional Mod requires a game with Roll20 Mod/API access and a GM account. [Roll20 documents that access and the creator's Pro requirement](https://help.roll20.net/hc/en-us/articles/29620515876375-Invite-Promote-and-Manage-Players). Without it, use authorized manual/browser source inspection and the same local evidence model.

The bridge reads supported sandbox objects. It does not provide blanket access to every Compendium entry, Marketplace asset, dynamic sheet field, or browser view. Maps still need visual inspection. Each new game needs source mapping and rule verification; storing an adventure in Roll20 does not automatically index or adjudicate it.

No live game writes, automated turns, background fictional simulation, scheduled model calls, or credentials are bundled. Test-copy writes and optional manual music cues are explicitly bounded. Different assistants may follow the workflow differently; structural tests cannot guarantee good characterization or continuity.

## Validation

```sh
python -m unittest discover -s tests -v
node roll20/GMControl.test.cjs
python tools/check_distribution.py
```

Before publishing an export, also run `python tools/check_distribution.py --staged --history --private-terms /outside-repository/private-terms.txt`. Supply a private UTF-8 list of names and distinctive phrases, one per line. Keep that list outside the public repository. This checks the full Git index and locally reachable historical blobs; fetch intended remote refs first. Review the actual content too: literal matches cannot certify that paraphrased personal lore is absent. Historical matches require an explicit history-cleanup decision; deleting a current file does not remove old commits.

The release includes focused regression tests and synthetic examples. CI runs Python 3.10/3.13 on Linux and Windows. See the evaluation guide for the distinction between verified code behavior and unverified live-game or model performance.

MIT licensed. Roll20 is a separate service; this project is not affiliated with or endorsed by Roll20.
