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

    # Not a supported URL: look for supported bare identifiers
    found = find_id_in_string(q, strict=False)
    if found:
        typ, id_ = found
        if typ in (ArticleType.LEGIARTI, ArticleType.JORFARTI):
            return {"source": "id", "kind": "article", "id": id_}
        if typ == ArticleType.CETATEXT:
            return {"source": "id", "kind": "text", "id": id_}

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
                    md = await article_skeleton(id_)
                elif kind == "jorftext" and id_:
                    md = await jorf_markdown_skeleton(id_)
                elif kind == "text" and id_:
                    # For texts, fetch top-level skeleton
                    md = await markdown_skeleton(id_, sectionid="")
                else:
                    error = "Aucun identifiant pris en charge n'a été trouvé"
                    "dans votre saisie."
            except Exception as e:
                error = str(e)
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "query": query, "md": md, "error": error},
    )


@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"
