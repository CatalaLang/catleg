"""
Utilities for querying various data sources for law texts:
  - legifrance
  - legistix database (standalone)
  - legistix database (auto-api via datasette)
"""

import asyncio
import datetime
import functools
import json
import logging
from types import SimpleNamespace
from typing import Iterable, Optional, Protocol

import aiometer
import httpx

from catala_devtools_fr.article import Article, ArticleType, parse_article_id
from catala_devtools_fr.cli_util import set_basic_loglevel
from catala_devtools_fr.config import settings


class Backend(Protocol):
    async def query_article(self, id: str) -> Optional[Article]:
        ...

    async def query_articles(self, ids: Iterable[str]) -> Iterable[Optional[Article]]:
        ...


class LegifranceBackend(Backend):
    def __init__(self, client_id, client_secret):
        self.client = httpx.AsyncClient(auth=LegifranceAuth(client_id, client_secret))

    async def query_article(self, id: str) -> Optional[Article]:
        reply = await self._query_article_legi(id)
        article = _article_from_legifrance_reply(reply)
        if article is None:
            logging.warning(f"Could not retrieve article {id} (wrong identifier?)")
        return article

    async def query_articles(self, ids: Iterable[str]) -> Iterable[Optional[Article]]:
        jobs = [functools.partial(self._query_article_legi, id) for id in ids]
        replies = await aiometer.run_all(jobs, max_at_once=10, max_per_second=15)
        return [_article_from_legifrance_reply(reply) for reply in replies]

    async def _query_article_legi(self, id: str):
        typ, id = parse_article_id(id)
        headers = {"Accept": "application/json"}
        api_base_url = "https://api.aife.economie.gouv.fr/dila/legifrance/lf-engine-app"
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
        reply = await self.client.post(url, headers=headers, json=params)
        reply.raise_for_status()
        return json.loads(reply.text)


def get_backend(spec: str):
    # TODO: multiple backends, fallbacks...
    client_id, client_secret = _get_legifrance_credentials(raise_if_missing=True)
    return LegifranceBackend(client_id, client_secret)


def _get_legifrance_credentials(*, raise_if_missing=True):
    client_id = settings.get("lf_client_id")
    client_secret = settings.get("lf_client_secret")
    if raise_if_missing:
        if (client_id is None) or (client_secret is None):
            raise ValueError(
                "Please supply Legifrance credentials \
                         (using .catdev_secrets.toml or in the environment)"
            )
    return client_id, client_secret


def _article_from_legifrance_reply(reply) -> Optional[Article]:
    if "article" in reply:
        article = reply["article"]
        if article is None:
            return None
    elif "text" in reply:
        article = reply["article"]
    else:
        raise ValueError("Could not parse Legifrance reply")
    text = article["texte"]
    id = article["id"]
    return SimpleNamespace(
        text=text,
        id=id,
        expiration_date=None,
        new_version=None,
    )


class LegifranceAuth(httpx.Auth):
    """
    Manages authentication for Legifrance API access
    Requires a client id and a client secret, uses those
    to fetch and refresh an access token and passes it along
    in requests.

    Note that the auth flow is synchronous, this is on purpose
    (we do not expect frequent token refreshes).
    See https://github.com/encode/httpx/issues/1176#issuecomment-674381420
    """

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expires_at: Optional[datetime.datetime] = None

    def auth_flow(self, request: httpx.Request):
        if self.token is None or self.token_expires_at <= datetime.datetime.now():
            logging.info("Requesting auth token")
            data = {
                "grant_type": "client_credentials",
                "scope": "openid",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            resp = httpx.post(
                "https://oauth.aife.economie.gouv.fr/api/oauth/token", data=data
            )
            if not 200 <= resp.status_code < 300:
                yield resp
            resp_json = json.loads(resp.text)
            self.token = resp_json["access_token"]
            expires_in = int(resp_json["expires_in"])
            self.token_expires_at = datetime.datetime.now() + datetime.timedelta(
                seconds=expires_in
            )
        else:
            logging.info("Using existing auth token")

        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


if __name__ == "__main__":
    # Example use
    set_basic_loglevel()
    back = get_backend("legifrance")
    print(asyncio.run(back.query_article("LEGIARTI000038814944")))
