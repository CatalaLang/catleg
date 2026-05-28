import asyncio
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

from catleg.find_changes import find_changes


_CATALA_WITH_ARCHIVE = """
###### Article L822-2 | LEGIARTI000038814944

Article text here.

###### Article L821-2 [archive] | LEGIARTI000038814974

Old archived text.
"""


def _make_mock_backend(articles):
    back = MagicMock()
    back.articles = AsyncMock(return_value=articles)
    return back


def _make_article(id, text="some text"):
    art = MagicMock()
    art.id = id
    art.text_and_nota = MagicMock(return_value=text)
    art.text = text
    return art


def test_archive_articles_are_skipped():
    """find_changes must not diff archived articles."""
    live_art = _make_article("LEGIARTI000038814944")
    archive_art = _make_article("LEGIARTI000038814974")
    mock_back = _make_mock_backend([live_art, archive_art])

    wdiff_calls = []

    def fake_wdiff(a, b, *, return_exit_code, line_offset):
        wdiff_calls.append((a, b))
        return b"", 0

    with patch("catleg.find_changes.get_backend", return_value=mock_back):
        with patch("catleg.find_changes.wdiff", side_effect=fake_wdiff):
            asyncio.run(find_changes(StringIO(_CATALA_WITH_ARCHIVE)))

    assert (
        len(wdiff_calls) == 1
    ), f"Expected wdiff called once (non-archived article only), got {len(wdiff_calls)}"
