#!/bin/sh
set -eu

source_dir=${1:-.}
destination_dir=${2:-./export}

if [ ! -d "$source_dir/recipes" ]; then
  echo "Recipe source not found: $source_dir/recipes" >&2
  exit 1
fi

mkdir -p "$destination_dir"

find "$destination_dir" -maxdepth 1 -type f \
  -name 'bc-recipe__*.yaml' -delete

found=0
for recipe in "$source_dir"/recipes/*/bc-recipe__*.yaml; do
  if [ ! -f "$recipe" ]; then
    continue
  fi
  cp "$recipe" "$destination_dir/"
  provider_dir=$(dirname "$recipe")
  service_name=$(basename "$recipe" .yaml)
  service_name=${service_name#bc-recipe__}
  metadata="$provider_dir/metadata.yaml"
  if [ ! -f "$metadata" ]; then
    echo "Metadata not found for $service_name." >&2
    exit 1
  fi
  cp "$metadata" "$destination_dir/bc-metadata__${service_name}.yaml"
  found=1
done

if [ "$found" -ne 1 ]; then
  echo "No deployable recipes found." >&2
  exit 1
fi

echo "Recipes exported to $destination_dir"
