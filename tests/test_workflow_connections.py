"""Regression scenarios for capabilities lost in the first public extraction."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from gm_framework.authoring import add_character, link_source, upgrade
from gm_framework.bootstrap import initialize, write_json
from gm_framework.cli import main
from gm_framework.demo import build_demo
from gm_framework.sources import import_source, source_menu
from gm_framework.store import Campaign, digest, manifest, read_json, render


class WorkflowConnections(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = build_demo(Path(self.tmp.name) / "campaign")
        self.c = Campaign(self.root)

    def save(self):
        write_json(self.root / "campaign.json", self.c.config)
        self.c = Campaign(self.root)

    def test_phases_have_distinct_work_and_resolve_no_fiction(self):
        snapshot = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        expected = {"orientation": "foundation", "preparation": "world-catalogue",
                    "world": "world-strategy", "cleanup": "records-cleanup", "scene": "play-context"}
        for phase, ref in expected.items():
            plan = self.c.recover("review", phase)
            self.assertIn(ref, {e["ref"] for e in plan["entries"]})
            self.assertEqual(plan["request"]["phase"], phase)
        self.assertEqual(snapshot, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})
        with self.assertRaises(ValueError):
            self.c.recover("context", reuse_procedures=True)

    def test_rest_resolution_and_close_surface_actual_duties_and_history(self):
        for activity, expected in [("rest", "play-rest"), ("resolution", "play-development"), ("scene-close", "records-cleanup")]:
            plan = self.c.prepare("pc", actors=["ally"], activity=activity)
            ids = {e["ref"] for e in plan["entries"]}
            self.assertIn(expected, ids)
            self.assertIn("development", ids)
            self.assertIn("accepted-visit", ids)
            self.assertIn("I kept a place for your tools", render(plan))
        self.assertEqual(self.c.owner("state")["resources"], {})

    def test_causal_history_update_routes_to_profiles_and_work_without_copying_it(self):
        self.c.entities["ally"].pop("profile")
        self.c.entities["ally"]["profile_refs"] = ["ally-profile"]
        self.c.config["focused_refresh"]["relationship"] = {"entities": ["ally"], "topics": ["core"],
            "refs": ["accepted-visit"], "why": "Recheck the actual promise with full profile retained"}
        self.save()
        operations = self.c.owner("operations")
        operations[0]["refs"] = ["accepted-visit"]
        write_json(self.root / "records/operations.json", operations)
        impact = self.c.impact("accepted-visit")
        self.assertIn("ally", impact["entities"])
        self.assertIn(operations[0]["id"], impact["operations"])
        self.assertIn("relationship", impact["refreshes"])
        history = self.root / self.c.refs["accepted-visit"]["path"]
        history.write_text(history.read_text(encoding="utf-8").replace("I kept a place for your tools", "I kept a place for your maps"), encoding="utf-8")
        text = render(self.c.prepare("ally"))
        self.assertIn("I kept a place for your maps", text)
        self.assertNotIn("I kept a place for your tools", text)
        self.assertIn("ally-profile", {e["ref"] for e in self.c.prepare("ally")["entries"]})

    def test_unpromoted_commitment_surfaces_on_early_return_with_empty_queue(self):
        write_json(self.root / "records/operations.json", [])
        path = self.root / "records/SCENE.md"
        path.write_text(path.read_text(encoding="utf-8").replace("## Commitments", "## Commitments\n\nThe steward promised a confidential answer before the party returns."), encoding="utf-8")
        plan = self.c.prepare("site", destination="site", until=500)
        text = render(plan)
        self.assertIn("confidential answer", text)
        self.assertEqual(text.count("The steward promised"), 1, "Contained selectors must not duplicate their owner")
        self.assertEqual(plan["attention"]["operations"], [])

    def test_independent_actor_event_and_parent_sources_reach_world_review(self):
        add_character(self.root, "envoy", "Sable", sources=["source-site"], history=["accepted-visit"])
        self.c = Campaign(self.root)
        self.c.config["review_actors"] = ["envoy"]
        self.save()
        operations = self.c.owner("operations")
        operations.append({"id": "envoy-hearing", "kind": "source-event", "actors": ["envoy"], "cadence": "ACTIVE",
            "status": "deferred", "last_step": "No invitation issued", "condition": "Reconsider after repair report",
            "refs": ["work-site", "repair-rule"], "purpose": "Hear competing petitions", "means": "Local audience chamber"})
        write_json(self.root / "records/operations.json", operations)
        plan = self.c.recover("review", "world")
        ids = {e["ref"] for e in plan["entries"]}
        self.assertTrue({"envoy-profile", "accepted-visit", "source-site", "regional-context", "supplement", "world-events"} <= ids)
        self.assertNotIn("envoy", self.c.owner("state")["scene"]["participants"])

    def test_focused_refresh_keeps_qualifiers_and_actual_actor_full_context(self):
        self.c.refs["ally-knowledge"] = {"path": "records/CHARACTERS.md", "section": "Knowledge",
            "dependencies": [{"ref": "accepted-visit", "required": True, "why": "Actual delivery did not establish a test outcome"}]}
        self.c.config["focused_refresh"]["repair-knowledge"] = {"entities": ["ally"], "topics": ["core"],
            "refs": ["ally-knowledge"], "why": "Answer a narrow factual question after full character recovery"}
        self.save()
        narrow = self.c.prepare("specialist", refresh="repair-knowledge")
        self.assertNotIn("ally-profile", {e["ref"] for e in narrow["entries"]})
        self.assertIn("accepted-visit", {e["ref"] for e in narrow["entries"]})
        full = self.c.prepare("ally", actors=["ally"], refresh="repair-knowledge")
        self.assertIn("distant sibling", render(full))
        self.assertEqual(render(full).count("They have not received the test result"), 1)
        with self.assertRaises(ValueError):
            self.c.prepare("pc", refresh="repair-knowledge")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root), "prepare", "ally", "--refresh", "repair-knowledge"]), 2)

    def test_minor_departed_actor_uses_exact_accepted_scene_without_fake_profile(self):
        self.c.entities["apprentice"] = {"name": "Apprentice", "kind": "character", "importance": "minor",
            "history": ["accepted-visit"], "topics": {"core": []}}
        self.save()
        text = render(self.c.prepare("apprentice"))
        self.assertIn("apprentice helped locate", text)
        self.assertNotIn("apprentice", self.c.owner("state")["party"])
        self.assertFalse(self.c.audit()["errors"])

    def test_inactive_child_cannot_leak_through_parent_read_or_broad_discovery(self):
        path = self.root / "history/ACCEPTED.md"
        with path.open("a", encoding="utf-8") as handle:
            handle.write("\n\n## Withdrawn branch\nThe comet destroyed the city.\n")
        self.c.refs["withdrawn"] = {"path": "history/ACCEPTED.md", "section": "Withdrawn branch", "status": "superseded"}
        self.save()
        with self.assertRaisesRegex(ValueError, "contains inactive"):
            self.c.read("history")
        candidates = self.c.discover("comet")
        self.assertEqual(candidates["candidates"], [])
        self.assertTrue(candidates["gaps"])
        self.assertIn("I kept a place", self.c.read("accepted-visit"))

    def test_new_unrouted_evidence_or_new_boundary_invalidates_byte_reuse(self):
        before = self.c.prepare("ally")
        saved = manifest(before, "one scene", "premises checked")
        self.assertIn("Unchanged bytes omitted", render(before, saved, "one scene", invalidation="premises checked"))
        (self.root / "history/NEW.md").write_text("# New accepted exchange\nA prior promise was qualified.\n", encoding="utf-8")
        self.assertIn("Reuse invalidated", render(self.c.prepare("ally"), saved, "one scene", invalidation="premises checked"))
        plan = self.c.prepare("ally")
        saved = manifest(plan, "one scene", "premises checked")
        state = self.c.owner("state")
        state["time"]["tick"] += 1
        write_json(self.root / "records/state.json", state)
        self.assertIn("Reuse invalidated", render(self.c.prepare("ally"), saved, "one scene", invalidation="premises checked"))

    def test_source_capture_to_real_entity_route_includes_readable_complete_sections(self):
        raw = '<h1>Archive</h1><h2>Envoy</h2><p>Protects the witness, but distrusts the council.</p><h2>Region</h2><p>Another place.</p>'
        length = len(raw.encode('utf-16-le')) // 2
        rows = [{"id": "SYNTHETIC", "field": "gmnotes", "view": "raw", "fingerprint": "synthetic",
                 "total": length, "rawLength": length, "offset": 0, "next": None, "text": raw}]
        import_source(self.root, rows, "archive-source", "Original archive", "DEMO", "handout", "Synthetic", "original")
        add_character(self.root, "envoy", "Sable")
        link_source(self.root, "archive-source", "envoy", heading="Envoy", key="envoy-source", required=True)
        c = Campaign(self.root)
        text = render(c.prepare("envoy"))
        self.assertIn("Protects the witness, but distrusts the council", text)
        self.assertNotIn("Another place.", text)
        self.assertEqual(source_menu(c, "envoy")["sources"][0]["ref"], "envoy-source")
        self.assertEqual(c.owner("sources")[-1]["adoption"], "unassessed")
        # Bold/paragraph area keys can use exact literal bounds without a guessed heading parser.
        link_source(self.root, "archive-source", "envoy", start="Protects", end="## Region", key="literal-key", topic="recall")
        self.assertNotIn("Another place.", Campaign(self.root).read("literal-key"))

    def test_upgrade_preview_and_customization_conflict_preserve_state(self):
        config = self.c.config
        config["workflow_revision"] = 1
        config.pop("review_phases")
        config.pop("activities")
        self.save()
        state = (self.root / "records/state.json").read_bytes()
        preview = upgrade(self.root)
        self.assertFalse(preview["applied"])
        self.assertNotIn("review_phases", read_json(self.root / "campaign.json"))
        self.assertTrue(upgrade(self.root, apply=True)["applied"])
        self.assertEqual((self.root / "records/state.json").read_bytes(), state)
        self.assertFalse(Campaign(self.root).audit()["errors"])
        path = self.root / "DM_WORKFLOW.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nCustom instruction.\n", encoding="utf-8")
        result = upgrade(self.root, apply=True)
        self.assertIn("DM_WORKFLOW.md", result["conflicts"])
        self.assertIn("Custom instruction", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
