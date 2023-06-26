from itertools import dropwhile

import mdformat

from catleg.query import get_backend


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
            formatted = mdformat.text(article.to_markdown(), options={"wrap": 80})
            parts.append(formatted)
        else:
            parts.append(f"{'#' * level} {node['title']}")

    return "\n\n".join(parts)


def _preorder(node, level=1):
    """Preorder traversal of articles and sections"""
    yield node, level
    for article in node["articles"]:
        yield article, level
    for section in node["sections"]:
        yield from _preorder(section, level + 1)
