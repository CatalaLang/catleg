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
import warnings
from difflib import ndiff

from catala_devtools_fr.parse_catala_markdown import parse_catala_file
from catala_devtools_fr.query import get_backend


def find_changes(f):
    # parse articles from file
    articles = parse_catala_file(f)
    back = get_backend("legifrance")

    # fetch articles text (can/should be done in parallel)
    # compute diff
    # display diff
    diffcnt = 0
    for article in articles:
        ref_article = back.query_article(article.id.upper())
        if ref_article is None:
            warnings.warn(f"Could not retrieve article '{article.id}'")
            continue
        clean_text = _clean_article_text(article.text)
        clean_ref_text = _clean_article_text(ref_article.text)
        if clean_text != clean_ref_text:
            diff = ndiff(clean_text, clean_ref_text)
            print(article.id)
            print("".join(diff))
            diffcnt += 1
    if diffcnt > 0:
        print(
            f"found {diffcnt} articles with diffs (out of {len(articles)} articles)",
            file=sys.stderr,
        )
    # (ci mode : error code != 0 if any diff?)


def _clean_article_text(text: str) -> str:
    return text.replace("\n", "")


if __name__ == "__main__":
    """
    Example driver -- a proper CLI is needed too
    """
    import sys

    with open(sys.argv[1], "r") as f:
        find_changes(f)
