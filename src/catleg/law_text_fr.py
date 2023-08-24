import re
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Protocol

from more_itertools import intersperse

ArticleType = Enum("ArticleType", ["LEGIARTI", "CETATEXT", "JORFARTI"])


class Article(Protocol):
    @property
    def type(self) -> ArticleType:
        ...

    @property
    def id(self) -> str:
        """Article identifier, for instance LEGIARTI000038814944"""
        ...

    @property
    def text(self) -> str:
        ...


class ExpiryInfo(Protocol):
    @property
    def expiration_date(self) -> date:
        ...


class NewVersionInfo(Protocol):
    @property
    def new_version(self) -> str:
        ...


class FileLineInfo(Protocol):
    @property
    def file_path(self) -> Path | None:
        ...

    @property
    def start_line(self) -> int:
        ...


@dataclass(frozen=True)
class CatalaFileArticle:
    type: ArticleType
    id: str
    text: str
    file_path: Path | None
    start_line: int
    is_archive: bool


def parse_article_id(article_id: str) -> tuple[ArticleType, str]:
    """
    Parse a string that looks like 'article-l822-2-legiarti000038814944'
    and return (ArticleType.LEGIARTI, 'legiarti000038814944')
    """
    article_id = article_id.split("-")[-1]
    typ = ArticleType[article_id[:8].upper()]
    return typ, article_id


# Some people, when confronted with a problem, think
# "I know, I'll use regular expressions."
# Now they have two problems. (Jamie Zawinsky)
TYPES_OR_REGEX = "".join(intersperse("|", [typ.name for typ in ArticleType]))
ARTICLE_ID_REGEX = re.compile(f"\\b(({TYPES_OR_REGEX})[0-9]{{12}})\\b")


def find_id_in_string(text: str) -> tuple[ArticleType, str] | None:
    """
    Finds an article ID in a string, returns a tuple (ArticleType, ID)
    if found or None if the string does not contain an article ID.
    """
    match = ARTICLE_ID_REGEX.search(text)
    if match:
        return parse_article_id(match.group(0))
    return None
