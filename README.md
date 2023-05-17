# catala-devtools-fr

A library of helper tools for [catala](https://catala-lang.org) programming in the context
of French legislative texts.

## Installing

`catala-devtools-fr` is not released on PyPI yet ; install it by running `pip install -e .` from a source clone.

## Running `catdev`

Run `catdev --help` for a list of commands.

## Development install

Run `pip install -e .[dev]` for a local, editable install that includes development dependencies.

`catala-devtools-fr` uses [tox](https://tox.wiki/en/latest/) to run linters and unit tests in various environments.

Run `tox` to execute tests and linters.

Formatting and import ordering is done by [µFmt](https://ufmt.omnilib.dev/en/stable/index.html) which is basically black + µsort.
To ensure code is always formatted before a commit, you can use the supplied [pre-commit](https://pre-commit.com) hook.

Run this once:

`pre-commit install`

Then, before every commit, the code will be reformatted automatically.
