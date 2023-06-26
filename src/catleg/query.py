"""
Utilities for querying various data sources for law texts:
  - legifrance
  - legistix database (standalone)
  - legistix database (auto-api via datasette)
"""

import datetime
import functools
import logging
from typing import Iterable, Optional, Protocol

import aiometer
import httpx
from markdownify import markdownify as md  # type: ignore

from catleg.config import settings

from catleg.law_text_fr import Article, ArticleType, parse_article_id


class Backend(Protocol):
    async def article(self, id: str) -> Optional[Article]:
        """
        Retrieve a law article.
        """
        ...

    async def articles(self, ids: Iterable[str]) -> Iterable[Optional[Article]]:
        ...

    async def list_codes(self):
        """
        List available codes.
        """
        ...

    async def code_toc(self, id: str):
        """
        Retrieve the structure of a law code (i.e sections,
        subsections... up to articles).
        Does not include article text.
        """
        ...


class LegifranceBackend(Backend):
    API_BASE_URL = "https://api.aife.economie.gouv.fr/dila/legifrance/lf-engine-app"

    def __init__(self, client_id, client_secret):
        headers = {"Accept": "application/json"}
        self.client = httpx.AsyncClient(
            auth=LegifranceAuth(client_id, client_secret), headers=headers
        )

    async def article(self, id: str) -> Optional[Article]:
        reply = await self.query_article_legi(id)
        article = _article_from_legifrance_reply(reply)
        if article is None:
            logging.warning(f"Could not retrieve article {id} (wrong identifier?)")
        return article

    async def articles(self, ids: Iterable[str]) -> Iterable[Optional[Article]]:
        jobs = [functools.partial(self.query_article_legi, id) for id in ids]
        replies = await aiometer.run_all(jobs, max_at_once=10, max_per_second=15)
        return [_article_from_legifrance_reply(reply) for reply in replies]

    async def list_codes(self):
        # TODO pagination
        params = {"pageSize": 100, "pageNumber": 1, "states": ["VIGUEUR"]}
        reply = await self.client.post(f"{self.API_BASE_URL}/list/code", json=params)
        reply.raise_for_status()
        reply_json = reply.json()
        return reply_json["results"]

    async def code_toc(self, id: str):
        params = {"textId": id, "date": str(datetime.date.today())}
        reply = await self.client.post(
            f"{self.API_BASE_URL}/consult/legi/tableMatieres", json=params
        )
        reply.raise_for_status()
        if "sections" not in reply.json():
            raise ValueError(f"Could not retrieve TOC for text {id}")
        return reply.json()

    async def query_article_legi(self, id: str):
        typ, id = parse_article_id(id)
        match typ:
            case ArticleType.LEGIARTI | ArticleType.JORFARTI:
                url = f"{self.API_BASE_URL}/consult/getArticle"
                params = {"id": id}
            case ArticleType.CETATEXT:
                url = f"{self.API_BASE_URL}/consult/juri"
                params = {"textId": id}
            case _:
                raise ValueError("Unknown article type")

        # A POST request to fetch an article?
        # And no way of using a simple query string?
        # Really, Legifrance?
        reply = await self.client.post(url, json=params)
        reply.raise_for_status()
        return reply.json()


def get_backend(spec: str):
    # TODO: multiple backends, fallbacks...
    assert spec == "legifrance"
    client_id, client_secret = _get_legifrance_credentials(raise_if_missing=True)
    return LegifranceBackend(client_id, client_secret)


class LegifranceArticle(Article):
    def __init__(self, id: str, text: str, text_html: str, nota: str, nota_html: str):
        self._id = id
        self._text = text
        self._text_html = text_html
        self._nota = nota
        self._nota_html = nota_html

    @property
    def id(self) -> str:
        return self._id

    @property
    def text(self) -> str:
        return self._text

    @property
    def text_html(self) -> str:
        return self._text_html

    @property
    def nota(self) -> str:
        return self._nota

    @property
    def nota_html(self) -> str:
        return self._nota_html

    @property
    def type(self) -> ArticleType:
        return parse_article_id(self.id)[0]

    def to_markdown(self) -> str:
        text_md = md(self.text_html).strip()
        if len(self.nota_html):
            nota_md = md(self.nota_html).strip()
            text_md += f"\n\nNOTA :\n\n{nota_md}"
        return text_md


def _get_legifrance_credentials(*, raise_if_missing=True):
    client_id = settings.get("lf_client_id")
    client_secret = settings.get("lf_client_secret")
    if raise_if_missing:
        if (client_id is None) or (client_secret is None):
            raise ValueError(
                "Please supply Legifrance credentials \
                         (using .catleg_secrets.toml or in the environment)"
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

    return LegifranceArticle(
        id=article["id"],
        text=article["texte"],
        text_html=article["texteHtml"],
        nota=article["nota"],
        nota_html=article["notaHtml"],
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
            resp_json = resp.json()
            self.token = resp_json["access_token"]
            expires_in = int(resp_json["expires_in"])
            self.token_expires_at = datetime.datetime.now() + datetime.timedelta(
                seconds=expires_in
            )
        else:
            logging.info("Using existing auth token")

        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request
