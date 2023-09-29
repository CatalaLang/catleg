from itertools import dropwhile

import mdformat

from catleg.query import _article_from_legifrance_reply, get_backend


async def markdown_skeleton(textid: str, sectionid: str) -> str:
    """
    Return a skeleton (formatted law text section)
    """
    if sectionid[:8].upper() != "LEGISCTA":
        raise ValueError("Expected section identifier (should start with 'SCTA')")

    back = get_backend("legifrance")
    toc = await back.code_toc(textid)

    nodes = dropwhile(
        lambda node_level: node_level[0]["cid"] != sectionid, _preorder(toc)
    )

    # some existence checking is needed here
    root, root_level = next(nodes)
    parts = []

    for node, level in _preorder(root, root_level):
        if node["id"][:8] != "LEGISCTA":
            # If it is not a section, then it is an article
            parts.append(f"{'#' * (level + 1)} Article {node['num']} | {node['id']}")
            article = await back.article(node["id"])
            parts.append(_formatted_atricle(article))
        else:
            parts.append(f"{'#' * level} {node['title']}")

    return "\n\n".join(parts)


async def article_skeleton(articleid: str) -> str:
    """
    Return an article skeleton.
    """
    back = get_backend("legifrance")
    # This uses the Legifrance API directly, not the backend abstraction
    raw_article_json = await back.query_article_legi(articleid)
    article_json = raw_article_json["article"]
    article = _article_from_legifrance_reply(raw_article_json)
    if article is None:
        raise RuntimeError(
            "Could not extract article from json reply %s", raw_article_json
        )
    parts = []
    # level: code (1) + length of section hierarchy + article (1)
    level = 1 + len(article_json["context"]["titresTM"]) + 1
    parts.append(f"{'#' * level} Article {article_json['num']} | {article.id}")
    parts.append(_formatted_atricle(article))
    return "\n\n".join(parts)


def _preorder(node, level=1):
    """Preorder traversal of articles and sections"""
    yield node, level
    for article in node["articles"]:
        yield article, level
    for section in node["sections"]:
        yield from _preorder(section, level + 1)


def _formatted_atricle(article):
    return mdformat.text(article.to_markdown(), options={"wrap": 80, "number": True})
