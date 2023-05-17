# `catdev` entry point
import asyncio
from pathlib import Path

import typer

from catala_devtools_fr.cli_util import set_basic_loglevel
from catala_devtools_fr.find_changes import find_changes
from catala_devtools_fr.query import get_backend

app = typer.Typer()


@app.command()
def diff(file: Path):
    with open(file, "r") as f:
        asyncio.run(find_changes(f, file_path=file))


@app.command()
def query(article_id: str):
    back = get_backend("legifrance")
    print(asyncio.run(back.query_article(article_id)))


if __name__ == "__main__":
    set_basic_loglevel()

    app()
