"""
Utilities for querying various data sources for law texts:
  - legifrance
  - legistix database (standalone)
  - legistix database (auto-api via datasette)
"""

from typing import Optional
from catala_devtools_fr.article import Article, ArticleType, parse_article_id
from catala_devtools_fr.config import settings
import httpx
import json


def query_article(id: str) -> Optional[Article]:
    pass

def _query_article_legistix(id: str):
    raise NotImplementedError("Coming soon...")

def _check_nonempty_legifrance_credentials(client_id, client_secret):
    if (client_id is None) or (client_secret is None):
        raise ValueError("Please supply Legifrance credentials \
                         (using .catdev_secrets.toml or in the environment)")

def _check_and_refresh_token() -> str:
    pass

def _query_article_legifrance(id: str, legifrance_args=None) -> Article:
    client_id = settings.get("client_id")
    client_secret = settings.get("client_secret")
    _check_nonempty_legifrance_credentials(client_id, client_secret)

    # XXX TODO: check for an existing token and refresh as needed
    token = _get_legifrance_token(client_id, client_secret)['access_token']

    typ, id = parse_article_id(id)
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/json"}
    api_base_url = "https://api.aife.economie.gouv.fr/dila/legifrance-beta/lf-engine-app"
    params = {}
    match typ:
        case ArticleType.LEGIARTI | ArticleType.JORFARTI:
            url = f"{api_base_url}/consult/getArticle"
            params = {"id": id}
        case ArticleType.CETATEXT:
            raise NotImplementedError("Should be with us real soon now :)")
        case _:
            raise ValueError("Unknown article type")

    # A POST request to fetch an article?!?
    # And no way to use a simple query-param?
    # Really, Legifrance?
    reply = httpx.post(url, headers=headers, json=params)
    reply.raise_for_status()
    return reply

def _get_legifrance_token(client_id: str, client_secret: str):
    data = {"grant_type": "client_credentials", 
            "scope": "openid",
            "client_id": client_id, 
            "client_secret": client_secret
            }
    reply = httpx.post("https://oauth.aife.economie.gouv.fr/api/oauth/token", data=data)
    reply.raise_for_status()
    return json.loads(reply.text)

if __name__ == "__main__":
    """Example use"""
    print(_query_article_legifrance("LEGIARTI000038814944").text)