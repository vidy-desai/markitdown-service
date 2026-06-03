import os
import shutil
import tempfile

import pdfplumber
import pytesseract
import openai as openai_lib
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Request, Form
from fastapi.responses import PlainTextResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from markitdown import MarkItDown

# ── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(title="MarkItDown Service")

SECRET_KEY  = os.environ.get("SECRET_KEY", "changeme-set-this-in-railway")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# ── Config from env ───────────────────────────────────────────────────────────
API_KEY    = os.environ.get("API_KEY", "")
LOGIN_USER = os.environ.get("LOGIN_USER", "")
LOGIN_PASS = os.environ.get("LOGIN_PASS", "")

OPENAI_KEY   = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

openai_client = openai_lib.OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

md = MarkItDown(
    enable_plugins=bool(OPENAI_KEY),
    llm_client=openai_client,
    llm_model=OPENAI_MODEL,
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def check_api_key(x_api_key: str = None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def is_logged_in(request: Request) -> bool:
    return request.session.get("authenticated") is True


def pdf_to_markdown_ocr(path: str) -> str:
    pages_md = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text and len(text.strip()) > 20:
                pages_md.append(f"## Page {i}\n\n{text.strip()}")
            else:
                img = page.to_image(resolution=300).original
                ocr_text = pytesseract.image_to_string(img)
                if ocr_text.strip():
                    pages_md.append(f"## Page {i}\n\n{ocr_text.strip()}")
    return "\n\n---\n\n".join(pages_md)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if is_logged_in(request):
        return RedirectResponse("/")
    with open("static/login.html") as f:
        return f.read()


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == LOGIN_USER and password == LOGIN_PASS:
        request.session["authenticated"] = True
        return RedirectResponse("/", status_code=303)
    with open("static/login.html") as f:
        content = f.read()
    return HTMLResponse(
        content.replace("<!--ERROR-->", '<p class="error">Invalid credentials</p>'),
        status_code=401,
    )


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if LOGIN_USER and not is_logged_in(request):
        return RedirectResponse("/login")
    with open("static/index.html") as f:
        return f.read()


@app.post("/convert", response_class=PlainTextResponse)
async def convert(
    request: Request,
    file: UploadFile = File(...),
    x_api_key: str = Header(None),
):
    if LOGIN_USER and not is_logged_in(request):
        check_api_key(x_api_key)

    suffix = os.path.splitext(file.filename)[1] or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        if suffix.lower() == ".pdf":
            result = pdf_to_markdown_ocr(tmp_path)
        else:
            result = md.convert(tmp_path).text_content
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        os.unlink(tmp_path)


app.mount("/static", StaticFiles(directory="static"), name="static")
