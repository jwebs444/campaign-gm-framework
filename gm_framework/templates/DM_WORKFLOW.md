# GM operating workflow

This is the operating core. `procedures/` contains triggered detail, not additional recurring checklists. The CLI selects evidence and surfaces duties; the GM performs the interpretation, adjudication, narration, and record updates.

## Authority and owners

Apply authority within the player's actual control: explicit player decisions and adopted corrections, then accepted canon/rulings, then adopted supplements, then compatible original adventure/rules. A player's stated intention does not automatically succeed. A higher-authority change invalidates dependent preparation; it does not erase unrelated accepted history.

`campaign.json` configures identities, owners, retrieval references, source dependencies, and review times. It does not duplicate story facts. Default owners:

| Owner | What it owns |
|---|---|
| `records/state.json` | Current time, exact scene boundary, HOLD, resources, effects, party, pending player input, review coverage |
| `records/CHARACTERS.md` | Full character profiles, relationships, earned knowledge, experience and inner development |
| `records/SCENE.md` | Current working preparation: individual and group stakes, access, opportunities, next plausible scenes |
| `records/operations.json` | Commitments, projects, reports, actor plans, last resolved step, next trigger, blockers and delivery |
| `records/development.json` | Personalized opportunities, practice, credited achievements, rewards, unresolved build choices |
| `records/MECHANICS.md` | Adopted rules and interpretations |
| `history/ACCEPTED.md` | Detailed accepted events and meaningful dialogue, recorded once |
| `records/CORRECTIONS.md` | Accepted correction pointers and affected owners; no rejected scene replay |
| `records/sources.json` | Source provenance, availability, completeness, edition and adoption status |

Split large owners into coherent sections or files when useful. Update their references instead of adding rival CURRENT summaries. One fact may serve several routes; it still has one owner. File edit time measures maintenance, not fictional occurrence or authority.

## Recovery and focused retrieval

Use `recover --mode context` after context loss, `fresh` for a new GM, and `review` at a broad review. Read the operating core once. Restore all current protagonists and actual scene participants through full profile routes. Add missing sources and outside dependencies before reliance. A frozen transfer document cannot overrule live owners.

Use `prepare ENTITY --topic TOPIC --actor PARTICIPANT` at material scene/topic changes. Add `--destination ID` and `--until TICK` before a transition. Required dependencies remain selected; topical dependencies are selected for that topic. Related entities are suggestions, not aliases or shared knowledge. Read relevant ones explicitly. Inspect `unselected_refs` and `discover` when evidence may be missing or contrary. No search result is not proof of absence.

The output is private GM material. Reference hashes establish bytes, not truth, comprehension, or character awareness. `--list-parts` is a menu, not a completed read. Read each required full `--part`. Scoped reuse is permitted only while previous complete bodies remain available and their interpretation remains current. Do not reuse a manifest across context loss merely because the hash matches.

## Workflow A: each narrative response

1. Ground the exchange in the last delivered scene and checkpoint. Separate spoken words, actions, observations, private thoughts, and OOC instructions. Preserve unanswered exchanges and the players' pending choices.
2. Decide relevant NPC behavior before drafting dialogue. Use actual knowledge, motives, emotions, relationships, authority, attention and means. Include stationary or absent actors whose established opportunities matter. Consider groups and individual differences without requiring a chorus or a conflict. Translate relevant history into a present choice, not a biography recital.
3. Resolve legal means, timing and consequences. Verify costs, abilities, dice stakes, geometry, routes, perception and communication. Explain choice-changing constraints before commitments. Resolve due operations and conditional event triggers before dependent arrivals, reports or choices. An unfinished GM lookup is not an NPC obstacle.
4. Write and inspect the actual scene. Check consequential claims about names, places, knowledge, promises, time and resources against accepted evidence. Preserve individual voices, independent companion initiative and space for the players' response. Keep private analysis out of dialogue. Correct unsupported decisions before saving; a read receipt is insufficient.
5. Save the delivered change in its owners. Record meaningful events and dialogue once. Reconcile resources, knowledge, operations, corrections and retrieval routes together. Review individual development and rewards at meaningful resolutions. Do not save an unpresented continuation as accepted play.

Reuse unchanged facts. Do not simulate the whole world, reread the library, or run technical tests after each exchange. Ordinary silence and stable choices need no forced development.

## Living world and time

Run the attention view before advancing time or entering a scene that depends on other work. Include commitments not yet promoted to operations. Resolve the earliest applicable checkpoint:

- IMMEDIATE: meaningful actions, changing awareness, danger, communication, confrontation or directly affected event predicates.
- ACTIVE: next task step, deadline, consequential information change, or dependent arrival/report/decision, whichever occurs first. Promised work can be active before it starts.
- BACKGROUND: configured broad reviews unless urgency or dependencies promote it.

Resolve actual progress or a supported blocker, not another promise. Do not move a deadline because preparation was forgotten. Keep parent projects and remaining delivery duties after a subtask finishes. Routine work can be batched. No automatic success, full-cast simulation, message-count clock, or real-world scheduler is implied.

## Ordered broad review

Default review offsets correspond to morning and evening; configure them for the campaign's calendar. The CLI surfaces crossed boundaries and unresolved earlier coverage. It does not run reviews. At each actual boundary:

1. Orientation: refresh the foundation, adopted lore, chronology, consequential cast and wider situation.
2. Preparation: select relevant developments for each protagonist and important actor. Review source events, clues, opportunities, rewards and neglected commitments. Turn applicable preparation into feasible openings.
3. World: resolve due work through earned information, real channels, means, motives, elapsed time and uncertain dice. Stop for meaningful player decisions or perceptible events.
4. Cleanup: close completed steps, repair stale claims, preserve unique history, remove rejected branches, and verify affected retrieval output.
5. Scene: restore the exact checkpoint, HOLD, pending exchange, cast, resources and next boundary.

Record completed and partial coverage in the state owner. Do not replay completed outcomes, skip unfinished phases, or confuse OOC maintenance with fictional time. A late correction can require targeted re-evaluation without simulating missed harms retroactively.

## Specialist triggers

| Trigger | Procedure |
|---|---|
| Returning actor/topic, dialogue, learning, relationship or emotional development | `procedure play` |
| Consequential actor decision, report, promise, project, time advance, source event, reward review | `procedure world` |
| Movement, awareness, coordination, combat, new site, map or viewpoint image | `procedure spatial` |
| Resource transaction, correction, source adoption, cleanup or session close | `procedure records` |
| Roll20 source/UI access, bridge setup, character-sheet interpretation or music | `procedure tools` |
| Explicit transfer to another GM/chat | `procedure handoff` |

Choose only relevant sections and reuse them while current. The specialist instructions are part of Workflow A, not extra passes over the same scene.

## Completion and verification

At session close reconcile the exact boundary, resources, promises, effects, knowledge and development. Assess workflow success through delivered play: continuity, character depth, consequences, accessible clues, fair counterplay and pacing. Use focused code tests for technical changes and affected-owner readback for record edits. A test count cannot certify narrative quality.
