"""Reproduce the Bourse Direct adapter gap against an untouched engine archive.

Use the Python environment installed from the pinned engine's requirements.
This is a negative compatibility proof, not provider qualification.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tarfile
import tempfile
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
REVISION = "4a9bffc46015b1c6e36d0bf16b0de2b8634265cb"
FIXTURE = ROOT / "tests/fixtures/bourse_direct/historical-recipe.yaml"


def worker(area):
    engine = area / "engine"
    sys.path.insert(0, str(engine / "apps"))
    from billcollector import config, recipes, runner
    from billcollector.db import Database

    assert importlib.metadata.version("playwright") == "1.63.0"
    text = FIXTURE.read_text()
    expected = (
        "invalid method contract: service BourseDirect, step 2, method "
        "bourse_direct: unknown public Playwright attribute"
    )
    resource = Mock(side_effect=AssertionError("External resource access refused"))
    with patch.object(socket.socket, "connect", resource), \
            patch.object(socket.socket, "connect_ex", resource), \
            patch.object(runner.display, "allocate_display", resource), \
            patch.object(runner, "_vault_preflight", resource), \
            patch.object(runner, "sync_playwright", resource):
        # Positive controls distinguish an adapter gap from a broken environment.
        shipped = sorted(config.RECIPE_DIR.glob("recipe-pw__*.yaml"))
        assert len(shipped) == 15
        for path in shipped:
            ok, error, _, _ = recipes.load_recipe(path)
            assert ok, (path.name, error)
        login = re.search(
            r"```yaml\n(.*?)```", (engine / "doc/SAFE_LOGIN.md").read_text(), re.S
        )[1]
        ok, error, _ = recipes.validate_recipe(login)
        assert ok, error

        ok, error, _ = recipes.validate_recipe(text)
        assert not ok and error == expected, error
        ok, error, _, data = recipes.load_recipe(FIXTURE)
        assert not ok and error == expected and data is None, error
        destination = area / "runtime/recipe.yaml"
        destination.write_text(login)
        before = destination.read_bytes()
        ok, error = recipes.save_recipe(destination, text)
        assert not ok and error == expected, error
        assert destination.read_bytes() == before

        db = Database()
        try:
            task = db.create_task("BourseDirect", "synthetic", recipe_file=str(FIXTURE))
        finally:
            db.close()
        assert runner.run_task(task) == 1
        resource.assert_not_called()

    print(json.dumps({
        "engine_revision": REVISION,
        "playwright": importlib.metadata.version("playwright"),
        "historical_recipe_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "shipped_recipes_accepted": len(shipped),
        "native_login_candidate": "accepted",
        "historical_candidate": {
            "validate": "rejected", "load": "rejected", "save": "rejected",
            "save_preserves_previous_file": True, "run_exit": 1,
            "display_vault_browser_socket_calls": resource.call_count,
            "error": expected,
        },
    }, indent=2))


def main():
    if not __debug__:
        raise RuntimeError("Run this proof without Python optimization")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine_repository", type=Path, nargs="?")
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
        return
    if args.engine_repository is None:
        parser.error("engine_repository is required")
    with tempfile.TemporaryDirectory(prefix="bd-gate-") as temporary:
        area = Path(temporary)
        engine = area / "engine"
        engine.mkdir()
        archive = area / "engine.tar"
        with archive.open("wb") as stream:
            subprocess.run(
                ["git", "-C", str(args.engine_repository), "archive", REVISION],
                stdout=stream, check=True,
            )
        with tarfile.open(archive) as source:
            source.extractall(engine, filter="data")
        runtime = area / "runtime"
        runtime.mkdir()
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(("BC_", "BW_", "BEADS_"))
               and key not in {"PYTHONPATH", "PYTHONHOME", "PYTHONOPTIMIZE"}}
        for name, path in {
            "BC_DATA_DIR": runtime / "data", "BC_DB_DIR": runtime / "db",
            "BC_DB_FILE": runtime / "db/proof.db", "BC_LOG_DIR": runtime / "logs",
            "BC_PROFILE_ROOT": runtime / "profiles",
            "BC_DOWNLOAD_DIR": runtime / "downloads",
            "BC_BROWSER_DIR": runtime / "browser",
            "PLAYWRIGHT_BROWSERS_PATH": runtime / "browser",
        }.items():
            env[name] = str(path)
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", str(area)],
            env=env, cwd=engine, check=True,
        )


if __name__ == "__main__":
    main()
