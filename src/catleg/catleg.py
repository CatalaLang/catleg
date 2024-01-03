import asyncio
import json
from pathlib import Path
from typing import Annotated, Optional

import typer

from catleg.check_expiry import check_expiry as expiry
from catleg.cli_util import article_id_or_url, parse_legifrance_url, set_basic_loglevel
from catleg.find_changes import find_changes
from catleg.query import get_backend
from catleg.skeleton import article_skeleton as askel, markdown_skeleton

app = typer.Typer(add_completion=False)
# legifrance-specific commands (query legifrance API and return
# raw JSON)
lf = typer.Typer()
app.add_typer(lf, name="lf", help="Commands for querying the raw Legifrance API")


def _article(aid_or_url: str):
    article_id = article_id_or_url(aid_or_url)
    if article_id is None:
        raise ValueError(f"Sorry, I do not know how to process {article_id_or_url}")

    skel = asyncio.run(askel(article_id))
    return skel


@app.command()
def article(
    aid_or_url: Annotated[
        str,
        typer.Argument(
            help="An article ID or Legifrance URL, for instance 'LEGIARTI000033971416' "
            "or 'https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033971416'."
        ),
    ]
):
    """
    Output an article.
    By default, outputs markdown-formatted text.
    """

    print(_article(aid_or_url))


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


def _skeleton(url_or_textid: str, sectionid: str | None):
    """
    Output a given section of a law text.
    """
    if sectionid is not None:
        textid = url_or_textid
    else:
        res = parse_legifrance_url(url_or_textid)
        match res:
            case ["section", textid, sectionid]:
                textid, sectionid = textid, sectionid
            case _:
                raise ValueError(f"Sorry, I do not know how to process {url_or_textid}")
    skel = asyncio.run(markdown_skeleton(textid, sectionid))
    return skel


@app.command()
def skeleton(
    url_or_textid: str,
    sectionid: Annotated[Optional[str], typer.Argument()] = None,  # noqa: UP007
):
    print(_skeleton(url_or_textid, sectionid))


def _lf_article(aid_or_url: str):
    article_id = article_id_or_url(aid_or_url)
    if article_id is None:
        raise ValueError(f"Sorry, I do not know how to fetch {aid_or_url}")

    back = get_backend("legifrance")
    return asyncio.run(back.query_article_legi(article_id))


@lf.command("article")
def lf_article(
    aid_or_url: Annotated[
        str,
        typer.Argument(
            help="An article ID or Legifrance URL, for instance 'LEGIARTI000033971416' "
            "or 'https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033971416'."
        ),
    ]
):
    """
    Retrieve an article from Legifrance.
    Outputs the raw Legifrance JSON representation.
    """
    json.dumps(
        _lf_article(aid_or_url),
        indent=2,
        ensure_ascii=False,
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
