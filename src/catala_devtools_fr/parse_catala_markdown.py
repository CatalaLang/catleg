from types import SimpleNamespace
from typing import List, TextIO

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from mdformat.renderer import MDRenderer
from more_itertools import sliding_window

from catala_devtools_fr.article import Article, find_id_in_string


def parse_catala_file(f: TextIO) -> List[Article]:
    """
    Given a catala file, return a list of articles
    """
    md = MarkdownIt("commonmark")
    tokens = md.parse(f.read())
    tree = SyntaxTreeNode(tokens)
    articles = _parse_catala_doc(tree)
    return articles


def _parse_catala_doc(tree: SyntaxTreeNode) -> List[Article]:
    articles: List[Article] = []
    windowed_tree = sliding_window(tree.walk(), 3)
    renderer = MDRenderer()
    for window in windowed_tree:
        match [elem.type for elem in window]:
            case ["heading", "inline", "text"]:
                if type_id := find_id_in_string(window[-1].content):
                    typ, id = type_id
                    text = []
                    curr_elem = window[0]
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
                        SimpleNamespace(type=typ, id=id, text=" ".join(text))
                    )

    return articles


if __name__ == "__main__":
    import sys

    with open(sys.argv[1], "r") as f:
        doc = parse_catala_file(f)
        print(doc)
