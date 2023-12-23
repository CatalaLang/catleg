from typing import Literal
from urllib.parse import urlparse

from catleg.config import settings
from catleg.law_text_fr import find_id_in_string


def set_basic_loglevel():
    """
    Utility for setting the log level as per config -- meant to be used
    within CLI tools only.

    To use, set CATLEG_LOG_LEVEL=INFO in the environment
    or log_level in the .catleg.toml configuration file
    """
    log_level = settings.get("log_level")
    if log_level is not None:
        import logging

        logging.basicConfig(level=log_level.upper())


# XXX ugly
def article_id_or_url(candidate: str) -> str | None:
    if (type_id := find_id_in_string(candidate)) is not None:
        return type_id[1]
    try:
        parse_res = parse_legifrance_url(candidate)
    except ValueError:
        return None
    if parse_res is not None and parse_res[0] == "article":
        return parse_res[1]
    return None


def parse_legifrance_url(
    url: str,
) -> tuple[Literal["article"], str] | tuple[Literal["section"], str, str] | None:
    """
    Parse a Legifrance URL, see if it matches an article or a section of a code,
    and return the corresponding type and identifier(s).
    """
    parsed_url = urlparse(url)
    if parsed_url.hostname != "www.legifrance.gouv.fr":
        return None

    path_elems = parsed_url.path.split("/")[1:]
    path_elems = [e for e in path_elems if e]  # remove empty path segments

    match path_elems:
        case ["codes", "article_lc", article_id]:
            return "article", article_id
        case ["codes", "section_lc", text_id, section_id]:
            return "section", text_id, section_id
        case _:
            return None
