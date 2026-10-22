import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from gm_framework.bootstrap import initialize, write_json
from gm_framework.cli import main
from gm_framework.demo import build_demo
from gm_framework.sources import assemble, import_source
from gm_framework.store import Campaign, digest, inside, manifest, read_json, render


class FrameworkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = build_demo(self.base / "campaign")
        self.c = Campaign(self.root)

    def change_config(self):
        write_json(self.root / "campaign.json", self.c.config)
        self.c = Campaign(self.root)

    def test_two_settings_have_independent_identity_rules_and_full_profiles(self):
        other = Campaign(build_demo(self.base / "orbital", "orbital"))
        for c, name, absent in [(self.c, "Mira", "Ori"), (other, "Ori", "Mira")]:
            text = render(c.recover("fresh"))
            self.assertIn(name, text)
            self.assertNotIn(absent + " repairs", text)
            for meaningful in ["distant sibling", "dry", "asking for observations", "not received the test result"]:
                self.assertIn(meaningful, text)
            self.assertFalse(c.audit()["errors"])
        self.assertNotEqual(self.c.config["rules_system"], other.config["rules_system"])

    def test_required_parent_original_and_topical_supplement_dependencies(self):
        core = self.c.prepare("site")
        core_ids = {e["ref"] for e in core["entries"]}
        self.assertTrue({"work-site", "regional-context", "source-site"} <= core_ids)
        self.assertNotIn("supplement", core_ids)
        work = self.c.prepare("site", "repair")
        self.assertIn("supplement", {e["ref"] for e in work["entries"]})
        self.assertIn("not adopted", render(work))
        self.assertEqual(next(e for e in work["entries"] if e["ref"] == "supplement")["status"], "source")

    def test_profiles_survive_departure_without_aliasing_related_characters(self):
        state = self.c.owner("state")
        state["party"] = ["pc"]
        state["scene"]["participants"] = ["pc"]
        write_json(self.root / "records/state.json", state)
        self.assertIn("distant sibling", render(self.c.prepare("specialist")))
        self.assertEqual(self.c.resolve("Tamsin"), "pc")
        self.c.entities["ally"]["aliases"].append("Tamsin")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            self.c.resolve("Tamsin")

    def test_early_return_clock_review_and_conditional_duties_do_not_advance_time(self):
        before = (self.root / "records/state.json").read_bytes()
        attention = self.c.attention(500, "site")
        self.assertIn("dependent destination or event", attention["operations"][0]["attention_reasons"])
        self.assertNotIn("due or overdue clock checkpoint", attention["operations"][0]["attention_reasons"])
        self.assertIn("due or overdue clock checkpoint", self.c.attention(540)["operations"][0]["attention_reasons"])
        self.assertEqual(self.c.attention(1100)["review_boundaries"], [1080])
        self.assertEqual((self.root / "records/state.json").read_bytes(), before)
        with self.assertRaises(ValueError):
            self.c.attention(100)

    def test_expired_review_coverage_and_partial_phase_remain_visible(self):
        state = self.c.owner("state")
        state["reviews"] = {"through_tick": 0, "partial": {"tick": 360, "completed": ["orientation"]}}
        write_json(self.root / "records/state.json", state)
        attention = self.c.attention()
        self.assertEqual(attention["review_boundaries"], [360])
        self.assertEqual(attention["partial_review"]["completed"], ["orientation"])

    def test_full_context_scope_hash_reuse_changes_only_changed_evidence(self):
        plan = self.c.prepare("ally")
        saved = manifest(plan, "scene-session-1", "changed premises checked")
        reused = render(plan, saved, "scene-session-1", invalidation="changed premises checked")
        self.assertNotIn("draws unfamiliar birds", reused)
        self.assertIn("draws unfamiliar birds", render(plan, saved, "new-context"))
        path = self.root / "records/CHARACTERS.md"
        path.write_text(path.read_text(encoding="utf-8").replace("dry", "understated"), encoding="utf-8")
        changed = self.c.prepare("ally")
        text = render(changed, saved, "scene-session-1", invalidation="changed premises checked")
        self.assertIn("understated", text)
        self.assertIn("Reuse invalidated", text)
        # A newly required dependency invalidates the old selection, even if old bodies match.
        self.c.entities["ally"]["required"].append("accepted-visit")
        self.assertIn("Current boundary", render(self.c.prepare("ally"), saved, "scene-session-1"))

    def test_no_truncation_and_invalid_part_rejected(self):
        plan = self.c.prepare("ally")
        menu = render(plan, list_parts=True)
        self.assertNotIn("draws unfamiliar birds", menu)
        combined = "\n".join(render(plan, part=i) for i in range(1, len(plan["entries"]) + 1))
        self.assertIn("draws unfamiliar birds", combined)
        with self.assertRaises(ValueError):
            render(plan, part=999)

    def test_missing_dependency_and_visual_geometry_are_not_ready(self):
        visual = self.c.prepare("site", "approach")
        self.assertEqual(visual["gaps"][0]["kind"], "visual-inspection")
        self.c.refs["work-site"]["dependencies"].append({"ref": "missing", "required": True, "why": "Test gap"})
        with self.assertRaisesRegex(ValueError, "Missing dependency"):
            self.c.prepare("site")
        self.assertTrue(self.c.audit()["errors"])

    def test_dependencies_terminate_cycles_and_report_reverse_impact(self):
        self.c.refs["source-site"]["dependencies"] = [{"ref": "work-site", "required": True, "why": "Reverse link"}]
        plan = self.c.prepare("site")
        self.assertEqual(sum(e["ref"] == "work-site" for e in plan["entries"]), 1)
        self.assertIn("site", self.c.impact("source-site")["entities"])

    def test_rejected_records_excluded_and_unrouted_accepted_history_discoverable(self):
        (self.root / "rejected").mkdir()
        (self.root / "rejected/old.md").write_text("unicorn", encoding="utf-8")
        self.c.refs["old"] = {"path": "rejected/old.md", "status": "superseded"}
        (self.root / "history/NEW.md").write_text("# Accepted return\nA unicorn was seen.", encoding="utf-8")
        matches = self.c.discover("unicorn")["candidates"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["path"], "history/NEW.md")
        # A new section in an already routed document must also remain discoverable.
        with (self.root / "records/CHARACTERS.md").open("a", encoding="utf-8") as handle:
            handle.write("\n\n## New arrival\nAn astronomer studies pulsars.\n")
        self.assertTrue(any(m["path"] == "records/CHARACTERS.md" for m in self.c.discover("pulsars")["candidates"]))
        with self.assertRaises(ValueError):
            self.c.read("old")
        with self.assertRaises(ValueError):
            self.c.path("rejected/old.md")

    def test_path_escape_and_ambiguous_headings_rejected(self):
        for path in ["../outside.md", "C:/secret.md", "/etc/passwd", "..\\outside.md"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                inside(self.root, path)
        self.c.refs["bad"] = {"path": "records/CHARACTERS.md", "section": "Not present"}
        with self.assertRaises(ValueError):
            self.c.read("bad")

    def test_authoritative_guarded_update_and_stale_write_rejection(self):
        old = (self.root / "records/operations.json").read_text(encoding="utf-8")
        new = self.c.owner("operations")
        new[0]["last_step"] = "Seal fitted; pressure test pending"
        proposal = self.base / "proposal.json"
        write_json(proposal, new)
        args = ["--root", str(self.root), "update", "operations", "--from-file", str(proposal), "--expect", digest(old)]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(args), 0)
            self.assertEqual(main(args), 2)
        self.assertIn("pressure test pending", render(self.c.prepare("site")))

    def test_source_byte_change_detected_and_no_init_overwrite(self):
        self.c.refs["source-site"]["sha256"] = digest((self.root / "sources/original.md").read_text(encoding="utf-8"))
        with (self.root / "sources/original.md").open("a", encoding="utf-8") as handle:
            handle.write("Changed")
        with self.assertRaisesRegex(ValueError, "hash changed"):
            self.c.read("source-site")
        with self.assertRaises(ValueError):
            initialize(self.root, "x", "x", "x", "x", "x")


