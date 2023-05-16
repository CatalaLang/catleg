from __future__ import annotations

import logging

from itertools import islice, repeat

from markdown_it import MarkdownIt
from markdown_it.common.utils import isSpace
from markdown_it.rules_block.state_block import StateBlock

"""
Arbitrary-level (but not configurable) heading extension for markdown-it-py.

This is needed because law texts go beyond 6 levels of headers, and we do want to
stay true to them without adding new syntax.

This file embeds code from the markdown-it-py project, licensed under the MIT license.

MIT License

Copyright (c) 2020 ExecutableBookProject

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

""" Atex heading (#, ##, ...) """

LOGGER = logging.getLogger(__name__)
HEADING_LIMIT = 20


def more_heading(state: StateBlock, startLine: int, endLine: int, silent: bool):
    LOGGER.debug("entering heading: %s, %s, %s, %s", state, startLine, endLine, silent)

    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    # if it's indented more than 3 spaces, it should be a code block
    if state.sCount[startLine] - state.blkIndent >= 4:
        return False

    ch: int | None = state.srcCharCode[pos]

    # /* # */
    if ch != 0x23 or pos >= maximum:
        return False

    # count heading level
    level = 1
    pos += 1
    try:
        ch = state.srcCharCode[pos]
    except IndexError:
        ch = None
    # /* # */
    while ch == 0x23 and pos < maximum and level <= HEADING_LIMIT:
        level += 1
        pos += 1
        try:
            ch = state.srcCharCode[pos]
        except IndexError:
            ch = None

    if level > HEADING_LIMIT or (pos < maximum and not isSpace(ch)):
        return False

    if silent:
        return True

    # Let's cut tails like '    ###  ' from the end of string

    maximum = state.skipSpacesBack(maximum, pos)
    tmp = state.skipCharsBack(maximum, 0x23, pos)  # #
    if tmp > pos and isSpace(state.srcCharCode[tmp - 1]):
        maximum = tmp

    state.line = startLine + 1

    token = state.push("heading_open", "h" + str(level), 1)
    token.markup = "".join(islice(repeat("#"), level))
    token.map = [startLine, state.line]

    token = state.push("inline", "", 0)
    token.content = state.src[pos:maximum].strip()
    token.map = [startLine, state.line]
    token.children = []

    token = state.push("heading_close", "h" + str(level), -1)
    token.markup = "".join(islice(repeat("#"), level))

    return True


def replace_heading_rule(md: MarkdownIt):
    md.block.ruler.at("heading", more_heading)
    return md
