"""End-to-end check: real Gemini call, real Tectonic compile, real zip.

Requires GEMINI_API_KEY and ACCESS_TOKEN in .env, and tectonic on PATH.
This spends API quota. Run `python test_compile.py` first.

    python test_pipeline.py
"""

import os
import shutil
import sys
import zipfile
from pathlib import Path

import app

JOB_DESCRIPTION = """\
Software Engineer, Platform

We are looking for a software engineer to build and operate backend services.

Requirements:
- Proficiency in Python and experience with a web framework such as FastAPI
- Experience designing REST APIs and working with PostgreSQL
- Comfortable with Docker and CI/CD pipelines
- Track record of debugging production issues and improving reliability
"""


def main() -> int:
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        print("FAIL: GEMINI_API_KEY is not set (check .env)", file=sys.stderr)
        return 1
    token = os.environ.get("ACCESS_TOKEN")
    if not token:
        print("FAIL: ACCESS_TOKEN is not set (check .env)", file=sys.stderr)
        return 1

    payload = app.GenerateRequest(
        company="Acme Corp",
        role="Software Engineer, Platform",
        job_description=JOB_DESCRIPTION,
        include_cover_letter=True,
    )

    print("Calling Gemini and compiling with Tectonic. This takes a minute.")
    response = app.generate(payload, x_access_token=token, token=None)

    zip_path = Path(response.path)
    workdir = zip_path.parent
    try:
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            sizes = {name: archive.getinfo(name).file_size for name in names}

        if sorted(names) != ["cover_letter.pdf", "resume.pdf"]:
            print(f"FAIL: unexpected archive contents: {names}", file=sys.stderr)
            return 1
        empty = [name for name, size in sizes.items() if size == 0]
        if empty:
            print(f"FAIL: empty PDFs in archive: {empty}", file=sys.stderr)
            return 1

        print(f"OK: {zip_path.name}")
        for name, size in sorted(sizes.items()):
            print(f"  {name}: {size} bytes")
        return 0
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
