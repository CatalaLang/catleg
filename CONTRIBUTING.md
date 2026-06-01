# Contributing to catleg 🐱⚖️

Thanks for contributing! Here are a few hints to get you started.

## Development install

From a source clone, run `pip install -e .[dev]` for a local, editable install that includes development dependencies.

`catleg` uses [tox](https://tox.wiki/en/latest/) to run linters and unit tests in various environments.

Run `tox` to execute tests and linters.

Formatting and import ordering is done by [µFmt](https://ufmt.omnilib.dev/en/stable/index.html) which is basically black + µsort.

### Pre-commit hook

To ensure code is always formatted before a commit, you can use the supplied [pre-commit](https://pre-commit.com) hook.

Run this once:

`pre-commit install`

Then, before every commit, the code will be reformatted automatically.

The pre-commit hook will also run the `ruff` linter.

## Releasing a new version

The version is derived automatically from git tags via `hatch-vcs`, so creating a release is just a matter of tagging.

1. Go to the repository on GitHub → **Releases** → **Draft a new release**.
2. Create a new tag (e.g. `v0.2.10`) targeting `main` and publish the release.
3. The `publish` CI workflow triggers automatically: it runs the full test matrix, then builds and uploads the package to PyPI.
