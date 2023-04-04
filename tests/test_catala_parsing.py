from catala_devtools_fr.article import ArticleType, parse_article_id


def test_parse_article_id():
    typ, id = parse_article_id("legiarti000038814944")
    assert typ == ArticleType.LEGIARTI
    assert id == "legiarti000038814944"
