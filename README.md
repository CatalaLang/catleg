# catleg

A library of helper tools for [catala](https://catala-lang.org) programming in the context
of French legislative texts.

## Installing

`catleg` requires python >= 3.10

### from PyPI

`pip install catleg`

### from a source clone

`pip install .`

### from github

`pip install 'catleg @ git+https://github.com/CatalaLang/catleg@main'`

You may replace `main` with any ref (commit SHA, tag, branch...)

## Running `catleg`

Run `catleg --help` for a list of commands.

### Legifrance credentials

`catleg` uses the Legifrance API (though we hope to provide our own API soon!) to access French legislative texts.

This API is authenticated and requires credentials, which may be obtained by registering on the
[Piste portal](https://piste.gouv.fr/).

To provide credentials to `catleg`, create a `.catleg_secrets.toml` file like so:

```toml
lf_client_id = "your_client_id"
lf_client_secret = "your_client_secret"
```

Alternatively, you may define the environment variables `CATLEG_LF_CLIENT_ID` and `CATLEG_LF_CLIENT_SECRET`.
