"""
Current OCaml API


val get_article_id : article -> string
val get_article_text : article -> string
val get_article_title : article -> string
val get_article_expiration_date : article -> Unix.tm
val get_article_new_version : article -> string

"""
from datetime import date
from enum import Enum
from typing import Protocol, Tuple

ArticleType = Enum("ArticleType", ["LEGIARTI", "CETATEXT", "JORFARTI"])


class Article(Protocol):
    @property
    def id(self) -> str:
        """ """
        pass

    @property
    def text(self) -> str:
        """ """
        pass

    @property
    def expiration_date(self) -> date:
        """ """
        pass

    @property
    def new_version(self) -> str:
        """ """
        pass


def parse_article_id(article_id: str) -> Tuple[ArticleType, str]:
    """
    Parse a string that looks like 'article-l822-2-legiarti000038814944'
    and return (ArticleType.LEGIARTI, 'legiarti000038814944')
    """
    article_id = article_id.split("-")[-1]
    typ = ArticleType[article_id[:8].upper()]
    return typ, article_id
