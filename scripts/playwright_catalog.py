"""Validate the catalog and export only managed Playwright runtime files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

import yaml
from jsonschema import validate

REVISION = "45e530b7d6240abb308810183dbe4f65aae5b6dc"
MANIFEST = ".billcollector-playwright.json"
SCHEMA = "recipe-pw-schema.yaml"


def check_steps(steps, nested=False):
    numbers = [step["step"] for step in steps]
    if not numbers or len(numbers) != len(set(numbers)):
        raise ValueError("Empty steps or duplicate step numbers")
    for step in steps:
        methods = step.get("methods", [])
        names = [method["method"] for method in methods]
        if names == ["expect_download"] and not nested:
            check_steps(step.get("steps", []), nested=True)
        elif names == ["wait_user"] and not nested:
            args = {k: v for arg in methods[0].get("arguments", []) for k, v in arg.items()}
            if not args.get("prompt") or not args.get("until", {}).get("selector"):
                raise ValueError("Supervised authentication requires a prompt and selector")
        elif names == ["goto"] and not nested:
            if not methods[0].get("arguments", [{}])[0].get("url", "").startswith("https://"):
                raise ValueError("Navigation must use a public HTTPS URL")
        elif names in (["locator", "click"], ["locator", "first", "click"],
                       ["locator", "fill"], ["locator", "download_all"],
                       ["locator", "click_until_absent"]):
            if not methods[0].get("arguments", [{}])[0].get("selector"):
                raise ValueError("Missing selector")
            options = {k: v for arg in methods[-1].get("arguments", []) for k, v in arg.items()}
            if names[-1] == "click":
                timeout = options.get("timeout")
                if not isinstance(timeout, int) or not 0 < timeout <= 60000:
                    raise ValueError("Click must have a finite timeout")
            elif names[-1] == "fill":
                if options.get("value") not in {"{{USERNAME}}", "{{PASSWORD}}"}:
                    raise ValueError("Credentials must use engine placeholders")
        elif names == ["login"] and not nested:
            options = {k: v for arg in methods[0].get("arguments", []) for k, v in arg.items()}
            if not options.get("success", {}).get("selector"):
                raise ValueError("Login requires an authenticated success selector")
            check_steps(step.get("steps", []), nested=True)
            check_steps([step["submit"]], nested=True)
        elif names == ["evaluate"] and not nested:
            expression = methods[0].get("arguments", [{}])[0].get("expression")
            if not isinstance(expression, str) or not expression.strip():
                raise ValueError("DOM evaluation requires an expression")
        else:
            raise ValueError(f"Unsupported method chain: {names}")
        if "steps" in step and names not in (["expect_download"], ["login"]):
            raise ValueError("Unexpected nested steps")


def catalog(source):
    schema_bytes = (source / "schema/playwright/recipe.schema.yaml").read_bytes()
    schema = yaml.safe_load(schema_bytes)
    metadata_schema = json.loads((source / "schema/playwright/metadata.schema.json").read_text())
    files = {SCHEMA: schema_bytes}
    providers = sorted((source / "playwright").iterdir())
    if not providers:
        raise ValueError("Empty Playwright catalog")
    for provider in providers:
        if not provider.is_dir() or provider.is_symlink():
            raise ValueError(f"Unexpected provider entry: {provider}")
        metadata = yaml.safe_load((provider / "metadata.yaml").read_text())
        validate(metadata, metadata_schema)
        service = metadata["service"]
        if service != provider.name:
            raise ValueError("Provider directory and service differ")
        recipes = list(provider.glob("recipe-pw__*.yaml"))
        expected = provider / f"recipe-pw__{service}.yaml"
        if recipes != [expected] or expected.is_symlink():
            raise ValueError("Expected exactly one named recipe per provider")
        data = expected.read_bytes()
        recipe = yaml.safe_load(data)
        validate(recipe, schema)
        if len(recipe.get("services", [])) != 1 or recipe["services"][0]["serviceName"] != service:
            raise ValueError("Recipe service differs from metadata")
        steps = recipe["services"][0]["steps"]
        check_steps(steps)
        downloads = [s for s in steps if s["methods"][-1]["method"] in
                     {"expect_download", "download_all"}]
        if not downloads and metadata["validation"]["realProvider"] != "blocked-no-invoices":
            raise ValueError("At least one tracked download is required")
        if steps[0]["methods"][0]["method"] != "goto":
            raise ValueError("Expected public HTTPS entry point")
        if metadata["status"] == "qualified":
            proof = metadata["validation"]
            expected_count = proof.get("expectedDocuments")
            if (not isinstance(expected_count, int) or isinstance(expected_count, bool) or expected_count < 1
                    or not proof.get("date")
                    or metadata["coverage"] != "all-available-invoices"
                    or proof["realProvider"] != "two-pass-qualified"
                    or proof.get("firstRunNew") != expected_count
                    or proof.get("firstRunPdfReadback") != expected_count
                    or proof.get("repeatRunNew") != 0
                    or proof.get("firstRunClicks") != expected_count
                    or proof.get("firstRunDownloadEvents") != expected_count
                    or proof.get("repeatRunClicks") != 0
                    or proof.get("repeatRunDownloadEvents") != 0
                    or proof.get("independentSessions") is not True
                    or proof.get("recipeSha256") != hashlib.sha256(data).hexdigest()):
                raise ValueError("Qualified metadata must bind complete two-pass proof to this recipe")
            if any(s["methods"][0]["method"] == "wait_user" for s in steps):
                raise ValueError("Qualified unattended recipes cannot wait for an operator")
            for step in downloads:
                method = step["methods"][-1]
                options = {k: v for arg in method.get("arguments", []) for k, v in arg.items()}
                if method["method"] != "download_all" or options.get("incremental") is not True or options.get("key_attribute") != "data-bc-invoice-key":
                    raise ValueError("Qualified recipes require stable incremental invoice keys")
        if expected.name in files:
            raise ValueError("Duplicate export filename")
        files[expected.name] = data
    return files


def export(source, destination, revision):
    if revision != REVISION:
        raise ValueError("Unsupported engine revision")
    files = catalog(source)  # Validate everything before creating the destination.
    if destination.is_symlink():
        raise ValueError("Destination must not be a symlink")
    destination.mkdir(parents=True, exist_ok=True)
    previous = set()
    manifest = destination / MANIFEST
    if manifest.exists():
        content = json.loads(manifest.read_text())
        if content.get("engine") != "playwright-daemon" or not isinstance(content.get("files"), list):
            raise ValueError("Invalid ownership manifest")
        previous = set(content["files"])
        if any(not isinstance(n, str) or Path(n).name != n or
               not (n == SCHEMA or (n.startswith("recipe-pw__") and n.endswith(".yaml")))
               for n in previous):
            raise ValueError("Unsafe ownership manifest")
    for path in destination.iterdir():
        if path.name.startswith(("bc-recipe__", "bc-metadata__")):
            raise ValueError("Mixed Selenium destination")
        if path.name.startswith("recipe-pw__") and path.name not in previous:
            raise ValueError("Unmanaged Playwright recipe")
    if (destination / SCHEMA).exists() and (destination / SCHEMA).read_bytes() != files[SCHEMA]:
        raise ValueError("Existing runtime schema differs")
    files[MANIFEST] = (json.dumps({"engine": "playwright-daemon", "revision": revision,
                                  "files": sorted(files)}, indent=2) + "\n").encode()
    affected = previous | set(files)
    for name in affected:
        target = destination / name
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError("Managed paths must be regular files")
    backup = {n: (destination / n).read_bytes() if (destination / n).exists() else None
              for n in affected}
    # The destination is a release directory, never a live daemon directory.
    # Per-file replace is atomic. Caught errors restore the complete previous set.
    # A process death is not a directory transaction: discard that release directory.
    with tempfile.TemporaryDirectory(prefix=".bc-export-", dir=destination) as temporary:
        staging = Path(temporary)
        for name, data in files.items():
            (staging / name).write_bytes(data)
        try:
            for name in sorted(files):
                os.replace(staging / name, destination / name)
            for name in previous - set(files):
                (destination / name).unlink(missing_ok=True)
        except Exception:
            for name, data in backup.items():
                target = destination / name
                if data is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(data)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--engine-revision", required=True)
    args = parser.parse_args()
    export(args.source, args.destination, args.engine_revision)
    print("Playwright release export validated")


if __name__ == "__main__":
    main()
