# Audit of the public framework against its working predecessor

## Finding

The initial v0.1.0 export preserved much of the philosophy, but lost important execution and retrieval connections. Calling it fully equivalent was too strong. In particular, describing five review phases did not make them separately retrievable, and asking for character depth did not reliably retrieve the history needed to portray it.

v0.2.0 repairs those losses in the existing owner-and-route design. It is a usable campaign framework with setup, source intake, recurring preparation, living-world duties, corrections and continuing-GM recovery. It is not a preconfigured adventure, an autonomous narrator, or a guarantee that a model will use the evidence well.

The comparison examined the predecessor's operating core, specialist procedure sections, recovery/activity selection, character and source readers, preparation deduplication/reuse, and accepted-record maintenance. Private plot, characters, dialogue, source prose and game identifiers were not exported. The comparison was semantic and functional, not a line-count target.

## Material losses and repairs

The v0.3 follow-up addresses maintenance after consolidation. Source refresh updates existing field owners and validates linked selectors; discovery no longer bypasses a source hash failure through a broad file scan. Nested JSON rejected branches cannot bypass the accepted-record boundary through formatting differences. Stable IDs retain relocated character/history routes, and audits include dormant operation references. RECORDS now specifies coherent topic replacement, causal-detail preservation and disposal in its existing workflow. These behaviors have synthetic regression coverage in `tests/test_maintenance.py`; they do not imply a live-game or narration evaluation.

| Area | What v0.1 lost or weakened | v0.2 implementation and evidence |
|---|---|---|
| Morning/evening work | Five phases described in prose; one broad review selection | Separate orientation, preparation, world, cleanup and scene selections read updated owners in order. Tests verify different required duties and no implicit state mutation. |
| Duties at actual play boundaries | No activity entry point for rests, resolutions, downtime or scene close | `prepare --activity` selects the existing mechanics, development, commitments and procedure sections. Rest and resolution scenarios verify the relevant duty appears without granting or spending anything. |
| Independent world actors | No standard route for consequential actors outside the current scene | `review_actors`, unfinished operation actors and operation `refs` recover profiles, history and source-event constraints. An absent envoy scenario includes original, parent and adopted-supplement dependencies. |
| Early returns and unpromoted work | Promises not yet entered into operations could disappear from practical preparation | Scene/Commitments owner is connected to recovery, activities and transitions. An early-return scenario with an empty operations queue still retrieves the promised answer. |
| Full character depth | One profile reference, no automatic accepted-history joins, no economical minor-character recovery | Multiple `profile_refs`, `history` joins, required constraints and minor-character history fallback. Significant characters retain full profiles. Departed characters stay retrievable without becoming present again. |
| Portrayal instructions | Condensation weakened competing motives, prior relationships, source voice and causal inner development | PLAY explicitly connects experience to supported emotional, intellectual, spiritual and philosophical changes; preserves contrary influences, stable voice, independent life and guarded behavior. Recovery supplies the evidence; narration still requires review. |
| Meaningful scene evidence | Too little emphasis on small moments and exact terms/audience | RECORDS preserves causal dialogue, terms, recipients and what was actually accepted once in history. No routine paraphrase should overwrite the evidence needed for later portrayal. |
| Source events and rewards | General principles without enough detail about deployment, neglect or protagonist-specific preparation | WORLD restores the recurring preparation catalogue and distinguishes source-read, prepared, offered, accepted, activated and delivered events. It requires durable gains and aftermath as well as threats. Connected to resolutions and preparation/world review. |
| Source retrieval | Complete raw capture existed, but practical keyed/text views and route authoring were weak | `sources`, `read --view text`, exact headings or literal boundaries, `source-link`, and full-original hash verification. A synthetic complete HTML capture is linked into a new character without adopting it as canon. |
| Retrieval cost | Exact duplicate suppression only; repeated queue text and no narrow retained-context refresh | Same-owner contained-unit deduplication, operation summaries during full recovery, lightweight part navigation, configured focused refreshes with invariant qualifiers. Explicit actual actors still load full profiles/history. |
| Reuse safety | No invalidation for new unrouted evidence or changed checkpoint; insufficient semantic assertion | Request/configuration/selection, checkpoint digest, accepted-file metadata, selected body hashes and explicit retained-context/invalidation assertions. New history and checkpoint-change tests force full output. |
| Accepted-record boundary | Fallback discovery could resurface inactive material from an otherwise accepted file | Block contaminated parent reads and withhold broad fallback on mixed-status files while retaining clean registered sections. A superseded-child scenario tests both paths. Physical cleanup remains required. |
| Space and fair adjudication | Technical outline too thin about applied geometry and invalidated premises | SPATIAL requires source/adopted positions, intermediate spaces, views, routes, effect footprints and a preserved delivered boundary when correcting an error. No invented map geometry is supplied by the software. |
| Practical setup and adoption | A mostly manual configuration with no safe way to bring repairs to generated campaigns | Character scaffold and source-link helpers; a preview/apply upgrade for unchanged v0.1 templates. Customized templates stop the whole upgrade for manual merge. An actual v0.1-generated synthetic campaign was upgraded with state/history/operations/development byte-identical. |

