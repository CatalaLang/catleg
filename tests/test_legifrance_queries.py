import asyncio

import pytest
from catala_devtools_fr.query import _get_legifrance_credentials, get_backend


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
