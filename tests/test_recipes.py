import unittest
from pathlib import Path

import yaml
from jsonschema import FormatChecker, validate


ROOT = Path(__file__).resolve().parents[1]


class RecipeRepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe_schema = yaml.safe_load(
            (ROOT / "schema" / "recipe.schema.json").read_text()
        )
        cls.metadata_schema = yaml.safe_load(
            (ROOT / "schema" / "metadata.schema.json").read_text()
        )

    def test_recipe_and_metadata_pairs(self):
        providers = sorted(path for path in (ROOT / "recipes").iterdir()
                           if path.is_dir())
        self.assertTrue(providers, "repository must contain a recipe")

        for provider in providers:
            metadata_path = provider / "metadata.yaml"
            self.assertTrue(metadata_path.is_file(), metadata_path)
            metadata = yaml.safe_load(metadata_path.read_text())
            validate(
                metadata,
                self.metadata_schema,
                format_checker=FormatChecker(),
            )

            recipe_path = provider / (
                f"bc-recipe__{metadata['service']}.yaml"
            )
            self.assertTrue(recipe_path.is_file(), recipe_path)
            recipe = yaml.safe_load(recipe_path.read_text())
            validate(recipe, self.recipe_schema)
            self.assertEqual(
                [metadata["service"]],
                [service["serviceName"] for service in recipe["services"]],
            )
            self.assertEqual(metadata["recipeFormatVersion"], 1)

            actions = {
                action["actionType"]
                for service in recipe["services"]
                for action in service["actions"]
            }
            self.assertEqual(set(metadata["requiredActions"]), actions)

    def test_recipe_filenames_are_unique(self):
        names = [
            path.name
            for path in (ROOT / "recipes").glob("*/bc-recipe__*.yaml")
        ]
        self.assertEqual(len(names), len(set(names)))

    def test_exported_runtime_contract_is_named_for_the_service(self):
        metadata = yaml.safe_load(
            (ROOT / "recipes" / "free" / "metadata.yaml").read_text()
        )
        expected = f"bc-metadata__{metadata['service']}.yaml"
        self.assertEqual(expected, "bc-metadata__free.yaml")

    def test_fulli_recipe_matches_the_public_two_step_login(self):
        recipe = yaml.safe_load(
            (ROOT / "recipes" / "fulli" / "bc-recipe__fulli.yaml")
            .read_text()
        )
        actions = recipe["services"][0]["actions"]
        self.assertEqual(
            ["SendKeys", "Click", "SendKeys", "Click"],
            [action["actionType"] for action in actions],
        )
        self.assertEqual(
            ["identifier", "otp-submit-btn", "password", "pass-submit-btn"],
            [action["parameters"]["locators"][0]["element"]
             for action in actions],
        )
        self.assertEqual(
            "{USERNAME}", actions[0]["parameters"]["variable"]
        )
        self.assertEqual(
            "{PASSWORD}", actions[2]["parameters"]["variable"]
        )


if __name__ == "__main__":
    unittest.main()
