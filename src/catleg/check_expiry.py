import warnings
from pathlib import Path
from time import gmtime
from typing import TextIO

from catleg.parse_catala_markdown import parse_catala_file
from catleg.query import get_backend


async def check_expiry(f: TextIO, *, file_path: Path | None = None):
    # parse articles from file
    articles = parse_catala_file(f, file_path=file_path)

    back = get_backend("legifrance")
    ref_articles = await back.articles([article.id.upper() for article in articles])
    has_expired_articles = False
    now = gmtime()

    for article, ref_article in zip(articles, ref_articles):
        if ref_article is None:
            warnings.warn(f"Could not retrieve article '{article.id}'")
            continue

        if not ref_article.is_open_ended:
            if now > ref_article.date_fin:
                warnings.warn(
                    f"Article '{article.id}' has expired (on {ref_article.date_fin})"
                )
                has_expired_articles = True
            else:
                warnings.warn(
                    f"Article '{article.id}' is set to expire on {ref_article.date_fin}"
                )

    return 0 if not has_expired_articles else 1
