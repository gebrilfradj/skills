"""Verify the local Tectonic install and warm its package cache.

Run this once before first use: it forces Tectonic to download the CTAN
packages a resume typically needs, so the first real request is not slow.

    python test_compile.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

PACKAGES = ["geometry", "hyperref", "enumitem", "titlesec", "fontawesome5"]

DOCUMENT = """\\documentclass[letterpaper,11pt]{article}
%s
\\begin{document}
Tectonic pre-warm. \\faGithub{} \\href{https://example.com}{link}
\\begin{itemize}\\item item\\end{itemize}
\\end{document}
""" % "\n".join(f"\\usepackage{{{name}}}" for name in PACKAGES)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="tectonic-prewarm-") as tmp:
        workdir = Path(tmp)
        tex_path = workdir / "prewarm.tex"
        tex_path.write_text(DOCUMENT, encoding="utf-8")

        print(f"Compiling with: {', '.join(PACKAGES)}")
        print("First run downloads the Tectonic bundle and may take several minutes.", flush=True)
        try:
            result = subprocess.run(
                ["tectonic", "--chatter=minimal", "--outdir", str(workdir), str(tex_path)],
                capture_output=True,
                text=True,
                cwd=workdir,
            )
        except FileNotFoundError:
            print("FAIL: tectonic binary not found on PATH", file=sys.stderr)
            return 1

        if result.returncode != 0 or not (workdir / "prewarm.pdf").exists():
            print(f"FAIL: tectonic exited {result.returncode}", file=sys.stderr)
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return 1

        size = (workdir / "prewarm.pdf").stat().st_size
        print(f"OK: compiled prewarm.pdf ({size} bytes). Package cache is warm.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
