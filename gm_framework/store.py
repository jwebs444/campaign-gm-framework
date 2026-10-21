"""Authoritative owner reads, explicit dependency selection, and scoped byte reuse.

The code selects evidence. The GM interprets it and adjudicates the world.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PureWindowsPath
import re


def digest(value):
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def inside(root, relative):
    root = Path(root).resolve()
    if Path(relative).is_absolute() or PureWindowsPath(relative).drive or "\\" in relative:
        raise ValueError("Use a relative, forward-slash path inside the campaign")
    target = (root / relative).resolve()
    target.relative_to(root)
    return target


def section(text, name, include_children=True):
    marks = list(re.finditer(r"(?m)^(#{1,6}) (.+)$", text))
    hits = [(i, m) for i, m in enumerate(marks) if m[2].strip().casefold() == name.casefold()]
    if len(hits) != 1:
        raise ValueError(f"Exact heading must match once: {name!r} ({len(hits)} matches)")
    i, match = hits[0]
    end = next((m.start() for m in marks[i + 1:] if not include_children or len(m[1]) <= len(match[1])), len(text))
    return text[match.start():end].strip()


def pointer(data, address):
    if address == "":
        return data
    if not address.startswith("/"):
        raise ValueError("JSON pointer must start with /")
    for part in address[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        data = data[int(part)] if isinstance(data, list) else data[part]
    return data


def bounded_text(text, start, end=None):
    """Exact literal boundaries for source keys that are not Markdown headings."""
    if not start or text.count(start) != 1:
        raise ValueError("Source start marker must be nonempty and match exactly once")
    begin = text.index(start)
    finish = len(text)
    if end is not None:
        if not end or text.count(end) != 1 or text.index(end) <= begin:
            raise ValueError("Source end marker must match once after the start")
        finish = text.index(end)
    return text[begin:finish].strip()


class Campaign:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.config = read_json(self.root / "campaign.json")
        if self.config.get("version") != 1:
            raise ValueError("Unsupported campaign version")
        self.refs = self.config["refs"]
        self.entities = self.config["entities"]
        calendar = self.config["calendar"]
        if not isinstance(calendar["period"], int) or calendar["period"] <= 0:
            raise ValueError("Calendar period must be a positive integer")
        if any(not isinstance(t, int) or not 0 <= t < calendar["period"] for t in calendar["review_offsets"]):
            raise ValueError("Review offsets must fall within the configured period")

    def path(self, relative):
        target = inside(self.root, relative)
        for excluded in self.config.get("excluded", ["rejected", "evaluations", "handoffs", "receipts"]):
            base = inside(self.root, excluded)
            if target == base or base in target.parents:
                raise ValueError(f"Excluded from ordinary retrieval: {relative}")
        return target

    def owner(self, name):
        return read_json(self.path(self.config["owners"][name]))

    def profile_refs(self, key):
        entity = self.entities[self.resolve(key)]
        profiles = entity.get("profile_refs", []) + ([entity["profile"]] if entity.get("profile") else [])
        if not profiles and entity.get("importance") == "minor":
            profiles = entity.get("history", [])
        if not profiles:
            raise ValueError(f"No full profile or accepted minor-character evidence for {key}")
        return list(dict.fromkeys(profiles + entity.get("history", []) + entity.get("required", [])))

    def candidate_signature(self):
        """Cheap invalidation metadata, never evidence of age, authority, or reading."""
        rows = []
        for pattern in self.config.get("discovery_paths", []):
            inside(self.root, pattern)
            for file in self.root.glob(pattern):
                if file.is_file():
                    relative = file.relative_to(self.root).as_posix()
                    try:
                        self.path(relative)
                    except ValueError:
                        continue
                    stat = file.stat()
                    rows.append((relative, stat.st_size, stat.st_mtime_ns))
        return digest(sorted(set(rows)))

    def resolve(self, name):
        hits = [key for key, entity in self.entities.items()
                if name.casefold() in {s.casefold() for s in [key, entity["name"], *entity.get("aliases", [])]}]
        if len(hits) != 1:
            raise ValueError(f"Unknown or ambiguous entity: {name!r}. Use an exact ID.")
        return hits[0]

    def read(self, key):
        ref = self.refs[key]
        status = ref.get("status", "accepted")
        if status not in {"accepted", "source", "proposed"}:
            raise ValueError(f"Inactive evidence: {key} ({status})")
        if ref.get("format") == "visual":
            raise ValueError(f"Visual inspection required: {key}. Use its Roll20 locator; text cannot certify geometry.")
        # Original-source hashes include their exact newline sequences.
        with self.path(ref["path"]).open(encoding="utf-8-sig", newline="") as handle:
            text = handle.read()
        if "sha256" in ref and digest(text) != ref["sha256"]:
            raise ValueError(f"Source hash changed: {key}; review before refreshing the fingerprint")
        if ref.get("view") == "text":
            from .sources import readable_html
            text = readable_html(text)
        if "section" in ref:
            text = section(text, ref["section"], ref.get("include_children", True))
        if "start" in ref:
            text = bounded_text(text, ref["start"], ref.get("end"))
        if "pointer" in ref:
            text = json.dumps(pointer(json.loads(text), ref["pointer"]), ensure_ascii=False, indent=2)
        for selector, splitter in [("paragraph_prefix", "\n\n"), ("row_prefix", "\n")]:
            if selector in ref:
                hits = [p for p in text.split(splitter) if p.strip().startswith(ref[selector])]
                if len(hits) != 1:
                    raise ValueError(f"Selector must match once: {key}.{selector}")
                text = hits[0]
        if status in {"accepted", "source"}:
            # A broad owner read must not bypass an inactive/proposed child selector.
            for other_key, other in self.refs.items():
                if other_key == key or other.get("path") != ref["path"] or other.get("status", "accepted") in {"accepted", "source"}:
                    continue
                try:
                    with self.path(other["path"]).open(encoding="utf-8-sig", newline="") as handle:
                        blocked = handle.read()
                    if other.get("view") == "text":
                        from .sources import readable_html
                        blocked = readable_html(blocked)
                    if "section" in other:
                        blocked = section(blocked, other["section"], other.get("include_children", True))
                    if "start" in other:
                        blocked = bounded_text(blocked, other["start"], other.get("end"))
                    if "pointer" in other:
                        blocked = json.dumps(pointer(json.loads(blocked), other["pointer"]), ensure_ascii=False, indent=2)
                    for selector, splitter in [("paragraph_prefix", "\n\n"), ("row_prefix", "\n")]:
                        if selector in other:
                            hits = [p for p in blocked.split(splitter) if p.strip().startswith(other[selector])]
                            if len(hits) != 1:
                                blocked = ""
                                break
                            blocked = hits[0]
                except (ValueError, KeyError, IndexError):
                    continue  # Physically removed withdrawn text is not retrieved.
                if blocked.strip() and blocked.strip() in text:
                    raise ValueError(f"{key} contains inactive/proposed material from {other_key}; clean or narrow the owner before retrieval")
        return text.strip()

    def closure(self, keys, topic):
        """Required or topic-relevant references recurse; cycles terminate once."""
        reasons, ordered, seen = {}, [], set()
        def visit(key, why):
            if key not in self.refs:
                raise ValueError(f"Missing dependency {key!r}: {why}")
            reasons.setdefault(key, [])
            if why not in reasons[key]:
                reasons[key].append(why)
            if key in seen:
                return
            seen.add(key)
            ordered.append(key)
            for edge in self.refs[key].get("dependencies", []):
                if edge.get("required") or topic in edge.get("topics", []) or "*" in edge.get("topics", []):
                    visit(edge["ref"], f"{key}: {edge['why']}")
        for key, why in keys:
            visit(key, why)
        return ordered, reasons

    def plan(self, keys, topic, request):
        ordered, reasons = self.closure(keys, topic)
        entries, gaps = [], []
        for key in ordered:
            ref = self.refs[key]
            if ref.get("format") == "visual":
                gaps.append({"ref": key, "kind": "visual-inspection", "locator": ref.get("locator"), "why": reasons[key]})
                continue
            body = self.read(key)
            entries.append({"ref": key, "owner": ref["path"], "selector": ref.get("section", ref.get("pointer", "document")),
                            "status": ref.get("status", "accepted"), "authority": ref.get("authority", "campaign"),
                            "sha256": digest(body), "why": reasons[key], "body": body})
        # Only exact or provably contained selections from the SAME owner merge.
        def covers(parent, child):
            if (parent["owner"], parent["status"], parent["authority"]) != (child["owner"], child["status"], child["authority"]):
                return False
            a, b = self.refs[parent["ref"]], self.refs[child["ref"]]
            if a.get("view") != b.get("view") or child["body"] not in parent["body"]:
                return False
            if a == b:
                return True
            if any(k in a for k in ("pointer", "row_prefix", "paragraph_prefix", "start")) or "pointer" in b:
                return False
            if a.get("include_children") is False:
                return False
            return not b.get("section") or bool(re.search(r"(?m)^#{1,6} " + re.escape(b["section"]) + r"\s*$", parent["body"]))
        unique = []
        for entry in entries:
            representative = max((e for e in entries if covers(e, entry)), key=lambda e: len(e["body"]), default=entry)
            same = next((e for e in unique if e["ref"] == representative["ref"]), None)
            if same:
                same["why"] = list(dict.fromkeys(same["why"] + entry["why"]))
                if entry["ref"] != same["ref"]:
                    same.setdefault("also", []).append(entry["ref"])
            else:
                chosen = dict(representative, why=list(dict.fromkeys(representative["why"] + entry["why"])))
                if entry["ref"] != chosen["ref"]:
                    chosen["also"] = [entry["ref"]]
                unique.append(chosen)
        return {"request": request, "policy": digest(self.config), "entries": unique, "gaps": gaps,
                "boundary": digest(self.owner("state")),
                "candidates": self.candidate_signature(),
                "notice": "Private GM evidence. Selection and hashes do not establish comprehension, knowledge, or readiness."}

    def prepare(self, name, topic="core", actors=(), destination=None, until=None, activity=None, refresh=None):
        key = self.resolve(name)
        entity = self.entities[key]
        if topic not in entity.get("topics", {"core": []}):
            raise ValueError(f"Unmapped topic {topic!r} for {key}; inspect available topics before proceeding")
        selected = [(self.config["checkpoint_ref"], "Current boundary and resources")]
        selected += [(r, "Current scene and unanswered exchanges") for r in [self.config.get("scene_ref")] if r]
        if refresh:
            view = self.config.get("focused_refresh", {}).get(refresh)
            if not view or key not in [self.resolve(x) for x in view["entities"]] or (view.get("topics") and topic not in view["topics"]):
                raise ValueError("Focused refresh is unknown or not applicable to this entity/topic")
            selected += [(r, f"Focused refresh {refresh}: {view['why']}") for r in view["refs"]]
            selected += [(r, "Invariant refresh qualifier") for r in entity.get("invariants", ["corrections"])]
        else:
            selected += [(r, f"{key}: required context") for r in entity.get("required", [])]
            selected += [(r, f"{key}: topic {topic}") for r in entity["topics"][topic]]
            if entity.get("kind") == "character":
                selected += [(r, f"{key}: full characterization and causal history") for r in self.profile_refs(key)]
        for actor in actors:
            actor_id = self.resolve(actor)
            selected += [(r, f"Full participating character and history: {actor_id}") for r in self.profile_refs(actor_id)]
        if activity:
            if activity not in self.config.get("activities", {}):
                raise ValueError(f"Unmapped activity: {activity}")
            selected += [(r, f"Activity: {activity}") for r in self.config["activities"][activity]]
        if destination is not None or until is not None:
            selected += [(r, "Dependent transition: include unpromoted commitments") for r in [self.config.get("commitments_ref")] if r]
        attention = self.attention(until, destination, [key, *actors], activity, topic)
        for op in attention["operations"]:
            selected += [(r, f"Operation {op['id']}: governing evidence") for r in op.get("refs", [])]
        plan = self.plan(selected, topic, {"entity": key, "topic": topic, "actors": list(actors),
                                           "destination": destination, "until": until, "activity": activity, "refresh": refresh})
        plan["available_topics"] = list(entity["topics"])
        plan["unselected_refs"] = sorted(set(r for refs in entity["topics"].values() for r in refs) -
                                        {e["ref"] for e in plan["entries"]})
        plan["related_entities"] = entity.get("related", [])
        # Duties stay complete and small; selection cannot silently hide an unindexed promise.
        plan["attention"] = attention
        plan["focused_refreshes"] = [k for k, v in self.config.get("focused_refresh", {}).items() if key in [self.resolve(e) for e in v["entities"]]]
        return plan

    def recover(self, mode="context", phase=None, actors=(), reuse_procedures=False):
        from .workflow import PHASES
        if phase and mode != "review":
            raise ValueError("--phase requires review recovery")
        if reuse_procedures and mode not in {"review", "scene"}:
            raise ValueError("Procedure reuse is only valid for scene/review with retained procedural context")
        selected = self.config["recovery"][mode]
        if mode == "review":
            phase = phase or "orientation"
            if phase not in PHASES or phase not in self.config.get("review_phases", {}):
                raise ValueError("Review phase is not connected; upgrade the campaign workflow")
            selected = self.config["review_phases"][phase]
        if reuse_procedures:
            selected = [r for r in selected if self.refs[r].get("authority") != "procedure" and r != "workflow"]
        keys = [(r, f"Recovery: {mode}" + (f"/{phase}" if phase else "")) for r in selected]
        state = self.owner("state")
        roster = {self.resolve(a) for a in actors}
        if mode != "review" or phase in {"orientation", "preparation", "scene"}:
            roster.update(state.get("party", []) + state.get("scene", {}).get("participants", []))
        if mode == "review" and phase in {"orientation", "preparation", "world"}:
            roster.update(self.resolve(a) for a in self.config.get("review_actors", []))
        if mode == "review" and phase == "world":
            for op in self.attention()["operations"]:
                roster.update(op.get("actors", []))
                keys += [(r, f"Operation {op['id']}: source/event/decision dependency") for r in op.get("refs", [])]
        for key in sorted(roster):
            keys += [(r, f"Full profile and history: {key}") for r in self.profile_refs(key)]
        plan = self.plan(keys, "core", {"mode": mode, "phase": phase, "actors": list(actors), "reuse_procedures": reuse_procedures})
        plan["attention"] = self.attention()
        return plan

    def attention(self, until=None, destination=None, queries=(), activity=None, topic=None):
        state = self.owner("state")
        now = state["time"]["tick"]
        if until is not None and until < now:
            raise ValueError("Proposed time precedes the current checkpoint")
        end = now if until is None else until
        operations = self.owner("operations")
        wanted = {self.resolve(q) for q in queries}
        if destination:
            try:
                destination = self.resolve(destination)
            except ValueError:
                pass  # Event labels may be deliberately different from entity IDs.
        broad = not queries or destination is not None or until is not None or activity in {"arrival", "transition", "scene-close"}
        work = []
        for op in operations:
            if op["status"] in {"complete", "cancelled"}:
                continue
            triggers = []
            if op.get("next_tick") is not None and op["next_tick"] <= end:
                triggers.append("due or overdue clock checkpoint")
            if destination and destination in op.get("before", []):
                triggers.append("dependent destination or event")
            if op.get("cadence") == "IMMEDIATE":
                triggers.append("immediate predicate requires assessment")
            related = bool(wanted & set(op.get("actors", []) + op.get("entities", []) + op.get("before", []))) or topic in op.get("topics", []) or activity in op.get("activities", [])
            if not broad and not related and not triggers:
                continue
            work.append({**op, "attention_reasons": triggers})
        period = self.config["calendar"]["period"]
        last = state.get("reviews", {}).get("through_tick", now)
        boundaries = []
        if end >= last:
            for n in range(last // period, end // period + 1):
                for offset in self.config["calendar"]["review_offsets"]:
                    tick = n * period + offset
                    if last < tick <= end:
                        boundaries.append(tick)
        return {"current_tick": now, "proposed_tick": until, "review_boundaries": sorted(boundaries),
                "partial_review": state.get("reviews", {}).get("partial"), "operations": work,
                "scope": "whole unfinished queue" if broad else "related and due work; unpromoted commitments remain in scene preparation",
                "notice": "Read-only reminders. Check conditional triggers, unqueued commitments, and actual opportunity; no world advancement occurs here."}

    def discover(self, query):
        words = re.findall(r"\w+", query.casefold())
        if not words:
            raise ValueError("Enter a nonempty search query")
        matches, gaps = [], []
        for key, ref in self.refs.items():
            if ref.get("status", "accepted") not in {"accepted", "source"}:
                continue
            if ref.get("format") == "visual":
                continue
            try:
                body = self.read(key)
            except (ValueError, KeyError, OSError) as exc:
                gaps.append({"ref": key, "error": str(exc)})
                continue
            score = sum(body.casefold().count(word) for word in words)
            if score:
                matches.append({"ref": key, "score": score, "path": ref["path"],
                                "selector": ref.get("section", ref.get("pointer", "document")),
                                "status": ref.get("status", "accepted"), "sha256": digest(body)})
        # Discovery is broader than curated routes. New accepted files must be findable
        # before anyone knows to add the exact dependency link.
        inactive_paths = {ref.get("path") for ref in self.refs.values() if ref.get("status", "accepted") not in {"accepted", "source"}}
        for pattern in self.config.get("discovery_paths", []):
            inside(self.root, pattern)
            for path in sorted(self.root.glob(pattern)):
                if not path.is_file():
                    continue
                relative = path.relative_to(self.root).as_posix()
                if relative in inactive_paths:
                    gaps.append({"path": relative, "error": "Broad scan withheld: inactive/proposed material shares this file. Clean the owner; accepted registered sections remain searchable."})
                    continue
                try:
                    body = self.path(relative).read_text(encoding="utf-8-sig")
                except (ValueError, OSError) as exc:
                    gaps.append({"path": relative, "error": str(exc)})
                    continue
                score = sum(body.casefold().count(word) for word in words)
                if score:
                    matches.append({"ref": "", "score": score, "path": relative,
                                    "selector": "whole accepted-owner candidate; may contain unrouted sections", "status": "discovery-candidate",
                                    "sha256": digest(body)})
        return {"candidates": sorted(matches, key=lambda m: (-m["score"], m["ref"], m["path"])), "gaps": gaps,
                "notice": "Lexical candidates, not relevance or authority. No result does not prove absence; inspect source inventory and missing routes."}

    def impact(self, target):
        if target not in self.refs:
            raise ValueError("Unknown reference")
        affected = {target}
        while True:
            added = {key for key, ref in self.refs.items()
                     if any(e["ref"] in affected for e in ref.get("dependencies", []))}
            if added <= affected:
                break
            affected |= added
        entities = [key for key, entity in self.entities.items() if
                    set(entity.get("required", []) + [r for rows in entity.get("topics", {}).values() for r in rows] +
                        entity.get("profile_refs", []) + entity.get("history", []) + entity.get("invariants", []) +
                        ([entity["profile"]] if entity.get("profile") else [])) & affected]
        return {"refs": sorted(affected), "entities": entities,
                "operations": [op["id"] for op in self.owner("operations") if set(op.get("refs", [])) & affected],
                "entry_points": {group: [key for key, refs in self.config.get(group, {}).items() if set(refs) & affected]
                                 for group in ("recovery", "review_phases", "activities")},
                "refreshes": [key for key, view in self.config.get("focused_refresh", {}).items() if set(view["refs"]) & affected],
                "notice": "Declared links only. Also inspect semantic consequences, operations, knowledge, and corrections."}

    def audit(self):
        errors, warnings = [], []
        for key, ref in self.refs.items():
            try:
                if ref.get("status", "accepted") in {"accepted", "source", "proposed"}:
                    if ref.get("format") == "visual":
                        if not ref.get("locator"):
                            raise ValueError("Visual reference needs a locator")
                    else:
                        self.read(key)
                for dep in ref.get("dependencies", []):
                    if dep["ref"] not in self.refs or not dep.get("why"):
                        raise ValueError("Dependency needs an existing reference and reason")
                    if not dep.get("required") and not dep.get("topics"):
                        raise ValueError("Dependency is never selected: specify required or topics")
            except (ValueError, KeyError, OSError) as exc:
                errors.append(f"{key}: {exc}")
        for key, entity in self.entities.items():
            for alias in [key, entity["name"], *entity.get("aliases", [])]:
                try:
                    self.resolve(alias)
                except ValueError as exc:
                    errors.append(str(exc))
            for topic in entity.get("topics", {}):
                try:
                    self.prepare(key, topic)
                except (ValueError, KeyError, OSError) as exc:
                    errors.append(f"{key}/{topic}: {exc}")
            if entity.get("kind") == "character":
                try:
                    for r in self.profile_refs(key):
                        self.read(r)
                except (ValueError, KeyError, OSError) as exc:
                    errors.append(f"Profile {key}: {exc}")
        for mode in self.config.get("recovery", {}):
            try:
                self.recover(mode)
            except (ValueError, KeyError, OSError) as exc:
                errors.append(f"Recovery {mode}: {exc}")
        for phase in self.config.get("review_phases", {}):
            try:
                self.recover("review", phase)
            except (ValueError, KeyError, OSError) as exc:
                errors.append(f"Review {phase}: {exc}")
        for activity, refs in self.config.get("activities", {}).items():
            try:
                self.plan([(r, activity) for r in refs], "core", {"audit": activity})
            except (ValueError, KeyError, OSError) as exc:
                errors.append(f"Activity {activity}: {exc}")
        for key, refresh in self.config.get("focused_refresh", {}).items():
            try:
                for entity in refresh["entities"]:
                    for topic in refresh.get("topics", ["core"]):
                        self.prepare(entity, topic, refresh=key)
            except (ValueError, KeyError, OSError) as exc:
                errors.append(f"Refresh {key}: {exc}")
        for op in self.owner("operations"):
            if op["status"] not in {"complete", "cancelled"} and op.get("next_tick") is None and not (op.get("before") or op.get("condition")):
                errors.append(f"Operation {op['id']} has no next trigger")
            if op.get("cadence") not in {"IMMEDIATE", "ACTIVE", "BACKGROUND"}:
                errors.append(f"Operation {op['id']} has an invalid cadence")
            for actor in op.get("actors", []):
                if actor not in self.entities:
                    errors.append(f"Operation {op['id']} references unknown actor {actor}")
        calendar = self.config["calendar"]
        if not isinstance(calendar["period"], int) or calendar["period"] <= 0:
            errors.append("Calendar period must be a positive integer")
        elif any(not isinstance(t, int) or not 0 <= t < calendar["period"] for t in calendar["review_offsets"]):
            errors.append("Review offsets must fall within the configured period")
        if not self.owner("sources"):
            warnings.append("No source inventory: campaign source intake is incomplete")
        for source in self.owner("sources"):
            key = source["id"]
            if key not in self.refs:
                warnings.append(f"Source {key} has no readable/visual reference route")
            if source.get("adoption") in {None, "unassessed"}:
                warnings.append(f"Source {key} adoption is unassessed; capture is not integration")
        if self.config.get("workflow_revision", 1) < 2:
            warnings.append("Legacy workflow lacks connected phases/activities; use upgrade preview and reconcile it")
        return {"errors": sorted(set(errors)), "warnings": warnings,
                "notice": "Structural checks do not certify portrayal, source completeness, maps, or narrative readiness."}


def manifest(plan, scope, invalidation=None):
    if not scope:
        raise ValueError("A context scope is required")
    return {"version": 2, "scope": scope, "invalidation": invalidation, "request": plan["request"], "policy": plan["policy"],
            "candidates": plan.get("candidates"), "boundary": plan.get("boundary"),
            "entries": {entry["ref"]: entry["sha256"] for entry in plan["entries"]}}


def render(plan, reuse=None, scope=None, part=None, list_parts=False, invalidation=None):
    lines = [plan["notice"]]
    reusable = bool(reuse and reuse.get("version") == 2 and scope and invalidation and reuse.get("invalidation") == invalidation
                    and reuse.get("scope") == scope and reuse.get("policy") == plan["policy"]
                    and reuse.get("candidates") == plan.get("candidates") and reuse.get("boundary") == plan.get("boundary")
                    and reuse.get("request") == plan["request"] and
                    set(reuse.get("entries", {})) == {e["ref"] for e in plan["entries"]})
    parts = [part] if isinstance(part, int) else part
    if list_parts and parts is not None:
        raise ValueError("Choose --list-parts or --part")
    if parts is not None and (not parts or any(not 1 <= p <= len(plan["entries"]) for p in parts)):
        raise ValueError("Invalid part; use --list-parts")
    if reuse and not reusable:
        lines.append("Reuse invalidated or assertions incomplete; complete selected bodies follow.")
    for i, entry in enumerate(plan["entries"], 1):
        title = f"{i}. {entry['ref']} | {entry['owner']} :: {entry['selector']} | {entry['status']}/{entry['authority']}"
        if list_parts:
            lines.append(title + f" | {len(entry['body'])} characters")
            continue
        if parts is not None and i not in parts:
            continue
        lines.append("\n" + title + "\nWHY: " + "; ".join(entry["why"]))
        if reusable and reuse["entries"].get(entry["ref"]) == entry["sha256"]:
            lines.append("Unchanged bytes omitted under your asserted retained-context scope.")
        else:
            lines.append(entry["body"])
    for key in ["gaps", "unselected_refs", "available_topics", "related_entities", "focused_refreshes", "attention"]:
        if plan.get(key):
            value = plan[key]
            if key == "attention":
                if list_parts or parts is not None:
                    value = {k: v for k, v in value.items() if k != "operations"}
                    value["operations_notice"] = "Operation bodies omitted from part navigation; use attention before a dependent transition."
                elif any(e["ref"] == "operations" or "operations" in e.get("also", []) for e in plan["entries"]):
                    value = dict(value, operations=[{"id": o["id"], "attention_reasons": o["attention_reasons"]} for o in value["operations"]])
            lines.append("\n" + key.upper() + "\n" + json.dumps(value, ensure_ascii=False, indent=2))
    return "\n".join(lines)
