# Roll20 GM Control

`GMControl.js` is the generalized inspection bridge. It is optional: authorized manual/browser source inspection can populate the same campaign records.

## Requirements and scope

The game must have Mod/API access; the game creator's Pro subscription enables that feature. See [Roll20's access documentation](https://help.roll20.net/hc/en-us/articles/29620515876375-Invite-Promote-and-Manage-Players). Only GM-issued API chat commands are accepted.

The bridge uses supported sandbox objects. Handout `notes`/`gmnotes` and character `bio`/`gmnotes` are read through callbacks, as required by [Roll20's object documentation](https://help.roll20.net/hc/en-us/articles/360037772793-Mod-Scripts-Objects). This does not grant general Compendium or Marketplace access. Inspect non-exposed sources in the authorized UI; retain provenance and exact coverage manually.

Local mock tests cover the bridge behavior. This generic release has not been installed in a fresh live Roll20 game as part of publication. Verify capability in your game before relying on it. Isolated cloning requires the sandbox's supported `createCopy` method; ordinary reads do not require cloning.

## Install

1. Open the intended game's Mod/API script editor as an authorized GM.
2. Add a script containing `GMControl.js`, then save it.
3. Run this command in that game's chat:

```text
!gmctl {"op":"ping","request":"setup-check"}
```

Confirm version 1.1.0 and the reported mode. The bridge has its own state namespace and does not migrate a different installed script's state. Do not install multiple copies. The script does not start playback or change live resources at startup.

## Source inventory and reads

```text
!gmctl {"op":"list","type":"handout","offset":0,"limit":40,"request":"source-list"}
!gmctl {"op":"list","type":"page","offset":0,"limit":40,"request":"map-list"}
!gmctl {"op":"source","type":"handout","id":"HANDOUT_ID","field":"gmnotes","view":"raw","offset":0,"limit":12000,"request":"source-part-1"}
```

Use actual IDs returned by your game. Follow every `next` offset until it is null. Offsets are JavaScript UTF-16 units; use the exact returned value. Read `notes` separately when the handout contains relevant material there. Source fields from characters use `type: character` and `field: bio` or `gmnotes`.

The Mod writes complete machine-readable `GMCTL_RECEIPT` JSON to the private API console and escaped paginated previews to GM chat. Save the JSON envelopes for all source slices into a private local JSON array. Do not copy only the first preview page or treat `unchanged` as source text. Receipt previews are transient; the console/local capture is not automatic filesystem synchronization.

```json
[
  {
    "version": "1.1.0",
    "op": "source",
    "result": {
      "id": "SYNTHETIC",
      "field": "gmnotes",
      "view": "raw",
      "fingerprint": "4:example",
      "rawLength": 4,
      "total": 4,
      "offset": 0,
      "next": null,
      "text": "Test"
    }
  }
]
```

This is a synthetic format example, not a receipt from a game. Import your real complete captures:

```sh
campaign-gm --root ../my-private-campaign source-import --receipts source-parts.json --id harbor-source --title "Harbor key" --game YOUR_GAME_ID --type handout --edition "Your edition" --authority original
campaign-gm --root ../my-private-campaign sources
campaign-gm --root ../my-private-campaign read harbor-source
```

The importer checks identity, view, fingerprint consistency, gap-free slices, continuation offsets and total length, including split Unicode surrogate pairs. It stores original raw text and a SHA-256. The bridge fingerprint is only a noncryptographic cache hint. Complete-field coverage does not mean complete adventure coverage or source adoption.

Register maps as visual dependencies. A page's dimensions or token list cannot establish walls, exits, elevations or visibility without inspecting its actual map and key.

## Character and scene reads

```text
!gmctl {"op":"character","id":"CHARACTER_ID","names":["YOUR_ATTRIBUTE","ANOTHER_ATTRIBUTE"],"request":"sheet-read"}
!gmctl {"op":"character","id":"CHARACTER_ID","all":true,"offset":0,"limit":100,"request":"sheet-inventory"}
!gmctl {"op":"scene","page":"PAGE_ID","layers":["objects"],"offset":0,"limit":40,"request":"scene-read"}
!gmctl {"op":"token","id":"TOKEN_ID","fields":["name","left","top","layer"],"request":"token-read"}
```

Attribute defaults are intentionally empty. Use exact sheet-specific names, `all`, or `filter`, and follow pagination. A displayed default/formula is explicitly marked and needs interpretation. No D&D classes, slots, rest rules or resource semantics are built in.

The `batch` operation accepts one to five independent read operations; it cannot contain writes or nested batches. Use `help` to inspect supported operation names. Private output can include secrets; do not publish it or copy it into player-facing narration.

## Isolated test copies

Live token/attribute editing is disabled. The optional lab lets developers verify supported edits on registered private copies only.

1. Create a private page named exactly `GM Framework Lab` that no player is viewing or assigned to.
2. Register its ID with `{"op":"lab","page":"LAB_PAGE_ID"}`.
3. Clone a token with `{"op":"clone","id":"TOKEN_ID","names":["ATTRIBUTE_TO_COPY"],"request":"clone-unique"}`.
4. Inspect the returned test IDs. Use `preview` with exact `expect` values before `edit`, then independently read back.
5. Use `undo` only when the fields still match the verified transaction. Intervening changes cause refusal.

Prefix each JSON command with `!gmctl `. Requests must have fresh unique labels. No live links are copied into test bars. The page cannot become the current player page or an assigned split-party page. Do not use this mechanism to synchronize live campaign maps.

The lab is for narrow field behavior, not full character-sheet worker rollback. The bridge intentionally retains no general-purpose live-edit switch.

## Optional music

`music-status` returns track flags and defined cue metadata. It is not proof of audible playback. Define a cue using actual existing track IDs, volume and a unique request. Preview a `start`, `next` or `stop` action before applying it. An applied action requires the current fingerprint, a fresh request and `exclusiveReady: true` after native playlists have been stopped in the UI.

```text
!gmctl {"op":"music-status","request":"music-read"}
!gmctl {"op":"music","action":"define","cue":"quiet","tracks":["TRACK_ID"],"volume":30,"request":"define-quiet"}
!gmctl {"op":"music","action":"start","cue":"quiet","preview":true,"request":"preview-quiet"}
```

Use the preview's expected fingerprint when applying. Never claim audition from metadata. Cues do not advance automatically and do not advance fictional time. Only change playback when authorized by the group.

## Security and support

The bridge makes no HTTP calls, reads no local files, and contains no credentials. Its source/text outputs are escaped to prevent accidental chat commands or public multiline output. It checks GM identity before handling requests. It does not execute handout text as code.

Run `node roll20/GMControl.test.cjs` to test supported behavior with synthetic objects. If a live game differs, report the operation and redacted error. Do not attach private receipts, paid source text, game IDs, player data, or access tokens to public issues.
