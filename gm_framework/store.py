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


def section(text, name):
    marks = list(re.finditer(r"(?m)^(#{1,6}) (.+)$", text))
    hits = [(i, m) for i, m in enumerate(marks) if m[2].strip().casefold() == name.casefold()]
    if len(hits) != 1:
        raise ValueError(f"Exact heading must match once: {name!r} ({len(hits)} matches)")
    i, match = hits[0]
    end = next((m.start() for m in marks[i + 1:] if len(m[1]) <= len(match[1])), len(text))
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
        if "section" in ref:
            text = section(text, ref["section"])
        if "pointer" in ref:
            text = json.dumps(pointer(json.loads(text), ref["pointer"]), ensure_ascii=False, indent=2)
        for selector, splitter in [("paragraph_prefix", "\n\n"), ("row_prefix", "\n")]:
            if selector in ref:
                hits = [p for p in text.split(splitter) if p.strip().startswith(ref[selector])]
                if len(hits) != 1:
                    raise ValueError(f"Selector must match once: {key}.{selector}")
                text = hits[0]
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
        # Only identical selections from the same owner and authority merge.
        unique = []
        for entry in entries:
            same = next((e for e in unique if (e["owner"], e["body"], e["status"], e["authority"]) ==
                         (entry["owner"], entry["body"], entry["status"], entry["authority"])), None)
            if same:
                same["why"] += entry["why"]
                same.setdefault("also", []).append(entry["ref"])
            else:
                unique.append(entry)
        return {"request": request, "policy": digest(self.config), "entries": unique, "gaps": gaps,
                "notice": "Private GM evidence. Selection and hashes do not establish comprehension, knowledge, or readiness."}

    def prepare(self, name, topic="core", actors=(), destination=None, until=None):
        key = self.resolve(name)
        entity = self.entities[key]
        if topic not in entity.get("topics", {"core": []}):
            raise ValueError(f"Unmapped topic {topic!r} for {key}; inspect available topics before proceeding")
        selected = [(self.config["checkpoint_ref"], "Current boundary and resources")]
        selected += [(r, f"{key}: required context") for r in entity.get("required", [])]
        selected += [(r, f"{key}: topic {topic}") for r in entity["topics"][topic]]
        for actor in actors:
            actor_id = self.resolve(actor)
            profile = self.entities[actor_id].get("profile")
            if not profile:
                raise ValueError(f"No full profile route for participant {actor_id}")
            selected.append((profile, f"Full participating character profile: {actor_id}"))
        plan = self.plan(selected, topic, {"entity": key, "topic": topic, "actors": list(actors),
                                           "destination": destination, "until": until})
        plan["available_topics"] = list(entity["topics"])
        plan["unselected_refs"] = sorted(set(r for refs in entity["topics"].values() for r in refs) -
                                        {e["ref"] for e in plan["entries"]})
        plan["related_entities"] = entity.get("related", [])
        # Duties stay complete and small; selection cannot silently hide an unindexed promise.
        plan["attention"] = self.attention(until, destination)
        return plan

    def recover(self, mode="context"):
        keys = [(r, f"Recovery: {mode}") for r in self.config["recovery"][mode]]
        state = self.owner("state")
        roster = set(state.get("party", []) + state.get("scene", {}).get("participants", []))
        for key in sorted(roster):
            profile = self.entities[key].get("profile")
            if not profile:
                raise ValueError(f"Participant {key} needs a full profile before portrayal")
            keys.append((profile, f"Full profile: {key}"))
        plan = self.plan(keys, "core", {"mode": mode})
        plan["attention"] = self.attention()
        return plan

    def attention(self, until=None, destination=None):
        state = self.owner("state")
        now = state["time"]["tick"]
        if until is not None and until < now:
            raise ValueError("Proposed time precedes the current checkpoint")
        end = now if until is None else until
        operations = self.owner("operations")
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
        for pattern in self.config.get("discovery_paths", []):
            inside(self.root, pattern)
            for path in sorted(self.root.glob(pattern)):
                if not path.is_file():
                    continue
                relative = path.relative_to(self.root).as_posix()
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
                        ([entity["profile"]] if entity.get("profile") else [])) & affected]
        return {"refs": sorted(affected), "entities": entities,
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
            if entity.get("kind") == "character" and not entity.get("profile"):
                errors.append(f"Character {key} has no full profile route")
            elif entity.get("profile"):
                try:
                    self.read(entity["profile"])
                except (ValueError, KeyError, OSError) as exc:
                    errors.append(f"Profile {key}: {exc}")
        for mode in self.config.get("recovery", {}):
            try:
                self.recover(mode)
            except (ValueError, KeyError, OSError) as exc:
                errors.append(f"Recovery {mode}: {exc}")
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
        return {"errors": sorted(set(errors)), "warnings": warnings,
                "notice": "Structural checks do not certify portrayal, source completeness, maps, or narrative readiness."}


def manifest(plan, scope):
    if not scope:
        raise ValueError("A context scope is required")
    return {"version": 1, "scope": scope, "request": plan["request"], "policy": plan["policy"],
            "entries": {entry["ref"]: entry["sha256"] for entry in plan["entries"]}}


def render(plan, reuse=None, scope=None, part=None, list_parts=False):
    lines = [plan["notice"]]
    reusable = bool(reuse and scope and reuse.get("scope") == scope and reuse.get("policy") == plan["policy"]
                    and reuse.get("request") == plan["request"] and
                    set(reuse.get("entries", {})) == {e["ref"] for e in plan["entries"]})
    if part is not None and not 1 <= part <= len(plan["entries"]):
        raise ValueError("Invalid part; use --list-parts")
    for i, entry in enumerate(plan["entries"], 1):
        title = f"{i}. {entry['ref']} | {entry['owner']} :: {entry['selector']} | {entry['status']}/{entry['authority']}"
        if list_parts:
            lines.append(title + f" | {len(entry['body'])} characters")
            continue
        if part is not None and part != i:
            continue
        lines.append("\n" + title + "\nWHY: " + "; ".join(entry["why"]))
        if reusable and reuse["entries"].get(entry["ref"]) == entry["sha256"]:
            lines.append("Unchanged bytes omitted under your asserted retained-context scope.")
        else:
            lines.append(entry["body"])
    for key in ["gaps", "unselected_refs", "available_topics", "related_entities", "attention"]:
        if plan.get(key):
            lines.append("\n" + key.upper() + "\n" + json.dumps(plan[key], ensure_ascii=False, indent=2))
    return "\n".join(lines)
