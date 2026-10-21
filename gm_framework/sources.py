"""Import complete, authorized Roll20 receipts; never connect to an account."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from html.parser import HTMLParser

from .store import Campaign, digest


def readable_html(raw):
    """Deterministic text view; exact original HTML stays stored and hashed."""
    class Reader(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts = []
            self.hidden = 0
        def handle_starttag(self, tag, attrs):
            if tag in {"script", "style"}:
                self.hidden += 1
            if self.hidden:
                return
            if re.fullmatch(r"h[1-6]", tag):
                self.parts.append("\n\n" + "#" * int(tag[1]) + " ")
            elif tag in {"p", "div", "br", "li", "tr"}:
                self.parts.append("\n")
            elif tag in {"td", "th"}:
                self.parts.append(" | ")
            elif tag == "img":
                values = dict(attrs)
                self.parts.append(f"\n[image requires inspection: {values.get('alt', '')} {values.get('src', '')}]\n")
            elif tag == "a":
                href = dict(attrs).get("href", "")
                if href:
                    self.parts.append(f"[source link: {href}] ")
        def handle_endtag(self, tag):
            if tag in {"script", "style"}:
                self.hidden = max(0, self.hidden - 1)
            elif not self.hidden and (tag in {"p", "div", "li", "tr"} or re.fullmatch(r"h[1-6]", tag)):
                self.parts.append("\n")
        def handle_data(self, text):
            if not self.hidden:
                self.parts.append(text)
    parser = Reader()
    parser.feed(raw)
    parser.close()
    return "".join(parser.parts).strip()


def source_menu(campaign, entity=None):
    """Full source menu, including optional topics; no hidden top-N cutoff."""
    keys = set(campaign.refs)
    if entity:
        key = campaign.resolve(entity)
        item = campaign.entities[key]
        seeds = item.get("required", []) + item.get("history", []) + item.get("profile_refs", [])
        seeds += [item["profile"]] if item.get("profile") else []
        seeds += [r for refs in item["topics"].values() for r in refs]
        keys = set(seeds)
        while True:
            expanded = keys | {e["ref"] for r in keys for e in campaign.refs[r].get("dependencies", [])}
            if expanded == keys:
                break
            keys = expanded
    inventory = {row["id"]: row for row in campaign.owner("sources")}
    rows = []
    for key in sorted(keys):
        ref = campaign.refs[key]
        if ref.get("status") == "source":
            rows.append({"ref": key, "path": ref.get("path"), "locator": ref.get("locator"),
                         "section": ref.get("section"), "authority": ref.get("authority"),
                         "coverage": inventory.get(key, {}).get("coverage", "See source owner; no complete-adventure claim"),
                         "adoption": inventory.get(key, {}).get("adoption", "See adopted owner")})
    return {"sources": rows, "inventory": list(inventory.values()) if not entity else None,
            "notice": "All declared source dependencies, including unselected topics. Missing undeclared material still requires source inventory/GM review."}


def assemble(receipts):
    rows = [r.get("result", r) for r in receipts]
    if not rows:
        raise ValueError("No source receipts")
    first = rows[0]
    identity = (first["id"], first["field"], first["view"], first["fingerprint"], first["total"], first["rawLength"])
    if first["view"] != "raw":
        raise ValueError("Import raw source receipts; retain the original rather than a lossy text conversion")
    offset, chunks = 0, []
    for row in sorted(rows, key=lambda r: r["offset"]):
        if tuple(row[k] for k in ["id", "field", "view", "fingerprint", "total", "rawLength"]) != identity:
            raise ValueError("Source changed or identities differ across receipt slices")
        if row.get("unchanged") or "text" not in row:
            raise ValueError("A cache hint is not source text; read again without ifFingerprint")
        if row["offset"] != offset:
            raise ValueError("Source slices have a gap or overlap")
        chunk = row["text"].encode("utf-16-le", errors="surrogatepass")
        offset += len(chunk) // 2  # Roll20 JavaScript offsets count UTF-16 code units.
        if row["next"] != (offset if offset < first["total"] else None):
            raise ValueError("Invalid continuation offset")
        chunks.append(chunk)
    if offset != first["total"] or first["rawLength"] != first["total"]:
        raise ValueError("Incomplete raw source")
    text = b"".join(chunks).decode("utf-16-le")
    return text, first


def import_source(root, receipts, key, title, game, object_type, edition, authority):
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,70}", key):
        raise ValueError("Source ID must use lowercase letters, digits, and hyphens")
    campaign = Campaign(root)
    if key in campaign.refs:
        raise ValueError("Reference exists. Review source changes and dependent canon before replacing its owner.")
    text, receipt = assemble(receipts)
    allowed = {"handout": {"notes", "gmnotes"}, "character": {"bio", "gmnotes"}}
    if object_type not in allowed or receipt["field"] not in allowed[object_type]:
        raise ValueError("Source field does not match object type")
    path = f"sources/{key}.html"
    target = campaign.path(path)
    if target.exists():
        raise ValueError("Source file already exists")
    entry = {"id": key, "title": title, "provider": "roll20", "game": game,
             "object_type": object_type, "object_id": receipt["id"], "field": receipt["field"],
             "edition": edition, "authority": authority, "path": path, "sha256": digest(text),
             "captured_at": datetime.now(timezone.utc).isoformat(), "completeness": "complete-field",
             "coverage": "One field only; linked handouts, maps, and other fields remain separate dependencies",
             "adoption": "unassessed", "redistribute": False}
    sources = campaign.owner("sources")
    sources.append(entry)
    config = campaign.config
    config["refs"][key] = {"path": path, "status": "source", "authority": authority, "sha256": digest(text),
                           "locator": {k: entry[k] for k in ["provider", "game", "object_type", "object_id", "field"]}}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="")
    campaign.path(config["owners"]["sources"]).write_text(json.dumps(sources, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (campaign.root / "campaign.json").write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return entry
