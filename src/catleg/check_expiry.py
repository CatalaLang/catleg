import logging
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

from catleg.parse_catala_markdown import parse_catala_file
from catleg.query import get_backend


logger = logging.getLogger(__name__)


async def check_expiry(f: TextIO, *, file_path: Path | None = None):
    # parse articles from file
    articles = parse_catala_file(f, file_path=file_path)

    back = get_backend("legifrance")
    ref_articles = await back.articles([article.id.upper() for article in articles])
    has_expired_articles = False
    now = datetime.now(timezone.utc)

    for article, ref_article in zip(articles, ref_articles):
        if ref_article is None:
            warnings.warn(f"Could not retrieve article '{article.id}'")
            continue

        if article.is_archive:
            logger.info("article '%s' is achived, skipping expiry check", article.id)
            continue

        logger.info("checking article '%s'", article.id)

        if not ref_article.is_open_ended:
            if now > ref_article.end_date:
                warnings.warn(
                    f"Article '{article.id}' has expired "
                    f"(on {ref_article.end_date.date()}). "
                    f"It has been replaced by '{ref_article.latest_version_id}'."
                )
                has_expired_articles = True
            else:
                warnings.warn(
                    f"Article '{article.id}' will expire "
                    f"on {ref_article.end_date.date()}. "
                    f"It will be replaced by '{ref_article.latest_version_id}'"
                )

    return 0 if not has_expired_articles else 1
