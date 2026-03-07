# brief-prompter

Python project that periodically transforms a creative brief into a Luma-ready prompt, generates a vertical short, and uploads it to TikTok.

## Features

- Re-read latest brief before every run from local file source.
- Adapter-style interfaces for source, prompt transformer, video generator, and uploader.
- Persistent job history in SQLite.
- APScheduler-based schedule (00:00, 06:00, 12:00, 18:00 Asia/Seoul).
- FastAPI endpoints + CLI commands.
- Dry-run mode, run-once mode, and retry flow.

## Quickstart

```bash
cp .env.example .env
# edit current_brief.txt as needed
python -m pip install -r requirements.txt
python -m app.cli run-once
```

Start API server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## CLI

- `python -m app.cli run-once`
- `python -m app.cli run-once --dry-run`
- `python -m app.cli refresh-brief`
- `python -m app.cli list-jobs`
- `python -m app.cli retry-job <job_id>`
- `python -m app.cli dry-run`

## API

- `GET /health`
- `GET /jobs`
- `GET /jobs/{job_id}`
- `POST /jobs/run-once`
- `POST /brief/refresh`

Retry API is exposed as:

- `POST /jobs/{job_id}/retry`

You can also run retry via CLI:

- `python -m app.cli retry-job <job_id>`

## Notes

- Replace adapter implementations to support new providers.
- Set `APP_TIMEZONE`, `BRIEF_FILE_PATH`, `DATABASE_URL`, API keys via `.env`.
