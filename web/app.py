from pathlib import Path

from catleg.law_text_fr import ArticleType, find_id_in_string
from catleg.skeleton import article_skeleton, markdown_skeleton

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="catleg markdown viewer", version="0.1.0")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _classify(query: str):
    found = find_id_in_string(query, strict=False)
    if not found:
        return None
    typ, id_ = found
    if typ in (ArticleType.LEGIARTI, ArticleType.JORFARTI):
        return ("article", id_)
    if typ == ArticleType.CETATEXT:
        return ("text", id_)
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
            kind, id_ = cls
            try:
                if kind == "article":
                    md = await article_skeleton(id_)
                else:
                    # For texts, fetch top-level skeleton
                    md = await markdown_skeleton(id_, sectionid="")
            except Exception as e:
                error = str(e)
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "query": query, "md": md, "error": error},
    )


@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"
