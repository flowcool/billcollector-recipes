"""Qualify the exact catalog recipe with the exact engine, loopback only."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('engine', type=Path)
    args = parser.parse_args()
    engine = args.engine.resolve()
    recipe = ROOT / 'playwright/bourse_direct/recipe-pw__bourse_direct.yaml'
    metadata = yaml.safe_load(recipe.with_name('metadata.yaml').read_text())
    revision = subprocess.check_output(['git', '-C', str(engine), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != metadata['engineRevision']:
        raise ValueError('Engine revision differs from the recipe qualification pin')
    expected = 'f3b92edaa352d29c794581b8ff67a5a3b7e6066a608c354e6d4799eabaafc523'
    for path in [ROOT / 'schema/playwright/recipe.schema.yaml', engine / 'apps/recipes_playwright/recipe-pw-schema.yaml']:
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Engine/catalog schema mismatch')
    env = dict(os.environ, PYTHONPATH=str(engine / 'apps'))
    command = [sys.executable, '-m', 'pytest',
               'tests/test_bc_bourse_direct_boundary.py',
               'tests/test_bc_method_validation.py', '-q', '-x']
    result = subprocess.run(command, check=False, cwd=engine, env=env)
    if result.returncode:
        raise SystemExit(result.returncode)
    check = [sys.executable, '-c', '''
from pathlib import Path
from billcollector import config, recipes
root = Path(__import__("os").environ["BC_RECIPE_ROOT"])
config.RECIPE_DIR = root / "playwright/bourse_direct"
config.RECIPE_SCHEMA = root / "schema/playwright/recipe.schema.yaml"
ok, error, _ = recipes.validate_recipe((config.RECIPE_DIR / "recipe-pw__bourse_direct.yaml").read_text())
raise SystemExit(0 if ok else error)
''']
    check_env = dict(env, BC_RECIPE_ROOT=str(ROOT))
    result = subprocess.run(check, check=False, cwd=engine, env=check_env, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout or 'catalog recipe validation failed')
    print(json.dumps({'engine_revision': revision,
                      'recipe_sha256': hashlib.sha256(recipe.read_bytes()).hexdigest(),
                      'schema_sha256': expected, 'portal': 'synthetic-loopback',
                      'all_months': 13, 'incremental': 'task-window',
                      'real_provider': False, 'paperless': False}), flush=True)


if __name__ == '__main__':
    main()
