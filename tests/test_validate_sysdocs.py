"""Exercise the actual validator on source/document trees, including scoped edits."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_sysdocs", ROOT / "scripts/validate-sysdocs.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class SysDocsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project"
        shutil.copytree(ROOT / "tests/fixtures/sysdocs/schema2", self.project)
        self.docs = self.project / "SysDocs"

    def edit(self, path, old, new):
        target = self.docs / path
        target.write_text(target.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")

    def report(self, *args):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/validate-sysdocs.py"), str(self.docs), *args], capture_output=True, text=True, encoding="utf-8")
        self.assertIn(result.returncode, (0, 2), result.stderr)
        return json.loads(result.stdout)

    def assert_rule(self, rule, *args):
        report = self.report(*args)
        self.assertEqual("FAILED", report["status"], report)
        self.assertIn(rule, {x["rule_id"] for x in report["issues"]})

    def test_schema2_links_to_source_and_external_authority_are_valid(self):
        report = self.report()
        self.assertEqual("COMPLETE", report["status"], report)
        self.assertEqual("INITIALIZED", report["inventory"])
        self.assertEqual("structure", report["validation_kind"])
        self.assertEqual("not_performed", report["content_verification"])
        self.assertTrue(report["unverified"])

    def test_legacy_layout_remains_readable_without_migration(self):
        root = ROOT / "tests/fixtures/sysdocs/initialized/SysDocs"
        before = {p: p.read_bytes() for p in root.rglob("*.md")}
        status, issues = VALIDATOR.validate(root)
        self.assertEqual("COMPLETE", status, issues)
        self.assertEqual(before, {p: p.read_bytes() for p in root.rglob("*.md")})

    def test_missing_library_is_not_complete(self):
        shutil.rmtree(self.docs)
        report = self.report()
        self.assertEqual("UNINITIALIZED", report["inventory"])
        self.assertNotEqual("COMPLETE", report["status"])

    def test_vibe_only_does_not_initialize_library(self):
        shutil.rmtree(self.docs)
        (self.docs / "VibeCoding").mkdir(parents=True)
        (self.docs / "VibeCoding/idea.md").write_text("---\nschema: 2\ndoc_type: vibe\nupdated: 2026-09-16\n---\n# Proposal\n", encoding="utf-8")
        self.assertEqual("UNINITIALIZED", self.report()["inventory"])

    def test_missing_required_navigation_is_partial_inventory(self):
        (self.docs / "architecture/overview.md").unlink()
        self.assertEqual("PARTIAL-INITIALIZED", self.report()["inventory"])
        self.assert_rule("SYSDOC-LAYOUT-01")

    def test_missing_schema2_entry_cannot_pass_full_validation(self):
        (self.docs / "README.md").unlink()
        self.assert_rule("SYSDOC-LAYOUT-01")
        self.assertEqual("PARTIAL-INITIALIZED", self.report()["inventory"])

    def test_required_fact_pages_cannot_be_replaced_with_redirects(self):
        for name, target in (("README.md", "architecture/overview.md"),
                             ("architecture/overview.md", "modules/order.md"),
                             ("files/README.md", "order.md")):
            with self.subTest(page=name):
                path = self.docs / name
                original = path.read_bytes()
                try:
                    path.write_text(f"# Moved\n[Read here]({target})\n", encoding="utf-8")
                    (self.project / "src/order/unindexed.py").write_text("class New: pass\n")
                    self.assert_rule("SYSDOC-FM-01")
                finally:
                    path.write_bytes(original)
                    (self.project / "src/order/unindexed.py").unlink()

    def test_scoped_new_module_requires_its_file_index(self):
        content = (self.docs / "architecture/modules/order.md").read_text(encoding="utf-8")
        (self.docs / "architecture/modules/new.md").write_text(
            content.replace("module_id: order", "module_id: new"), encoding="utf-8")
        with (self.docs / "README.md").open("a", encoding="utf-8") as output:
            output.write("\n[New module](architecture/modules/new.md)\n")
        self.assert_rule("SYSDOC-MAN-01", "--files", "SysDocs/README.md",
                         "SysDocs/architecture/modules/new.md")

    def test_scoped_new_file_index_requires_its_module(self):
        content = (self.docs / "files/order.md").read_text(encoding="utf-8")
        (self.docs / "files/new.md").write_text(
            content.replace("module_id: order", "module_id: new")
                   .replace("| order |", "| new |"), encoding="utf-8")
        self.assert_rule("SYSDOC-MAN-01", "--files", "SysDocs/files/new.md")

    def test_scoped_module_pair_removal_is_valid(self):
        for name in ("architecture/modules/order.md", "files/order.md"):
            (self.docs / name).unlink()
        (self.project / "src/order/service.py").unlink()
        # Removed pages may remain in --files, but all incoming links are repaired.
        for path in self.docs.rglob("*.md"):
            content = path.read_text(encoding="utf-8")
            content = "\n".join(line for line in content.splitlines()
                                if "order.md)" not in line)
            path.write_text(content, encoding="utf-8")
        report = self.report("--files", "SysDocs/README.md",
                             "SysDocs/architecture/modules/order.md", "SysDocs/files/order.md")
        self.assertEqual("COMPLETE", report["status"], report)
        self.assertEqual("COMPLETE", self.report()["status"])

    def test_future_schema_is_rejected_without_modification(self):
        self.edit("architecture/modules/order.md", "schema: 2", "schema: 99")
        before = {p: p.read_bytes() for p in self.docs.rglob("*.md")}
        self.assert_rule("SYSDOC-FM-02")
        self.assertEqual(before, {p: p.read_bytes() for p in self.docs.rglob("*.md")})

    def test_non_mapping_metadata_is_reported_not_crashed(self):
        (self.docs / "architecture/overview.md").write_text("---\n- invalid\n---\n", encoding="utf-8")
        self.assert_rule("SYSDOC-FM-01")

    def test_missing_summary_fails_for_generated_fact_page(self):
        self.edit("architecture/modules/order.md", "## 检索摘要", "## Other")
        self.assert_rule("SYSDOC-SUMMARY-01")

    def test_summary_extraction_does_not_emit_full_body(self):
        self.edit("architecture/flows/payment.md", "Order creation precedes", "BODY_ONLY_SENTINEL Order creation precedes")
        report = self.report("--summaries")
        self.assertIn("OrderService", json.dumps(report))
        self.assertNotIn("BODY_ONLY_SENTINEL", json.dumps(report))
        self.assertTrue(report["summaries"])

    def test_summary_extraction_reports_legacy_fallback(self):
        (self.docs / "decisions").mkdir()
        (self.docs / "decisions/old.md").write_text("# Historical ADR\nAccepted rationale.\n", encoding="utf-8")
        report = self.report("--summaries")
        self.assertIn("SysDocs/decisions/old.md", report["fallback_required"])
        self.assertEqual("COMPLETE", self.report()["status"])

    def test_new_business_file_under_components_is_not_excluded(self):
        directory = self.project / "src/order/components"
        directory.mkdir()
        (directory / "pay.py").write_text("class Payment: pass\n")
        self.assert_rule("SYSDOC-COVERAGE-01")

    def test_duplicate_file_ownership_is_rejected(self):
        self.edit("files/order.md", "| `src/order/service.py`", "| `src/order/service.py` | Duplicate ownership | order |\n| `src/order/service.py`")
        self.assert_rule("SYSDOC-COVERAGE-02")

    def test_deleted_or_renamed_source_requires_index_update(self):
        (self.project / "src/order/service.py").rename(self.project / "src/order/renamed.py")
        self.assert_rule("SYSDOC-PATH-01")

    def test_source_scope_cannot_escape_project(self):
        self.edit("files/README.md", "src/order/", "../")
        self.assert_rule("SYSDOC-PATH-02")

    def test_scoped_validation_includes_incoming_links(self):
        report = self.report("--files", "SysDocs/architecture/modules/order.md")
        self.assertEqual("COMPLETE", report["status"], report)
        self.assertEqual("affected", report["scope"]["mode"])
        self.assertIn("SysDocs/architecture/flows/payment.md", report["scope"]["documents"])

    def test_unrelated_broken_doc_does_not_block_scoped_delivery(self):
        other = self.docs / "architecture/modules/unrelated.md"
        other.write_text("---\nschema: 2\ndoc_type: architecture\n---\n# Broken\n", encoding="utf-8")
        report = self.report("--files", "SysDocs/architecture/flows/payment.md")
        self.assertEqual("COMPLETE", report["status"], report)
        self.assertNotIn("SysDocs/architecture/modules/unrelated.md", report["scope"]["documents"])
        self.assertNotEqual("COMPLETE", self.report()["status"])

    def test_deleted_document_in_scope_still_checks_incoming_links(self):
        (self.docs / "architecture/modules/order.md").unlink()
        self.assert_rule("SYSDOC-LINK-01", "--files", "SysDocs/architecture/modules/order.md")

    def test_external_authority_link_stays_inside_project(self):
        self.edit("README.md", "../docs/adr/ADR-001.md", "../../outside.md")
        self.assert_rule("SYSDOC-LINK-02")

    def test_human_markers_are_preserved_and_invalid_pairs_rejected(self):
        self.edit("architecture/modules/order.md", "<!-- human:end -->", "")
        self.assert_rule("SYSDOC-HUMAN-01")

    def test_working_tree_requires_evidence_beyond_head(self):
        self.edit("README.md", "source_scope: unversioned", "source_scope: committed+working-tree\ngenerated_from: 1234567")
        self.assert_rule("SYSDOC-BASELINE-01")

    def test_historical_reports_do_not_claim_new_protocol_conformance(self):
        directory = self.docs / ".meta/reports"
        directory.mkdir(parents=True)
        (directory / "old.md").write_text("# Old schema report\nNot current validation evidence.\n", encoding="utf-8")
        self.assertEqual("COMPLETE", self.report()["status"])

    def test_mixed_layout_with_old_body_requires_repair(self):
        shutil.copy(ROOT / "tests/fixtures/sysdocs/initialized/SysDocs/SYSTEM_ROOT.md", self.docs / "SYSTEM_ROOT.md")
        self.assert_rule("SYSDOC-LAYOUT-02")

    def test_migration_compatibility_link_is_allowed(self):
        (self.docs / "SYSTEM_ROOT.md").write_text("# Moved\n[New entry](README.md)\n", encoding="utf-8")
        self.assertEqual("COMPLETE", self.report()["status"])

    def test_malformed_type_and_url_are_reported_without_crashing(self):
        self.edit("architecture/modules/order.md", "doc_type: architecture", "doc_type: []")
        self.edit("README.md", "../docs/adr/ADR-001.md", "https://[")
        self.assert_rule("SYSDOC-FM-03")

    def test_local_file_index_checks_new_source_in_declared_scope(self):
        (self.project / "src/order/missing.py").write_text("class NewOrder: pass\n")
        self.assert_rule("SYSDOC-COVERAGE-01", "--files", "SysDocs/files/order.md")

    def test_schema1_proposal_is_preserved_in_migrated_library(self):
        directory = self.docs / "VibeCoding"
        directory.mkdir()
        (directory / "legacy.md").write_text("---\nschema: 1\ndoc_type: vibe\nstatus: draft\nvibe_id: legacy\n---\n# Unimplemented idea\n", encoding="utf-8")
        self.assertEqual("COMPLETE", self.report()["status"])

    def test_legacy_library_accepts_new_schema2_supplementary_pages(self):
        shutil.rmtree(self.docs)
        shutil.copytree(ROOT / "tests/fixtures/sysdocs/initialized/SysDocs", self.docs)
        for directory, doc_type in (("VibeCoding", "vibe"), ("specs", "spec"), ("decisions", "decision")):
            folder = self.docs / directory
            folder.mkdir(exist_ok=True)
            path = folder / "new.md"
            path.write_text(
                f"---\nschema: 2\ndoc_type: {doc_type}\nupdated: 2026-09-16\n"
                "status: draft\nvibe_id: new\ntargets: []\n"
                "implementation:\n  status: unknown\nmerge:\n  status: pending\n"
                "---\n# Proposal\n\n## 检索摘要\n\nProposed change, not implemented.\n",
                encoding="utf-8")
            with self.subTest(doc_type=doc_type):
                report = self.report("--files", f"SysDocs/{directory}/new.md")
                self.assertEqual("COMPLETE", report["status"], report)
        before = {p: p.read_bytes() for p in self.docs.rglob("*.md")}
        report = self.report()
        self.assertEqual("COMPLETE", report["status"], report)
        self.assertEqual("INITIALIZED", report["inventory"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.docs.rglob("*.md")})
        self.edit("VibeCoding/new.md", "schema: 2", "schema: 99")
        self.assert_rule("SYSDOC-FM-02", "--files", "SysDocs/VibeCoding/new.md")

    def test_legacy_library_still_rejects_in_place_fact_schema_upgrade(self):
        shutil.rmtree(self.docs)
        shutil.copytree(ROOT / "tests/fixtures/sysdocs/initialized/SysDocs", self.docs)
        self.edit("modules/order-service.md", "schema: 1", "schema: 2")
        self.assert_rule("SYSDOC-FM-02")

    def test_historical_authority_frontmatter_is_preserved_in_both_layouts(self):
        for legacy in (False, True):
            if legacy:
                shutil.rmtree(self.docs)
                shutil.copytree(ROOT / "tests/fixtures/sysdocs/initialized/SysDocs", self.docs)
            for directory in ("specs", "decisions"):
                with self.subTest(legacy=legacy, directory=directory):
                    folder = self.docs / directory
                    folder.mkdir(exist_ok=True)
                    path = folder / "historical.md"
                    path.write_text("---\ntitle: Use SQL\nstatus: accepted\ndate: 2020-01-01\n"
                                    "---\n# Historical authority\nKeep accepted text intact.\n", encoding="utf-8")
                    before = path.read_bytes()
                    report = self.report()
                    self.assertEqual("COMPLETE", report["status"], report)
                    self.assertEqual(before, path.read_bytes())
                    self.edit(f"{directory}/historical.md", "title: Use SQL", "schema: 99\ntitle: Use SQL")
                    self.assert_rule("SYSDOC-FM-02")
                    path.write_bytes(before)

    def test_historical_authority_exemption_keeps_link_checks(self):
        (self.docs / "decisions").mkdir()
        (self.docs / "decisions/old.md").write_text(
            "---\ntitle: Old ADR\nstatus: accepted\n---\n[Missing](absent.md)\n", encoding="utf-8")
        self.assert_rule("SYSDOC-LINK-01")

    def test_unrelated_unreadable_authority_is_reported_outside_local_scope(self):
        for legacy in (False, True):
            if legacy:
                shutil.rmtree(self.docs)
                shutil.copytree(ROOT / "tests/fixtures/sysdocs/initialized/SysDocs", self.docs)
            with self.subTest(legacy=legacy):
                (self.docs / "decisions").mkdir(exist_ok=True)
                (self.docs / "decisions/old.md").write_bytes(b"\xff")
                target = "SysDocs/modules/order-service.md" if legacy else "SysDocs/architecture/flows/payment.md"
                report = self.report("--files", target)
                self.assertEqual("COMPLETE", report["status"], report)
                self.assertIn("SysDocs/decisions/old.md", {x["path"] for x in report["out_of_scope_issues"]})
                self.assertTrue(any("incoming links" in gap for gap in report["unverified"]))
                self.assert_rule("SYSDOC-FM-01")

    def test_requested_unreadable_document_blocks_local_validation(self):
        (self.docs / "architecture/flows/payment.md").write_bytes(b"\xff")
        self.assert_rule("SYSDOC-FM-01", "--files", "SysDocs/architecture/flows/payment.md")

    def test_unreadable_authority_linked_from_requested_page_is_required(self):
        (self.docs / "decisions").mkdir()
        (self.docs / "decisions/old.md").write_bytes(b"\xff")
        with (self.docs / "architecture/flows/payment.md").open("a", encoding="utf-8") as output:
            output.write("\n[Required decision](../../decisions/old.md)\n")
        self.assert_rule("SYSDOC-FM-01", "--files", "SysDocs/architecture/flows/payment.md")

    def test_unreadable_source_scope_is_required_for_local_file_index(self):
        (self.docs / "files/README.md").write_bytes(b"\xff")
        self.assert_rule("SYSDOC-FM-01", "--files", "SysDocs/files/order.md")

    def test_fact_page_cannot_bypass_checks_by_claiming_spec_type(self):
        self.edit("architecture/modules/order.md", "doc_type: architecture", "doc_type: spec")
        self.assert_rule("SYSDOC-FM-03")

    def test_unrelated_broken_link_on_incoming_navigation_is_not_in_scope(self):
        self.edit("README.md", "[Accepted decision](../docs/adr/ADR-001.md)", "[Unrelated old page](old-missing.md)")
        self.assertEqual("COMPLETE", self.report("--files", "SysDocs/architecture/modules/order.md")["status"])
        self.assert_rule("SYSDOC-LINK-01")

    def test_summary_output_redacts_possible_secrets(self):
        self.edit("README.md", "`OrderService` creates", "token=DEMO_SENTINEL_NOT_REAL `OrderService` creates")
        report = self.report("--summaries")
        self.assertEqual("FAILED", report["status"])
        self.assertNotIn("DEMO_SENTINEL_NOT_REAL", json.dumps(report))

    def test_path_alias_cannot_create_second_file_owner(self):
        self.edit("files/order.md", "| `src/order/service.py`", "| `src/order/../order/service.py` | Alias owner | order |\n| `src/order/service.py`")
        self.assert_rule("SYSDOC-COVERAGE-02")

    def test_file_responsibility_rows_cannot_name_directories(self):
        self.edit("files/order.md", "`src/order/service.py`", "`src/order/`")
        self.assert_rule("SYSDOC-PATH-01")

    def test_full_library_requires_reachable_navigation(self):
        self.edit("README.md", "## Navigation", "## Navigation\n\n```")
        with (self.docs / "README.md").open("a", encoding="utf-8") as output:
            output.write("\n```\n")
        self.assert_rule("SYSDOC-LAYOUT-01")
        self.assertEqual("PARTIAL-INITIALIZED", self.report()["inventory"])

    def test_iso_timestamp_is_valid_updated_metadata(self):
        self.edit("README.md", "updated: 2026-09-16", "updated: 2026-09-16T12:30:00+08:00")
        self.assertEqual("COMPLETE", self.report()["status"])

    def test_legacy_manifest_escape_is_rejected(self):
        shutil.rmtree(self.docs)
        shutil.copytree(ROOT / "tests/fixtures/sysdocs/initialized/SysDocs", self.docs)
        outside = self.project.parent / "outside.md"
        outside.write_text("---\nschema: 1\ndoc_type: page\nstatus: active\nmodule_id: order-service\npage_id: outside\n---\n", encoding="utf-8")
        self.edit("SYSTEM_ROOT.md", "pages: []", "pages: [../../outside.md]")
        self.assert_rule("SYSDOC-PATH-02")

    def test_legacy_null_manifest_is_reported_without_crashing(self):
        shutil.rmtree(self.docs)
        shutil.copytree(ROOT / "tests/fixtures/sysdocs/initialized/SysDocs", self.docs)
        self.edit("SYSTEM_ROOT.md", "modules:\n  - id: order-service\n    path: modules/order-service.md\n    pages: []", "modules: null")
        self.assert_rule("SYSDOC-FM-04")

    def test_invalid_yaml_date_returns_diagnostic(self):
        self.edit("README.md", "updated: 2026-09-16", "updated: 2026-99-99")
        self.assert_rule("SYSDOC-FM-01")

    def test_legacy_directory_page_and_invalid_encoding_return_diagnostics(self):
        shutil.rmtree(self.docs)
        shutil.copytree(ROOT / "tests/fixtures/sysdocs/initialized/SysDocs", self.docs)
        self.edit("SYSTEM_ROOT.md", "pages: []", "pages: [modules]")
        (self.docs / "bad.md").write_bytes(b"\xff")
        self.assert_rule("SYSDOC-MAN-03")

    def test_unrelated_exclusion_metadata_does_not_block_flow_scope(self):
        self.edit("files/README.md", "exclusions: []", "exclusions: {}")
        self.assertEqual("COMPLETE", self.report("--files", "SysDocs/architecture/flows/payment.md")["status"])

    def test_legacy_unrelated_navigation_defect_does_not_block_module_scope(self):
        shutil.rmtree(self.docs)
        shutil.copytree(ROOT / "tests/fixtures/sysdocs/initialized/SysDocs", self.docs)
        with (self.docs / "SYSTEM_ROOT.md").open("a", encoding="utf-8") as output:
            output.write("\n[Old unrelated link](missing.md)\n")
        self.assertEqual("COMPLETE", self.report("--files", "SysDocs/modules/order-service.md")["status"])


if __name__ == "__main__":
    unittest.main()
