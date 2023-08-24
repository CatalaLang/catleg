import sys
import warnings
from pathlib import Path
from typing import TextIO

from catleg.git_diff import wdiff

from catleg.parse_catala_markdown import parse_catala_file
from catleg.query import get_backend


async def find_changes(f: TextIO, *, file_path: Path | None = None):
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
            _reformat(_escape_ref_text(ref_article.text_and_nota())),
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
    paragraph = paragraph.replace("\n", " ")
    while "  " in paragraph:
        paragraph = paragraph.replace("  ", " ")
    return paragraph.strip()


def _escape_ref_text(paragraph: str):
    """
    Escape markdown special chars from reference text.
    Since we use the "raw text" version of the Legifrance article,
    we escape brackets and asteriks unconditionnally.
    """
    return paragraph.replace("[", r"\[").replace("]", r"\]").replace("*", r"\*")
