"""
description copied from ocaml original

(** Parses the Catala master source file and checks each article:
    - if the article has a LégiFrance ID, checks the text of the article in the
      source code vs the text from LégiFrance;
    - if the article has an expiration date, display the difference between the
      current version of the article and the next one on LégiFrance;
    - fill each [@@Include ...@@] tag with the contents retrieved from
      LégiFrance *)

"""
import asyncio
import warnings

from catala_devtools_fr.cli_util import set_basic_loglevel
from catala_devtools_fr.git_diff import wdiff

from catala_devtools_fr.parse_catala_markdown import parse_catala_file
from catala_devtools_fr.query import get_backend


async def find_changes(f):
    # parse articles from file
    articles = parse_catala_file(f)

    # fetch articles' reference text
    # compute diff
    # display diff
    back = get_backend("legifrance")
    ref_articles = await back.query_articles(
        [article.id.upper() for article in articles]
    )

    diffcnt = 0
    for article, ref_article in zip(articles, ref_articles):
        if ref_article is None:
            warnings.warn(f"Could not retrieve article '{article.id}'")
            continue
        clean_text = _clean_article_text(article.text)
        clean_ref_text = _clean_article_text(ref_article.text)
        if clean_text != clean_ref_text:
            diff = wdiff(clean_text, clean_ref_text)
            print(article.id)
            print(diff)
            diffcnt += 1
    if diffcnt > 0:
        print(
            f"Found {diffcnt} articles with diffs (out of {len(articles)} articles)",
            file=sys.stderr,
        )
    # (ci mode : error code != 0 if any diff?)


def _clean_article_text(text: str) -> str:
    return text.replace("\n", "")


if __name__ == "__main__":
    # Example driver -- a proper CLI is needed too
    import sys

    set_basic_loglevel()

    with open(sys.argv[1], "r") as f:
        asyncio.run(find_changes(f))
