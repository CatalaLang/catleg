from catala_devtools_fr.article import ArticleType, find_id_in_string, parse_article_id


def test_parse_article_id():
    typ, id = parse_article_id("legiarti000038814944")
    assert typ == ArticleType.LEGIARTI
    assert id == "legiarti000038814944"


def test_find_id_in_string():
    assert find_id_in_string("####### Article R821-2 | LEGIARTI000038879021") == (
        ArticleType.LEGIARTI,
        "LEGIARTI000038879021",
    )
    assert find_id_in_string("###### Article L841-1 | LEGIARTI000038814864") == (
        ArticleType.LEGIARTI,
        "LEGIARTI000038814864",
    )
    assert find_id_in_string("This definitely does not match") is None
