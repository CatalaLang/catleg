from enum import Enum
from typing import Tuple, TextIO

import panflute as pf # type:ignore

ArticleType = Enum('ArticleType', ['LEGIARTI', 'CETATEXT', 'JORFARTI'])

def parse_catala_file(f: TextIO):
    """
    Given a catala file, return a list of articles
    """
    return _parse_catala_doc(pf.convert_text(f.read(), standalone=True))

def _parse_catala_doc(doc):
    doc._articles = []
    pf.run_filters([_article_filter_action], doc=doc)
    articles = doc._articles
    del doc._articles
    return articles

def _article_filter_action(elem, doc):
    match elem:
        case pf.Header() as hd if hd.identifier.startswith("article"):
            article_type, article_id = _parse_article_id(hd.identifier)
            # collect all elements up to next header or EOF,
            # skip code blocks and flatten the rest to get the
            # text representation of the legislative article
            text = []
            while elem.next is not None:
                if isinstance(elem.next, pf.Header):
                    break
                if not isinstance(elem.next, pf.CodeBlock):
                    text.append(pf.stringify(elem.next))
                elem = elem.next

            doc._articles.append({"type": article_type, "id": article_id, "text": "".join(text)})

def _parse_article_id(article_id: str) -> Tuple[ArticleType, str]:
    """
    Parse a string that looks like 'article-l822-2-legiarti000038814944'
    and return (ArticleType.LEGIARTI, 'legiarti000038814944')
    """
    article_id = article_id.split('-')[-1]
    typ = ArticleType[article_id[:8].upper()]
    return typ, article_id

if __name__ == "__main__":
    import sys
    with open(sys.argv[1], 'r') as f:
        doc = parse_catala_file(f)
        print(doc)