## What remains deliberately different

- The predecessor's per-adventure source indexes and topic builders are replaced by explicit per-campaign references. A new campaign needs real source mapping; a generic program cannot know every cross-chapter dependency. Inventory warnings, source menus and broader accepted discovery help expose omissions, but do not prove completeness.
- The public engine emits complete selected units rather than inheriting a keyword-preview heuristic. This favors inspectable qualifiers. Large profiles and broadly linked history can cost more context; split coherent owners and curate causal anchors before adding fragment ranking.
- Fresh recovery defaults to accepted history. A mature campaign should configure bounded current chronology and appropriate history anchors, rather than loading its entire archive on every takeover.
- Host-specific browser/chat tools, local runtimes and one-use campaign repair scripts are not bundled. The host supplies authorized tool access. The optional Roll20 bridge has defined inspection scope; it does not expose every licensed source surface or replace visual map inspection.
- The source adventure, adopted supplements, source-active cast and character sheets are private inputs. Omitting them from this repository is necessary. Omitting the *ability to retrieve and apply them* would not be acceptable.

No additional fact graph, checklist layer, schedule daemon or alternate canon store was introduced. Character records, scene commitments, operations and development remain the owners of their existing responsibilities.

## Practical verification

Run the focused suite with `python -m unittest discover -s tests -v`. The additional scenarios live in `tests/test_workflow_connections.py`; source/owner/bridge tests retain their existing locations. They test observable retrieval and update behavior, not whether text contains a flattering description of the system.

For a human or model trial:

1. Initialize a private campaign or upgrade an unchanged v0.1 example. Inspect `catalog`, `topics ENTITY` and `sources ENTITY` to understand available evidence.
2. Complete one coherent scene's real source and character mapping, including a contrary constraint and an accepted small interaction. Do not supply a desired dialogue answer.
3. Ask an unfamiliar question about a character's changed outlook, an early return, an absent actor's pending decision, or a source event that should become available. Inspect what preparation actually retrieves and what the GM does with it.
4. Change one accepted fact through its owner, reconcile dependencies, and repeat. Confirm unchanged history survives and stale evidence cannot be silently reused.
5. Execute the five review phases, then recover the exact scene. Confirm the work was resolved or explicitly blocked, not merely relisted.

The release validation also exercises upgrading a real v0.1-generated fixture and installing the packaged distribution outside the checkout. This matters because working importable code alone does not prove that templates, migration metadata and command entry points ship correctly.

## Gains, costs and remaining uncertainty

The principal gain is that duties and causal evidence now reach the GM when needed. The initial version depended too heavily on remembering prose instructions and manually reconstructing links. The repaired version makes normal recovery, early returns, rest opportunities and independent strategic review executable entry points.

The costs are a few more explicit configuration fields, longer first-time character/history recovery, and conservative reuse invalidation when unrelated accepted files change. Metadata invalidation is deliberately cheap and imperfect: it is not content-based semantic discovery. Source mapping and honest profile maintenance remain human/GM work.

Structural tests cannot establish convincing dialogue, good pacing, semantic source completeness, fair psychology or sustained model compliance. No fresh live Roll20 deployment or longitudinal campaign playtest is claimed for this release. The repairs support those outcomes and remove known obstacles; future evaluation must judge delivered play, not the test count.
