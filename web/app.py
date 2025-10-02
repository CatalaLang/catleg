import asyncio
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from catleg.law_text_fr import ArticleType, find_id_in_string
from catleg.skeleton import article_skeleton, jorf_markdown_skeleton, markdown_skeleton

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="catleg markdown viewer", version="0.1.0")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

SKELETON_TIMEOUT_SEC = float(os.getenv("CATLEG_SKELETON_TIMEOUT_SECONDS", "5"))


def _classify(query: str):
    """
    Classify user input as either a Legifrance URL or a bare identifier and
    return a structured description.

    Returns a dict like:
      - {"source": "url", "kind": "article" | "jorftext" | "text" | "unknown",
      "url": str, "id": str | None, "uri": {...}?}
      - {"source": "id",  "kind": "article" | "jorftext" | "text", "id": str}
    or None if nothing supported is found.
    """
    q = query.strip()

    # Try URL parsing first
    parsed = urlparse(q)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        host = parsed.netloc.split(":", 1)[0].lower()
        if not host.endswith("legifrance.gouv.fr"):
            return None
        # Specific support for /jorf/id/JORFTEXTXXXXXXXXXXXX
        segments = [seg for seg in parsed.path.split("/") if seg]
        if (
            len(segments) >= 3
            and segments[0].lower() == "jorf"
            and segments[1].lower() == "id"
        ):
            id_candidate = segments[2]
            if re.fullmatch(r"JORFTEXT\d{12}", id_candidate, flags=re.I):
                canon = id_candidate.upper()
                return {
                    "source": "url",
                    "kind": "jorftext",
                    "url": q,
                    "id": canon,
                    "uri": {"root": "jorf", "action": "id"},
                }
        # Support for /codes/section_lc/LEGITEXT.../LEGISCTA...
        if (
            len(segments) >= 4
            and segments[0].lower() == "codes"
            and segments[1].lower() == "section_lc"
            and re.fullmatch(r"LEGITEXT\d{12}", segments[2], flags=re.I)
            and re.fullmatch(r"LEGISCTA\d{12}", segments[3], flags=re.I)
        ):
            text_id = segments[2].upper()
            section_id = segments[3].upper()
            return {
                "source": "url",
                "kind": "code_section",
                "url": q,
                "text_id": text_id,
                "section_id": section_id,
                "uri": {"root": "codes", "action": "section_lc"},
            }

    # Not a supported URL: look for supported bare identifiers
    found = find_id_in_string(q, strict=False)
    if found:
        typ, id_ = found
        if typ in (ArticleType.LEGIARTI, ArticleType.JORFARTI, ArticleType.CETATEXT):
            return {"source": "id", "kind": "article", "id": id_}

    # Also support JORFTEXT ids given directly
    m = re.search(r"\bJORFTEXT\d{12}\b", q, flags=re.I)
    if m:
        return {"source": "id", "kind": "jorftext", "id": m.group(0).upper()}

    return None


@app.get("/")
async def home(request: Request, query: str = ""):
    md = None
    error = None
    if query:
        cls = _classify(query)
        if not cls:
            error = "Aucun identifiant pris en charge n'a été trouvé dans votre saisie."
        else:
            kind = cls.get("kind")
            id_ = cls.get("id")
            try:
                if kind == "article" and id_:
                    md = await asyncio.wait_for(
                        article_skeleton(id_), timeout=SKELETON_TIMEOUT_SEC
                    )
                elif kind == "jorftext" and id_:
                    md = await asyncio.wait_for(
                        jorf_markdown_skeleton(id_), timeout=SKELETON_TIMEOUT_SEC
                    )
                elif kind == "code_section":
                    text_id = cls.get("text_id")
                    section_id = cls.get("section_id")
                    if text_id and section_id:
                        md = await asyncio.wait_for(
                            markdown_skeleton(text_id, section_id),
                            timeout=SKELETON_TIMEOUT_SEC,
                        )
                    else:
                        error = "URL de section de code invalide."
                else:
                    error = "Aucun identifiant pris en charge n'a été"
                    " trouvé dans votre saisie."
            except asyncio.TimeoutError:
                error = "La génération du texte a dépassé le délai autorisé."
            except Exception as e:
                error = str(e)
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "query": query, "md": md, "error": error},
    )


@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"
