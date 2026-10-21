# Configuring a campaign

All campaign paths below are relative to the private campaign directory. Edit one authoritative owner at a time, then run `audit` and inspect affected preparation. Use a single writer.

## Characters and controllers

Initialization creates one player and one character. Add any number to `players` and `entities`. Entity IDs are stable internal keys; names and aliases are exact identity labels. Do not use a faction, relative, hometown or another person's name as an alias.

```json
{
  "players": [{"name": "Player A", "characters": ["pc-a"]}],
  "entities": {
    "pc-a": {
      "name": "Chosen character name",
      "kind": "character",
      "controller": "player",
      "profile": "pc-a-profile",
      "required": ["pc-a-profile", "corrections"],
      "topics": {"core": [], "development": ["development"]}
    }
  }
}
```

This is a fragment, not a replacement for the whole configuration. Define every referenced ID under `refs`. GM companions use `controller: gm`. List party members and actual scene participants in `records/state.json`; recovery loads their full profiles. Important departed characters remain in `entities` with valid profile/history routes.

## Profiles and history

Keep each profile coherent: identity, voice/habits, background, values, goals, relationships, earned knowledge, independent interests, relevant experience and development. Separate played evidence, interpretation and prospective choices. Use precise accepted-history links where depth matters. Current balances and location remain in state.

For the player-controlled character, record declared background and development without supplying their inner thoughts. Significant companions deserve the same preparation and reward attention as protagonists; no romance or permanent companionship is presumed.

## References and dependencies

```json
{
  "refs": {
    "harbor-adopted": {
      "path": "records/PLACES.md",
      "section": "Harbor",
      "status": "accepted",
      "authority": "campaign",
      "dependencies": [
        {"ref": "harbor-source", "required": true, "why": "Defining location key"},
        {"ref": "tide-rule", "topics": ["travel"], "why": "Controls the crossing window"}
      ]
    },
    "harbor-source": {
      "path": "sources/harbor.html",
      "status": "source",
      "authority": "original"
    },
    "harbor-map": {
      "format": "visual",
      "status": "source",
      "locator": {"provider": "roll20", "page": "YOUR-PAGE-ID"}
    }
  }
}
```

Register the map as a required or relevant-topic dependency where spatial adjudication needs it. Its presence creates a visible inspection gap; it does not make the map geometrically verified. Keep adopted scale/access notes in a separate owner linked to the map and parent region.

Use `section` for an exact Markdown heading, `pointer` for a JSON pointer, or a unique `paragraph_prefix`/`row_prefix`. A source-wide `sha256`, when supplied, must match the raw UTF-8 text. Changing it requires source review, not automatic acceptance. `source-import` computes it for complete captures.

Status values: `accepted`, `source`, `proposed`, or inactive values such as `superseded`. Explicit reads can show proposals with labels; ordinary discovery excludes them. Inactive references cannot be read as current evidence. Add correction references to affected entity routes rather than expecting lexical search to discover every retcon.

Entity `required` selects invariant constraints. `topics` maps topic names to reference lists. `related` lists other entities with reasons; it is not automatic recursion or shared knowledge. `prepare --actor ID` loads that actual participant's full profile, not just a subject-specific fragment.

## Source inventory

Store original adventure/rule sources and approved supplements in the Roll20 game. Inventory handouts, character fields, maps and external dependencies exposed through that game. Import complete original fields through the bridge or manually record authorized UI reads. Do not assume one chapter's index captures all governing events or rules.

Each inventory entry should identify provider/game/object/field or page locator, title, edition, local path if cached, completeness, capture time, hash and adoption status. Keep source edition and supplement overrides explicit. Imported sources start unassessed; attach them to entities and governing owners only after review.

Do not add licensed source files to public repositories. The importer records `redistribute: false`. Original source availability, adopted lore and character knowledge are separate states.

## Operations and calendars

See [WORLD](../gm_framework/templates/procedures/WORLD.md) for an operation example. `next_tick` is an absolute fictional tick, not a duration or Unix time. `before` lists destination/entity IDs or event labels, such as `repair-report`, that need the result. `condition` records predicates the GM must assess. Status and cadence are distinct.

Default time uses minute ticks, a 1440-tick day, and offsets 360/1080. Change `period` and `review_offsets` to fit your calendar. `records/state.json` owns the current tick, last completed broad review (`reviews.through_tick`) and partial phase. Update completed coverage only after executing the required work. Never advance time merely to clear a reminder.

Keep operations compact and close finished work. The complete unfinished queue is returned to avoid losing unindexed dependencies. If it grows large, archive completed outcomes into accepted history and use deliberate actor/region groupings; do not silently drop active duties behind a ranking cutoff.

## Updating an owner

Prepare the full proposed JSON in a separate file. Obtain the SHA-256 of the current UTF-8 owner text. Then:

```sh
campaign-gm --root ../my-private-campaign update operations --from-file proposed-operations.json --expect CURRENT_SHA256
campaign-gm --root ../my-private-campaign attention
campaign-gm --root ../my-private-campaign audit
```

`update` rejects a stale expected hash. It does not infer related edits or validate narrative truth. Apply accepted changes to all affected owners and read back their outputs before resuming. Other record formats can be edited normally under the same single-writer and readback discipline.

## Context reuse

```sh
campaign-gm --root ../my-private-campaign prepare pc --manifest retained.json --assert-retained-context session-7-scene-2
campaign-gm --root ../my-private-campaign prepare pc --reuse retained.json --assert-retained-context session-7-scene-2
```

The first command prints full selected bodies. The second can omit unchanged bodies only because you explicitly assert that the prior evidence remains retained and assessed. Do not use it after context loss or as proof the assistant understood the material. Selection/request/policy changes invalidate reuse. Delete obsolete technical manifests; they are not campaign evidence.
