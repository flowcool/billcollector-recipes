"""Qualify the exact catalog recipe with the exact engine, loopback only."""
import argparse
import hashlib
import importlib.util
from importlib.metadata import distribution
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]

SELECTIONS = {
    'notice': 'actual_recipe_login_originals or all_covers_thirteen or history_reset or '
              'explicit_start_overrides or native_adapter_dispatches or invalid_gate',
    'statement': 'new_late_statement or full_offered_statement or statement_source_drift or '
                 'uncertain_statement or statement_post_guard',
}

IMAGE_WORKER = r'''
import hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
root = Path(tempfile.mkdtemp(prefix='bd-catalog-image-'))
for name, relative in {'BC_DATA_DIR':'data', 'BC_DB_DIR':'db', 'BC_DB_FILE':'db/proof.db',
                       'BC_PROFILE_ROOT':'profiles', 'BC_LOG_DIR':'logs',
                       'BC_DOWNLOAD_DIR':'downloads', 'HOME':'home'}.items():
    os.environ[name] = str(root/relative)
os.environ['PYTHONPATH'] = '/test-deps:/apps'
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
shutil.copytree('/checks', root/'tests')
shutil.copytree('/apps/recipes_playwright', root/'apps/recipes_playwright')
candidate = Path('/catalog/recipe-pw__bourse_direct.yaml')
import yaml
control = yaml.safe_load(candidate.read_bytes())
control['services'][0]['steps'][1]['methods'][-1]['arguments'][0].pop('collect_statements')
notice = root/'notice-control.yaml'
notice.write_text(yaml.safe_dump(control))
selected = json.loads(os.environ['BC_TEST_CATALOG_SELECTIONS'])
selections = [(notice, selected['notice']), (candidate, selected['statement'])]
for recipe, selected in selections:
    os.environ['BC_TEST_BOURSE_DIRECT_RECIPE'] = str(recipe)
    subprocess.run([sys.executable, '-m', 'pytest', str(root/'tests/test_bourse_direct.py'),
                    '-k', selected, '-q', '-p', 'pytest_asyncio.plugin',
                    '-o', 'asyncio_default_fixture_loop_scope=function'], check=True)
print(json.dumps({'catalog_recipe_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
                  'uid':os.getuid(), 'network':'none', 'proof':'exported-catalog-browser'}), flush=True)
'''


