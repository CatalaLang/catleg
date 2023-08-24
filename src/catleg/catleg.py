import asyncio
import json
from pathlib import Path

import typer

from catleg.check_expiry import check_expiry as expiry
from catleg.cli_util import set_basic_loglevel
from catleg.find_changes import find_changes
from catleg.query import get_backend
from catleg.skeleton import markdown_skeleton

app = typer.Typer(add_completion=False)
# legifrance-specific commands (query legifrance API and return
# raw JSON)
lf = typer.Typer()
app.add_typer(lf, name="lf", help="Commands for querying the raw Legifrance API")


@app.command()
def diff(file: Path):
    """
    Show differences between each article in a catala file and
    a reference version.
    """
    with open(file) as f:
        asyncio.run(find_changes(f, file_path=file))


@app.command()
def check_expiry(file: Path):
    """
    Check articles in a catala file for expiry.
    """
    with open(file) as f:
        retcode = asyncio.run(expiry(f, file_path=file))
        raise typer.Exit(retcode)


@app.command()
def query(article_id: str):
    """
    Retrieve a reference version of a French law article.
    """
    back = get_backend("legifrance")
    print(asyncio.run(back.article(article_id)))


@app.command()
def skeleton(textid: str, sectionid: str):
    """
    Output a given section of a law text.
    """
    skel = asyncio.run(markdown_skeleton(textid, sectionid))
    print(skel)


@lf.command()
def article(article_id: str):
    """Retrieve an article from Legifrance"""
    back = get_backend("legifrance")
    print(
        json.dumps(
            asyncio.run(back.query_article_legi(article_id)),
            indent=2,
            ensure_ascii=False,
        )
    )


@lf.command()
def codes():
    """
    Retrieve a list of available codes.
    """
    back = get_backend("legifrance")
    print(json.dumps(asyncio.run(back.list_codes()), indent=2, ensure_ascii=False))


@lf.command()
def toc(code: str):
    """
    Retrieve the table of contents for a given code.
    """
    back = get_backend("legifrance")
    print(json.dumps(asyncio.run(back.code_toc(code)), indent=2, ensure_ascii=False))


def main():
    set_basic_loglevel()

    app()
