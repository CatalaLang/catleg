# Minimal Legifrance Markdown viewer

A minimal FastAPI app that takes a Legifrance article/text ID or URL and returns the corresponding Markdown using the catleg library.

What it does
- Input: LEGIARTI... / JORFARTI... (articles), CETATEXT... (texts), or a Legifrance URL.
- Output: raw Markdown displayed on the page and available from a simple API.

Prerequisites
- Python 3.10+
- Legifrance API credentials available to catleg:
  - Either create a `.catleg_secrets.toml` at the repository root:
    ```
    lf_client_id = "your_client_id"
    lf_client_secret = "your_client_secret"
    ```
  - Or set environment variables:
    - `CATLEG_LF_CLIENT_ID`
    - `CATLEG_LF_CLIENT_SECRET`

Local development
1) Install dependencies (from the repo root):
   - Install the library + web extras (editable):
     - `pip install -e .[web]`
   - Or install dev + web extras:
     - `pip install -e .[dev,web]`

2) Start the server (from the repo root):
   - `uvicorn web.app:app --reload`

3) Open:
   - http://127.0.0.1:8000

Developer notes
Test the Dockerfile locally (build context is the repository root):

- Build the image:
  - `docker build -f web/Dockerfile -t catleg-web:local .`
- Run the container and expose it on http://127.0.0.1:8080:
  - `docker run --rm -p 8080:8080 catleg-web:local`
