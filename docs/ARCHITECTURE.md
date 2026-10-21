# Architecture and retrieval

## Representation

The system uses a hybrid of coherent owner documents, structured state, and explicit reference links. It does not make every sentence a graph node or copy a full biography into every scene.

Entities identify people, places, items, groups, events, projects, or rules. Reference IDs select authoritative evidence. Several entities can link to the same reference without duplicating its facts. A relationship is not containment, and containment does not imply knowledge. An entity's `related` links are a discovery menu; only explicit reference dependencies are followed automatically.

Mutable state has one owner. Detailed accepted events live once in history. A profile retains causal development and relationships with pointers to those events. Scene preparation selects the relevant implications without replacing the profile. Original source prose, adopted overrides, proposals and accepted events keep distinct status and authority labels.

For example, two characters can link to one accepted conversation while retaining different knowledge. A character's current location belongs in the checkpoint. A past meeting at another place remains history. The engine never interprets a shared reference as identical memory or location.

## Selection algorithm

`prepare` resolves an exact ID, name, or true alias. Unknown or ambiguous identities fail instead of guessing. It then selects:

1. The current checkpoint and scene owner, including unpromoted commitments.
2. The entity's required evidence and requested topic references.
3. Full profile and accepted causal-history references for a focal character and explicitly named actual participants.
4. The transitive closure of required or topic-matching reference dependencies.
5. Activity-specific duties and governing references for relevant/due operations. Transitions, arrivals, explicit time horizons and scene close expose the whole unfinished queue; ordinary focused preparation selects related and due work.

Dependency traversal visits each reference once and terminates cycles. Every edge carries a reason. Original source keys, parent areas, governing rules, contrary constraints and corrections can therefore stay attached to the evidence that depends on them. Dependencies are curated; the program does not infer all semantic relationships.

The output includes owner, selector, status, authority, hash and selection reason. Exact or provably contained selections from the same owner with the same status/authority/view merge, retaining their reasons. There is no cross-file semantic deduplication, invisible token cutoff, or claim that short output is necessarily better. Missing required text raises an error. Visual references produce explicit inspection gaps. Unselected topics, related entities and available focused refreshes remain visible.

Unlike the private predecessor's topic-keyword preview layer, this release emits complete selected units. This reduces ambiguous omission behavior at the cost of more text when owners are too large. Improve coherent section selectors before replacing profiles with fragments.

## Selectors and discovery

References support exact Markdown headings (optionally excluding child headings), JSON pointers, unique paragraph/row prefixes, and unique literal start/end boundaries. Ambiguous or missing selectors fail. A derived readable HTML view preserves heading structure and link targets while the complete raw original remains hashed. Paths must stay inside the campaign and outside rejected/evaluation/receipt/handoff stores, including through symbolic links.

`discover` searches registered accepted/source references and configured accepted-file discovery paths. It ranks lexical matches without a top-N cutoff. It also exposes newly added accepted documents that have no route yet. Matches are candidates: inspect authority, corrections, chronology and semantic relevance before use. Register relevant new selectors after discovery.

A file with registered proposed/inactive material is withheld from the broad fallback scan. Unrelated accepted registered sections remain searchable. A parent read that includes a blocked child fails instead of bypassing its status. This is a backstop, not a substitute for purging rejected material from live owners; unmarked prose cannot be classified automatically.

This addresses the indexing/search dependency in practical terms: curate reliable routes for known recurring work, but keep broader accepted-file discovery for information that has not yet been routed. Inventory missing source material separately. A zero-result search cannot establish that the underlying adventure lacks a fact.

`impact` traverses reverse declared dependencies and reports affected entities (including profile/history links), operation evidence, recovery/activity/review entry points and focused refreshes. It does not discover every narrative consequence. A correction still needs GM examination of resources, knowledge, reports, relationships and later events.

## Recovery, context size and reuse

Recovery modes select configured refs plus full profiles and history anchors for the party and current participants. Context recovery uses live owners; scene recovery restores the actual scene after interruptions. Fresh recovery also includes accepted history by default; split large histories into appropriate routes rather than requesting an unbounded transcript. Five separately selectable review phases read updated owners in sequence. Independent `review_actors` enter orientation/preparation/world, and unfinished operation actors and evidence enter world resolution. None of these reads certifies completion.

`--list-parts` shows a bounded reading menu; repeatable `--part N` returns complete selected units. Operation bodies are not repeated with each navigation part; use `attention` before a dependent transition. Full output also avoids duplicating the operations owner in attention. A list or truncated tool response is not a completed read. Keep owner units small enough for the host's output limits.

Optional manifests record request, policy, selected IDs, body hashes, checkpoint digest and accepted-discovery file metadata. Reuse requires matching retained-context and semantic-invalidation assertions. Changes to these inputs invalidate omission; selected bodies are always read and checked before omission. New unrouted evidence or a changed checkpoint therefore causes a conservative reread. File size/mtime metadata is cheap invalidation, not tamper-proof content verification or fictional age. A hash cannot prove reading, comprehension, fictional truth or source freshness. Context loss requires recovery even if bytes match.

Configured focused refreshes narrow a repeated topic only under asserted retained full context. They include invariant qualifiers; naming an actual actor still adds their full profile/history. This differs from manifest reuse: a refresh deliberately changes selection, whereas a manifest can suppress unchanged bytes in the same selection. Both need GM judgment about new premises.

## Time and living world

The state uses an absolute fictional `tick`, a human label, and a configurable period/review offsets. This avoids parsing one setting's calendar prose. Real file/capture timestamps are separate metadata. They never establish event chronology or override accepted authority.

`attention` lists unfinished operations and flags explicit due/overdue ticks, dependent destinations/events and immediate predicates. It lists crossed review boundaries since the last completed coverage and preserves a partial-phase marker. It does not simulate jobs, evaluate prose conditions, reroll outcomes, send messages or change state.

The GM resolves immediate actions, active work at its next meaningful opportunity, and background work at broad reviews. Due work must be resolved before a report or return depends on it. Morning/evening reviews order orientation, preparation, world resolution, cleanup and scene recovery. These are fictional checkpoints, not cron tasks.

## Mutations and trust

Retrieval is read-only. Initialization creates a new private directory. Source import writes captured source and provenance without adopting it as history. `add-character` creates an explicitly unfilled scaffold and routes; `source-link` connects existing source sections without adopting them. `upgrade` previews procedure/configuration changes and preserves customized templates by stopping for a manual merge. `update` performs an expected-hash guarded replacement of one configured JSON owner. Other authoring uses ordinary file tools with affected-selector readback.

Use a single writer. Cross-file changes are not transactional; keep play on HOLD through reconciliation, especially after an interrupted import or correction. Do not present this as a concurrent campaign database. Git can back up a private campaign if its users deliberately configure it; never publish that data by default.

The Roll20 bridge checks GM access, escapes private output, paginates reads, and isolates test writes from live objects. Captured source remains untrusted data and private intellectual property. Technical access does not grant redistribution rights.

## Scope of automation

Automated: exact selectors, required dependency closure, lexical candidate discovery, explicit attention reminders, structural checks, hashes, bounded output and controlled test-object operations.

GM responsibility: psychological interpretation, source adoption, disclosure, character knowledge, group decisions, visual geometry, conditional triggers, uncertain adjudication, narrative quality, meaningful opportunities and accepted record maintenance.

There is no A* search because this retrieval task has no useful shortest-path cost target. Dependency closure and lexical search address the present problem more directly. Semantic search or a larger graph can be added after evidence shows a benefit; neither replaces owner authority or correct portrayal.
