import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CiScopeTests(unittest.TestCase):
    def test_only_markdown_can_skip_full_checks(self):
        scope = load('ci_scope')
        self.assertFalse(scope.requires_checks(['README.md', 'docs/provider.md']))
        for paths in [['README.md', 'scripts/tool.py'], ['docs/recipe.yaml'],
                      ['.github/workflows/ci.yml'], ['playwright/free/metadata.yaml']]:
            with self.subTest(paths=paths):
                self.assertTrue(scope.requires_checks(paths))

    def test_security_gate_requires_both_exact_commit_analyses(self):
        gate = load('check_security_gate')
        rows = [dict(category=f'/language:{language}', commit_sha='head',
                     tool={'name': 'CodeQL'}, error='') for language in ['python', 'actions']]
        gate.validate_analyses(rows, 'head')
        for invalid in [rows[:1], [dict(row, commit_sha='old') for row in rows],
                        [dict(row, error='scan failed') for row in rows]]:
            with self.assertRaises(ValueError):
                gate.validate_analyses(invalid, 'head')

    def test_security_gate_keeps_alert_thresholds(self):
        gate = load('check_security_gate')
        gate.validate_alerts([{'rule': {'severity': 'warning', 'security_severity_level': 'medium'}}])
        for rule in [{'severity': 'error'}, {'security_severity_level': 'high'},
                     {'security_severity_level': 'critical'}]:
            with self.assertRaises(ValueError):
                gate.validate_alerts([{'rule': rule}])
