from pathlib import Path
from typing import cast, List, Optional, TextIO, Tuple

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from mdformat.renderer import MDRenderer
from more_itertools import sliding_window

from catala_devtools_fr.law_text_fr import CatalaFileArticle, find_id_in_string
from catala_devtools_fr.markdown_it.heading_extension import replace_heading_rule


def parse_catala_file(
    f: TextIO, file_path: Optional[Path] = None
) -> List[CatalaFileArticle]:
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
    tree: SyntaxTreeNode, file_path: Optional[Path] = None
) -> List[CatalaFileArticle]:
    articles: List[CatalaFileArticle] = []
    windowed_tree = sliding_window(tree.walk(), 3)
    renderer = MDRenderer()
    for window in windowed_tree:
        match [elem.type for elem in window]:
            case ["heading", "inline", "text"]:
                if type_id := find_id_in_string(window[-1].content):
                    typ, id = type_id
                    text = []
                    curr_elem = window[0]

                    # start line of the first text block
                    inline_map = window[1].map
                    assert inline_map is not None
                    start_line: int = cast(Tuple[int, int], inline_map)[0]

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
                        )
                    )

    return articles


if __name__ == "__main__":
    import sys

    with open(sys.argv[1], "r") as f:
        doc = parse_catala_file(f)
        print(doc)
