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
import sys
import warnings
from pathlib import Path
from typing import Optional, TextIO

from catleg.git_diff import wdiff

from catleg.parse_catala_markdown import parse_catala_file
from catleg.query import get_backend


async def find_changes(f: TextIO, *, file_path: Optional[Path] = None):
    # parse articles from file
    articles = parse_catala_file(f, file_path=file_path)

    # fetch articles' reference text
    # compute diff
    # display diff
    back = get_backend("legifrance")
    ref_articles = await back.articles([article.id.upper() for article in articles])

    diffcnt = 0
    for article, ref_article in zip(articles, ref_articles):
        if ref_article is None:
            warnings.warn(f"Could not retrieve article '{article.id}'")
            continue

        diff, retcode = wdiff(
            _reformat(article.text),
            _reformat(ref_article.text),
            return_exit_code=True,
            line_offset=article.start_line,
        )
        if retcode != 0:
            print(article.id)
            print(f"{article.file_path or 'UNKNOWN_FILE'}:{article.start_line}")
            sys.stdout.buffer.write(diff)
            diffcnt += 1
    if diffcnt > 0:
        sys.stdout.flush()
        print(
            f"Found {diffcnt} articles with diffs (out of {len(articles)} articles)",
            file=sys.stderr,
        )
    # (ci mode : error code != 0 if any diff?)


def _reformat(paragraph: str):
    """
    Catala has a 80-char line limit, so law texts will often be manually reformatted.
    We attempt to remove extra line breaks before comparison.
    """
    return paragraph.replace("\n", " ").strip().replace("  ", " ")
