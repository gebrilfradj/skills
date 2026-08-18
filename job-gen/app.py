import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from google import genai
from google.genai import types
from pydantic import BaseModel
from starlette.background import BackgroundTask

BASE_DIR = Path(__file__).parent
MODEL = "gemini-2.5-flash"

BASE_RESUME = (BASE_DIR / "base_resume.tex").read_text(encoding="utf-8")
RESUME_PROMPT = (BASE_DIR / "resume_prompt.txt").read_text(encoding="utf-8")
COVER_LETTER_PROMPT = (BASE_DIR / "cover_letter_prompt.txt").read_text(encoding="utf-8")
INDEX_HTML = (BASE_DIR / "index.html").read_text(encoding="utf-8")

app = FastAPI(title="job-gen")


class GenerateRequest(BaseModel):
    company: str
    role: str
    job_description: str
    include_cover_letter: bool = False


def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set")
    return genai.Client(api_key=api_key)


def extract_latex(text: str) -> str:
    """Return the LaTeX body, stripping ```latex fences when present."""
    match = re.search(r"```(?:latex|tex)?\s*(.*?)```", text, re.DOTALL)
    body = match.group(1) if match else text
    return body.strip()


def generate_latex(client: genai.Client, system_prompt: str, user_prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}") from exc

    latex = extract_latex(response.text or "")
    if not latex:
        raise HTTPException(status_code=502, detail="Gemini returned no LaTeX content")
    return latex


def compile_pdf(latex: str, workdir: Path, name: str) -> Path:
    tex_path = workdir / f"{name}.tex"
    tex_path.write_text(latex, encoding="utf-8")

    result = subprocess.run(
        ["tectonic", "--outdir", str(workdir), str(tex_path)],
        capture_output=True,
        text=True,
        cwd=workdir,
    )
    pdf_path = workdir / f"{name}.pdf"
    if result.returncode != 0 or not pdf_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Tectonic failed to compile {name}.tex:\n{result.stderr.strip()}",
        )
    return pdf_path


def safe_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    return cleaned or fallback


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(INDEX_HTML)


@app.post("/api/generate")
def generate(payload: GenerateRequest) -> FileResponse:
    client = get_client()
    workdir = Path(tempfile.mkdtemp(prefix="job-gen-"))
    try:
        resume_latex = generate_latex(
            client,
            RESUME_PROMPT,
            f"Target role: {payload.role}\n"
            f"Company: {payload.company}\n\n"
            f"Job description:\n{payload.job_description}\n\n"
            f"Base resume LaTeX:\n{BASE_RESUME}",
        )
        pdfs = [compile_pdf(resume_latex, workdir, "resume")]

        if payload.include_cover_letter:
            cover_latex = generate_latex(
                client,
                COVER_LETTER_PROMPT,
                f"Target role: {payload.role}\n"
                f"Company: {payload.company}\n\n"
                f"Job description:\n{payload.job_description}\n\n"
                f"Tailored resume LaTeX:\n{resume_latex}",
            )
            pdfs.append(compile_pdf(cover_latex, workdir, "cover_letter"))

        zip_path = workdir / f"{safe_name(payload.company, 'Company')}_Application.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for pdf in pdfs:
                archive.write(pdf, pdf.name)
    except Exception:
        shutil.rmtree(workdir, ignore_errors=True)
        raise

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=zip_path.name,
        background=BackgroundTask(shutil.rmtree, workdir, ignore_errors=True),
    )
