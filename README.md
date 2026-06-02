# MarkItDown Service

A self-hosted HTTP API + web UI for converting files to Markdown using [microsoft/markitdown](https://github.com/microsoft/markitdown).

## What's included

- `POST /convert` — upload a file, receive Markdown
- `GET /` — web UI for team use (drag & drop, copy, download)
- `GET /health` — health check for Railway

## Deploy to Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
3. Select this repo — Railway picks up the `Dockerfile` automatically
4. Under **Settings → Networking**, click **Generate Domain**
5. Optionally set `API_KEY` in **Variables** to restrict access

## Environment Variables

| Variable  | Default | Description                            |
|-----------|---------|----------------------------------------|
| `API_KEY` | _(none)_ | If set, requests must include `X-Api-Key: <key>` header |
| `PORT`    | `8000`  | Set automatically by Railway           |

## API Usage

```bash
# No API key
curl -X POST https://your-app.up.railway.app/convert \
  -F "file=@report.pdf"

# With API key
curl -X POST https://your-app.up.railway.app/convert \
  -H "X-Api-Key: your-secret-key" \
  -F "file=@report.pdf" \
  -o output.md
```

## Supported Formats

PDF, DOCX, PPTX, XLSX, XLS, HTML, CSV, JSON, XML, ZIP, EPUB, JPG, PNG, MP3, WAV, YouTube URLs
