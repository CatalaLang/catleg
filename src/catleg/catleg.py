import asyncio
import json
import sys
from pathlib import Path

import typer

from catleg.check_expiry import check_expiry as expiry
from catleg.cli_util import article_id_or_url, set_basic_loglevel
from catleg.find_changes import find_changes
from catleg.query import get_backend
from catleg.skeleton import article_skeleton as askel, markdown_skeleton

app = typer.Typer(add_completion=False)
# legifrance-specific commands (query legifrance API and return
# raw JSON)
lf = typer.Typer()
app.add_typer(lf, name="lf", help="Commands for querying the raw Legifrance API")


@app.command()
def article(aid_or_url: str):
    """
    Output an article.
    By default, outputs markdown-formatted text
    """
    article_id = article_id_or_url(aid_or_url)
    if article_id is None:
        print(f"Sorry, I do not know how to fetch {article_id_or_url}", file=sys.stderr)
        return 1

    skel = asyncio.run(askel(article_id))
    print(skel)


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
def skeleton(textid: str, sectionid: str):
    """
    Output a given section of a law text.
    """
    skel = asyncio.run(markdown_skeleton(textid, sectionid))
    print(skel)


@lf.command("article")
def lf_article(aid_or_url: str):
    """
    Retrieve an article from Legifrance.
    Outputs the raw Legifrance JSON representation.
    """
    article_id = article_id_or_url(aid_or_url)
    if article_id is None:
        print(f"Sorry, I do not know how to fetch {article_id_or_url}", file=sys.stderr)
        return 1

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
