# catala-devtools-fr

A library of helper tools for [catala](https://catala-lang.org) programming in the context
of French legislative texts.

## Installing

`catala-devtools-fr` is not released on PyPI yet ; install it by running `pip install -e .` from a source clone.

## Running `catdev`

Run `catdev --help` for a list of commands.

### Legifrance credentials

`catdev` uses the Legifrance API (though we hope to orovide our own API soon!) to access French legislative texts.

This API is authenticated and requires credentials, which may be obtained by registering on the
[Piste portal](https://developer.aife.economie.gouv.fr/).

To provide credentials to `catdev`, create a `.catdev_secrets.toml` file like so:

```toml
lf_client_id = "your_client_id"
lf_client_secret = "your_client_secret"
```

Alternatively, you may define the environment variables `CATDEV_LF_CLIENT_ID` and `CATDEV_LF_CLIENT_SECRET`.

## Development install

Run `pip install -e .[dev]` for a local, editable install that includes development dependencies.

`catala-devtools-fr` uses [tox](https://tox.wiki/en/latest/) to run linters and unit tests in various environments.

Run `tox` to execute tests and linters.

Formatting and import ordering is done by [µFmt](https://ufmt.omnilib.dev/en/stable/index.html) which is basically black + µsort.

### Pre-commit hook

To ensure code is always formatted before a commit, you can use the supplied [pre-commit](https://pre-commit.com) hook.

Run this once:

`pre-commit install`

Then, before every commit, the code will be reformatted automatically.

The pre-commit hook will also run the `ruff` linter.
