All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome.

For general information on how to contribute see https://sgkit-dev.github.io/sgkit/latest/contributing.html.

For local development, install uv 0.12.10 or newer and run:

```sh
uv sync --locked --all-extras
uv run --locked --all-extras pytest
uv run --locked --all-extras pre-commit install
```

See [the contributor guide](docs/contributing.rst) for dependency updates, documentation builds, and release checks.