class SourceTests(unittest.TestCase):
    def receipts(self, text="A\U0001f426B", cut=2):
        encoded = text.encode("utf-16-le")
        total = len(encoded) // 2
        chunks = [encoded[:cut*2], encoded[cut*2:]]
        offset = 0
        rows = []
        for chunk in chunks:
            end = offset + len(chunk)//2
            rows.append({"id": "SYNTHETIC", "field": "gmnotes", "view": "raw", "fingerprint": "test",
                         "rawLength": total, "total": total, "offset": offset, "next": end if end < total else None,
                         "text": chunk.decode("utf-16-le", errors="surrogatepass")})
            offset = end
        return rows

    def test_utf16_split_surrogates_and_incomplete_or_changed_receipts(self):
        rows = self.receipts()
        self.assertEqual(assemble(rows)[0], "A\U0001f426B")
        with self.assertRaises(ValueError):
            assemble(rows[:1])
        with self.assertRaises(ValueError):
            assemble(rows + rows[:1])
        rows[1]["fingerprint"] = "changed"
        with self.assertRaises(ValueError):
            assemble(rows)

    def test_source_import_provenance_no_implicit_adoption_or_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = initialize(Path(tmp)/"private", "Custom", "Player", "Hero", "Any", "Any")
            entry = import_source(root, self.receipts(), "test-source", "Synthetic", "TEST-GAME", "handout", "test", "original")
            self.assertEqual(entry["adoption"], "unassessed")
            self.assertFalse(entry["redistribute"])
            self.assertEqual(Campaign(root).read("test-source"), "A\U0001f426B")
            self.assertFalse(Campaign(root).audit()["errors"])
            with self.assertRaises(ValueError):
                import_source(root, self.receipts(), "test-source", "Synthetic", "TEST-GAME", "handout", "test", "original")
            crlf = self.receipts("A\r\nB", 2)
            for row in crlf:
                row["id"] = "SYNTHETIC-NEWLINES"
            import_source(root, crlf, "crlf-source", "Newlines", "TEST-GAME", "handout", "test", "original")
            self.assertEqual(Campaign(root).read("crlf-source"), "A\r\nB")


if __name__ == "__main__":
    unittest.main()
