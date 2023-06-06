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
