# job-gen

A small FastAPI app that tailors a LaTeX resume (and optionally a cover letter) to a job description with Gemini, compiles them with [Tectonic](https://tectonic-typesetting.github.io/), and returns a zip of the PDFs.

## Setup

Requires Python 3.11+, a `tectonic` binary on `PATH`, and a Google AI Studio API key.

```bash
pip install -r requirements.txt
cp .env.example .env   # then set GEMINI_API_KEY
export GEMINI_API_KEY=...
uvicorn app:app --reload --port 8080
```

Open http://localhost:8080.

## Customizing

- `base_resume.tex` — your real resume. Replace the stub.
- `resume_prompt.txt` — system instructions for the resume pass.
- `cover_letter_prompt.txt` — system instructions for the cover letter pass.

These are read once at startup, so restart the server after editing.

## API

`POST /api/generate`

```json
{
  "company": "Acme",
  "role": "Backend Engineer",
  "job_description": "...",
  "include_cover_letter": true
}
```

Returns `{Company}_Application.zip` containing `resume.pdf` and, when requested, `cover_letter.pdf`. A Tectonic compile failure returns HTTP 500 with the stderr log in `detail`.

## Docker

```bash
docker build -t job-gen .
docker run -p 8080:8080 -e GEMINI_API_KEY=... job-gen
```
