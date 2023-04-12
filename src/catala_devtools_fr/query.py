"""
Utilities for querying various data sources for law texts:
  - legifrance
  - legistix database (standalone)
  - legistix database (auto-api via datasette)
"""

import datetime
from typing import Optional, Protocol
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

def _query_article_legifrance(id: str, legifrance_args=None) -> Article:
    client_id = settings.get("client_id")
    client_secret = settings.get("client_secret")
    _check_nonempty_legifrance_credentials(client_id, client_secret)

    typ, id = parse_article_id(id)
    headers = {"Accept": "application/json"}
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

    # TODO: reuse client
    with httpx.Client(auth=LegifranceAuth(client_id, client_secret)) as client:
        # A POST request to fetch an article?
        # And no way of using a simple query string?
        # Really, Legifrance?
        reply = client.post(url, headers=headers, json=params)
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


class LegifranceAuth(httpx.Auth):
    """
    Manages authentication for Legifrance API access
    Requires a client id and a client secret, uses those
    to fetch and refresh an access token and passes it along
    in requests.
    """
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expires_at: Optional[datetime.datetime] = None
    
    def auth_flow(self, request: httpx.Request):
        if self.token is None or self.token_expires_at <= datetime.datetime.now():
            data = {"grant_type": "client_credentials", 
            "scope": "openid",
            "client_id": self.client_id, 
            "client_secret": self.client_secret
            }
            resp = httpx.post("https://oauth.aife.economie.gouv.fr/api/oauth/token", data=data)
            if not 200 <= resp.status_code < 300:
                yield resp
            resp_json = json.loads(resp.text)
            self.token = resp_json['access_token']
            expires_in = int(resp_json['expires_in'])
            self.token_expires_at = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
        
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request

    
if __name__ == "__main__":
    """Example use"""
    print(query_article("LEGIARTI000038814944"))