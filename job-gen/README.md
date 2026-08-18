# job-gen

A small FastAPI app that tailors a LaTeX resume (and optionally a cover letter) to a job description with Gemini, compiles them with [Tectonic](https://tectonic-typesetting.github.io/), and returns a zip of the PDFs.

## Setup

Requires Python 3.11+, a `tectonic` binary on `PATH`, and a Google AI Studio API key.

```bash
pip install -r requirements.txt
cp .env.example .env    # then fill in GEMINI_API_KEY and ACCESS_TOKEN
python test_compile.py  # verifies tectonic and warms its package cache
uvicorn app:app --reload --port 8080
```

Open http://localhost:8080, enter your access key once (it is kept in `localStorage`), and generate.

## Verifying

- `python test_compile.py` compiles a document using `geometry`, `hyperref`, `enumitem`, `titlesec`, and `fontawesome5`. The first run downloads the Tectonic bundle and is slow.
- `python test_pipeline.py` runs the full path: real Gemini call, real compile, real zip. It spends API quota.

## Customizing

- `base_resume.tex` — your real resume. Replace the stub.
- `resume_prompt.txt` — system instructions for the resume pass.
- `cover_letter_prompt.txt` — system instructions for the cover letter pass.

These are read once at startup, so restart the server after editing.

## API

`POST /api/generate`, authenticated with the `X-Access-Token` header or a `?token=` query param. Returns 401 if the key does not match `ACCESS_TOKEN`.

```bash
curl -X POST localhost:8080/api/generate \
  -H "X-Access-Token: $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"company":"Acme","role":"Backend Engineer","job_description":"...","include_cover_letter":true}' \
  -OJ
```

Returns `{Company}_Application.zip` containing `resume.pdf` and, when requested, `cover_letter.pdf`. A Tectonic failure returns 500 with the full compile log in `detail`; a compile exceeding 180s also returns 500.

## Deploying

The image bakes the Tectonic package cache in at build time, so cold starts are fast.

```bash
docker build -t job-gen .
docker run -p 8080:8080 -e GEMINI_API_KEY=... -e ACCESS_TOKEN=... job-gen
```

On Fly.io, using the included `fly.toml`:

```bash
fly launch --copy-config --no-deploy
fly secrets set GEMINI_API_KEY=... ACCESS_TOKEN=...
fly deploy
```

Never commit `.env`. It is covered by `.gitignore` and `.dockerignore`.
