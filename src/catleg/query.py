"""
Utilities for querying various data sources for law texts:
  - legifrance
  - legistix database (standalone)
  - legistix database (auto-api via datasette)
"""

import functools
import logging
from collections.abc import Iterable
from datetime import date, datetime, timedelta, timezone
from typing import Protocol

import aiometer
import httpx
from markdownify import markdownify as md  # type: ignore
from typing_extensions import assert_never

from catleg.config import settings

from catleg.law_text_fr import Article, ArticleType, parse_article_id


def _lf_timestamp_to_datetime(ts):
    return datetime.fromtimestamp(ts / 1000, timezone.utc)


# Legifrance uses 2999-01-01 to mark a non-expired or non-expiring text
END_OF_TIME = _lf_timestamp_to_datetime(32472144000000)


class Backend(Protocol):
    async def article(self, id: str) -> Article | None:
        """
        Retrieve a law article.
        """
        ...

    async def articles(self, ids: Iterable[str]) -> Iterable[Article | None]:
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
    API_BASE_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"

    def __init__(self, client_id, client_secret):
        headers = {"Accept": "application/json"}
        self.client = httpx.AsyncClient(
            auth=LegifranceAuth(client_id, client_secret), headers=headers
        )

    async def article(self, id: str) -> Article | None:
        reply = await self.query_article_legi(id)
        article = _article_from_legifrance_reply(reply)
        if article is None:
            logging.warning(f"Could not retrieve article {id} (wrong identifier?)")
        return article

    async def articles(self, ids: Iterable[str]) -> Iterable[Article | None]:
        jobs = [functools.partial(self.query_article_legi, id) for id in ids]
        replies = await aiometer.run_all(jobs, max_at_once=10, max_per_second=15)
        return [_article_from_legifrance_reply(reply) for reply in replies]

    async def list_codes(self):
        return self._list_codes()[0]

    async def _list_codes(self, page_size=20):
        params = {"pageSize": page_size, "pageNumber": 1, "states": ["VIGUEUR"]}
        reply = await self.client.post(f"{self.API_BASE_URL}/list/code", json=params)
        reply.raise_for_status()
        reply_json = reply.json()
        nb_results = reply_json["totalResultNumber"]
        results = reply_json["results"]
        while len(results) < nb_results:
            params["pageNumber"] += 1
            reply = await self.client.post(
                f"{self.API_BASE_URL}/list/code", json=params
            )
            reply.raise_for_status()
            reply_json = reply.json()
            results += reply_json["results"]
        return results, nb_results

    async def code_toc(self, id: str):
        params = {"textId": id, "date": str(date.today())}
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
    def __init__(
        self,
        id: str,
        text: str,
        text_html: str,
        nota: str,
        nota_html: str,
        end_date: int | str | None,
        latest_version_id: str,
    ):
        self._id: str = id
        self._text: str = text
        self._text_html: str = text_html
        self._nota: str = nota
        self._nota_html: str = nota_html
        self._end_date: datetime = (
            _lf_timestamp_to_datetime(int(end_date))
            if end_date is not None
            else END_OF_TIME
        )
        self._latest_version_id = latest_version_id

    @property
    def end_date(self) -> datetime:
        return self._end_date

    @property
    def is_open_ended(self) -> bool:
        return self._end_date == END_OF_TIME

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
    def latest_version_id(self) -> str:
        return self._latest_version_id

    def text_and_nota(self) -> str:
        if len(self.nota):
            return f"{self._text}\n\nNOTA :\n\n{self._nota}"
        return self._text

    @property
    def type(self) -> ArticleType:
        return parse_article_id(self.id)[0]

    def to_markdown(self) -> str:
        text_md = md(self.text_html, strip=["a"]).strip()
        if len(self.nota_html):
            nota_md = md(self.nota_html, strip=["a"]).strip()
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


def _article_from_legifrance_reply(reply) -> Article | None:
    if "article" in reply:
        article = reply["article"]
        if article is None:
            return None
    elif "text" in reply:
        article = reply["text"]
        if article is None:
            return None
    else:
        raise ValueError("Could not parse Legifrance reply")

    article_type, article_id = parse_article_id(article["id"])
    match article_type:
        case ArticleType.CETATEXT:
            latest_version_id = article_id
        case ArticleType.LEGIARTI | ArticleType.JORFARTI:
            article_versions = sorted(
                article["articleVersions"], key=lambda d: int(d["dateDebut"])
            )
            latest_version_id = article_versions[-1]["id"]
        case _:
            assert_never()

    return LegifranceArticle(
        id=article["id"],
        text=article["texte"],
        text_html=article["texteHtml"],
        nota=article["nota"] or "",
        nota_html=article["notaHtml"] or "",
        end_date=article["dateFin"],
        latest_version_id=latest_version_id,
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
        self.token_expires_at: datetime | None = None

    def auth_flow(self, request: httpx.Request):
        if self.token is None or self.token_expires_at <= datetime.now():
            logging.info("Requesting auth token")
            data = {
                "grant_type": "client_credentials",
                "scope": "openid",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            resp = httpx.post("https://oauth.piste.gouv.fr/api/oauth/token", data=data)
            if not 200 <= resp.status_code < 300:
                yield resp
            resp_json = resp.json()
            self.token = resp_json["access_token"]
            expires_in = int(resp_json["expires_in"])
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
        else:
            logging.info("Using existing auth token")

        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request
