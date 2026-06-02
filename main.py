import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from markitdown import MarkItDown

app = FastAPI(title="MarkItDown Service")

API_KEY = os.environ.get("API_KEY", "")
md = MarkItDown()


def check_api_key(x_api_key: str = None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html") as f:
        return f.read()


@app.post("/convert", response_class=PlainTextResponse)
async def convert(
    file: UploadFile = File(...),
    x_api_key: str = Header(None),
):
    check_api_key(x_api_key)

    suffix = os.path.splitext(file.filename)[1] or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = md.convert(tmp_path)
        return result.text_content
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        os.unlink(tmp_path)


@app.get("/health")
def health():
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory="static"), name="static")