def qualify_image(image, engine, exported, revision, proof_dir):
    info = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image], text=True))[0]
    if info['Config']['Labels']['org.opencontainers.image.revision'] != revision:
        raise ValueError('Image revision differs from the catalog pin')
    proof_dir.mkdir(parents=True, exist_ok=False)
    deps = proof_dir / 'test-deps'
    deps.mkdir()
    for name in ('pytest', '_pytest', 'pluggy', 'iniconfig', 'packaging', 'py', 'pytest_asyncio'):
        origin = Path(importlib.util.find_spec(name).origin)
        if origin.name == '__init__.py':
            shutil.copytree(origin.parent, deps/name)
        else:
            shutil.copy2(origin, deps/origin.name)
    package = distribution('pytest-asyncio')
    metadata = next(p.parent for p in package.files if p.name == 'METADATA'
                    and p.parent.name.endswith('.dist-info'))
    source = Path(package.locate_file(metadata))
    shutil.copytree(source, deps/source.name)
    for path in [proof_dir, deps, *deps.rglob('*')]:
        path.chmod(0o755 if path.is_dir() else 0o644)
    command = ['docker', 'run', '--rm', '--init', '--network', 'none', '--user', '1003:1000',
               '--shm-size', '256m', '--security-opt', f'seccomp={engine}/docker/chromium-seccomp.json',
               '--mount', f'type=bind,src={engine}/tests,dst=/checks,readonly',
               '--mount', f'type=bind,src={deps},dst=/test-deps,readonly',
               '--mount', f'type=bind,src={exported},dst=/catalog,readonly',
               '--env', 'BC_TEST_CATALOG_SELECTIONS=' + json.dumps(SELECTIONS),
               '-i', '--entrypoint', 'python3', image, '-']
    (proof_dir/'worker.py').write_text(IMAGE_WORKER)
    with (proof_dir/'container.log').open('w') as log:
        result = subprocess.run(command, input=IMAGE_WORKER, text=True,
                                stdout=log, stderr=subprocess.STDOUT)
    receipt = {'engine_revision':revision, 'image_id':info['Id'],
               'image_reference':image, 'exit_code':result.returncode, 'network':'none',
               'recipe_sha256':hashlib.sha256((exported/'recipe-pw__bourse_direct.yaml').read_bytes()).hexdigest()}
    (proof_dir/'result.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if result.returncode:
        raise RuntimeError('Catalog image proof failed; inspect retained container.log')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('engine', type=Path)
    parser.add_argument('--image', help='Run on this exact local image instead of the host runtime')
    parser.add_argument('--proof-dir', type=Path, help='New owned directory for image receipts')
    args = parser.parse_args()
    engine = args.engine.resolve()
    recipe = ROOT / 'playwright/bourse_direct/recipe-pw__bourse_direct.yaml'
    metadata = yaml.safe_load(recipe.with_name('metadata.yaml').read_text())
    revision = subprocess.check_output(['git', '-C', str(engine), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != metadata['engineRevision']:
        raise ValueError('Engine revision differs from the recipe qualification pin')
    expected = 'cebc9c7c6fb09f5d171f322a0cce92dd33a66d519478437c02559b16ef222b07'
    for path in [ROOT / 'schema/playwright/recipe.schema.yaml', engine / 'apps/recipes_playwright/recipe-pw-schema.yaml']:
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Engine/catalog schema mismatch')
    with tempfile.TemporaryDirectory(prefix='bd-catalog-proof-') as temporary:
        area = Path(temporary)
        exported = area / 'export'
        subprocess.run([sys.executable, str(ROOT / 'scripts/playwright_catalog.py'),
                        str(ROOT), str(exported), '--engine-revision', revision], check=True)
        candidate = exported / recipe.name
        if candidate.read_bytes() != recipe.read_bytes():
            raise ValueError('Export changed the candidate recipe')
        if args.image:
            if args.proof_dir is None:
                parser.error('--image requires --proof-dir')
            # mkdtemp is private by default; this export contains public YAML.
            area.chmod(0o755)
            qualify_image(args.image, engine, exported, revision, args.proof_dir.resolve())
            return
        control = yaml.safe_load(candidate.read_bytes())
        control['services'][0]['steps'][1]['methods'][-1]['arguments'][0].pop('collect_statements')
        notice = area / 'notice-control.yaml'
        notice.write_text(yaml.safe_dump(control))
        selections = [(notice, SELECTIONS['notice']), (candidate, SELECTIONS['statement'])]
        for source, selected in selections:
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith(('BC_', 'BW_', 'BEADS_'))}
            env['BC_TEST_BOURSE_DIRECT_RECIPE'] = str(source)
            command = [sys.executable, '-m', 'pytest', 'tests/test_bourse_direct.py',
                       '-k', selected, '-q', '-o', 'asyncio_default_fixture_loop_scope=function']
            subprocess.run(command, cwd=engine, env=env, check=True)
    print(json.dumps({'engine_revision': revision,
                      'recipe_sha256': hashlib.sha256(recipe.read_bytes()).hexdigest(),
                      'schema_sha256': expected, 'portal': 'synthetic-loopback',
                      'notice_months': 13, 'notice_incremental': 'task-window',
                      'statements': 'full-offered-list-both-modes', 'statement_identity': ['nc', 'type', 'dt'],
                      'notice_control': 'candidate with collect_statements removed',
                      'real_provider': False, 'paperless': False}), flush=True)


if __name__ == '__main__':
    main()
