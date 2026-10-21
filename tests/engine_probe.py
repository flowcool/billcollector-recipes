"""Run isolated recipe and crash-window proof against an exact engine archive.

Usage: .venv/bin/python tests/engine_probe.py /path/to/engine/git/repository
No provider, vault, daemon, display server, scheduler or shared database is used.
"""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
REVISION = "501898cade0b9981092db2011fb3fc02812af8b3"
UPSTREAM = "c539b3420d0495ee6c4133e88e3a74e6e98740ad"
PDF = b"%PDF-1.4\nsynthetic older document\n%%EOF\n"


def worker(area):
    # All imports with runtime side effects occur only inside the archive.
    sys.path.insert(0, str(area / "engine/apps"))
    from billcollector import config, downloads, runner
    from billcollector.db import Database
    # Legacy helpers overwrite this at import. Restore the explicit test cache.
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.environ["PROBE_BROWSER_CACHE"]
    config.ensure_dirs()
    if os.environ.get("PROBE_CRASH_ONLY") == "1":
        crash_proof(area, downloads, Database)
        return
    db = Database(str(area / "runtime/probe.sqlite"))
    db.set_setting("download_dir", str(area / "runtime/output"))
    html = (ROOT / "tests/fixtures/playwright/portal.html").read_text()
    summaries = []
    consumers = []

    def execute(service, task, mode="normal", cancel=False):
        run_id = db.create_run(task["id"])
        ctx = SimpleNamespace(task=task, db=db, run_id=run_id, debug=False,
                              files_downloaded=[], bcs=SimpleNamespace(service=service, usr="synthetic"))
        unexpected = []
        resume_count = 0

        def launch(ctx, playwright):
            ctx.context = playwright.chromium.launch_persistent_context(
                str(area / "runtime/profiles" / service), headless=True,
                accept_downloads=True, args=["--no-sandbox", "--disable-background-networking"])
            ctx.page = ctx.context.pages[0]
            ctx.page.set_default_timeout(350)
            original_expect = ctx.page.expect_download
            # Bound fixture event waits; the production wrapper uses its default timeout.
            ctx.page.expect_download = lambda **kw: original_expect(timeout=10000)
            ctx.bcs.page = ctx.page

            def route(request_route):
                url = urlparse(request_route.request.url)
                if url.hostname not in {"subscribe.free.fr", "client.mint-energie.com",
                                         "abonnes.cc-genevois.fr", "www.fulli.com", "octopusenergy.fr"}:
                    unexpected.append(url.hostname)
                    request_route.abort()
                    return
                is_pdf = (url.path.endswith(".pdf") or "facture_pdf.pl" in url.path
                          or "/invoice/download/" in url.path)
                if is_pdf:
                    if mode == "broken":
                        request_route.abort()
                    else:
                        content = PDF if "newer" not in request_route.request.url else PDF + b"newer"
                        request_route.fulfill(status=200, body=content,
                                              headers={"Content-Type": "application/pdf",
                                                       "Content-Disposition": "attachment; filename=synthetic.pdf"})
                else:
                    body = "<html><body>Empty synthetic account</body></html>" if mode == "empty" else html
                    if service == "octopus_energy" and url.path != "/factures-et-paiements":
                        body = body.replace('<a href="/factures-et-paiements/agreement">Agreement</a>', "")
                    request_route.fulfill(status=200, content_type="text/html; charset=utf-8", body=body)
            ctx.context.route("**/*", route)

        def resume(ctx, reason, *args):
            nonlocal resume_count
            resume_count += 1
            assert resume_count <= 2, "Fixture resume guard did not become visible"
            # Simulate operator resume; no vault or credential submission.
            if cancel or reason != "wait_user":
                return "cancel"
            ctx.last_pause_deadline = datetime.now() + timedelta(seconds=1)
            return "resume"

        recipe = yaml.safe_load((ROOT / f"playwright/{service}/recipe-pw__{service}.yaml").read_text())
        if mode == "empty":
            # Exercise the download handler directly on an empty account landing.
            # Navigation/login behavior is covered by the unchanged normal recipe.
            recipe["services"][0]["steps"] = [recipe["services"][0]["steps"][0],
                                                   recipe["services"][0]["steps"][-1]]
        if mode in {"empty", "broken"}:
            # Only reduce the click timeout in negative tests, not production recipes.
            last = recipe["services"][0]["steps"][-1]
            last["steps"][0]["methods"][-1]["arguments"] = [{"timeout": 350}]
        with patch.object(runner, "_launch_browser", launch), patch.object(runner, "pause_loop", resume):
            files, aborted, outcome = runner._run_recipe(ctx, recipe)
        assert not unexpected, unexpected
        result = runner.run_result(aborted, files, outcome)
        return files, result

    with patch.object(downloads, "CONSUMERS", [lambda record: consumers.append(record)]):
        for provider in sorted((ROOT / "playwright").iterdir()):
            service = provider.name
            task_id = db.create_task(service, "synthetic")
            task = db.get_task(task_id)
            first, status = execute(service, task)
            assert len(first) == 1 and status == "success", (service, first, status)
            out = Path(db.get_setting("download_dir"))
            before = {p.name: p.read_bytes() for p in out.iterdir()}
            consumer_count = len(consumers)
            second, status = execute(service, task)
            assert len(second) == 1 and status == "success"
            assert before == {p.name: p.read_bytes() for p in out.iterdir()}
            assert len(consumers) == consumer_count
            assert all(content == PDF for content in before.values()), "Must select older first, not claim latest"
            print(f"Verified {service}: one download, repeat publishes zero", flush=True)
            summaries.append({"provider": service, "first": 1, "repeat_new": 0, "result": status})
        # Use a dedicated Free task for negative cases.
        negative_id = db.create_task("free", "negative")
        negative = db.get_task(negative_id)
        for mode in ("empty", "broken"):
            files, status = execute("free", negative, mode=mode)
            assert not files and status == "cancelled", (mode, files, status)
        files, status = execute("free", negative, cancel=True)
        assert not files and status == "cancelled"
        assert runner.run_result(False, [], None) == "failure"
    print(json.dumps({"revision": REVISION, "ports": summaries,
                      "negative_cases": ["empty-list", "failed-download", "operator-cancel"],
                      "zero-event_result": "failure"}, sort_keys=True))
    db.conn.close()
    crash_proof(area, downloads, Database)


