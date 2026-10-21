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

For a new character scaffold, use `add-character envoy --name "The envoy" --controller gm --source-ref envoy-original --history-ref accepted-meeting` after registering those references. Source/history flags are optional and repeatable. A player character also needs `--player "Player name"`. The helper creates routes and clearly marked prompts; it establishes no biography, knowledge, arrival or party membership. Fill the profile before portraying the character.

## Profiles and history

Keep each profile coherent: identity, voice/habits, background, values, goals, relationships, earned knowledge, independent interests, relevant experience and development. Separate played evidence, interpretation and prospective choices. Use precise accepted-history links where depth matters. Current balances and location remain in state.

For the player-controlled character, record declared background and development without supplying their inner thoughts. Significant companions deserve the same preparation and reward attention as protagonists; no romance or permanent companionship is presumed.

An entity can use `profile_refs: ["voice", "relationships", "independent-development"]` for a profile split across owners, `history: ["accepted-meeting", "accepted-disagreement"]` for causal anchors, or both alongside `profile`. Normal character preparation and recovery join these with required constraints. These are curated relevant anchors, not a requirement to replay every conversation. A minor character may use `importance: "minor"` and nonempty `history` without a full profile. Significant characters require a profile. Keep departed characters registered; current presence belongs only in state.

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

Use `section` for an exact Markdown heading, `pointer` for a JSON pointer, or a unique `paragraph_prefix`/`row_prefix`. `include_children: false` stops a heading selection at its first child. `start` and optional `end` are unique literal boundaries for source keys that are not headings; start is included, end excluded. `view: "text"` derives readable text from HTML without changing the complete raw capture. A source-wide `sha256`, when supplied, must match the raw UTF-8 text. Changing it requires source review, not automatic acceptance. `source-import` computes it for complete captures.

Status values: `accepted`, `source`, `proposed`, or inactive values such as `superseded`. Explicit reads can show proposals with labels; ordinary discovery excludes them. Inactive references cannot be read as current evidence. A broad accepted read containing a registered inactive/proposed child fails, and fallback discovery withholds that file. Clean or narrow the owner rather than removing its status marker. Add correction references to affected entity routes instead of expecting lexical search to discover every retcon.

Entity `required` selects invariant constraints. `topics` maps topic names to reference lists. `related` lists other entities with reasons; it is not automatic recursion or shared knowledge. `prepare --actor ID` loads that actual participant's full profile, not just a subject-specific fragment.

## Source inventory

Store original adventure/rule sources and approved supplements in the Roll20 game. Inventory handouts, character fields, maps and external dependencies exposed through that game. Import complete original fields through the bridge or manually record authorized UI reads. Do not assume one chapter's index captures all governing events or rules.

Each inventory entry should identify provider/game/object/field or page locator, title, edition, local path if cached, completeness, capture time, hash and adoption status. Keep source edition and supplement overrides explicit. Imported sources start unassessed; attach them to entities and governing owners only after review.

Do not add licensed source files to public repositories. The importer records `redistribute: false`. Original source availability, adopted lore and character knowledge are separate states.

Inspect inventory and declared links with `sources` or `sources ENTITY`, then use `read SOURCE --view text --section "Exact heading"` or `--start "Unique key" --end "Next unique key"`. Connect reviewed retrieval units with:

```sh
campaign-gm --root ../my-private-campaign source-link chapter --entity harbor --topic travel --section "Harbor" --ref-id harbor-key
```

Use `--required` for defining constraints needed across topics. This links retrieval only; record adoption and overrides separately. `catalog` lists identities and selectors, and `topics ENTITY` lists topic routes. Source menus follow all declared topic/dependency branches but cannot discover an unrecorded governing passage elsewhere in an adventure. Read the inventory and relevant full sources when building those routes.

## Activity, review and focused refresh connections

New campaigns include `activities` and `review_phases` mappings in `campaign.json`. They select existing owners/procedure sections, not duplicate task records. Use `prepare pc --activity rest`, `prepare harbor --topic travel --activity transition --destination harbor --until 700`, or the other documented activity names. Focused preparation shows related/due operations; transition/arrival/time-horizon calls show the whole unfinished queue. Keep operation `actors`, `entities`, `before`, optional `topics`/`activities`, and governing `refs` explicit. Unpromoted promises remain in `records/SCENE.md` under Commitments.

Run `recover --mode review --phase orientation`, then preparation, world, cleanup and scene as their work completes. Configure `review_actors` with independent major actors, including unencountered source-active strategists. World recovery also joins unfinished operation actors and `refs`. `recover --mode scene` restores the pending scene after an interruption. `--reuse-procedures` is allowed only for review/scene when the operating instructions remain retained.

For a repeated narrow topic, an optional configuration is:

```json
{
  "focused_refresh": {
    "repair-status": {
      "entities": ["harbor"],
      "topics": ["repair"],
      "refs": ["repair-current"],
      "why": "Refresh the changed repair status with the full site context retained"
    }
  }
}
```

Call `prepare harbor --topic repair --refresh repair-status --assert-retained-context session-7`. Add `invariants` to the entity for qualifiers that must accompany every refresh; by default corrections are retained. Include defining source/override constraints if the refreshed fact depends on them. Explicit `--actor` participants still get full profile/history. A refresh must never substitute for fresh recovery or erase contrary evidence.

## Operations and calendars

See [WORLD](../gm_framework/templates/procedures/WORLD.md) for an operation example. `next_tick` is an absolute fictional tick, not a duration or Unix time. `before` lists destination/entity IDs or event labels, such as `repair-report`, that need the result. `condition` records predicates the GM must assess. Status and cadence are distinct.

Default time uses minute ticks, a 1440-tick day, and offsets 360/1080. Change `period` and `review_offsets` to fit your calendar. `records/state.json` owns the current tick, last completed broad review (`reviews.through_tick`) and partial phase. Update completed coverage only after executing the required work. Never advance time merely to clear a reminder.

Keep operations compact and close finished work. Unfiltered `attention` and transition preparation return the complete unfinished queue to avoid losing unindexed dependencies. If it grows large, archive completed outcomes into accepted history and use deliberate actor/region groupings; do not silently drop active duties behind a ranking cutoff.

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
campaign-gm --root ../my-private-campaign prepare pc --manifest retained.json --assert-retained-context session-7-scene-2 --assert-invalidation "Premises, knowledge, sources and corrections checked"
campaign-gm --root ../my-private-campaign prepare pc --reuse retained.json --assert-retained-context session-7-scene-2 --assert-invalidation "Premises, knowledge, sources and corrections checked"
```

The first command prints full selected bodies. The second can omit unchanged bodies only because you explicitly assert retained context and review of semantic changes. Both assertion strings must match. Do not use this after context loss or as proof the assistant understood the material. Selection/request/policy, checkpoint or accepted-discovery metadata changes invalidate reuse. `--part` can be repeated; manifests require full output rather than a partial read or a menu. Delete obsolete technical manifests; they are not campaign evidence.

## Upgrade an existing v0.1 campaign

Install the new package, keep play on HOLD and run `upgrade` to preview, then `upgrade --apply`. The upgrader replaces only unchanged recognized framework templates, connects missing default routes, and adds a Commitments heading if absent. It does not alter state, resources, history or outcomes. If any affected template was customized, it reports conflicts and applies nothing. Merge those templates manually with the published versions, preserving adopted campaign choices, then rerun. Back up private owners under your normal private backup policy first. Finish with `audit` and affected recovery readback; structural success does not fill missing character/source facts.
