from itertools import dropwhile

import mdformat

from catleg.query import _article_from_legifrance_reply, get_backend, LegifranceArticle


# TODO rename because this function is specific to code sections?
# (eventually we also want to handle JORF content etc.)
# Either that, or generalize
# Note: it seems that for codes, articles are leaves and the preorder
# traversal works! This seems *not* to be the case for JORF content
async def markdown_skeleton(textid: str, sectionid: str) -> str:
    """
    Return a skeleton (markdown-formatted law text section)
    """
    if sectionid[:8].upper() != "LEGISCTA":
        raise ValueError("Expected section identifier (should start with 'LEGISCTA')")

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
            parts.append(_formatted_article(article))
        else:
            parts.append(f"{'#' * level} {node['title']}")

    return "\n\n".join(parts)


async def article_skeleton(articleid: str, breadcrumbs: bool = True) -> str:
    """
    Return an article skeleton (markdown-formatted law article).

    Parameters
    ----------
    articleid: str
       Legifrance article identifier
    breadcrumbs: bool
       if True, emits breadcrumbs (table of contents headers) before
       outputting the article itself

    Returns
    -------
    str
       Markdown-formatted article
    """
    back = get_backend("legifrance")
    # This uses the Legifrance API directly, not the backend abstraction
    raw_article_json = await back.query_article_legi(articleid)
    return _article_skeleton(raw_article_json=raw_article_json, breadcrumbs=breadcrumbs)


async def jorf_markdown_skeleton(jorftextid: str) -> str:
    """
    Return a Markdown skeleton for a text published in the JORF
    (Journal Officiel) -- identifier starting with JORFTEXT.

    Note: this does not render a full issue of the JORF,
    which contains many such texts.
    """
    back = get_backend("legifrance")
    jorftext_json = await back.jorf(jorftextid)

    parts: list[str] = [f'# {jorftext_json["title"]}']

    def walk(node: dict, level: int):
        # Merge sections and articles preserving intended order using intOrdre
        merged: list[tuple[int, str, dict]] = []
        for section in node.get("sections", []):
            merged.append((section.get("intOrdre", 0), "section", section))
        for article in node.get("articles", []):
            merged.append((article.get("intOrdre", 0), "article", article))

        for _, kind, child in sorted(merged, key=lambda t: t[0]):
            if kind == "section":
                title = child.get("title") or ""
                parts.append(f'{"#" * level} {title}'.rstrip())
                walk(child, level + 1)
            else:
                num = child.get("num")
                header = (
                    f'{"#" * level} Article {num} | {child["id"]}'
                    if num
                    else f'{"#" * level} {child["id"]}'
                )
                parts.append(header)
                parts.append(_formatted_jorf_article_from_json(child))

    # Start walking children under the root title
    walk(jorftext_json, level=2)

    return "\n\n".join(parts)


# separate network calls and processing to ease unit testing
def _article_skeleton(raw_article_json, breadcrumbs: bool = True):
    article_json = raw_article_json["article"]
    article = _article_from_legifrance_reply(raw_article_json)
    if article is None:
        raise RuntimeError(
            "Could not extract article from json reply %s", raw_article_json
        )

    parts = []
    if breadcrumbs:
        texts = article_json["context"]["titreTxt"]
        texts_in_force = [item for item in texts if item["etat"] == "VIGUEUR"]
        # Pick the title of the first text currently in force,
        # or the last item from the candidates list
        crumbs = [texts_in_force[0] if texts_in_force else texts[-1]] + article_json[
            "context"
        ]["titresTM"]
        for i, toc_entry in enumerate(crumbs, start=1):
            parts.append(f"{'#' * i} {toc_entry['titre']}")

    # level: code (1) + length of section hierarchy + article (1)
    level = 1 + len(article_json["context"]["titresTM"]) + 1
    parts.append(f"{'#' * level} Article {article_json['num']} | {article.id}")
    parts.append(_formatted_article(article))
    return "\n\n".join(parts)


def _preorder(node, level=1):
    """Preorder traversal of articles and sections"""
    yield node, level
    for article in node["articles"]:
        yield article, level
    for section in node["sections"]:
        yield from _preorder(section, level + 1)


def _formatted_article(article):
    return mdformat.text(article.to_markdown(), options={"wrap": 80, "number": True})


def _formatted_jorf_article_from_json(article_json):
    """
    Construct a LegifranceArticle from a JORF article JSON node and
    reuse the existing HTML->Markdown logic implemented in
    LegifranceArticle.to_markdown.
    """
    # JORF article nodes provide HTML content in "content" and "nota" fields.
    # Build a minimal LegifranceArticle with these.
    art_id = article_json["id"]
    text_html = article_json.get("content") or ""
    nota_html = article_json.get("nota") or ""
    end_date = article_json.get("dateFin")
    # latest_version_id may be absent on JORF replies; fall back to id.
    latest_version_id = article_json.get("latest_version_id") or art_id

    legi_article = LegifranceArticle(
        id=art_id,
        text="",
        text_html=text_html,
        nota="",
        nota_html=nota_html,
        end_date=end_date,
        latest_version_id=latest_version_id,
    )
    return _formatted_article(legi_article)
