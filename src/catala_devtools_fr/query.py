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
    # TODO: configurable backends (legistix...)
    # and fallbacks (e.g. query legistix but use
    # Legifrance for CETATEXT records)
    reply = _query_article_legifrance(id)
    return _article_from_legifrance_reply(reply)

def _query_article_legistix(id: str):
    raise NotImplementedError("Coming soon...")

def _check_nonempty_legifrance_credentials(client_id, client_secret):
    if (client_id is None) or (client_secret is None):
        raise ValueError("Please supply Legifrance credentials \
                         (using .catdev_secrets.toml or in the environment)")

def _check_and_refresh_token(legifrance_args) -> str:
    if 'token' in legifrance_args:
        pass
    else:
        return _get_legifrance_token()

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
    match typ:
        case ArticleType.LEGIARTI | ArticleType.JORFARTI:
            url = f"{api_base_url}/consult/getArticle"
            params = {"id": id}
        case ArticleType.CETATEXT:
            url = f"{api_base_url}/consult/juri"
            params = {"textId": id}
        case _:
            raise ValueError("Unknown article type")

    # A POST request to fetch an article?
    # And no way of using a simple query string?
    # Really, Legifrance?
    reply = httpx.post(url, headers=headers, json=params)
    reply.raise_for_status()
    return json.loads(reply.text)

def _get_legifrance_token(client_id: str, client_secret: str):
    data = {"grant_type": "client_credentials", 
            "scope": "openid",
            "client_id": client_id, 
            "client_secret": client_secret
            }
    reply = httpx.post("https://oauth.aife.economie.gouv.fr/api/oauth/token", data=data)
    reply.raise_for_status()
    return json.loads(reply.text)

def _article_from_legifrance_reply(reply):
    if 'article' in reply:
        article = reply['article']
    elif 'text' in reply:
        article = reply['article']
    else:
        raise ValueError("cannot parse Legifrance reply")
    text = article['texte']
    id = article['id']
    return {
        'text': text,
        'id': id,
        'expiration_date': None,
        'new_version': None,
    }

if __name__ == "__main__":
    """Example use"""
    print(query_article("LEGIARTI000038814944"))