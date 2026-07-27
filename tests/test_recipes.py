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


if __name__ == "__main__":
    unittest.main()
