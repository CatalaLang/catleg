from catleg.query import _article_from_legifrance_reply
from catleg.skeleton import _formatted_atricle

from .test_legifrance_queries import _json_from_test_file


# Regression test for https://github.com/CatalaLang/catleg/issues/71
def test_no_article_renumbering():
    article_json = _json_from_test_file("LEGIARTI000044983201.json")
    article = _article_from_legifrance_reply(article_json)
    formatted_article_md = _formatted_atricle(article)
    assert "1. Le bénéfice ou revenu imposable est constitué" in formatted_article_md
    assert "2. Le revenu global net annuel" in formatted_article_md
    assert (
        "3. Le bénéfice ou revenu net de chacune des catégories" in formatted_article_md
    )
