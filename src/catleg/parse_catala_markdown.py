from pathlib import Path
from typing import cast, TextIO

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from mdformat.renderer import MDRenderer
from more_itertools import sliding_window

from catleg.law_text_fr import CatalaFileArticle, find_id_in_string
from catleg.markdown_it.heading_extension import replace_heading_rule


def parse_catala_file(
    f: TextIO, file_path: Path | None = None
) -> list[CatalaFileArticle]:
    """
    Given a catala file, return a list of articles
    """
    md = _make_markdown_parser()
    tokens = md.parse(f.read())
    tree = SyntaxTreeNode(tokens)
    articles = _parse_catala_doc(tree, file_path=file_path)
    return articles


def _make_markdown_parser() -> MarkdownIt:
    """
    Return a markdown parser suitable for Catala files
    (this currently is a CommonMark parser with an extension that
    increases the number of possible heading levels)
    """
    return replace_heading_rule(MarkdownIt("commonmark"))


def _parse_catala_doc(
    tree: SyntaxTreeNode, file_path: Path | None = None
) -> list[CatalaFileArticle]:
    articles: list[CatalaFileArticle] = []
    windowed_tree = sliding_window(tree.walk(), 3)
    renderer = MDRenderer()
    for window in windowed_tree:
        match [elem.type for elem in window]:
            case ["heading", "inline", "text"]:
                if type_id := find_id_in_string(window[-1].content):
                    typ, id = type_id
                    text = []
                    curr_elem = window[0]
                    is_archive = "[archive]" in window[-1].content

                    # start line of the first text block
                    inline_map = window[1].map
                    assert inline_map is not None
                    start_line: int = cast(tuple[int, int], inline_map)[0]

                    while curr_elem.next_sibling is not None:
                        if curr_elem.next_sibling.type == "heading":
                            break
                        # skip code blocks, retain all other elements
                        if curr_elem.next_sibling.type != "fence":
                            text.append(
                                renderer.render(
                                    curr_elem.next_sibling.to_tokens(),
                                    options={},
                                    env={},
                                )
                            )
                        curr_elem = curr_elem.next_sibling

                    articles.append(
                        CatalaFileArticle(
                            type=typ,
                            id=id,
                            text=" ".join(text),
                            start_line=start_line,
                            file_path=file_path,
                            is_archive=is_archive,
                        )
                    )

    return articles


if __name__ == "__main__":
    import sys

    with open(sys.argv[1]) as f:
        doc = parse_catala_file(f)
        print(doc)
