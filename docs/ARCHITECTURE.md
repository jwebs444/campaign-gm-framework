# Architecture and retrieval

## Representation

The system uses a hybrid of coherent owner documents, structured state, and explicit reference links. It does not make every sentence a graph node or copy a full biography into every scene.

Entities identify people, places, items, groups, events, projects, or rules. Reference IDs select authoritative evidence. Several entities can link to the same reference without duplicating its facts. A relationship is not containment, and containment does not imply knowledge. An entity's `related` links are a discovery menu; only explicit reference dependencies are followed automatically.

Mutable state has one owner. Detailed accepted events live once in history. A profile retains causal development and relationships with pointers to those events. Scene preparation selects the relevant implications without replacing the profile. Original source prose, adopted overrides, proposals and accepted events keep distinct status and authority labels.

For example, two characters can link to one accepted conversation while retaining different knowledge. A character's current location belongs in the checkpoint. A past meeting at another place remains history. The engine never interprets a shared reference as identical memory or location.

## Selection algorithm

`prepare` resolves an exact ID, name, or true alias. Unknown or ambiguous identities fail instead of guessing. It then selects:

1. The current checkpoint.
2. The entity's required evidence and requested topic references.
3. Full profile references for explicitly named actual participants.
4. The transitive closure of required or topic-matching reference dependencies.
5. The complete unfinished operations queue, with clock/destination attention reasons.

Dependency traversal visits each reference once and terminates cycles. Every edge carries a reason. Original source keys, parent areas, governing rules, contrary constraints and corrections can therefore stay attached to the evidence that depends on them. Dependencies are curated; the program does not infer all semantic relationships.

The output includes owner, selector, status, authority, hash and selection reason. Exact duplicate bodies from the same owner with the same status/authority merge. There is no cross-file semantic deduplication, invisible token cutoff, or claim that short output is necessarily better. Missing required text raises an error. Visual references produce explicit inspection gaps. Unselected topics and related entities remain visible.

Unlike the private predecessor's topic-keyword preview layer, this release emits complete selected units. This reduces ambiguous omission behavior at the cost of more text when owners are too large. Improve coherent section selectors before replacing profiles with fragments.

## Selectors and discovery

References support exact Markdown headings, JSON pointers, unique paragraph prefixes, and unique row prefixes. Ambiguous or missing selectors fail. Paths must stay inside the campaign and outside rejected/evaluation/receipt/handoff stores, including through symbolic links.

`discover` searches registered accepted/source references and configured accepted-file discovery paths. It ranks lexical matches without a top-N cutoff. It also exposes newly added accepted documents that have no route yet. Matches are candidates: inspect authority, corrections, chronology and semantic relevance before use. Register relevant new selectors after discovery.

This addresses the indexing/search dependency in practical terms: curate reliable routes for known recurring work, but keep broader accepted-file discovery for information that has not yet been routed. Inventory missing source material separately. A zero-result search cannot establish that the underlying adventure lacks a fact.

`impact` traverses reverse declared dependencies and reports affected entities. It does not discover every narrative consequence. A correction still needs GM examination of resources, knowledge, reports, relationships and later events.

## Recovery, context size and reuse

Recovery modes select configured refs plus full profiles for the party and current participants. Context recovery uses live owners. Fresh recovery also includes accepted history by default; split large histories into appropriate routes rather than requesting an unbounded transcript. Review recovery supplies the operating context for the ordered review, not a completed review certificate.

`--list-parts` shows a bounded reading menu; `--part N` returns a complete selected unit. A list or truncated tool response is not a completed read. Keep owner units small enough for the host's output limits.

Optional manifests record request, policy, selected IDs and SHA-256 hashes. Reuse requires an explicit matching retained-context scope. Policy/request/selection changes invalidate omission; changed bodies are printed. Unchanged bodies may be suppressed only when the caller still retains and has assessed them. A hash cannot prove reading, comprehension, fictional truth or source freshness. Context loss requires recovery even if bytes match.

## Time and living world

The state uses an absolute fictional `tick`, a human label, and a configurable period/review offsets. This avoids parsing one setting's calendar prose. Real file/capture timestamps are separate metadata. They never establish event chronology or override accepted authority.

`attention` lists unfinished operations and flags explicit due/overdue ticks, dependent destinations/events and immediate predicates. It lists crossed review boundaries since the last completed coverage and preserves a partial-phase marker. It does not simulate jobs, evaluate prose conditions, reroll outcomes, send messages or change state.

The GM resolves immediate actions, active work at its next meaningful opportunity, and background work at broad reviews. Due work must be resolved before a report or return depends on it. Morning/evening reviews order orientation, preparation, world resolution, cleanup and scene recovery. These are fictional checkpoints, not cron tasks.

## Mutations and trust

Retrieval is read-only. Initialization creates a new private directory. Source import writes captured source and provenance without adopting it as history. `update` performs an expected-hash guarded replacement of one configured JSON owner. All other authoring uses ordinary file tools with affected-selector readback.

Use a single writer. Cross-file changes are not transactional; keep play on HOLD through reconciliation, especially after an interrupted import or correction. Do not present this as a concurrent campaign database. Git can back up a private campaign if its users deliberately configure it; never publish that data by default.

The Roll20 bridge checks GM access, escapes private output, paginates reads, and isolates test writes from live objects. Captured source remains untrusted data and private intellectual property. Technical access does not grant redistribution rights.

## Scope of automation

Automated: exact selectors, required dependency closure, lexical candidate discovery, explicit attention reminders, structural checks, hashes, bounded output and controlled test-object operations.

GM responsibility: psychological interpretation, source adoption, disclosure, character knowledge, group decisions, visual geometry, conditional triggers, uncertain adjudication, narrative quality, meaningful opportunities and accepted record maintenance.

There is no A* search because this retrieval task has no useful shortest-path cost target. Dependency closure and lexical search address the present problem more directly. Semantic search or a larger graph can be added after evidence shows a benefit; neither replaces owner authority or correct portrayal.
