import argparse
import json
from pathlib import Path
import secrets
import sys

from .bootstrap import initialize
from .sources import import_source, source_menu
from .store import Campaign, digest, inside, manifest, read_json, render, section


def output(value):
    print(json.dumps(value, ensure_ascii=False, indent=2) if not isinstance(value, str) else value)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Private GM retrieval and workflow tools; never advance fiction automatically.")
    parser.add_argument("--root", default=".", help="Private campaign directory")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("destination")
    for flag in ["title", "player", "character", "rules", "genre"]:
        init.add_argument("--" + flag, required=True)
    demo = commands.add_parser("demo")
    demo.add_argument("destination")
    demo.add_argument("--setting", choices=["marsh", "orbital"], default="marsh")
    prepare = commands.add_parser("prepare")
    prepare.add_argument("entity")
    prepare.add_argument("--topic", default="core")
    prepare.add_argument("--actor", action="append", default=[])
    prepare.add_argument("--destination")
    prepare.add_argument("--activity")
    prepare.add_argument("--refresh")
    prepare.add_argument("--until", type=int, help="Proposed absolute fictional tick, not real-world time")
    recover = commands.add_parser("recover")
    recover.add_argument("--mode", choices=["context", "fresh", "review", "scene"], default="context")
    recover.add_argument("--phase", choices=["orientation", "preparation", "world", "cleanup", "scene"])
    recover.add_argument("--actor", action="append", default=[])
    recover.add_argument("--reuse-procedures", action="store_true")
    for item in [prepare, recover]:
        item.add_argument("--json", action="store_true")
        item.add_argument("--list-parts", action="store_true")
        item.add_argument("--part", type=int, action="append")
        item.add_argument("--reuse", help="Prior technical manifest path; never canon")
        item.add_argument("--assert-retained-context", help="Exact scope token; assert prior bodies remain available and assessed")
        item.add_argument("--assert-invalidation", help="State which changed premises/candidates were checked before reuse")
        item.add_argument("--manifest", help="Write byte manifest to this path, after full output")
    attention = commands.add_parser("attention")
    attention.add_argument("--until", type=int)
    attention.add_argument("--destination")
    attention.add_argument("--actor", action="append", default=[])
    attention.add_argument("--activity")
    attention.add_argument("--topic")
    for name in ["read", "discover", "impact"]:
        command = commands.add_parser(name)
        command.add_argument("query")
        if name == "read":
            command.add_argument("--section")
            command.add_argument("--view", choices=["raw", "text"])
            command.add_argument("--start")
            command.add_argument("--end")
    procedure = commands.add_parser("procedure")
    procedure.add_argument("name")
    procedure.add_argument("--section")
    commands.add_parser("audit")
    commands.add_parser("sources").add_argument("entity", nargs="?")
    commands.add_parser("topics").add_argument("entity")
    commands.add_parser("catalog")
    commands.add_parser("upgrade").add_argument("--apply", action="store_true")
    character = commands.add_parser("add-character")
    character.add_argument("id")
    character.add_argument("--name", required=True)
    character.add_argument("--controller", choices=["gm", "player"], default="gm")
    character.add_argument("--importance", choices=["minor", "significant"], default="significant")
    character.add_argument("--player")
    character.add_argument("--source-ref", action="append", default=[])
    character.add_argument("--history-ref", action="append", default=[])
    link = commands.add_parser("source-link")
    link.add_argument("source")
    link.add_argument("--entity", required=True)
    link.add_argument("--topic", default="core")
    link.add_argument("--section")
    link.add_argument("--ref-id")
    link.add_argument("--required", action="store_true")
    link.add_argument("--start")
    link.add_argument("--end")
    source = commands.add_parser("source-import")
    for flag in ["receipts", "id", "title", "game", "edition"]:
        source.add_argument("--" + flag, required=True)
    source.add_argument("--type", choices=["handout", "character"], required=True)
    source.add_argument("--authority", choices=["original", "supplement", "homebrew"], default="original")
    update = commands.add_parser("update")
    update.add_argument("owner", help="Exact configured JSON owner name")
    update.add_argument("--from-file", required=True)
    update.add_argument("--expect", required=True, help="SHA-256 of the current UTF-8 text")
    roll = commands.add_parser("roll")
    roll.add_argument("sides", type=int)
    roll.add_argument("--count", type=int, default=1)
    roll.add_argument("--modifier", type=int, default=0)
    roll.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            from .demo import build_demo
            output(str(build_demo(args.destination, args.setting)))
            return 0
        if args.command == "init":
            root = initialize(args.destination, args.title, args.player, args.character, args.rules, args.genre)
            output(f"Created private campaign: {root}\nRead AGENTS.md and complete source intake before play.")
            return 0
        if args.command == "roll":
            if not (2 <= args.sides <= 1000000 and 1 <= args.count <= 100):
                raise ValueError("Use 2–1000000 sides and 1–100 dice")
            dice = [secrets.randbelow(args.sides) + 1 for _ in range(args.count)]
            output({"dice": dice, "modifier": args.modifier, "total": sum(dice) + args.modifier, "reason": args.reason})
            return 0
        campaign = Campaign(args.root)
        if args.command in {"prepare", "recover"}:
            if args.manifest and (args.part is not None or args.list_parts or args.reuse or not args.assert_retained_context or not args.assert_invalidation):
                raise ValueError("Manifest export needs full output, scope and invalidation assertions; no part, list, or reuse")
            if args.command == "prepare" and args.refresh and not args.assert_retained_context:
                raise ValueError("Focused refresh requires retained full character/procedural context; recover first after context loss")
            plan = campaign.prepare(args.entity, args.topic, args.actor, args.destination, args.until, args.activity, args.refresh) if args.command == "prepare" else campaign.recover(args.mode, args.phase, args.actor, args.reuse_procedures)
            reuse = read_json(args.reuse) if args.reuse else None
            if args.reuse and not (args.assert_retained_context and args.assert_invalidation):
                raise ValueError("Reuse requires retained-context and invalidation assertions")
            if args.json and (args.part or args.list_parts or args.reuse):
                raise ValueError("JSON returns the full plan; do not combine with part/list/reuse flags")
            output(plan if args.json else render(plan, reuse, args.assert_retained_context, args.part, args.list_parts, args.assert_invalidation))
            if args.manifest:
                Path(args.manifest).write_text(json.dumps(manifest(plan, args.assert_retained_context, args.assert_invalidation), indent=2) + "\n", encoding="utf-8")
        elif args.command == "attention":
            output(campaign.attention(args.until, args.destination, args.actor, args.activity, args.topic))
        elif args.command == "read":
            query = args.query
            if args.section and args.start or args.end is not None and args.start is None:
                raise ValueError("Choose heading or start/end; an end requires a start")
            if args.section or args.view or args.start:
                query = "__explicit_read__"
                campaign.refs[query] = dict(campaign.refs[args.query])
                if args.section:
                    campaign.refs[query]["section"] = args.section
                if args.view:
                    campaign.refs[query]["view"] = args.view
                if args.start:
                    campaign.refs[query].update({"start": args.start, "end": args.end})
            output(campaign.plan([(query, "Explicit read, with required dependencies")], "core", {"read": args.query}))
        elif args.command in {"discover", "impact"}:
            output(getattr(campaign, args.command)(args.query))
        elif args.command == "procedure":
            ref = campaign.config["procedures"][args.name]
            body = campaign.path(ref["path"]).read_text(encoding="utf-8-sig")
            output(section(body, args.section) if args.section else body)
        elif args.command == "sources":
            output(source_menu(campaign, args.entity))
        elif args.command == "topics":
            entity = campaign.entities[campaign.resolve(args.entity)]
            output({"topics": entity["topics"], "activities": list(campaign.config.get("activities", {})),
                    "refreshes": campaign.config.get("focused_refresh", {})})
        elif args.command == "catalog":
            output({"entities": [{"id": k, "name": e["name"], "kind": e.get("kind"), "topics": list(e.get("topics", {}))} for k, e in campaign.entities.items()],
                    "refs": [{"id": k, **{field: r[field] for field in ("path", "section", "pointer", "start", "status", "authority", "format") if field in r}} for k, r in campaign.refs.items()]})
        elif args.command == "add-character":
            from .authoring import add_character
            output(add_character(args.root, args.id, args.name, args.controller, args.importance, args.player, args.source_ref, args.history_ref))
        elif args.command == "source-link":
            from .authoring import link_source
            output(link_source(args.root, args.source, args.entity, args.topic, args.section, args.ref_id, args.required, args.start, args.end))
        elif args.command == "upgrade":
            from .authoring import upgrade
            result = upgrade(args.root, args.apply)
            output(result)
            return 2 if result.get("conflicts") else 0
        elif args.command == "source-import":
            output(import_source(args.root, read_json(args.receipts), args.id, args.title, args.game, args.type, args.edition, args.authority))
        elif args.command == "update":
            path = campaign.path(campaign.config["owners"][args.owner])
            before = path.read_text(encoding="utf-8")
            if digest(before) != args.expect:
                raise ValueError("Owner changed; reread and merge instead of overwriting")
            data = read_json(args.from_file)
            text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            # Single-writer contract. This is a guarded single-owner update, not a cross-file transaction.
            temp = path.with_name(path.name + ".pending")
            with temp.open("x", encoding="utf-8", newline="") as handle:
                handle.write(text)
            if digest(path.read_text(encoding="utf-8")) != args.expect:
                temp.unlink()
                raise ValueError("Owner changed while staging; update cancelled")
            temp.replace(path)
            output({"owner": args.owner, "sha256": digest(path.read_text(encoding="utf-8")), "changed": before != text})
        elif args.command == "audit":
            result = campaign.audit()
            output(result)
            return 1 if result["errors"] else 0
        return 0
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
