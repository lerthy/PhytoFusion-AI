FROM python:3.12-slim

# BLAST+ is used by the comparative genomics engine
RUN apt-get update \
    && apt-get install -y --no-install-recommends ncbi-blast+ \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser
WORKDIR /srv

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

USER appuser
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
