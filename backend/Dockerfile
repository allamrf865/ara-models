FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_prod.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ../incoming/ara_model_bundle_20251016_040813.zip /app/incoming/

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

CMD uvicorn app:app --host 0.0.0.0 --port ${PORT}
