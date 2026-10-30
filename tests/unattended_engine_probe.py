"""Exercise unattended recipes on synthetic loopback portals with isolated state.

The engine checkout is an exact input. No real provider or vault is contacted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import io
import zipfile
from unittest.mock import patch
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
REVISION = "45e530b7d6240abb308810183dbe4f65aae5b6dc"


def invoice_guards():
    """Ambiguous identities and incomplete history must fail before a click."""
    from playwright.sync_api import Error, sync_playwright
    html = (ROOT / "tests/fixtures/playwright/unattended.html").read_text()
    cases = [
        ("mint_energie", html.replace("15/02/2026", "16/01/2026"), "Multiple invoices"),
        ("mint_energie", html.replace('value="02"', 'value="03"'), "Invoice filter unavailable"),
        ("free", html.replace("Février 2026", "Janvier 2026"), "Ambiguous invoice period"),
        ("fulli", html, "Invoice pagination incomplete"),
    ]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            for service, body, message in cases:
                recipe = yaml.safe_load((ROOT / f"playwright/{service}/recipe-pw__{service}.yaml").read_text())
                binding = next(step for step in recipe["services"][0]["steps"]
                               if step["description"].startswith(("Bind each invoice", "Bind invoice links", "Bind native ZIP")))
                page.set_content(body)
                page.evaluate("() => {window.clicks=0; document.addEventListener('click',()=>window.clicks++);}")
                try:
                    page.evaluate(binding["methods"][0]["arguments"][0]["expression"])
                except Error as exc:
                    assert message in str(exc), (service, str(exc))
                else:
                    raise AssertionError((service, "ambiguous source accepted"))
                assert page.evaluate("window.clicks") == 0
        finally:
            browser.close()
    print(json.dumps(dict(invoice_guard_cases=len(cases), download_clicks=0)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", type=Path)
    parser.add_argument("--provider", choices=["free", "fulli", "mint_energie", "cc_genevois"])
    parser.add_argument("--guards-only", action="store_true")
    args = parser.parse_args()
    import subprocess
    if args.guards_only:
        invoice_guards()
        return
    assert subprocess.check_output(["git", "-C", str(args.engine), "rev-parse", "HEAD"], text=True).strip() == REVISION
    invoice_guards()
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
        attempt = 0
        clicks = 0
        events = 0
        key_sets = {}
        original_snapshot = runner.collection._snapshot
        original_download = runner.collection._download_one

        def snapshot(locator, attribute):
            keys = original_snapshot(locator, attribute)
            if keys:
                key_sets.setdefault(attribute, sorted(keys))
            return keys

        def download(*args, **kwargs):
            nonlocal clicks
            clicks += 1
            return original_download(*args, **kwargs)

        def event(_):
            nonlocal events
            events += 1

        def launch(ctx, playwright):
            profile = root / "profiles" / ctx.task["service"] / str(attempt)
            runner._ensure_pdf_preference(profile)
            ctx.context = playwright.chromium.launch_persistent_context(str(profile), headless=True, service_workers="block", accept_downloads=True)
            ctx.page = ctx.context.new_page()
            ctx.page.on("download", event)
            ctx.bcs.page = ctx.page
            def route(r):
                url = urlparse(r.request.url)
                if url.hostname not in {"subscribe.free.fr", "www.fulli.com", "client.mint-energie.com", "abonnes.cc-genevois.fr"}:
                    unexpected.append(url.hostname)
                    r.abort()
                    return
                if url.path.endswith(".zip"):
                    # Native per-period Mint ZIP. Preserve the PDF BOM and bytes.
                    payload = b"\xef\xbb\xbf%PDF-1.4\nsynthetic " + url.path.encode() + b"\n%%EOF\n"
                    archive = io.BytesIO()
                    with zipfile.ZipFile(archive, "w") as z:
                        z.writestr("invoice-" + url.path[6:8] + ".pdf", payload)
                    r.fulfill(status=200, body=archive.getvalue(), headers={"Content-Type":"application/zip", "Content-Disposition":"attachment; filename=invoices.zip"})
                elif "facture_pdf.pl" in url.path or "/invoice/download/" in url.path or url.path.endswith(".pdf"):
                    payload = b"%PDF-1.4\nsynthetic " + url.path.encode() + url.query.encode() + b"\n%%EOF\n"
                    r.fulfill(status=200, body=payload, headers={"Content-Type":"application/pdf", "Content-Disposition":"attachment; filename=" + hashlib.sha256((url.path + url.query).encode()).hexdigest()[:16] + ".pdf"})
                else:
                    # Source link/session values change between independent sessions.
                    body = html.replace("?id=", f"?session={attempt}&id=")
                    r.fulfill(status=200, content_type="text/html; charset=utf-8", body=body)
            ctx.context.route("**/*", route)

        results = []
        try:
            with patch.object(runner, "_launch_browser", launch), patch.object(runner, "pause_loop", lambda *args: "cancel"), patch.object(downloads, "CONSUMERS", []), patch.object(runner.collection, "_snapshot", snapshot), patch.object(runner.collection, "_download_one", download):
                for service, count in {"free":2, "fulli":3, "mint_energie":2, "cc_genevois":2}.items():
                    if args.provider and service != args.provider:
                        continue
                    recipe = yaml.safe_load((ROOT / f"playwright/{service}/recipe-pw__{service}.yaml").read_text())
                    # Synthetic downloads are immediate and emit exactly one event.
                    for step in recipe["services"][0]["steps"]:
                        if step["methods"][-1]["method"] == "download_all":
                            step["methods"][-1]["arguments"][0]["event_window_ms"] = 200
                    task = db.create_task(service, "synthetic")
                    counts=[]
                    identity = None
                    for attempt in range(2):
                        clicks = events = 0
                        key_sets = {}
                        print(json.dumps(dict(service=service,attempt=attempt+1)),flush=True)
                        run = db.create_run(task)
                        ctx = runner._RunContext(db.get_task(task), run, db, False, {"user":"synthetic", "password":"synthetic", "otp":None}, "http://127.0.0.1:9")
                        files, aborted, outcome = runner._run_recipe(ctx, recipe)
                        result = runner.run_result(aborted, files, outcome, known_source_count=ctx.incremental_known_count)
                        db.update_run(run, result=result, ended_at=now())
                        rows = [dict(r) for r in db.list_downloads(run_id=run)]
                        new = sum(r["duplicate_of_id"] is None for r in rows)
                        expected = count if attempt == 0 else 0
                        assert result == "success" and len(rows) == expected, (service,result,len(rows),expected,db.conn.execute("SELECT error FROM PageStatus WHERE run_id=? ORDER BY id DESC LIMIT 1",(run,)).fetchone()[0])
                        assert new == (count if attempt == 0 else 0), (service,new,attempt)
                        assert clicks == events == expected, (service, clicks, events, expected)
                        if attempt == 0:
                            identity = key_sets.copy()
                            assert len(next(iter(identity.values()))) == count
                        else:
                            assert identity == key_sets, (service, "unstable source keys")
                        for row in rows:
                            assert row["source_key"]
                            payload = Path(row["saved_path"]).read_bytes()
                            if service == "mint_energie":
                                assert payload == b"\xef\xbb\xbf%PDF-1.4\nsynthetic /mint-" + (b"01" if "01" in Path(row["saved_path"]).name else b"02") + b".zip\n%%EOF\n"
                            else:
                                assert payload.startswith(b"%PDF-")
                        counts.append(new)
                    results.append(dict(service=service, first_new=counts[0], repeat_new=counts[1]))
            assert not unexpected, unexpected
            print(json.dumps(dict(revision=REVISION,providers=results,external_requests=unexpected)))
        finally:
            db.close()


if __name__ == "__main__":
    main()
