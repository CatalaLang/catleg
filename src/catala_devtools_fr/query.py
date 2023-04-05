"""
Utilities for querying various data sources for law texts:
  - legifrance
  - legistix database (standalone)
"""

from typing import Optional
from catala_devtools_fr.article import Article, ArticleType, parse_article_id
import httpx
import json


def query_article(id: str) -> Optional[Article]:
    pass

def _query_article_legistix(id: str):
    pass

def _query_article_legifrance(id: str, legifrance_options=None):
    typ, id = parse_article_id(id)
    match typ:
        case ArticleType.LEGIARTI:
            pass 
        case _:
            raise ValueError("Unknown article type")

def _get_legifrance_token(client_id: str, client_secret: str):
    data = {"grant_type": "client_credentials", 
            "scope": "openid",
            "client_id": client_id, 
            "client_secret": client_secret
            }
    reply = httpx.post("https://oauth.aife.economie.gouv.fr/api/oauth/token", data=data)
    reply.raise_for_status()
    return json.loads(reply.text)
