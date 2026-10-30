"""Exercise unattended recipes on synthetic loopback portals with isolated state.

The engine checkout is an exact input. No real provider or vault is contacted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
REVISION = "b401f801c9184f6b0c8917fb8d06a79fa0f0e917"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", type=Path)
    parser.add_argument("--provider", choices=["free", "fulli", "mint_energie", "cc_genevois"])
    args = parser.parse_args()
    import subprocess
    assert subprocess.check_output(["git", "-C", str(args.engine), "rev-parse", "HEAD"], text=True).strip() == REVISION
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix="unattended-recipes-") as directory:
        root = Path(directory)
        for name, path in {"BC_DATA_DIR":"data", "BC_DB_FILE":"proof.db", "BC_DB_DIR":"db", "BC_RUN_DIR":"runs", "BC_LOG_DIR":"logs", "BC_PROFILE_ROOT":"profiles", "BC_DOWNLOAD_DIR":"downloads"}.items():
            os.environ[name] = str(root / path)
        cache = os.environ["PLAYWRIGHT_BROWSERS_PATH"]
        import sys
        sys.path.insert(0, str(args.engine.resolve() / "apps"))
        from billcollector import config, downloads, runner
        from billcollector.db import Database, now
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = cache
        config.RUN_DIR = root / "runs"
        db = Database(root / "proof.db")
        db.set_setting("download_dir", str(root / "downloads"))
        db.set_setting("pause_deadline_seconds", "1")
        html = (ROOT / "tests/fixtures/playwright/unattended.html").read_text()
        unexpected = []

        def launch(ctx, playwright):
            profile = root / "profiles" / ctx.task["service"]
            runner._ensure_pdf_preference(profile)
            ctx.context = playwright.chromium.launch_persistent_context(str(profile), headless=True, service_workers="block", accept_downloads=True)
            ctx.page = ctx.context.new_page()
            ctx.bcs.page = ctx.page
            def route(r):
                url = urlparse(r.request.url)
                if url.hostname not in {"subscribe.free.fr", "www.fulli.com", "client.mint-energie.com", "abonnes.cc-genevois.fr"}:
                    unexpected.append(url.hostname)
                    r.abort()
                    return
                if "facture_pdf.pl" in url.path or "/invoice/download/" in url.path or url.path.endswith(".pdf"):
                    payload = b"%PDF-1.4\nsynthetic " + url.path.encode() + url.query.encode() + b"\n%%EOF\n"
                    r.fulfill(status=200, body=payload, headers={"Content-Type":"application/pdf", "Content-Disposition":"attachment; filename=" + hashlib.sha256((url.path + url.query).encode()).hexdigest()[:16] + ".pdf"})
                else:
                    r.fulfill(status=200, content_type="text/html; charset=utf-8", body=html)
            ctx.context.route("**/*", route)

        results = []
        try:
            with patch.object(runner, "_launch_browser", launch), patch.object(runner, "pause_loop", lambda *args: "cancel"), patch.object(downloads, "CONSUMERS", []):
                for service, count in {"free":2, "fulli":3, "mint_energie":1, "cc_genevois":2}.items():
                    if args.provider and service != args.provider:
                        continue
                    recipe = yaml.safe_load((ROOT / f"playwright/{service}/recipe-pw__{service}.yaml").read_text())
                    # Synthetic downloads are immediate and emit exactly one event.
                    for step in recipe["services"][0]["steps"]:
                        if step["methods"][-1]["method"] == "download_all":
                            step["methods"][-1]["arguments"][0]["event_window_ms"] = 200
                    task = db.create_task(service, "synthetic")
                    counts=[]
                    for attempt in range(2):
                        print(json.dumps(dict(service=service,attempt=attempt+1)),flush=True)
                        run = db.create_run(task)
                        ctx = runner._RunContext(db.get_task(task), run, db, False, {"user":"synthetic", "password":"synthetic", "otp":None}, "http://127.0.0.1:9")
                        files, aborted, outcome = runner._run_recipe(ctx, recipe)
                        result = runner.run_result(aborted, files, outcome)
                        db.update_run(run, result=result, ended_at=now())
                        rows = [dict(r) for r in db.list_downloads(run_id=run)]
                        new = sum(r["duplicate_of_id"] is None for r in rows)
                        assert result == "success" and len(rows) == count, (service,result,len(rows),count,db.conn.execute("SELECT error FROM PageStatus WHERE run_id=? ORDER BY id DESC LIMIT 1",(run,)).fetchone()[0])
                        assert new == (count if attempt == 0 else 0), (service,new,attempt)
                        counts.append(new)
                    results.append(dict(service=service, first_new=counts[0], repeat_new=counts[1]))
            assert not unexpected, unexpected
            print(json.dumps(dict(revision=REVISION,providers=results,external_requests=unexpected)))
        finally:
            db.close()


if __name__ == "__main__":
    main()
