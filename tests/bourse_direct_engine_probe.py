"""Qualify the exact catalog recipe with the exact engine, loopback only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

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
    expected = '1d3b111472c6fdfaab9860fe1ee28d6c255105c69de8281902eefcef631e70f2'
    for path in [ROOT / 'schema/playwright/recipe.schema.yaml', engine / 'apps/recipes_playwright/recipe-pw-schema.yaml']:
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Engine/catalog schema mismatch')
    env = dict(os.environ, BC_TEST_BOURSE_DIRECT_RECIPE=str(recipe))
    command = [sys.executable, '-m', 'pytest', 'tests/test_bourse_direct.py', 'tests/test_throttle.py', '-q']
    result = subprocess.run(command, cwd=engine, env=env)
    if result.returncode:
        raise SystemExit(result.returncode)
    print(json.dumps({'engine_revision': revision,
                      'recipe_sha256': hashlib.sha256(recipe.read_bytes()).hexdigest(),
                      'schema_sha256': expected, 'portal': 'synthetic-loopback',
                      'all_months': 13, 'incremental': 'task-window',
                      'real_provider': False, 'paperless': False}), flush=True)


if __name__ == '__main__':
    main()
