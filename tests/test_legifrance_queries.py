import asyncio
import os
from json import load

import pytest
from catleg.query import (
    _article_from_legifrance_reply,
    _get_legifrance_credentials,
    get_backend,
)


def _json_from_test_file(fname):
    path_to_current_file = os.path.realpath(__file__)
    current_directory = os.path.dirname(path_to_current_file)
    file_path = os.path.join(current_directory, fname)
    with open(file_path, "r", encoding="utf-8") as f:
        json_contents = load(f)
    return json_contents


@pytest.mark.skipif(
    _get_legifrance_credentials(raise_if_missing=False)[0] is None,
    reason="this test requires legifrance credentials",
)
def test_query_article():
    back = get_backend("legifrance")
    article = asyncio.run(back.article("LEGIARTI000038814944"))
    assert "logement" in article.text


@pytest.mark.skipif(
    _get_legifrance_credentials(raise_if_missing=False)[0] is None,
    reason="this test requires legifrance credentials",
)
def test_query_articles():
    back = get_backend("legifrance")
    art1, art2 = asyncio.run(
        back.articles(["LEGIARTI000038814944", "LEGIARTI000038814948"])
    )
    assert "logement" in art1.text
    assert "pacte" in art2.text


def test_no_extraneous_nota():
    article = _json_from_test_file("LEGIARTI000038814944.json")
    res = _article_from_legifrance_reply(article)
    assert "NOTA" not in res.to_markdown()


def test_nota_format():
    article = _json_from_test_file("LEGIARTI000046790860.json")
    res = _article_from_legifrance_reply(article)
    assert "\n\nNOTA :\n\nConformément à l'article 89" in res.to_markdown()


def test_keep_newlines():
    article = _json_from_test_file("LEGIARTI000046790860.json")
    res = _article_from_legifrance_reply(article)
    assert "\n" in res.to_markdown()
