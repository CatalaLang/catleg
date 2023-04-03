from catala_devtools_fr.parse_catala_markdown import ArticleType, _parse_article_id

def test_parse_article_id():
    typ, id = _parse_article_id("legiarti000038814944")
    assert typ == ArticleType.LEGIARTI
    assert id == "legiarti000038814944"
