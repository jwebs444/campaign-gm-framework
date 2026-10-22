"""Synthetic regression cases for current-owner maintenance and publication."""
import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from gm_framework.authoring import link_source
from gm_framework.bootstrap import write_json
from gm_framework.cli import main
from gm_framework.demo import build_demo
from gm_framework.sources import import_source, refresh_source, source_menu
from gm_framework.store import Campaign, digest, render
from tools import check_distribution


def receipts(text, identity="TEST-ARCHIVE"):
    length = len(text.encode("utf-16-le")) // 2
    return [{"id": identity, "field": "gmnotes", "view": "raw", "fingerprint": digest(text),
             "rawLength": length, "total": length, "offset": 0, "next": None, "text": text}]


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = build_demo(Path(self.tmp.name) / "campaign")
        self.original = "<h1>Archive</h1><h2>Workshop</h2><p>The eastern door is sealed.</p>"
        self.entry = import_source(self.root, receipts(self.original), "archive", "Test archive", "TEST-GAME", "handout", "test", "original")
        link_source(self.root, "archive", "site", heading="Workshop", key="workshop", required=True)

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def test_refresh_updates_same_owner_and_selectors_without_touching_adopted_records(self):
        c = Campaign(self.root)
        sources = c.owner("sources")
        sources[-1]["adoption"] = "modified; see repair-rule"
        write_json(self.root / c.config["owners"]["sources"], sources)
        before = self.snapshot()
        changed = self.original.replace("sealed", "open")
        preview = refresh_source(self.root, receipts(changed), "archive", self.entry["sha256"])
        self.assertFalse(preview["applied"])
        self.assertIn("site", preview["impact"]["entities"])
        self.assertEqual(before, self.snapshot())
        result = refresh_source(self.root, receipts(changed), "archive", self.entry["sha256"], apply=True)
        self.assertTrue(result["applied"])
        after = self.snapshot()
        changed_files = {p for p in before if before[p] != after[p]}
        self.assertEqual(changed_files, {"campaign.json", "records/sources.json", "sources/archive.html"})
        self.assertEqual(set(before), set(after))
        c = Campaign(self.root)
        self.assertIn("eastern door is open", render(c.prepare("site")))
        self.assertEqual(c.owner("sources")[-1]["adoption"], "modified; see repair-rule")
        menu = next(r for r in source_menu(c, "site")["sources"] if r["ref"] == "workshop")
        self.assertEqual(menu["source_id"], "archive")
        self.assertEqual(menu["completeness"], "complete-field")
        self.assertEqual(menu["adoption"], "modified; see repair-rule")
        self.assertFalse(c.audit()["errors"])

    def test_refresh_blocks_moved_key_stale_hash_wrong_identity_and_incomplete_capture(self):
        before = self.snapshot()
        cases = [
            (receipts("<h1>Archive</h1><p>No workshop heading remains.</p>"), self.entry["sha256"]),
            (receipts(self.original), "0" * 64),
            (receipts(self.original, "WRONG-OBJECT"), self.entry["sha256"]),
            ([], self.entry["sha256"]),
        ]
        for rows, expected in cases:
            with self.subTest(rows=rows, expected=expected), self.assertRaises(ValueError):
                refresh_source(self.root, rows, "archive", expected, apply=True)
            self.assertEqual(before, self.snapshot())

    def test_duplicate_source_identity_is_rejected_even_with_a_new_name(self):
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "already registered"):
            import_source(self.root, receipts(self.original), "duplicate", "New label", "TEST-GAME", "handout", "test", "original")
        self.assertEqual(before, self.snapshot())

    def test_unchanged_refresh_writes_nothing_and_cli_defaults_to_preview(self):
        before = self.snapshot()
        self.assertFalse(refresh_source(self.root, receipts(self.original), "archive", self.entry["sha256"], True)["changed"])
        incoming = Path(self.tmp.name) / "slices.json"
        write_json(incoming, receipts(self.original.replace("sealed", "open")))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root), "source-refresh", "--id", "archive", "--receipts", str(incoming), "--expect", self.entry["sha256"]]), 0)
        self.assertEqual(before, self.snapshot())

    def test_discovery_cannot_bypass_source_hash_or_leak_unselected_source_body(self):
        path = self.root / "sources/archive.html"
        path.write_text(self.original + "<p>Unverified secret addition.</p>", encoding="utf-8")
        result = Campaign(self.root).discover("Unverified secret addition")
        self.assertFalse(any(r["path"] == "sources/archive.html" for r in result["candidates"]))
        self.assertTrue(any("hash changed" in g["error"] for g in result["gaps"]))

    def test_stable_refs_follow_consolidated_owners_and_keep_character_reasoning(self):
        c = Campaign(self.root)
        old = self.root / "records/CHARACTERS.md"
        body = old.read_text(encoding="utf-8")
        new = self.root / "records/PEOPLE.md"
        new.write_text(body.replace("## Specialist", "## Engineer"), encoding="utf-8")
        old.unlink()
        for ref in c.refs.values():
            if ref.get("path") == "records/CHARACTERS.md":
                ref["path"] = "records/PEOPLE.md"
                if ref.get("section") == "Specialist":
                    ref["section"] = "Engineer"
        write_json(self.root / "campaign.json", c.config)
        c = Campaign(self.root)
        for plan in [c.prepare("specialist"), c.recover("context"), c.recover("fresh")]:
            text = render(plan)
            self.assertIn("After the apprentice identified a fault they missed", text)
            self.assertIn("asking for observations before giving instructions", text)
            self.assertIn("I kept a place for your tools", text)
            self.assertNotIn("records/CHARACTERS.md", {e["owner"] for e in plan["entries"]})
        self.assertFalse(c.audit()["errors"])

    def test_cleanup_retrieves_integration_and_dormant_operation_routes_are_audited(self):
        c = Campaign(self.root)
        self.assertIn("records-integration", {e["ref"] for e in c.recover("review", "cleanup")["entries"]})
        ops = c.owner("operations")
        ops[0].update(status="complete", refs=["missing-relocated-evidence"])
        write_json(self.root / "records/operations.json", ops)
        self.assertTrue(any("missing-relocated-evidence" in e for e in c.audit()["errors"]))

    def test_nested_json_withdrawn_branch_cannot_hide_behind_indentation(self):
        c = Campaign(self.root)
        write_json(self.root / "history/events.json", {"kept": {"event": "An accepted delivery"}, "withdrawn": {"event": "A rejected outcome"}})
        c.refs.update({"events": {"path": "history/events.json"},
                       "kept": {"path": "history/events.json", "pointer": "/kept"},
                       "withdrawn": {"path": "history/events.json", "pointer": "/withdrawn", "status": "superseded"}})
        with self.assertRaisesRegex(ValueError, "contains inactive"):
            c.read("events")
        self.assertIn("accepted delivery", c.read("kept"))


class PublicationTests(unittest.TestCase):
    def test_external_terms_detect_leak_in_index_and_history_without_printing_terms(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.DEVNULL)
            git("init")
            git("config", "user.name", "Synthetic tester")
            git("config", "user.email", "tester@example.invalid")
            term = "Private Navigator"
            terms = root / "terms.txt"
            terms.write_text(term + "\n", encoding="utf-8")
            file = root / "README.md"
            file.write_text(term, encoding="utf-8")
            git("add", "README.md")
            file.write_text("Clean working copy", encoding="utf-8")
            with patch.object(check_distribution, "ROOT", root), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(check_distribution.main(["--private-terms", str(terms), "--staged"]), 1)
                self.assertNotIn(term, output.getvalue())
            git("commit", "-m", "Synthetic fixture")
            git("add", "README.md")
            git("commit", "-m", "Clean current content")
            with patch.object(check_distribution, "ROOT", root), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(check_distribution.main(["--private-terms", str(terms), "--history"]), 1)
                self.assertIn("Private-term match", output.getvalue())
                self.assertNotIn(term, output.getvalue())


if __name__ == "__main__":
    unittest.main()
