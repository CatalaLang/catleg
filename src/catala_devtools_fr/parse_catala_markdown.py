from types import SimpleNamespace
from typing import List, Optional, TextIO, Tuple

import panflute as pf  # type:ignore

from catala_devtools_fr.article import Article, parse_article_id


def parse_catala_file(f: TextIO) -> List[Article]:
    """
    Given a catala file, return a list of articles
    """
    return _parse_catala_doc(pf.convert_text(f.read(), standalone=True))


def _parse_catala_doc(doc) -> List[Article]:
    articles: List[Article] = []
    pf.run_filters([_article_filter_action], doc=doc, articles=articles)
    return articles


def _article_filter_action(elem, doc, articles):
    match elem:
        case pf.Header() as hd if hd.identifier.startswith("article"):
            article_type, article_id = parse_article_id(hd.identifier)
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

            articles.append(
                SimpleNamespace(type=article_type, id=article_id, text="".join(text))
            )


if __name__ == "__main__":
    import sys

    with open(sys.argv[1], "r") as f:
        doc = parse_catala_file(f)
        print(doc)
