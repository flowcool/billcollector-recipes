"""Validate the catalog and export only managed Playwright runtime files."""
import argparse
import json
import os
import tempfile
from pathlib import Path

import yaml
from jsonschema import ValidationError, validate

REVISION = "89a89cc2c55c7dfc53ffb07acd73630621f2911b"
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
        elif names == ["bourse_direct"]:
            options = {k: v for arg in methods[0].get("arguments", []) for k, v in arg.items()}
            if (options.get("account_type") not in {"PEA", "PEA-PME"}
                    or type(options.get("max_months")) is not int
                    or not 1 <= options["max_months"] <= 120
                    or type(options.get("max_items")) is not int
                    or not 1 <= options["max_items"] <= 200
                    or type(options.get("timeout_ms")) is not int
                    or not 1 <= options["timeout_ms"] <= 7200000):
                raise ValueError("Invalid Bourse Direct bounds")
        elif names == ["login"]:
            args = {k: v for arg in methods[0].get("arguments", []) for k, v in arg.items()}
            if not args.get("success", {}).get("selector") or "submit" not in step:
                raise ValueError("Native login requires a success selector and submit block")
        elif names in (["locator", "click"], ["locator", "first", "click"]):
            if not methods[0].get("arguments", [{}])[0].get("selector"):
                raise ValueError("Missing selector")
            timeout = methods[-1].get("arguments", [{}])[0].get("timeout")
            if not isinstance(timeout, int) or not 0 < timeout <= 60000:
                raise ValueError("Click must have a finite timeout")
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
        try:
            validate(metadata, metadata_schema)
        except ValidationError as error:
            raise ValueError("Invalid provider metadata") from error
        service = metadata["service"]
        if service != provider.name:
            raise ValueError("Provider directory and service differ")
        recipes = list(provider.glob("recipe-pw__*.yaml"))
        expected = provider / f"recipe-pw__{service}.yaml"
        if recipes != [expected] or expected.is_symlink():
            raise ValueError("Expected exactly one named recipe per provider")
        data = expected.read_bytes()
        recipe = yaml.safe_load(data)
        try:
            validate(recipe, schema)
        except ValidationError as error:
            raise ValueError("Invalid provider recipe") from error
        if len(recipe.get("services", [])) != 1 or recipe["services"][0]["serviceName"] != service:
            raise ValueError("Recipe service differs from metadata")
        steps = recipe["services"][0]["steps"]
        check_steps(steps)
        tracked = [s for s in steps if s.get("methods") and
                   s["methods"][-1]["method"] in {"expect_download", "download_all", "bourse_direct"}]
        if len(tracked) != 1:
            raise ValueError("Current coverage requires one tracked download")
        if steps[0]["methods"][0]["method"] != "goto":
            raise ValueError("Expected public HTTPS entry point")
        if expected.name in files:
            raise ValueError("Duplicate export filename")
        files[expected.name] = data
        adapter = provider / f"{service}_adapter.py"
        if adapter.exists():
            if service != "bourse_direct" or adapter.is_symlink():
                raise ValueError("Unsupported adapter file")
            files[adapter.name] = adapter.read_bytes()
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
               not (n == SCHEMA or (n.startswith("recipe-pw__") and n.endswith(".yaml"))
                    or n == "bourse_direct_adapter.py")
               for n in previous):
            raise ValueError("Unsafe ownership manifest")
    for path in destination.iterdir():
        if path.name.startswith(("bc-recipe__", "bc-metadata__")):
            raise ValueError("Mixed Selenium destination")
        if path.name.startswith("recipe-pw__") and path.name not in previous:
            raise ValueError("Unmanaged Playwright recipe")
    if (destination / SCHEMA).exists() and (destination / SCHEMA).read_bytes() != files[SCHEMA]:
        raise ValueError("Existing runtime schema differs")
        if ((destination / "bourse_direct_adapter.py").exists()
                and "bourse_direct_adapter.py" not in previous):
            raise ValueError("Unmanaged adapter file")
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
