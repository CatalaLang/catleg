# `catdev` entry point
import asyncio
import json
from pathlib import Path

import typer

from catala_devtools_fr.cli_util import set_basic_loglevel
from catala_devtools_fr.find_changes import find_changes
from catala_devtools_fr.query import get_backend

app = typer.Typer()


@app.command()
def diff(file: Path):
    """
    Show differences between each article in a catala file and
    a reference version.
    """
    with open(file, "r") as f:
        asyncio.run(find_changes(f, file_path=file))


@app.command()
def query(article_id: str):
    """
    Retrieve a reference version of a French law article.
    """
    back = get_backend("legifrance")
    print(asyncio.run(back.article(article_id)))


@app.command()
def codes():
    """
    Retrieve a list of available codes.
    """
    back = get_backend("legifrance")
    print(json.dumps(asyncio.run(back.list_codes()), indent=2))


def main():
    set_basic_loglevel()

    app()