def crash_proof(area, downloads, Database):
    directory = area / "crash"
    directory.mkdir()
    database = directory / "db.sqlite"
    db = Database(str(database))
    task_id = db.create_task("synthetic", "crash")
    run_id = db.create_run(task_id)
    db.set_setting("download_dir", str(directory / "output"))
    db.conn.close()

    class SyntheticDownload:
        suggested_filename = "synthetic.pdf"
        url = "https://fixture.invalid/synthetic.pdf"

        def save_as(self, path):
            Path(path).write_bytes(PDF)

    def attempt(crash):
        db = Database(str(database))
        def consumer(record):
            with (directory / "consumer-events").open("a") as output:
                output.write("synthetic\n")
        with patch.object(downloads, "CONSUMERS", [consumer]):
            if crash:
                def die(*args, **kwargs):
                    os._exit(73)
                db.insert_download = die
            record = downloads.track_download(SyntheticDownload(), run_id, {"id": task_id}, db)
        db.conn.close()
        return record

    # Fork only an idle process: Chromium and its Playwright driver are closed.
    pid = os.fork()
    if pid == 0:
        attempt(True)
        os._exit(74)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 73
    db = Database(str(database))
    assert db.conn.execute("SELECT count(*) FROM Download").fetchone()[0] == 0
    db.conn.close()
    output = directory / "output"
    assert len(list(output.iterdir())) == 1
    record = attempt(False)
    files = sorted(output.iterdir())
    expected_files = 1 if os.environ["PROBE_REVISION"] == UPSTREAM else 2
    assert len(files) == expected_files and not record["duplicate"]
    assert len({hashlib.sha256(p.read_bytes()).hexdigest() for p in files}) == 1
    assert (directory / "consumer-events").read_text().splitlines() == ["synthetic", "synthetic"]
    db = Database(str(database))
    assert db.conn.execute("SELECT count(*) FROM Download").fetchone()[0] == 1
    db.conn.close()
    print(json.dumps({"crash_exit": 73, "rows_after_crash": 0, "files_after_crash": 1,
                      "files_after_restart": len(files), "identical_hashes": True,
                      "revision": os.environ["PROBE_REVISION"],
                      "rows_after_restart": 1, "consumer_calls": 2}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine_repository", type=Path, nargs="?")
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--revision", choices=[REVISION, UPSTREAM], default=REVISION)
    parser.add_argument("--crash-only", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
        return
    if args.engine_repository is None:
        parser.error("An engine Git repository is required")
    if args.revision == UPSTREAM and not args.crash_only:
        parser.error("Upstream supports only --crash-only in this proof")
    # Archive from Git, not a possibly modified working tree. Reject unknown baselines.
    sha = subprocess.check_output(["git", "-C", str(args.engine_repository), "rev-parse", args.revision]).decode().strip()
    assert sha == args.revision
    with tempfile.TemporaryDirectory(prefix="bc-catalog-probe-") as temporary:
        area = Path(temporary)
        archive = area / "engine.tar"
        with archive.open("wb") as output:
            subprocess.run(["git", "-C", str(args.engine_repository), "archive", args.revision], stdout=output, check=True)
        with tarfile.open(archive) as tar:
            tar.extractall(area / "engine", filter="data")
        assert (area / "engine/apps/recipes_playwright/recipe-pw-schema.yaml").read_bytes() == (ROOT / "schema/playwright/recipe.schema.yaml").read_bytes()
        env = os.environ.copy()
        env["PROBE_REVISION"] = args.revision
        env["PROBE_CRASH_ONLY"] = "1" if args.crash_only else "0"
        for key, path in {"BC_DATA_DIR": "data", "BC_DB_DIR": "db", "BC_DB_FILE": "db/bc.sqlite",
                          "BC_LOG_DIR": "logs", "BC_PROFILE_ROOT": "profiles",
                          "BC_RUN_DIR": "runs", "BC_DOWNLOAD_DIR": "output", "BC_BROWSER_DIR": "browser"}.items():
            env[key] = str(area / "runtime" / path)
        # Browser executable cache is read-only test input, profiles remain temporary.
        cache = Path(env.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "ms-playwright"
        env["PROBE_BROWSER_CACHE"] = env.get("PLAYWRIGHT_BROWSERS_PATH", str(cache))
        subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(area)],
                       env=env, cwd=area, check=True, timeout=300)


if __name__ == "__main__":
    main()
