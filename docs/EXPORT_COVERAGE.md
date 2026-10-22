# Generalization and export coverage

This release extracts a reusable framework from a long-running private GM workspace. It is **not** a dump of that workspace and does not replace or migrate its live campaign. The public Python package is a portable reimplementation of the active retrieval concepts. The Roll20 bridge preserves and generalizes the existing tested implementation.

**Correction to the initial release:** v0.1.0 overstated functional preservation. Important procedures survived in prose but lost retrieval connections, and character/source recovery was less capable. v0.2.0 restores the connections described below. See the [parity audit](PARITY_AUDIT.md) for concrete losses, repairs, evidence and remaining limits.

## Coverage map

v0.3 carries forward the subsequent maintenance repairs without copying campaign records: complete-topic rewrites, stable current-owner references, causal character reasoning, disposal of obsolete scaffolding, source refresh in place, and stronger retrieval/publication boundaries. The portable source layout remains one file per distinct field or asset with a separate metadata catalogue; it does not inherit an adventure-specific cache layout.

| Private-system responsibility | Public implementation | Treatment |
|---|---|---|
| Root agent instructions and operating core | Repository `AGENTS.md`, generated campaign `AGENTS.md`, `DM_WORKFLOW.md` | Generalized roles, rules, paths, review clocks and authority; removed fixed cast/plot/level target |
| Play, encounter, campaign review, records and tool procedures | Six triggered procedure documents | Consolidated repeated safeguards while preserving decision, awareness, group, source, development and cleanup duties |
| Entity/category readers and ordinary lore routes | `store.Campaign`, `campaign.json` | One explicit reference registry; configurable paths, identities and topics |
| Module contexts, original cache readers and source views | Source inventory, reference dependencies and `sources.py` | Replaced adventure-specific builders and numeric source mappings with explicit per-game provenance |
| Focused preparation and context views | `prepare`, `recover`, `attention` | Full profiles/history, activity duties, focused refreshes, five review phases, scene recovery, independent review actors and operation evidence |
| Preparation-selection fingerprints | `manifest`, `render` | Same-owner contained-section deduplication; scoped reuse guarded by selection, policy, checkpoint, candidate metadata and semantic review assertion |
| Accepted-history readers/correction gates | Character history joins, broader accepted-path discovery, `impact`, excluded stores | Inactive child reads also block contaminated parent reads/broad discovery; minor departed actors can use accepted-history evidence |
| Spatial parent reader and map startup | Reference dependency closure, visual-gap records, spatial procedure | Preserved parent/source dependencies; no game-specific geometry or map builder |
| Actual uncertain rolls | `roll` | System-independent die sides/count/modifier; no automatic adjudication |
| Inspection Mod and its unit harness | `roll20/GMControl.js`, `.test.cjs` | Retained private read/receipt, lab guard, expected-value, undo and music behavior; renamed command/namespace; removed fixed resource list |
| Current checkpoint, operations and progression owners | Initialized private records and templates | Empty/configurable, not transferred from any campaign |
| Explicit continuing-GM transfer | Handoff procedure | Host-independent instructions; no account-specific chat control code |
| Current-owner source refresh | `source-refresh`, shared selectors and source inventory | Replaces one verified field in place; previews dependent routes, rejects broken selectors and retains adoption/identity |
| Consolidation and maintenance | RECORDS integration section, cleanup dependency, stable reference IDs | Rewrite existing owners, retain causal reasoning and accepted history, dispose of scaffolding, inspect actual output |
| Publication privacy | `check_distribution.py --staged --history --private-terms` | Scans the intended index and reachable historical blobs; private terms stay outside the public repository |
| Reusable mechanical rulings | `docs/OPTIONAL_RULINGS.md` | Explicit optional variants, with no character grants, setting exceptions or default rules edition |
| Structural regression checks | Focused Python tests, inherited/generalized bridge tests and CI | Synthetic fixtures; no private histories or expected player outcomes |
| Granular-record/graph experiments | Evaluation guidance and architecture notes | Findings retained; frozen campaign-specific pilot engines not shipped as production features |

## Deliberate exclusions

- Player names, personal lore, campaign transcripts, character sheets, romance/history records, current secrets, live IDs and private receipts.
- Publisher adventure prose, paid maps, cached handout exports, supplemental third-party text and other material the repository does not license.
- One-off scene patch scripts, hard-coded map-reconciliation deployments, handoff snapshots, old releases, generated reports, diagnostic receipts and failed/rejected branches.
- Generic document/image-generation utilities unrelated to running the GM workflow, local runtime binaries, browser sessions, credentials and host-specific automation configuration.
- Obsolete parallel retrieval pilots whose schemas and tests depended on private canon. No claim is made that a universal fact graph replaced the owner-based system.

These exclusions are appropriate privacy and portability boundaries. They did not justify the initial release's missing reusable behavior. The restored responsibilities are mapped above; publishing private files after replacing a few names would still expose source material and preserve misleading assumptions.

## Behavior changes and tradeoffs

The public engine uses one root/configuration boundary instead of modules fixed to a particular directory. All character classes and roles are data. Related people remain separate identities. Calendar ticks replace prose-date parsing. Original and supplementary sources share the same provenance model.

Selection emits complete declared units instead of keyword-ranked profile previews. This is easier to inspect and less likely to hide a qualifier, but can cost more context if owner sections are too coarse. It deliberately does not claim the private system's earlier benchmark gains.

The lightweight package omits an autonomous model runner, browser session manager and database server. The GM host supplies tools and authenticated access. This keeps accounts and model choice independent but requires explicit setup, source registration, and competent record maintenance.

The revised procedures connect review phases, activity triggers, character history and source events to actual retrieval entry points. Their success still depends on applying them to narration. Validation demonstrates retrieval behavior and bridge guards, not universal game quality. Evaluate unfamiliar scenes before expanding automation.
