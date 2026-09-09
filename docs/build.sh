#!/bin/sh
set -eu

cd "$(dirname "$0")"
project_dir=$(cd .. && pwd)
export UV_PROJECT_ENVIRONMENT="$project_dir/.venv-docs"

uv sync --project "$project_dir" --locked --all-extras --group docs --no-default-groups

# Dask 2024.8.0 cannot color task graphs with the locked NumPy 2 versions.
# Keep this exception in the docs environment and preserve other locked packages.
# New Dask includes dask-expr, whose old package pins Dask 2024.8.0.
uv pip uninstall --python "$UV_PROJECT_ENVIRONMENT" dask-expr
uv pip install --python "$UV_PROJECT_ENVIRONMENT" 'dask==2026.8.0'

exec uv run --project "$project_dir" --no-sync "$@"
