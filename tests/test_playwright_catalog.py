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

    def test_five_ports_and_repeat_export_preserve_unrelated_files(self):
        self.export()
        self.assertEqual(len(list(self.dest.glob("recipe-pw__*.yaml"))), 5)
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
                                   recipeSha256=hashlib.sha256(recipe.read_bytes()).hexdigest())
        metadata.write_text(yaml.safe_dump(proof))
        self.export()
        before = self.snapshot()
        recipe.write_bytes(recipe.read_bytes() + b"\n# changed recipe\n")
        with self.assertRaisesRegex(ValueError, "two-pass proof"):
            self.export()
        self.assertEqual(before, self.snapshot())

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
