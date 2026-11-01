import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
from jsonschema.exceptions import ValidationError
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("catalog", ROOT / "scripts/playwright_catalog.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PlaywrightCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        for name in ("playwright", "schema"):
            shutil.copytree(ROOT / name, self.source / name)
        self.dest = self.root / "release"

    def export(self):
        module.export(self.source, self.dest, module.REVISION)

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.dest.iterdir()}

    def test_six_ports_and_repeat_export_preserve_unrelated_files(self):
        self.export()
        self.assertEqual(len(list(self.dest.glob("recipe-pw__*.yaml"))), 6)
        self.assertFalse(list(self.dest.glob("*metadata*")))
        (self.dest / "keep.txt").write_text("keep")
        before = self.snapshot()
        self.export()
        self.assertEqual(before, self.snapshot())

    def test_refuses_mixed_unmanaged_schema_and_symlink_destinations(self):
        for name, data in (("bc-recipe__free.yaml", "legacy"),
                           ("recipe-pw__free.yaml", "unmanaged"),
                           (module.SCHEMA, "different")):
            with self.subTest(name=name):
                self.dest.mkdir(exist_ok=True)
                path = self.dest / name
                path.write_text(data)
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    self.export()
                self.assertEqual(before, self.snapshot())
                path.unlink()
        real = self.root / "real"
        real.mkdir()
        self.dest.rmdir()
        self.dest.symlink_to(real, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.export()

    def test_invalid_sources_do_not_change_previous_export(self):
        self.export()
        before = self.snapshot()
        path = self.source / "playwright/free/recipe-pw__free.yaml"
        original = path.read_bytes()
        for change in ("unknown", "DownloadAll", "download_all"):
            recipe = yaml.safe_load(original)
            recipe["services"][0]["steps"][0]["methods"][0]["method"] = change
            path.write_text(yaml.safe_dump(recipe))
            with self.assertRaises((ValueError, ValidationError)):
                self.export()
            self.assertEqual(before, self.snapshot())
        path.write_bytes(original)
        (path.parent / "recipe-pw__extra.yaml").write_bytes(original)
        with self.assertRaises(ValueError):
            self.export()
        self.assertEqual(before, self.snapshot())

    def test_missing_metadata_wrong_engine_and_duplicate_service_refused(self):
        self.export()
        before = self.snapshot()
        metadata = self.source / "playwright/free/metadata.yaml"
        data = metadata.read_bytes()
        metadata.unlink()
        with self.assertRaises(FileNotFoundError):
            self.export()
        metadata.write_bytes(data)
        with self.assertRaises(ValueError):
            module.export(self.source, self.dest, "selenium")
        shutil.copytree(metadata.parent, metadata.parent.parent / "duplicate")
        with self.assertRaises(ValueError):
            self.export()
        self.assertEqual(before, self.snapshot())

    def test_qualified_proof_is_bound_to_recipe_and_complete_counts(self):
        recipe = self.source / "playwright/free/recipe-pw__free.yaml"
        metadata = recipe.with_name("metadata.yaml")
        proof = yaml.safe_load(metadata.read_text())
        proof.update(status="qualified", coverage="all-available-invoices")
        proof["validation"] = dict(synthetic="tests/unattended_engine_probe.py",
                                   realProvider="two-pass-qualified", date="2026-10-30",
                                   expectedDocuments=2, firstRunNew=2, firstRunPdfReadback=2, repeatRunNew=0,
                                   firstRunClicks=2, firstRunDownloadEvents=2, repeatRunClicks=0,
                                   repeatRunDownloadEvents=0, independentSessions=True, keySetsSha256="a"*64,
                                   recipeSha256=hashlib.sha256(recipe.read_bytes()).hexdigest())
        metadata.write_text(yaml.safe_dump(proof))
        self.export()
        before = self.snapshot()
        recipe.write_bytes(recipe.read_bytes() + b"\n# changed recipe\n")
        with self.assertRaisesRegex(ValueError, "two-pass proof"):
            self.export()
        self.assertEqual(before, self.snapshot())

    def test_repeat_downloads_and_disabled_incremental_are_not_qualified(self):
        path = self.source / "playwright/free/metadata.yaml"
        original = yaml.safe_load(path.read_text())
        for field in ("repeatRunClicks", "repeatRunDownloadEvents"):
            proof = yaml.safe_load(path.read_text())
            proof["validation"][field] = 1
            path.write_text(yaml.safe_dump(proof))
            with self.assertRaisesRegex(ValueError, "two-pass proof"):
                self.export()
            path.write_text(yaml.safe_dump(original))
        recipe = path.with_name("recipe-pw__free.yaml")
        body = yaml.safe_load(recipe.read_text())
        body["services"][0]["steps"][-1]["methods"][-1]["arguments"][0]["incremental"] = False
        recipe.write_text(yaml.safe_dump(body))
        original["validation"]["recipeSha256"] = hashlib.sha256(recipe.read_bytes()).hexdigest()
        path.write_text(yaml.safe_dump(original))
        with self.assertRaisesRegex(ValueError, "stable incremental"):
            self.export()

    def test_literal_credentials_are_refused_before_export(self):
        recipe = self.source / "playwright/free/recipe-pw__free.yaml"
        body = yaml.safe_load(recipe.read_text())
        method = next(m for step in body["services"][0]["steps"]
                      for m in step["methods"] if m["method"] == "fill")
        method["arguments"] = [{"value": "synthetic-literal-credential"}]
        recipe.write_text(yaml.safe_dump(body))
        with self.assertRaisesRegex(ValueError, "placeholders"):
            self.export()
        self.assertFalse(self.dest.exists())

    def test_stale_owned_file_removed_but_unrelated_file_kept(self):
        self.export()
        stale = self.dest / "recipe-pw__retired.yaml"
        stale.write_text("retired")
        manifest = self.dest / module.MANIFEST
        data = json.loads(manifest.read_text())
        data["files"].append(stale.name)
        manifest.write_text(json.dumps(data))
        (self.dest / "keep.txt").write_text("keep")
        self.export()
        self.assertFalse(stale.exists())
        self.assertEqual((self.dest / "keep.txt").read_text(), "keep")

    def test_partial_write_failure_restores_previous_set(self):
        self.export()
        before = self.snapshot()
        path = self.source / "playwright/free/recipe-pw__free.yaml"
        path.write_text(path.read_text() + "\n# changed release\n")
        metadata = path.with_name("metadata.yaml")
        proof = yaml.safe_load(metadata.read_text())
        proof["validation"]["recipeSha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        metadata.write_text(yaml.safe_dump(proof))
        replace = module.os.replace
        count = 0

        def fail_after_two(*args):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError("synthetic disk error")
            return replace(*args)

        with patch.object(module.os, "replace", side_effect=fail_after_two):
            with self.assertRaises(OSError):
                self.export()
        self.assertEqual(before, self.snapshot())

    def test_unsafe_manifest_and_managed_symlink_refused(self):
        self.export()
        manifest = self.dest / module.MANIFEST
        original = manifest.read_bytes()
        manifest.write_text(json.dumps({"engine": "playwright-daemon", "files": ["../outside"]}))
        with self.assertRaises(ValueError):
            self.export()
        manifest.write_bytes(original)
        recipe = self.dest / "recipe-pw__free.yaml"
        recipe.unlink()
        recipe.symlink_to(self.source / "playwright/free/recipe-pw__free.yaml")
        with self.assertRaises(ValueError):
            self.export()

    def test_bd_intake_is_required_and_invalid_scope_keeps_previous_export(self):
        import copy
        self.export()
        before = self.snapshot()
        path = self.source / 'playwright/bourse_direct/metadata.yaml'
        original = yaml.safe_load(path.read_text())
        missing = copy.deepcopy(original)
        del missing['scope']
        bad_bound = copy.deepcopy(original)
        bad_bound['scope']['history']['maxMonths'] = 14
        no_control = copy.deepcopy(original)
        no_control['scope']['history']['controlRunRequired'] = False
        unexplained = copy.deepcopy(original)
        del unexplained['scope']['families']['tax_documents']['reason']
        for data in (missing, bad_bound, no_control, unexplained):
            with self.subTest(data=data):
                path.write_text(yaml.safe_dump(data))
                with self.assertRaises(ValidationError):
                    self.export()
                self.assertEqual(before, self.snapshot())


class BourseDirectCatalogTests(unittest.TestCase):
    def test_history_recipe_is_experimental_and_preserves_incremental_default(self):
        metadata = yaml.safe_load((ROOT / 'playwright/bourse_direct/metadata.yaml').read_text())
        self.assertEqual(metadata['status'], 'experimental')
        self.assertEqual(metadata['validation']['realProvider'], 'not-run')
        recipe = yaml.safe_load((ROOT / 'playwright/bourse_direct/recipe-pw__bourse_direct.yaml').read_text())
        step = recipe['services'][0]['steps'][1]
        self.assertEqual(step['notice_identity']['query_parameters'], ['nc', 'type', 'year', 'month', 'day'])
        options = step['methods'][-1]['arguments'][0]
        self.assertEqual(options['max_months'], 13)
        self.assertTrue(options['incremental'])
        self.assertEqual(options['max_items'], 100)
        self.assertEqual(options['timeout_ms'], 7200000)
        module.check_steps(recipe['services'][0]['steps'])

    def test_unsupported_history_or_disabled_incremental_is_rejected(self):
        import copy
        recipe = yaml.safe_load((ROOT / 'playwright/bourse_direct/recipe-pw__bourse_direct.yaml').read_text())
        for change in ({'max_months': 14}, {'max_months': True}, {'incremental': False}, {'max_items': 99}):
            with self.subTest(change=change):
                altered = copy.deepcopy(recipe)
                altered['services'][0]['steps'][1]['methods'][-1]['arguments'][0].update(change)
                with self.assertRaises(ValueError):
                    module.check_steps(altered['services'][0]['steps'])
