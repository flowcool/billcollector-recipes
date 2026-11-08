"""Probe historical gaps or a statement-capable engine commit, offline.

Run with the selected engine's Python runtime dependencies installed.
Default: historical negative proof. --candidate-revision: positive compatibility.
Neither mode proves collection qualification.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tarfile
import tempfile
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
REVISIONS = (
    "c87f980b985d526dac95760e477cec95f280896d",
    "515155f4e87fa6968ff899946787a0ee5284851a",
)


def worker(area, revision, candidate=False):
    sys.path.insert(0, str(area / "engine/apps"))
    from billcollector import bourse_direct, recipes

    recipe = ROOT / "playwright/bourse_direct/recipe-pw__bourse_direct.yaml"
    data = yaml.safe_load(recipe.read_text())
    options = data["services"][0]["steps"][1]["methods"][-1]["arguments"][0]
    options.pop('collect_statements', None)  # Explicit unchanged-notice control.
    original_options = dict(options)

    def refused(*args, **kwargs):
        raise AssertionError("External access is forbidden in this proof")

    results = {}
    with patch.object(socket.socket, "connect", refused), \
            patch.object(socket.socket, "connect_ex", refused):
        ok, error, _ = recipes.validate_recipe(recipe.read_text())
        if not ok:
            raise RuntimeError("Notice recipe positive control failed: " + error)
        results["notice_recipe_accepted"] = True

        options["collect_statements"] = True
        ok, _, _ = recipes.validate_recipe(yaml.safe_dump(data))
        if candidate:
            if not ok:
                raise RuntimeError('Statement candidate option is refused')
            from billcollector.bourse_direct_statements import POLICY
            from billcollector.notice import source_digest

            target, day = bourse_direct._target(
                bourse_direct.ORIGIN + '/priv/new/releves.php',
                'releveCompte.php?nc=1&type=RE&dt=20251128&trash=/avis.pdf&pdf=1',
                account='1', period=(2025, 11), pdf=True, family='statement')
            if day.isoformat() != '2025-11-28' or len(source_digest(target, POLICY)) != 64:
                raise RuntimeError('Statement offered date or source identity is invalid')
            print(json.dumps({'engine_revision': revision,
                              'recipe_sha256': hashlib.sha256(recipe.read_bytes()).hexdigest(),
                              'proof': 'positive-compatibility', 'real_provider': False,
                              'paperless': False, **results, 'statement_option_accepted': True,
                              'statement_identity_accepted': True, 'statement_original_target_accepted': True},
                             sort_keys=True))
            return
        if ok:
            raise RuntimeError("Engine now accepts a statement option; requalify the gap")
        results["statement_option_rejected"] = True

        options.clear()
        options.update(original_options)
        data["services"][0]["steps"][1]["notice_identity"] = {
            "query_parameters": ["nc", "type", "dt"]
        }
        ok, _, _ = recipes.validate_recipe(yaml.safe_dump(data))
        if ok:
            raise RuntimeError("Engine now accepts a statement identity; requalify the gap")
        results["statement_identity_rejected"] = True

        try:
            bourse_direct._target(
                bourse_direct.ORIGIN + "/priv/new/releves.php",
                "releveCompte.php?nc=1&type=RE&dt=20251128&trash=/avis.pdf&pdf=1",
                account="1", period=(2025, 11), pdf=True,
            )
        except bourse_direct.SourceError:
            results["statement_original_target_rejected"] = True
        else:
            raise RuntimeError("Engine now accepts a statement target; requalify the gap")

    print(json.dumps({
        "engine_revision": revision,
        "recipe_sha256": hashlib.sha256(recipe.read_bytes()).hexdigest(),
        "proof": "negative-compatibility",
        "real_provider": False,
        "paperless": False,
        **results,
    }, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine_repository", type=Path, nargs="?")
    parser.add_argument('--candidate-revision', help='Check this exact statement-capable commit instead of historical gaps')
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--revision", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if not args.revision:
            parser.error("--worker requires --revision")
        worker(args.worker, args.revision, candidate=args.candidate_revision is not None)
        return
    if args.engine_repository is None:
        parser.error("engine_repository is required")
    revisions = REVISIONS
    if args.candidate_revision:
        revisions = (subprocess.check_output(
            ['git', '-C', str(args.engine_repository), 'rev-parse', '--verify',
             args.candidate_revision + '^{commit}'], text=True).strip(),)
    for revision in revisions:
        with tempfile.TemporaryDirectory(prefix="bd-statements-gap-") as temporary:
            area = Path(temporary)
            engine = area / "engine"
            engine.mkdir()
            archive = area / "engine.tar"
            with archive.open("wb") as stream:
                subprocess.run(
                    ["git", "-C", str(args.engine_repository), "archive", revision],
                    stdout=stream, check=True,
                )
            with tarfile.open(archive) as source:
                source.extractall(engine, filter="data")
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith(("BC_", "BW_", "BEADS_"))
                   and key not in {"PYTHONPATH", "PYTHONHOME", "PYTHONOPTIMIZE"}}
            for key, value in {
                "BC_DATA_DIR": "data", "BC_DB_DIR": "db", "BC_DB_FILE": "db/proof.db",
                "BC_LOG_DIR": "logs", "BC_PROFILE_ROOT": "profiles",
                "BC_DOWNLOAD_DIR": "downloads", "BC_BROWSER_DIR": "browser",
                "PLAYWRIGHT_BROWSERS_PATH": "browser",
            }.items():
                env[key] = str(area / value)
            command = [sys.executable, str(Path(__file__).resolve()), '--worker', str(area), '--revision', revision]
            if args.candidate_revision:
                command += ['--candidate-revision', revision]
            subprocess.run(command, env=env, cwd=engine, check=True)


if __name__ == "__main__":
    main()
