FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TECTONIC_VERSION=0.15.0 \
    TECTONIC_CACHE_DIR=/var/cache/tectonic

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-$(uname -m)-unknown-linux-musl.tar.gz" \
       | tar -xz -C /usr/local/bin tectonic \
    && chmod +x /usr/local/bin/tectonic \
    && tectonic --version

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# Bake the CTAN package cache into the image so the first request is not slow.
RUN python test_compile.py

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
